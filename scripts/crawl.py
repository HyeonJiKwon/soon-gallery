#!/usr/bin/env python3
"""Crawl a specific Naver blog category (posts + images) and save as JSON + local images.

Usage:
    python3 crawl.py --blog-id khjkes --category-no 46
"""
import argparse
import json
import re
import subprocess
import time
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
EXCLUDED_IMAGES_PATH = DATA_DIR / "excluded_images.json"

CLAUDE_BIN = "/Users/khjbest39/.local/bin/claude"
CLASSIFY_SYSTEM_PROMPT = (
    "You are an image classifier. You have file-reading tools to view images. "
    "Respond with JSON only, no explanation, no markdown fences."
)

DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"


def fetch(url, ua=DESKTOP_UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def fetch_rss_dates(blog_id):
    """Naver's post-view pages show relative time ('n시간 전') for posts less
    than ~24h old instead of an absolute date. The blog's RSS feed has an
    absolute <pubDate> per item, so use it to override the date whenever
    available. Only covers the ~50 most recent posts across ALL categories,
    so older posts keep falling back to whatever the post page shows (which
    is already an absolute date by then)."""
    try:
        raw = fetch(f"https://rss.blog.naver.com/{blog_id}.xml").decode("utf-8")
    except Exception:
        return {}

    dates = {}
    for item in re.findall(r"<item>(.*?)</item>", raw, re.S):
        log_no_m = re.search(r"/(\d{5,})\?fromRss", item)
        pub_m = re.search(r"<pubDate>(.*?)</pubDate>", item)
        if not log_no_m or not pub_m:
            continue
        try:
            d = parsedate_to_datetime(pub_m.group(1))
        except Exception:
            continue
        dates[log_no_m.group(1)] = f"{d.year}. {d.month}. {d.day}. {d.hour:02d}:{d.minute:02d}"
    return dates


def list_post_ids(blog_id, category_no, count_per_page=30, known_ids=None):
    """List post ids newest-first. If known_ids is given, stop as soon as a
    post already in known_ids is seen (everything after it was crawled
    before), so only ids newer than the last crawl are returned."""
    known_ids = known_ids or set()
    log_nos = []
    page = 1
    while True:
        url = (
            "https://blog.naver.com/PostTitleListAsync.naver"
            f"?blogId={blog_id}&currentPage={page}&categoryNo={category_no}"
            f"&countPerPage={count_per_page}"
        )
        raw = fetch(url).decode("utf-8")
        raw = raw.replace("\\'", "'")
        data = json.loads(raw)
        posts = data.get("postList", [])
        if not posts:
            break
        reached_known = False
        for p in posts:
            if p["logNo"] in known_ids:
                reached_known = True
                break
            log_nos.append(p["logNo"])
        if reached_known:
            break
        total = int(data.get("totalCount", 0))
        if len(log_nos) >= total:
            break
        page += 1
        time.sleep(0.3)
    return log_nos


def parse_post(blog_id, log_no, rss_dates=None):
    from bs4 import BeautifulSoup

    url = f"https://m.blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
    html = fetch(url, ua=MOBILE_UA).decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text().strip() if soup.title else log_no
    title = re.sub(r"\s*:\s*네이버\s*블로그\s*$", "", title).strip()

    date = (rss_dates or {}).get(log_no, "")
    if not date:
        date_el = soup.select_one(".blog_date, .se_publishDate, .date")
        if date_el:
            date = date_el.get_text(strip=True)

    container = soup.select_one(".se-main-container")
    if not container:
        container = soup.select_one("#postViewArea")

    img_urls = []
    text_parts = []
    if container:
        for tag in container.select("script, style"):
            tag.decompose()

        for img in container.select("img"):
            src = img.get("data-lazy-src") or img.get("src")
            if not src or not src.startswith("http"):
                continue
            if "storep-phinf.pstatic.net" in src:
                # OGQ market sticker/emoticon, not blog content
                continue
            img_urls.append(src)

        body_text = container.get_text("\n", strip=True)
        text_parts.append(body_text)

    seen = set()
    clean_urls = []
    for u in img_urls:
        base = u.split("?")[0]
        if base in seen or "ssl.pstatic.net/static" in base:
            continue
        seen.add(base)
        if "mblogthumb-phinf.pstatic.net" in base or "blogfiles.pstatic.net" in base:
            clean_urls.append(base + "?type=w966")
        else:
            # non-photo assets (stickers, etc.) only exist at their original querystring
            clean_urls.append(u)

    body_text = "\n".join(text_parts).strip()

    return {
        "logNo": log_no,
        "title": title,
        "date": date,
        "text": body_text,
        "images": clean_urls,
        "originalUrl": f"https://blog.naver.com/{blog_id}/{log_no}",
    }


def download_image(url, dest_path):
    if dest_path.exists():
        return
    data = fetch(url)
    dest_path.write_bytes(data)


def crawl_post(blog_id, log_no, category_label, rss_dates=None):
    post = parse_post(blog_id, log_no, rss_dates=rss_dates)
    post["category"] = category_label

    post_img_dir = IMAGES_DIR / log_no
    post_img_dir.mkdir(parents=True, exist_ok=True)
    local_images = []
    for j, img_url in enumerate(post["images"]):
        path_part = img_url.split("?")[0]
        ext = Path(path_part).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            ext = ".jpg"
        fname = f"{j:02d}{ext}"
        dest = post_img_dir / fname
        try:
            download_image(img_url, dest)
            local_images.append(f"images/{log_no}/{fname}")
        except Exception as e:
            print(f"  이미지 다운로드 실패 ({img_url}): {e}")
        time.sleep(0.15)
    post["localImages"] = local_images
    return post


def classify_finished_images(local_image_paths):
    """Ask Claude to judge which images in a post are finished artwork vs.
    process shots / unrelated photos. Returns the subset of local_image_paths
    (relative, 'images/<logNo>/nn.ext') that should be EXCLUDED from the
    /all gallery. Fails open (returns []) on any error so a bad call never
    hides an image that should be visible."""
    if not local_image_paths:
        return []

    abs_paths = [str(BASE_DIR / p) for p in local_image_paths]
    prompt = (
        "다음 이미지 파일들을 봐줘:\n"
        + "\n".join(abs_paths)
        + "\n\n완성작 판단 기준: 그림 구석에 'soon'/'Soon' 서명이 있거나 손글씨 캡션이 함께 쓰여 있으면 완성작. "
        "실사 사진이거나 스케치 진행 과정이면 제외 대상.\n"
        'JSON만 출력 (전체 경로 그대로 사용): {"finished": [...], "excluded": [...]}'
    )
    try:
        result = subprocess.run(
            [
                CLAUDE_BIN, "-p",
                "--system-prompt", CLASSIFY_SYSTEM_PROMPT,
                "--allowedTools", "Read",
                "--output-format", "json",
                prompt,
            ],
            capture_output=True, text=True, timeout=120,
        )
        outer = json.loads(result.stdout)
        text = outer["result"].strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        parsed = json.loads(text)
        excluded_abs = set(parsed.get("excluded", []))
    except Exception as e:
        print(f"  분류 실패, 건너뜀: {e}")
        return []

    excluded_rel = []
    for rel, ap in zip(local_image_paths, abs_paths):
        if ap in excluded_abs:
            excluded_rel.append(rel)
    return excluded_rel


def update_excluded_images(new_excluded_paths):
    excluded_list = []
    if EXCLUDED_IMAGES_PATH.exists():
        excluded_list = json.loads(EXCLUDED_IMAGES_PATH.read_text(encoding="utf-8"))
    seen = set(excluded_list)
    added = [p for p in new_excluded_paths if p not in seen]
    if added:
        excluded_list.extend(added)
        EXCLUDED_IMAGES_PATH.write_text(
            json.dumps(excluded_list, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blog-id", required=True)
    ap.add_argument("--category-no", required=True)
    ap.add_argument("--category-label", required=True, help="short label to tag posts with, e.g. 그림 or 제주")
    ap.add_argument("--limit", type=int, default=None, help="max posts to crawl (for testing)")
    ap.add_argument(
        "--full",
        action="store_true",
        help="ignore existing data/posts.json and re-crawl every post",
    )
    ap.add_argument(
        "--no-classify",
        action="store_true",
        help="skip automatic finished-artwork classification (excluded_images.json won't be updated)",
    )
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    out_path = DATA_DIR / "posts.json"
    # always load whatever's already saved (other categories included) so we
    # never lose it; --full only controls whether THIS category's posts are
    # treated as "already crawled" for the early-stop listing below.
    existing_by_id = {}
    if out_path.exists():
        existing_by_id = {p["logNo"]: p for p in json.loads(out_path.read_text(encoding="utf-8"))}

    known_ids = set() if args.full else set(existing_by_id.keys())
    if known_ids:
        print(f"마지막 크롤링 시점 이후 신규 게시글만 확인 중... (기존 {len(known_ids)}개는 건너뜀)")
    else:
        print("게시글 목록 가져오는 중...")
    to_crawl = list_post_ids(args.blog_id, args.category_no, known_ids=known_ids)
    if args.limit:
        to_crawl = to_crawl[: args.limit]
    print(f"신규 게시글 {len(to_crawl)}개 발견")

    rss_dates = fetch_rss_dates(args.blog_id) if to_crawl else {}

    crawled_by_id = {}
    for i, log_no in enumerate(to_crawl, 1):
        print(f"[{i}/{len(to_crawl)}] {log_no} 크롤링 중...")
        try:
            post = crawl_post(args.blog_id, log_no, args.category_label, rss_dates=rss_dates)
            crawled_by_id[log_no] = post
            if not args.no_classify and post["localImages"]:
                print("  완성작 판별 중...")
                new_excluded = classify_finished_images(post["localImages"])
                added = update_excluded_images(new_excluded)
                if added:
                    print(f"  전체 이미지 갤러리에서 제외: {len(added)}개")
        except Exception as e:
            print(f"  실패: {e}")
        time.sleep(0.3)

    # newest-first: freshly crawled posts, then everything else already saved
    # (other categories, or same-category posts not touched this run)
    posts = [crawled_by_id[ln] for ln in to_crawl if ln in crawled_by_id]
    seen = set(p["logNo"] for p in posts)
    for p in existing_by_id.values():
        if p["logNo"] not in seen:
            posts.append(p)
            seen.add(p["logNo"])

    out_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료. 총 {len(posts)}개 게시글 저장됨 (신규 {len(crawled_by_id)}개) -> {out_path}")


if __name__ == "__main__":
    main()
