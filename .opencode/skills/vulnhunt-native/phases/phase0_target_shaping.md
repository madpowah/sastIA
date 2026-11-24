# Phase 0 — Target Shaping

> Run before recon. Goal: choose the right lenses, scope the audit, and avoid
> applying a web model to a kernel or a library.

## Step 0.1 — Target class

```text
[ ] native library / SDK
[ ] network daemon / protocol parser
[ ] kernel / hypervisor
[ ] CLI tool / file-format parser
[ ] firmware / embedded
[ ] IPC service / broker
[ ] desktop application
[ ] other: ______
```

## Step 0.2 — Security assets

Check every asset that exists in this target:

```text
[ ] memory safety / control flow
[ ] authenticated identity (certificate, token, session, SSH key)
[ ] connection / session / cache object
[ ] credentials / key material
[ ] privilege boundary (user/root, tenant, sandbox, capability)
[ ] availability of a shared service or kernel
[ ] tenant / user data
[ ] configuration / control plane
[ ] file system / IPC isolation
```

## Step 0.3 — Lenses

```text
[ ] INJ  — data-to-sink injection (command, path, format, env, deserialization)
[ ] AUTH — authentication, authorization, privilege, IPC peer credentials
[ ] MEM  — memory safety and lifetime
[ ] PROTO— protocol/state machine, sequence arithmetic, guard composition
[ ] IDENT— pools, sessions, reuse predicates, credential selection
[ ] COMPOSE — always on (Phase 2c)
```

For each lens marked not applicable, record a **concrete reason**:

| Lens | Applicable? | Reason if no |
|---|---|---|
| INJ | | |
| AUTH | | |
| MEM | | |
| PROTO | | |
| IDENT | | |

Do not write "probably empty". If the target has no network, IPC, auth, or
credential code, say so with file evidence.

## Step 0.4 — Build / run capability

```text
[ ] can build the target
[ ] can run the target
[ ] can run under ASan / UBSan / MSan
[ ] can run under KASan / kernel VM
[ ] can craft network packets
[ ] can run a local test harness
[ ] static only
```

`TARGET_MODE`:
- `dynamic` if at least one of build+run+sanitizer or packet crafting is
  available;
- `static` otherwise.

If `static`, Phase 3 must produce a validation plan and mark unproven findings
`Potential`, not `Confirmed`.

Write `TARGET_MODE: static` or `TARGET_MODE: dynamic` at the top of
`target_shaping.md`. The orchestrator reads it.

## Step 0.5 — Initial risk ranking

Rank source files/subsystems 1–5:

- **5** — parsers, protocol handlers, auth/handshake, option handling,
  connection/session pools, allocation, state machines, callbacks, privilege
  transitions.
- **4** — glue code that calls those, serialization, cleanup/error paths,
  IPC handlers, file-format code.
- **3** — complex business logic, configuration, device I/O.
- **2** — utilities, logging, build helpers.
- **1** — constants, types, documentation.

For a large target (kernel, browser, firmware), start at 5 and go down. Do not
rank a file 5 just because it is large; rank it by attacker-controlled input
and security state.

## Step 0.6 — Initial partition guess

Write a first guess of 3–10 partitions by subsystem/parser/state object. This
is refined in Phase 1. The goal is to avoid one giant partition and to make
sure every 5-ranked file lands in a partition.

| Partition (guess) | Files / subsystem | Why |
|---|---|---|

## Output

Write `${VULNHUNT_DIR}/target_shaping.md` with the sections above. Keep it
short (one screen). The orchestrator and Phase 1 read it.
