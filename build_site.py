#!/usr/bin/env python3
import os
import re
import json
import time
import hashlib
from datetime import datetime
import markdown

BASE_DIR = "/Users/agenten/vinverdenenrundt"
DATA_FILE = os.path.join(BASE_DIR, "data", "articles_index.json")
ARTICLES_DIR = os.path.join(BASE_DIR, "content", "articles")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DOMAIN = "https://vinverdenenrundt.dk"

BUILD_TIME = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
BUILD_VERSION = f"v{int(time.time())}"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Sort descending by date
articles.sort(key=lambda x: x.get("date", ""), reverse=True)

print(f"📦 Starter fuldt site-build for {len(articles)} artikler...")

# Helper to read article markdown body
def get_article_data(slug):
    md_file = os.path.join(ARTICLES_DIR, f"{slug}.md")
    if not os.path.exists(md_file):
        return ""
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content

# Compute related articles
def get_related(article, all_articles, count=3):
    current_slug = article["slug"]
    current_tags = set(t.lower() for t in article.get("tags", []))
    current_cat = (article.get("category") or "").lower()
    
    scored = []
    for other in all_articles:
        if other["slug"] == current_slug:
            continue
        score = 0
        other_tags = set(t.lower() for t in other.get("tags", []))
        overlap = len(current_tags.intersection(other_tags))
        score += overlap * 2
        if (other.get("category") or "").lower() == current_cat:
            score += 1
        scored.append((score, other))
    
    scored.sort(key=lambda x: (x[0], x[1].get("date", "")), reverse=True)
    return [item[1] for item in scored[:count]]

