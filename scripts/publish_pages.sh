#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/sherry/codex/HelloWorld"
SITE_DIR="$ROOT/site"
PAGES_REPO="/tmp/cryptosherry_pages_repo"
REMOTE_URL="https://github.com/imcryptosherry/cryptosherry.zyx.git"
BRANCH="main"

if [[ ! -d "$PAGES_REPO/.git" ]]; then
  echo "[info] Pages repo missing; cloning to $PAGES_REPO"
  rm -rf "$PAGES_REPO"
  git clone "$REMOTE_URL" "$PAGES_REPO"
fi

git -C "$PAGES_REPO" pull --rebase origin "$BRANCH"
rsync -av --delete \
  --exclude '.git/' \
  --exclude '.github/' \
  --exclude 'CNAME' \
  --exclude '.nojekyll' \
  "$SITE_DIR"/ "$PAGES_REPO"/

git -C "$PAGES_REPO" add -A
if git -C "$PAGES_REPO" diff --cached --quiet; then
  echo "[skip] No site changes to publish"
  exit 0
fi

if [[ -z "$(git -C "$PAGES_REPO" config --get user.name || true)" ]]; then
  git -C "$PAGES_REPO" config user.name "imcryptosherry"
fi
if [[ -z "$(git -C "$PAGES_REPO" config --get user.email || true)" ]]; then
  git -C "$PAGES_REPO" config user.email "imsherrywu@outlook.com"
fi

git -C "$PAGES_REPO" commit -m "Auto update daily picks: $(date -u +%F)"
git -C "$PAGES_REPO" push origin "$BRANCH"

echo "[ok] Published to GitHub Pages branch $BRANCH"
