"""CLI modes work without an existing tmux server."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class NoServerModeTests(unittest.TestCase):
    def test_legacy_defaults_and_foreground_command_without_server(self):
        with tempfile.TemporaryDirectory(prefix="tmux-mode-cli-") as directory:
            home = Path(directory)
            root = home / "plugin"
            shutil.copytree(Path(__file__).resolve().parents[1], root,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            adapter = root / "scripts/tools/no-server-fixture.sh"
            adapter.write_text('#!/bin/sh\nprintf "%s\\n" "$PWD"\nexit 23\n')
            adapter.chmod(0o755)
            registry = home / "local.tsv"
            registry.write_text("fixture_cli\t-\t-\tCLI fixture\t-\t-\t"
                                "scripts/tools/no-server-fixture.sh\tcommand\tforeground\n")
            env = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory,
                       TMUX_TMPDIR=directory, TMPDIR=directory,
                       TMUX_POPUPS_LOCAL_REGISTRY=str(registry))
            for key in ["TMUX", "TMUX_PANE", "TMUX_POPUPS_DIRECTORY"]:
                env.pop(key, None)
            rows = subprocess.run([str(root / "scripts/list-popups.sh"), "--tsv"],
                                  env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(rows.returncode, 0, rows.stderr)
            self.assertIn("scripts/tools/yazi.sh\twindow\tforeground", rows.stdout)
            result = subprocess.run([str(root / "scripts/run-popup.sh"), "fixture_cli"],
                                    cwd=home, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual(result.stdout, directory + "\n")
            self.assertEqual(list(home.glob("tmux-popups-cli.*")), [])
