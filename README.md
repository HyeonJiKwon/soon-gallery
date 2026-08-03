# 그림놀이터 갤러리 — 명령어 정리

네이버 블로그(`blog.naver.com/khjkes`)를 크롤링해서 정적 갤러리로 만드는 프로젝트.
배포 사이트: https://soon-gallery.vercel.app

## 폴더 구조

```
naver_blog_gallery/
├── index.html          # 홈 (전체 이미지 갤러리)
├── posts/index.html    # 글감 보기 (게시글 카드 + 본문 모달)
├── data/
│   ├── posts.json          # 크롤링 원본 데이터 (제목/날짜/본문/이미지/카테고리)
│   ├── excluded_images.json # /all 갤러리에서 제외할 이미지 경로 목록
│   └── auto_update.log     # 자동 실행 로그
├── images/              # 다운로드된 이미지 (게시글 logNo별 폴더)
└── scripts/
    ├── crawl.py          # 크롤러
    ├── generate_site.py  # index.html / posts/index.html 생성
    ├── sync_images.py    # 로컬에서 지운 이미지 참조 정리
    └── auto_update.sh    # 크롤링→생성→배포 전체 자동화 스크립트
```

## 크롤링

기본은 **증분 크롤링** — 마지막으로 저장된 글 이후 신규 글만 확인합니다.

```bash
cd /Users/khjbest39/myprj/naver_blog_gallery

# 그림 카테고리 (categoryNo=46)
python3 scripts/crawl.py --blog-id khjkes --category-no 46 --category-label 그림

# 제주 카테고리 (categoryNo=51)
python3 scripts/crawl.py --blog-id khjkes --category-no 51 --category-label 제주
```

옵션:
- `--full` : 증분 무시하고 해당 카테고리 전체 재크롤링 (다른 카테고리 데이터는 안전하게 보존됨)
- `--limit N` : 테스트용으로 N개만 크롤링
- `--no-classify` : 아래 자동 완성작 판별을 건너뜀 (`excluded_images.json` 안 건드림)

날짜는 블로그 RSS 피드(`rss.blog.naver.com`)의 절대 발행 시각을 우선 사용합니다.
네이버 글 상세 페이지는 하루 이내 최근 글은 "n시간 전"처럼 상대 시간만 보여줘서,
그것만 쓰면 크롤링한 시점의 상대 시간이 데이터에 고정돼버리는 문제가 있었음.

### 완성작 자동 판별

신규 글을 크롤링할 때마다, 그 글의 이미지들을 Claude가 자동으로 보고
완성작인지(전체 이미지 갤러리에 노출) 과정/사진인지(제외) 판단해서
`data/excluded_images.json`에 자동으로 추가합니다.

판단 기준:
- 그림 구석에 `soon`/`Soon` 서명이 있으면 완성작
- 손글씨 캡션이 그림과 함께 쓰여 있으면 완성작
- 실사 사진이거나 스케치 진행 과정이면 제외

내부적으로 `claude -p` (Claude Code CLI, 로그인된 구독 계정 사용, 별도 API 키/과금 없음)를
글 1개당 한 번 호출합니다. 분류에 실패하면 아무것도 제외하지 않고 넘어갑니다(안전 쪽으로 fail).

```bash
# 예: 제주 카테고리 전체 재크롤링
python3 scripts/crawl.py --blog-id khjkes --category-no 51 --category-label 제주 --full
```

## 사이트 생성

크롤링 후에는 항상 재생성 필요 (`posts.json` → `index.html` + `posts/index.html`):

```bash
python3 scripts/generate_site.py
```

## 이미지 정리

**로컬에서 이미지 파일을 직접 지웠을 때** (Finder 등에서), `posts.json`에 남은 깨진 참조를 정리:

```bash
python3 scripts/sync_images.py
```

**`/all` 갤러리에서만 특정 이미지를 숨기고 싶을 때** (원본 파일은 유지):
`data/excluded_images.json`에 경로 추가 후 재생성.

```json
[
  "images/224362727172/00.jpg"
]
```

## 배포 (GitHub → Vercel 자동 배포)

GitHub 저장소(https://github.com/HyeonJiKwon/soon-gallery)가 Vercel 프로젝트에
연결되어 있어서, `main` 브랜치에 push만 하면 Vercel이 알아서 빌드/배포합니다.
CLI로 직접 배포할 필요 없음:

```bash
git add -A -- data images index.html posts .gitignore
git commit -m "업데이트"
git push origin main
```

## 한 번에 다 하기

크롤링(그림+제주) → 사이트 재생성 → 변경 있으면 커밋+푸시(Vercel 자동 배포)까지 한 번에:

```bash
bash scripts/auto_update.sh
```

로그는 `data/auto_update.log`에 누적 기록됨.

## 자동 실행 (매일 오후 2시)

macOS `launchd`로 매일 자동 실행되도록 등록되어 있음
(`~/Library/LaunchAgents/com.khjkes.bloggallery.plist`).

```bash
# 상태 확인
launchctl print gui/$(id -u)/com.khjkes.bloggallery

# 끄기
launchctl bootout gui/$(id -u)/com.khjkes.bloggallery

# 다시 켜기
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.khjkes.bloggallery.plist

# 지금 바로 한 번 더 실행 (테스트용)
bash scripts/auto_update.sh
```

> Mac이 켜져 있고 로그인된 상태여야 실행됩니다. 완전히 꺼져 있거나 잠자기 상태면 그 회차는 건너뜁니다.
