# Crosswalk Module: Terminological and Conformance Mapping (REG)

This module provides an interactive, open correspondence matrix between the execution concepts of the **REG (Runtime Execution Governance)** protocol and existing terminologies or regulatory and normative frameworks (NIST AI RMF, ISO/IEC 42001, EU AI Act, IAM, etc.).

---

## 🎯 Objective and Philosophy

* **Semantic proximity, not legal equivalence**: The matrix identifies points of contact or conceptual overlap. It does not assert strict equivalence or automatic conformance.
* **Transparency and independence**: The terms and statuses presented are proposals, subject to independent review by the authors of the cited frameworks and by the community.
* **Neutrality**: The mention *"Not found in the consulted sources"* only indicates that no direct equivalent was identified in the initial bibliographic study. It is not a definitive absence from the targeted framework.

Every row is governed by [`MAPPING_POLICY.md`](MAPPING_POLICY.md): what a row must cite, state, and what each status may mean.

---

## 📐 Taxonomy and Vocabulary

### Relation types (`relation`)

*Defined for future use. Not yet part of `schema.json`.*

* **`partial` (Partial match)**: The external framework covers a similar need, but with different mechanisms, scope or guarantees.
* **`shared_word_different_object` (Shared word, different object)**: The same term is used in the literature or the standard, but designates a different object or technical artefact.
* **`not_found_in_sources` (Not found in the consulted sources)**: No direct equivalent term has been identified in the literature examined to date.

### Verification statuses (`verification_status`)

* **`unverified` (Unverified)**: Initial proposal derived from the preliminary bibliographic analysis.
* **`partially_checked` (Partially checked)**: Reviewed by at least one third party, or aligned with a specific regulatory or normative text. *Not yet part of `schema.json`.*
* **`verified` (Verified)**: Formally confirmed by the authors or experts of the framework concerned. *Not yet part of `schema.json`.*
* **`specified-in-rfc4` (Specified in RFC-4)**: The vector is described in the RFC, but no executable test in the laboratory repository covers it yet. This is **not** a verification.
* **`tested` (Tested)**: An executable test in the laboratory repository covers the vector. The entry then carries an `evidence` object with the test file, the executed commit SHA, and the CI run identifier.
* **`planned` (Planned)**: Vector listed in the catalogue `vectors/dist/vectors.json`, with no executable test to date. It does not appear in the text of the published RFCs.
* **`frozen` (Frozen)**: The source document is frozen (RFC-4, frozen version) and its vectors are covered by other rows. This status is neither a verification nor the absence of one: it only signals that a direct correspondence remains to be established.

The status `verified-by-vector` is no longer used: it asserted a verification without evidence.

---

## 🤝 How to Contribute

Contributions are welcome to enrich, correct or validate the matrix:

1. **Submit a correction or a new term**:
   * Edit the JSON data file directly: [`data/crosswalk.json`](data/crosswalk.json). It must validate against [`schema.json`](schema.json).
   * Open a pull request describing the change and giving the associated textual reference, as [`MAPPING_POLICY.md`](MAPPING_POLICY.md) requires.
2. **Open a discussion**:
   * Open an issue on the repository with the `crosswalk` label to request a review: [Create an issue](https://github.com/skiredj-prog/reg-conformance/issues/new).

---

## 📁 Directory Structure

* `index.html`: Interactive web interface (filters, search, counters).
* `data/crosswalk.json`: Structured data source for the terminological mapping.
* `schema.json`: JSON Schema for rows and evidence objects.
* `MAPPING_POLICY.md`: Rules a row must meet before it is merged.
* `data/related-work.md`: Summary of the research works and standards concerned.
* `data/rfc-mapping.md`: Draft mapping for the RFC specifications.

The vector catalogue itself is maintained at `vectors/dist/vectors.json`, at the root of the repository.
