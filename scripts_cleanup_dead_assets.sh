#!/usr/bin/env bash
# Removes build artefacts and asset files that nothing in the project references.
#
# Kept as a separate script, rather than folded into the code changes, because it
# deletes files and you should read it first. Every path below was verified
# unreferenced by any template, stylesheet or Python module.
#
# Rollback:
#   Build output:  npm run minify && python manage.py collectstatic --noinput
#   Image assets:  git checkout -- static/images/did-academy
set -euo pipefail
cd "$(dirname "$0")"

echo "== django-compressor build artefacts (gitignored, ~1.2 MB) =="
# django-compressor has been removed from INSTALLED_APPS and requirements: no
# template ever contained a "compress" tag, so these are orphaned output.
rm -rf static/CACHE staticfiles/CACHE

echo "== unreferenced did-academy assets (~16 MB, tracked in git) =="
# grep over templates/, static/css/input.css and apps/ finds zero references to
# anything in this directory. idi_did_processflow.svg alone is 15.5 MB, which is
# almost certainly a raster image wrapped in an SVG container rather than a real
# vector export. If the process diagram is still wanted, re-export it properly
# (SVGO, or a WebP at display resolution) and reference it from a template.
rm -rf static/images/did-academy

echo "== collected copies of the JS/CSS already deleted from static/ =="
# Sources removed because they were either referenced nowhere at all
# (cdn.min.js was a 0-byte file; jquery-3.6.0.min.js had no script tag anywhere)
# or gated on DOM elements that exist in no template (lottie on #lottie-container,
# swiper on .projectSwiper). lazy-loading.js searched for img.lazy / data-src,
# which no template uses -- native loading="lazy" already covers it.
rm -f staticfiles/js/cdn.min.js \
      staticfiles/js/jquery-3.6.0.min.js \
      staticfiles/js/lottie.min.js \
      staticfiles/js/lazy-loading.js \
      staticfiles/js/vendor/swiper-bundle.min.js \
      staticfiles/css/vendor/swiper-bundle.min.css

# Hashed variants produced by ManifestStaticFilesStorage.
find staticfiles \( -name 'cdn.min.*.js' \
                 -o -name 'jquery-3.6.0.min.*.js' \
                 -o -name 'lottie.min.*.js' \
                 -o -name 'lazy-loading.*.js' \
                 -o -name 'swiper-bundle.min.*' \) -delete 2>/dev/null || true

echo
echo "Done. Regenerate the manifest with:"
echo "  python manage.py collectstatic --noinput"
