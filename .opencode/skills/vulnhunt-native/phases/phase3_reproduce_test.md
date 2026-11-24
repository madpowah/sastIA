# Phase 3 — Reproduce, Test, and Validate (Native)

> Confirmed findings only (Phase 2b + Phase 2c). Produce a PoC and an exploit
> test for each. If `TARGET_MODE=dynamic`, run the validation; otherwise
> produce a validation plan and mark unproven findings `Potential`.

## Output destinations

- PoCs: `${VULNHUNT_DIR}/poc/VULN-NNN_*.md`
- Exploit tests: `${VULNHUNT_DIR}/exploit_tests/test_vuln_NNN_*`
- Phase summary: `${VULNHUNT_DIR}/phase3_output.md`

## Pre-Phase 3 completeness check

Map every confirmed finding to an ID. Preserve the `VULN-NNN` IDs assigned in
Phase 2b; assign new sequential IDs only to confirmed compositions from Phase
2c.

| VULN-NNN | Phase 2b/2c # | Title | Severity |
|---|---|---|---|

Row count must equal the total confirmed findings. A confirmed finding cannot
be removed without an explicit FAIL verdict from its exploit test.

## Phase 3a — PoC

Choose the appropriate format:

### A. Static data/state flow trace

```text
[VULN-NNN] Static PoC: Title

1. ENTRY: attacker sends/does ...
   -> file:line  function()
   -> field `x` = ...

2. STATE: precondition (snd_una=..., session=..., pool=...)
   -> file:line

3. PROPAGATION: x -> function -> sink
   -> file:line

4. SINK: dangerous operation
   -> file:line
   -> concrete value: ...

5. IMPACT: crash / UAF / auth bypass / info leak / privilege
```

Requirements: concrete values, file:line at every step, the literal dangerous
value, and a concrete impact.

### B. Runnable PoC (when a test environment is available)

- C/C++ harness that calls the library API;
- packet capture/PCAP or Scapy script for a network daemon;
- shell/Python script for a CLI or file parser;
- kernel module/syscall harness for a kernel target;
- unit test in the project's framework.

```c
/* Example: two handles sharing a connection pool */
CURL *a = curl_easy_init();
CURL *b = curl_easy_init();
curl_easy_setopt(a, CURLOPT_SSLCERT, "client.pem");
curl_easy_setopt(a, CURLOPT_SSLKEY, "old.key");
/* ... perform transfer A ... */
curl_easy_setopt(b, CURLOPT_SSLCERT, "client.pem");
curl_easy_setopt(b, CURLOPT_SSLKEY, "new.key");
/* ... perform transfer B; does it reuse A's connection? ... */
```

## Phase 3b — Exploit test (mandatory)

The test must prove the **attacker's goal**, not just that a code path runs.

| Class | What "success" means |
|---|---|
| Memory corruption | ASan/KASan report, crash at the target address, controlled write/read |
| UAF/double free | sanitizer report or observable reuse |
| Integer/domain | undersized allocation + OOB write/read |
| NULL deref | crash at the NULL access (remote panic if applicable) |
| Auth bypass | access to a resource/privilege without the credential |
| IDENT reuse | second handle uses the first identity / stale credential |
| Path traversal | file outside the intended directory read/written |
| Command injection | attacker's command executes |
| Format string | `%n` write or leak observed |
| Privilege escalation | effective UID/capability changes |
| Info leak | secret/key/memory content returned |
| DoS | service/daemon/kernel crashes or becomes unavailable |

A test that only proves "the vulnerable function is called" is a **FAIL**.

### Test structure

```text
test_vuln_NNN_<name>:
  Setup: build target, start daemon/VM, prepare packet/file/API state
  Action: send the exact payload/sequence from the PoC
  Assert: attacker's goal achieved (crash report, auth bypass, read, ...)
  Cleanup: stop target, remove temp files
```

### Test outcomes

| Result | Action |
|---|---|
| PASS (goal achieved) | Confirmed; proceed to fix strategy |
| CODE RUNS but mitigated | Code Smell; document the defense |
| FAIL (blocked) | Investigate why; read the actual path |
| FAIL (can't build/run) | `Potential`; write validation plan |
| FAIL (type/compiler prevents) | Eliminate with evidence |

**Mandatory exploitation attempt before Code Smell**: write the PoC and test
file first, then document why it fails.

## Phase 3c — Dynamic validation (optional)

If `TARGET_MODE=dynamic`:

1. **Build** with sanitizers:
   - C/C++: `-fsanitize=address,undefined` (ASan/UBSan);
   - kernel: KASan/KMSan config, VM or privileged container;
   - Rust: `-Z sanitizer=address` (nightly) or Miri for unsafe blocks.
2. **Run the harness**:
   - library: link the test harness against the built library;
   - daemon: start it in a network namespace/container, send packets;
   - kernel: boot the VM, load the module/trigger the syscall;
   - CLI/file: run with the crafted file/args.
3. **Capture evidence**: sanitizer report, panic trace, `dmesg`, packet
   capture, `strace`, core dump.
4. **Minimize**: reduce the PoC to the smallest packet/input that still
   triggers.
5. Save evidence to `${VULNHUNT_DIR}/evidence/VULN-NNN/`.

If dynamic validation is impossible, write a **validation plan** with exact
commands, build flags, and expected output. Mark the finding `Potential`.

## Phase 3d — Fix strategy

For each confirmed finding, propose a fix that eliminates the class, not just
the PoC:

- add the missing guard/field/NULL check;
- change the domain/type;
- reorder the privilege drop;
- bind the credential to the resource;
- add a regression test.

Do not apply the fix to the source tree; this audit is read-only.

## Phase 3 output

Write `${VULNHUNT_DIR}/phase3_output.md`:

| Finding | PoC | Test | Result | Evidence | Status |
|---|---|---|---|---|---|

Only PASS findings proceed to the final report as `Confirmed`. `Potential`
findings are reported separately with the validation plan.

## Where to put tests

```text
${VULNHUNT_DIR}/exploit_tests/
  test_vuln_001_curl_conn_reuse.c
  test_vuln_002_sack_panic.py
  test_vuln_003_path_traversal.sh
```
