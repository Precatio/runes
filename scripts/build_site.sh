#!/usr/bin/env bash
# The public website (vitkirunor.se) built locally, the same way GitHub builds it (.github/workflows/site.yml): a copy of
# web/ without the app's pages, built as static files to .site-build/web/out. Leaves the running app alone (its own
# copy and its own .next). Preview: (cd .site-build/web/out && python3 -m http.server 4000)
set -euo pipefail
cd "$(dirname "$0")/.."
B="${SITE_BUILD_DIR:-.site-build}"   # another folder (absolute) for a trial build elsewhere
rm -rf "$B" && mkdir -p "$B/web"
for f in web/* web/.[!.]*; do
  case "$(basename "$f")" in .next|out) continue ;; esac
  cp -cR "$f" "$B/web/" 2>/dev/null || cp -R "$f" "$B/web/"   # a copy-on-write clone on APFS
done
cp CITATION.cff .gitignore "$B/"
git -C "$B" init -q   # Tailwind skips what .gitignore lists (node_modules) only inside a git repository
# The app's pages and API, and the app map's realm boundaries (public/geo), which no public page uses
rm -rf "$B/web/src/app/(app)" "$B/web/src/app/api" "$B/web/src/app/indexnow-key.txt" "$B/web/public/geo"
cd "$B/web"
# Only the catalog entries the public pages can show, from the current catalog (src/i18n/public-catalog.mjs)
npm run --silent i18n:public
# The vote on the start page writes to this Firebase project (public; as in site.yml)
NEXT_PUBLIC_SITE_MODE=public NEXT_PUBLIC_SITE_URL="${SITE_URL:-https://vitkirunor.se}" \
  NEXT_PUBLIC_FIREBASE_PROJECT_ID="${NEXT_PUBLIC_FIREBASE_PROJECT_ID:-runes-1656b}" NEXT_TELEMETRY_DISABLED=1 npx next build
# The English editions of the articles declare English as the page's language (perl: sed -i differs on macOS)
find out/en -name '*.html' -exec perl -pi -e 's/<html lang="sv"/<html lang="en"/' {} +
touch out/.nojekyll
echo "Klart: $(pwd)/out"
