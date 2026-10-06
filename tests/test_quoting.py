#!/usr/bin/env python3
"""Execute generated actions through an attached synthetic tmux client."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import unittest
import test_launcher as launcher


class QuotingTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until
    def setUp(self):
        launcher.LauncherTests.setUp(self)
        self.tmux("respawn-pane", "-k", "-c", str(self.home),
                  "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        self.checkout = self.base / r"plugin with spaces and ' apostrophe\; $(touch injected)"
        shutil.copytree(Path(__file__).resolve().parents[1], self.checkout, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def run_script(self, name, *args, input=None, check=True, env=None):
        return subprocess.run([str(self.checkout / name), *args], input=input, text=True,
                              capture_output=True, env=env or self.env, cwd=self.home,
                              timeout=12, check=check)

    def fixture(self):
        marker = self.home / "called"
        tool = self.checkout / "scripts/tools/fixture with ' quote; $.sh"
        tool.write_text("#!/bin/bash\nprintf called > " + shlex.quote(str(marker)) + "\n")
        tool.chmod(0o755)
        registry = self.home / "local with spaces and ' apostrophe; $.tsv"
        registry.write_text("yazi\tY\tr\tquote ' \" $HOME; $(touch injected)\t70%\t70%\t" + str(tool.relative_to(self.checkout)) + "\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        return marker

    def test_quoted_direct_menu_window_popup_actions(self):
        marker = self.fixture()
        client = self.attach()
        for mode in ["window", "popup"]:
            for source in ["direct", "menu"]:
                with self.subTest(mode=mode, source=source):
                    self.tmux("set-option", "-g", "@tmux-popups-yazi-mode", mode)
                    self.load()
                    if source == "direct":
                        os.write(client, b"\x02Y")
                    else:
                        self.terminal_output.clear()
                        os.write(client, b"\x02\r")
                        self.wait_until(lambda: b"Quick Menu" in self.terminal_output)
                        os.write(client, b"r")
                    self.wait_until(marker.exists)
                    marker.unlink()
        self.assertFalse((self.home / "injected").exists())

    def test_quoted_reload_and_configurable_menu_command(self):
        working = self.home / r"pane with spaces and ' quote\; $(touch pane-injected)"
        working.mkdir()
        self.tmux("respawn-pane", "-k", "-c", str(working),
                  "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        config = self.home / "config with ' \" $HOME; quote.conf"
        config.write_text("set-option -g @fixture-reloaded yes\n")
        marker = self.home / "editor marker ' quote"
        command = "pwd > " + shlex.quote(str(marker))
        self.tmux("set-option", "-g", "@tmux-popups-config-file", str(config))
        self.tmux("set-option", "-g", "@tmux-popups-enable-vscode", "on")
        self.tmux("set-option", "-g", "@tmux-popups-vscode-command", command)
        self.load()
        client = self.attach()
        os.write(client, b"\x02R")
        self.wait_until(lambda: self.tmux("show-option", "-gqv", "@fixture-reloaded").stdout.strip() == "yes")
        self.tmux("set-option", "-gu", "@fixture-reloaded")
        self.terminal_output.clear()
        os.write(client, b"\x02\r")
        self.wait_until(lambda: b"Quick Menu" in self.terminal_output)
        os.write(client, b"R")
        self.wait_until(lambda: self.tmux("show-option", "-gqv", "@fixture-reloaded").stdout.strip() == "yes")
        self.terminal_output.clear()
        os.write(client, b"\x02\r")
        self.wait_until(lambda: b"Quick Menu" in self.terminal_output)
        os.write(client, b"v")
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text().strip(), str(working))
        self.assertFalse((working / "pane-injected").exists())

    def test_tmux_format_data_is_rejected(self):
        registry = self.home / "format.tsv"
        registry.write_text("fixture\tX\tx\t#(touch injected)\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported tmux format", result.stderr)
        registry.write_text("fixture\tX\tx\ttitle\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-config-file", "#{session_name}.conf")
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("config path", result.stderr)
        self.tmux("set-option", "-gu", "@tmux-popups-config-file")
        destination = self.base / "plugin #{session_name}"
        self.checkout.rename(destination)
        self.checkout = destination
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plugin path", result.stderr)
        self.assertFalse((self.home / "injected").exists())

    def test_unsupported_id_is_rejected_as_data(self):
        registry = self.home / "bad.tsv"
        registry.write_text("bad;touch injected\tX\tx\ttitle\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported popup id", result.stderr)
        self.assertFalse((self.home / "injected").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
