import os
import json
import requests
from core.config import settings

class FieldMapper:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY environment variable is not set!")

    def _flatten_ocr_data(self, raw_data: dict) -> str:
        """Converts the raw OCR bounding box data into a readable text dump."""
        header_text = [item.get('text', '') for item in raw_data.get("header_raw", []) if isinstance(item, dict)]
        
        table_text = []
        for row in raw_data.get("table_rows", []):
            if isinstance(row, list):
                cleaned_row = [str(cell).strip() for cell in row if str(cell).strip()]
                table_text.append(" | ".join(cleaned_row))
                
        footer_text = raw_data.get("footer_notes", [])

        return (
            "--- HEADER OCR ---\n" + "\n".join(header_text) + "\n\n"
            "--- TABLE OCR ---\n" + "\n".join(table_text) + "\n\n"
            "--- FOOTER OCR ---\n" + "\n".join(footer_text)
        )

    def map_fields(self, raw_data: dict) -> dict:
        print("Passing OCR text to Gemini AI via REST API for Semantic Mapping...")
        
        combined_ocr_text = self._flatten_ocr_data(raw_data)
        
        prompt = f"""
        You are an elite Industrial Metallurgical Data Extraction AI. 
        I am providing you with the raw, imperfect OCR text from an Induction Furnace Melting Log Sheet.
        
        Your task is to semantically analyze the text, correct any obvious OCR typos, and map the values to the exact JSON schema provided.
        
        RAW OCR TEXT:
        {combined_ocr_text}
        
        OUTPUT SCHEMA INSTRUCTIONS:
        You MUST return ONLY a valid JSON object matching this exact structure. 
        
        {{
          "header": {{
            "date": "Extract Date", "grade": "Extract Grade", "melt_number": "Extract Melt Number", "crucible_no": "Extract Crucible No"
          }},
          "time_and_energy": {{
            "furnace_started_at": "Time string", "sample_times": [], "melt_tapped_at": "", 
            "total_time_consumed": "", "power_initial_reading": 0.0, "power_final_reading": 0.0, "power_total_units": 0.0
          }},
          "chemical_composition": [
            {{
              "element": "e.g., C, Mn, Si", "inti_min": 0.0, "inti_max": 0.0, "uapl_min": 0.0, "uapl_max": 0.0,
              "bath_readings": [], "final_sample": 0.0
            }}
          ],
          "scrap_and_returns": [],
          "ferro_pure_alloys": [],
          "deoxidants": [],
          "process_parameters": {{
            "tapping_temp_c": "", "pouring_temp_c": "", "shank_ladle_temp_c": "",
            "lining_condition": "", "slag_condition": "", "shank_ladle_condition": "", "dissolved_gas_level": ""
          }},
          "yield_and_dispatch": {{
            "total_charges_kgs": 0.0, "total_addition_kgs": 0.0, "total_metal_tapped_kgs": 0.0,
            "no_of_moulds_poured": 0, "no_of_test_bars": 0, "qc_remarks": ""
          }}
        }}
        """

        # Update fallback data to match the new Pydantic Schema exactly
        fallback_data = {
            "header": {}, "time_and_energy": {}, "chemical_composition": [],
            "scrap_and_returns": [], "ferro_pure_alloys": [], "deoxidants": [],
            "process_parameters": {}, "yield_and_dispatch": {},
            "error": "AI Inference failed.", "raw_text_dump": combined_ocr_text
        }

        if not self.api_key:
            fallback_data["error"] = "Missing GEMINI_API_KEY"
            return fallback_data

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            ai_text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            structured_data = json.loads(ai_text_response)
            structured_data["raw_text_dump"] = combined_ocr_text 
            
            return structured_data
            
        except Exception as e:
            print(f"AI Mapping Error: {e}")
            return fallback_data