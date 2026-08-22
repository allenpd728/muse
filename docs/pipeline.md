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
| 2. Import | `importer/` (MIDI/MusicXML → IR → schema) | ✅ done | Batch 2; large scores need `--max-old-space-size` |
| 3. Refine | manual JSON edit + explorer inspection | ⚠️ partial | composer tool scoped (#74); MVP chain starts at #79 |
| 4. Validate | `tools/validate.mjs`, `schema/`, semantics lint | ✅ done | Batch 1; 48 suite groups green |
| 5. Interpret | `interpreter/offline.mjs` / `expand.mjs` | ⚠️ partial | hand-authored examples render; imported corpus → 0 notes (#88) |
| 6. Play | `player/render.mjs` → WAV | ✅ done | deterministic synthesis placeholder; demo WAVs in `docs/demo/` |
| 7. Listen | — | ❌ not built | scope task #89 available |

## Supporting surfaces

| Surface | Status | Notes |
|---|---|---|
| Explorer (`dev--muse-qa-58fd708e.netlify.app`) | ✅ done | read-only browse/validate; QA preview only |
| Benchmark corpus (10 public-domain imports) | ⚠️ partial | validates; audible pending #88 |
| Conformance metrics harness | 🔄 in progress | #72 |
| CI (GitHub Actions) | 🚫 blocked | account billing lock — #42, needs human |

## Update rule

When a task changes any row (tool lands, gap opens, status flips), update the
table in the same commit that closes the task. The sweep rule in
TASK_WORKFLOW.md references this file; stale status is a process failure,
same class as a stale build section in AGENTS.md.
