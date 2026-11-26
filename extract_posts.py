#!/usr/bin/env python3
import os
import re
import sys
import json
import html
import urllib.request
import urllib.parse
from markdownify import markdownify as md
from bs4 import BeautifulSoup

BASE_DIR = "/Users/agenten/vinverdenenrundt"
CONTENT_DIR = os.path.join(BASE_DIR, "content", "articles")
IMAGES_DIR = os.path.join(BASE_DIR, "public", "images")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"

def download_file(url, target_path):
    if not url:
        return False
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"    [Advarsel] Kunne ikke hente billede {url}: {e}")
        return False

def clean_filename(url):
    parsed = urllib.parse.urlparse(url)
    basename = os.path.basename(parsed.path)
    # fjern query params og sære tegn
    basename = re.sub(r"[^\w\-.]", "_", basename)
    return basename

print("🔄 Henter alle artikler fra vinverdenenrundt.dk via WP REST API...")

all_posts = []
page = 1
while True:
    api_url = f"https://vinverdenenrundt.dk/wp-json/wp/v2/posts?per_page=50&page={page}&_embed=true"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            posts = json.loads(resp.read().decode())
            if not posts:
                break
            all_posts.extend(posts)
            print(f"  Side {page}: Hentede {len(posts)} artikler (I alt {len(all_posts)})...")
            page += 1
    except urllib.error.HTTPError as e:
        if e.code == 400: # Over last page
            break
        print(f"  Fejl på side {page}: {e}")
        break
    except Exception as e:
        print(f"  Netværksfejl: {e}")
        break

print(f"\n✅ Færdig med API-hentning. I alt {len(all_posts)} artikler modtaget.")

# Gem rå backup
raw_backup_path = os.path.join(DATA_DIR, "raw_posts.json")
with open(raw_backup_path, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=2)
print(f"💾 Rå API-data gemt i: {raw_backup_path}")

articles_index = []
downloaded_images = set()

print("\n🚀 Konverterer til Markdown og henter medier...")

for idx, p in enumerate(all_posts, start=1):
    post_id = p.get("id")
    slug = p.get("slug")
    date = p.get("date")
    modified = p.get("modified")
    title = html.unescape(p.get("title", {}).get("rendered", "")).strip()
    
    # Hent categories og tags fra _embedded
    categories = []
    tags = []
    emb = p.get("_embedded", {})
    if "wp:term" in emb:
        for tg in emb["wp:term"]:
            for term in tg:
                taxonomy = term.get("taxonomy")
                name = html.unescape(term.get("name", "")).strip()
                if taxonomy == "category" and name.lower() != "uncategorized":
                    categories.append(name)
                elif taxonomy == "post_tag":
                    tags.append(name)

    # Primær kategori
    primary_category = categories[0] if categories else "Vin"

    # Featured Image
    featured_img_url = None
    featured_img_local = None
    if "wp:featuredmedia" in emb and emb["wp:featuredmedia"]:
        fm = emb["wp:featuredmedia"][0]
        featured_img_url = fm.get("source_url")
        if featured_img_url:
            img_fname = clean_filename(featured_img_url)
            img_target = os.path.join(IMAGES_DIR, img_fname)
            if download_file(featured_img_url, img_target):
                featured_img_local = f"/images/{img_fname}"
                downloaded_images.add(img_fname)

    # Excerpt
    raw_excerpt = p.get("excerpt", {}).get("rendered", "")
    soup_excerpt = BeautifulSoup(raw_excerpt, "html.parser")
    clean_excerpt = html.unescape(soup_excerpt.get_text()).replace("\n", " ").strip()

    # Content & inline billeder
    raw_content = p.get("content", {}).get("rendered", "")
    soup_content = BeautifulSoup(raw_content, "html.parser")

    # Find og download inline billeder
    for img in soup_content.find_all("img"):
        src = img.get("src")
        if src and ("vinverdenenrundt.dk" in src or src.startswith("http")):
            fname = clean_filename(src)
            target = os.path.join(IMAGES_DIR, fname)
            if download_file(src, target):
                img["src"] = f"/images/{fname}"
                downloaded_images.add(fname)
            if img.get("srcset"):
                del img["srcset"]

    # Konverter HTML til Markdown
    clean_html = str(soup_content)
    markdown_body = md(clean_html, heading_style="ATX", strip=["script", "style"]).strip()
    # Fjern multi-linje linjeskift
    markdown_body = re.sub(r"\n{3,}", "\n\n", markdown_body)

    safe_title = title.replace('"', '\\"')
    safe_excerpt = clean_excerpt.replace('"', '\\"')

    # Byg frontmatter
    frontmatter = [
        "---",
        f'title: "{safe_title}"',
        f'slug: "{slug}"',
        f'date: "{date}"',
        f'modified: "{modified}"',
        f'category: "{primary_category}"',
        f'categories: {json.dumps(categories, ensure_ascii=False)}',
        f'tags: {json.dumps(tags, ensure_ascii=False)}',
        f'featured_image: {json.dumps(featured_img_local)}',
        f'excerpt: "{safe_excerpt}"',
        "---",
        "",
        markdown_body,
        ""
    ]

    md_content = "\n".join(frontmatter)
    md_filename = f"{slug}.md"
    md_path = os.path.join(CONTENT_DIR, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    articles_index.append({
        "id": post_id,
        "title": title,
        "slug": slug,
        "date": date,
        "category": primary_category,
        "tags": tags,
        "image": featured_img_local,
        "excerpt": clean_excerpt
    })

    if idx % 20 == 0 or idx == len(all_posts):
        print(f"  [{idx}/{len(all_posts)}] Behandlet: {title[:40]}...")

index_path = os.path.join(DATA_DIR, "articles_index.json")
with open(index_path, "w", encoding="utf-8") as f:
    json.dump(articles_index, f, ensure_ascii=False, indent=2)

print(f"\n🎉 Succes! {len(articles_index)} artikler konverteret til Markdown.")
print(f"🖼️  {len(downloaded_images)} unikke billeder downloadet til /public/images/.")
print(f"📂 Artikler ligger i: {CONTENT_DIR}")
