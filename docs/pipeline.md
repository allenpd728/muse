# Pipeline — composer to listener, with live status

The full Muse loop, end to end. **Status is a living table** — agents update
it whenever they complete a task that changes a tool's state (per
TASK_WORKFLOW.md: status sweep is a session duty). Status values:
`✅ done` · `⚠️ partial` (works with caveats) · `🔄 in progress` · `❌ not built` · `🚫 blocked`.

## The loop

```
1. AUTHOR   compose in any DAW/notation tool (or later, the composer tool)
2. IMPORT   importer/cli.mjs: MIDI/MusicXML → .muse.json (lossy, marked)
3. REFINE   cleanup: human/agent edits, guided by explorer + validation
4. VALIDATE npm run validate / npm test — schema is canonical from here
5. INTERPRET schema + rendition → §7 performance document (LLM or offline)
6. PLAY     tools/play.mjs: performance → audio (V1 synth, V2 plugins)
7. LISTEN   listener picks composer + rendition, hears the piece
```

## Status per step

| Step | Tool | Status | Notes |
|---|---|---|---|
| 1. Author | external DAW/notation (MusicXML/MIDI out) | ✅ done | any tool with MusicXML/MIDI export works |
| 2. Import | `importer/` (MIDI/MusicXML → IR → schema) | ✅ done | Batch 2; themes assembled + uses wired (#92); large scores need `--max-old-space-size` |
| 3. Refine | composer tool (`explorer/src/composer/`) | ✅ done | full MVP: graph model (#79), shell (#80), edge editing (#81), material editors (#82), validation + export (#83) |
| 4. Validate | `tools/validate.mjs`, `schema/`, semantics lint | ✅ done | Batch 1; 57 suites green; v0.3 adds tempo_shapes, structured instrumentation, mix topology (#75–#77, tests #84–#87) |
| 5. Interpret | `interpreter/offline.mjs` / `expand.mjs` | ✅ done | offline fallback realization (#91); LLM harness with retry loop; Gemini free-tier adapter (#106/#110), manual paste mode (#108/#111); live E2E pending key (#113) |
| 6. Play | `player/render.mjs` → WAV | ✅ done | render-core split (browser-safe) with honor-or-drop techniques (#86); demo WAVs in `docs/demo/` |
| 7. Listen | `explorer/src/listen/` | ✅ done | playback core (#97), Listen tab (#98), A/B rendition switch (#99), WAV download (#100) |

## Supporting surfaces

| Surface | Status | Notes |
|---|---|---|
| Explorer (`dev--muse-qa-58fd708e.netlify.app`) | ✅ done | read-only browse/validate + composer + listener; QA preview only |
| Benchmark corpus (10 public-domain imports) | ✅ done | validates + audible (themes assembled #92, fallback realization #91); metrics score all entries |
| Conformance metrics harness | ✅ done | #72 landed (154e10e); residual coverage #90 closed — motif recall (incl. rhythm-grid), structure fidelity, tempo-shape conformance, harmonic fidelity |
| CI (Netlify build gate) | ✅ done | #42 closed: `netlify.toml` command runs `npm test` + `npm run test:explorer` before the dev-- build; failing tests block publish (gate verified both directions). `.github/workflows/ci.yml` retained in-tree; account billing lock still blocks Actions, swap back if cleared |

## Update rule

When a task changes any row (tool lands, gap opens, status flips), update the
table in the same commit that closes the task. The sweep rule in
TASK_WORKFLOW.md references this file; stale status is a process failure,
same class as a stale build section in AGENTS.md.
