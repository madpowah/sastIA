# Spec and API Contract Sources

A spec is an oracle, not a substitute for reading the code. Use it to generate
obligations, then verify each obligation at a file:line.

## Sources by target

| Target | Sources |
|---|---|
| TCP/IP | RFC 793, 2018 (SACK), 3168, 4291, 8200 |
| TLS | RFC 8446, 5246, 6125, 5280 |
| HTTP/2/3 | RFC 7540, 9113, 9114 |
| DNS | RFC 1035, 2181, 6891, 7873 |
| SSH | RFC 4251–4254, 5656, 8332 |
| QUIC | RFC 9000, 9001, 9002 |
| File formats | format spec, reference parser, fuzzing corpus |
| Kernel | man pages, `Documentation/`, UAPI headers |
| Library | public headers, man pages, API docs, changelog |
| Crypto | NIST/FIPS, RFC, library docs |

## How to use

1. Quote the clause (number + short text). If you cannot quote it, mark
   `unverified` — do not hallucinate a spec obligation.
2. Write the code obligation as a checkable statement:
   - "a SACK block start must be >= snd_una";
   - "the certificate must be valid for the hostname";
   - "the session ticket must be bound to the client certificate".
3. Find the enforcement point(s). If there are multiple backends/parsers, list
   all of them.
4. Record divergence: one backend enforces it, another does not.

## Table

| Clause | Obligation | Enforcement point(s) | Enforced? | Divergence? |
|---|---|---|---|---|

## Warning

Specs describe the ideal; implementations have extensions, quirks, and
compatibility paths. A spec violation is a candidate only if the code's
security model relies on that clause. Record the reliance.
