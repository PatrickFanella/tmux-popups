#!/usr/bin/env python3
"""Launcher checks using private tmux sockets, homes and tool substitutes."""

import atexit
import os
import fcntl
from pathlib import Path
import pty
import select
import shlex
import shutil
import signal
import subprocess
import struct
import tempfile
import threading
import termios
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
REAL_TMUX = shutil.which("tmux")


class LauncherTests(unittest.TestCase):
    def owned_cleanup(self, callback):
        atexit.register(callback)
        self.addCleanup(atexit.unregister, callback)
        self.addCleanup(callback)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tmux-popups-test-")
        self.owned_cleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.socket = self.base / "tmux.sock"
        self.env = dict(os.environ)
        for key in list(self.env):
            if key == "TMUX" or key.startswith("TMUX_POPUPS_"):
                self.env.pop(key)
        self.env.update(
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.home / "config"),
            XDG_CACHE_HOME=str(self.home / "cache"),
            XDG_DATA_HOME=str(self.home / "data"),
            XDG_STATE_HOME=str(self.home / "state"),
            PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
            SHELL="/bin/bash",
            TERM="xterm-256color",
        )
        self.stub("tmux", f"exec {shlex.quote(REAL_TMUX)} -S {shlex.quote(str(self.socket))} \"$@\"")
        self.tmux("-f", "/dev/null", "new-session", "-d", "-s", "fixture", "-x", "100", "-y", "30", "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        self.owned_cleanup(lambda: self.tmux("kill-server", check=False))
        self.tmux("set-option", "-g", "@tmux-popups-enable-vscode", "off")
        self.tmux("set-option", "-g", "assume-paste-time", "0")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body + "\n")
        path.chmod(0o755)
        return path

    def run_script(self, name, *args, input=None, check=True, env=None):
        return subprocess.run(
            [str(ROOT / name), *args], input=input, text=True,
            capture_output=True, env=env or self.env, cwd=self.home,
            timeout=12, check=check,
        )

    def tmux(self, *args, check=True):
        return subprocess.run(
            [REAL_TMUX, "-S", str(self.socket), *args],
            env=self.env, text=True, capture_output=True, timeout=12, check=check,
        )

    def generated(self):
        return Path(self.env["XDG_CACHE_HOME"]) / "tmux-popups/generated.conf"

    def load(self):
        self.run_script("tmux-popups.tmux")

    def attach(self):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 100, 0, 0))
        process = subprocess.Popen(
            [REAL_TMUX, "-S", str(self.socket), "attach-session", "-t", "fixture"],
            stdin=slave, stdout=slave, stderr=slave, env=self.env,
        )
        os.close(slave)
        stopped = threading.Event()
        self.terminal_output = bytearray()

        def drain():
            while not stopped.is_set():
                try:
                    if select.select([master], [], [], 0.05)[0]:
                        chunk = os.read(master, 65536)
                        self.terminal_output.extend(chunk)
                        if not chunk:
                            break
                except OSError:
                    break

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()

        def cleanup():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            stopped.set()
            reader.join(timeout=1)
            os.close(master)

        self.owned_cleanup(cleanup)
        self.wait_until(lambda: bool(self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()))
        self.wait_until(lambda: b"fixture-ready" in self.terminal_output)
        return master

    def wait_until(self, predicate):
        end = time.monotonic() + 6
        while time.monotonic() < end:
            if predicate():
                return
            time.sleep(0.03)
        self.fail("fixture did not complete within six seconds")

    def test_registry_override_keeps_order_and_adds_local_entry(self):
        registry = self.home / "local.tsv"
        registry.write_text(
            "# fixture\n\n"
            "timer\t-\tP\tlocal timer\t60%\t60%\tscripts/tools/timer.sh\n"
            "fixture\t-\tx\tfixture\t70%\t70%\t-\n"
        )
        env = dict(self.env, TMUX_POPUPS_LOCAL_REGISTRY=str(registry))
        rows = [line.split("\t") for line in self.run_script("scripts/list-popups.sh", "--tsv", env=env).stdout.splitlines()]
        timers = [row for row in rows if row[0] == "timer"]
        self.assertEqual(len(timers), 1)
        self.assertEqual(timers[0][3], "local timer")
        self.assertEqual(rows[-1][0], "fixture")
        self.assertEqual(rows[0][0], "help")

    def test_generated_config_parses_and_loads_twice(self):
        self.load()
        before = self.tmux("list-keys", "-T", "prefix").stdout
        self.assertIn("run-popup.sh yazi", before)
        self.load()
        self.assertEqual(before, self.tmux("list-keys", "-T", "prefix").stdout)
        self.assertTrue(self.generated().is_file())

    def test_reload_binding_sources_only_fixture_config(self):
        config = self.home / "fixture.conf"
        config.write_text("set-option -g @fixture-reloaded yes\n")
        self.tmux("set-option", "-g", "@tmux-popups-config-file", str(config))
        self.load()
        client = self.attach()
        os.write(client, b"\x02R")
        self.wait_until(lambda: self.tmux("show-option", "-gqv", "@fixture-reloaded").stdout.strip() == "yes")

    def test_direct_binding_executes_yazi_substitute(self):
        marker = self.home / "yazi-called"
        self.stub("yazi", f"printf '%s' called > {shlex.quote(str(marker))}")
        self.load()
        client = self.attach()
        os.write(client, b"\x02Y")
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text(), "called")

    def test_menu_action_executes_yazi_substitute(self):
        marker = self.home / "menu-called"
        self.stub("yazi", f"printf '%s' menu > {shlex.quote(str(marker))}")
        self.load()
        client = self.attach()
        self.assertIn("display-menu", self.tmux("list-keys", "-T", "prefix").stdout)
        os.write(client, b"\x02\r")
        self.wait_until(lambda: b"Quick Menu" in self.terminal_output)
        os.write(client, b"r")
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text(), "menu")

    def test_popup_accepts_input_from_attached_terminal(self):
        marker = self.home / "input-called"
        self.stub("python3", f"printf 'fixture input: '\nIFS= read -r value\nprintf '%s' \"$value\" > {shlex.quote(str(marker))}")
        self.load()
        client = self.attach()
        os.write(client, b"\x02\r")
        self.wait_until(lambda: b"Quick Menu" in self.terminal_output)
        os.write(client, b"=")
        self.wait_until(lambda: b"fixture input:" in self.terminal_output)
        os.write(client, b"terminal fixture\r")
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text(), "terminal fixture")

    def test_unknown_entry_fails_with_readable_error(self):
        result = self.run_script("scripts/run-popup.sh", "fixture-does-not-exist", input="\n", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown popup id", result.stderr)

    def test_tool_dependency_failure_does_not_use_real_tool(self):
        self.stub("yazi", "exit 23")
        result = self.run_script("scripts/run-popup.sh", "yazi", check=False)
        self.assertEqual(result.returncode, 23)

    def test_home_relative_reload_path_expands_once(self):
        self.tmux("set-option", "-g", "@tmux-popups-config-file", "~/config/tmux.conf")
        self.run_script("scripts/generate-config.sh")
        self.assertIn(f'"{self.home}/config/tmux.conf"', self.generated().read_text())
        self.assertNotIn(f"{self.home}/~/", self.generated().read_text())

    def test_home_relative_registry_selection(self):
        registry = self.home / "config/local entries.tsv"
        registry.parent.mkdir()
        registry.write_text("fixture\t-\tx\tfixture\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", "~/config/local entries.tsv")
        self.run_script("scripts/generate-config.sh")
        self.assertIn("run-popup.sh fixture", self.generated().read_text())
        env = dict(self.env, TMUX_POPUPS_LOCAL_REGISTRY="~/config/local entries.tsv")
        self.assertIn("fixture\t", self.run_script("scripts/list-popups.sh", "--tsv", env=env).stdout)

    def test_project_path_expansion_is_literal(self):
        marker = self.home / "project-argument"
        self.stub("yazi", f"printf '%s' \"$1\" > {shlex.quote(str(marker))}")
        for value, expected in [
            ("~/Work with spaces", str(self.home / "Work with spaces")),
            ("~", str(self.home)),
            ("/tmp/absolute path", "/tmp/absolute path"),
            ("relative path", "relative path"),
            ("$(touch unexpected)", "$(touch unexpected)"),
            ("$OTHER_HOME/path", "$OTHER_HOME/path"),
        ]:
            with self.subTest(value=value):
                self.run_script("scripts/tools/projects.sh", env=dict(self.env, PROJECTS_DIR=value))
                self.assertEqual(marker.read_text(), expected)
        self.assertFalse((self.home / "unexpected").exists())

    def test_registry_option_survives_fresh_dispatch(self):
        registry = self.home / "custom.tsv"
        registry.write_text(
            "fixture\t-\tx\tfixture\t70%\t70%\tscripts/tools/calc.sh\n"
            "yazi\tY\tr\tcustom yazi\t80%\t80%\tscripts/tools/calc.sh\n"
        )
        marker = self.home / "dispatched"
        self.stub("python3", f"printf selected > {shlex.quote(str(marker))}")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        self.load()
        for entry in ["fixture", "yazi"]:
            with self.subTest(entry=entry):
                self.run_script("scripts/run-popup.sh", entry)
                self.assertEqual(marker.read_text(), "selected")
                marker.unlink()
        self.stub("less", "exec cat")
        self.assertIn(str(registry), self.run_script("scripts/popup-help.sh").stdout)
        self.assertIn("fixture\t", self.run_script("scripts/list-popups.sh", "--tsv").stdout)

    def test_explicit_registry_environment_precedes_tmux_option(self):
        option = self.home / "option.tsv"
        explicit = self.home / "explicit.tsv"
        option.write_text("fixture\t-\tx\toption\t70%\t70%\t-\n")
        explicit.write_text("fixture\t-\tx\texplicit\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(option))
        env = dict(self.env, TMUX_POPUPS_LOCAL_REGISTRY=str(explicit))
        self.run_script("scripts/generate-config.sh", env=env)
        self.assertIn("# Local source: " + str(explicit), self.generated().read_text())
        self.assertIn("\texplicit\t", self.run_script("scripts/list-popups.sh", "--tsv", env=env).stdout)

    def test_missing_explicit_registry_fails_without_silent_fallback(self):
        missing = self.home / "missing.tsv"
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(missing))
        for script, args in [
            ("scripts/generate-config.sh", []),
            ("scripts/list-popups.sh", ["--tsv"]),
            ("scripts/run-popup.sh", ["yazi"]),
        ]:
            with self.subTest(script=script):
                result = self.run_script(script, *args, input="\n", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(str(missing), result.stderr)


if __name__ == "__main__":
    def terminate(signum, frame):
        raise KeyboardInterrupt("verification deadline reached")

    signal.signal(signal.SIGTERM, terminate)
    unittest.main(verbosity=2)
