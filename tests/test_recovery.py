"""Opt-in recovery does not read tool input until its owned launch has ended."""
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import unittest
import test_launcher as launcher


class RecoveryTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def setUp(self):
        launcher.LauncherTests.setUp(self)
        self.env['FIXTURE'] = str(self.home)
        self.tmux("set-environment", "-g", "FIXTURE", str(self.home))
        self.adapter = self.stub("adapter with ' spaces", '''echo $$ >> "$FIXTURE/calls"
echo $$ > "$FIXTURE/tool-pid"
printf 'tool-output\\n'
case "${APP_ACTION:-status}" in
once)
  if [[ ! -f "$FIXTURE/once" ]]; then touch "$FIXTURE/once"; exit 23; fi ;;
read)
  printf 'application-input> '
  read -r value
  printf '%s' "$value" > "$FIXTURE/input" ;;
slow)
  /bin/sleep 60 &
  echo $! > "$FIXTURE/sleep-pid"
  wait ;;
signal) kill -TERM $$ ;;
raw) stty -echo -icanon -isig ;;
esac
exit "${APP_STATUS:-0}"''')
        self.registry = self.home / "recovery.tsv"
        self.registry.write_text("fixture\tX\tx\tfailure fixture\t80%\t70%\t" + str(self.adapter) + "\tpopup\tforeground\ton\t-\tabsolute\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(self.registry))
        self.tmux("set-option", "-g", "@tmux-popups-fixture-close", "on-success")
        self.client = self.attach()
        target = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        ids = self.tmux("display-message", "-p", "-t", "fixture", "#{session_id}|#{window_id}|#{pane_id}").stdout.strip().split("|")
        self.directory = self.home / "origin ' \\; #{session_name}\t\n"
        self.directory.mkdir()
        self.context = [target, *ids, str(self.directory)]

    def settings(self, **settings):
        for key, value in settings.items():
            self.tmux("set-environment", "-g", key, value)
            self.env[key] = value

    def start(self):
        process = subprocess.Popen([str(launcher.ROOT / "scripts/run-popup.sh"), "fixture", "--launch", *self.context],
                                   env=self.env, cwd=self.home, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        def cleanup():
            if process.poll() is None:
                process.terminate()
            try: process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.communicate(timeout=3)
        self.addCleanup(cleanup)
        return process

    def prompt(self, status):
        self.wait_until(lambda: f"exited with status {status}".encode() in self.terminal_output)
        self.assertIn(b"tool-output", self.terminal_output)
        self.assertIn(b"[r] retry", self.terminal_output)

    def calls(self):
        path = self.home / "calls"
        return path.read_text().splitlines() if path.exists() else []

    def test_success_closes_and_compatibility_policy_keeps_status(self):
        process = self.start()
        _, error = process.communicate(timeout=6)
        self.assertEqual(process.returncode, 0, error)
        self.assertNotIn(b"exited with status", self.terminal_output)
        self.tmux("set-option", "-gu", "@tmux-popups-fixture-close")
        self.settings(APP_STATUS="23")
        process = self.start()
        process.communicate(timeout=6)
        self.assertEqual(process.returncode, 23)

    def test_failure_retry_waits_for_completion_then_succeeds(self):
        self.settings(APP_ACTION="once")
        process = self.start()
        self.prompt(23)
        self.assertIsNone(process.poll())
        first = int(self.calls()[0])
        self.assertFalse(Path(f"/proc/{first}").exists())
        os.write(self.client, b"r")
        _, error = process.communicate(timeout=6)
        self.assertEqual(process.returncode, 0, error)
        self.assertEqual(len(self.calls()), 2)
        self.assertNotEqual(self.calls()[0], self.calls()[1])

    def test_never_policy_holds_success_and_close_returns_status(self):
        self.tmux("set-option", "-g", "@tmux-popups-fixture-close", "never")
        process = self.start()
        self.prompt(0)
        self.assertIsNone(process.poll())
        os.write(self.client, b"c")
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0)

    def test_read_input_reaches_application_before_recovery_controls(self):
        self.settings(APP_ACTION="read", APP_STATUS="23")
        process = self.start()
        self.wait_until(lambda: b"application-input>" in self.terminal_output)
        os.write(self.client, b"r w c literal input\r")
        self.prompt(23)
        self.assertEqual((self.home / "input").read_text(), "r w c literal input")
        os.write(self.client, b"c")
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 23)

    def test_ctrl_c_stops_owned_slow_group_before_prompt(self):
        self.settings(APP_ACTION="slow")
        process = self.start()
        marker = self.home / "sleep-pid"
        self.wait_until(marker.exists)
        child = int(marker.read_text())
        os.write(self.client, b"\x03")
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 130)
        def stopped():
            stat = Path(f"/proc/{child}/stat")
            return not stat.exists() or stat.read_text().split()[2] == 'Z'
        self.wait_until(stopped)

    def test_signal_and_missing_target_remain_readable_for_retry(self):
        self.settings(APP_ACTION="signal")
        process = self.start()
        self.prompt(143)
        self.adapter.unlink()
        self.terminal_output.clear()
        os.write(self.client, b"r")
        self.wait_until(lambda: b"executable" in self.terminal_output)
        self.wait_until(lambda: b"exited with status 1" in self.terminal_output)
        self.adapter.write_text("#!/usr/bin/env bash\nprintf 'restored-tool\\n'\nexit 0\n")
        self.adapter.chmod(0o755)
        os.write(self.client, b"r")
        process.communicate(timeout=6)
        self.assertEqual(process.returncode, 0)

    def test_window_fallback_starts_fresh_process_with_original_context(self):
        record = self.home / "fallback-context"
        code = "import os,json,pathlib; pathlib.Path("+repr(str(record))+").write_text(json.dumps({k:os.environ.get('TMUX_POPUPS_'+k) for k in ['CLIENT','SESSION','WINDOW','PANE','DIRECTORY']}|{'cwd':os.getcwd()}))"
        self.stub(self.adapter.name, 'echo $$ >> "$FIXTURE/calls"; printf "tool-output\\n"; python3 -c '+shlex.quote(code)+'; exit 23')
        process = self.start()
        self.prompt(23)
        before = self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout.splitlines()
        self.terminal_output.clear()
        os.write(self.client, b"w")
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0)
        self.wait_until(lambda: len(self.calls()) == 2)
        self.wait_until(lambda: b"exited with status 23" in self.terminal_output)
        self.assertEqual(json.loads(record.read_text()),
                         dict(zip(["CLIENT","SESSION","WINDOW","PANE","DIRECTORY"],self.context),cwd=str(self.directory)))
        after = self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout.splitlines()
        self.assertEqual(len(after),len(before)+1)
        created = next(window for window in after if window not in before)
        self.wait_until(lambda: "exited with status 23" in self.tmux("capture-pane", "-p", "-t", created).stdout)
        frame = self.tmux("capture-pane", "-p", "-t", created).stdout
        self.assertNotIn("[w] start again", frame)
        os.write(self.client,b"c")
        self.wait_until(lambda: self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout.splitlines()==before)

    def test_invalid_policy_and_command_mode_leave_last_good_config(self):
        self.load()
        before = self.generated().read_bytes(), self.tmux("list-keys").stdout
        for value, mode in [("bad", "popup"), ("on-success", "command")]:
            self.tmux("set-option", "-g", "@tmux-popups-fixture-close", value)
            self.registry.write_text(self.registry.read_text().replace("\tpopup\t", "\t"+mode+"\t"))
            result = self.run_script("scripts/generate-config.sh",check=False)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("close policy",result.stderr)
            self.assertEqual(before,(self.generated().read_bytes(),self.tmux("list-keys").stdout))

    def test_nonterminal_recovery_returns_tool_status_without_prompt(self):
        self.settings(APP_STATUS="23")
        result = self.run_script("scripts/recover-entry.sh", "fixture", "on-success", "popup", input="", check=False)
        self.assertEqual(result.returncode, 23)
        self.assertNotIn("[r] retry", result.stdout)

    def test_terminating_recovery_wrapper_stops_its_owned_group(self):
        self.settings(APP_ACTION="slow")
        process = self.start()
        marker = self.home / "sleep-pid"
        self.wait_until(marker.exists)
        tool = int((self.home / "tool-pid").read_text())
        wrapper = int(Path(f"/proc/{tool}/stat").read_text().split()[3])
        sleeper = int(marker.read_text())
        os.kill(wrapper, signal.SIGTERM)
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 143)
        self.wait_until(lambda: not Path(f"/proc/{tool}").exists())
        self.wait_until(lambda: not Path(f"/proc/{sleeper}/stat").exists() or
                        Path(f"/proc/{sleeper}/stat").read_text().split()[2] == "Z")

    def test_crashed_raw_terminal_is_restored_for_recovery_input(self):
        self.settings(APP_ACTION="raw", APP_STATUS="23")
        process = self.start()
        self.prompt(23)
        os.write(self.client, b"\x03")
        _, error = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 130, error)

    def test_retry_rejects_a_change_to_background_command_mode(self):
        self.settings(APP_STATUS="23")
        process = self.start()
        self.prompt(23)
        self.tmux("set-option", "-g", "@tmux-popups-fixture-close", "always")
        self.registry.write_text(self.registry.read_text().replace("\tpopup\tforeground", "\tcommand\tbackground"))
        self.terminal_output.clear()
        os.write(self.client, b"r")
        self.wait_until(lambda: b"close recovery and relaunch" in self.terminal_output)
        self.wait_until(lambda: b"exited with status 1" in self.terminal_output)
        self.assertEqual(len(self.calls()), 1)
        os.write(self.client, b"c")
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 1)

    def test_default_policy_needs_no_python_but_retained_policy_does(self):
        directory = self.base / "without-python"
        directory.mkdir()
        for name in ["bash", "dirname"]:
            (directory / name).symlink_to(shutil.which(name))
        command = '. "$1"; entry_close_policy fixture popup "$2"'
        for policy, expected in [("always", 0), ("on-success", 1), ("never", 1)]:
            result = subprocess.run(["/bin/bash", "-c", command, "bash", str(launcher.ROOT / "scripts/lib.sh"), policy],
                                    env=dict(self.env, PATH=str(directory)), capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, expected)
            if expected: self.assertIn("python3 required", result.stderr)

    def test_recovery_cancels_if_original_pane_has_vanished(self):
        env = dict(self.env, TMUX_POPUPS_CLIENT=self.context[0], TMUX_POPUPS_SESSION=self.context[1],
                   TMUX_POPUPS_WINDOW=self.context[2], TMUX_POPUPS_PANE="%999999", TMUX_POPUPS_DIRECTORY=self.context[4])
        result = self.run_script("scripts/run-popup.sh", "fixture", "--recover", env=env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("origin is no longer available", result.stderr)
        self.assertEqual(self.calls(), [])
