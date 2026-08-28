"""Thin http.server fork exposing the runner over localhost.

Endpoints:
  GET  /api/commands   -> {"commands": [...], "error": null|str}
  POST /api/run        -> {"name": str, "args": [..]} -> runner result JSON

Binds 127.0.0.1 only; the workbench page talks to this.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .runner import Runner


def make_handler(runner: Runner):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/commands":
                self._json({"commands": runner.available, "error": runner.error})
            else:
                self._json({"error": "not found"}, 404)

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


def serve(port=0, config_path=None):
    """Start server; returns (server, url). port=0 picks ephemeral."""
    runner = Runner(config_path)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(runner))
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


if __name__ == "__main__":
    srv, url = serve()
    print(f"workbench runner on {url} (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
