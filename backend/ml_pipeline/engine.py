import cv2
import base64
import json
import os
import requests
import re
from .preprocessing import ImagePreprocessor
from core.config import settings

class IntelligentDocumentProcessor:
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    def _repair_json(self, raw_text: str) -> str:
        """Strips markdown and cleans up standard AI syntax errors to ensure parsing."""
        text = raw_text.strip()
        
        if text.startswith("```json"): 
            text = text[7:]
        if text.startswith("```"): 
            text = text[3:]
        if text.endswith("```"): 
            text = text[:-3]
        text = text.strip()
        
        text = re.sub(r"(?<!\\)'", '"', text)
        text = re.sub(r',\s*([\]}])', r'\1', text)
        return text

    def process_document(self, image_path: str) -> dict:
        if not self.api_key: 
            return {"error": "Missing GEMINI_API_KEY. Please check your .env file."}

        print(f"1. Processing image: {image_path}")
        enhanced_img, _ = self.preprocessor.enhance(image_path)
        # Compress to 50 quality to speed up the network transfer!
        _, buffer = cv2.imencode('.jpg', enhanced_img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        print("2. Sending to Verified Gemini 2.5 Flash API...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        # Extremely clean and clear prompt
        prompt = """Extract ALL data from this Induction Furnace Log / Production Plan document.
        
        CRITICAL RULES: 
        1. Only extract rows that have actual written data. Do NOT repeat or duplicate rows.
        2. If a column or row is empty in the image, set its value to null.
        3. Do NOT include any materials in `scrap_and_returns`, `ferro_pure_alloys`, or `deoxidants` arrays if their quantity is 0 or null. Only include actual added materials.
        4. Keep the JSON compact. Write arrays (like bath_readings) on a single line (e.g., [0.08, 0.08]) to save tokens.
        5. Do NOT get stuck in loops repeating readings.
        6. In the `chemical_composition` array, ONLY include elements that have actual hand-written measurements. Do NOT include elements like B, PREN, CF, N, Fe which are empty or have no values.
        7. Do NOT include `inti_min`, `inti_max`, `uapl_min`, or `uapl_max` in the JSON if they are 0 or null.
        
        Extract the data into a JSON object matching this exact schema:"""

        # The schema does all the heavy lifting now
        schema = {
            "type": "OBJECT",
            "properties": {
                "header": {
                  "type": "OBJECT",
                  "properties": {
                    "date": {"type": "STRING"},
                    "grade": {"type": "STRING"},
                    "melt_number": {"type": "STRING"},
                    "crucible_no": {"type": "STRING"}
                  }
                },
                "time_and_energy": {
                  "type": "OBJECT",
                  "properties": {
                    "total_time_consumed": {"type": "STRING"},
                    "power_total_units": {"type": "NUMBER"},
                    "furnace_readings": {
                      "type": "ARRAY",
                      "items": {
                        "type": "OBJECT",
                        "properties": {
                          "time_hrs": {"type": "STRING"},
                          "freq": {"type": "STRING"},
                          "kw": {"type": "STRING"},
                          "voltage": {"type": "STRING"},
                          "inlet": {"type": "STRING"},
                          "outlet": {"type": "STRING"},
                          "gld": {"type": "STRING"}
                        }
                      }
                    }
                  }
                },
                "chemical_composition": {
                  "type": "ARRAY",
                  "items": {
                    "type": "OBJECT",
                    "properties": {
                      "element": {"type": "STRING"},
                      "inti_min": {"type": "NUMBER"},
                      "inti_max": {"type": "NUMBER"},
                      "uapl_min": {"type": "NUMBER"},
                      "uapl_max": {"type": "NUMBER"},
                      "bath_readings": {
                        "type": "ARRAY",
                        "items": {"type": "NUMBER"}
                      },
                      "final_sample": {"type": "NUMBER"}
                    }
                  }
                },
                "scrap_and_returns": {
                  "type": "ARRAY",
                  "items": {
                    "type": "OBJECT",
                    "properties": {
                      "material_name": {"type": "STRING"},
                      "quantity_kgs": {"type": "NUMBER"},
                      "quantity_ladle_kgs": {"type": "NUMBER"}
                    }
                  }
                },
                "ferro_pure_alloys": {
                  "type": "ARRAY",
                  "items": {
                    "type": "OBJECT",
                    "properties": {
                      "material_name": {"type": "STRING"},
                      "quantity_kgs": {"type": "NUMBER"},
                      "quantity_ladle_kgs": {"type": "NUMBER"}
                    }
                  }
                },
                "deoxidants": {
                  "type": "ARRAY",
                  "items": {
                    "type": "OBJECT",
                    "properties": {
                      "material_name": {"type": "STRING"},
                      "quantity_kgs": {"type": "NUMBER"},
                      "quantity_ladle_kgs": {"type": "NUMBER"}
                    }
                  }
                },
                "process_parameters": {
                  "type": "OBJECT",
                  "properties": {
                    "tapping_temp_c": {"type": "STRING"},
                    "pouring_temp_c": {"type": "STRING"},
                    "furnace_lining_condition": {"type": "STRING"},
                    "tags_punched": {"type": "STRING"},
                    "hind_tags_checked": {"type": "STRING"}
                  }
                },
                "yield_and_dispatch": {
                  "type": "OBJECT",
                  "properties": {
                    "total_metal_tapped_kgs": {"type": "NUMBER"},
                    "total_charges_kgs": {"type": "NUMBER"},
                    "extra_metal_kgs": {"type": "NUMBER"},
                    "qc_incharge": {"type": "STRING"},
                    "melting_incharge": {"type": "STRING"},
                    "fic_charge_hand": {"type": "STRING"},
                    "spilage_metal_kgs": {"type": "NUMBER"},
                    "tags_discard": {"type": "STRING"},
                    "qc_remarks": {"type": "STRING"}
                  }
                },
                "pouring_table": {
                  "type": "ARRAY",
                  "items": {
                    "type": "OBJECT",
                    "properties": {
                      "item_description": {"type": "STRING"},
                      "quantity": {"type": "NUMBER"},
                      "planned_weight_kg": {"type": "NUMBER"},
                      "poured_weight_kg": {"type": "NUMBER"}
                    }
                  }
                }
            }
        }

        try:
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt}, 
                        {"inlineData": {"mimeType": "image/jpeg", "data": img_base64}}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.0, 
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json",
                    "responseSchema": schema
                }
            }
            import time
            
            max_retries = 3
            backoff_factor = 2
            response = None
            
            for retry in range(max_retries + 1):
                try:
                    response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
                    
                    # If 503 (High Demand) or 429 (Rate Limit) occurs, retry with backoff
                    if response.status_code in [503, 429] and retry < max_retries:
                        wait_time = (backoff_factor ** retry) + 2
                        print(f"⚠️ Google API returned {response.status_code}. Retrying in {wait_time} seconds (attempt {retry + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if retry == max_retries or (response is not None and response.status_code not in [503, 429]):
                        raise e
            
            raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            clean_text = self._repair_json(raw_text)
            
            try:
                parsed_data = json.loads(clean_text)
                print("✅ Extraction and JSON Parse Successful!")
                return parsed_data
            except json.JSONDecodeError as je:
                if not clean_text.endswith("}"):
                    try:
                        emergency_close = clean_text + "}]}}"
                        parsed_data = json.loads(emergency_close)
                        print("✅ Emergency JSON Recovery Successful!")
                        return parsed_data
                    except:
                        pass
                
                print(f"❌ JSON Parse Error: {je}")
                print(f"\n--- RAW TEXT THAT FAILED TO PARSE ---\n{clean_text}\n-------------------------------------\n")
                return {"error": f"JSON Parse Error: {je}. Check terminal for raw output."}
                
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text
            print(f"❌ API HTTP Error: {error_msg}")
            return {"error": f"API Error: {error_msg}"}
        except Exception as e:
            print(f"❌ Extraction Error: {e}")
            return {"error": str(e)}