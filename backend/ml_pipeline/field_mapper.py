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
        You are an elite Industrial Data Extraction AI. 
        I am providing you with the raw, imperfect OCR text from a Ladle Pouring Record.
        
        Your task is to semantically analyze the text, correct any obvious OCR typos (e.g., 'Laddie' -> 'Ladle', 'Tem Pexqture' -> 'Temperature'), and map the values to the exact JSON schema provided. 
        Use your intelligence to align the columns properly. For example, if you see 'WCB', that is the Grade. If you see 'Geco Special Machiners', that is the Customer.
        
        RAW OCR TEXT:
        {combined_ocr_text}
        
        OUTPUT SCHEMA INSTRUCTIONS:
        You MUST return ONLY a valid JSON object matching this exact structure. Do not invent data. If a field is missing, use an empty string "".
        
        {{
          "document_info": {{
            "date": "Extract the document date",
            "heat_no": "Extract the Heat Number (e.g., A09600)",
            "ladle_capacity": "Extract ladle capacity (e.g., '3 Ton')"
          }},
          "pouring_details": {{
            "excess_metal_ingot_kg": "Extract excess metal ingot as a number (e.g., 240.0)",
            "pouring_temperatures": ["Array of pouring temperatures, e.g., '1534°C'"],
            "ladle_temperature": "Extract ladle temperature, e.g., '786°C'"
          }},
          "table_data": [
            {{
              "date": "Row Date (if any)",
              "heat_no": "Row Heat No (e.g., A09600-01)",
              "item": "Item description (e.g., BEARING HOUSING, TC-3000)",
              "grade": "Material grade (e.g., WCB)",
              "customer": "Customer Name",
              "planned_pouring_weight": "Planned weight",
              "pouring_time_planned": "Planned time",
              "ladle_number": "Ladle No",
              "tapping_sequence": "Tapping sequence number",
              "pouring_sequence": "Pouring sequence number",
              "pouring_time_sec": "Pouring time in seconds",
              "metal_weight_before_kg": "Weight before pouring",
              "metal_weight_after_kg": "Weight after pouring",
              "kno_weight": "Kno weight",
              "actual_liquid_poured_kg": "Actual liquid poured",
              "weight_diff": "Difference in weight",
              "pouring_observation": "Remarks or observations",
              "weight_before_cutting": "Weight before cutting"
            }}
          ]
        }}
        
        RULES:
        1. Ignore table headers (e.g., do not make a row where customer="Customer" or item="Item").
        2. Ensure data aligns correctly. Do not put numbers in the Customer field unless it is an actual numbered customer code.
        """

        # Fallback dictionary if API fails
        fallback_data = {
            "document_info": {}, "pouring_details": {}, "table_data": [], 
            "error": "AI Inference failed.", "raw_text_dump": combined_ocr_text
        }

        if not self.api_key:
            fallback_data["error"] = "Missing GEMINI_API_KEY"
            return fallback_data

        try:
            # DIRECT REST API CALL (Bypasses Google SDK & Protobuf conflicts completely)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse the Gemini JSON response
            result = response.json()
            ai_text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            structured_data = json.loads(ai_text_response)
            structured_data["raw_text_dump"] = combined_ocr_text 
            
            return structured_data
            
        except Exception as e:
            print(f"AI Mapping Error: {e}")
            if 'response' in locals():
                print(f"API Response: {response.text}")
            return fallback_data