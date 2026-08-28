"""Claim-staleness validator (TASK_WORKFLOW §Claiming).

A claim is STALE when the newest claim comment is older than 1 hour vs.
current UTC with no activity since (no commits, no new comments). This
runs the check physically: it lists status:claimed issues, reads each
newest claim comment's UTC timestamp, computes now-utc minus that time,
and prints fresh/STALE with the age. It does not return "fresh" on sight
alone — the delta must be printed so the verdict is auditable.
"""

import datetime
import json
import subprocess

REPO = "allenpd728/muse"


def _gh_json(*args):
    out = subprocess.run(["gh"] + list(args), capture_output=True,
                         text=True).stdout
    return json.loads(out)


def _parse_utc(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def check():
    claimed = _gh_json("issue", "list", "--repo", REPO, "--state", "open",
                       "--label", "status:claimed",
                       "--json", "number,updatedAt")
    now = datetime.datetime.now(datetime.timezone.utc)
    print(f"now_utc: {now:%Y-%m-%dT%H:%M:%SZ}")
    print(f"{'#':>5} {'age_h':>6}  verdict   last-claim-comment")
    for issue in claimed:
        n = issue["number"]
        data = _gh_json("issue", "view", str(n), "--repo", REPO,
                        "--json", "comments")
        comments = data["comments"]
        if not comments:
            print(f"{n:>5} {'—':>6}  STALE     (no comments)")
            continue
        last = comments[-1]
        claim = _parse_utc(last["createdAt"])
        age_h = (now - claim).total_seconds() / 3600
        verdict = "STALE" if age_h > 1 else "fresh"
        snippet = (last["body"] or "").replace("\n", " ")[:60]
        print(f"{n:>5} {age_h:5.2f}h  {verdict:8s} {snippet!r}")


if __name__ == "__main__":
    check()
