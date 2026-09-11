#!/usr/bin/env python3
"""CLI smoke tests against an installed `refract` executable.

These tests use a temporary HOME so they never touch the real shell rc files.
Run after installing the wheel or sdist, with `refract` on PATH.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROMPT_MARK = "# >>> refract prompt integration >>>"
WRAPPER_MARK = "# >>> refract shell wrapper >>>"
USE_PROBE = """# refract CI probe: exit the nested login shell after activation
if [ -n "${REFRACT_ENV:-}" ] && [ -n "${REFRACT_CI_USE_TEST:-}" ]; then
  printf 'REFRACT_ENV=%s\\n' "$REFRACT_ENV"
  command -v python || command -v python3
  exit 0
fi
"""


def which_refract() -> str:
    path = shutil.which("refract")
    if not path:
        raise unittest.SkipTest("refract is not on PATH")
    return path


class IsolatedHomeTest(unittest.TestCase):
    def setUp(self):
        which_refract()
        self._tmpdir = tempfile.mkdtemp(prefix="refract-test-")
        self.home = Path(self._tmpdir) / "home"
        self.home.mkdir()
        (self.home / ".local" / "bin").mkdir(parents=True)
        (self.home / ".zshrc").write_text("# test zshrc\n")
        (self.home / ".bashrc").write_text("# test bashrc\n")
        (self.home / ".bash_profile").write_text("# test bash_profile\n" + USE_PROBE)
        (self.home / ".zprofile").write_text("# test zprofile\n" + USE_PROBE)
        (self.home / ".profile").write_text("# test profile\n")

        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env.pop("REFRACT_ENV", None)
        self.env["REFRACT_CI_USE_TEST"] = "1"
        shell = os.environ.get("REFRACT_TEST_SHELL") or os.environ.get("SHELL") or "/bin/bash"
        self.env["SHELL"] = shell

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def run_refract(self, *args, check=True, timeout=60, extra_env=None):
        env = self.env.copy()
        if extra_env:
            env.update(extra_env)
        result = subprocess.run(
            ["refract", *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )
        if check and result.returncode != 0:
            self.fail(
                f"refract {' '.join(args)} failed ({result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def config(self):
        return json.loads((self.home / ".refract" / "refract.json").read_text())

    def envs_dir(self):
        return self.home / ".refract" / "envs"


class UsageTests(IsolatedHomeTest):
    def test_no_args_prints_usage(self):
        result = self.run_refract()
        self.assertIn("refract install", result.stdout)
        self.assertIn("refract init", result.stdout)

    def test_invalid_command(self):
        result = self.run_refract("not-a-command")
        self.assertIn("Invalid command", result.stdout)
        self.assertIn("refract init", result.stdout)

    def test_debug_flag(self):
        result = self.run_refract("--debug", "list")
        self.assertIn("[DEBUG]", result.stdout)
        self.assertIn(str(self.home / ".refract"), result.stdout)


class InstallTests(IsolatedHomeTest):
    def test_install_creates_config_and_snippets(self):
        result = self.run_refract("install")
        self.assertIn("Shell integration is ready", result.stdout)

        config_path = self.home / ".refract" / "refract.json"
        self.assertTrue(config_path.is_file())
        config = self.config()
        self.assertEqual(config["colorway"]["background"], "green")
        self.assertEqual(config["colorway"]["text"], "black")
        self.assertTrue((self.home / ".refract" / "envs").is_dir())

        zshrc = (self.home / ".zshrc").read_text()
        bashrc = (self.home / ".bashrc").read_text()
        for contents in (zshrc, bashrc):
            self.assertEqual(contents.count(PROMPT_MARK), 1)
            self.assertEqual(contents.count(WRAPPER_MARK), 1)
            self.assertIn("[refract:$REFRACT_ENV]", contents)

    def test_install_is_idempotent(self):
        self.run_refract("install")
        self.run_refract("install")
        zshrc = (self.home / ".zshrc").read_text()
        bashrc = (self.home / ".bashrc").read_text()
        self.assertEqual(zshrc.count(PROMPT_MARK), 1)
        self.assertEqual(bashrc.count(PROMPT_MARK), 1)
        self.assertEqual(zshrc.count(WRAPPER_MARK), 1)
        self.assertEqual(bashrc.count(WRAPPER_MARK), 1)


class EnvLifecycleTests(IsolatedHomeTest):
    def test_list_when_empty(self):
        result = self.run_refract("list")
        self.assertIn("No environments found", result.stdout)

    def test_init_list_current_rm(self):
        created = self.run_refract("init", "ci_env")
        env_path = self.envs_dir() / "ci_env"
        self.assertTrue((env_path / "bin" / "activate").is_file(), created.stdout)
        self.assertTrue((env_path / "bin" / "python").exists() or (env_path / "bin" / "python3").exists())

        listed = self.run_refract("list")
        self.assertIn("ci_env", listed.stdout)

        current = self.run_refract("current")
        self.assertIn("No refract environment currently active", current.stdout)

        active = self.run_refract("current", extra_env={"REFRACT_ENV": "ci_env"})
        self.assertIn("ci_env", active.stdout)

        removed = self.run_refract("rm", "ci_env")
        self.assertIn("Removed environment", removed.stdout)
        self.assertFalse(env_path.exists())

    def test_init_rejects_invalid_name(self):
        result = self.run_refract("init", "my-project", check=False)
        self.assertIn("valid identifier", result.stdout)
        self.assertFalse((self.envs_dir() / "my-project").exists())

    def test_init_rejects_duplicate(self):
        self.run_refract("init", "dupenv")
        result = self.run_refract("init", "dupenv", check=False)
        self.assertIn("already exists", result.stdout)

    def test_rm_missing(self):
        result = self.run_refract("rm", "nope", check=False)
        self.assertIn("not found", result.stdout)

    def test_use_missing(self):
        result = self.run_refract("use", "nope", check=False)
        self.assertIn("does not exist", result.stdout)

    def test_use_activates_and_returns(self):
        self.run_refract("init", "use_env")
        result = self.run_refract("use", "use_env", timeout=30)
        self.assertIn("Switching to environment 'use_env'", result.stdout)
        self.assertIn("REFRACT_ENV=use_env", result.stdout)
        python_path = None
        for line in result.stdout.splitlines():
            if "python" in line and "use_env" in line:
                python_path = line.strip()
        self.assertIsNotNone(python_path, result.stdout)
        self.assertIn(str(self.envs_dir() / "use_env"), python_path)


class ColorwayTests(IsolatedHomeTest):
    def test_colorway_updates_config_and_snippets(self):
        self.run_refract("install")
        result = self.run_refract("colorway", "cyan/white")
        self.assertIn("cyan", result.stdout)
        self.assertIn("white", result.stdout)
        config = self.config()
        self.assertEqual(config["colorway"]["background"], "cyan")
        self.assertEqual(config["colorway"]["text"], "white")
        zshrc = (self.home / ".zshrc").read_text()
        self.assertIn("cyan", zshrc)
        self.assertIn("white", zshrc)

    def test_colorway_rejects_invalid(self):
        result = self.run_refract("colorway", "octarine/black", check=False)
        self.assertIn("Invalid color", result.stdout)
        config_path = self.home / ".refract" / "refract.json"
        if config_path.exists():
            self.assertNotEqual(self.config()["colorway"]["background"], "octarine")

    def test_colorway_usage(self):
        result = self.run_refract("colorway", "green", check=False)
        self.assertIn("Usage: refract colorway", result.stdout)


if __name__ == "__main__":
    unittest.main()
