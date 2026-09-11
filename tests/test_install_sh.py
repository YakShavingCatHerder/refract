#!/usr/bin/env python3
"""Source-tree tests for ./install.sh (python-only, --pip, --pipx)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"


@unittest.skipUnless(os.environ.get("REFRACT_TEST_INSTALL_SH") == "1", "set REFRACT_TEST_INSTALL_SH=1")
class InstallScriptTests(unittest.TestCase):
    def setUp(self):
        if not INSTALL_SH.is_file():
            self.skipTest("install.sh not found")
        self._tmpdir = tempfile.mkdtemp(prefix="refract-install-sh-")
        self.home = Path(self._tmpdir) / "home"
        self.home.mkdir()
        (self.home / ".local" / "bin").mkdir(parents=True)
        (self.home / ".zshrc").write_text("# test zshrc\n")
        (self.home / ".bashrc").write_text("# test bashrc\n")

        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env.pop("REFRACT_ENV", None)
        local_bin = str(self.home / ".local" / "bin")
        self.env["PATH"] = f"{local_bin}:{self.env['PATH']}"
        self.env["PYTHONUSERBASE"] = str(self.home / ".local")
        self.env["PIPX_HOME"] = str(self.home / ".local" / "pipx")
        self.env["PIPX_BIN_DIR"] = local_bin
        self.env["SHELL"] = self.env.get("SHELL") or "/bin/bash"

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _run_install(self, *args):
        result = subprocess.run(
            ["bash", str(INSTALL_SH), *args],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=str(REPO_ROOT),
            timeout=180,
        )
        if result.returncode != 0:
            self.fail(
                f"./install.sh {' '.join(args)} failed ({result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def _assert_installed(self, result):
        binary = self.home / ".local" / "bin" / "refract"
        self.assertTrue(binary.exists() or shutil.which("refract", path=self.env["PATH"]), result.stdout)
        self.assertTrue((self.home / ".refract" / "refract.json").is_file(), result.stdout)
        listed = subprocess.run(
            ["refract", "list"],
            capture_output=True,
            text=True,
            env=self.env,
            timeout=30,
        )
        self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)
        self.assertIn("No environments found", listed.stdout)

    def test_python_only(self):
        result = self._run_install()
        self.assertTrue((self.home / ".local" / "bin" / "refract").is_file(), result.stdout)
        self._assert_installed(result)

    def test_pip(self):
        if os.environ.get("REFRACT_TEST_INSTALL_METHOD", "pip") not in ("pip", "all"):
            self.skipTest("not this install method")
        result = self._run_install("--pip")
        self._assert_installed(result)

    def test_pipx(self):
        if os.environ.get("REFRACT_TEST_INSTALL_METHOD") != "pipx":
            self.skipTest("not this install method")
        if shutil.which("pipx") is None:
            self.skipTest("pipx not installed")
        result = self._run_install("--pipx")
        self._assert_installed(result)


if __name__ == "__main__":
    unittest.main()
