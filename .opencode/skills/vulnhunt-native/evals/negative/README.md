# Negative Control

The native skill should not produce a confirmed finding on the **fixed**
snapshots:

- `curl_cve_2026_8932` fixed (`7541ae5`);
- `openbsd_sack` fixed (`tcp_input.c` r1.465).

Run:

```bash
python3 scripts/score_eval.py \
  /path/to/vulnhunt_native_results/phase2b_output.md \
  evals/curl_cve_2026_8932/expected.json \
  --mode fixed
```

A pass means the report does **not** contain a confirmed finding for the known
bug. A failure means the methodology is overfitting to the pattern and flags
the fixed code too.

## Web control

Run `/vulnhunt-native` on a small web application. The skill should report
"out of scope" (target class = web app) rather than produce native findings.
This checks that the new skill does not replace the web skill by accident.
