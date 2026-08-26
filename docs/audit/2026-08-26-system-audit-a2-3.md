# System audit — A2.3 golden vectors (2026-08-26)

**Task:** #291. **Module:** s1_stream.
**Method:** explicit verify() on mxl + mid sources, tamper_proof, suite: 45 passed (constructed with s1's fast+full in one dir).

| Doc claim | Evidence | Verdict | Findings |
|---|---|---|---|
| golden verify exits 0 on byte-exact match, 1 otherwise (CI gate) | \`verify ../../corpus/bach/bwv227.1.mxl golden/bach_bwv227.1.json\` → PASS; byrd golden verified via mid → PASS | works | — |
| tamper detection | corrupted vector (96→99 char sub) verify → False | works | — |
| canonical form | schema-stability + formatting pins covered by the 45-test suite | works | — |
| no machine-local paths | audit of the lineage hops formats; vectors keep repo-relative | works | — |

**Findings:** none filed. 45 tests incl. the full-corpus + schema-stability pins pass.

**Suites at close:** 45 passed / full gate to be verified after this row is committed (per audit protocol).
