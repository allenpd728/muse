"""Mechanical doc-prose lint for the Muse repo (issue #299 / T7).

Deterministic, offline, zero API calls: the agent *is* the prose checker
(that is the checklist convention in AGENTS.md); this module is the cheap
mechanical tier that runs in the fast test suite and catches the drift a
human reviewer keeps re-finding by hand.

Four classes of finding, all derived from the repo's own conventions:

  * ``broken-link``    — a relative markdown link whose target does not exist.
  * ``unresolved-ref`` — a backticked path that names a live repo path which
                         does not resolve (placeholders, globs and abbreviated
                         dot-lists are skipped — they are prose, not claims).
  * ``stale-open-ref`` — a reference to an ``open_*`` record (test spec, bug,
                         blocker) whose file has since been renamed ``closed_``.
  * ``unfilled-template`` — a raw ``[TODO]``/``TBD`` placeholder left in a doc.

Two exclusions keep the signal honest, and both are load-bearing:

  * **Historical records are skipped.** ``tests/closed_*``, ``bugs/closed_*``,
    ``blockers/closed_*`` and ``docs/audit/*`` describe the state of the world
    *at the time they were written*. A path that has since moved is not drift
    in a record; flagging it would force agents to rewrite history.
  * **Superseded docs are skipped** (``docs/superseded.txt``): ``SCHEMA_SPEC.md``
    is explicitly "design history only", so its dead paths are intentional.

Findings are a triaged, non-blocking queue (``docs/audit/<date>-doc-prose.md``
+ a ``documentation`` issue), but the suite fails while any exist so
regressions cannot land silently. Use the CLI ``--report`` for the triage view.
"""

from __future__ import annotations

import glob
import os
import re

EXCLUDE_DIRS = (".git", "node_modules", "__pycache__", ".pytest_cache")

# Live-repo top-level directories: a backticked reference starting with one of
# these is claiming to name a real path, so it must resolve.
LIVE_ROOTS = (
    "tools/", "docs/", "corpus/", "seeds/", "tests/", "bugs/",
    "blockers/", "scripts/", ".github/",
)

# Prose, not claims: placeholders, globs, abbreviated lists.
PLACEHOLDER_RE = re.compile(r"YYYY|MM-DD|\.\.\.|<[^>]*>|\*|\?|\{|\}")
ABBREV_RE = re.compile(r"\.\.|\b\d+/\d+\b|\bv\d+/\s*v\d+\b")

# A path named *as history* is not drift: "not the earlier `tools/muse_ir/`",
# "superseded `tools/muse_pack`". Current design docs legitimately record what
# a thing used to be; flagging that would force agents to erase the reasoning.
HISTORICAL_MENTION_RE = re.compile(
    r"\b(superseded|earlier|former|previous|previously|renamed|removed|"
    r"no longer|deprecated|retired|deleted|old)\b",
    re.IGNORECASE,
)

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
OPEN_REF_RE = re.compile(r"((?:tests|bugs|blockers)/open_[0-9A-Za-z_-]+\.md)")

UNFILLED_MARKERS = ("[TODO]", "[TBD]", "TODO:", "TBD:")


