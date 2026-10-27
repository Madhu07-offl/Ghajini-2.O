import os

base_txt = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "static", "logo_base64.txt")
out_py = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "static", "logo_data.py")

with open(base_txt, "r", encoding="utf-8") as f:
    b64 = f.read().strip()

with open(out_py, "w", encoding="utf-8") as f:
    f.write(f'LOGO_BASE64 = "{b64}"\n')

print(f"Generated {out_py} with {len(b64)} chars.")
