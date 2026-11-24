#!/usr/bin/env python3
"""Field-coverage eval for curl CVE-2026-8932.

This is an eval unit test, not a production SAST engine. It checks that a
security-relevant field of ssl_config_data is missing from ssl_primary_config
and therefore invisible to match_ssl_primary_config().

Usage:
  python3 field_coverage.py /path/to/curl/source
"""

import re
import sys
from pathlib import Path

SECURITY_FIELDS = {
    "clientcert", "cert_blob", "cert_type",
    "key", "key_blob", "key_type", "key_passwd",
    "CAfile", "CApath", "ca_info_blob", "issuercert", "issuercert_blob",
    "CRLfile", "pinned_key",
    "verifypeer", "verifyhost", "verifystatus",
    "cipher_list", "cipher_list13", "curves", "signature_algorithms",
    "version", "version_max", "ssl_options",
}


def extract_struct(text: str, name: str) -> str:
    m = re.search(r"struct\s+" + re.escape(name) + r"\s*\{", text)
    if not m:
        raise SystemExit(f"struct {name} not found")
    i = m.end()
    depth = 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[m.end():i - 1]


def extract_function(text: str, name: str) -> str:
    for m in re.finditer(r"\b" + re.escape(name) + r"\s*\(", text):
        open_paren = text.find("(", m.start())
        depth = 1
        j = open_paren + 1
        while j < len(text) and depth:
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
            j += 1
        if depth:
            continue
        k = j
        while k < len(text) and text[k].isspace():
            k += 1
        if k < len(text) and text[k] == "{":
            depth = 1
            end = k + 1
            while end < len(text) and depth:
                if text[end] == "{":
                    depth += 1
                elif text[end] == "}":
                    depth -= 1
                end += 1
            return text[k + 1:end - 1]
    raise SystemExit(f"definition of {name} not found")


def fields_of(body: str) -> list[str]:
    names = []
    for m in re.finditer(r"\bBIT\s*\(\s*(\w+)\s*\)", body):
        names.append(m.group(1))
    for line in body.splitlines():
        line = line.split("/*")[0].strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(
            r"(?:const\s+)?(?:unsigned\s+)?(?:struct\s+\w+|char|int|long|short|"
            r"uint\d*_t|int\d*_t|size_t|curl_\w+|bool|CURLcode)\s*\*?\s*(\w+)\s*[;,]",
            line,
        )
        if m:
            names.append(m.group(1))
    return names


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: field_coverage.py /path/to/curl/source")
    root = Path(sys.argv[1])
    urldata = (root / "lib/urldata.h").read_text(errors="replace")
    vtls = (root / "lib/vtls/vtls.c").read_text(errors="replace")

    primary = fields_of(extract_struct(urldata, "ssl_primary_config"))
    data = fields_of(extract_struct(urldata, "ssl_config_data"))
    compared = set(re.findall(r"\bc[12]->(\w+)\b",
                              extract_function(vtls, "match_ssl_primary_config")))

    findings = []
    for f in data:
        if f in SECURITY_FIELDS and f not in primary:
            findings.append(f"A) {f}: in ssl_config_data, absent from "
                            f"ssl_primary_config/match")
    for f in primary:
        if f in SECURITY_FIELDS and f not in compared:
            findings.append(f"B) {f}: in ssl_primary_config, not compared")

    if findings:
        print("FINDINGS")
        for line in findings:
            print(" -", line)
        return 1
    print("OK: all security-relevant primary fields are compared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
