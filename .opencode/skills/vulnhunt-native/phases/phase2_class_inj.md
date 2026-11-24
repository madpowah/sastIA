# Class Group: Injection (INJ) — Native

## Dangerous Sink Reference

- **Command execution**: `system`, `popen`, `exec*`, `posix_spawn`, `fork+exec`,
  `CreateProcess`, shell wrappers, `sh -c`.
- **Path/file operations**: `open`, `openat`, `fopen`, `creat`, `unlink`,
  `rename`, `chdir`, `dlopen`, `mkstemp`, archive extraction (`tar`, `zip`,
  `cpio`), recursive delete.
- **Format strings**: `printf`/`fprintf`/`snprintf`/`syslog`/`err`/`warn` with
  a user-controlled format string; `%n`.
- **Environment**: `setenv`, `putenv`, `execve` environment, `PATH`,
  `LD_PRELOAD`, `LD_LIBRARY_PATH`, `TMPDIR`, locale, `HOME`.
- **Deserialization / parsing**: pickle, Java serialization, YAML, XML, protobuf
  with attacker-controlled descriptors, custom binary formats.
- **SQL** (embedded DB): raw query construction, ORM raw fragments.
- **Templates / eval**: template compile/render with user-controlled template,
  `eval`, `dlopen` of user path.
- **Log / IPC**: log injection, syslog format, IPC message injection, command
  injection through a helper process.
- **Argument injection**: user value starting with `-` passed to a tool that
  interprets it as an option (`ssh`, `git`, `tar`, `find`, `curl`).

## Vulnerability Classes

- **Command injection**: trace input into a shell or argument vector. Check
  quoting, `execve` vs `system`, argument injection (`--`), and environment.
- **Path traversal / symlink**: trace input into a path. Check canonicalization
  (`realpath`, `openat`, `O_NOFOLLOW`), base directory, `..`, absolute paths,
  symlink races, TOCTOU.
- **Format string**: user input used as the format argument, not as an argument
  to `%s`. CWE-134.
- **Environment injection**: privileged code trusting `PATH`, `LD_*`, `TMPDIR`,
  locale, `HOME`, or `IFS`. CWE-426/427.
- **Unsafe deserialization**: untrusted bytes reconstruct objects or trigger
  gadget chains. CWE-502.
- **File/archive parsing**: path traversal in archive entries, zip bombs,
  symlink entries, absolute paths, duplicate entries, encoding tricks.
- **SQL injection** (embedded DB): string construction into SQL. CWE-89.
- **Argument injection**: user value passed as an option to a privileged
  helper. CWE-88.
- **Log injection**: control characters/format strings in logs. CWE-117.

## Gate 2b (INJ-specific)

- **Empirically verify the sanitizer/escaping**. Read the source or construct a
  test. If you cannot, treat it as ineffective.
- **Context match**: shell quoting does not protect SQL; HTML escaping does not
  protect a path; URL encoding does not protect a command; `strlcpy` does not
  protect a binary copy.
- **Path checks**: string prefix checks are bypassable (`/base` vs `/baseevil`,
  `..`, symlinks, `//`, Windows separators). Require canonicalization +
  `openat`/`O_NOFOLLOW` or equivalent.
- **Argument injection**: a value that starts with `-` is not made safe by
  shell quoting. Require `--` or an allowlist.
- **Format string**: only a constant format string is safe. `printf(user)` is
  not made safe by escaping `%`.

## Gate 3 (INJ-specific)

Do not eliminate because:
- the path is "internal" — check reachability;
- the command is "trusted" — check whether the input can alter arguments or
  environment;
- the file is "read-only" — read access can still leak keys/data;
- the attacker "can already run code" — cite the exact existing path; a
  different privilege/tenant is a new capability.

## Severity Floor (INJ-specific)

- Unauthenticated remote command execution: **Critical**.
- Local privilege escalation via command/path injection: **High**.
- Arbitrary file read/write with privilege: **High**.
- Path traversal limited to a sandbox directory: **Medium**.
- Argument injection with no proven privileged effect: **Low/Medium**.