# Article page template
def render_article_page(art, body_html, related):
    title = art["title"]
    slug = art["slug"]
    date_iso = art.get("date", "")
    mod_iso = art.get("modified", date_iso) or date_iso
    cat = art.get("category", "Vin")
    tags = art.get("tags", [])
    excerpt = art.get("excerpt", "")
    img_rel = art.get("image") or "/images/italien-vin.jpg"
    img_abs = f"{DOMAIN}{img_rel}" if img_rel.startswith("/") else img_rel
    canonical = f"{DOMAIN}/{slug}/"
    
    # Word count and reading time
    word_count = len(re.findall(r"\w+", body_html))
    read_time = max(2, word_count // 180)
    
    try:
        dt = datetime.fromisoformat(date_iso.split("+")[0])
        date_dk = dt.strftime("%d. %B %Y").replace("January", "januar").replace("February", "februar")\
            .replace("March", "marts").replace("April", "april").replace("May", "maj").replace("June", "juni")\
            .replace("July", "juli").replace("August", "august").replace("September", "september")\
            .replace("October", "oktober").replace("November", "november").replace("December", "december")
    except Exception:
        date_dk = date_iso[:10]

    # JSON-LD Schema
    schema_article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical
        },
        "headline": title,
        "description": excerpt,
        "image": [img_abs],
        "datePublished": date_iso,
        "dateModified": mod_iso,
        "author": {
            "@type": "Person",
            "name": "Klaus Kryger",
            "url": f"{DOMAIN}/"
        },
        "publisher": {
            "@type": "Organization",
            "name": "VinVerdenenRundt",
            "logo": {
                "@type": "ImageObject",
                "url": f"{DOMAIN}/images/AOC_winemag.png"
            }
        },
        "articleSection": cat,
        "keywords": ", ".join(tags)
    }

    schema_breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Forside",
                "item": f"{DOMAIN}/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": cat,
                "item": f"{DOMAIN}/#cat-{cat.lower()}"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": canonical
            }
        ]
    }

    related_html = ""
    for r in related:
        r_img = r.get("image") or "/images/italien-vin.jpg"
        related_html += f"""
        <a href="/{r['slug']}/" class="related-card">
            <div class="related-img-wrap">
                <img src="{r_img}" alt="{r['title']}" loading="lazy">
            </div>
            <div class="related-body">
                <span class="related-cat">{r.get('category', 'Vin')}</span>
                <h4 class="related-title">{r['title']}</h4>
            </div>
        </a>
        """

    tag_pills = "".join([f'<span class="tag-pill">#{t}</span>' for t in tags[:6]])

    return f"""<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — VinVerdenenRundt</title>
    <meta name="description" content="{excerpt[:155]}...">
    <link rel="canonical" href="{canonical}">
    
    <!-- Cache control & PWA -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    
    <!-- OpenGraph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{img_abs}">
    <meta property="og:site_name" content="VinVerdenenRundt">
    <meta property="article:published_time" content="{date_iso}">
    <meta property="article:section" content="{cat}">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{excerpt}">
    <meta name="twitter:image" content="{img_abs}">

    <!-- Schema.org JSON-LD -->
    <script type="application/ld+json">
    {json.dumps(schema_article, ensure_ascii=False, indent=2)}
    </script>
    <script type="application/ld+json">
    {json.dumps(schema_breadcrumbs, ensure_ascii=False, indent=2)}
    </script>

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400;1,600&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-page: #FAF8F5;
            --bg-card: #FFFFFF;
            --bg-card-subtle: #F4EFEA;
            --border: #E8DFD5;
            --border-hover: #C5A059;
            --wine-primary: #691724;
            --wine-dark: #3F0D15;
            --gold: #C5A059;
            --gold-light: #EADBBE;
            --text-main: #241E19;
            --text-muted: #6B6259;
            --text-dim: #998E84;
            --shadow-sm: 0 2px 8px rgba(36, 30, 25, 0.04);
            --shadow-md: 0 8px 24px rgba(36, 30, 25, 0.08);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-page);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
        }}

        .topbar {{
            background: var(--wine-dark);
            color: var(--gold-light);
            font-size: 0.8rem;
            text-align: center;
            padding: 7px 16px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 100%;
        }}
        .reload-btn {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            margin-right: 12px;
        }}

        header {{
            background: rgba(250, 248, 245, 0.95);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(8px);
        }}
        .nav-container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .brand {{
            display: flex;
            flex-direction: column;
            text-decoration: none;
            color: var(--wine-dark);
        }}
        .brand-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.6rem;
            font-weight: 900;
        }}
        .brand-title span {{ color: var(--gold); }}
        .btn-back {{
            color: var(--wine-primary);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 6px;
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }}
        .btn-back:hover {{
            background: var(--wine-primary);
            color: #fff;
            border-color: var(--wine-primary);
        }}

        .article-container {{
            max-width: 860px;
            margin: 40px auto 80px;
            padding: 0 24px;
        }}

        .breadcrumbs {{
            font-size: 0.85rem;
            color: var(--text-dim);
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .breadcrumbs a {{
            color: var(--text-muted);
            text-decoration: none;
        }}
        .breadcrumbs a:hover {{
            color: var(--wine-primary);
        }}

        .article-header {{
            margin-bottom: 32px;
        }}
        .cat-badge {{
            display: inline-block;
            background: var(--wine-dark);
            color: var(--gold-light);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            padding: 5px 12px;
            border-radius: 4px;
            margin-bottom: 16px;
        }}
        .article-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.75rem;
            line-height: 1.2;
            color: var(--wine-dark);
            margin-bottom: 20px;
            font-weight: 900;
        }}
        .article-meta {{
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 0.9rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 28px;
        }}
        .author-box {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .author-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--wine-primary);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
        }}

        .hero-img-wrap {{
            margin: 0 -24px 36px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            background: #2a201c;
        }}
        .hero-img {{
            width: 100%;
            max-height: 480px;
            object-fit: cover;
            display: block;
        }}

        .article-body {{
            font-size: 1.12rem;
            line-height: 1.85;
            color: var(--text-main);
        }}
        .article-body h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.85rem;
            color: var(--wine-dark);
            margin: 44px 0 16px;
            line-height: 1.3;
        }}
        .article-body h3 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.4rem;
            color: var(--wine-primary);
            margin: 32px 0 14px;
        }}
        .article-body p {{
            margin-bottom: 24px;
        }}
        .article-body ul, .article-body ol {{
            margin: 0 0 24px 28px;
        }}
        .article-body li {{
            margin-bottom: 8px;
        }}
        .article-body blockquote {{
            border-left: 3px solid var(--gold);
            padding: 12px 24px;
            margin: 28px 0;
            background: var(--bg-card-subtle);
            font-style: italic;
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            color: var(--wine-dark);
        }}
        .article-body img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 32px 0;
            box-shadow: var(--shadow-sm);
        }}
        .article-body a {{
            color: var(--wine-primary);
            text-decoration: underline;
        }}

        .tags-section {{
            margin: 48px 0;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .tag-pill {{
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 600;
        }}

        /* Related Section */
        .related-section {{
            margin-top: 64px;
            padding-top: 48px;
            border-top: 2px solid var(--border);
        }}
        .related-heading {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.7rem;
            color: var(--wine-dark);
            margin-bottom: 24px;
        }}
        .related-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 20px;
        }}
        .related-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            transition: all 0.25s ease;
            box-shadow: var(--shadow-sm);
        }}
        .related-card:hover {{
            transform: translateY(-4px);
            border-color: var(--gold);
            box-shadow: var(--shadow-md);
        }}
        .related-img-wrap {{
            height: 140px;
            overflow: hidden;
            background: #2a201c;
        }}
        .related-img-wrap img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .related-body {{
            padding: 16px;
        }}
        .related-cat {{
            font-size: 0.72rem;
            color: var(--wine-primary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .related-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.05rem;
            margin-top: 6px;
            line-height: 1.35;
            color: var(--wine-dark);
        }}

        footer {{
            background: #1C070B;
            color: #d1c0be;
            padding: 48px 24px;
            border-top: 3px solid var(--gold);
            text-align: center;
            font-size: 0.88rem;
        }}
        footer a {{ color: var(--gold-light); text-decoration: none; }}

        @media (max-width: 768px) {{
            .article-title {{ font-size: 2rem; }}
            .hero-img-wrap {{ margin: 0 0 24px; border-radius: 8px; }}
            .article-container {{ padding: 0 16px; margin: 24px auto 60px; }}
        }}
    </style>
</head>
<body>
    <div class="topbar">
        <div style="flex:1"></div>
        <div>Dansk vinmagasin & terroir-guide</div>
        <div style="flex:1; text-align:right">
            <button class="reload-btn" onclick="location.reload(true)" title="Tving genindlæsning">🔄 Opdater</button>
        </div>
    </div>

    <header>
        <div class="nav-container">
            <a href="/" class="brand">
                <div class="brand-title">VinVerdenen<span>Rundt</span></div>
            </a>
            <a href="/" class="btn-back">← Tilbage til magasinet</a>
        </div>
    </header>

    <main class="article-container">
        <nav class="breadcrumbs">
            <a href="/">Forside</a>
            <span>/</span>
            <a href="/#{cat.lower()}">{cat}</a>
            <span>/</span>
            <span>{title}</span>
        </nav>

        <header class="article-header">
            <span class="cat-badge">{cat}</span>
            <h1 class="article-title">{title}</h1>
            <div class="article-meta">
                <div class="author-box">
                    <div class="author-avatar">KK</div>
                    <span>Af <strong>Klaus Kryger</strong></span>
                </div>
                <span>•</span>
                <time datetime="{date_iso}">{date_dk}</time>
                <span>•</span>
                <span>{read_time} min læsetid</span>
            </div>
        </header>

        <div class="hero-img-wrap">
            <img src="{img_rel}" alt="{title}" class="hero-img" onerror="this.src='/images/italien-vin.jpg'">
        </div>

        <article class="article-body">
            {body_html}
        </article>

        <div class="tags-section">
            <span style="font-weight:700; font-size:0.85rem; color:var(--text-dim);">Emner:</span>
            {tag_pills}
        </div>

        <section class="related-section">
            <h3 class="related-heading">Læs også om samme emne</h3>
            <div class="related-grid">
                {related_html}
            </div>
        </section>
    </main>

    <footer>
        <p>© 2026 VinVerdenenRundt.dk • Skrevet med passion for vinens verden</p>
        <p style="margin-top:8px;"><a href="/">← Gå til forsiden</a></p>
    </footer>
</body>
</html>"""

