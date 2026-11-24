# Trace Agent Shared Instructions (Native)

These instructions apply to all lens agents (INJ, AUTH, MEM, PROTO, IDENT).
Read your class file after this file.

## Iteration rules

For each input in the inventory:

1. **Trace forward** from the input. Follow it through assignments, function
   calls, copies, state stores, queues, callbacks, and error paths until it:
   - (a) reaches a dangerous sink without effective validation → **candidate**;
   - (b) is proven constrained before every sink → **safe**;
   - (c) exits the codebase (returned, logged, discarded) → **safe**;
   - (d) reaches a store (global, cache, pool, session, file, shared memory) →
     grep for all readers and trace each independently. Do not record NO-MATCH
     at a store boundary.
2. **Trace state, not only data.** Record the state precondition for every
   effect (e.g., `th_ack == snd_una`, `snd_holes == NULL`, connection pooled,
   session authenticated, privilege dropped).
3. **Exhaust all paths.** If the input is used in 3 places, trace all 3. An
   input validated on one path may be unvalidated on another. A safe path does
   not clear the input.
4. **Follow error and cleanup paths.** Native bugs love `goto fail`, early
   returns, partial initialization, double cleanup, and reentrancy.
5. **Continue past the first finding.** The same input may reach independent
   sinks; each is a separate candidate. If fixing one would not fix the other,
   they are separate.
