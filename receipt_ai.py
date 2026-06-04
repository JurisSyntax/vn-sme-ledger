import pytesseract, re
from PIL import Image, ImageFilter

def parse_receipt_vn(img_path, model="qwen2.5:3b"):
    try:
        img = Image.open(img_path).convert('L').filter(ImageFilter.SHARPEN)
        raw = pytesseract.image_to_string(img, lang='vie+eng')[:1500]
        amount_matches = re.findall(r"(\d[\d\.,]{3,})", raw)
        total = 0
        if amount_matches:
            total = max(int(x.replace(".", "").replace(",", "")) for x in amount_matches if x.replace(".", "").replace(",", "").isdigit())
        return {
            "date": "",
            "vendor": "",
            "total_vnd": total,
            "vat_vnd": 0,
            "category": "Other",
            "raw_text": raw,
            "note": "Offline OCR only; vui lòng kiểm tra lại trước khi ghi sổ.",
        }
    except Exception as e:
        return {"error": str(e)}