# Generate 158 individual article pages
sitemap_urls = [
    {
        "loc": f"{DOMAIN}/",
        "lastmod": BUILD_TIME[:10],
        "changefreq": "daily",
        "priority": "1.0"
    }
]

md_converter = markdown.Markdown(extensions=["extra", "nl2br", "sane_lists"])

for idx, art in enumerate(articles, start=1):
    slug = art["slug"]
    raw_md = get_article_data(slug)
    
    # Fix inline image paths in markdown
    raw_md = re.sub(r"https://vinverdenenrundt\.dk/wp-content/uploads/\d{4}/\d{2}/([^)\s]+)", r"/images/\1", raw_md)
    
    body_html = md_converter.convert(raw_md)
    # Article template already owns the single H1. Convert legacy markdown H1s
    # to H2s so imported articles do not create duplicate H1 elements.
    body_html = re.sub(r"<h1(\\s[^>]*)?>(.*?)</h1>", r"<h2\\1>\\2</h2>", body_html, flags=re.IGNORECASE | re.DOTALL)
    
    # Reset markdown converter state
    md_converter.reset()
    
    related = get_related(art, articles, count=3)
    page_html = render_article_page(art, body_html, related)
    
    # Write to /public/<slug>/index.html for clean URL mapping
    article_dir = os.path.join(PUBLIC_DIR, slug)
    os.makedirs(article_dir, exist_ok=True)
    with open(os.path.join(article_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page_html)

    # Also add to sitemap
    art_date = (art.get("date") or BUILD_TIME)[:10]
    sitemap_urls.append({
        "loc": f"{DOMAIN}/{slug}/",
        "lastmod": art_date,
        "changefreq": "monthly",
        "priority": "0.8"
    })

    if idx % 30 == 0 or idx == len(articles):
        print(f"  [{idx}/{len(articles)}] Genereret: /{slug}/")

print("\n🗺️  Genererer sitemap.xml og robots.txt...")

# Preserve inbound links after cleaning legacy emoji-based slugs.
LEGACY_REDIRECTS = {
    "udforsk-vin-fra-det-sydlige-rhone-en-rejse-gennem-solskin-og-smag-%f0%9f%8c%9e%f0%9f%8d%87": "udforsk-vin-fra-det-sydlige-rhone-en-rejse-gennem-solskin-og-smag",
    "mclaren-vale-vin-magi-en-dybdegaaende-guide-til-topvine-og-historien-bag-australiens-vinparadis-%f0%9f%8d%87%f0%9f%8c%8f": "mclaren-vale-vin-magi-en-dybdegaaende-guide-til-topvine-og-historien-bag-australiens-vinparadis",
    "%f0%9f%8d%b7-alternativer-vin-til-jule-middagen-de-skjulte-julevine-fra-syd-%f0%9f%8d%87": "alternativer-vin-til-jule-middagen-de-skjulte-julevine-fra-syd",
}
for old_slug, new_slug in LEGACY_REDIRECTS.items():
    alias_dir = os.path.join(PUBLIC_DIR, old_slug)
    os.makedirs(alias_dir, exist_ok=True)
    redirect_html = f'''<!doctype html>
<html lang="da"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0;url=/{new_slug}/">
<link rel="canonical" href="{DOMAIN}/{new_slug}/">
<title>Side flyttet — VinVerdenenRundt</title>
</head><body><p>Siden er flyttet. <a href="/{new_slug}/">Gå til artiklen</a>.</p></body></html>'''
    with open(os.path.join(alias_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(redirect_html)

# Generate sitemap.xml
sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sitemap_urls:
    sitemap_xml.append(f"""  <url>
    <loc>{u['loc']}</loc>
    <lastmod>{u['lastmod']}</lastmod>
    <changefreq>{u['changefreq']}</changefreq>
    <priority>{u['priority']}</priority>
  </url>""")
sitemap_xml.append('</urlset>')

sitemap_path = os.path.join(PUBLIC_DIR, "sitemap.xml")
with open(sitemap_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap_xml))

# Generate robots.txt
robots_txt = f"""# Robots.txt for VinVerdenenRundt.dk
User-agent: *
Allow: /

# Explicit AI Search Crawlers (GEO / Generative Engine Optimization)
User-agent: Googlebot
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Applebot
Allow: /

User-agent: bingbot
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""

robots_path = os.path.join(PUBLIC_DIR, "robots.txt")
with open(robots_path, "w", encoding="utf-8") as f:
    f.write(robots_txt)

# Generate version.json
version_data = {
    "version": BUILD_VERSION,
    "build_time": BUILD_TIME,
    "article_count": len(articles)
}
with open(os.path.join(PUBLIC_DIR, "version.json"), "w", encoding="utf-8") as f:
    json.dump(version_data, f, indent=2)

print("✅ Trin 1 & 2 fuldført!")
print(f"  • {len(articles)} individuelle SEO-sider genereret i /public/<slug>/index.html")
print(f"  • sitemap.xml oprettet med {len(sitemap_urls)} URL'er")
print("  • robots.txt oprettet med AI-crawler adgang (GEO-optimeret)")
print("  • version.json oprettet til cache-busting")
