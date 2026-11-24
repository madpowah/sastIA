---
name: vulnhunt-native
description: >
  Security audit for non-web targets: native libraries, daemons, kernels,
  protocol parsers, CLI tools, firmware, and IPC services. Uses state and
  identity inventories, invariant registers, memory/lifetime analysis,
  protocol state machines, cache/reuse predicates, and bounded composition.
  Static-first, with an optional dynamic validation mode.
---

# VulnHunter Native — Security Audit Skill for Non-Web Targets

## MANDATORY FIRST ACTIONS

Bind work variables:

- `CODE_DIR` = source root to audit
- `VULNHUNT_DIR` = `${CODE_DIR}/vulnhunt_native_results`
- `SKILL_DIR` = directory containing this `SKILL.md` (the skill loader reports it;
  if not, locate it with `Glob "**/vulnhunt-native/SKILL.md"`)
- `PHASES_DIR` = `${SKILL_DIR}/phases`
- `REFERENCES_DIR` = `${SKILL_DIR}/references`
- `Repository URL` = repo URL or directory name
- `TARGET_MODE` = `static` (default) or `dynamic` (if the kickoff says
  "dynamic validation is available")

Create `${VULNHUNT_DIR}` and `${VULNHUNT_DIR}/partitions`, `${VULNHUNT_DIR}/results`,
`${VULNHUNT_DIR}/poc`, `${VULNHUNT_DIR}/exploit_tests`, `${VULNHUNT_DIR}/evidence`.

Where this skill says "general-purpose subagent", use the host's general
subagent type (in OpenCode: `general`).

**This skill is not a web SAST.** Do not apply HTTP route/controller/ORM
assumptions to a kernel, a daemon, a library, or a parser. If the target is a
web application, use `/vulnhunt` instead.

## Operating Principles

1. **State is an input.** A packet field, an API option, a prior message, a
   pooled connection, and a cached credential are all inputs. Trace state, not
   only scalar data.
2. **Absence is a finding.** A missing guard, a missing field in a match/key
   predicate, and a missing NULL check are candidates. Enumerate what should be
   there, not only what is.
3. **Invariant-first.** For every candidate, state the security invariant that
   is violated (identity, state, domain, lifetime, order). "Tainted data reaches
   a sink" is not the only proof.
4. **Never discard a half-bug.** A defect that is individually harmless or
   unreachable goes to `latent_defects.md`. Phase 2c composes halves.
5. **Do not credit design intent when its precondition can be violated.**
   "Connection reuse is a feature" is not a defense if the reuse predicate
   accepts a different identity. "Parsing is a feature" is not a defense if the
   parser accepts an out-of-window value.
6. **A remote crash is security.** A remotely triggerable panic of a shared
   service or kernel is a security finding, not a reliability bug. Severity
   depends on reachability and impact, not on the absence of memory corruption.
7. **Prove the outcome.** A PoC must show the attacker's goal (crash, UAF,
   auth bypass, privilege, info leak), not just that a code path runs.
8. **Production code only**, except: for a critical dependency explicitly in
   scope, audit the dependency's security boundary (the API surface used by the
   caller), not its entire codebase. Record the boundary.

## Analysis Lenses

The skill uses five vulnerability classes plus composition:

| Lens | Focus |
|---|---|
| **INJ** | command/path/format/env/deserialization/SQL injection, file and archive parsing, unsafe data-to-sink flows |
| **AUTH** | authentication, authorization, privilege boundaries, setuid/capabilities, IPC peer credentials, sandbox, file permissions, confused deputy |
| **MEM** | memory safety and lifetime: bounds, integer/domain mismatch, UAF, double free, container cursors, reentrancy, type confusion |
| **PROTO** | wire parsing, state machines, sequence arithmetic, guard composition, packet ordering, spec conformance |
| **IDENT** | connection/session pools, reuse predicates, key completeness, credential selection, cross-handle isolation, host keys |
| **COMPOSE** | Phase 2c: composition of latent defects, impossible conjunctions, free-then-use cursors, identity reuse |

Phase 0 selects which lenses apply. Do **not** skip a lens because it is
"probably empty" — skip only with a concrete, recorded reason.

## Workflow

### Step 0 — Target shaping (orchestrator)

Read `${PHASES_DIR}/phase0_target_shaping.md`. Produce
`${VULNHUNT_DIR}/target_shaping.md`: target class, security assets, lenses,
build/run capability, initial risk ranking. This is short; do it yourself.

### Step 1 — Recon (subagent)

Spawn a general-purpose subagent:

> Your scan directory is `${VULNHUNT_DIR}`. Your skill directory is `${SKILL_DIR}`.
> Follow `${PHASES_DIR}/phase1_recon.md`. Write
> `${VULNHUNT_DIR}/phase1_output.md`, `state_identity_inventory.md`,
> `invariant_register.md`, `negative_space.md`, and `risk_ranking.md`.
> IMPORTANT: return ≤20 words.

Verify the files exist. **Do not read them in full.** Read only:
- the partition table,
- the input inventory table,
- the state/pool inventory table,
- the risk ranking.

