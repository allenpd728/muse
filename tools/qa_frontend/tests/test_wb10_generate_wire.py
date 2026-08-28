"""W-B10 mockup-generate wire (issue #294; spec tests/closed_*_wb10).

Source-scan tier per the B1/boardroom convention — the pane's mockup-
generate flow (seed select, assemble-prompt, generate, paste-stdin) plus
the runner/server/config registration of the generate commands.
"""

import json
import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PAGE = os.path.join(REPO, "docs", "workbench", "terminal.html")
RUNNER_CFG = os.path.join(REPO, "workbench.config.json")
RUNNER_PY = os.path.join(REPO, "tools", "muse_workbench_runner", "runner.py")


def _html():
    with open(PAGE) as fh:
        return fh.read()


def test_generate_flow_elements_present():
    html = _html()
    for el in ("gen-prompt", "gen-run", "gen-paste", "seed-path"):
        assert f'id="{el}"' in html, f"missing #{el}"


def test_generate_commands_in_allowlist():
    cfg = json.load(open(RUNNER_CFG))
    assert "muse_generate.prompt" in cfg["allowlist"]
    assert "muse_generate.mockup" in cfg["allowlist"]


def test_generate_commands_in_runner():
    src = open(RUNNER_PY).read()
    assert '"muse_generate.prompt"' in src
    assert '"muse_generate.mockup"' in src
    assert "stdin_data" in src, "runner must accept the chat-transport paste"
    assert "env_prefix" in src, "founder-gated live flag rides per-command"


def test_pane_wires_stdin_for_paste():
    html = _html()
    assert "stdin" in html, "pane must pipe the paste as stdin"
    assert "gen-paste" in html
    assert "MUSE_L1_LIVE" in html, "the live flag is founder-gated per command"