def repo_root(start=None):
    """Walk up from this file to the repo root (the dir holding tools/)."""
    here = os.path.abspath(start or os.path.dirname(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(here, "tools")) and os.path.isfile(
            os.path.join(here, "AGENTS.md")
        ):
            return here
        here = os.path.dirname(here)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def read_text_checked(path):
    """Return (text, finding_or_None).

    A non-UTF-8 markdown file is itself a defect — it breaks the repo's
    tooling (editors, diffs, agents) and is invisible in review. It is
    reported as a finding rather than raised, so one bad byte cannot stop
    the whole lint (found live: docs/design/r1-rehearsal-directives.md).
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError as exc:
        return raw.decode("utf-8", errors="replace"), {
            "kind": "encoding",
            "file": None,  # filled in by the caller
            "ref": "byte %d" % exc.start,
            "detail": "file is not valid UTF-8 (0x%02x at byte %d)"
                      % (raw[exc.start], exc.start),
        }


def superseded_paths(root):
    """Doc paths deliberately exempt from the lint (design history)."""
    out = set()
    listing = os.path.join(root, "docs", "superseded.txt")
    if not os.path.isfile(listing):
        return out
    for line in read_text(listing).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(os.path.normpath(line))
    return out


def is_historical(relpath):
    """Records of past state — never linted for drift."""
    relpath = relpath.replace(os.sep, "/")
    if relpath.startswith("docs/audit/"):
        return True
    base = os.path.basename(relpath)
    top = relpath.split("/")[0]
    return base.startswith(("closed_", "open_")) and top in (
        "tests", "bugs", "blockers",
    )


def iter_markdown(root):
    for path in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True)):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if any(part in EXCLUDE_DIRS for part in rel.split("/")):
            continue
        yield rel, path


def _is_prose_ref(ref):
    """True when a backticked token is prose rather than a path claim."""
    if PLACEHOLDER_RE.search(ref) or ABBREV_RE.search(ref):
        return True
    if ref.startswith(("http://", "https://", "//", "#", "-")):
        return True
    return False


def lint_link(relpath, target, root):
    """A relative markdown link target must exist."""
    if target.startswith(("http://", "https://", "mailto:", "#", "//")):
        return None
    clean = target.split("#", 1)[0]
    if not clean:
        return None
    resolved = os.path.normpath(os.path.join(os.path.dirname(relpath), clean))
    if os.path.exists(os.path.join(root, resolved)):
        return None
    return {
        "kind": "broken-link",
        "file": relpath,
        "ref": target,
        "detail": "relative link target does not exist",
    }


def lint_backtick_path(relpath, ref, root):
    """A backticked live-repo path must resolve.

    Two shapes need care, both found in the wild while landing this tool:

    * ``tools/muse_workbench_runner/README.md`` writes a command line inside
      backticks — ``tools/muse_seed_cli/cli.py validate`` — where the token
      after the path is an *argument*, not part of the path. Only the
      leading path-shaped run is checked.
    * ``docs/design/*`` legitimately names a path that no longer exists when
      the prose is explicitly about its removal ("not the earlier
      ``tools/muse_ir/``"). Marked with a ``superseded`` note in the doc or
      listed in ``docs/superseded.txt``; a bare mention of the old path in a
      *current* design doc is still drift worth surfacing.
    """
    ref = ref.strip().rstrip("/")
    if _is_prose_ref(ref) or not ref.startswith(LIVE_ROOTS):
        return None
    # Trim a trailing command argument: keep only the longest existing prefix
    # or the leading path-shaped run when nothing exists.
    ref = _leading_path(ref)
    if os.path.exists(os.path.join(root, ref)):
        return None
    alt = os.path.normpath(os.path.join(os.path.dirname(relpath), ref))
    if os.path.exists(os.path.join(root, alt)):
        return None
    return {
        "kind": "unresolved-ref",
        "file": relpath,
        "ref": ref,
        "detail": "backticked repo path does not resolve",
    }


def _leading_path(ref):
    """Reduce ``a/b.py arg --flag`` to its path-shaped leading run."""
    parts = ref.split()
    if len(parts) == 1:
        return ref
    head = parts[0]
    # A leading run that keeps a filename/extension is the path; otherwise
    # fall back to the whole token so the finding stays honest.
    return head if "/" in head else ref


def lint_stale_open_ref(relpath, ref, root):
    """An ``open_*`` record reference whose file was renamed ``closed_``."""
    if os.path.exists(os.path.join(root, ref)):
        return None
    directory, base = os.path.split(ref)
    closed = os.path.join(directory, base.replace("open_", "closed_", 1))
    if os.path.exists(os.path.join(root, closed)):
        return {
            "kind": "stale-open-ref",
            "file": relpath,
            "ref": ref,
            "detail": "renamed to %s (record completed)" % closed,
        }
    return None


def lint_unfilled(relpath, text):
    """Template placeholders that never got filled in.

    A marker inside backticks is documentation *about* the marker ("flags
    unfilled ``[TODO]``s"), not an unfilled template — found live when this
    tool's own AGENTS.md convention was flagged.
    """
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = BACKTICK_RE.sub("", line)
        for marker in UNFILLED_MARKERS:
            if marker in stripped:
                out.append({
                    "kind": "unfilled-template",
                    "file": relpath,
                    "ref": marker,
                    "detail": "line %d: %s" % (lineno, line.strip()[:100]),
                })
    return out


def lint_file(relpath, root, superseded):
    """All findings for one markdown file.

    Findings are de-duplicated per (kind, ref): the same reference mentioned
    three times in a README is one piece of drift to fix, not three.
    """
    if is_historical(relpath) or os.path.normpath(relpath) in superseded:
        return []
    if relpath.startswith("tools/muse_docs/"):
        return []  # this tool's own docs quote the markers/patterns by design
    text, enc_finding = read_text_checked(os.path.join(root, relpath))
    findings = []
    if enc_finding:
        enc_finding["file"] = relpath
        findings.append(enc_finding)

    seen = set()

    def add(finding):
        key = (finding["kind"], finding["ref"])
        if key in seen:
            return
        seen.add(key)
        findings.append(finding)

    for m in MD_LINK_RE.finditer(text):
        f = lint_link(relpath, m.group(1), root)
        if f:
            add(f)
    for m in BACKTICK_RE.finditer(text):
        if _in_historical_context(text, m.start()):
            continue
        f = lint_backtick_path(relpath, m.group(1), root)
        if f:
            add(f)
    for m in OPEN_REF_RE.finditer(text):
        f = lint_stale_open_ref(relpath, m.group(1), root)
        if f:
            add(f)
    for f in lint_unfilled(relpath, text):
        add(f)
    return findings


def _in_historical_context(text, index):
    """True when the mention at ``index`` is prose about a past state.

    Looks at the sentence fragment preceding the reference, which is where
    qualification that a path is gone appears ("not the earlier ``X``").
    """
    start = max(text.rfind("\n\n", 0, index), text.rfind(". ", 0, index))
    window = text[start if start != -1 else 0:index]
    return bool(HISTORICAL_MENTION_RE.search(window[-120:]))


def lint_repo(root=None):
    """Every finding in the repo, sorted for stable output."""
    root = os.path.abspath(root or repo_root())
    superseded = superseded_paths(root)
    findings = []
    for relpath, _ in iter_markdown(root):
        findings.extend(lint_file(relpath, root, superseded))
    findings.sort(key=lambda f: (f["file"], f["kind"], f["ref"]))
    return findings


def summarize(findings):
    """Kind -> count, for the report header."""
    counts = {}
    for f in findings:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    return dict(sorted(counts.items()))


def format_findings(findings):
    return "\n".join(
        "%s: [%s] %s — %s" % (f["file"], f["kind"], f["ref"], f["detail"])
        for f in findings
    )