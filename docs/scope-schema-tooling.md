# Scope — Schema tooling (first milestone)

First buildable layer: JSON Schema for the spec, a validator, example documents,
and CI. Node.js throughout. Everything later (composer, engine, listener) depends
on "validates against schema v0.x" being mechanically checkable.

## Decisions (locked)

- **Schema decomposition:** split by spec section — 7 files
  (`metadata`, `globals`, `material`, `form`, `constraints`, `renditions`,
  `extensions`) referenced from root `schema/muse.schema.json` via `$ref`.
  Mirrors SCHEMA_SPEC.md structure; a spec edit maps to one schema file;
  per-section files can be built in parallel.
- **Validator:** ajv (JSON Schema draft 2020-12, `$ref` resolution).
- **Examples — three tiers:**
  - `examples/minimal.muse.json` — smallest valid document (happy path)
  - `examples/full.muse.json` — exercises every section; stress-tests the spec
  - `examples/invalid/*.muse.json` — one file per failure mode; the test harness
    must assert these are *rejected* (guards against a validator that accepts
    everything)
- **Package:** root `package.json`, `"type": "module"`, ajv only dependency.
  `npm test` runs validation over all examples (valid pass, invalid fail).
- **CI:** GitHub Actions on push to `dev`: `npm ci && npm test`.

## Target layout

```
package.json
tools/validate.mjs        # CLI: validate a .muse.json file
tools/test.mjs            # runs examples/ + examples/invalid/ assertions
schema/muse.schema.json   # root, $refs the 7 section files
schema/{metadata,globals,material,form,constraints,renditions,extensions}.schema.json
examples/minimal.muse.json
examples/full.muse.json
examples/invalid/*.muse.json
.github/workflows/ci.yml
```

## Integration review

The last task in a batch is a **cross-task integration review** (this batch: issue
#37), blocked by everything else in the batch. It reads the batch's full output
together and catches convention drift / semantic mismatch — the things structural
validation won't. Review is read-only; findings become new claimable corrective
tasks. **Pattern for all future batches: the final task is the integration
review, blocked by the rest of the batch.**

## Consequences for spec work

Writing the schema will surface gaps/contradictions in SCHEMA_SPEC.md. When that
happens, the schema task does not invent semantics — it files a blocker per
TASK_WORKFLOW.md, and the spec gets amended (with changelog discipline) before
the schema task completes.
