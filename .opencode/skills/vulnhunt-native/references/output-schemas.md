# Output Schemas

Keep artifacts structured. Tables at the top of each file so the orchestrator
can read only what it needs.

## `target_shaping.md`

```markdown
## Target class
...
## Assets
...
## Lenses
| Lens | Applicable? | Reason if no |
## Build/run
...
## Initial risk ranking
| Rank | File/subsystem | Why |
## Initial partitions
| Partition (guess) | Files | Why |
```

## `state_identity_inventory.md`

```markdown
## Long-lived objects
| Object | Field | Type | Owner | Security role | Clone | Free | Compare | Key |
## Pools / caches / sessions
| Pool | Object | Reuse predicate | Key function | Identity | Compared | Omitted |
## State machines
| State | Event | Guard | Transition | Invariant |
```

## `invariant_register.md`

```markdown
| Invariant | Source | Must hold at | Can be violated at | Proof |
```

## `negative_space.md`

```markdown
| Operation | Expected guard | Present? | Location | Gap |
```

## `latent_defects.md`

```markdown
| ID | Defect | Precondition that makes it harmless | Effect if false | What makes it false | State object | Location |
```

## `results/sg-N_class_results.md`

```markdown
## Dispositions
| # | Input | Disposition | Sink | Invariant | Reason |
## Candidates
### [VULN-NNN] ...
## Latent
| ID | Defect | Precondition | Effect | Location |
## Cross-lens
| Input | Sink | Suspected lens |
```

## `phase2b_output.md`

```markdown
## Candidate manifest
Count: N
## Verdicts
| Finding | Gates | Reachable | Defense/domain | Severity | Call sites | Verdict |
## Confirmed findings
...
## False positives
...
```

## `phase2c_output.md`

```markdown
| Composition | Halves | Trigger sequence | Domain/alias proof | Gates | Verdict | VULN |
```

## `phase3_output.md`

```markdown
| Finding | PoC | Test | Result | Evidence | Status |
```

## `phase3d_output.md`

```markdown
| Root cause | Pattern | Total found | Candidates | Mitigated | Dev-only | Remaining |
```

## `phase4_report.md`

See `phases/phase4_report.md`.