### Step 2 — Hunt (dispatch)

Read `${PHASES_DIR}/phase2_hunt.md`. Create
`${VULNHUNT_DIR}/partitions/sg-{N}_data.md` for each production partition.
Dispatch one agent per lens per partition, plus one sink-driven agent.

**Minimum agent count = (5 × production_partition_count) + 1.**

If a lens was explicitly marked not applicable in `target_shaping.md` with a
concrete reason, record the skip and subtract it. A skipped lens without a
recorded reason is a coverage failure.

Dispatch in waves of at most 6 agents. Wait for each wave's results files
before the next wave. The sink-driven agent is the final wave.

### Step 3 — Verify (subagent)

Spawn a general-purpose subagent:

> Your scan directory is `${VULNHUNT_DIR}`. Follow
> `${PHASES_DIR}/phase2b_verify.md`. Read all `results/*.md`, the state
> inventory, the invariant register, and the negative space. Write
> `${VULNHUNT_DIR}/phase2b_output.md` and append every near-miss to
> `${VULNHUNT_DIR}/latent_defects.md`. Return ≤20 words.

Verify the files exist.

### Step 4 — Compose (subagent)

Spawn a general-purpose subagent:

> Your scan directory is `${VULNHUNT_DIR}`. Follow
> `${PHASES_DIR}/phase2c_composition.md`. Read `phase2b_output.md`,
> `latent_defects.md`, `state_identity_inventory.md`, `invariant_register.md`,
> and `negative_space.md`. Write `${VULNHUNT_DIR}/phase2c_output.md`.
> Return ≤20 words.

Verify the file exists. Composition candidates are **not** confirmed yet; Phase
2c applies the gates to the composition and records the verdict.

### Step 5 — Reproduce, test, and optionally validate (subagent)

Spawn a general-purpose subagent:

> Your scan directory is `${VULNHUNT_DIR}`. Follow
> `${PHASES_DIR}/phase3_reproduce_test.md`. Read confirmed findings from
> `phase2b_output.md` and confirmed compositions from `phase2c_output.md`.
> Write PoCs to `poc/` and exploit tests to `exploit_tests/`. Write
> `${VULNHUNT_DIR}/phase3_output.md`. If `TARGET_MODE=dynamic`, also follow
> the dynamic-validation section. Return ≤20 words.

Verify `phase3_output.md`, `poc/`, and `exploit_tests/` exist.

### Step 6 — Sweep (subagent)

Spawn a general-purpose subagent:

> Your scan directory is `${VULNHUNT_DIR}`. Follow
> `${PHASES_DIR}/phase3d_sweep.md`. Write
> `${VULNHUNT_DIR}/phase3d_output.md`. Return ≤20 words.

### Step 7 — Report (orchestrator)

Read `${PHASES_DIR}/phase4_report.md` and compile the final report from the
artifacts in `${VULNHUNT_DIR}/`.

Before writing the summary table, check:
- every confirmed exploit test PASS has one `VULN-NNN` row;
- every confirmed composition has its own row;
- latent defects are in a separate section, not in the VULN table;
- the coverage artifacts are present (input inventory, state inventory,
  invariant register, negative space, partition table, sweep table).

### What the report contains

- Coverage artifacts (completeness proof).
- Confirmed vulnerabilities (one `VULN-NNN` per sink/root-cause instance that
  passed an exploit test).
- Confirmed compositions.
- Latent defects (not vulnerabilities yet).
- Proposed fix strategies.
- Sweep verification table.
- "Not found / excluded" section with reasons.

## Stopping Rules

**Zero confirmed findings is valid**, but only after the coverage artifacts are
complete. A "no findings" report with an empty state inventory or an empty
invariant register is not a clean audit; it is an incomplete audit.

Do not soften criteria to produce findings. However, do not eliminate a
candidate merely because:
- it is a remote crash (see Principle 6);
- it needs another defect to be reachable (record it as latent and compose);
- the design "intended" the feature (check the precondition);
- no scalar input appears in the immediate function (state is an input).

## Context Management

Your role is orchestrator. You dispatch subagents and verify output files. You
do not perform analysis yourself. Keep your context lean:
- do not read source code;
- do not read full result files;
- verify completion by checking files exist;
- if a subagent fails, re-launch it; do not diagnose it yourself.

## Phase Files

- `phase0_target_shaping.md` — target class, assets, lenses, risk ranking
- `phase1_recon.md` — native input inventory, state/identity, invariants, partitions
- `phase2_hunt.md` — dispatch procedure
- `phase2_shared.md` — trace rules, gates, severity, output format
- `phase2_class_{inj,auth,mem,proto,ident}.md` — class references
- `phase2b_verify.md` — adversarial verification + recall mode
- `phase2c_composition.md` — latent defects + bounded composition
- `phase3_reproduce_test.md` — PoC, exploit test, dynamic validation
- `phase3d_sweep.md` — field/predicate/domain/lifetime/spec sweeps
- `phase4_report.md` — final report format

If any phase file is missing, STOP and report the missing path. Do not
improvise the methodology.
