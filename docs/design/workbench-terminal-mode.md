# Workbench terminal mode + pipeline GUI

**Follow-up to #228 (workbench-design.md). Status: draft.**

## What it actually means

The founder's correct framing: a webpage can't speak SSH, but it *can* host a
terminal component that proxies keystrokes to a local shell (such as
openvscode-server's integrated terminal here, or a tmux session), and that
shell runs the agent CLI or the repo commands. This doc specifies the
"terminal mode + GUI" shape that is the resolution of that discussion — a
real pipeline workflow GUI on top of a proper terminal path, not an
ssh-in-html gimmick.

## One wire mechanism, four surfaces

A single `terminal component` (xterm-style) embedded in the page proxies
keystrokes via WebSocket to a local session (ssh → sandbox → tmux → the
OpenHands CLI or the repo commands). Four surfaces therefore coexist:

| Surface | Purpose | Wire |
|---|---|---|
| **Tree panel** | all 5 works / 13 file-ids, seeded markers | static data |
| **Pipeline drawer** | buttons for each pipeline stage | runs CLI via prompt |
| **Prompt mode** | free-form input to the same runner, with `--help` | text routing |
| **Chat pane** | agent threaded into the loop | `curl` against Agent Canvas API |

## Pipeline drawer (the "GUI" the user asked for)

Button, not command-line. All commands are namespaced over one runner and
one allow-list; `--help` within each item is the helper:

```
data    → muse_chain round-trip      (corpus → IR → pack → container → decode)
analyze → muse_analyze --all + viz   (pattern detector + piano-roll)
author  → muse_seed create / validate / propose_seed
mockup  → muse_mockup → muse_play    (L1 generator + P2 soundfont)
iterate → muse_grow                  (L1→L4→compare)
probe   → muse_probes run            (W-B1 seven probes + W-B2 quality checks)
qa      → tools/run_tests.sh fast    (unified test runner)
diff    → muse_diff                  (W4 recall/precision compare)
```

Failing command → highlighted with an explanatory toast (exit code +
what assertion failed). No free shell; same allow-list as the prompt mode.

## Chat pane (the "into thing" the user asked for)

A small pane wired to Agent Canvas API: read-only assistant context,
push a message into the current conversation. The only dynamic credential
is `SESSION_API_KEY` or equivalent loaded from the versioned path.
Purpose: seed-iteration loop commentary: "v32 → tempo_curve_shape regressed"
without alt-tabbing to the raw chat window. Read mostly, embed optional.

## Terminal mode is cosmetic, not a vault

If the sandbox is already running openvscode-server (as here), "terminal mode"
is a redirect of the same wire protocol; the pane wires to a tmux session
(NOT into sshd), not the page holding the key. The page never owns credentials.

## Configuration gate (amends workbench-design.md)

`workbench.config.json` adds:

```json
"terminal": {
  "enabled": true,
  "mode": "embedded",
  "session": "tmux",
  "attach_chat": true,
  "pane_target": "openhands"
}
```

Missing/malformed → embedded terminal hidden + warning toast.

## Module split (updates from #228)

| Module | Own |
|---|---|
| `tools/muse_workbench_runner` | allow-list exec + config parser |
| `docs/workbench/index.html` | tree, drawer, prompt, terminal, chat panes |
| `docs/workbench/data/works.json` | corpus index |
| `tools/qa_frontend/tests/test_workbench_dom.py` | tree + button labels |
| `tools/qa_frontend/tests/test_workbench_interactions.py` | drawer + prompt + terminal |
| new `test_workbench_terminal.py` | terminal proxy + chat pane contract |

## Open questions (before implementation)

- Which of the four surfaces has precedence: drawer (declarative) or prompt
  (imperative)? Decision: drawer is default; prompt for power users.
- Chat pane: full conversation mirror, or embedded only (send-only)?
  Proposed embedded-only to avoid a scrape surface.
