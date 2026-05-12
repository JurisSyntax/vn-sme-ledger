import re
with open("C:/Users/AMD/.gemini/antigravity/scratch/vn-sme-ledger/main.py", "r", encoding="utf-8") as f:
    text = f.read()
matches = re.findall(r'self\.lbl\["([^"]+)"\]', text)
print(set(matches))
