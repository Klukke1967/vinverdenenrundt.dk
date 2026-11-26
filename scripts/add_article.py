#!/usr/bin/env python3
"""
scripts/add_article.py
Hjælpe-script til automatisk at tilføje og publicere en ny vinartikel
direkte via Hermes Agent og pushe til GitHub Pages.
"""

import os
import re
import sys
import json
import subprocess
import unicodedata
from datetime import datetime

BASE_DIR = "/Users/agenten/vinverdenenrundt"
CONTENT_DIR = os.path.join(BASE_DIR, "content", "articles")
DATA_FILE = os.path.join(BASE_DIR, "data", "articles_index.json")

# Importer billedgenerator
sys.path.append(os.path.join(BASE_DIR, "scripts"))
try:
    from generate_image import generate_wine_image
except ImportError:
    generate_wine_image = None

def slugify(text):
    text = text.lower()
    text = text.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text

def add_article(title, category, tags, excerpt, markdown_body, image_rel=None, image_prompt=None, auto_push=True):
    slug = slugify(title)
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # 1. Billedhåndtering (AI-generering via Google Gemini hvis intet billede er givet)
    if not image_rel and image_prompt and generate_wine_image:
        print(f"📸 Genererer skræddersyet forsidebillede via Google Gemini...")
        generated = generate_wine_image(image_prompt, slug)
        if generated:
            image_rel = generated

    if not image_rel:
        image_rel = "/images/italien-vin.jpg"
    
    # 2. Byg Frontmatter
    safe_title = title.replace('"', '\\"')
    safe_excerpt = excerpt.replace('"', '\\"')
    
    frontmatter = [
        "---",
        f'title: "{safe_title}"',
        f'slug: "{slug}"',
        f'date: "{now_iso}"',
        f'modified: "{now_iso}"',
        f'category: "{category}"',
        f'categories: {json.dumps([category], ensure_ascii=False)}',
        f'tags: {json.dumps(tags, ensure_ascii=False)}',
        f'featured_image: "{image_rel}"',
        f'excerpt: "{safe_excerpt}"',
        "---",
        "",
        markdown_body.strip(),
        ""
    ]
    
    md_content = "\n".join(frontmatter)
    md_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"📄 Gemte Markdown i: {md_path}")
    
    # 2. Opdater articles_index.json
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    # Fjern eksisterende hvis samme slug
    articles = [a for a in articles if a.get("slug") != slug]
    
    new_entry = {
        "title": title,
        "slug": slug,
        "date": now_iso,
        "category": category,
        "tags": tags,
        "image": image_rel,
        "excerpt": excerpt
    }
    articles.insert(0, new_entry)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("📋 Opdaterede articles_index.json")
    
    # 3. Kør build_site og generate_prototype
    subprocess.run(["python3", os.path.join(BASE_DIR, "generate_prototype.py")], check=True)
    subprocess.run(["/Users/agenten/.hermes/tools/python-3.14.9+20261021-darwin-arm64/bin/python3", os.path.join(BASE_DIR, "build_site.py")], check=True)
    print("🔨 Sitet er genopbygget")
    
    # 4. Git commit & push hvis ønsket
    if auto_push:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"feat(article): add '{title}'"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
        print(f"🚀 Pushede til GitHub! Ny artikel vil være live om 20 sekunder på:")
        print(f"   https://klukke1967.github.io/vinverdenenrundt.dk/{slug}/")
    
    return slug

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: importer modul eller kør via python")
        sys.exit(0)
