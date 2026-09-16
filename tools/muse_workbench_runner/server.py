"""Thin http.server fork exposing the runner over localhost.

Endpoints:
  GET  /api/commands   -> {"commands": [...], "error": null|str}
  POST /api/run        -> {"name": str, "args": [..]} -> runner result JSON

Binds 127.0.0.1 only; the workbench page talks to this.

Optionally serves the static `docs/` tree on the **same origin** (issue
#305): the workbench terminal page previously hardcoded
`http://127.0.0.1:9145`, which from a proxied/hosted browser resolves to the
visitor's own machine — nothing listening — so the pane 404'd. One origin
removes the problem and keeps the localhost-only posture: the API is reached
at an origin-relative `/api/...` path, so whatever host serves the page also
serves the runner.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Dual-mode import: this file is both a package module (imported by tests and
# by `python3 -m muse_workbench_runner.server`) and a script (the
# `python3 tools/muse_workbench_runner/server.py` invocation the README
# documents). A bare relative import breaks the script case — which had gone
# unnoticed until a #316 test ran the CLI. Add the package parent to the path
# for the script case instead.
if __package__ in (None, ""):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from muse_workbench_runner.runner import REPO_ROOT, Runner
else:
    from .runner import REPO_ROOT, Runner

DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def make_handler(runner: Runner, docs_dir=None, allow_origins=()):
    """Handler factory.

    ``allow_origins`` is the cross-origin opt-in (issue #316). Empty (the
    default) means no CORS headers at all, so a browser on another origin
    cannot read this server's responses. Each entry is matched **exactly**
    against the request's ``Origin`` header; a wildcard is never emitted,
    and the server warns at startup when the list is non-empty.

    This is deliberately not a default: the server executes allow-listed
    commands, so any origin granted access can drive them from a page the
    user merely visits.
    """
    allowed = tuple(o.rstrip("/") for o in allow_origins)

    class Handler(BaseHTTPRequestHandler):
        # Reject any inherited HTTP version pitfalls; explicit and local.
        server_version = "muse-workbench-runner/1"

        def _origin(self):
            """The request Origin, if and only if it is explicitly allowed."""
            origin = (self.headers.get("Origin") or "").rstrip("/")
            if origin and origin in allowed:
                return origin
            return None

        def _cors(self, origin):
            """Emit CORS headers for an allowed origin. Always Vary, so a
            cache never serves one origin's response to another."""
            self.send_header("Vary", "Origin")
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors(self._origin())
            self.end_headers()
            self.wfile.write(body)

        # Static responses are streamed in chunks rather than read whole: the
        # spike listener ships multi-MB WAVs (the largest is ~11MB), and
        # ThreadingHTTPServer serves concurrent requests, so buffering each
        # file entirely would multiply memory by the number of live requests.
        CHUNK = 64 * 1024

        def _static(self):
            """Serve the docs/ tree, or 404 when static serving is off."""
            if not docs_dir:
                self._json({"error": "not found"}, 404)
                return
            rel = self.path.split("?", 1)[0].lstrip("/")
            if rel.endswith("/") or rel == "":
                rel += "index.html"
            target = os.path.normpath(os.path.join(docs_dir, rel))
            # Path traversal guard: stay inside docs_dir.
            if not target.startswith(os.path.abspath(docs_dir) + os.sep) or not os.path.isfile(target):
                self._json({"error": "not found"}, 404)
                return
            ctype = {
                ".html": "text/html; charset=utf-8",
                ".json": "application/json",
                ".js": "text/javascript",
                ".css": "text/css",
                ".wav": "audio/wav",
                ".png": "image/png",
                ".svg": "image/svg+xml",
                ".md": "text/markdown; charset=utf-8",
            }.get(os.path.splitext(target)[1], "application/octet-stream")
            try:
                size = os.path.getsize(target)
                with open(target, "rb") as fh:
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(size))
                    self._cors(self._origin())
                    self.end_headers()
                    while True:
                        chunk = fh.read(self.CHUNK)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                # The client navigated away mid-download; not an error worth
                # a stack trace, and the handler must not die.
                pass

        def do_GET(self):
            if self.path == "/api/commands":
                self._json({"commands": runner.available, "error": runner.error})
            elif self.path.startswith("/api/"):
                self._json({"error": "not found"}, 404)
            else:
                self._static()

        def do_OPTIONS(self):
            """CORS preflight for the JSON POST (issue #316).

            Only answered for an allowed origin; anything else gets a bare
            403 with no CORS headers, so an unlisted page cannot even learn
            whether the endpoint exists."""
            origin = self._origin()
            if not origin:
                self.send_response(403)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self._cors(origin)
            self.end_headers()

        def do_POST(self):
            if self.path != "/api/run":
                self._json({"error": "not found"}, 404)
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n))
                name = payload.get("name", "")
                args = payload.get("args", [])
                env = payload.get("env", "")
                stdin_data = payload.get("stdin", None)
                if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
                    self._json({"error": "args must be list[str]"}, 400)
                    return
                if not isinstance(env, str):
                    self._json({"error": "env must be a string"}, 400)
                    return
            except (ValueError, json.JSONDecodeError):
                self._json({"error": "bad request"}, 400)
                return
            result = runner.run(name, args, env_prefix=env, stdin_data=stdin_data)
            code = 200 if result.get("ok") else (405 if result.get("rc") == 405 else 500)
            self._json(result, code)

        def log_message(self, *a):
            pass

    return Handler


def serve(port=0, config_path=None, docs_dir=None, allow_origins=()):
    """Start server; returns (server, url). port=0 picks ephemeral.

    Pass ``docs_dir`` (or ``--docs`` via the CLI) to serve the static
    workbench tree and the API from one origin (#305).

    Pass ``allow_origins`` (or ``--allow-origin``, repeatable) to permit
    cross-origin reads from those exact origins (#316). Default is none: the
    overrides in the page then only work same-origin.
    """
    runner = Runner(config_path)
    srv = ThreadingHTTPServer(
        ("127.0.0.1", port),
        make_handler(runner, docs_dir, allow_origins),
    )
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(prog="muse-workbench-runner", description=__doc__)
    ap.add_argument("--port", type=int, default=9145)
    ap.add_argument("--config", default=None)
    ap.add_argument("--docs", action="store_true",
                    help="also serve the static docs/ tree on the same origin")
    ap.add_argument("--docs-dir", default=None, help="override the docs directory")
    ap.add_argument("--allow-origin", action="append", default=[], metavar="ORIGIN",
                    help="permit cross-origin reads from this exact origin "
                         "(repeatable, e.g. --allow-origin https://host:12000). "
                         "Never a wildcard. Off by default: this server "
                         "executes commands.")
    args = ap.parse_args()

    for origin in args.allow_origin:
        if origin.strip() in ("*", "null"):
            ap.error("--allow-origin does not accept a wildcard or 'null' origin")

    srv, url = serve(args.port, args.config,
                     args.docs_dir or (DOCS_DIR if args.docs else None),
                     args.allow_origin)
    print(f"workbench runner on {url} (Ctrl-C to stop)")
    if args.docs_dir or args.docs:
        print(f"  static: {url}/workbench/terminal.html")
        print(f"  api:    {url}/api/commands")
    if args.allow_origin:
        print("  WARNING: cross-origin access enabled for: "
              + ", ".join(args.allow_origin))
        print("           this server executes allow-listed commands; only "
              "pass origins you control.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
