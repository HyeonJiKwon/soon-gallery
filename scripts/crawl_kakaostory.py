#!/usr/bin/env python3
"""Fetch KakaoStory post(s) and add them to data/posts.json under a category.

KakaoStory embeds a full JSON blob (`boot.parseInitialData({...})`) in the
post page's HTML, so no login/API key is needed for public posts.

Usage:
    python3 crawl_kakaostory.py <post_url> [<post_url> ...] --category-label 스토리
"""
import argparse
import datetime
import json
import re
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"


def fetch(url, ua=UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def extract_initial_data(html):
    marker = "boot.parseInitialData("
    start = html.find(marker)
    if start == -1:
        raise ValueError("boot.parseInitialData(...)를 찾을 수 없음 (비공개 글이거나 페이지 구조 변경)")
    start += len(marker)
    depth = 0
    i = start
    while i < len(html):
        c = html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return json.loads(html[start : i + 1])


def parse_post(post_url):
    html = fetch(post_url).decode("utf-8")
    data = extract_initial_data(html)
    act = data["activity"]

    post_id = act["id"]
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", post_id)
    log_no = f"kakao_{safe_id}"

    content = act.get("content", "").strip()
    first_line = content.splitlines()[0] if content else post_id
    title = re.sub(r"\s+", " ", first_line).strip()[:40] or post_id

    date = ""
    created_at = act.get("created_at", "")
    if created_at:
        dt = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        dt += datetime.timedelta(hours=9)  # UTC -> KST
        date = f"{dt.year}. {dt.month}. {dt.day}. {dt.hour:02d}:{dt.minute:02d}"

    images = [m.get("origin_url") or m.get("url") for m in act.get("media", [])]
    images = [u for u in images if u]

    return {
        "logNo": log_no,
        "title": title,
        "date": date,
        "text": content,
        "images": images,
        "originalUrl": act.get("permalink", post_url),
    }


def download_image(url, dest_path):
    if dest_path.exists():
        return
    data = fetch(url)
    dest_path.write_bytes(data)


def crawl_post(post_url, category_label):
    post = parse_post(post_url)
    post["category"] = category_label

    post_img_dir = IMAGES_DIR / post["logNo"]
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
            local_images.append(f"images/{post['logNo']}/{fname}")
        except Exception as e:
            print(f"  이미지 다운로드 실패 ({img_url}): {e}")
        time.sleep(0.15)
    post["localImages"] = local_images
    return post


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post_urls", nargs="+")
    ap.add_argument("--category-label", default="스토리")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    out_path = DATA_DIR / "posts.json"
    posts = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else []
    by_id = {p["logNo"]: p for p in posts}

    for post_url in args.post_urls:
        print(f"크롤링 중: {post_url}")
        try:
            post = crawl_post(post_url, args.category_label)
        except Exception as e:
            print(f"  실패: {e}")
            continue
        by_id[post["logNo"]] = post
        print(f"  완료: {post['title']} ({len(post['localImages'])}장, {post['date']})")

    out_path.write_text(
        json.dumps(list(by_id.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"총 {len(by_id)}개 게시글 저장됨 -> {out_path}")


if __name__ == "__main__":
    main()
