# Phase 2b — Adversarial Verification (Native)

> Candidates come from parallel lens agents with partial file scope. Your job
> is to try to disprove each one — but **without** discarding the halves of a
> composition. Every candidate is a hypothesis until verified.

## Candidate manifest (mandatory)

Read every `results/*.md`. Build a flat list of all CANDIDATE and LATENT
entries. Count them. Your verdict table must have exactly as many CANDIDATE
rows.

LATENT entries go to `latent_defects.md`, not the verdict table. They still
need a precondition and an effect.

## Consensus-skip

- **Consensus Gate 1 fail**: all agents for the partition cite the same
  reachability evidence at the same file:line → record
  `"ELIMINATED — Gate 1 consensus [file:line]"`.
- **Split decision**, or different evidence → full verification.
- **Any CANDIDATE from any agent** → full verification.
- **Sink-driven candidates** → always full verification.

Include consensus-skipped rows in the table marked `consensus-skipped`.

## For each candidate

### 1. Gates complete?

Check Gate 0/1/2a/2b/3/4. Fill any blank. A blank gate is a red flag.

**No-input elimination does NOT apply to**:
- remotely triggerable availability bugs;
- state-composition bugs;
- identity/cache reuse bugs.

A crash caused by a crafted packet, a connection-reuse sequence, or a
state-machine transition is a security finding even if no scalar "input"
appears in the immediate function. Record the trigger sequence and proceed.

### 2. Reachability

Re-verify with fresh eyes:
- all call sites, not just the traced path;
- the state sequence (packet 1 → packet 2, API call A → B);
- for libraries: all public API callers;
- for kernels: syscall/packet/ioctl path;
- for daemons: network/IPC path and auth state.

A function called from one dev-only path and one production path is
production-reachable. Route/entry-point registration is not reachability by
itself.

### 3. Defenses and domain

Identify every defense between the source/state and the sink. For each:
- read the actual code;
- determine the domain it covers (width, signedness, unit, range);
- determine the paths on which it executes;
- check whether it covers the specific sink.

**Defense classes**:
- length/range checks (same domain?);
- integer overflow checks (before the arithmetic?);
- path canonicalization (`realpath`, `openat`, `O_NOFOLLOW`);
- privilege drop (before parsing? irreversible?);
- IPC peer credential check (kernel-verified?);
- refcount/lifetime;
- sanitizer/allocator hardening;
- TLS/certificate/host-key verification (all backends?).

**Validation composition**: a guard that is skipped on a reachable path, or
that is a total order only within a limited domain, is ineffective. Evaluate
guards together, not one at a time.

**Sanitizer/validator scope mismatch is a vulnerability, not a mitigation.**
Examples:
- byte count vs element count;
- signed int vs `size_t`;
- `strlcpy` for binary data;
- path prefix check vs symlink;
- HTML/XML escaping for a shell;
- one TLS backend validated, another not.

### 4. Severity calibration

Re-check against the native severity definitions in `phase2_shared.md`:
- Does the impact type match the tier?
- Is the attacker remote/local/authenticated?
- Is the crash a remote panic (High) or a local self-crash (Low)?
- Is it a cross-principal identity issue or same-principal stale state?
- Does exploitation require a chain/race? (lower, but not eliminated)

**Remote availability floor**: remote unauthenticated panic of a daemon/kernel
is at least High. Do not downgrade to "reliability".

### 5. Downgrade discipline

Before downgrading/eliminating:
1. Grep all call sites of the sink function.
2. Read each call site; check parameters and attacker control.
3. Trace callers of callers for shared utilities.
4. Document each call site's reachability and exploitability.

A finding can only be downgraded when **all** call sites are verified
non-exploitable. One safe call site does not clear the others.

**Multi-writer property rule**: when dismissing a state value as
"server-controlled", grep all write paths (setters, storage writes, direct
assignments). A property with N writers is only trusted if all N are trusted.

### 6. SAFE spot-check

For each partition, re-verify 2–3 SAFE inputs closest to dangerous sinks
(parsers, allocation, privilege drop, pools, auth). Fresh Read/Grep.

### 7. Sink-coverage gap check

Grep for high-risk sinks (allocation, copy, free, exec, open, privilege drop,
auth checks, pool lookup). For each:
- no disposition at all → gap; trace backward;
- multiple distinct sources → verify each independently.

### 8. Comment skepticism / hypotheses

For every dismissed/downgraded finding, check whether a gate was satisfied by
prose rather than code:
- "by design" / "intentional" / "backward compat" → Gate 0;
- `sanitize()`/`validate()`/`safe*()` naming → Gate 2b;
- "the caller validates" / "the kernel checks" / "the allocator prevents" →
  Gate 2b/Gate 3;
- "internal only" / "not user-facing" → Gate 1;
- "type-safe" / "schema validated" → Gate 2b.

If a gate was satisfied by prose, re-verify empirically.

**Comments as hypotheses**: a comment that asserts an invariant ("last hole is
p and it's not NULL", "the connection matches the setup", "validated by the
caller") is a proof obligation. Test it. Do not use the comment as clearance.

### 9. Recall mode (native/critical targets)

Before dropping a candidate as FALSE POSITIVE, Code Smell, DESIGN-INTENT, or
unreachable, record it in `latent_defects.md` with:
- the precondition that makes it harmless;
- the effect if the precondition is false;
- what would make the precondition false.

Do not discard a half of a composition. Phase 2c evaluates the composition.

### 10. Composition handoff

No candidate may be eliminated if it appears in `latent_defects.md` as a half
of a pair/sequence, unless Phase 2c has evaluated the composition.

## Verification output

Present this table before Phase 2c:

| Finding | Gates complete? | Reachable? | Defense/domain covers? | Severity correct? | All call sites? | Verdict |
|---|---|---|---|---|---|---|

**FALSE POSITIVE verdicts require evidence**: cite the file:line of the
defense, type constraint, or non-attacker origin. "Not reachable" is not
enough; cite the path/state.

**Anti-merge rule**: do not merge findings that differ in (a) attacker
privilege, (b) entry point, (c) state object/connection, or (d) exploited
parameter. Each gets its own row. Silent omission is merging.

**Drop all FALSE POSITIVE findings from the VULN table.** They go to the Code
Quality / latent sections with a rationale.

## Output

Write `${VULNHUNT_DIR}/phase2b_output.md` with:
- candidate manifest count;
- verdict table;
- confirmed findings (full candidate format);
- false positives with evidence;
- latent defects appended to `latent_defects.md`;
- a list of `latent_defects.md` entries to pass to Phase 2c.
