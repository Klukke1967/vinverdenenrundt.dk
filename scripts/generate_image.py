#!/usr/bin/env python3
"""
scripts/generate_image.py
Genererer vin-billeder i fotorealistisk høj kvalitet via Google Gemini Flash Image API
og gemmer dem direkte i /public/images/.
"""

import os
import sys
import json
import base64
import subprocess
import urllib.request
import urllib.parse

BASE_DIR = "/Users/agenten/vinverdenenrundt"
IMAGES_DIR = os.path.join(BASE_DIR, "public", "images")
ENV_FILE = os.path.join(BASE_DIR, ".env")

os.makedirs(IMAGES_DIR, exist_ok=True)

def get_api_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip("\"'")
    return None

def generate_wine_image(prompt_description, filename_slug):
    key = get_api_key()
    if not key:
        print("❌ Ingen GEMINI_API_KEY fundet.")
        return None

    # Forbedr prompten med professionelle fotomarkører
    full_prompt = (
        f"A cinematic, high-end editorial photograph for a prestigious wine magazine. "
        f"{prompt_description}. "
        f"Photorealistic, natural soft ambient lighting, rich color grading, depth of field, 35mm film photography, 8k resolution, award-winning composition, no text, no watermarks."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={key}"
    data = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}]
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    print(f"🎨 Genererer AI-billede med Google Gemini...")
    print(f"   Prompt: {prompt_description[:70]}...")
    
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            res = json.loads(resp.read().decode())
            cands = res.get("candidates", [])
            if not cands:
                print("❌ Ingen kandidater returneret fra Gemini.")
                return None
            
            parts = cands[0].get("content", {}).get("parts", [])
            for p in parts:
                if "inlineData" in p:
                    b64_data = p["inlineData"].get("data")
                    mime = p["inlineData"].get("mimeType", "image/png")
                    img_bytes = base64.b64decode(b64_data)
                    
                    raw_png = os.path.join(IMAGES_DIR, f"{filename_slug}_raw.png")
                    final_jpg = os.path.join(IMAGES_DIR, f"{filename_slug}.jpg")
                    
                    with open(raw_png, "wb") as f:
                        f.write(img_bytes)
                    
                    # Konverter til optimeret JPG via macOS sips
                    subprocess.run(["/usr/bin/sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", raw_png, "--out", final_jpg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Fjern rå PNG for at spare plads
                    if os.path.exists(final_jpg) and os.path.getsize(final_jpg) > 0:
                        os.remove(raw_png)
                        rel_path = f"/images/{filename_slug}.jpg"
                        print(f"✅ Billede genereret og gemt i: {final_jpg}")
                        return rel_path
                    else:
                        rel_path = f"/images/{filename_slug}_raw.png"
                        return rel_path

    except Exception as e:
        print(f"❌ Fejl under billedgenerering: {e}")
        return None

    return None

if __name__ == "__main__":
    if len(sys.argv) > 2:
        prompt = sys.argv[1]
        slug = sys.argv[2]
        res = generate_wine_image(prompt, slug)
        print("Resultat:", res)
    else:
        print("Usage: python generate_image.py '<prompt>' '<slug>'")
