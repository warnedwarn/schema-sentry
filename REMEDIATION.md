# Steward remediation

| Requirement | Code path | Targeted proof | Deployment or browser proof | Status |
| --- | --- | --- | --- | --- |
| Remove the obsolete registration call | Browser `register` action passes review ID, service, revision, three sources, three authority addresses, and release controller | Frontend signature test | Production source inspection | UNVERIFIED |
| Remove the obsolete acknowledgement flow | Browser exposes `attest_source(review_id, slot, digest)` and no `acknowledge` method | Frontend signature and removed-method tests | Production browser flow | UNVERIFIED |
| Operate the revised contract lifecycle | Browser supports register, three authority attestations, review, execute release, and canonical readback | Frontend lifecycle surface tests | Fresh public-site lifecycle | UNVERIFIED |
| Preserve transaction finality semantics | Browser waits for `FINALIZED`, requires `MAJORITY_AGREE`, and rejects failed execution | Frontend receipt-gate tests | Production source inspection | UNVERIFIED |
| Use the submitted deployment | Browser address matches the corrected deployment and the deployed source matches repository source | Deployment verifier | Explorer, manifest, and production build | UNVERIFIED |
