import cv2
import numpy as np
import fitz  # PyMuPDF

class ImagePreprocessor:
    @staticmethod
    def enhance(file_path: str) -> tuple[np.ndarray, np.ndarray]:
        if file_path.lower().endswith('.pdf'):
            pdf_document = fitz.open(file_path)
            page = pdf_document.load_page(0)
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            
            if pix.n == 4: img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3: img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pix.n == 1: img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            pdf_document.close()
        else:
            img = cv2.imread(file_path)
            
        if img is None:
            raise ValueError(f"Could not load image: {file_path}")

        h, w = img.shape[:2]
        if h > w:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Only upscale for OCR accuracy if the image is relatively low-resolution (max dimension < 1500)
        h, w = img.shape[:2]
        if max(h, w) < 1500:
            img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        
        # CRITICAL FIX: Gentle Contrast Enhancement instead of harsh B&W Thresholding
        # This prevents faded printed text from disappearing.
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return enhanced_bgr, img