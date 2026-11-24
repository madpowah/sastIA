# Phase 1 — Reconnaissance (Native)

> Read `phase0_target_shaping.md` first. Your goal is to map the attack
> surface, the security state, and the invariants **before** looking for
> specific bugs.

## Step 1 — Structural overview

Use Glob/Grep/Read to identify:

- languages and build system;
- binaries/libraries/daemons in scope;
- architecture (32/64-bit, endianness, kernel/user, sandbox);
- public API surface (headers, exported symbols, RPC/IPC interfaces);
- network listeners, IPC endpoints, file formats, device interfaces;
- privilege transitions (`setuid`, `seteuid`, capabilities, sandbox, `chroot`,
  `pledge`/`unveil`, seccomp, namespaces);
- third-party dependencies and their security boundaries.

Output a short **Architecture** paragraph plus a **Surface** table:

| Surface | Entry point | Protocol/format | Trust boundary | Files |
|---|---|---|---|---|

## Step 2 — Native input inventory

Enumerate every point where attacker-influenced data or state enters the
codebase. This inventory is the completeness guarantee.

### 2.1 Input categories

| Category | Examples | Where to look |
|---|---|---|
| Network packet | TCP/UDP fields, IP options, SACK blocks, DNS messages, TLS records, HTTP/2 frames | `*_input.c`, `*_parse*`, `*_decode*`, protocol handlers |
| IPC | Unix sockets, netlink, D-Bus, pipes, shared memory, io_uring, RPC | `*_ipc*`, `*_server*`, `*_client*`, socket handlers |
| File | file content, filename, path, symlink, archive entry, config file | parsers, archive extractors, config readers |
| CLI / env | `argv`, `stdin`, environment variables, locale, `PATH` | `main`, option parsers, `getenv` |
| Device | `ioctl`, `mmap`, DMA, USB descriptors, firmware blob, sysfs/procfs | drivers, device handlers |
| Library API | public functions, callbacks, handles, option setters | headers, exported symbols |
| State | prior messages, session state, connection pool, cache, global state | state machines, pools, globals |
| Privileged action | `setuid`, file open, `exec`, mount, module load | privilege transitions |

Do not stop at the examples. Add any input vector specific to the target
(firmware update, hypercall, eBPF program, seccomp filter, etc.).

### 2.2 Input record

For each input, record:

| # | Source type | Location | Variable | Entry point | State precondition | Relation | Trust level |
|---|---|---|---|---|---|---|---|

- **State precondition**: what must be true for this input to have this effect
  (e.g., `th_ack == snd_una`, `snd_holes != NULL`, session authenticated,
  connection pooled).
- **Relation**: the other field/constant it is compared to (e.g.,
  `sack.start` vs `snd_una`; `key` vs `clientcert`; `len` vs `sizeof(dst)`).
- **Trust level**: `remote-unauth`, `remote-auth`, `local-unauth`, `local-user`,
  `ipc-client`, `admin`, `root`, `physical`.

**Sibling rule**: when a parser extracts N fields, enumerate all N. Do not
pre-filter "dangerous-looking" fields. Phase 2 decides safety.

**Structural input rule**: for every length/count/offset/index field, also
inventory the buffer it bounds and the allocation it sizes. A length without
its buffer is not traceable.

### 2.3 Input completeness check

For every entry point in the Surface table, confirm at least one input. For
every parser, confirm every wire field is either inventoried or explicitly
constant/unused. Record gaps.

## Step 3 — State and identity inventory

For every object that outlives a request/message/packet:

### 3.1 Long-lived objects

| Object | Field | Type | Owner (request/connection/global) | Security role | Clone | Free | Compare/Match | Key/Hash |
|---|---|---|---|---|---|---|---|---|

Security roles: `identity`, `authorization`, `lifetime`, `bounds`, `crypto`,
`routing`, `state`, `none`.

### 3.2 Pools, caches, sessions

| Pool/cache | Object | Reuse predicate | Key function | Identity carried | Fields compared | Fields omitted |
|---|---|---|---|---|---|---|

Examples: connection pool, TLS session cache, credential cache, DNS cache,
HSTS/alt-svc, SSH multiplexing, object pool, file descriptor cache.

### 3.3 Field-coverage rules (mandatory)

1. **Field coverage**: a field with a security role that is present in the
   object but absent from `compare/match/key` is a **candidate**.
2. **Marker vs value**: a key component that records presence (`has_cert`)
   instead of value (cert path/hash) is a **collision candidate**.
3. **Ownership**: a per-request security field stored in a per-connection
   object is an **inheritance candidate**.
4. **Clone/free completeness**: a field cloned but not freed (or freed but not
   cloned) is a **lifetime candidate**.

### 3.4 Security-role decision procedure

Do not label a field "security" or "none" by intuition alone. Use these
definitions and record the evidence:

| Role | Test | Examples |
|---|---|---|
| `identity` | Does the field select or verify **who** the peer/principal is? | client cert, key, token, user, host key, session ID |
| `authorization` | Does the field select a **permission, role, tenant, or policy**? | role, scope, ACL, tenant ID |
| `lifetime` | Does the field own, free, or refcount a resource? | refcount, owner, destructor, list link |
| `bounds` | Does the field size/index/copy memory or limit a loop? | length, count, offset, index, size |
| `crypto` | Is it key material, a nonce/IV, an algorithm, or a verification flag? | key, IV, nonce, `verifypeer` |
| `routing` | Does it select the network destination or peer? | host, port, scheme, proxy, SNI |
| `state` | Does it select a protocol/connection/session state? | handshake state, hole list, cursor |
| `none` | Cosmetic, cache hint, debug, unused. | comment, label, padding |

**Second-opinion rule**: a field classified `identity` or `authorization` must
be confirmed by a second agent (or by an API doc/comment that states the
security role). If two agents disagree, treat it as security-relevant and let
Phase 2b eliminate it with evidence.

**Ambiguity rule**: when a field is plausibly security-relevant, classify it as
security-relevant. The cost of a false candidate is a Phase 2b verification;
the cost of a false negative is a missed auth bypass.

### 3.4 State machines

For each parser/state machine:

| State | Event | Guard | Transition | Invariant preserved |
|---|---|---|---|---|

Include duplicate, retransmission, out-of-order, partial, empty, first/last,
and error transitions.

## Step 4 — Invariant register

Extract invariants from every source:

- comments (`/* last hole is p and it's not NULL */`);
- `assert`, `KASSERT`, `BUG_ON`, `WARN_ON`, `panic` conditions;
- API documentation / man pages / headers;
- RFC / protocol spec;
- function names (`match_`, `validate_`, `check_`, `is_`);
- tests (what do they assert?).

| Invariant | Source | Where it must hold | Where it can be violated | Proof |
|---|---|---|---|---|

**Comments are hypotheses, not defenses.** A comment that asserts an invariant
is a proof obligation. A comment that says "validated by the caller" is a
candidate, not a clearance.

## Step 5 — Negative space

For every sensitive operation, list the guard you expect and whether it is
present:

| Operation | Expected guard | Present? | Location | Gap |
|---|---|---|---|---|
| copy into buffer | `len <= sizeof(dst)` in the same domain | | | |
| index into table | `index < count`, same width | | | |
| use after delete | cursor not NULL / not freed | | | |
| append to list | list non-empty / tail non-NULL | | | |
| reuse connection | all identity fields equal | | | |
| parse sequence range | start and end within window | | | |
| privilege drop | drop before processing input | | | |
| IPC peer auth | peer credentials verified | | | |
| file open | path resolved, no symlink escape | | | |
| free | all aliases invalidated | | | |

Each "Present? = no" is a candidate, not a code smell.

## Step 6 — Threat model (native)

For each entry-point group, record one row:

| Entry-point group | Reachability | Credential / boundary | Attacker profile | Attacker controls | Attacker does NOT control | Existing capabilities |
|---|---|---|---|---|---|---|

- **Reachability**: network, IPC, local, physical; auth required?
- **Credential / boundary**: certificate, token, UID, capability, sandbox,
  file permission.
- **Attacker profile**: remote unauth, remote auth, local user, IPC client,
  admin, root, physical.
- **Existing capabilities**: what this attacker can already do by design. Do
  not derive baseline capabilities from missing auth (circular).

For a library, the "entry point" is the public API function; the attacker is
the caller (or a tenant of the caller). For a kernel, the entry point is a
syscall/packet/ioctl; the attacker is the unprivileged user/remote peer.

## Step 7 — Partitions

Build partitions by subsystem, parser, protocol, or state object — **not** by
HTTP route.

1. Group inputs whose data/state flows through shared application-specific
   code.
2. Factor out shared infrastructure (allocator, logging, generic containers,
   crypto primitives).
3. Split oversized partitions (>20 inputs or >15 files) by file/subsystem.
4. Merge undersized partitions (≤2 inputs and 1 file) with the closest
   related partition.
5. Ensure every 5-ranked file is in a partition.

Output:

| Partition | Inputs | Entry points | State objects | Files | Shared infra | Risk |
|---|---|---|---|---|---|---|

**Coverage check**: every subsystem/parser/protocol in the Surface table must
appear in at least one partition. Any gap is a blind spot — go back.

## Step 8 — Risk ranking

Write `risk_ranking.md`:

| Rank | File/subsystem | Why | Partition |
|---|---|---|---|

5 = parsers/auth/state/pools/allocation/callbacks; 1 = constants/types/docs.

## Output

Write in `${VULNHUNT_DIR}/`:

- `phase1_output.md` — architecture, surface, threat model, partition table,
  coverage check, input inventory summary;
- `state_identity_inventory.md` — objects, fields, pools, state machines;
- `invariant_register.md` — invariants and proof obligations;
- `negative_space.md` — expected vs present guards;
- `risk_ranking.md` — file/subsystem ranking.

The orchestrator reads only the partition table, input inventory, state/pool
inventory, and risk ranking. Put the tables at the top of each file.
