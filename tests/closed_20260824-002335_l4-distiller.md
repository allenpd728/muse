# Test spec — L4 distiller (task #196)

Written 2026-08-24 by the completing session, per TASK_WORKFLOW §6.

## Status of coverage

5 pytest tests in tools/muse_distill/tests/test_distill.py, all passing:
- Stats extraction (velocity mean/pstdev, note_count)
- Curve-shape classification (flat, arch — with 3-point map positive)
- Revision dict shape (params tempo, interpretation fields)
- Dual dump format (yaml with specific key, json with named field)

Run: `cd tools/muse_distill && python -m pytest` (<1 s).

## Behaviors still needing coverage (gaps)

1. **wavering-shape classification.** The classify logic has flat | arch |
   wavering paths; wavering is the default for degenerate curves. A pin
   map case would make it positive.
2. **Human-apply walk.** The revisions are human-reviewable; the apply
   path through muse_author's reset remains in the C2 loop to keep the
   "human approves" invariant, not a programmatic twist. Design doc keeps
   this accurate.
3. **Curves dict on the mockup.** The mockup supports `curves` sections,
   but the extractor uses tempo_map/notes; richer devices (attack,
   release, legato) belong in the mockup-update path, not here.
4. **CLI end-to-end.** __main__ writes delta YAML; subprocess test
   currently verified via the API, not the CLI entry point.

## Invocation

`cd tools/muse_distill && python -m pytest` (<1 s).

---

## Closed 2026-08-24 (issue #222, run=20260824-1059-b671)

Landed coverage: `tools/muse_distill/tests/test_distill.py` grew 5 → 7
tests, closing gaps 1 and 4:

- **wavering classification pinned positive** — a monotonic fall
  (120→110→100 bpm) is neither flat (range ≥ 2) nor arch (first > last);
  asserts the shape and the extracted range.
- **CLI end-to-end** — `python -m muse_distill <mockup.json> --out` in a
  subprocess: a dumped mockup goes in, the delta YAML comes out with the
  arch shape and tempo bounds, and the stdout summary names the curve.

Gaps 2–3 stand by design: the human-apply walk is the C2 loop's
"human approves" invariant (not a programmatic test), and curves-dict
extraction belongs to the mockup-update path.

Gate: `cd tools/muse_distill && python -m pytest` → 7 passed (<1 s);
`./tools/run_tests.sh` fast tier → all suites green.
