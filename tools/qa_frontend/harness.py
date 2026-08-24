"""Static-server + headless-page harness shared by the DOM tests."""

from __future__ import annotations

import functools
import http.server
import threading

from playwright.sync_api import sync_playwright


class serve_static:
    """Serve a directory over HTTP on a free port for the context's life."""

    def __init__(self, directory):
        self.directory = directory
        self.port = None
        self._server = None
        self._thread = None

    def __enter__(self):
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=self.directory
        )
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)
        return False

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"


class PageSession:
    """One headless Chromium session; captures console errors."""

    def __init__(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch()
        self.console_errors = []

    def new_page(self):
        page = self.browser.new_page()
        page.on("console", lambda msg: (
            self.console_errors.append(msg.text) if msg.type == "error" else None
        ))
        page.on("pageerror", lambda err: self.console_errors.append(str(err)))
        return page

    def close(self):
        self.browser.close()
        self._pw.stop()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
