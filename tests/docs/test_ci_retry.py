"""CI flaky-retry workflow coherence (issues #293,#300.

The deliverable is a workflow file + docs, so coverage is mechanical
coherence:the retry workflow is dispatch-only one-shot(no self-triggering
topology possible)and docs/ci-retry.md + docs/pipeline.md agree. Pure text/YAML
assertions -- no network, no live Actions. Match on stable keywords, not
full lines.

The live trigger(real Actions failures) cannot be pinned here:it depends
on the runner issue the repo is working around. Static parse + argument pins
are the repo-side gate. Tests updated for the #300 redesign: the old
workflow_run trigger + the run_attempt loop-brake are gone because the
topology cannot self-trigger in the first place).
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


def test_workflow_is_dispatch_only_one_shot():
    """No workflow_run trigger -- cannot self-re-trigger; the dispatch
    input run_id is required numeric.**
    """
    wf = _wf()
    assert "workflow_run" not in wf["on"], "workflow_run trigger must be gone"
    assert "workflow_dispatch" in wf["on"]
    inputs = wf["on"]["workflow_dispatch"]["inputs"]
    assert "run_id" in inputs
    assert inputs["run_id"]["required"] is True
    assert inputs["run_id"]["type"] == "number", "run_id input must be numeric"


def test_retry_runs_only_failed_jobs_with_write_actions():
    wf = _wf()
    assert wf["permissions"]["actions"] == "write"
    assert wf["permissions"]["contents"] == "read"
    step = wf["jobs"]["retry"]["steps"][0]
    script = step["run"]
    assert "--failed" in script, "retry step re-runs only failed jobs"
    assert "gh run rerun" in script
    assert re.search(r"case .\$run_id. in", script), "numeric input guard lost"
    assert re.search(r"\[\!0-9\]", script), "numeric guard lost its pattern"
    assert step["env"]["GH_TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"


def test_no_workflow_run_guard_remains():
    """The loop-brake era is over:no run_attempt/workflow_run references
    may linger in the workflow (the topology cannot self-trigger; a guard
    would be dead weight,and a rerun'd re-emit as a new run anyway)."""
    text = _read(WF)
    assert "run_attempt" not in text
    assert "workflow_run" not in text


def test_doc_covers_manual_trigger_and_why_not_auto():
    doc = _read(DOC)
    assert "workflow_dispatch" in doc, "doc lostthe dispatch-only trigger"
    assert "gh run rerun" in doc
    assert "--failed" in doc
    assert "24" in doc, "when-not-to-retry matrix droppedthe >24h rule"
    assert re.search(r"fix the code, not the rerun", doc.lower()), "retry matrix lost its guidance"
    assert "self-trigger" in doc.lower(), "doc lostthe self-trigger-loop lesson"
    assert re.search(r"workflow_run", doc), "why-not section lost the topology explanation"
    assert "run_attempt == 1" not in doc


def test_pipeline_tracks_retry_row():
    text = _read(PIPELINE)
    assert re.search(r"\| CI flaky retry \|.*#293", text), "pipeline lostthe retry row (#293)"
    assert "#300" in text, "pipeline retry row not updated for the redesign"
