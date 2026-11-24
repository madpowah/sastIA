# Native Vulnerability Archetypes

Use these as hypotheses, not as a checklist to force findings.

| # | Archetype | Real example | Detection question |
|---|---|---|---|
| 1 | Incomplete identity predicate | curl CVE-2026-8932 | Which fields change the identity? Are they all in the compare/match/key? |
| 2 | Marker vs value in a cache key | curl scache `:CCERT` | Does the key contain the value or only its presence? |
| 3 | Credential selection fallback | curl CVE-2026-8926 (.netrc) | Can (host, user) fall back to another user's credential? |
| 4 | Policy predicate incomplete over types | curl CVE-2026-9547 (SSH host key) | Are all key types/algorithms validated on every backend? |
| 5 | Callback reentrancy UAF | curl CVE-2026-9080 (`curl_easy_pause`) | Can a callback mutate state in use? |
| 6 | Lifetime across cleanup | curl CVE-2026-8925 / 10536 | Can cleanup free what another branch still uses? |
| 7 | Guard skipped on degenerate path | OpenBSD SACK Bug 1 | Which guard runs only under a condition on another field? |
| 8 | Signed comparison overflow at 2^31 | OpenBSD SACK | Is every signed subtraction a total order over the input domain? |
| 9 | NULL cursor after deleting the last node | OpenBSD SACK Bug 2 | After a delete, which cursor is NULL, and who uses it? |
| 10 | Sentinel collision | FFmpeg `-1` / 65535 | Can a valid value equal the sentinel? |
| 11 | Length-domain mismatch | FFmpeg 16-bit table vs 32-bit counter | Are length and index in the same width/unit? |
| 12 | Per-request security state stored per-connection | curl CVE-2026-8932 | What security state survives the request? |
| 13 | Privilege drop after parsing | classic setuid daemon | Is the drop before attacker input? Can it be undone? |
| 14 | IPC peer identity spoofing | Unix socket / D-Bus | Is the peer credential kernel-verified before the privileged op? |
| 15 | TOCTOU on a path/permission | temp file, symlink | Is there a check-then-use gap on a path or fd? |
| 16 | Partial initialization on error path | `goto fail` | Is every field initialized before cleanup/use? |
| 17 | Type confusion / union misuse | tagged pointer, `void *` context | Can one type be read as another? |
| 18 | Refcount underflow/overflow | object lifetime | Can a refcount wrap or be decremented twice? |
| 19 | State-machine invalid transition | protocol handshake | Do two valid transitions compose into an invalid state? |
| 20 | Spec/backend divergence | TLS backends | Does one backend implement the check while another does not? |

## How to use

For each partition, pick the 3–5 archetypes most plausible for the target and
turn them into explicit questions. Record the answer in the results file. An
archetype that does not apply is fine; an archetype that was never asked is a
coverage gap.
