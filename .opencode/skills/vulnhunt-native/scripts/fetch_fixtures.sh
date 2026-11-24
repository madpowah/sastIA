#!/usr/bin/env bash
# Fetch the eval fixtures for vulnhunt-native.
#
#   ./fetch_fixtures.sh [destination]
#
# Default: <skill>/evals/fixtures
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${1:-${SCRIPT_DIR}/../evals/fixtures}"
CURL_PARENT="a4dca608e185e2831dcf18ca0c0149484a554206"   # parent of the fix
CURL_FIXED="7541ae569d82fb308a5e2d94916027da4fa3ba3e"    # CVE-2026-8932 fix

mkdir -p "$DEST/curl_vuln/lib/vtls" "$DEST/curl_fixed/lib/vtls"

for f in lib/urldata.h lib/vtls/vtls.c; do
  curl -fsSL --max-time 60 \
    "https://raw.githubusercontent.com/curl/curl/${CURL_PARENT}/${f}" \
    -o "$DEST/curl_vuln/${f}"
  curl -fsSL --max-time 60 \
    "https://raw.githubusercontent.com/curl/curl/${CURL_FIXED}/${f}" \
    -o "$DEST/curl_fixed/${f}"
done

curl -fsSL --max-time 60 \
  'https://cvsweb.openbsd.org/src/sys/netinet/tcp_input.c?rev=1.464&content-type=text/plain' \
  -o "$DEST/tcp_input_1.464.c"
curl -fsSL --max-time 60 \
  'https://cvsweb.openbsd.org/src/sys/netinet/tcp_input.c?rev=1.465&content-type=text/plain' \
  -o "$DEST/tcp_input_1.465.c"

cat <<EOF
Fixtures written to $DEST

Eval commands:
  python3 ${SCRIPT_DIR}/field_coverage.py $DEST/curl_vuln
  python3 ${SCRIPT_DIR}/field_coverage.py $DEST/curl_fixed
  python3 ${SCRIPT_DIR}/guard_coverage.py $DEST/tcp_input_1.464.c
  python3 ${SCRIPT_DIR}/guard_coverage.py $DEST/tcp_input_1.465.c

Score a report:
  python3 ${SCRIPT_DIR}/score_eval.py REPORT \\
    ${SCRIPT_DIR}/../evals/curl_cve_2026_8932/expected.json --mode vulnerable
EOF
