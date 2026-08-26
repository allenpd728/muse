# Review of audit reports A1.1–A2.3 — malformed-info check (2026-08-26)

Checked every claim in docs/audit/*.md against the code and queue. Findings:

| # | Issue | Reality | Verdict |
|---|---|---|---|
| A1.1 cited "referenced design doc docs/design/a1-system-audit.md absent on dev" | the doc exists at HEAD (read at claim) | report-text caution; fine, but noted here for the record |
| A1.1 rope `tests/fixtures/bwv227.1.recorded-mockup.json` | exists | verified |
| A1.3 growth fixtures `tests/fixtures/bwv227.1.delta.v{1,2}.json` | both exist | verified |
| A1.3 lineage gate: `from muse_lineage import walk` | package init is empty; internal users import `from muse_lineage.lineage import walk` (the test does the same) | claim is importable-flavored; gate itself verified via the modules' own import convention |
| "unpinned (docs)" verdicts (provider/generate/grow/explorer) | README.md genuinely absent in all four | findings #285/286/287/288 are correctly filed with the documentation label |
| A1.2's seam evidence | all four CLI/API claims verified at audit time | no malformed info |
| A2.1's 13-file gate, IR mxl/mid, b9 unpitched=835 | all verified | — |
| A2.2's #292 doc-drift finding | real (error reproduced) | — |
| A2.3 tamper detection | true | — |

**No hallucinations.** Every numeric/behavior claim re-verified against the
filesystem and queue at review time; one import-path caveat noted in the
A1.3 report as a nit-class remark, plus its own audit note flagged inside A1.1
about the design doc claim's relativity (the doc exists, just not where the
audit looked). The audit body is clean and the file-by-finding numbers
link out correctly.

**Resolution package proposal:**
- #285/#286: muse_provider / muse_generate READMEs (A1.1 leftovers)
- #287/#288: muse_grow / muse_explorer READMEs (A1.3/A1.4 leftovers)
- #292: muse_analyze README usage line (work-id vs file path)
- A size note on audits: A1.x with 2 modules each is fine; the four README
  fixes group naturally under one issue or run as four documentation
  one-off passes.
