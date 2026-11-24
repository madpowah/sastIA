#!/usr/bin/env python3
"""Guard-coverage eval for the OpenBSD TCP SACK bug.

This is an eval unit test, not a production SAST engine. It checks that
tcp_sack_option() has an unconditional start guard and a NULL guard on the
append path.

Usage:
  python3 guard_coverage.py sys/netinet/tcp_input.c
"""

import re
import sys
from pathlib import Path


def _matching(text: str, pos: int, open_ch: str, close_ch: str) -> int:
    depth = 0
    i = pos
    while i < len(text):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def extract_function(text: str, name: str) -> str:
    for m in re.finditer(r"\b" + re.escape(name) + r"\s*\(", text):
        open_paren = text.find("(", m.start())
        close_paren = _matching(text, open_paren, "(", ")")
        if close_paren < 0:
            continue
        j = close_paren + 1
        while j < len(text) and text[j].isspace():
            j += 1
        if j < len(text) and text[j] == "{":
            close_brace = _matching(text, j, "{", "}")
            if close_brace > 0:
                return text[j + 1:close_brace]
    raise SystemExit(f"definition of {name} not found")


def block_after_if(text: str, condition_re: str) -> str | None:
    m = re.search(r"if\s*\(" + condition_re + r"\)\s*\{", text)
    if not m:
        return None
    open_brace = text.find("{", m.end() - 1)
    close_brace = _matching(text, open_brace, "{", "}")
    if close_brace < 0:
        return None
    return text[open_brace + 1:close_brace]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: guard_coverage.py sys/netinet/tcp_input.c")
    body = extract_function(Path(sys.argv[1]).read_text(errors="replace"),
                            "tcp_sack_option")

    start_re = r"SEQ_LT\s*\(\s*sack\.start\s*,\s*tp->snd_una\s*\)"
    th_ack_block = block_after_if(
        body, r"SEQ_GT\s*\(\s*th->th_ack\s*,\s*tp->snd_una\s*\)"
    )
    present = bool(re.search(start_re, body))
    nested = bool(th_ack_block and re.search(start_re, th_ack_block))
    has_start = present and not nested
    has_null = bool(re.search(
        r"p\s*!=\s*NULL\s*&&\s*SEQ_LT\s*\(\s*tp->rcv_lastsack\s*,\s*sack\.start\s*\)",
        body,
    ))

    print(f"[{'OK' if has_start else 'MISSING'}] unconditional start guard")
    print(f"[{'OK' if has_null else 'MISSING'}] NULL guard on append")
    return 0 if has_start and has_null else 1


if __name__ == "__main__":
    sys.exit(main())
