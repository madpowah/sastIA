# Class Group: Authorization & Privilege (AUTH) — Native

## Scope

This class covers authentication, authorization, privilege boundaries, IPC
peer identity, sandboxing, file permissions, and confused deputy in native
services, daemons, kernels, and libraries.

## Dangerous Sink Reference

- **Privilege transitions**: `setuid`, `seteuid`, `setresuid`, `setgid`,
  `setgroups`, `capset`, `prctl(PR_SET_KEEPCAPS)`, `chroot`, `pledge`,
  `unveil`, `seccomp`, namespaces, `unshare`, `clone`.
- **Identity checks**: `getuid`, `geteuid`, `getpeereid`, `SO_PEERCRED`,
  `SCM_CREDENTIALS`, `accept4`, D-Bus policy, netlink credentials, socket
  ownership, file owner checks.
- **File permissions**: `open`, `openat`, `fopen`, `creat`, `mkdir`, `chmod`,
  `chown`, `umask`, `O_NOFOLLOW`, `O_EXCL`, temporary files.
- **Authentication**: password/token/certificate/host-key verification,
  session lookup, replay protection, nonce/expiry, constant-time compare.
- **Sandbox / isolation**: seccomp filters, pledge/unveil, capabilities,
  chroot, mount namespaces, user namespaces, `no_new_privs`.
- **Management / debug interfaces**: admin sockets, debug ports, ioctl,
  `/proc`/`sysfs` knobs, firmware update, recovery mode.

## Mandatory Gates

### Privilege-drop gate

For any privileged program that parses attacker input:

1. Where is the privilege drop (`setuid`/`setgid`/capabilities/seccomp)?
2. Does it happen **before** parsing/processing the input?
3. Can it be undone (`seteuid(0)`, retained capabilities, `PR_SET_KEEPCAPS`)?
4. Are supplementary groups, `LD_*`, `PATH`, `TMPDIR`, `HOME`, and file
   descriptors sanitized before the drop?

A drop after parsing, or a retained capability, is a candidate.

### IPC peer gate

For every IPC endpoint:

1. What credential does the peer present? (UID/GID, pid, SCM_CREDENTIALS,
   D-Bus name, socket file permission)
2. Is it verified **before** the privileged operation?
3. Can the peer spoof it (abstract socket, filesystem permissions, pid reuse)?
4. Is the authorization per-operation or only per-connection?

### File-permission gate

For every file operation with attacker-influenced path:

1. Is the path canonicalized and resolved with `openat`/`O_NOFOLLOW`?
2. Is the file opened with the least privilege?
3. Is there a TOCTOU between check and use?
4. Are temp files created with `O_EXCL`, `mkstemp`, and correct permissions?
5. Can a symlink or hardlink redirect the operation?

### Auth-branch gate

For endpoints with multiple auth methods:

1. Enumerate every branch.
2. What credential is required?
3. Is it cryptographically verified?
4. What identity does it produce?
5. What authorization scope does that identity get downstream?

A weaker branch is a distinct finding even if gated by a caller allowlist.

## Vulnerability Classes

- Missing or ineffective auth on a management/debug/admin endpoint.
- Privilege drop after parsing, or incomplete drop (capabilities, groups, fds).
- IPC peer identity spoofing / missing peer credential check.
- File permission / symlink / TOCTOU / predictable temp file.
- Capability retention / ambient authority / sandbox escape.
- Authentication bypass, weak token/session validation, replay.
- Certificate/host-key verification missing on one backend.
- Confused deputy: privileged service acts on behalf of an unverified caller.
- Identity spoofing: user-supplied UID/pid/name used for authorization.
- Authorization-scope selection: user chooses a policy/config that changes
  permissions (e.g., `skipValidation`, `allowAll`).
- Setuid environment injection (`PATH`, `LD_PRELOAD`, `IFS`, locale).

## Gate 2b (AUTH-specific)

- A declared decorator/policy/annotation is not proof of enforcement; read the
  enforcing code.
- A header/peer-credential presence check is not verification; require a
  cryptographic or kernel-verified binding.
- A check on one backend/branch does not cover the others.
- A check that runs only when a companion input is present is bypassable.
- A privilege drop that can be undone is not a drop.
- A path prefix check is not a canonicalization.

## Gate 3 (AUTH-specific)

Do not eliminate because:
- "the endpoint is internal" — cite the binding/auth code;
- "the caller is trusted" — check whether the caller identity is verified;
- "the attacker is already local" — privilege escalation or cross-tenant
  access is a new capability;
- "the service runs as root by design" — check what the attacker can make it
  do.

## Severity Floor (AUTH-specific)

- Unauthenticated remote auth bypass to admin/root: **Critical**.
- Local privilege escalation: **High**.
- Cross-tenant identity/credential access: **High**.
- Missing auth on a network-exposed management endpoint: **Medium** (High if
  state modification).
- File permission issue with no proven privilege impact: **Low/Medium**.
