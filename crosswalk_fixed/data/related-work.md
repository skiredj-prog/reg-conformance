# Related work and source-boundary notes

## Scope of this review

This document records a bounded documentary comparison, not an endorsement or formal equivalence assessment by NIST, ISO, or the REG authors.

## NIST AI Risk Management Framework 1.0

Primary source reviewed: NIST AI 100-1, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, January 2023.

Official PDF: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf

The reviewed occurrences of “evidence” concern documented governance, validation, or empirical evidence of incidents. The review did not establish that NIST defines a runtime execution-state axis equivalent to REG `EvidenceStatus`. The shared word should therefore not be treated as semantic equivalence.

## ISO/IEC 42001:2023

The comparison was based on secondary sources; the full official standard was not available for controlled review. The secondary material describes evidence primarily as audit and management-system records (for example, policies, logs, reviews, operating records, and impact assessments). This is not sufficient to establish a runtime status equivalent to REG `EvidenceStatus`.

## REG public corpus

The documentary review identified the following public materials as the available normative baseline:

- RFC-0 through RFC-7 under `reg-standards-baseline/rfc/` in the `reg-conformance` repository.
- `spec.md` v0.3.1, as identified in the review.
- Manuscript v7.0, as identified in the review.

No public artifact named **“REG Core Protocol v0.3.0”** was found. Accordingly, this crosswalk does not cite that title as a verified source. The frozen public RFCs are the normative public sources used for this bounded assessment.

## Interpretation rule

`verification_status: "unverified"` means that the mapping has not been formally validated against an authoritative definition or confirmed by the authors of the target framework. It does not mean the proposed relationship is necessarily false.
