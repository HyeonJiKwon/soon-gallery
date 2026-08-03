#!/bin/bash
# Incrementally crawl both categories, regenerate the site, and deploy to Vercel.
# Intended to be run on a schedule (see scripts/com.khjkes.bloggallery.plist).
set -e

PROJECT_DIR="/Users/khjbest39/myprj/naver_blog_gallery"
LOG_FILE="$PROJECT_DIR/data/auto_update.log"
export PATH="/Users/khjbest39/.nvm/versions/node/v22.12.0/bin:/usr/bin:/bin:/usr/local/bin:$PATH"

cd "$PROJECT_DIR"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') ====="

  python3 scripts/crawl.py --blog-id khjkes --category-no 46 --category-label 그림
  python3 scripts/crawl.py --blog-id khjkes --category-no 51 --category-label 제주

  python3 scripts/generate_site.py

  vercel --prod --yes

  echo "완료: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
} >> "$LOG_FILE" 2>&1
