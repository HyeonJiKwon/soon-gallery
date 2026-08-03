#!/bin/bash
# Incrementally crawl both categories, regenerate the site, and push to GitHub.
# Vercel is connected to the GitHub repo, so a push alone triggers the deploy.
# Intended to be run on a schedule (see scripts/com.khjkes.bloggallery.plist).
set -e

PROJECT_DIR="/Users/khjbest39/myprj/naver_blog_gallery"
LOG_FILE="$PROJECT_DIR/data/auto_update.log"
export PATH="/Users/khjbest39/.nvm/versions/node/v22.12.0/bin:/usr/bin:/bin:/usr/local/bin:$PATH"

cd "$PROJECT_DIR"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') ====="

  python3 scripts/crawl.py --blog-id khjkes --category-no 46 --category-label 일상
  python3 scripts/crawl.py --blog-id khjkes --category-no 51 --category-label 제주

  python3 scripts/generate_site.py

  if [ -n "$(git status --porcelain)" ]; then
    git add -A -- data images index.html posts .gitignore
    git commit -m "자동 업데이트: $(date '+%Y-%m-%d %H:%M')"
    git push origin main
    echo "git push 완료 -> Vercel 자동 배포 트리거됨"
  else
    echo "변경 사항 없음 (커밋/푸시 생략)"
  fi

  echo "완료: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
} >> "$LOG_FILE" 2>&1
