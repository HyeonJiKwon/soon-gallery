#!/usr/bin/env python3
"""Sync data/posts.json's localImages with what actually exists in images/.

Run this after manually deleting unwanted image files, so posts.json (and the
generated site) stop referencing files that no longer exist.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "posts.json"
IMAGES_DIR = BASE_DIR / "images"


def main():
    posts = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    total_removed = 0
    for post in posts:
        local_images = post.get("localImages", [])
        kept = [p for p in local_images if (BASE_DIR / p).exists()]
        removed = len(local_images) - len(kept)
        if removed:
            total_removed += removed
            print(f"  {post['logNo']} ({post['title']}): {removed}개 정리됨")
        post["localImages"] = kept

    DATA_PATH.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료. 총 {total_removed}개의 끊어진 이미지 참조를 정리했습니다.")


if __name__ == "__main__":
    main()
