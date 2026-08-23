"""muse-pack CLI: pack/unpack corpus files and verify the W4 diff gate.

    python3 tools/muse_pack/cli.py pack <corpus-file> [-o payload.bin]
    python3 tools/muse_pack/cli.py roundtrip <corpus-file>
    python3 tools/muse_pack/cli.py --self-test          # full corpus sweep

Exit 0 ok; 1 diff-gate failure. Never in the container path (S5 owns it).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "corpus_loader"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "muse_diff"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

import muse_corpus  # noqa: E402
from muse_diff.diff import diff  # noqa: E402
from muse_ir.model import Maps, Meta, Note, Part, Work  # noqa: E402

from muse_pack.pack import pack, unpack  # noqa: E402
from muse_pack.rebuild import unpack_to_canonical  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _work_from_unpacked(payload):
    parts = [
        Part(
            id=p["id"],
            name=p["name"],
            notes=[
                Note(
                    pitch=n["pitch"],
                    onset=n["onset"],
                    duration=n["duration"],
                    voice=n["voice"],
                    velocity=n["velocity"],
                    notations=frozenset(n["notations"]),
                )
                for n in p["notes"]
            ],
        )
        for p in payload["parts"]
    ]
    return Work(
        parts=parts,
        maps=Maps(),
        meta=Meta(
            source_format=payload["meta"]["source_format"],
            ppq=payload["meta"]["ppq"],
        ),
    )


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def cmd_pack(args):
    work = muse_corpus.load_file(_resolve(args.corpus_file))
    t0 = time.time()
    payload = pack(work)
    out = args.output or args.corpus_file + ".mupack"
    with open(out, "wb") as fh:
        fh.write(payload)
    src = os.path.getsize(_resolve(args.corpus_file))
    print(
        f"packed {args.corpus_file}: {src} → {len(payload)} bytes "
        f"({len(payload) * 100 / src:.1f}%, {time.time() - t0:.2f}s) → {out}"
    )
    return 0


def cmd_roundtrip(args):
    work = muse_corpus.load_file(_resolve(args.corpus_file))
    restored = _work_from_unpacked(unpack_to_canonical(unpack(pack(work))))
    report = diff(work, restored)
    ok = report.ok()
    print(
        f"{args.corpus_file}: recall={report.recall:.4f} "
        f"precision={report.precision:.4f} matched={report.matched}/"
        f"{report.total_a} {'OK' if ok else 'FAIL'}"
    )
    return 0 if ok else 1


def cmd_self_test(_args):
    failures = 0
    total_src = total_packed = 0
    for work_id, title, relpath, _pins in muse_corpus.iter_files():
        work = muse_corpus.load_file(os.path.join(REPO, "corpus", relpath))
        payload = pack(work)
        restored = _work_from_unpacked(unpack_to_canonical(unpack(payload)))
        report = diff(work, restored)
        ok = report.ok()
        failures += 0 if ok else 1
        src = os.path.getsize(os.path.join(REPO, "corpus", relpath))
        total_src += src
        total_packed += len(payload)
        print(
            f"{'OK ' if ok else 'FAIL'} {relpath}: "
            f"{src} → {len(payload)} ({len(payload) * 100 / src:.1f}%)"
        )
    print(
        f"\nTOTAL: {total_src} → {total_packed} "
        f"({total_packed * 100 / total_src:.1f}%)"
    )
    return failures


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-pack", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_pack = sub.add_parser("pack", help="pack a corpus file")
    p_pack.add_argument("corpus_file")
    p_pack.add_argument("-o", "--output")
    p_rt = sub.add_parser("roundtrip", help="verify W4 diff on one file")
    p_rt.add_argument("corpus_file")
    sub.add_parser("--self-test", help="full corpus sweep")
    args = ap.parse_args(argv)
    return {
        "pack": cmd_pack,
        "roundtrip": cmd_roundtrip,
        "--self-test": cmd_self_test,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
