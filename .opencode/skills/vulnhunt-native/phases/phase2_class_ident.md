# Class Group: Identity, Credential & Reuse (IDENT) — Native

## Scope

Security-state objects that outlive a request/message:

- connection pools (TCP, TLS, SSH, database, file descriptors);
- TLS session caches / session tickets;
- credential caches (netrc, .pgpass, keychains, token caches, SSH agent);
- DNS / HSTS / alt-svc caches;
- object pools / buffer pools that carry state;
- multiplexed sessions (HTTP/2, SSH, QUIC);
- host-key / known_hosts / certificate stores.

## Mandatory Inventory

For each pool/cache/session store:

| Pool | Object | Reuse predicate | Key function | Identity carried | Fields compared | Fields omitted |
|---|---|---|---|---|---|---|

For each object field:

| Field | Security role | Owner (request/connection/global) | Clone | Free | Compare/Match | Key/Hash |
|---|---|---|---|---|---|---|

## Mandatory Checks

### 1. Field coverage

Any field with a security role that is present in the object but absent from
the `compare/match/key` function is a **candidate**.

Security-relevant fields for a connection/session include:

- client certificate (`clientcert`, `cert_blob`, `cert_type`);
- private key (`key`, `key_blob`, `key_type`, `key_passwd`);
- CA file/path, CRL, pinned key;
- `verifypeer`, `verifyhost`;
- TLS version, ciphers, curves, signature algorithms;
- SNI / hostname / port / scheme;
- proxy / tunnel;
- user / password / auth mechanism (Basic, Digest, Negotiate, NTLM, SASL,
  SRP, SSH key);
- host key / known_hosts entry;
- session ID / ticket / resumption secret.

### 2. Marker vs value

A key component that records only **presence** (`":CCERT"`, `has_cert`,
`auth_type`) instead of the value (path, hash, ID) is a collision candidate.
Two different credentials can produce the same key.

### 3. Ownership: per-request vs per-connection

- A per-request security field absent from the connection identity predicate
  is a candidate.
- A per-connection field cloned from the first handle and never updated is a
  candidate.
- A shared pool used by multiple handles/tenants/users is a candidate surface.

### 4. Credential selection

For credential lookup (netrc, keychain, token cache):

- What is the lookup key? (host, host+user, host+realm, host+path)
- What happens when the exact key is missing? Is there a fallback to a broader
  key? A fallback to another user's credential is a candidate.
- Is the credential bound to the resource actually contacted (host, port,
  scheme, proxy)?
- Can userinfo in a URL (`user@host`) change the selection without a password?

### 5. Policy predicate completeness

For host key / certificate / token validation:

- Are all key types / algorithms / versions validated?
- Is there a default-allow branch for an unrecognized type?
- Is the validation applied to every backend (OpenSSL, GnuTLS, mbedTLS,
  rustls, Schannel, wolfSSL, libssh, libssh2)?
- Does the test matrix cover every backend?

### 6. Cross-handle / cross-tenant test

1. Handle A sets identity A (cert/key/token) and creates a connection.
2. Handle B sets identity B and shares the pool.
3. Assert B does not reuse A's connection, or that the reused connection
   presents B's identity.
4. Repeat for the session cache, not just the connection cache.

## Gate 2b (IDENT-specific)

- A comparison that omits a field is not a defense.
- A key that contains a marker instead of a value is not a defense.
- A per-backend check missing on one backend is not a defense.
- A test that covers only one backend is not a defense.

## Gate 3 (IDENT-specific)

- Cross-principal identity inheritance is a new capability even if the attacker
  can authenticate as themselves.
- Stale credential reuse after rotation/revocation is a new capability.
- A cache key collision that lets one tenant read another tenant's data is a
  new capability.

## Severity

- Cross-tenant / cross-principal auth bypass: **High/Critical**.
- Stale credential after rotation: **Medium/High**, depending on revocation
  expectation.
- Same-principal stale state with no security impact: **Low / Code Smell**.
