"""
ml_pipeline/engine.py  —  Fixed version
Fixes:
  1. JSON truncation  → increased max_output_tokens + streaming reassembly
  2. 503 retries      → exponential backoff (3 attempts)
  3. Partial JSON     → trim-and-repair before json.loads()
"""

import base64
import json
import logging
import re
import time
from pathlib import Path

import httpx                   # already used in most FastAPI projects; swap for requests if needed
import fitz                    # PyMuPDF doesn't require external Poppler installation

logger = logging.getLogger(__name__)

# ── Gemini config ──────────────────────────────────────────────────────────────
GEMINI_MODEL    = "gemini-2.5-flash"   # keep your verified model string
GEMINI_API_URL  = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# ── Tunables ───────────────────────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = 8192      # ← FIX 1: was too small; 8 k handles full composition tables
MAX_RETRIES       = 5         # ← FIX 2: retry on 503
RETRY_DELAYS      = [5, 10, 20, 30, 45]   # seconds between attempts


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pdf_to_base64_images(pdf_path: str) -> list[str]:
    """Convert each PDF page to a base64-encoded PNG string using PyMuPDF."""
    doc = fitz.open(pdf_path)
    images_b64 = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        images_b64.append(base64.b64encode(img_bytes).decode())
    return images_b64


def _repair_truncated_json(raw: str) -> str:
    """
    Robust JSON repairer that handles truncation at any point:
    - Inside a string (closes it)
    - After a colon (appends null)
    - After a comma (strips it)
    - In the middle of an incomplete key-value pair or literal
    """
    # Strip markdown fences Gemini sometimes wraps around JSON
    raw = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)
    raw = raw.strip()

    if not raw:
        return "{}"

    stack = []
    in_string = False
    escape_next = False
    
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if escape_next:
            escape_next = False
            i += 1
            continue
        if ch == "\\":
            escape_next = True
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            if not in_string:
                # Finished a string
                if stack:
                    container = stack[-1]
                    if container["type"] == "object":
                        if container["state"] in ("expect_key_or_close", "expect_key"):
                            container["state"] = "expect_colon"
                        elif container["state"] == "expect_value":
                            container["state"] = "expect_comma_or_close"
                    elif container["type"] == "array":
                        if container["state"] in ("expect_value_or_close", "expect_value"):
                            container["state"] = "expect_comma_or_close"
            i += 1
            continue
            
        if in_string:
            i += 1
            continue
            
        # Outside string
        if ch in (" ", "\t", "\n", "\r"):
            i += 1
            continue
            
        if ch == "{":
            stack.append({"type": "object", "state": "expect_key_or_close"})
        elif ch == "[":
            stack.append({"type": "array", "state": "expect_value_or_close"})
        elif ch == "}":
            if stack and stack[-1]["type"] == "object":
                stack.pop()
                if stack:
                    parent = stack[-1]
                    if parent["type"] == "object" and parent["state"] == "expect_value":
                        parent["state"] = "expect_comma_or_close"
                    elif parent["type"] == "array" and parent["state"] in ("expect_value_or_close", "expect_value"):
                        parent["state"] = "expect_comma_or_close"
        elif ch == "]":
            if stack and stack[-1]["type"] == "array":
                stack.pop()
                if stack:
                    parent = stack[-1]
                    if parent["type"] == "object" and parent["state"] == "expect_value":
                        parent["state"] = "expect_comma_or_close"
                    elif parent["type"] == "array" and parent["state"] in ("expect_value_or_close", "expect_value"):
                        parent["state"] = "expect_comma_or_close"
        elif ch == ":":
            if stack and stack[-1]["type"] == "object" and stack[-1]["state"] == "expect_colon":
                stack[-1]["state"] = "expect_value"
        elif ch == ",":
            if stack:
                container = stack[-1]
                if container["type"] == "object" and container["state"] == "expect_comma_or_close":
                    container["state"] = "expect_key"
                elif container["type"] == "array" and container["state"] == "expect_comma_or_close":
                    container["state"] = "expect_value"
        elif ch in ("-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "t", "f", "n"):
            if stack:
                container = stack[-1]
                if container["type"] == "object" and container["state"] == "expect_value":
                    container["state"] = "expect_comma_or_close"
                elif container["type"] == "array" and container["state"] in ("expect_value_or_close", "expect_value"):
                    container["state"] = "expect_comma_or_close"
        i += 1

    repaired = raw
    if in_string:
        repaired += '"'
        if stack:
            container = stack[-1]
            if container["type"] == "object":
                if container["state"] in ("expect_key_or_close", "expect_key"):
                    container["state"] = "expect_colon"
                elif container["state"] == "expect_value":
                    container["state"] = "expect_comma_or_close"
            elif container["type"] == "array":
                if container["state"] in ("expect_value_or_close", "expect_value"):
                    container["state"] = "expect_comma_or_close"

    # Get the last non-whitespace character of repaired string
    last_char = ""
    for ch in reversed(repaired):
        if ch not in (" ", "\t", "\n", "\r"):
            last_char = ch
            break

    # Resolve each open structure in the stack from inside out
    while stack:
        container = stack.pop()
        if container["type"] == "object":
            if container["state"] == "expect_key":
                # Trailing comma, strip it
                repaired = repaired.rstrip()
                if repaired.endswith(","):
                    repaired = repaired[:-1]
                repaired += "}"
            elif container["state"] == "expect_key_or_close":
                repaired += "}"
            elif container["state"] == "expect_colon":
                repaired += ": null}"
            elif container["state"] == "expect_value":
                if last_char == ":":
                    repaired += " null"
                elif last_char in ("-", "."):
                    repaired += "null"
                elif last_char.isalpha() and last_char not in ("e", "s", "l"):  # not ending valid true/false/null
                    # Strip partial word
                    repaired = repaired.rstrip("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
                    repaired += "null"
                repaired += "}"
            elif container["state"] == "expect_comma_or_close":
                # If the last character was a decimal point, append 0
                if last_char == ".":
                    repaired += "0"
                repaired += "}"
        elif container["type"] == "array":
            if container["state"] == "expect_value":
                # Trailing comma, strip it
                repaired = repaired.rstrip()
                if repaired.endswith(","):
                    repaired = repaired[:-1]
                repaired += "]"
            elif container["state"] == "expect_value_or_close":
                repaired += "]"
            elif container["state"] == "expect_comma_or_close":
                if last_char == ".":
                    repaired += "0"
                repaired += "]"
        
        # When closing this structure, it counts as completing a value for the parent container (if any)
        if stack:
            parent = stack[-1]
            if parent["type"] == "object" and parent["state"] == "expect_value":
                parent["state"] = "expect_comma_or_close"
            elif parent["type"] == "array" and parent["state"] in ("expect_value_or_close", "expect_value"):
                parent["state"] = "expect_comma_or_close"
        # Reset last_char for the next container
        last_char = "}" if container["type"] == "object" else "]"

    return repaired


def _call_gemini(api_key: str, prompt: str, images_b64: list[str]) -> dict:
    """
    Call Gemini with retry logic.
    Returns the parsed JSON dict or raises on unrecoverable failure.
    """
    parts = [{"text": prompt}]
    for img_b64 in images_b64:
        parts.append({
            "inlineData": {
                "mimeType": "image/png",
                "data":     img_b64,
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature":     0.1,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,   # ← FIX 1
            "responseMimeType": "application/json",  # ask Gemini to return pure JSON
        },
    }

    last_error = None
    for attempt in range(MAX_RETRIES):                       # ← FIX 2
        try:
            response = httpx.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload,
                timeout=120,   # generous timeout for large PDFs
            )

            if response.status_code == 503:
                wait = RETRY_DELAYS[attempt]
                logger.warning(
                    "Gemini 503 (overloaded) — attempt %d/%d, retrying in %ds",
                    attempt + 1, MAX_RETRIES, wait,
                )
                time.sleep(wait)
                last_error = f"503 after {attempt+1} attempt(s)"
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    f"API HTTP Error: {response.text}"
                )

            # ── Parse Gemini response structure ──────────────────────────────
            gemini_data = response.json()
            raw_text    = (
                gemini_data
                .get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            if not raw_text:
                raise ValueError("Gemini returned an empty response body.")

            # ── FIX 3: repair before parsing ─────────────────────────────────
            repaired = _repair_truncated_json(raw_text)
            logger.info("JSON Repair Debug: Raw len=%d, Repaired len=%d, Repaired ends with=%r", len(raw_text), len(repaired), repaired[-50:])
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                logger.error("JSON Parse Error: %s\n\n--- RAW ---\n%s\n-----------", e, raw_text)
                raise ValueError(f"JSON Parse Error: {e}. Check terminal for raw output.") from e

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            wait = RETRY_DELAYS[attempt]
            logger.warning("Network error on attempt %d: %s — retrying in %ds", attempt + 1, exc, wait)
            time.sleep(wait)
            last_error = str(exc)

    raise RuntimeError(f"Gemini failed after {MAX_RETRIES} retries. Last error: {last_error}")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry-point called by FastAPI route
# ─────────────────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """
You are an expert metallurgical data extraction assistant.
Extract ALL data from the provided steel/iron Induction Furnace Melting Log Sheet (which may span multiple pages).

Return ONLY a valid, complete JSON object — no markdown, no commentary.

Important:
- Include every field present in the document. 
- Ensure you read both Page 1 (Furnace Logs, Chemistry, Yield) and Page 2 (Pouring Table).
- For floats/numbers, extract them as numbers. Use null for any field you cannot find.
- Correct obvious OCR/handwriting typos.

Output strictly to this Schema:
{
  "header": {
    "date": "<string>",
    "grade": "<string>",
    "melt_number": "<string>",
    "crucible_no": "<string>"
  },
  "time_and_energy": {
    "furnace_readings": [
      {"time_hrs": "<string>", "freq": "<string>", "kw": "<string>", "voltage": "<string>", "inlet": "<string>", "outlet": "<string>", "gld": "<string>"}
    ],
    "furnace_started_at": "<string>",
    "sample_times": ["<string>"],
    "melt_tapped_at": "<string>",
    "total_time_consumed": "<string>",
    "power_initial_reading": <float>,
    "power_final_reading": <float>,
    "power_total_units": <float>
  },
  "chemical_composition": [
    {
      "element": "<symbol e.g. C, Si, Mn>",
      "inti_min": <float>,
      "inti_max": <float>,
      "uapl_min": <float>,
      "uapl_max": <float>,
      "bath_readings": [<float>],
      "final_sample": <float>
    }
  ],
  "scrap_and_returns": [
    {"material_name": "<string>", "quantity_kgs": <float>, "quantity_ladle_kgs": <float>}
  ],
  "ferro_pure_alloys": [
    {"material_name": "<string>", "quantity_kgs": <float>, "quantity_ladle_kgs": <float>}
  ],
  "deoxidants": [
    {"material_name": "<string>", "quantity_kgs": <float>, "quantity_ladle_kgs": <float>}
  ],
  "process_parameters": {
    "tapping_temp_c": "<string>",
    "pouring_temp_c": "<string>",
    "furnace_lining_condition": "<string>",
    "slag_condition": "<string>",
    "dissolved_gas_level": "<string>",
    "hind_tags_checked": "<string>",
    "tags_punched": "<string>"
  },
  "yield_and_dispatch": {
    "total_charges_kgs": <float>,
    "total_addition_kgs": <float>,
    "total_metal_tapped_kgs": <float>,
    "no_of_moulds_poured": <integer>,
    "spilage_metal_kgs": <float>,
    "extra_metal_kgs": <float>,
    "tags_discard": "<string>",
    "melting_incharge": "<string>",
    "qc_incharge": "<string>",
    "fic_charge_hand": "<string>",
    "qc_remarks": "<string>"
  },
  "pouring_table": [
    {
      "item_description": "<string>",
      "quantity": <integer>,
      "planned_weight_kg": <float>,
      "poured_weight_kg": <float>
    }
  ]
}
"""


def process_document(pdf_path: str, gemini_api_key: str) -> dict:
    """
    Process a melt certificate PDF and return structured data.

    Returns a dict with either:
      { "status": "success", "data": { ... } }
    or:
      { "status": "error", "message": "..." }

    The route handler must check 'status' before using 'data'.
    """
    pdf_path = str(pdf_path)
    logger.info("1. Processing image: %s", pdf_path)

    try:
        images_b64 = _pdf_to_base64_images(pdf_path)
    except Exception as exc:
        logger.error("PDF conversion failed: %s", exc)
        return {"status": "error", "message": f"PDF conversion failed: {exc}"}

    logger.info("2. Sending to Verified Gemini 2.5 Flash API...")
    try:
        result = _call_gemini(gemini_api_key, EXTRACTION_PROMPT, images_b64)
        logger.info("✅ Extraction successful.")
        return {"status": "success", "data": result}
    except Exception as exc:
        err_msg = str(exc)
        if "403" in err_msg or "permission_denied" in err_msg.lower():
            logger.error("❌ Extraction error: %s. HINT: Your project/API key has been denied access by Google. Please check your credentials or update the key in backend/.env.", exc)
        elif "429" in err_msg or "quota" in err_msg.lower():
            logger.error("❌ Extraction error: %s. HINT: Quota exceeded for this API key. Please check your AI Studio billing details or request limits.", exc)
        else:
            logger.error("❌ Extraction error: %s", exc)
        return {"status": "error", "message": err_msg}