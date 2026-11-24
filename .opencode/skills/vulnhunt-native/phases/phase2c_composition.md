# Phase 2c — Composition and Latent-Defect Analysis

> Some bugs are not one defect but the **composition of two defects**, each
> individually benign or unreachable. The OpenBSD SACK bug is the canonical
> example: a skipped guard + a NULL cursor after deleting the only hole.
>
> This phase is deliberately **bounded**. Unbounded pair search is a
> false-positive factory.

## Inputs

- `phase2b_output.md` (confirmed + eliminated candidates)
- `latent_defects.md` (all near-misses, Code Smells, DESIGN-INTENT, Gate 1
  "unreachable" entries)
- `invariant_register.md`
- `state_identity_inventory.md`
- `negative_space.md`

## Step 1 — Build the ledger

For each latent defect, record:

| ID | Defect | Precondition that makes it harmless | Effect if precondition false | What makes it false | State object | File/function |
|---|---|---|---|---|---|---|

Do not delete entries. A half-bug is a potential graph edge.

## Step 2 — Build the composition graph (bounded)

Create an edge `A -> B` only if:

1. A and B are in the **same state object**, **same function**, or **same
   file/subsystem**; and
2. A's effect satisfies one of B's preconditions; and
3. the combined trigger sequence is expressible (messages, API calls, state
   transitions).

Do not connect defects across unrelated subsystems just because the words
match. If you cannot write the trigger sequence, do not create the edge.

**Cap**: at most 20 candidate pairs per partition. If more, keep the pairs
with the strongest state/data connection and record the rest as "not
evaluated".

## Step 3 — Mandatory composition patterns

### 3.1 Impossible conjunction

Two predicates on the same value that cannot both be true under normal
arithmetic, but can under:
- signed overflow/underflow;
- wrap-around (2^32, 2^64);
- truncation (64 → 32 → 16 bits);
- aliasing (two names for the same memory);
- domain change (bytes vs elements, ms vs ticks).

Build the table:

| Value | Domain | Predicate 1 | Predicate 2 | Both true? (normal) | Both true? (edge) |
|---|---|---|---|---|---|

**Solve the inequalities.** A narrow window may be required. Do not stop at
"2^31 is a boundary".

### 3.2 Validation-skip-then-sink

A guard runs only under a condition on **another** field. When the condition is
false, the guard is skipped, and a later sink assumes it ran.

| Guard | Execution condition | Skipped when | Sink that assumes it ran |
|---|---|---|---|

### 3.3 Free-then-use cursor

A delete path frees a node and sets a cursor to NULL; an append/insert path
uses that cursor.

| Delete path | Cursor after delete | Append path | Guard on cursor? |
|---|---|---|---|

### 3.4 Identity-reuse

A pooled/cached object is reused while a field of its security identity changed.

- Which object?
- Which identity field changed?
- Why is it not in the predicate/key?
- Can the attacker drive the change?

### 3.5 Sentinel collision

A valid value equals the sentinel for "empty"/"invalid" (`-1`, `0xFFFF`,
`NULL`, `SIZE_MAX`). Check every comparison to the sentinel.

### 3.6 Length-domain mismatch

A length and an index/table size are in different widths or units. Check every
conversion and every multiplication.

### 3.7 Reentrancy

A callback invoked during the operation can re-enter and mutate state in use.
Check free paths, list surgery, and refcounts under the reentrant call.

### 3.8 State-machine transition

Two individually valid transitions compose into an invalid state (e.g.,
authenticated → reconfigured → reused; parsed → freed → appended).

## Step 4 — Proof obligation

For every pair, before calling it a candidate:

1. Write the **full trigger sequence** (initial state → message/API 1 →
   message/API 2 → effect).
2. Prove each step is attacker-reachable.
3. Prove the **domain/alias** condition (arithmetic window, wrap, truncation,
   reentrancy, etc.).
4. Check for any guard that blocks the sequence. If a guard blocks it, the
   composition is not confirmed; record why.
5. Apply the gates to the **composition**, not the halves:
   - Gate 0: does the design assume a state the composition violates?
   - Gate 1: is the sequence reachable?
   - Gate 2a: is each step attacker-controlled?
   - Gate 2b: is any guard ineffective on the composed path?
   - Gate 3: what new effect (crash, corruption, identity, privilege)?

If you cannot write the sequence or the domain proof, keep the pair in the
**latent** section, not in the confirmed table.

## Step 5 — Output

Write `${VULNHUNT_DIR}/phase2c_output.md`:

| Composition | Halves | Trigger sequence | Domain/alias proof | Gates | Verdict | VULN |
|---|---|---|---|---|---|---|

- **Confirmed compositions** get new `VULN-NNN` IDs starting after the highest
  ID assigned in Phase 2b, and proceed to Phase 3.
- **Unconfirmed compositions** stay in `latent_defects.md` with the missing
  proof.
- Do not merge a composition with its halves. The halves keep their own
  dispositions; the composition is a separate finding.

## Golden rule

> A defect that is "harmless alone" is not a harmless defect. It is a puzzle
> piece — but only assemble it if the trigger sequence and the domain proof
> hold.
