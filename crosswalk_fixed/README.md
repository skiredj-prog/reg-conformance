# REG crosswalk — documentary audit candidate

This directory is an **isolated candidate** for the documentary crosswalk reported on 13 October 2026. It does not replace the existing production crosswalk under `crosswalk/`; the existing crosswalk and its live page are left untouched pending review of the target and data model.

## Files

- `index.html` — standalone browser view of the eight documentary mappings.
- `data/crosswalk.json` — eight mappings; every row is `unverified`.
- `data/related-work.md` — source-boundary notes for NIST AI RMF and ISO/IEC 42001.
- `data/rfc-mapping.md` — comparison against the public REG RFC corpus and OP-1 disposition.

## Evidence and status discipline

All eight rows retain `verification_status: "unverified"`. The `relation_type` field describes the kind of preliminary relationship; it is not a verification status. “Not found in sources” is bounded to the sources named in the documentary review.

No public document titled “REG Core Protocol v0.3.0” was found. The candidate therefore does not cite that title as a verified source. OP-1 remains unresolved: the public material reviewed does not establish that `EvidenceStatus` normatively represents pending or failed evidence writes.

## Validation

The JSON is intentionally self-contained and can be parsed with any JSON parser. This candidate is not a change to the normative REG core, does not claim implementation, and does not assert conformance with NIST or ISO.
