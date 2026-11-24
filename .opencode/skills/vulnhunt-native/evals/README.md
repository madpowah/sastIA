# Evals — VulnHunter Native

The goal is to measure whether a methodology change improves **recall on known
bugs** without degrading **precision on fixed code**. Without this, a change is
an opinion.

## Fixtures

| Fixture | Vulnerable | Fixed | What it tests |
|---|---|---|---|
| `curl_cve_2026_8932` | parent of `7541ae5` | `7541ae5` | field-coverage / identity predicate |
| `openbsd_sack` | `tcp_input.c` r1.464 | r1.465 | guard composition / domain |

Fetch and smoke-test:

```bash
./scripts/fetch_fixtures.sh
./scripts/smoke_test.sh
```

The fixtures are source snapshots only. **Do not include git history or the fix
commit** in the vulnerable snapshot: the agent must not be able to read the
answer.

## Run

1. Copy the vulnerable snapshot to a working directory.
2. Run `/vulnhunt-native` (and, for comparison, `/vulnhunt`) with the same
   target.
3. Score the report:

```bash
python3 scripts/score_eval.py \
  /path/to/vulnhunt_native_results/phase2b_output.md \
  evals/curl_cve_2026_8932/expected.json \
  --mode vulnerable
```

4. Run on the fixed snapshot and score with `--mode fixed`. The expected result
   is **no confirmed finding** for the known bug (precision control).

## Metrics

| Metric | Definition | Target |
|---|---|---|
| Recall@1 | the known bug is the top candidate | 2/2 |
| Localization | candidate cites the right file + function | 100 % |
| Mechanism | candidate cites the missing field/guard/domain | ≥ 2/3 elements |
| Precision (fixed) | no confirmed finding on the fixed snapshot | 100 % |
| Cost | tokens/time per fixture | tracked, no initial target |

## Baseline and ablation

Before changing the skill, run the **current** methodology on the vulnerable
snapshot. Record the four failure modes:

1. file never read;
2. read but not seen;
3. seen but a gate eliminated;
4. seen but lost at aggregation.

Then apply **one** change at a time and measure. A change that improves recall
but destroys precision is not a win.

## Negative control

Run on the fixed snapshots and on a small web app. The native skill should
**not** apply to the web app (it should be out of scope), and the web skill
should not regress on its own eval set.

## Leakage

- No fix commit in the fixture.
- No `git log`/`git blame` pointing to the fix.
- No test case that asserts the fixed behavior.
- The expected JSON is not visible to the agent under test.

## What counts

A candidate must cite:
- the exact file and function;
- the missing field / guard / state transition;
- the trigger sequence (for composition).

A generic "memory issue in tcp_input.c" does **not** count.