6. **Record the disposition**:
   - **CANDIDATE** (input #, sink file:line, lens, invariant violated);
   - **SAFE** (reason: validated / constrained / not reaching);
   - **LATENT** (individually harmless or unreachable; write to
     `latent_defects.md` with precondition and effect);
   - **DESIGN-INTENT** (only if the design precondition holds).

**Severity-context check**: classify under the highest-impact context the sink
accepts. If the sink's mode/format/scheme/type is attacker-selected, evaluate
the most dangerous value, not the expected one.

**Sanitizer/validator match check**: before recording SAFE, verify the defense
covers the sink's dangerous domain. Examples:
- length check on the wrong width/unit;
- `strlcpy` for a non-string binary copy;
- integer range check in signed arithmetic for an unsigned length;
- path normalization without symlink resolution;
- HTML/XML escaping for a shell command;
- TLS certificate check on one backend but not another.

If the defense is in a different domain or context → CANDIDATE, not SAFE.

## Mandatory state checks

### State gate (all lenses)

For every candidate, record:
- the state object (connection, session, pool, list, table, global);
- the invariant that must hold;
- the transition that can violate it;
- whether the attacker can drive that transition.

A candidate without a state precondition is fine (classic data-flow bug), but a
candidate that **changes** state must name the transition.

### Absent/degenerate value gate

For every guard, ask: what happens when the value is absent, zero, empty,
equal to a sibling field, first/last, or the list is empty? A guard that is
skipped on a degenerate path is a **Conditional Validation Bypass** candidate
(CWE-306/19/20 as applicable). This applies to protocol fields, not only HTTP
cookies.

### Composition gate

If a candidate is individually harmless or unreachable, do **not** discard it.
Write it to `latent_defects.md` with:
- precondition;
- effect;
- what would make it reachable.
Phase 2c composes latent defects.

## HARD GATES

Every candidate must pass these gates in order. Each gate is cheap. If a gate
eliminates the finding, record why and stop.

### Gate 0 — Design contract

Is this the code doing what it is designed to do?

A feature working as designed is not a vulnerability. But **Gate 0 does not
apply when the design assumes a security-relevant precondition and the attacker
can violate it**:

- the reused connection has the same authenticated identity / credential set;
- the cached object was created for the same tenant/host/TLS config;
- the parser state is in the expected state for this message;
- the container is non-empty when the append path runs;
- the privilege drop happened before parsing;
- the length is in the same domain as the allocation.

Test: state the invariant that makes the design safe; then check whether the
admission predicate/guard enforces every field of that invariant. If not, the
finding stands.

"Connection reuse is a feature" is not a defense if the reuse predicate accepts
a different identity. "Parsing SACK is a feature" is not a defense if the parser
accepts an out-of-window value.

### Gate 1 — Reachability

Use Grep for all call sites. Exhaust every one. A function called from one
dev-only path and one production path is production-reachable.

For native/protocol/kernel targets, reachability is also a **state sequence**:
a sink is reachable if there exists a sequence of attacker-controlled messages,
packets, syscalls, or API calls that reaches it. Record the sequence and the
state preconditions. Do not eliminate because no HTTP route calls the function.

Route registration/entry point registration is not reachability by itself.
Verify the sink code is reachable, not just registered.

### Gate 2a — Attacker control

Is the value or state controlled by the attacker?

- scalar data: packet field, file content, argv/env, IPC message, API argument;
- state: API option setter (`curl_easy_setopt`, `ioctl`, `setsockopt`), prior
  message, pooled object created by another principal, cache entry, global
  configuration exposed to users;
- for a library: the caller and its tenants;
- for a kernel: unprivileged user or remote peer;
- for a daemon: remote peer, IPC client, local user, admin.

Verify indirect control through stores: user input → store A → service reads A
→ store B → sink. Stop only at a provably trusted origin or when no
attacker-reachable path can write the store.

If the value is not attacker-controlled, eliminate. If it is, proceed. Do not
check validation here.

### Gate 2b — Validation and domain

Is there an effective guard between the source/state and the sink?

**Exhaust all callers** for validation too. A safe caller does not clear the
finding; only proving every caller validates clears it.

**Empirically verify the defense**:
- read its source and confirm it covers this sink's domain; or
- construct a test that proves it on the attack-relevant values; or
- if you cannot, treat it as ineffective and proceed to Gate 3.

**Validation composition**: for every guard, record:
- the condition under which it executes;
- the domain it assumes (width, signedness, unit, range);
- the sink invariant it enforces.

A guard that is skipped on a reachable path is ineffective. A guard that is a
total order only within a limited domain (e.g., signed subtraction within
2^31) is ineffective outside that domain. Evaluate guards as a composition, not
one at a time.

**Native-specific defenses to verify**:
- length checks in the same width/unit as the allocation;
- integer overflow checks before multiplication/addition;
- `strlcpy`/`snprintf` for strings, but not for binary data;
- path resolution (`realpath`, `openat`, `O_NOFOLLOW`) vs string prefix checks;
- privilege drop before parsing;
- reference counting and lifetime;
- sanitizer/allocator hardening (ASan, KASan, FORTIFY) — presence is not proof;
- TLS/certificate/host-key verification on every backend.

If effective, context-matched defense exists → eliminate. Else → Gate 3.

### Gate 3 — New capability

What concrete new outcome does the attacker get?

You must affirmatively demonstrate the outcome. "I could not find another path"
is not enough. If the PoC proves the mechanism but not the outcome, it is a
Code Smell.

**Do not eliminate because**:
- the attacker "can already" perform the operation with their own credentials —
  cross-principal identity inheritance, stale credential reuse, or reading
  another tenant's cached object is a new capability;
- "it only crashes" — a remotely triggerable crash/panic of a shared service or
  kernel is a security finding (CWE-400/617/476 as applicable);
- "it needs another bug" — record the latent defect and compose in Phase 2c;
- "the design intended it" — check the design precondition (Gate 0).

**Remote availability floor**:
- remote unauthenticated crash of a daemon/kernel: at least **High**;
- remote authenticated crash or single-tenant service: at least **Medium**;
- local unprivileged crash of a shared system service: **Medium**;
- local crash of the attacker's own process: **Low / Code Smell**.

A crash that requires a rare but attacker-controllable sequence is still a
finding; rarity affects severity, not existence.

### Gate 4 — Composition

If the candidate is individually harmless, unreachable, or "needs another
condition", write it to `latent_defects.md` and mark it **LATENT**. Do not
promote it to VULN. Phase 2c decides whether it composes.

## Severity (native)

**Critical**
- Remote unauthenticated RCE / kernel code execution
- Sandbox escape / hypervisor escape
- Authentication bypass to admin/root
- Cross-tenant key/credential compromise

**High**
- Remote unauthenticated memory corruption or panic (daemon/kernel)
- Local privilege escalation
- Cross-principal identity/credential inheritance
- Arbitrary file read/write with privilege
- PII/key material exposure across trust boundaries

**Medium**
- Remote authenticated memory corruption / DoS
- Local unprivileged DoS of a shared service
- Info leak requiring local access or auth
- Limited cross-boundary data exposure
- Missing auth on a management/debug interface (network-exposed)

**Low**
- Local DoS of the attacker's own process
- Limited info leak with no proven exploit
- Defense-in-depth gap with a verified mitigating control
- Header/format issue with no proven downstream impact

**Informational**
- Real gap bounded by a verified upstream control in the audited code
- Still gets VULN-NNN + data/state flow + PoC; classification only

**Adjustment factors**: unauthenticated → higher; single request/packet →
higher; race/chain required → lower; all instances affected → higher; self-only
→ lower.

Do not reduce severity based on assumed infrastructure defenses (firewall, WAF,
network segmentation, container isolation) unless they are in the audited code
and wired into startup.

## Candidate output format

```markdown
### [VULN-NNN] Title

- **Input**: inventory # and description
- **Lens**: INJ / AUTH / MEM / PROTO / IDENT
- **Class**: CWE-XXX: Name
- **Severity**: Critical / High / Medium / Low / Informational
- **Location**: file:line
- **State object**: object/field, or N/A
- **State precondition**: what must be true
- **Invariant violated**: identity / bounds / lifetime / order / auth / spec
- **Gate 0 (design contract)**: ...
- **Gate 1 (reachable)**: ... (call sites + state sequence)
- **Gate 2a (attacker control)**: ... (data or state; trust level)
- **Gate 2b (validation/domain)**: ... (guards, domains, composition)
- **Gate 3 (new capability)**: ...
- **Gate 4 (composition)**: confirmed / latent (if latent, stop)
- **Entry point**: ...
- **Data/state flow**: source -> ... -> sink (file:line at each step)
- **Root cause**: 1-2 sentences
- **Exploitability**: practical assessment
- **Confidence**: high / medium / low
```

## What to write to latent_defects.md

For every LATENT disposition:

| ID | Defect | Precondition that makes it harmless | Effect if precondition false | What makes it false |
|---|---|---|---|---|

Do not delete latent entries. Phase 2c needs them.
