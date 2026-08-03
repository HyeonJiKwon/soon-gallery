#!/usr/bin/env python3
"""Generate a static gallery index.html from data/posts.json."""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "posts.json"
EXCLUDED_IMAGES_PATH = BASE_DIR / "data" / "excluded_images.json"
HOME_OUT_PATH = BASE_DIR / "index.html"
POSTS_OUT_PATH = BASE_DIR / "posts" / "index.html"

BLOG_TITLE = "Gallery of Soon"
BLOG_ID = "khjkes"
NAVER_BLOG_URL = "https://blog.naver.com/khjkes/"
INSTAGRAM_URL = "https://www.instagram.com/goatmom.archive"

FOOTER_HTML = """<footer>
  <a href="{naver_url}" target="_blank" rel="noopener" aria-label="네이버 블로그">
    <svg viewBox="-19.5 0 585 585" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="90" height="585" fill="#03C75A"/>
      <rect x="480" y="0" width="66" height="585" fill="#03C75A"/>
      <circle cx="270" cy="380" r="170" fill="none" stroke="#03C75A" stroke-width="95"/>
    </svg>
  </a>
  <a href="{instagram_url}" target="_blank" rel="noopener" aria-label="인스타그램">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="igGrad" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stop-color="#feda75"/>
          <stop offset="25%" stop-color="#fa7e1e"/>
          <stop offset="50%" stop-color="#d62976"/>
          <stop offset="75%" stop-color="#962fbf"/>
          <stop offset="100%" stop-color="#4f5bd5"/>
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="20" height="20" rx="6" fill="url(#igGrad)"/>
      <circle cx="12" cy="12" r="5" fill="none" stroke="white" stroke-width="1.8"/>
      <circle cx="17.3" cy="6.7" r="1.2" fill="white"/>
    </svg>
  </a>
</footer>""".format(naver_url=NAVER_BLOG_URL, instagram_url=INSTAGRAM_URL)

TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{blog_title}</title>
<style>
  :root {{
    --bg: #faf7f2;
    --card-bg: #ffffff;
    --ink: #2b2622;
    --ink-soft: #6f665c;
    --accent: #c07a4a;
    --border: #e8e0d5;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #1c1a17;
      --card-bg: #262320;
      --ink: #efe9e1;
      --ink-soft: #b3a99b;
      --accent: #e0995f;
      --border: #38332c;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    background: var(--bg);
    color: var(--ink);
  }}
  header {{
    padding: 48px 24px 24px;
    text-align: center;
  }}
  header h1 {{
    margin: 0 0 8px;
    font-size: 2rem;
    letter-spacing: -0.02em;
  }}
  header p {{
    margin: 0;
    color: var(--ink-soft);
    font-size: 0.95rem;
  }}
  header a {{ color: var(--accent); text-decoration: none; }}
  .tabs {{
    display: flex;
    justify-content: center;
    gap: 8px;
    padding: 16px 24px 0;
    flex-wrap: wrap;
  }}
  .tab {{
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--ink-soft);
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 7px 16px;
  }}
  .tab.active {{
    color: #fff;
    background: var(--accent);
    border-color: var(--accent);
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 20px;
    padding: 8px 24px 64px;
    max-width: 1200px;
    margin: 0 auto;
  }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }}
  .card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  }}
  .card .thumb {{
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
    background: var(--border);
  }}
  .card .meta {{
    padding: 12px 14px 16px;
  }}
  .card .meta h3 {{
    margin: 0 0 4px;
    font-size: 1rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .card .meta .date {{
    margin: 0;
    font-size: 0.8rem;
    color: var(--ink-soft);
  }}
  /* modal */
  .overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(20, 16, 12, 0.72);
    z-index: 50;
    padding: 24px;
    overflow-y: auto;
  }}
  .overlay.open {{ display: block; }}
  .modal {{
    background: var(--card-bg);
    max-width: 720px;
    margin: 0 auto;
    border-radius: 16px;
    overflow: hidden;
  }}
  .modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 22px;
    border-bottom: 1px solid var(--border);
  }}
  .modal-header h2 {{
    margin: 0;
    font-size: 1.2rem;
  }}
  .modal-header .close {{
    cursor: pointer;
    font-size: 1.4rem;
    color: var(--ink-soft);
    background: none;
    border: none;
    line-height: 1;
    padding: 4px;
  }}
  .modal-date {{
    padding: 0 22px;
    margin: 10px 0 0;
    font-size: 0.85rem;
    color: var(--ink-soft);
  }}
  .modal-images img {{
    width: 100%;
    display: block;
  }}
  .modal-images {{
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .modal-text {{
    padding: 20px 22px;
    white-space: pre-wrap;
    line-height: 1.7;
    font-size: 0.95rem;
  }}
  .modal-footer {{
    padding: 12px 22px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }}
  .modal-footer a {{
    color: var(--accent);
    font-size: 0.85rem;
    text-decoration: none;
  }}
  .modal-footer .copy-link {{
    cursor: pointer;
    font-size: 0.8rem;
    color: var(--ink-soft);
    background: none;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
  }}
  .modal-footer .copy-link:hover {{
    color: var(--accent);
    border-color: var(--accent);
  }}
  .empty {{
    text-align: center;
    padding: 60px 20px;
    color: var(--ink-soft);
  }}
  footer {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    padding: 32px 24px 48px;
  }}
  footer a {{
    display: inline-flex;
    width: 40px;
    height: 40px;
    transition: transform 0.15s ease;
  }}
  footer a:hover {{ transform: translateY(-2px); }}
  footer svg {{ width: 100%; height: 100%; }}
</style>
</head>
<body>
<header>
  <h1>{blog_title}</h1>
  <p><a href="https://blog.naver.com/{blog_id}" target="_blank" rel="noopener">blog.naver.com/{blog_id}</a> · 총 {post_count}개 게시글 · <a href="../index.html">작품 한눈에 보기 →</a></p>
</header>

<div class="tabs" id="tabs"></div>
<div class="grid" id="grid"></div>
<div class="overlay" id="overlay">
  <div class="modal" id="modal"></div>
</div>

{footer_html}

<script>
const posts = {posts_json};
const categories = {categories_json};
const postsById = {{}};
posts.forEach(p => {{ postsById[p.logNo] = p; }});

const grid = document.getElementById('grid');
const tabsEl = document.getElementById('tabs');
let activeCategory = '전체';

function renderTabs() {{
  const tabs = ['전체', ...categories];
  tabsEl.innerHTML = '';
  tabs.forEach(cat => {{
    const btn = document.createElement('button');
    btn.className = 'tab' + (cat === activeCategory ? ' active' : '');
    btn.textContent = cat;
    btn.addEventListener('click', () => {{
      activeCategory = cat;
      renderTabs();
      renderGrid();
    }});
    tabsEl.appendChild(btn);
  }});
}}

function renderGrid() {{
  const filtered = activeCategory === '전체' ? posts : posts.filter(p => p.category === activeCategory);
  grid.innerHTML = '';
  if (filtered.length === 0) {{
    grid.innerHTML = '<p class="empty">게시글이 없습니다.</p>';
    return;
  }}
  filtered.forEach((post) => {{
    const card = document.createElement('div');
    card.className = 'card';
    const cover = post.localImages && post.localImages[0] ? '../' + post.localImages[0] : '';
    card.innerHTML = `
      ${{cover ? `<img class="thumb" src="${{cover}}" loading="lazy" alt="${{post.title}}">` : '<div class="thumb"></div>'}}
      <div class="meta">
        <h3>${{post.title}}</h3>
        <p class="date">${{post.date || ''}}</p>
      </div>
    `;
    card.addEventListener('click', () => openModal(post.logNo));
    grid.appendChild(card);
  }});
}}

renderTabs();
renderGrid();

const overlay = document.getElementById('overlay');
const modal = document.getElementById('modal');

function openModal(logNo, {{ pushState = true }} = {{}}) {{
  const post = postsById[logNo];
  if (!post) return;
  const imagesHtml = (post.localImages || [])
    .map(src => `<img src="../${{src}}" loading="lazy" alt="">`)
    .join('');
  modal.innerHTML = `
    <div class="modal-header">
      <h2>${{post.title}}</h2>
      <button class="close" aria-label="닫기">&times;</button>
    </div>
    <p class="modal-date">${{post.date || ''}}</p>
    <div class="modal-images">${{imagesHtml}}</div>
    <div class="modal-text">${{escapeHtml(post.text || '')}}</div>
    <div class="modal-footer">
      <a href="${{post.originalUrl}}" target="_blank" rel="noopener">네이버 블로그 원문 보기 →</a>
      <button class="copy-link">링크 복사</button>
    </div>
  `;
  modal.querySelector('.close').addEventListener('click', closeModal);
  modal.querySelector('.copy-link').addEventListener('click', (e) => {{
    navigator.clipboard.writeText(window.location.origin + window.location.pathname + '?id=' + logNo);
    e.target.textContent = '복사됨!';
    setTimeout(() => {{ e.target.textContent = '링크 복사'; }}, 1500);
  }});
  overlay.classList.add('open');
  if (pushState) {{
    const url = window.location.pathname + '?id=' + logNo;
    history.pushState({{ logNo }}, '', url);
  }}
}}

function closeModal({{ pushState = true }} = {{}}) {{
  overlay.classList.remove('open');
  modal.innerHTML = '';
  if (pushState) {{
    history.pushState({{}}, '', window.location.pathname);
  }}
}}

overlay.addEventListener('click', (e) => {{
  if (e.target === overlay) closeModal();
}});
document.addEventListener('keydown', (e) => {{
  if (e.key === 'Escape' && overlay.classList.contains('open')) closeModal();
}});

window.addEventListener('popstate', () => {{
  const id = new URLSearchParams(window.location.search).get('id');
  if (id && postsById[id]) {{
    openModal(id, {{ pushState: false }});
  }} else {{
    closeModal({{ pushState: false }});
  }}
}});

function escapeHtml(str) {{
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}}

// open directly if URL already has ?id=... on load
const initialId = new URLSearchParams(window.location.search).get('id');
if (initialId && postsById[initialId]) {{
  openModal(initialId, {{ pushState: false }});
}}
</script>
</body>
</html>
"""


ALL_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{blog_title}</title>
<style>
  :root {{
    --bg: #faf7f2;
    --card-bg: #ffffff;
    --ink: #2b2622;
    --ink-soft: #6f665c;
    --accent: #c07a4a;
    --border: #e8e0d5;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #1c1a17;
      --card-bg: #262320;
      --ink: #efe9e1;
      --ink-soft: #b3a99b;
      --accent: #e0995f;
      --border: #38332c;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    background: var(--bg);
    color: var(--ink);
  }}
  header {{
    padding: 40px 24px 20px;
    text-align: center;
  }}
  header h1 {{
    margin: 0 0 8px;
    font-size: 1.6rem;
    letter-spacing: -0.02em;
  }}
  header p {{
    margin: 0;
    color: var(--ink-soft);
    font-size: 0.9rem;
  }}
  header a {{ color: var(--accent); text-decoration: none; }}
  .tabs {{
    display: flex;
    justify-content: center;
    gap: 8px;
    padding: 16px 24px 0;
    flex-wrap: wrap;
  }}
  .tab {{
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--ink-soft);
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 7px 16px;
  }}
  .tab.active {{
    color: #fff;
    background: var(--accent);
    border-color: var(--accent);
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 4px;
    padding: 8px;
    max-width: 1400px;
    margin: 0 auto 48px;
  }}
  .thumb {{
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
    width: 100%;
    cursor: pointer;
    background: var(--border);
    border-radius: 4px;
  }}
  .overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(20, 16, 12, 0.85);
    z-index: 50;
    padding: 24px;
    overflow-y: auto;
  }}
  .overlay.open {{ display: flex; flex-direction: column; align-items: center; }}
  .lightbox {{
    background: var(--card-bg);
    max-width: 720px;
    width: 100%;
    margin: auto;
    border-radius: 16px;
    overflow: hidden;
  }}
  .lightbox img {{
    width: 100%;
    display: block;
  }}
  .lightbox-info {{
    padding: 16px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }}
  .lightbox-info h3 {{
    margin: 0 0 4px;
    font-size: 1rem;
  }}
  .lightbox-info p {{
    margin: 0;
    font-size: 0.8rem;
    color: var(--ink-soft);
  }}
  .lightbox-info a {{
    color: var(--accent);
    font-size: 0.85rem;
    text-decoration: none;
    white-space: nowrap;
  }}
  .close {{
    position: fixed;
    top: 20px;
    right: 28px;
    cursor: pointer;
    font-size: 2rem;
    color: #fff;
    background: none;
    border: none;
    line-height: 1;
    z-index: 51;
  }}
  .nav-arrow {{
    position: fixed;
    top: 50%;
    transform: translateY(-50%);
    cursor: pointer;
    font-size: 2.5rem;
    color: #fff;
    background: rgba(0, 0, 0, 0.25);
    border: none;
    line-height: 1;
    z-index: 51;
    padding: 12px 16px;
    border-radius: 8px;
  }}
  .nav-arrow:hover {{ background: rgba(0, 0, 0, 0.45); }}
  .nav-prev {{ left: 12px; }}
  .nav-next {{ right: 12px; }}
  @media (max-width: 640px) {{
    .nav-arrow {{ font-size: 1.8rem; padding: 8px 12px; }}
  }}
  footer {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    padding: 8px 24px 48px;
  }}
  footer a {{
    display: inline-flex;
    width: 40px;
    height: 40px;
    transition: transform 0.15s ease;
  }}
  footer a:hover {{ transform: translateY(-2px); }}
  footer svg {{ width: 100%; height: 100%; }}
</style>
</head>
<body>
<header>
  <h1>{blog_title}</h1>
  <p><a href="posts/index.html">글감 보기 →</a> · 총 <span id="imgCount">{image_count}</span>장</p>
</header>

<div class="tabs" id="tabs"></div>
<div class="grid" id="grid"></div>
<div class="overlay" id="overlay">
  <button class="close" id="closeBtn" aria-label="닫기">&times;</button>
  <button class="nav-arrow nav-prev" id="prevBtn" aria-label="이전 이미지">&#8249;</button>
  <button class="nav-arrow nav-next" id="nextBtn" aria-label="다음 이미지">&#8250;</button>
  <div class="lightbox" id="lightbox"></div>
</div>

{footer_html}

<script>
const images = {images_json};
const categories = {categories_json};

const grid = document.getElementById('grid');
const tabsEl = document.getElementById('tabs');
const countEl = document.getElementById('imgCount');
let activeCategory = '전체';
let filteredImages = images;

function renderTabs() {{
  const tabs = ['전체', ...categories];
  tabsEl.innerHTML = '';
  tabs.forEach(cat => {{
    const btn = document.createElement('button');
    btn.className = 'tab' + (cat === activeCategory ? ' active' : '');
    btn.textContent = cat;
    btn.addEventListener('click', () => {{
      activeCategory = cat;
      renderTabs();
      renderGrid();
    }});
    tabsEl.appendChild(btn);
  }});
}}

function renderGrid() {{
  filteredImages = activeCategory === '전체' ? images : images.filter(img => img.category === activeCategory);
  countEl.textContent = filteredImages.length;
  grid.innerHTML = '';
  filteredImages.forEach((img, idx) => {{
    const el = document.createElement('img');
    el.className = 'thumb';
    el.src = img.src;
    el.loading = 'lazy';
    el.alt = img.title;
    el.addEventListener('click', () => openLightbox(idx));
    grid.appendChild(el);
  }});
}}

renderTabs();
renderGrid();

const overlay = document.getElementById('overlay');
const lightbox = document.getElementById('lightbox');
let currentIdx = -1;

function imgParamId(img) {{
  const filename = img.src.split('/').pop();
  return img.logNo + '_' + filename;
}}

function openLightbox(idx) {{
  currentIdx = idx;
  const img = filteredImages[idx];
  lightbox.innerHTML = `
    <img src="${{img.src}}" alt="">
    <div class="lightbox-info">
      <div>
        <h3>${{img.title}}</h3>
        <p>${{img.date || ''}}</p>
      </div>
      <a href="posts/index.html?id=${{img.logNo}}">글 보기 →</a>
    </div>
  `;
  overlay.classList.add('open');
  const url = window.location.pathname + '?img=' + encodeURIComponent(imgParamId(img));
  history.replaceState(null, '', url);
}}

function showNext() {{
  if (currentIdx < 0) return;
  openLightbox((currentIdx + 1) % filteredImages.length);
}}

function showPrev() {{
  if (currentIdx < 0) return;
  openLightbox((currentIdx - 1 + filteredImages.length) % filteredImages.length);
}}

function closeLightbox() {{
  overlay.classList.remove('open');
  lightbox.innerHTML = '';
  currentIdx = -1;
  history.replaceState(null, '', window.location.pathname);
}}

document.getElementById('closeBtn').addEventListener('click', closeLightbox);
document.getElementById('nextBtn').addEventListener('click', showNext);
document.getElementById('prevBtn').addEventListener('click', showPrev);
overlay.addEventListener('click', (e) => {{
  if (e.target === overlay) closeLightbox();
}});
document.addEventListener('keydown', (e) => {{
  if (!overlay.classList.contains('open')) return;
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowRight') showNext();
  if (e.key === 'ArrowLeft') showPrev();
}});

// open directly if URL already has ?img=... on load (no history entry added)
const initialImgParam = new URLSearchParams(window.location.search).get('img');
if (initialImgParam) {{
  const fullIdx = images.findIndex(img => imgParamId(img) === initialImgParam);
  if (fullIdx >= 0) {{
    activeCategory = '전체';
    renderTabs();
    renderGrid();
    openLightbox(fullIdx);
  }}
}}
</script>
</body>
</html>
"""


def date_sort_key(date_str):
    """Parse 'YYYY. M. D. HH:MM' into a tuple that sorts newest-first when
    reverse=True. Posts with an unparseable/missing date sort last (oldest)."""
    m = re.match(r"(\d+)\.\s*(\d+)\.\s*(\d+)\.\s*(\d+):(\d+)", date_str or "")
    if not m:
        return (0, 0, 0, 0, 0)
    return tuple(int(x) for x in m.groups())


def main():
    posts = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    posts.sort(key=lambda p: date_sort_key(p.get("date", "")), reverse=True)
    categories = sorted(set(p.get("category", "그림") for p in posts))

    POSTS_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    posts_html = TEMPLATE.format(
        blog_title=BLOG_TITLE,
        blog_id=BLOG_ID,
        post_count=len(posts),
        posts_json=json.dumps(posts, ensure_ascii=False),
        categories_json=json.dumps(categories, ensure_ascii=False),
        footer_html=FOOTER_HTML,
    )
    POSTS_OUT_PATH.write_text(posts_html, encoding="utf-8")
    print(f"생성 완료 -> {POSTS_OUT_PATH}")

    excluded = set()
    if EXCLUDED_IMAGES_PATH.exists():
        excluded = set(json.loads(EXCLUDED_IMAGES_PATH.read_text(encoding="utf-8")))

    images = []
    for post in posts:
        for src in post.get("localImages", []):
            if src in excluded:
                continue
            images.append(
                {
                    "src": src,
                    "title": post["title"],
                    "date": post.get("date", ""),
                    "logNo": post["logNo"],
                    "category": post.get("category", "그림"),
                }
            )

    home_html = ALL_TEMPLATE.format(
        blog_title=BLOG_TITLE,
        image_count=len(images),
        images_json=json.dumps(images, ensure_ascii=False),
        categories_json=json.dumps(categories, ensure_ascii=False),
        footer_html=FOOTER_HTML,
    )
    HOME_OUT_PATH.write_text(home_html, encoding="utf-8")
    print(f"생성 완료 -> {HOME_OUT_PATH}")


if __name__ == "__main__":
    main()
