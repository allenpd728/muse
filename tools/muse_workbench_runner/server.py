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

from .runner import REPO_ROOT, Runner

DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def make_handler(runner: Runner, docs_dir=None):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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
            with open(target, "rb") as fh:
                body = fh.read()
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
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/commands":
                self._json({"commands": runner.available, "error": runner.error})
            elif self.path.startswith("/api/"):
                self._json({"error": "not found"}, 404)
            else:
                self._static()

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


def serve(port=0, config_path=None, docs_dir=None):
    """Start server; returns (server, url). port=0 picks ephemeral.

    Pass ``docs_dir`` (or ``serve_docs=True`` via the CLI) to serve the
    static workbench tree and the API from one origin (#305).
    """
    runner = Runner(config_path)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(runner, docs_dir))
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
    args = ap.parse_args()

    srv, url = serve(args.port, args.config, args.docs_dir or (DOCS_DIR if args.docs else None))
    print(f"workbench runner on {url} (Ctrl-C to stop)")
    if args.docs_dir or args.docs:
        print(f"  static: {url}/workbench/terminal.html")
        print(f"  api:    {url}/api/commands")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
