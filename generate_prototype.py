import json
import os
import glob
import re

BASE_DIR = "/Users/agenten/vinverdenenrundt"
DATA_FILE = os.path.join(BASE_DIR, "data", "articles_index.json")
ARTICLES_DIR = os.path.join(BASE_DIR, "content", "articles")
OUTPUT_HTML = os.path.join(BASE_DIR, "public", "index.html")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Sort by date descending
articles.sort(key=lambda x: x.get("date", ""), reverse=True)

# Preload full content into a small lookup for modal reading
content_lookup = {}
for a in articles:
    slug = a["slug"]
    md_file = os.path.join(ARTICLES_DIR, f"{slug}.md")
    if os.path.exists(md_file):
        with open(md_file, "r", encoding="utf-8") as f:
            raw = f.read()
            # Split frontmatter
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                body = parts[2].strip()
                content_lookup[slug] = body
            else:
                content_lookup[slug] = a.get("excerpt", "")

# Tag categorizations
REGIONS = [
    {"name": "Piemonte", "tag": "piemonte", "desc": "Barolo, Barbaresco & Nebbiolo", "image": "/images/Piemonte.jpeg"},
    {"name": "Bourgogne", "tag": "Bourgogne", "desc": "Pinot Noir & Chardonnay i verdensklasse", "image": "/images/Bourgogne-jpg.webp"},
    {"name": "Champagne", "tag": "Champagne", "desc": "Grand Cru landsbyer, Meunier & Blanc de Blancs", "image": "/images/ay-champagne-1024x425.webp"},
    {"name": "Toscana", "tag": "chianti", "desc": "Chianti Classico, Brunello & Supertoscanere", "image": "/images/Toscana-jpg.webp"},
    {"name": "Rhône", "tag": "cotes du rhone", "desc": "Nordlig Syrah & Sydlig Grenache", "image": "/images/Rhone-Guigal--jpg.webp"},
    {"name": "Mosel & Tyskland", "tag": "riesling", "desc": "Stejle skiferskrænter & mineralsk Riesling", "image": "/images/i-mosel-er-riesling-kongen-duu.jpg"},
    {"name": "Rioja & Ribera", "tag": "ribera", "desc": "Spaniens stolte Tempranillo-ikoner", "image": "/images/RIOJA.png"}
]

DRAPES = [
    {"name": "Pinot Noir", "tag": "pinot noir", "color": "#7D1D2C"},
    {"name": "Nebbiolo", "tag": "nebbiolo", "color": "#631322"},
    {"name": "Champagne / Bobler", "tag": "Champagne", "color": "#C5A059"},
    {"name": "Chardonnay", "tag": "chardonnay", "color": "#B88E3E"},
    {"name": "Cabernet Sauvignon", "tag": "Cabernet Sauvignon", "color": "#4A0E17"},
    {"name": "Riesling", "tag": "riesling", "color": "#3A6351"},
    {"name": "Syrah / Shiraz", "tag": "syrah", "color": "#3B1124"}
]

