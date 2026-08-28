"""CI flaky-retry workflow coherence (issue #293).

The deliverable is a workflow file + docs, so coverage is mechanical
coherence:the retry workflow keeps its guarded, bounded re-run contract,
and docs/ci-retry.md + docs/pipeline.md agree. Pure text/YAML assertions —
no network, no live Actions. Match on stable keywords, not full lines.

The live trigger (workflow_run fires on real conformance failures) cannot be
pinned here: it depends on the runner issue the repo is working around. Static
parse + argument pins are the repo-side gate.
"""

import os
import re

import yaml

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
WF = os.path.join(REPO, ".github", "workflows", "retry-flaky.yml")
DOC = os.path.join(REPO, "docs", "ci-retry.md")
PIPELINE = os.path.join(REPO, "docs", "pipeline.md")


def _read(path):
    with open(path) as fh:
        return fh.read()


def _wf():
    return yaml.safe_load(_read(WF))


def test_workflow_parses_and_triggers_on_conformance_completed():
    wf = _wf()
    trig = wf["on"]["workflow_run"]
    assert trig["workflows"] == ["conformance"]
    assert trig["types"] == ["completed"]


def test_retry_runs_only_failed_jobs_with_write_actions():
    wf = _wf()
    assert wf["permissions"]["actions"] == "write"
    assert wf["permissions"]["contents"] == "read"
    step = wf["jobs"]["retry"]["steps"][0]
    script = step["run"]
    assert "--failed" in script, "retry step no longer re-runs only failed jobs"
    assert "gh run rerun" in script
    assert step["env"]["GH_TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"


def test_attempt_guard_is_the_loop_brake():
    expr = _wf()["jobs"]["retry"]["if"]
    # only the run's FIRST attempt may trigger; a retried run (attempt >1)
    # cannot re-trigger, bounding the retry loop.

    collapsed = expr.replace(" ", "")
    assert "run_attempt==1" in collapsed
    assert "conclusion=='failure'" in collapsed
    assert "event=='push'" in collapsed


def test_doc_covers_auto_trigger_and_manual_hatch():
    doc = _read(DOC)
    assert "workflow_run" in doc
    assert "run_attempt == 1" in doc
    assert "--failed" in doc
    assert "gh run rerun" in doc
    assert "24" in doc, "when-not-to-retry matrix dropped the >24h rule"
    assert re.search(r"fix the code, not the rerun", doc.lower()), "retry matrix lost its fix-the-code guidance"


def test_pipeline_tracks_retry_row():
    text = _read(PIPELINE)
    assert re.search(r"\| CI flaky retry \|.*#293", text), "pipeline lost the CI flaky retry row (#293)"