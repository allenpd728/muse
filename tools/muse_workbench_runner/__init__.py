"""Workbench runner (W-B5) — allow-listed command executor.

Executes only commands named in workbench.config.json's allow-list via
subprocess (shell=False, cwd=repo root). The page POSTs /run against a
thin http.server fork; the runner validates the command name and returns
stdout/stderr/exit-code JSON. Fails closed on missing/malformed config.
"""
