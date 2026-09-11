#!/usr/bin/env bash
# deploy.sh — 사이트 재생성 + (나중에 채울) 원격 배포 훅
# 원격 배포 대상(GitHub Pages / 정적 호스팅 등)이 정해지면 DEPLOY 부분만 채운다.
set -euo pipefail
cd "$(dirname "$0")"

python3 generate_html.py

# ── 배포 (미설정) ──────────────────────────────────────────
# 예시 1) GitHub에 push (원격 연결 후):
#   git add -A && git commit -m "update: $(date +%F)" && git push
# 예시 2) 정적 서버에 rsync:
#   rsync -avz --delete index.html archive/ user@host:/var/www/ai-news/
echo "HTML 재생성 완료. 원격 배포는 아직 미설정 (deploy.sh의 DEPLOY 부분 참고)."
