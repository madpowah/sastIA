# Class Group: Protocol & State Machine (PROTO) — Native

## Scope

Network daemons, protocol parsers, packet processing, stateful client
libraries, file-format parsers with internal state, and any code that parses a
sequence of messages with mutable state.

## Mandatory Inputs

For each parser entry point, enumerate:

- every wire field and its type/width;
- every option / TLV / extension / attribute;
- every length, count, offset, index, sequence number, ACK, window;
- the mutable state it reads and writes (`snd_una`, `snd_max`, `snd_holes`,
  `rcv_lastsack`, session ID, handshake state, parser cursor).

Add the **state precondition** and **relation** columns from Phase 1.

## Mandatory Checks

### 1. State machine table

| State | Event | Guard | Transition | Invariant preserved |
|---|---|---|---|---|

Enumerate every attacker-sendable event:

- duplicate, retransmission, out-of-order, partial;
- zero-length, max-length, empty list, first/last element;
- same packet with multiple options/blocks;
- two packets in sequence;
- reset/close/reopen;
- version negotiation / downgrade;
- error/timeout paths.

### 2. Guard composition

For each guard:

| Guard | Executes when | Skipped when | Sink it protects | Sink assumes it ran? |
|---|---|---|---|---|

A guard that executes only under a condition on **another field** is skipped
when that condition is false. That skipped path is a candidate.

This generalizes Conditional Validation Bypass from presence/absence to
degenerate values (equality, zero, empty, first/last, list-empty).

### 3. Sequence arithmetic / domain

For each comparison/macro (`SEQ_LT`, `SEQ_GT`, `before`, `after`, `wrap`):

- What is the assumed domain? (signed 32-bit subtraction, unsigned modular,
  monotonic 64-bit)
- Is the comparison a total order over the entire input domain?
- Enumerate boundary distances: `0`, `1`, `2^31-1`, `2^31`, `2^31+1`,
  `2^32-1`.
- A signed subtraction is a total order only within a 2^31 window.
- **Solve the inequalities**, not just list the boundaries. A composition may
  require a narrow window (e.g., `end < δ ≤ rcv_lastsack`).

| Expression | Domain | Boundary value | Result | Correct? |
|---|---|---|---|---|

### 4. Container invariants

For each list/ring/tree mutated by the parser:

- sorted / non-overlapping;
- covers exactly the unacknowledged ranges;
- `head`/`tail` consistency;
- cursor `p` points to the last node, or NULL if empty;
- after delete, no cursor points to freed memory;
- append path is skipped when the list is empty.

### 5. Spec conformance

For each RFC / protocol clause that applies:

| Clause | Obligation | Code location | Enforced? |
|---|---|---|---|

Examples: RFC 793 (TCP), RFC 2018 (SACK), RFC 8446 (TLS), RFC 7540 (HTTP/2),
file-format specs. A comment that says "per RFC X" is a hypothesis, not proof.

**Do not hallucinate a spec obligation.** Cite the clause or mark it
`unverified`.

### 6. Composition

Feed every skipped guard / domain violation / impossible conjunction to Phase
2c. The OpenBSD SACK bug is the canonical example: a skipped guard enables a
second defect that would otherwise be unreachable.

## Gate 2b (PROTO-specific)

- A length/range check in a different domain (bytes vs elements, signed vs
  unsigned) is not a defense.
- A check that runs only when another field has a particular relation is not a
  defense on the other paths.
- A `NULL` check after a delete is not a defense if the append path runs after
  the check or through a different alias.
- A parser that "works on normal traffic" is not safe against crafted values.

## Gate 3 (PROTO-specific)

- Remote unauthenticated panic/crash: **High** (not "reliability").
- Protocol state corruption leading to auth bypass: evaluate as identity
  inheritance.
- A crash that requires a rare but attacker-controllable sequence is still a
  finding; rarity affects severity, not existence.
