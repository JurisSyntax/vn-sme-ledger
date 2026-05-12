import pytesseract, re, json, requests
from PIL import Image, ImageFilter

def parse_receipt_vn(img_path, model="qwen2.5:3b"):
    try:
        img = Image.open(img_path).convert('L').filter(ImageFilter.SHARPEN)
        raw = pytesseract.image_to_string(img, lang='vie+eng')[:1500]
        
        prompt = f"""Extract VN receipt data. Return ONLY valid JSON:
        {{"date":"YYYY-MM-DD","vendor":"str","total_vnd":num,"vat_vnd":num,"category":"str"}}
        Rules: category ∈ [Paper_Ink, Machine_Maint, Rent, Ingredients, Med_Supplies, Office, Other].
        Text: {raw}"""
        
        resp = requests.post("http://localhost:11434/api/generate",
                             json={"model": model, "prompt": prompt, "stream": False}, timeout=10)
        try:
            return json.loads(re.search(r'\{.*\}', resp.json()['response'], re.DOTALL).group())
        except: return {"error": "Parse failed. Verify OCR/Ollama."}
    except Exception as e:
        return {"error": str(e)}
