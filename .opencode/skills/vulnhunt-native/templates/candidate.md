# Candidate Template (Native)

```markdown
### [VULN-NNN] Title

- **Input**: inventory # and description
- **Lens**: INJ / AUTH / MEM / PROTO / IDENT
- **Class**: CWE-XXX: Name
- **Severity**: Critical / High / Medium / Low / Informational
- **Location**: file:line
- **State object**: object/field or N/A
- **State precondition**: what must be true
- **Invariant violated**: identity / bounds / lifetime / order / auth / spec
- **Gate 0 (design contract)**: ...
- **Gate 1 (reachable)**: ... (call sites + state sequence)
- **Gate 2a (attacker control)**: ... (data or state; trust level)
- **Gate 2b (validation/domain)**: ... (guards, domains, composition)
- **Gate 3 (new capability)**: ...
- **Gate 4 (composition)**: confirmed / latent
- **Entry point**: ...
- **Data/state flow**: source -> ... -> sink (file:line each step)
- **Root cause**: 1-2 sentences
- **Exploitability**: practical assessment
- **Confidence**: high / medium / low
```
