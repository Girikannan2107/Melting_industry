import torch
import cv2
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

class TrOCRClient:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten")
        self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-handwritten").to(self.device)

    def extract_handwritten(self, img_array) -> dict:
        image = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device)
        
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)
            
        text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return {"text": text, "confidence": 0.85, "type": "handwritten"}