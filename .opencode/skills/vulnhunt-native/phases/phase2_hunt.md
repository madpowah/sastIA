# Phase 2 — Vulnerability Hunting (Native)

> Read Phase 0 and Phase 1 outputs. Dispatch parallel trace agents by lens.
> Each agent traces all inputs in its partition but only evaluates its lens.

## Class groups

| Group | ID | Focus |
|---|---|---|
| Injection | INJ | command, path, format string, environment, deserialization, SQL (embedded), template, log, file/archive parsing |
| Authorization | AUTH | authn/authz, privilege boundaries, setuid/capabilities, IPC peer credentials, sandbox, file permissions, confused deputy |
| Memory/Lifetime | MEM | bounds, integer/domain mismatch, UAF, double free, container cursor, reentrancy, type confusion |
| Protocol/State | PROTO | wire parsing, state machine, sequence arithmetic, guard composition, packet ordering, spec conformance |
| Identity/Reuse | IDENT | pools, sessions, reuse predicates, key completeness, credential selection, cross-handle isolation |
| Composition | COMPOSE | Phase 2c only; not dispatched here |

## Dispatch procedure

For each production partition `SG-N`:

1. Create `${VULNHUNT_DIR}/partitions/sg-N_data.md` containing:
   - assigned inputs (full rows from the inventory);
   - entry points;
   - file scope;
   - state objects and invariants in scope;
   - shared infrastructure catalog;
   - threat model row;
   - risk notes.
2. Spawn one agent per applicable lens with `phase2_shared.md` and
   `phase2_class_{lens}.md`.
3. Spawn one sink-driven audit agent as the final wave.

**Minimum agent count = (5 × production_partition_count) + 1.**

If Phase 0 marked a lens not applicable with a concrete reason, record the skip
in `phase1_output.md` and subtract it. Any other skip is a coverage failure.

Dispatch in waves of at most 10 agents. Wait for each wave's results files.
Do not dispatch all agents at once (rate limits, context).

### Budget and scale

- Target **≤ 30 agents per run**. If the formula exceeds 30, split the target
  into separate subsystem audits (e.g., `net/`, `fs/`, `ipc/`) and run them
  independently.
- If a partition has >20 inputs or >15 files, split it before dispatch.
- If a lens is not applicable, skip it **only** with the Phase 0 reason.
- Record the actual agent count, token cost, and wall time in
  `phase1_output.md` (or a `cost.md`). A recall gain that costs 10× must be
  visible in the comparison.

## Trace agent prompt template

```text
You are a {CLASS} trace agent for partition {SG_ID}. Your lens focus:
{CLASS_FOCUS}

You are responsible ONLY for vulnerability classes in your class file. If an
input reaches a sink for a DIFFERENT lens, flag as:
  CROSS-LENS (input #, sink file:line, suspected lens: INJ/AUTH/MEM/PROTO/IDENT)

Read these files IN ORDER before starting:
1. ${PHASES_DIR}/phase2_shared.md — iteration rules, gates, severity, output
2. ${PHASES_DIR}/phase2_class_{class}.md — sink reference and lens method
3. ${VULNHUNT_DIR}/partitions/sg-{SG_ID}_data.md — inputs and file scope
4. ${VULNHUNT_DIR}/state_identity_inventory.md — objects, pools, fields
5. ${VULNHUNT_DIR}/invariant_register.md — invariants and proof obligations
6. ${VULNHUNT_DIR}/negative_space.md — expected vs present guards

For each input, return:
- CANDIDATE (input #, sink file:line, lens, invariant violated)
- SAFE (input #, reason — only for your lens's sinks)
- NO-MATCH (input #) -> input does not reach sinks in your lens
- CROSS-LENS (input #, sink file:line, suspected lens)
- LATENT (input #, reason) -> individually harmless/unreachable; write to
  latent_defects.md
- DESIGN-INTENT (input #, reason) -> only if the design precondition holds

Write results to: ${VULNHUNT_DIR}/results/sg-{SG_ID}_{class}_results.md

IMPORTANT: Your return message must be under 20 words.
```

## Sink-driven audit agent (final wave)

This agent works backward from dangerous patterns, not forward from inputs. It
catches missing checks that no input trace reaches.

```text
You are a sink-driven audit agent for a native target. Your job is to audit
dangerous patterns backward: who can reach them, under what state, and what
check is missing.

Perform these audits:

1. PRIVILEGE SINK AUDIT: grep for setuid/seteuid/setgid/setresuid, capability
   changes (capset, prctl), chroot, pledge/unveil, seccomp, namespace
   creation, exec of user-controlled paths. For each, verify the drop happens
   BEFORE attacker-controlled parsing/processing, and cannot be undone.
2. FILE PERMISSION AUDIT: grep for open/openat/fopen/creat/mkdir/chmod/chown,
   temporary files, symlink handling, O_NOFOLLOW, umask. Check for TOCTOU,
   symlink escape, predictable temp names, world-writable paths.
3. IPC PEER AUDIT: grep for SO_PEERCRED, getpeereid, SCM_CREDENTIALS,
   accept4, D-Bus policy, netlink credentials. Verify peer identity is checked
   before privileged operations.
4. CREDENTIAL/CACHE AUDIT: grep for connection/session pools, caches, peer
   keys, credential lookup. For each, list fields compared vs fields that can
   change identity.
5. ALLOCATION/FREE AUDIT: grep for malloc/calloc/realloc/alloca/pool_get,
   free/pool_put/refcount. Check size domain, free paths, aliases, reentrancy.
6. CALLBACK/REENTRANCY AUDIT: grep for function pointer calls, callbacks,
   signal handlers, destructors, atexit. Check whether a callback can re-enter
   and mutate state in use.
7. CRYPTO AUDIT: grep for crypto APIs. Check algorithm/mode/key size, key
   storage, random source, certificate/host-key verification, TLS session
   resumption.
8. ENVIRONMENT AUDIT: grep for getenv, PATH, LD_PRELOAD, locale, TMPDIR,
   HOME. Check whether privileged code trusts attacker-controlled environment.

For each finding, return the candidate format used by trace agents (but do NOT
assign VULN-NNN IDs). Include gate results where applicable.
```

## Results aggregation

1. Merge input dispositions across lenses:
   - CANDIDATE if any agent returns CANDIDATE;
   - SAFE only if all agents return SAFE/NO-MATCH;
   - LATENT goes to `latent_defects.md`;
   - CROSS-LENS: use the target lens agent's disposition; re-dispatch only if
     the target lens did not evaluate that sink.
2. Assign `VULN-NNN` to candidates in dispatch order, then input order.
3. Deduplicate only the **same sink at the same file:line**. Keep the most
   pessimistic severity and the union of flows.
4. Completeness: total dispositions must equal the input inventory count.
5. **Absent-state checkpoint**: for every security-critical state condition
   (auth, session, lock, privilege drop, bounds, list-empty), answer: "if this
   state is missing/degenerate, does the check fail closed or fail open?"
   Every fail-open is a candidate.
6. Present the merged candidate list and resolved inventory before Phase 2b.

## Fallback: large partition

If a partition is too large to parallelize effectively, process it sequentially
by entry point × lens, saving intermediate results to
`${VULNHUNT_DIR}/candidates/sg-N_entry_lens.md`. Do not skip a lens.

## Dispatch checklist (mandatory)

- [ ] All applicable lens agents spawned and produced a results file
- [ ] One sink-driven agent spawned and returned
- [ ] All results merged
- [ ] Every input has a disposition
- [ ] Every skipped lens has a recorded reason
- [ ] `latent_defects.md` contains every LATENT disposition
