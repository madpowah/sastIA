# Final Report Format (Native)

> Compile the final report from the artifacts in `${VULNHUNT_DIR}/`. Findings
> describe the source as it existed at scan time; the audit does not modify
> source files.
>
> **The output template is the same as the web pipeline.** Use the same README
> header, the same Summary table columns, and the same finding-detail structure.
> Native-only content (Lens, state, invariants, compositions, latent defects,
> coverage artifacts) is added inside that template, never by replacing it.

## Summary table

One row per exploit test PASS / confirmed composition.

| ID | Title | CWE | Severity | Exploit Test | Status |
|---|---|---|---|---|---|
| VULN-001 | ... | CWE-XXX | Critical/High/Medium/Low/Informational | PASS | Confirmed |

Do not change the `ID | Title | CWE | Severity` column order — the backend
parses it to compute severity counts. The `Lens` value goes in the finding
detail table, not in the Summary table.

Do not merge multiple sink locations under one VULN-NNN. Each confirmed
instance gets its own row.

## Finding detail

### [VULN-NNN] Title

| Field | Value |
|---|---|
| **Title** | ... |
| **Input** | inventory # and description |
| **Lens** | INJ/AUTH/MEM/PROTO/IDENT |
| **CWE** | CWE-XXX: Name |
| **Severity** | Critical/High/Medium/Low/Informational |
| **Location** | file:line |
| **State object** | object/field or N/A |
| **State precondition** | ... |
| **Invariant violated** | identity / bounds / lifetime / order / auth / spec |
| **Entry point** | ... |
| **Data/state flow** | source -> ... -> sink (file:line at each step) |
| **Composition** | if applicable: half A + half B -> effect |
| **PoC** | [poc/VULN-NNN_description.md](poc/VULN-NNN_description.md) — what it proves |
| **Exploit test** | [exploit_tests/test_vuln_NNN_description.py](exploit_tests/test_vuln_NNN_description.py) — PASS/FAIL + reason |
| **Evidence** | [evidence/VULN-NNN/report.txt](evidence/VULN-NNN/report.txt) (sanitizer, panic, pcap) |
| **Fix** | proposed strategy (not applied) |
| **Root cause** | shared root cause name, if part of a sweep group |
| **Confidence** | high / medium / low |
| **Status** | Confirmed / Potential / Fixed / Verified |

**Validation rule**: a finding is invalid if the PoC or exploit test field is
empty, "N/A", or "see above". Each must point to a saved artifact. If you cannot
produce a PoC/test, downgrade to `Potential` and include a validation plan.

## Confirmed compositions

For each Phase 2c composition:

| Composition | Halves | Trigger sequence | Domain/alias proof | Effect | VULN |
|---|---|---|---|---|---|

A composition gets its own VULN-NNN. Do not merge it with its halves.

## Latent defects

These are **not** vulnerabilities yet. They are individually harmless or
unreachable, but may compose.

| ID | Defect | Precondition that makes it harmless | Effect if false | What makes it false | Location |
|---|---|---|---|---|---|

Do not give latent defects VULN-NNN IDs or PoCs. They are an audit artifact.

## Code quality / defense in depth

Findings that failed an exploit test because a verified mitigation blocks them.
Include:
- location;
- pattern;
- which gate/test failed and the evidence (file:line);
- what would make it exploitable;
- recommendation.

## Coverage artifacts (completeness proof)

Include or link:

- `target_shaping.md` — target class, lenses, risk ranking;
- `phase1_output.md` — surface, threat model, partition table, input inventory;
- `state_identity_inventory.md` — objects, fields, pools, state machines;
- `invariant_register.md` — invariants and proof obligations;
- `negative_space.md` — expected vs present guards;
- `phase3d_output.md` — sweep table;
- the resolved input inventory with dispositions.

A "no findings" report with empty coverage artifacts is an incomplete audit,
not a clean audit.

## "Not found / excluded"

List checked-but-clean areas and excluded areas with reasons:
- lens marked not applicable (with Phase 0 reason);
- files/subsystems out of scope;
- dependencies excluded (unless critical-dependency mode);
- sanitizer/validation that was verified.

## README

Create `${VULNHUNT_DIR}/README.md` as the entry point, using the **same header
and sections as the web pipeline**:

```markdown
# VulnHunter Security Audit Report

**Run ID**: <VULNHUNT_DIR basename>
**Repository**: <repo URL>
**Audit Date**: <YYYY-MM-DD>
**Branch**: <branch [commit]>
**Model**: <model>
**Target class**: <library/daemon/kernel/...>   <!-- native only -->
**Mode**: static / dynamic                      <!-- native only -->
**Findings Summary**: <N Critical, N High, N Medium, N Low, N Informational>

## Summary
| ID | Title | CWE | Severity | Exploit Test | Status |
...

## Findings
For each: same detail table as the web template, plus `Lens`, `State object`,
`State precondition`, `Invariant violated`, `Composition`, `Evidence`,
`Confidence`. Link to PoC, exploit test, evidence.

## Resolved Input Inventory
...

## Not Found / Excluded
...

## Code Quality / Defense in Depth
...

## Confirmed compositions
...

## Latent defects
...

## Coverage artifacts
Links to target_shaping.md, state_identity_inventory.md,
invariant_register.md, negative_space.md, risk_ranking.md, phase3d_output.md.

## Sweep
...

## Artifacts
Table of all files in the results directory.
```

**Clickable links**: each finding row links to its PoC and exploit test.

**Cross-check**: the README summary table must list every VULN-NNN in the
report. Count and compare.

## Structured JSON (`report.json`)

In addition to `README.md`, write `${VULNHUNT_DIR}/report.json` with the **same
schema as the web pipeline** (`sastia_rapport.md`), including at minimum:

- `audit_id`, `project`, `source`, `date`, `summary`;
- `metrics` (`critical`, `high`, `medium`, `low`, `info`, total);
- `summary_table` (the exact markdown Summary table);
- `vulnerabilities[]` (one entry per VULN-NNN);
- `input_inventory[]`, `not_found[]`, `code_quality[]`, `docker_validation[]`.

Native optional additions: `target_type`, `target_class`, `lenses`,
`compositions`, `latent_defects`, `coverage_artifacts`.

If `report_markdown` is not included, the worker falls back to `README.md`.

## What NOT to report

- Test code, build scripts, vendored/generated code, unless the dependency is
  explicitly in scope.
- Style/best-practice issues without security impact.
- Theoretical issues with no demonstrated path — put them in latent/code
  quality with the missing proof.
- A crash of the attacker's own process with no shared impact (Low/Code Smell).
- A finding whose only "defense" is assumed infrastructure (firewall, WAF,
  container isolation) not in the audited code.
