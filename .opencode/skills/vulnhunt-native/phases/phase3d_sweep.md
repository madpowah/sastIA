# Phase 3d — Sweep Verification (Native)

> Every confirmed root cause must be enumerated across the **full** codebase,
> not just the originating partition. Native bugs often repeat: the same
> missing field in another predicate, the same signed comparison in another
> parser, the same free-then-use pattern in another list.

## Pre-sweep validation

Count distinct sink file:line values across confirmed findings. If that count
exceeds the VULN-NNN count, findings were collapsed — expand them before
sweeping.

## Sweep patterns

### 1. Field/predicate coverage

If a confirmed finding is an omitted identity field:

- list every struct with a `compare`/`match`/`key`/`hash` function;
- for each, diff its fields against the function's references;
- triage each omitted security-relevant field.

```bash
# Example: fields vs match function
rg -n "match_|compare_|key_make|peer_key|hash_" src/
```

### 2. Predicate coverage

For every `match_*`, `eq_*`, `is_*`, `check_*`, `validate_*` on a security
object, list the fields it reads. Diff against the object's fields.

### 3. Marker vs value

Grep for string key components / cache markers:

```bash
rg -n '":CCERT"|":AUTH"|":PROXY"|has_cert|auth_type' src/
```

A marker that records presence instead of value is a collision candidate.

### 4. Signed comparison / domain

Grep for sequence comparisons and signed subtraction:

```bash
rg -n "SEQ_LT|SEQ_GT|SEQ_LEQ|SEQ_GEQ|\(int\)\([^)]*-[^)]*\)|before\(|after\(" src/
```

For each, verify the domain and the 2^31/2^63 boundary. Check every use of the
same macro in the codebase.

### 5. Free-then-use / lifetime

Grep for frees and puts:

```bash
rg -n "\bfree\(|pool_put|kfree|delete |refcount_dec|TAILQ_REMOVE|LIST_REMOVE" src/
```

For each, check the cursor/alias after the free and every later use.

### 6. List surgery

Grep for `->next =`, `TAILQ_INSERT`, `TAILQ_REMOVE`, `RB_INSERT`,
`RB_REMOVE`. Check empty-list, head/tail, and cursor invariants.

### 7. Spec clause

For each RFC/protocol clause implicated by a finding, check every parser that
implements it. A fix in one parser may be missing in another (e.g., IPv4 vs
IPv6, TCP vs UDP, one TLS backend vs another).

### 8. Sentinel collision

Grep for sentinel initializations and comparisons (`-1`, `0xFF`, `0xFFFF`,
`NULL`, `SIZE_MAX`, `memset(..., -1, ...)`). Check whether a valid value can
equal the sentinel.

### 9. Length-domain mismatch

Grep for length/count fields and casts:

```bash
rg -n "\(u?int(8|16|32)_t\)|\(size_t\)|\(int\)|\* sizeof|<< 8|>> 8" src/
```

Check allocation vs copy, index vs count, table width vs counter width.

### 10. Reentrancy

Grep for callbacks, function pointers, signal handlers, destructors, `atexit`,
`longjmp`. Check whether they can re-enter a state in use.

### 11. Auth coverage

If a confirmed finding is a missing auth check:

- enumerate all handlers/endpoints/IPC methods in the same module;
- any sibling with a check while this one has none → candidate CWE-306/862;
- check every auth backend/branch.

### 12. Privilege drop

If a confirmed finding is a privilege issue:

- enumerate all setuid/setgid/capability/seccomp/chroot/pledge sites;
- check every daemon startup path;
- check every re-exec/reload path.

## For each instance

1. File:line and the value/state.
2. Is it attacker-controlled? Trace backward through stores/state.
3. What mitigation exists? Read the code.
4. Triage: **CANDIDATE** / **MITIGATED** (reason) / **DEV-ONLY** / **LATENT**.
5. A CANDIDATE goes through the full pipeline (gates, PoC, test).

Do not assume an instance is exploitable because it shares a root cause.
Different call sites may have different state, validation, or context.

## Sweep output

Write `${VULNHUNT_DIR}/phase3d_output.md`:

| Root cause | Pattern | Total found | Candidates | Mitigated | Dev-only | Remaining |
|---|---|---|---|---|---|---|

If any row has `Remaining > 0`, those are unaccounted instances — investigate
before the report.

## Pipeline for sweep candidates

1. Gates (Gate 0–4) from `phase2_shared.md`.
2. If individually harmless/unreachable → `latent_defects.md` and Phase 2c.
3. PoC + exploit test (Phase 3).
4. Only PASS findings become VULN-NNN.
