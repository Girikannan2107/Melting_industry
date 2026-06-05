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
        
        # Remove markdown formatting
        if text.startswith("```json"): 
            text = text[7:]
        if text.startswith("```"): 
            text = text[3:]
        if text.endswith("```"): 
            text = text[:-3]
        text = text.strip()
        
        # Replace unescaped single quotes with double quotes
        text = re.sub(r"(?<!\\)'", '"', text)
        # Remove trailing commas before closing brackets
        text = re.sub(r',\s*([\]}])', r'\1', text)
        return text

    def process_document(self, image_path: str) -> dict:
        if not self.api_key: 
            return {"error": "Missing GEMINI_API_KEY. Please check your .env file."}

        print(f"1. Processing image: {image_path}")
        enhanced_img, _ = self.preprocessor.enhance(image_path)
        _, buffer = cv2.imencode('.jpg', enhanced_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        print("2. Sending to Verified Gemini 2.5 Flash API...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"        
        # Extremely strict prompt to prevent pretty-printing cutoffs
        prompt = """Extract ALL data from this 2-page Induction Furnace Melting Log.
        
        CRITICAL RULES: 
        1. Output EXACTLY ONE valid JSON object.
        2. You MUST minify the JSON. Do NOT use any spaces, tabs, or newlines in the output.
        3. Do NOT wrap the output in markdown (no ```json).
        4. Use null for blank fields. Do NOT include empty rows in arrays.
        
        Schema Requirement:
        {"header":{},"time_and_energy":{},"chemical_composition":[],"scrap_and_returns":[],"ferro_pure_alloys":[],"deoxidants":[],"process_parameters":{},"yield_and_dispatch":{},"pouring_table":[]}"""

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
                    "maxOutputTokens": 8192
                    # responseMimeType is INTENTIONALLY REMOVED here to prevent the API cutoff bug
                }
            }
            
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            response.raise_for_status()
            
            raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            clean_text = self._repair_json(raw_text)
            
            try:
                parsed_data = json.loads(clean_text)
                print("✅ Extraction and JSON Parse Successful!")
                return parsed_data
            except json.JSONDecodeError as je:
                # Emergency closure: If the token limit still cuts off the very end of the JSON, safely close it.
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