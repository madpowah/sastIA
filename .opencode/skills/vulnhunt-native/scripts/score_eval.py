#!/usr/bin/env python3
"""Score a VulnHunter Native report against an expected.json.

Usage:
  python3 score_eval.py REPORT EXPECTED.json --mode vulnerable
  python3 score_eval.py REPORT EXPECTED.json --mode fixed

Vulnerable mode: each must_find entry must be present with enough mechanism
detail (file, function, missing fields/guard, keywords).

Fixed mode: the report must NOT contain a confirmed VULN section for the known
file/function. This is a precision control.

This is a heuristic eval, not a proof. Use it to catch regressions, not to
replace human review.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("expected")
    ap.add_argument("--mode", choices=["vulnerable", "fixed"], default="vulnerable")
    ap.add_argument("--require-confirmed", action="store_true",
                    help="only score text inside ### [VULN-...] sections")
    args = ap.parse_args()

    text = Path(args.report).read_text(errors="replace")
    expected = json.loads(Path(args.expected).read_text())

    scope_text = text
    if args.require_confirmed:
        sections = re.split(r"(?=#{2,4}\s*\[VULN-)", text)
        scope_text = "".join(
            s for s in sections if re.match(r"#{2,4}\s*\[VULN-", s)
        )
    ntext = norm(scope_text)

    if args.mode == "fixed":
        failures = []
        for item in expected.get("must_find", []):
            fn = item.get("function", "")
            fp = item.get("file", "")
            sections = re.split(r"(?=#{2,4}\s*\[VULN-)", text)
            for sec in sections:
                if "[VULN-" not in sec:
                    continue
                if (fn and fn in sec) or (fp and Path(fp).name in sec):
                    failures.append(
                        f"fixed-mode: confirmed section mentions {fn or fp}"
                    )
                    break
        if failures:
            print("FAIL")
            for f in failures:
                print(" -", f)
            return 1
        print("PASS: no confirmed finding for the known bug on the fixed snapshot")
        return 0

    ok = True
    for item in expected.get("must_find", []):
        checks = []

        def check(label, cond):
            nonlocal ok
            checks.append((label, bool(cond)))
            if not cond:
                ok = False

        fp = item.get("file", "")
        fn = item.get("function", "")
        check(f"file {fp}", fp and Path(fp).name in ntext)
        check(f"function {fn}", fn and fn.lower() in ntext)

        fields = item.get("missing_fields", [])
        if fields:
            present = [f for f in fields if re.search(r"\b" + re.escape(f.lower()) + r"\b", ntext)]
            need = item.get("min_fields", len(fields))
            check(f"missing fields ({len(present)}/{len(fields)}, need {need})",
                  len(present) >= need)

        guard = item.get("missing_guard")
        if guard:
            g = norm(guard)
            # Accept the full expression or its key tokens.
            tokens = [t for t in re.split(r"[^a-z0-9_>.-]+", g) if len(t) > 3]
            hit = g in ntext or (tokens and sum(t in ntext for t in tokens) >= max(2, len(tokens) // 2))
            check(f"guard {guard}", hit)

        null = item.get("null_deref")
        if null:
            check(f"null deref {null}", norm(null) in ntext or "null" in ntext)

        comp = item.get("composition")
        if comp:
            toks = [t for t in re.split(r"[^a-z0-9]+", comp.lower()) if len(t) > 2]
            check(f"composition {comp}",
                  sum(t in ntext for t in toks) >= max(2, len(toks) // 2))

        for kw in item.get("keywords", []):
            check(f"keyword {kw}", kw.lower() in ntext)

        print(f"== {item.get('function', fp)} ==")
        for label, passed in checks:
            print(f"  [{'OK' if passed else 'MISS'}] {label}")

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
