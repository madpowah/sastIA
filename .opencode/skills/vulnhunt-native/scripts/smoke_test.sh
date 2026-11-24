#!/usr/bin/env bash
# Smoke test for the eval detectors.
#
#   ./smoke_test.sh [fixture_dir]
#
# Fetches the fixtures if needed, then checks that the detectors fire on the
# vulnerable snapshots and stay clean on the fixed ones.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIX="${1:-/tmp/opencode/vulnhunt-native-fixtures}"

if [ ! -f "$FIX/tcp_input_1.464.c" ]; then
  "$SCRIPT_DIR/fetch_fixtures.sh" "$FIX" >/dev/null
fi

fail=0

curl_vuln_out="$(python3 "$SCRIPT_DIR/field_coverage.py" "$FIX/curl_vuln" 2>&1 || true)"
if grep -q "key" <<<"$curl_vuln_out"; then
  echo "[OK] field_coverage flags the vulnerable curl snapshot"
else
  echo "[FAIL] field_coverage did not flag the vulnerable curl snapshot"
  fail=1
fi

curl_fixed_out="$(python3 "$SCRIPT_DIR/field_coverage.py" "$FIX/curl_fixed" 2>&1 || true)"
if grep -q "OK" <<<"$curl_fixed_out"; then
  echo "[OK] field_coverage is clean on the fixed curl snapshot"
else
  echo "[FAIL] field_coverage flags the fixed curl snapshot"
  fail=1
fi

obsd_vuln_out="$(python3 "$SCRIPT_DIR/guard_coverage.py" "$FIX/tcp_input_1.464.c" 2>&1 || true)"
if grep -q "MISSING" <<<"$obsd_vuln_out"; then
  echo "[OK] guard_coverage flags the vulnerable OpenBSD snapshot"
else
  echo "[FAIL] guard_coverage did not flag the vulnerable OpenBSD snapshot"
  fail=1
fi

obsd_fixed_out="$(python3 "$SCRIPT_DIR/guard_coverage.py" "$FIX/tcp_input_1.465.c" 2>&1 || true)"
if grep -q "OK" <<<"$obsd_fixed_out"; then
  echo "[OK] guard_coverage is clean on the fixed OpenBSD snapshot"
else
  echo "[FAIL] guard_coverage flags the fixed OpenBSD snapshot"
  fail=1
fi

exit "$fail"
