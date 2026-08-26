# System audit — A1.2 post-mockup chain (2026-08-26)

**Task:** #279. **Modules:** muse_render, muse_compare, muse_distill, muse_audio.
**Method:** per-module CLI/API evidence against README claims; seams executed (render→WAV, compare→deltas.json, distill→provenance, audio→manifest+sha256). Suites: 64 passed (all four modules).

| Module | Doc claim | Evidence | Verdict | Findings |
|---|---|---|---|---|
| muse_render | README: mockup → audio (sfizz/spike fallback); CLI `python -m muse_render <mockup.json> [-o out.wav]` | CLI on committed mockup `seeds/bwv227.1.v2.mockup.json`: wrote /tmp/audit-render-cli.wav, 279 notes, 38.5s, parts P1-P4; wav RIFF/44.1k. duration = 76 quarters at tempo_map[] default 120bpm ≈ 38.0s (correct, not the 0.69s ppq bug) | works | timestamp audit note: 38.5s at empty tempo_map 120bpm matches; no issue |
| muse_compare | README: same score+seed, deterministic per-model variants, blind ledger + deltas.json | CLI: models a,b; ledger hashes e8727ca3/5cd0de0a; deltas.json pair model-a|model-b with tempo/density keys | works | — |
| muse_distill | README: extract tempo curve/bpm/velocity/rubato/part gains; CLI mockup → delta | CLI: /tmp/audit-delta.yaml written; extract_interpretation returns dataclass with all 8 fields; S3.8b: provenance.operation + extends stamped when mockup_path given | works | S3.8b verified with path; without path gets operation+distilled_from but no extends (correct per design) |
| muse_audio | README: stand-in (deterministic) + --live (real L1.3 loop); committed manifest; WAVs session-local | render_revision on v1/v2 with sha256 in manifest; manifest json format muse-audio-manifest-v1; write_manifest verified | works | — |


**Findings:** none filed. All seams verified against README claims; suites green on audit completion (64 passed). T6 (#275) covers committed-mockup load+render — this audit consumes that pin at the seam level, doesn't duplicate it.

**Suites at close:** `./tools/run_tests.sh` fast tier all green (33 suites, 870 passed per boardroom stats at audit time).
