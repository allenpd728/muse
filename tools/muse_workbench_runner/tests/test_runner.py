"""W-B5 runner tests: allow-list enforcement, fail-closed config, exec."""

import json
import sys
import urllib.request
import urllib.error
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from muse_workbench_runner.runner import Runner, COMMANDS, REPO_ROOT
from muse_workbench_runner.server import serve

ROOT = REPO_ROOT


def cfg(tmp_path, **over):
    base = {
        "runner": "tools/muse_workbench_runner",
        "sandbox": "local",
        "allowlist": ["muse_probes.run"],
        "prompt_enabled": True,
    }
    base.update(over)
    p = tmp_path / "wb.json"
    p.write_text(json.dumps(base))
    return p


class TestConfig:
    def test_repo_config_loads(self):
        r = Runner()
        assert r.error is None
        assert "muse_seed.validate" in r.available

    def test_missing_config_fails_closed(self, tmp_path):
        r = Runner(tmp_path / "nope.json")
        assert r.error is not None
        assert r.available == []
        assert r.run("muse_probes.run")["ok"] is False

    def test_empty_allowlist_fails_closed(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=[]))
        assert r.error is not None

    def test_unknown_command_in_allowlist_rejected(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=["rm -rf /"]))
        assert r.error is not None

    def test_malformed_json_fails_closed(self, tmp_path):
        p = tmp_path / "wb.json"
        p.write_text("{ not json")
        r = Runner(p)
        assert r.error is not None


class TestRun:
    def test_unknown_command_405(self, tmp_path):
        r = Runner(cfg(tmp_path))
        res = r.run("shell")
        assert res["rc"] == 405
        assert res["ok"] is False

    def test_disallowed_command_405(self, tmp_path):
        r = Runner(cfg(tmp_path))  # allowlist only has probes
        res = r.run("muse_play.render")
        assert res["rc"] == 405

    def test_exec_captures_output(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=["muse_probes.run"]))
        res = r.run("muse_probes.run", ["--help"])
        assert res["argv"][0] == "python3"
        assert res["stdout"] or res["stderr"]
        assert res["rc"] in (0, 1, 2)


class TestServer:
    @pytest.fixture
    def server(self, tmp_path):
        srv, url = serve(config_path=cfg(tmp_path))
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield url
        srv.shutdown()

    def get(self, url, path):
        return json.loads(urllib.request.urlopen(url + path).read())

    def post(self, url, path, payload):
        req = urllib.request.Request(
            url + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_commands_endpoint(self, server):
        out = self.get(server, "/api/commands")
        assert out["error"] is None
        assert out["commands"] == ["muse_probes.run"]

    def test_run_unknown_405(self, server):
        code, out = self.post(server, "/api/run", {"name": "shell", "args": []})
        assert code == 405
        assert out["ok"] is False

    def test_run_allowed(self, server):
        code, out = self.post(server, "/api/run", {"name": "muse_probes.run", "args": ["--help"]})
        assert code in (200, 500)
        assert "argv" in out

    def test_run_bad_args_400(self, server):
        code, out = self.post(server, "/api/run", {"name": "muse_probes.run", "args": "not-a-list"})
        assert code == 400

    def test_404_other_paths(self, server):
        with pytest.raises(urllib.error.HTTPError) as e:
            self.get(server, "/api/secret")
        assert e.value.code == 404


def test_all_commands_map_to_repo_tools():
    for name, argv in COMMANDS.items():
        assert argv[0] in ("python3", "bash")
        tool = argv[1]
        assert (ROOT / tool).exists(), f"{name}: {tool} missing"


class TestSameOriginStaticServing:
    """Issue #305: the server can serve docs/ and /api from one origin."""

    @pytest.fixture
    def docs_server(self):
        srv, url = serve(0, None, ROOT / "docs")
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield url
        srv.shutdown()

    def test_static_page_served(self, docs_server):
        with urllib.request.urlopen(docs_server + "/workbench/terminal.html") as r:
            assert r.status == 200
            assert b"<html" in r.read().lower()

    def test_api_and_static_share_the_origin(self, docs_server):
        for path in ("/api/commands", "/workbench/terminal.html", "/index.html"):
            with urllib.request.urlopen(docs_server + path) as r:
                assert r.status == 200, path

    def test_directory_path_serves_index(self, docs_server):
        with urllib.request.urlopen(docs_server + "/explorer/") as r:
            assert r.status == 200
            assert b"html" in r.read().lower()

    def test_api_paths_are_not_shadowed_by_static(self, docs_server):
        """ /api/<unknown> must 404 as JSON machinery, never fall through to
        the static tree."""
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(docs_server + "/api/secret")
        assert e.value.code == 404

    def test_path_traversal_blocked(self, docs_server):
        """Must not escape docs/ (AGENTS.md lives one level up)."""
        for probe in ("/../AGENTS.md", "/../../etc/passwd", "/..%2fAGENTS.md"):
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(docs_server + probe)
            assert e.value.code == 404, probe

    def test_static_serving_off_by_default(self, tmp_path):
        """Without docs_dir the server is API-only — the previous behavior."""
        srv, url = serve(0, None, None)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(url + "/workbench/terminal.html")
            assert e.value.code == 404
            with urllib.request.urlopen(url + "/api/commands") as r:
                assert r.status == 200
        finally:
            srv.shutdown()

    def test_json_content_type_on_api(self, docs_server):
        with urllib.request.urlopen(docs_server + "/api/commands") as r:
            assert r.headers["Content-Type"] == "application/json"
