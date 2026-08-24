# Rendered audio (QA session artifacts)

WAV files rendered by `tools/muse_play` (P2 reference renderer) for the
QA/explorer/workbench surfaces.

## Convention

- **Generated, not committed.** Audio is rendered on demand by the serving
  session and gitignored (`docs/audio/*.wav`). Nothing here is source of
  truth — the renderer reproduces any file deterministically from the
  corpus.
- **Served by the session server.** When an agent spins up the QA server
  (`cd docs && python3 -m http.server 12000`), rendered audio is reachable
  at `/audio/<work>.wav` for the life of that session. The sandbox is the
  host; there is no persistent audio store.
- **Regenerate on demand.** Any missing file is one command away:

  ```bash
  python3 -c "
  import sys; sys.path.insert(0, 'tools/ir'); sys.path.insert(0, 'tools')
  from muse_play.play import render_work
  from muse_ir import load
  render_work(load('corpus/bach/bwv227.1.mxl'), 'docs/audio/bwv227.1.wav')
  "
  ```

- **Committed audio is the exception.** The spike listener
  (`docs/spike/*.wav`) predates this convention and is committed because
  those files are part of the spike's evidence record. New rendered audio
  stays session-local.

## Why not commit rendered audio

Renderer output is a deterministic function of the corpus; committing it
duplicates bytes the renderer reproduces exactly. The workbench/explorer
pages link to `/audio/<work>.wav` and degrade gracefully when the file
isn't rendered yet (the audio element simply doesn't load).
