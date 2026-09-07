# Schema Sentry

Schema Sentry is an enforceable, multi-authority release gate for API revisions. A registrant proposes an old schema, a candidate schema and a migration policy from three distinct parsed HTTPS origins. Validators fetch all three during registration, hash the complete response bytes, and freeze bounded snapshots plus their authoritative digests before any review can occur.

## Independent authority model

The registrant cannot attest any source. Three distinct authority wallets are assigned one immutable source slot each and must confirm the exact validator-frozen digest for their slot. A review remains `PENDING_ATTESTATIONS` until all three independent identities have attested. A separate release controller owns the execution right and cannot be the registrant.

## Enforceable workflow

```text
PENDING_ATTESTATIONS -> READY -> APPROVED -> RELEASED
                              -> BLOCKED
```

Validators agree on the exact compatibility verdict, breaking paths and covered paths from the frozen snapshots. Only `COMPATIBLE` creates `APPROVED`. Only the nominated release controller can call `execute_release`, and the call succeeds only from `APPROVED`; every other verdict gates the release in `BLOCKED`.

## Verification

```bash
genvm-lint check sentry_core/schema_sentry.py
python -m pytest compat_checks -q
```

The direct suite covers complete digest freezing, wrong-digest rejection, three-wallet attestation, owner/authority separation, release-controller authorization, blocked release enforcement, duplicate IDs and hosts, and forged validator fields.
