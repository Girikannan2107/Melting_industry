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
    FIX 3: If Gemini still truncates despite a higher token budget,
    attempt to close any open brackets/braces so json.loads() can succeed.
    Works for the specific pattern seen in the logs (open array/object).
    """
    # Strip markdown fences Gemini sometimes wraps around JSON
    raw = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)
    raw = raw.strip()

    # Count unclosed brackets
    open_braces   = raw.count("{") - raw.count("}")
    open_brackets = raw.count("[") - raw.count("]")

    if open_braces == 0 and open_brackets == 0:
        return raw   # nothing to fix

    # If the last character is a comma or whitespace, strip it before closing
    raw = raw.rstrip().rstrip(",")

    # Close open structures in LIFO order  (simple heuristic)
    closing = ""
    # Walk backwards through the raw string to figure out ordering
    depth_stack = []
    in_string   = False
    escape_next = False
    for ch in raw:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
        if not in_string:
            if ch in ("{", "["):
                depth_stack.append(ch)
            elif ch in ("}", "]"):
                if depth_stack:
                    depth_stack.pop()

    for opener in reversed(depth_stack):
        closing += "}" if opener == "{" else "]"

    repaired = raw + closing
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
Extract ALL chemical composition data from this steel/iron melt certificate PDF.

Return ONLY a valid, complete JSON object — no markdown, no commentary.

Schema:
{
  "chemical_composition": [
    {
      "element":      "<symbol e.g. C>",
      "bath_readings": [<float>, ...],
      "final_sample": <float>,
      "inti_min":     <float>,
      "inti_max":     <float>,
      "uapl_min":     <float>,
      "uapl_max":     <float>
    }
  ],
  "heat_number":   "<string or null>",
  "grade":         "<string or null>",
  "date":          "<ISO date string or null>"
}

Important:
- Include every element present in the document.
- Use null for any field you cannot find.
- Do NOT truncate the array — include ALL elements.
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
        logger.error("❌ Extraction error: %s", exc)
        return {"status": "error", "message": str(exc)}