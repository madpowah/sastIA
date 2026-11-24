# Native Input Checklist

Use the section that matches the target class. Add target-specific vectors.

## Network daemon / protocol parser

- Packet header fields: length, type, flags, version, checksum, sequence, ACK,
  window, offset, count.
- Options/extensions/TLVs: type, length, value, nesting, duplicates, order.
- Payload: text, binary, compressed, chunked, fragmented.
- State: handshake, authentication, session, connection pool, retransmission
  queue, reassembly buffer.
- Error/timeout/reset/close paths.
- IPv4 vs IPv6, TCP vs UDP, TLS vs plaintext, one backend vs another.

## Kernel / driver

- Syscall arguments: pointers, lengths, flags, offsets, handles, ioctls.
- `copy_from_user` / `copy_to_user` sizes and user pointers.
- Netlink, io_uring, eBPF, seccomp, namespaces.
- Device `ioctl`, `mmap`, DMA, USB descriptors, firmware blobs.
- `procfs`/`sysfs` knobs, module parameters.
- Interrupt/signal/softirq reentrancy, locking, RCU, refcounts.
- Privilege: `CAP_*`, `setuid`, `ptrace`, `userfaultfd`, `io_uring`.

## Library / SDK

- Public headers and exported symbols.
- Every option setter and its state (per-object/per-connection/global).
- Callbacks, completion handlers, cancellation, reentrancy.
- Handles, pools, caches, sessions, shared state.
- Thread-safety and lifetime (who owns/frees what).
- ABI/type confusion across versions.

## CLI / file-format parser

- `argv`, `stdin`, environment, locale, `PATH`, `TMPDIR`, `HOME`.
- File content, filename, extension, symlink, hardlink, permissions.
- Archive entries: path traversal, absolute path, symlink, duplicate, encoding.
- Recursive/streaming formats, compression, size limits, depth limits.
- Temp files, `O_EXCL`, `mkstemp`, cleanup.

## Firmware / embedded

- Update image header, length, signature, version, rollback.
- Flash layout, partition table, bootloader, recovery mode.
- Device descriptors, network services, debug UART/JTAG.
- Crypto/key storage, secure boot, attestation.
- Denial-of-service via watchdog/reset.

## IPC service / broker

- Socket type, permissions, abstract namespace, peer credentials.
- Message framing, length, serialization, authentication.
- Method/policy authorization, per-object vs per-connection.
- Shared memory, file descriptor passing, `SCM_RIGHTS`.
- Reentrancy, blocking calls, deadlocks.

## Universal questions

For every input:

1. What state must be true for this input to have this effect?
2. What other field/constant is it compared to?
3. Who can set it? (remote/local/user/admin/root)
4. What is the worst value it can take? (0, max, 2^31, empty, first/last)
5. What buffer/allocation does it bound?
6. What happens on the error/absent path?