html_template = f"""<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VinVerdenenRundt — Magasinet om vin, terroir og gastronomi</title>
    <!-- Cache control & PWA -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#3F0D15">
    
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
            --wine-light: #8E2333;
            --gold: #C5A059;
            --gold-light: #EADBBE;
            --text-main: #241E19;
            --text-muted: #6B6259;
            --text-dim: #998E84;
            --shadow-sm: 0 2px 8px rgba(36, 30, 25, 0.04);
            --shadow-md: 0 8px 24px rgba(36, 30, 25, 0.08);
            --shadow-lg: 0 16px 40px rgba(63, 13, 21, 0.12);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-page);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        /* Header & Top Bar */
        .topbar {{
            background: var(--wine-dark);
            color: var(--gold-light);
            font-size: 0.8rem;
            text-align: center;
            padding: 7px 16px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
        }}

        header {{
            background: var(--bg-page);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(8px);
            background-color: rgba(250, 248, 245, 0.94);
        }}

        .nav-container {{
            max-width: 1300px;
            margin: 0 auto;
            padding: 18px 24px;
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
            font-size: 1.85rem;
            font-weight: 900;
            letter-spacing: -0.01em;
            line-height: 1;
        }}

        .brand-title span {{
            color: var(--gold);
        }}

        .brand-subtitle {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            font-size: 0.95rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-top: 4px;
            font-style: italic;
        }}

        .nav-links {{
            display: flex;
            gap: 28px;
            list-style: none;
        }}

        .nav-links a {{
            text-decoration: none;
            color: var(--text-main);
            font-size: 0.92rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            transition: color 0.2s ease;
            position: relative;
            padding-bottom: 4px;
        }}

        .nav-links a:hover {{
            color: var(--wine-primary);
        }}

        .nav-links a.active {{
            color: var(--wine-primary);
        }}

        .nav-links a.active::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--gold);
        }}

        .main-container {{
            max-width: 1300px;
            margin: 0 auto;
            padding: 32px 24px 80px;
        }}

        /* Hero Article Section */
        .hero-section {{
            margin-bottom: 48px;
        }}

        .hero-card {{
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            display: grid;
            grid-template-columns: 1.25fr 1fr;
            box-shadow: var(--shadow-md);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
        }}

        .hero-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--border-hover);
        }}

        .hero-image-wrap {{
            position: relative;
            min-height: 440px;
            overflow: hidden;
            background: #2a201c;
        }}

        .hero-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.6s ease;
        }}

        .hero-card:hover .hero-image {{
            transform: scale(1.03);
        }}

        .hero-badge {{
            position: absolute;
            top: 24px;
            left: 24px;
            background: var(--wine-dark);
            color: var(--gold-light);
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        .hero-content {{
            padding: 48px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .meta-line {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 16px;
            font-weight: 500;
        }}

        .meta-pill {{
            color: var(--wine-primary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
        }}

        .hero-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2.35rem;
            font-weight: 900;
            line-height: 1.2;
            color: var(--wine-dark);
            margin-bottom: 18px;
        }}

        .hero-excerpt {{
            font-size: 1.05rem;
            color: var(--text-muted);
            line-height: 1.65;
            margin-bottom: 28px;
        }}

        .btn-read {{
            align-self: flex-start;
            background: var(--wine-primary);
            color: #ffffff;
            padding: 13px 28px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.92rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s ease, transform 0.2s ease;
        }}

        .btn-read:hover {{
            background: var(--wine-dark);
            transform: translateX(4px);
        }}

        /* Search & Filter Bar */
        .search-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 28px 32px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 48px;
        }}

        .search-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }}

        .search-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--wine-dark);
        }}

        .article-count-badge {{
            font-size: 0.82rem;
            color: var(--gold);
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 700;
        }}

        .search-input-wrap {{
            position: relative;
            margin-bottom: 22px;
        }}

        .search-input {{
            width: 100%;
            padding: 16px 20px 16px 52px;
            font-size: 1.05rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-page);
            color: var(--text-main);
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            font-family: inherit;
        }}

        .search-input:focus {{
            border-color: var(--gold);
            box-shadow: 0 0 0 3px rgba(197, 160, 89, 0.2);
            background: #ffffff;
        }}

        .search-icon {{
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            font-size: 1.2rem;
        }}

        .filter-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}

        .filter-label {{
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-dim);
            margin-right: 6px;
        }}

        .filter-btn {{
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 7px 16px;
            border-radius: 20px;
            font-size: 0.84rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .filter-btn:hover {{
            background: var(--border);
            color: var(--wine-dark);
        }}

        .filter-btn.active {{
            background: var(--wine-primary);
            color: #ffffff;
            border-color: var(--wine-primary);
        }}

        /* Article Magazine Grid */
        .grid-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 28px;
            border-bottom: 2px solid var(--border);
            padding-bottom: 12px;
        }}

        .grid-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.85rem;
            font-weight: 800;
            color: var(--wine-dark);
        }}

        .grid-subtitle {{
            font-size: 0.9rem;
            color: var(--text-muted);
            font-style: italic;
        }}

        .article-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(370px, 1fr));
            gap: 32px;
            margin-bottom: 32px;
        }}

        .load-more-wrap {{
            text-align: center;
            margin: 32px 0 64px;
        }}

        .btn-load-more {{
            background: var(--bg-card);
            border: 2px solid var(--gold);
            color: var(--wine-dark);
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 0.95rem;
            font-weight: 700;
            padding: 14px 36px;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.25s ease;
            box-shadow: var(--shadow-sm);
        }}

        .btn-load-more:hover {{
            background: var(--wine-primary);
            color: #ffffff;
            border-color: var(--wine-primary);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }}

        .article-card {{
            background: var(--bg-card);
            border-radius: 10px;
            border: 1px solid var(--border);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: var(--shadow-sm);
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
            cursor: pointer;
        }}

        .article-card:hover {{
            transform: translateY(-5px);
            box-shadow: var(--shadow-md);
            border-color: var(--gold);
        }}

        .card-image-wrap {{
            position: relative;
            height: 220px;
            overflow: hidden;
            background: #2a201c;
        }}

        .card-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.4s ease;
        }}

        .article-card:hover .card-image {{
            transform: scale(1.05);
        }}

        .card-badge {{
            position: absolute;
            top: 14px;
            left: 14px;
            background: rgba(63, 13, 21, 0.9);
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .card-body {{
            padding: 24px;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-bottom: 12px;
            font-weight: 500;
        }}

        .card-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.3;
            color: var(--wine-dark);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .card-excerpt {{
            font-size: 0.92rem;
            color: var(--text-muted);
            line-height: 1.55;
            margin-bottom: 20px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            flex-grow: 1;
        }}

        .card-footer {{
            border-top: 1px solid var(--border);
            padding-top: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .read-more-link {{
            color: var(--wine-primary);
            font-size: 0.85rem;
            font-weight: 700;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .read-time {{
            font-size: 0.78rem;
            color: var(--text-dim);
        }}

        /* Regions Carousel & Wine Explorer */
        .regions-section {{
            background: linear-gradient(180deg, #3F0D15 0%, #29080E 100%);
            border-radius: 16px;
            padding: 48px 40px;
            color: #ffffff;
            margin-bottom: 64px;
            box-shadow: var(--shadow-lg);
        }}

        .regions-header {{
            text-align: center;
            max-width: 650px;
            margin: 0 auto 36px;
        }}

        .regions-tag {{
            color: var(--gold);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        .regions-title {{
            font-family: 'Playfair Display', serif;
            font-size: 2.2rem;
            font-weight: 900;
            color: #ffffff;
            margin-bottom: 12px;
        }}

        .regions-desc {{
            color: #d1c0be;
            font-size: 0.95rem;
        }}

        .regions-carousel {{
            display: flex;
            gap: 20px;
            overflow-x: auto;
            padding-bottom: 18px;
            scroll-snap-type: x mandatory;
            scrollbar-width: thin;
            scrollbar-color: var(--gold) rgba(255,255,255,0.1);
        }}

        .region-card {{
            flex: 0 0 280px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 10px;
            overflow: hidden;
            scroll-snap-align: start;
            cursor: pointer;
            transition: transform 0.25s, border-color 0.25s, background 0.25s;
        }}

        .region-card:hover {{
            transform: translateY(-4px);
            border-color: var(--gold);
            background: rgba(255, 255, 255, 0.15);
        }}

        .region-img-wrap {{
            height: 150px;
            overflow: hidden;
            position: relative;
        }}

        .region-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .region-info {{
            padding: 18px;
        }}

        .region-name {{
            font-family: 'Playfair Display', serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--gold-light);
            margin-bottom: 6px;
        }}

        .region-desc-short {{
            font-size: 0.82rem;
            color: #e2d7d5;
            line-height: 1.45;
        }}

        /* Article Reading Modal */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(20, 10, 12, 0.85);
            backdrop-filter: blur(8px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            padding: 24px;
        }}

        .modal-overlay.open {{
            display: flex;
        }}

        .modal-box {{
            background: var(--bg-card);
            width: 100%;
            max-width: 860px;
            max-height: 90vh;
            border-radius: 12px;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border);
        }}

        .modal-close {{
            position: sticky;
            top: 18px;
            float: right;
            margin-right: 18px;
            z-index: 10;
            background: var(--bg-card-subtle);
            border: 1px solid var(--border);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            cursor: pointer;
            color: var(--wine-dark);
            box-shadow: var(--shadow-sm);
        }}

        .modal-hero-img {{
            width: 100%;
            max-height: 380px;
            object-fit: cover;
        }}

        .modal-content-area {{
            padding: 48px;
        }}

        .modal-meta {{
            display: flex;
            gap: 16px;
            align-items: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 14px;
        }}

        .modal-title {{
            font-family: 'Playfair Display', serif;
            font-size: 2.4rem;
            font-weight: 900;
            line-height: 1.25;
            color: var(--wine-dark);
            margin-bottom: 28px;
        }}

        .modal-article-body {{
            font-size: 1.1rem;
            line-height: 1.8;
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}

        .modal-article-body h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.7rem;
            color: var(--wine-dark);
            margin: 36px 0 16px;
        }}

        .modal-article-body h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.35rem;
            color: var(--wine-primary);
            margin: 28px 0 12px;
        }}

        .modal-article-body p {{
            margin-bottom: 20px;
        }}

        .modal-article-body a {{
            color: var(--wine-primary);
            text-decoration: underline;
        }}

        .modal-article-body img {{
            max-width: 100%;
            border-radius: 8px;
            margin: 24px 0;
        }}

        footer {{
            background: #1C070B;
            color: #d1c0be;
            padding: 64px 24px 36px;
            border-top: 3px solid var(--gold);
        }}

        .footer-grid {{
            max-width: 1300px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 48px;
            margin-bottom: 48px;
        }}

        .footer-brand {{
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            font-weight: 900;
            color: #ffffff;
            margin-bottom: 14px;
        }}

        .footer-text {{
            font-size: 0.9rem;
            line-height: 1.65;
            color: #b5a4a2;
        }}

        .footer-col-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.15rem;
            color: var(--gold-light);
            margin-bottom: 16px;
            font-weight: 700;
        }}

        .footer-links {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .footer-links a {{
            color: #d1c0be;
            text-decoration: none;
            font-size: 0.88rem;
            transition: color 0.2s;
        }}

        .footer-links a:hover {{
            color: var(--gold);
        }}

        .footer-bottom {{
            max-width: 1300px;
            margin: 0 auto;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 24px;
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #887877;
        }}

        @media (max-width: 900px) {{
            .hero-card {{
                grid-template-columns: 1fr;
            }}
            .hero-image-wrap {{
                min-height: 260px;
            }}
            .hero-content {{
                padding: 28px;
            }}
            .hero-title {{
                font-size: 1.8rem;
            }}
            .article-grid {{
                grid-template-columns: 1fr;
            }}
            .footer-grid {{
                grid-template-columns: 1fr;
                gap: 32px;
            }}
            .nav-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>

    <div class="topbar">
        <div style="flex:1"></div>
        <div>Dansk vinmagasin & terroir-guide • 158 artikler om vinens verden</div>
        <div style="flex:1; text-align:right">
            <button onclick="location.reload(true)" style="background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25); color:#fff; padding:3px 10px; border-radius:4px; font-size:0.75rem; cursor:pointer;" title="Tving genindlæsning">🔄 Opdater</button>
        </div>
    </div>

    <header>
        <div class="nav-container">
            <a href="#" class="brand">
                <div class="brand-title">VinVerdenen<span>Rundt</span></div>
                <div class="brand-subtitle">Terroir • Tradition • Smag</div>
            </a>
            <ul class="nav-links">
                <li><a href="#" class="nav-link-item active" data-filter="all" onclick="filterCategory('all'); return false;">Forside</a></li>
                <li><a href="#" class="nav-link-item" data-filter="tag:Bourgogne" onclick="filterByTag('Bourgogne'); return false;">Bourgogne</a></li>
                <li><a href="#" class="nav-link-item" data-filter="tag:Champagne" onclick="filterByTag('Champagne'); return false;">Champagne</a></li>
                <li><a href="#" class="nav-link-item" data-filter="tag:piemonte" onclick="filterByTag('piemonte'); return false;">Piemonte</a></li>
                <li><a href="#" class="nav-link-item" data-filter="tag:chianti" onclick="filterByTag('chianti'); return false;">Toscana</a></li>
                <li><a href="#" class="nav-link-item" data-filter="tag:riesling" onclick="filterByTag('riesling'); return false;">Riesling & Tyskland</a></li>
                <li><a href="#" class="nav-link-item" data-filter="Mad & Vin" onclick="filterCategory('Mad & Vin'); return false;">Mad & Vin</a></li>
            </ul>
        </div>
    </header>

    <main class="main-container">

        <!-- HERO SECTION -->
        <section class="hero-section" id="heroArea">
            <!-- Dynamically populated or static top story -->
        </section>

        <!-- SEARCH & FILTER BAR -->
        <section class="search-section">
            <div class="search-header">
                <h2 class="search-title">Udforsk Vinsamlingen</h2>
                <div class="article-count-badge" id="articleCountBadge">Viser 158 artikler</div>
            </div>

            <div class="search-input-wrap">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" class="search-input" placeholder="Søg efter drue (fx Pinot Noir), distrikt (fx Barolo, Chianti), madret eller vinmager...">
            </div>

            <div class="filter-tags">
                <span class="filter-label">Filtre:</span>
                <button class="filter-btn active" onclick="filterCategory('all', this)">Alle (158)</button>
                <button class="filter-btn" onclick="filterCategory('Rødvin', this)">Rødvin</button>
                <button class="filter-btn" onclick="filterCategory('Hvidvin', this)">Hvidvin</button>
                <button class="filter-btn" onclick="filterByTag('Champagne', this)">Champagne / Bobler</button>
                <button class="filter-btn" onclick="filterByTag('pinot noir', this)">Pinot Noir</button>
                <button class="filter-btn" onclick="filterByTag('nebbiolo', this)">Nebbiolo / Barolo</button>
                <button class="filter-btn" onclick="filterByTag('riesling', this)">Riesling</button>
                <button class="filter-btn" onclick="filterCategory('Mad & Vin', this)">Mad & Vin</button>
            </div>
        </section>

        <!-- ARTICLE GRID -->
        <section>
            <div class="grid-header">
                <div>
                    <h3 class="grid-title" id="gridTitle">Seneste Vinartikler</h3>
                    <div class="grid-subtitle">Dybdegående artikler om vinens store og små hemmeligheder</div>
                </div>
            </div>

            <div class="article-grid" id="articleGrid">
                <!-- Artikler indsættes med JS -->
            </div>

            <div class="load-more-wrap" id="loadMoreContainer"></div>
        </section>

        <!-- REGIONS CAROUSEL -->
        <section class="regions-section">
            <div class="regions-header">
                <div class="regions-tag">Vinrejser & Terroir</div>
                <h3 class="regions-title">Gå på Opdagelse i Regionerne</h3>
                <p class="regions-desc">Klik på en region for at udforske alle artikler, historier og smagsnoter fra netop det område.</p>
            </div>

            <div class="regions-carousel">
                {''.join([f'''
                <div class="region-card" onclick="filterByTag('{r["tag"]}')">
                    <div class="region-img-wrap">
                        <img src="{r["image"]}" alt="{r["name"]}" class="region-img" onerror="this.src='/images/italien-vin.jpg'">
                    </div>
                    <div class="region-info">
                        <div class="region-name">{r["name"]}</div>
                        <div class="region-desc-short">{r["desc"]}</div>
                    </div>
                </div>
                ''' for r in REGIONS])}
            </div>
        </section>

    </main>

    <!-- ARTICLE MODAL -->
    <div class="modal-overlay" id="articleModal" onclick="closeModal(event)">
        <div class="modal-box" onclick="event.stopPropagation()">
            <button class="modal-close" onclick="closeModalDirect()">✕</button>
            <img src="" id="modalImg" class="modal-hero-img" alt="">
            <div class="modal-content-area">
                <div class="modal-meta">
                    <span id="modalCat" class="meta-pill"></span>
                    <span id="modalDate"></span>
                </div>
                <h1 id="modalTitle" class="modal-title"></h1>
                <div id="modalBody" class="modal-article-body"></div>
            </div>
        </div>
    </div>

    <footer>
        <div class="footer-grid">
            <div>
                <div class="footer-brand">VinVerdenenRundt</div>
                <p class="footer-text">
                    Et personligt, uafhængigt vinmagasin med fokus på terroirets magi, druernes karakter, de passionerede vinbønder og mad- og vinparringer. Fra de store klassikere i Bourgogne og Barolo til oversete perler.
                </p>
            </div>
            <div>
                <div class="footer-col-title">Populære Druer</div>
                <ul class="footer-links">
                    <li><a href="#" onclick="filterByTag('pinot noir'); return false;">Pinot Noir</a></li>
                    <li><a href="#" onclick="filterByTag('nebbiolo'); return false;">Nebbiolo</a></li>
                    <li><a href="#" onclick="filterByTag('riesling'); return false;">Riesling</a></li>
                    <li><a href="#" onclick="filterByTag('chardonnay'); return false;">Chardonnay</a></li>
                    <li><a href="#" onclick="filterByTag('syrah'); return false;">Syrah / Shiraz</a></li>
                </ul>
            </div>
            <div>
                <div class="footer-col-title">Klassiske Regioner</div>
                <ul class="footer-links">
                    <li><a href="#" onclick="filterByTag('Bourgogne'); return false;">Bourgogne</a></li>
                    <li><a href="#" onclick="filterByTag('Champagne'); return false;">Champagne</a></li>
                    <li><a href="#" onclick="filterByTag('piemonte'); return false;">Piemonte & Langhe</a></li>
                    <li><a href="#" onclick="filterByTag('chianti'); return false;">Toscana & Chianti</a></li>
                    <li><a href="#" onclick="filterByTag('mosel'); return false;">Mosel & Rheingau</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <div>© 2026 VinVerdenenRundt.dk • Udviklet med kærlighed til god vin</div>
            <div>158 artikler bevaret & optimeret</div>
        </div>
    </footer>

    <!-- INLINE DATA & SCRIPTS -->
    <script>
        const articles = {json.dumps(articles, ensure_ascii=False)};
        const contentLookup = {json.dumps(content_lookup, ensure_ascii=False)};

        const PAGE_SIZE = 18;
        let visibleCount = PAGE_SIZE;
        let currentFilter = 'all';
        let currentSearch = '';

        function renderHero() {{
            const heroArticle = articles[0]; // Nyeste artikel
            if (!heroArticle) return;

            const dateStr = new Date(heroArticle.date).toLocaleDateString('da-DK', {{ day: 'numeric', month: 'long', year: 'numeric' }});
            const imgUrl = heroArticle.image || '/images/italien-vin.jpg';

            document.getElementById('heroArea').innerHTML = `
                <div class="hero-card" onclick="openArticle('${{heroArticle.slug}}')">
                    <div class="hero-image-wrap">
                        <img src="${{imgUrl}}" alt="${{heroArticle.title}}" class="hero-image" onerror="this.src='/images/italien-vin.jpg'">
                        <div class="hero-badge">Fremhævet Artikel</div>
                    </div>
                    <div class="hero-content">
                        <div class="meta-line">
                            <span class="meta-pill">${{heroArticle.category}}</span>
                            <span>•</span>
                            <span>${{dateStr}}</span>
                            <span>•</span>
                            <span>5 min læsetid</span>
                        </div>
                        <h1 class="hero-title">${{heroArticle.title}}</h1>
                        <p class="hero-excerpt">${{heroArticle.excerpt}}</p>
                        <a href="javascript:void(0)" class="btn-read">
                            Læs artiklen <span>→</span>
                        </a>
                    </div>
                </div>
            `;
        }}

        function renderArticles() {{
            const grid = document.getElementById('articleGrid');
            const loadMoreContainer = document.getElementById('loadMoreContainer');
            const searchLower = currentSearch.toLowerCase().trim();

            const filtered = articles.slice(1).filter(a => {{
                // Kategori/Tag filter
                let matchesCategory = false;
                if (currentFilter === 'all') {{
                    matchesCategory = true;
                }} else if (currentFilter.startsWith('tag:')) {{
                    const targetTag = currentFilter.replace('tag:', '').toLowerCase();
                    const hasTag = (a.tags || []).some(t => t.toLowerCase().includes(targetTag));
                    const inTitle = a.title.toLowerCase().includes(targetTag);
                    const inCategory = (a.category || '').toLowerCase().includes(targetTag);
                    matchesCategory = hasTag || inTitle || inCategory;
                }} else if (currentFilter === 'Mad & Vin') {{
                    matchesCategory = a.title.toLowerCase().includes('mad') || 
                                      a.title.toLowerCase().includes('menu') || 
                                      a.title.toLowerCase().includes('parring') ||
                                      a.title.toLowerCase().includes('lam') ||
                                      a.title.toLowerCase().includes('jul');
                }} else {{
                    matchesCategory = (a.category || '').toLowerCase() === currentFilter.toLowerCase();
                }}

                if (!matchesCategory) return false;

                // Søgning
                if (searchLower) {{
                    const inTitle = a.title.toLowerCase().includes(searchLower);
                    const inExcerpt = (a.excerpt || '').toLowerCase().includes(searchLower);
                    const inTags = (a.tags || []).some(t => t.toLowerCase().includes(searchLower));
                    const inCategory = (a.category || '').toLowerCase().includes(searchLower);
                    return inTitle || inExcerpt || inTags || inCategory;
                }}

                return true;
            }});

            document.getElementById('articleCountBadge').innerText = `Viser ${{Math.min(visibleCount, filtered.length)}} af ${{filtered.length}} artikler`;

            if (filtered.length === 0) {{
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: #fff; border-radius: 8px; border: 1px dashed var(--border);">
                        <div style="font-size: 2rem; margin-bottom: 12px;">🍷</div>
                        <h4 style="font-family: 'Playfair Display', serif; font-size: 1.4rem; color: var(--wine-dark); margin-bottom: 8px;">Ingen artikler matchede søgningen</h4>
                        <p style="color: var(--text-muted); font-size: 0.95rem;">Prøv at søge efter noget andet, eller nulstil filtrene.</p>
                        <button onclick="resetFilters()" style="margin-top: 16px; background: var(--wine-primary); color: #fff; border: none; padding: 8px 18px; border-radius: 6px; cursor: pointer;">Nulstil filtre</button>
                    </div>
                `;
                loadMoreContainer.style.display = 'none';
                return;
            }}

            const visible = filtered.slice(0, visibleCount);

            grid.innerHTML = visible.map(a => {{
                const dateStr = new Date(a.date).toLocaleDateString('da-DK', {{ day: 'numeric', month: 'short', year: 'numeric' }});
                const img = a.image || '/images/italien-vin.jpg';
                return `
                    <article class="article-card" onclick="openArticle('${{a.slug}}')">
                        <div class="card-image-wrap">
                            <img src="${{img}}" alt="${{a.title}}" class="card-image" loading="lazy" onerror="this.src='/images/italien-vin.jpg'">
                            <div class="card-badge">${{a.category}}</div>
                        </div>
                        <div class="card-body">
                            <div class="card-meta">
                                <span>${{dateStr}}</span>
                                <span class="read-time">4 min læsetid</span>
                            </div>
                            <h3 class="card-title">${{a.title}}</h3>
                            <p class="card-excerpt">${{a.excerpt}}</p>
                            <div class="card-footer">
                                <span class="read-more-link">Læs mere →</span>
                                <span style="font-size: 0.75rem; color: var(--gold); font-weight: 600;">${{(a.tags && a.tags[0]) ? '#' + a.tags[0] : ''}}</span>
                            </div>
                        </div>
                    </article>
                `;
            }}).join('');

            // Pagination button
            if (visibleCount < filtered.length) {{
                loadMoreContainer.style.display = 'block';
                loadMoreContainer.innerHTML = `
                    <button class="btn-load-more" onclick="loadMore()">
                        Indlæs flere artikler (${{visible.length}} af ${{filtered.length}}) ↓
                    </button>
                `;
            }} else {{
                loadMoreContainer.style.display = 'none';
            }}
        }}

        function loadMore() {{
            visibleCount += PAGE_SIZE;
            renderArticles();
        }}

        function updateNavLinks(targetFilter) {{
            document.querySelectorAll('.nav-link-item').forEach(link => {{
                if (link.getAttribute('data-filter') === targetFilter) {{
                    link.classList.add('active');
                }} else {{
                    link.classList.remove('active');
                }}
            }});
        }}

        function filterCategory(cat, btn) {{
            currentFilter = cat;
            visibleCount = PAGE_SIZE;
            updateFilterButtons(btn);
            updateNavLinks(cat);
            document.getElementById('gridTitle').innerText = cat === 'all' ? 'Seneste Vinartikler' : `Artikler om ${{cat}}`;
            renderArticles();
        }}

        function filterByTag(tag, btn) {{
            currentFilter = 'tag:' + tag;
            visibleCount = PAGE_SIZE;
            updateFilterButtons(btn);
            updateNavLinks('tag:' + tag);
            document.getElementById('gridTitle').innerText = `Artikler med fokus på ${{tag}}`;
            renderArticles();
            document.querySelector('.search-section').scrollIntoView({{ behavior: 'smooth' }});
        }}

        function updateFilterButtons(activeBtn) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            if (activeBtn) {{
                activeBtn.classList.add('active');
            }}
        }}

        function resetFilters() {{
            currentFilter = 'all';
            currentSearch = '';
            visibleCount = PAGE_SIZE;
            document.getElementById('searchInput').value = '';
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            document.querySelector('.filter-btn').classList.add('active');
            updateNavLinks('all');
            document.getElementById('gridTitle').innerText = 'Seneste Vinartikler';
            renderArticles();
        }}

        document.getElementById('searchInput').addEventListener('input', (e) => {{
            currentSearch = e.target.value;
            visibleCount = PAGE_SIZE;
            renderArticles();
        }});

        function openArticle(slug) {{
            const a = articles.find(x => x.slug === slug);
            if (!a) return;

            document.getElementById('modalTitle').innerText = a.title;
            document.getElementById('modalCat').innerText = a.category;
            document.getElementById('modalDate').innerText = new Date(a.date).toLocaleDateString('da-DK', {{ day: 'numeric', month: 'long', year: 'numeric' }});
            
            const imgEl = document.getElementById('modalImg');
            if (a.image) {{
                imgEl.src = a.image;
                imgEl.style.display = 'block';
            }} else {{
                imgEl.style.display = 'none';
            }}

            const rawContent = contentLookup[slug] || a.excerpt;
            // Simpel markdown til HTML konvertering for modal-læsning
            let formattedHtml = rawContent
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^# (.*$)/gim, '<h2>$1</h2>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\\n\\n/g, '</p><p>')
                .replace(/\\[(.*?)\\]\\((.*?)\\)/g, '<a href="$2" target="_blank">$1</a>');

            document.getElementById('modalBody').innerHTML = '<p>' + formattedHtml + '</p>';
            document.getElementById('articleModal').classList.add('open');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal(e) {{
            if (e.target.id === 'articleModal') {{
                closeModalDirect();
            }}
        }}

        function closeModalDirect() {{
            document.getElementById('articleModal').classList.remove('open');
            document.body.style.overflow = 'auto';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModalDirect();
        }});

        // Init
        renderHero();
        renderArticles();

        // Standard Auto-update & Cache-busting package
        let currentBuildVersion = null;
        async function checkForUpdates() {{
            try {{
                const res = await fetch('/version.json?t=' + Date.now(), {{ cache: 'no-store' }});
                if (!res.ok) return;
                const data = await res.json();
                if (currentBuildVersion && data.version && data.version !== currentBuildVersion) {{
                    showUpdateToast();
                }}
                currentBuildVersion = data.version;
            }} catch (e) {{}}
        }}

        function showUpdateToast() {{
            if (document.getElementById('updateToast')) return;
            const toast = document.createElement('div');
            toast.id = 'updateToast';
            toast.style.cssText = 'position:fixed; bottom:24px; right:24px; background:#3F0D15; color:#fff; border:1px solid #C5A059; padding:16px 22px; border-radius:8px; box-shadow:0 8px 30px rgba(0,0,0,0.3); z-index:9999; display:flex; align-items:center; gap:14px; font-size:0.92rem;';
            toast.innerHTML = '<span>🍷 <strong>Ny opdatering klar!</strong></span><button onclick="location.reload(true)" style="background:#C5A059; color:#241E19; border:none; padding:6px 14px; border-radius:4px; font-weight:700; cursor:pointer;">Opdater nu</button>';
            document.body.appendChild(toast);
        }}

        // Poll on load & visibility change
        checkForUpdates();
        document.addEventListener('visibilitychange', () => {{
            if (document.visibilityState === 'visible') checkForUpdates();
        }});

        // Register Service Worker
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js').catch(() => {{}});
        }}
    </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ Prototype skrevet til: {OUTPUT_HTML}")
