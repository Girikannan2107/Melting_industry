from paddleocr import PaddleOCR, PPStructure

class PaddleClient:
    def __init__(self):
        # FORCE English models for layout and table detection
        self.layout_engine = PPStructure(show_log=False, use_gpu=True, lang='en')
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True, show_log=False)

    def get_layout(self, image):
        return self.layout_engine(image)

    def extract_printed(self, img_array) -> list:
        result = self.ocr.ocr(img_array, cls=True)
        if not result or not result[0]: return []
        
        return [
            {"text": line[1][0], "confidence": line[1][1], "bbox": line[0]} 
            for res in result if res for line in res
        ]