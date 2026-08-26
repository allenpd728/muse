# System audit — A2.2 analyzer / diff / viz (2026-08-26)

**Task:** #290. **Modules:** muse_analyze, muse_diff, muse_viz.
**Method:** CLI invocations + file checks; suites: 49 passed; findings: one documentation issue filed (#292).

| Module | Doc claim | Evidence | Verdict | Findings |
|---|---|---|---|---|
| muse_analyze | Full corpus → docs/analysis-report.md; patterns: exact/transposed/ostinato/imitative | `--all` rewrites report; file unchanged post-audit (reproduce) | works | — |
| muse_diff | IR ↔ IR recall/precision in tick space; self-test passes; tolerance classifier | `--self-test` OK (insertion/drift classification); identical identical-pair recall=1.0 | works | — |
| muse_viz | PNG plots | rendered 2 parts → 17KB PNG, header verified | works | — |

**Finding (documentation, #292):** the analyzer README's usage line shows `<file>` form, but `_resolve_work_id` expects a work-id like `bach-bwv227`; passing a path raises FileNotFoundError inside corpus_loader. README needs the work-id form. Audit-filed per A1-design — documentation label.

**Suites at close:** 49 passed for the three modules; all green.
