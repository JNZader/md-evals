#!/usr/bin/env bash
set -euo pipefail

# Build script for Cloudflare Pages
# Replicates .github/workflows/deploy-pages.yml assembly logic
# Output: _site/ (landing + React app + Docsify docs)

echo "==> Installing dependencies..."
npm ci --prefix apps/web

echo "==> Building frontend..."
npm run build --prefix apps/web

echo "==> Assembling _site/..."
rm -rf _site
mkdir -p _site _site/app _site/docs

# 1. React app → _site/app/
if [ -d apps/web/dist ]; then
  cp -r apps/web/dist/* _site/app/
else
  echo "WARNING: apps/web/dist not found — skipping app"
fi

# 2. Landing page (docs/index.html) → _site/ root
if [ -f docs/index.html ]; then
  cp docs/index.html _site/index.html
fi

# 3. Remaining docs content → _site/docs/
if [ -d docs ]; then
  # Copy everything except the landing page index.html
  rsync -a --exclude='index.html' docs/ _site/docs/
  # Use docsify.html as the docs portal index
  if [ -f docs/docsify.html ]; then
    cp docs/docsify.html _site/docs/index.html
  fi
fi

echo "==> Done! Output in _site/"
echo "    Contents:"
ls -la _site/
