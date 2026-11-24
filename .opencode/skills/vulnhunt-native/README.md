# VulnHunter Native

Security audit skill for **non-web targets**:

- native libraries / SDKs
- network daemons / protocol parsers
- kernels / hypervisors
- CLI tools / file-format parsers
- firmware / embedded
- IPC services / brokers

It keeps what works in `/vulnhunt` (input inventory, parallel lens agents,
gates, PoC, exploit test, sweep, report) and adds what native bugs need:

- **state and identity inventory** (objects, fields, pools, state machines);
- **invariant register** (comments, asserts, docs, RFCs);
- **negative space** (expected guards vs present guards);
- **MEM / PROTO / IDENT lenses** (plus INJ / AUTH);
- **bounded composition** of latent defects (the OpenBSD SACK class);
- **native severity** (remote panic, privilege, identity inheritance);
- **optional dynamic validation** (ASan/UBSan/KASan, packet crafting, VM);
- **evals** for curl CVE-2026-8932 and OpenBSD SACK, with a precision control.

## Install

```bash
./install.sh            # symlink into ~/.config/opencode/skills/
./install.sh --copy     # copy instead of symlink
```

Then invoke:

```text
/vulnhunt-native
```

or ask: "audit this C daemon with vulnhunt-native".

## Usage

The skill expects a source tree. It creates
`<source>/vulnhunt_native_results/` with:

```text
target_shaping.md
phase1_output.md
state_identity_inventory.md
invariant_register.md
negative_space.md
risk_ranking.md
partitions/sg-N_data.md
results/sg-N_lens_results.md
phase2b_output.md
latent_defects.md
phase2c_output.md
phase3_output.md
poc/
exploit_tests/
evidence/
phase3d_output.md
README.md
```

## Compare with `/vulnhunt`

Run both on the same source, then compare:

- time to first candidate;
- recall on the eval fixtures;
- false positives on the fixed snapshots;
- number of confirmed findings;
- quality of the mechanism (does the candidate cite the missing field/guard?).

The native skill is **not** a replacement for the web skill. If the target is a
web app, use `/vulnhunt`.

## Evals

```bash
./scripts/fetch_fixtures.sh
./scripts/smoke_test.sh          # detectors on vulnerable + fixed snapshots
python3 scripts/field_coverage.py evals/fixtures/curl_vuln
python3 scripts/guard_coverage.py evals/fixtures/tcp_input_1.464.c
python3 scripts/score_eval.py REPORT evals/curl_cve_2026_8932/expected.json
```

See `evals/README.md`.

## Design notes

- The methodology is **static-first**. Dynamic validation is optional and
  produces evidence, not a replacement for source reasoning.
- Composition is **bounded**: same state object/function/file, concrete trigger
  sequence, domain/alias proof. Unbounded pair search is a false-positive
  factory.
- Latent defects are **not** vulnerabilities. They live in a separate artifact
  until Phase 2c proves the composition.
- A remote crash of a shared service/kernel is a security finding, not a
  reliability bug.
