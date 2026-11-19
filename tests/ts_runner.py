"""Runs a pure TypeScript module of the web app (no imports) with node's type stripping, for tests that hold the
browser's rules to the server's (tests/test_scan_quality.py, test_analysis_grid.py, test_rune_proposal.py)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_ts(module: str, body: str) -> object:
    """Imports web/src/lib/<module>.ts as M, runs body (JavaScript that ends by printing JSON with console.log) and
    returns the parsed output. Skips when node is missing."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node saknas")
    path = os.path.join(ROOT, "web", "src", "lib", module + ".ts")
    with tempfile.TemporaryDirectory() as tmp:
        driver = os.path.join(tmp, "driver.mjs")
        with open(driver, "w", encoding="utf-8") as fh:
            fh.write(f"import * as M from {json.dumps('file://' + path)};\n{body}\n")
        out = subprocess.run([node, "--experimental-strip-types", "--no-warnings", driver], capture_output=True,
                             text=True, timeout=60, cwd=tmp)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)
