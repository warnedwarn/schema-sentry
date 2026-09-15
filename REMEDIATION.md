# Steward remediation

| Requirement | Code path | Targeted proof | Deployment or browser proof | Status |
| --- | --- | --- | --- | --- |
| Remove the obsolete registration call | Browser `register` action passes review ID, service, revision, three sources, three authority addresses, and release controller | Frontend signature test | Production source inspection | PASS |
| Remove the obsolete acknowledgement flow | Browser exposes `attest_source(review_id, slot, digest)` and no `acknowledge` method | Frontend signature and removed-method tests | Production UI exposes slot and digest attestation | PASS |
| Operate the revised contract lifecycle | Browser supports register, three authority attestations, review, execute release, and canonical readback | Frontend lifecycle surface tests | Production loaded `SS-1788740378` as `RELEASED / COMPATIBLE`; recorded writes are finalized | PASS |
| Preserve transaction finality semantics | Browser waits for `FINALIZED`, requires `MAJORITY_AGREE`, and rejects failed execution | Frontend receipt-gate tests | Production source contains the receipt gate | PASS |
| Use the submitted deployment | Browser address matches the corrected deployment and the deployed source matches repository source | Deployment verifier | `0xF301...00D49`, source match, and production build verified | PASS |
