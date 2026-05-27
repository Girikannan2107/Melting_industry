import cv2
import base64
import json
import os
import requests
from .preprocessing import ImagePreprocessor
from core.config import settings

class IntelligentDocumentProcessor:
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        # Notice we removed Paddle and TrOCR completely!

    def process_document(self, image_path: str) -> dict:
        if not self.api_key:    
            return {"error": "Missing GEMINI_API_KEY. Please set the environment variable or hardcode it in engine.py."}

        print("1. Converting PDF/Document to Image...")
        # We still use your preprocessor to handle PDFs and enhance the image
        enhanced_img, orig_img = self.preprocessor.enhance(image_path)

        print("2. Encoding image for AI Vision...")
        # Convert the OpenCV image array into a standard JPG base64 string
        _, buffer = cv2.imencode('.jpg', enhanced_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        print("3. Sending image directly to Gemini 1.5 Flash Vision API...")
        prompt = """
        You are an elite Industrial Data Extraction AI. 
        I am providing you with an image of a Ladle Pouring Record.
        
        Read the image carefully. Read both the printed text and the handwriting. 
        Correct any obvious typos based on the context (e.g., 'Laddie' -> 'Ladle', 'Tem Pexqture' -> 'Temperature').
        
        OUTPUT SCHEMA INSTRUCTIONS:
        You MUST return ONLY a valid JSON object matching this exact structure. Do not invent data. If a field is missing or empty in the image, use an empty string "".
        
        {
          "document_info": {
            "date": "Extract the document date",
            "heat_no": "Extract the Heat Number (e.g., A09600)",
            "ladle_capacity": "Extract ladle capacity (e.g., '3 Ton')"
          },
          "pouring_details": {
            "excess_metal_ingot_kg": "Extract excess metal ingot as a number (e.g., 240.0)",
            "pouring_temperatures": ["Array of pouring temperatures, e.g., '1534°C'"],
            "ladle_temperature": "Extract ladle temperature, e.g., '786°C'"
          },
          "table_data": [
            {
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
            }
          ]
        }
        
        RULES:
        1. Ignore table headers. Start mapping from the actual data rows.
        2. Keep the 18 columns strictly aligned. 
        3. Only output raw JSON, no markdown formatting blocks.
        """

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": img_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.1 # Low temperature for highly factual OCR extraction
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            ai_text_response = result['candidates'][0]['content']['parts'][0]['text']
            
            return json.loads(ai_text_response)
            
        except Exception as e:
            print(f"AI Vision Error: {e}")
            if 'response' in locals():
                print(f"API Response: {response.text}")
            return {"error": str(e)}