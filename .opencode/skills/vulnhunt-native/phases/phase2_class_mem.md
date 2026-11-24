# Class Group: Memory & Lifetime (MEM) — Native

## Dangerous Sink Reference

- **Size arithmetic**: `malloc`, `calloc`, `realloc`, `alloca`, `pool_get`,
  `kmem_alloc`, `kmalloc`, `vmalloc`, `new[]`, flexible array members, VLAs.
- **Copies**: `memcpy`, `memmove`, `strcpy`, `strlcpy`, `strncpy`, `sprintf`,
  `snprintf`, `vsnprintf`, `copyin`, `copyout`, `read`, `recv`.
- **Indexing**: `ptr[i]`, `array[i]`, ring buffer head/tail, `base + offset`,
  bitfields, shift counts.
- **Lifetime**: `free`, `pool_put`, `kfree`, `delete`, refcount decrement,
  list removal (`TAILQ_REMOVE`, `LIST_REMOVE`, `RB_REMOVE`).
- **Containers**: `TAILQ_*`, `LIST_*`, `SLIST_*`, `RB_*`, `STAILQ_*`, custom
  `->next` surgery.
- **Reentrancy**: callbacks, signal handlers, destructors, `atexit`, completion
  handlers, `setjmp`/`longjmp`.
- **Type confusion**: casts, unions, tagged pointers, `void *` context.

## Mandatory Checks

### 1. Domain proof (allocation vs copy)

For every allocation and every copy into it, prove:

- same width (no 64 → 32 → 16 truncation);
- same signedness (no negative size cast to `size_t`);
- same unit (bytes vs elements vs pages);
- multiplication/addition does not overflow before the allocation;
- off-by-one is accounted for (terminator, header, alignment);
- the length is re-validated after any transformation.

| Allocation | Size expression | Copy length expression | Same domain? | Overflow possible? |
|---|---|---|---|---|

### 2. Lifetime ledger

For every `free`/`put`/`delete`:

1. List every alias (local pointer, struct field, list node, callback context,
   global, fd/refcount).
2. List every path that can use an alias after the free: normal, error, loop
   iteration, callback, reentrancy, signal.
3. Check whether the free path invalidates **all** aliases or only one.
4. A NULL assignment does not clear aliases held elsewhere.

| Free site | Aliases | Used after free at | Path | Guard? |
|---|---|---|---|---|

### 3. Container cursor invariants

For each container mutation:

- After a delete, which cursor points to the freed node?
- Does the delete update `head`, `tail`, `prev`, `next`, `cur`, `p`?
- Does a subsequent append/insert assume the cursor is non-NULL?
- If the container becomes empty, is the append path skipped?
- Are `cur = cur->next` and `p = cur` consistent when `cur` becomes NULL?

### 4. Reentrancy

Can a callback invoked during the operation re-enter and mutate the same state?

- user-provided comparator/destructor;
- completion callback (e.g., `curl_easy_pause` in a socket callback);
- signal handler that frees/reallocates;
- `longjmp` out of a critical section.

### 5. Type confusion / uninitialized memory

- cast to a different struct and read fields;
- union member read after write to another member;
- `void *` context passed to the wrong callback type;
- tagged pointer / low-bit tagging;
- partial initialization on error path;
- `realloc` failure loses the original pointer.

## Gate 2b (MEM-specific)

- **Sanitizers are evidence, not proof.** ASan/UBSan/KASan/MSan output is a
  strong PASS; absence of a report is not a PASS.
- **Static proof is acceptable** if it shows the exact size/domain mismatch or
  the exact free-then-use path with file:line.
- **Do not credit** a `NULL` check on one alias as protection for another.
- **Do not credit** a length check in a different domain.
- **Do not credit** `strlcpy`/`snprintf` for a binary copy.
- **Do not credit** a refcount increment without checking the decrement path.

## Gate 3 (MEM-specific)

Do not eliminate because:
- "it only crashes" — see the remote availability floor in `phase2_shared.md`;
- "the attacker needs a rare sequence" — record the sequence; rarity affects
  severity, not existence;
- "the allocator/hardening prevents it" — cite the hardening and prove it
  covers this case;
- "another layer validates the length" — cite the layer at file:line or treat
  as ineffective.

## Severity Floor (MEM-specific)

- Remote unauthenticated kernel/daemon memory corruption: **Critical/High**.
- Remote unauthenticated panic/crash: **High**.
- Local privilege escalation: **High**.
- Read-only OOB with a proven info leak: **Medium/High**.
- Null deref with no proven control: **Low/Medium** (High if remote panic).
