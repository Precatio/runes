#!/usr/bin/env bash
# The public website (vitkirunor.se) built locally, the same way GitHub builds it (.github/workflows/site.yml): a copy of
# web/ without the app's pages, built as static files to .site-build/web/out. Leaves the running app alone (its own
# copy and its own .next). Preview: (cd .site-build/web/out && python3 -m http.server 4000)
set -euo pipefail
cd "$(dirname "$0")/.."
B=.site-build
rm -rf "$B" && mkdir -p "$B/web"
for f in web/* web/.[!.]*; do
  case "$(basename "$f")" in .next|out) continue ;; esac
  cp -cR "$f" "$B/web/" 2>/dev/null || cp -R "$f" "$B/web/"   # a copy-on-write clone on APFS
done
cp CITATION.cff .gitignore "$B/"
git -C "$B" init -q   # Tailwind skips what .gitignore lists (node_modules) only inside a git repository
rm -rf "$B/web/src/app/(app)" "$B/web/src/app/api" "$B/web/src/app/indexnow-key.txt"
cd "$B/web"
NEXT_PUBLIC_SITE_MODE=public NEXT_PUBLIC_SITE_URL="${SITE_URL:-https://vitkirunor.se}" NEXT_TELEMETRY_DISABLED=1 npx next build
touch out/.nojekyll
echo "Klart: $(pwd)/out"
