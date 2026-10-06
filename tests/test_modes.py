"""Per-entry modes on disposable PTYs and sockets; no terminal qualification."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest
import test_launcher as launcher
import test_context as context


class ModeTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    setUp = launcher.LauncherTests.setUp
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until
    clients = context.ContextTests.clients

    def registry(self, mode=None, completion=None, command="scripts/tools/calc.sh"):
        fields = ["fixture_entry", "X", "x", "mode fixture", "61", "17", command]
        if mode is not None:
            fields.append(mode)
        if completion is not None:
            fields.append(completion)
        path = self.home / "modes.tsv"
        path.write_text("\t".join(fields) + "\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(path))
        return path

    def adapter(self):
        marker = self.home / "record"
        gate = self.home / "gate"
        code = "\n".join([
            "import os,json,pathlib,time",
            "try: size=list(os.get_terminal_size(0))",
            "except OSError: size=None",
            "record={k:os.environ.get('TMUX_POPUPS_'+k) for k in ['CLIENT','SESSION','WINDOW','PANE','DIRECTORY']}",
            "record.update(cwd=os.getcwd(),size=size)",
            "pathlib.Path(" + repr(str(marker)) + ").write_text(json.dumps(record))",
            "end=time.monotonic()+5",
            "while not pathlib.Path(" + repr(str(gate)) + ").exists() and time.monotonic()<end: time.sleep(.02)",
            "raise SystemExit(23)",
        ])
        real_python = shlex.quote(os.path.realpath(launcher.shutil.which("python3")))
        self.stub("python3", "exec " + real_python + " -c " + shlex.quote(code))
        return marker, gate

    def test_legacy_and_extended_direct_menu_cwd_dimensions_and_exit(self):
        first, second, origins = self.clients()
        marker, gate = self.adapter()
        self.tmux("set-option", "-g", "remain-on-exit", "on")
        for mode, completion in [(None, None), ("popup", None), ("window", "foreground"),
                                 ("command", "foreground"), ("command", "background")]:
            self.registry(mode, completion)
            self.load()
            for source in ("direct", "menu"):
                with self.subTest(mode=mode, completion=completion, source=source):
                    marker.unlink(missing_ok=True)
                    gate.unlink(missing_ok=True)
                    self.client_output[first].clear()
                    self.tmux("select-window", "-t", origins["fixture"]["WINDOW"])
                    before = self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout.splitlines()
                    if source == "direct":
                        os.write(first, b"\x02X")
                    else:
                        self.client_output[first].clear()
                        os.write(first, b"\x02\r")
                        self.wait_until(lambda: b"Quick Menu" in self.client_output[first])
                        os.write(first, b"x")
                    self.wait_until(marker.exists)
                    record = json.loads(marker.read_text())
                    self.assertEqual({k:record[k] for k in origins["fixture"]}, origins["fixture"])
                    self.assertEqual(record["cwd"], origins["fixture"]["DIRECTORY"])
                    if mode in (None, "popup"):
                        self.assertEqual(record["size"], [59, 15])
                    elif mode == "window":
                        self.assertEqual(record["size"], [100, 39])
                    else:
                        self.assertIsNone(record["size"])
                    after = self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout.splitlines()
                    self.assertEqual(len(after), len(before) + (mode == "window"))
                    gate.touch()
                    if mode == "window":
                        created = next(window for window in after if window not in before)
                        self.wait_until(lambda: self.tmux("display-message", "-p", "-t", created,
                                                        "#{pane_dead_status}").stdout.strip() == "23")
                        self.tmux("kill-window", "-t", created)
                    else:
                        if completion != "background":
                            # tmux displays run-shell exit failures in view mode
                            # after the popup closes or direct command exits.
                            self.wait_until(lambda: b"returned 23" in self.client_output[first])
                            os.write(first, b"q")
                            self.wait_until(lambda: self.tmux("display-message", "-p", "-t", origins["fixture"]["PANE"],
                                                            "#{pane_in_mode}").stdout.strip() == "0")
                        # Input must reach the original shell after completion.
                        closed = self.home / "returned"
                        closed.unlink(missing_ok=True)
                        os.write(first, ("touch " + shlex.quote(str(closed)) + "\r").encode())
                        self.wait_until(closed.exists)
                    self.assertEqual(self.tmux("display-message", "-p", "-t", origins["other"]["PANE"],
                                               "#{session_name}").stdout.strip(), "other")

    def test_command_completion_cli_and_launch(self):
        first, second, origins = self.clients()
        marker, gate = self.adapter()
        context = [origins["fixture"][k] for k in ("CLIENT", "SESSION", "WINDOW", "PANE", "DIRECTORY")]
        for entrypoint in ([], ["--launch", *context]):
            for completion in ("foreground", "background"):
                with self.subTest(entrypoint=entrypoint, completion=completion):
                    self.registry("command", completion)
                    marker.unlink(missing_ok=True)
                    gate.unlink(missing_ok=True)
                    process = subprocess.Popen([str(launcher.ROOT / "scripts/run-popup.sh"), "fixture_entry", *entrypoint],
                                               env=self.env, cwd=self.home, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.addCleanup(lambda p=process: p.poll() is None and p.kill())
                    self.wait_until(marker.exists)
                    if completion == "foreground":
                        self.assertIsNone(process.poll(), "foreground returned before adapter exit")
                        gate.touch()
                        self.assertEqual(process.wait(timeout=6), 23)
                    else:
                        self.assertEqual(process.wait(timeout=6), 0)
                        self.assertFalse(gate.exists(), "background waited for completion")
                        gate.touch()
                    process.communicate(timeout=6)

    def test_compatibility_paths_and_explicit_local_override(self):
        self.registry(command="scripts/tools/yazi.sh")
        rows = self.run_script("scripts/list-popups.sh", "--tsv").stdout
        self.assertIn("scripts/tools/yazi.sh\twindow\tforeground", rows)
        self.tmux("set-option", "-g", "@tmux-popups-yazi-mode", "popup")
        rows = self.run_script("scripts/list-popups.sh", "--tsv").stdout
        self.assertIn("scripts/tools/yazi.sh\tpopup\tforeground", rows)
        self.registry("window", command="scripts/tools/yazi.sh")
        rows = self.run_script("scripts/list-popups.sh", "--tsv").stdout
        self.assertIn("scripts/tools/yazi.sh\twindow\tforeground", rows)
        self.registry(command="scripts/tools/calc.sh")
        rows = self.run_script("scripts/list-popups.sh", "--tsv").stdout
        self.assertIn("scripts/tools/calc.sh\tpopup\tforeground", rows)

    def test_command_literal_control_directories_on_two_clients(self):
        first, second, origins = self.clients()
        marker = self.home / "literal-command"
        code = "import os,json,pathlib; pathlib.Path(" + repr(str(marker)) + ").write_text(json.dumps({k:os.environ.get('TMUX_POPUPS_'+k) for k in ['CLIENT','SESSION','WINDOW','PANE','DIRECTORY']}|{'cwd':os.getcwd()}))"
        real_python = shlex.quote(os.path.realpath(launcher.shutil.which("python3")))
        self.stub("python3", "exec " + real_python + " -c " + shlex.quote(code))
        directory = self.home / "literal\nreview_payload\n' \\; $(review_payload) #{session_name}\t\n\n"
        directory.mkdir()
        unexpected = self.home / "unexpected"
        self.stub("review_payload", "touch " + shlex.quote(str(unexpected)))
        for origin in origins.values():
            self.tmux("respawn-pane", "-k", "-t", origin["PANE"], "-c", str(directory).replace("#", "##"),
                      "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
            origin["DIRECTORY"] = str(directory)
        for completion in ("foreground", "background"):
            self.registry("command", completion)
            self.load()
            for source in ("direct", "menu"):
                for session, fd in (("fixture", first), ("other", second)):
                    with self.subTest(completion=completion, source=source, session=session):
                        marker.unlink(missing_ok=True)
                        self.client_output[fd].clear()
                        if source == "direct":
                            os.write(fd, b"\x02X")
                        else:
                            os.write(fd, b"\x02\r")
                            self.wait_until(lambda: b"Quick Menu" in self.client_output[fd])
                            os.write(fd, b"x")
                        self.wait_until(marker.exists)
                        self.assertEqual(json.loads(marker.read_text()), origins[session] | {"cwd": str(directory)})
                        self.assertFalse(unexpected.exists())

    def test_invalid_extension_preserves_last_good_and_bindings(self):
        self.load()
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        for mode, completion, command, message in [
            ("wrong", None, "scripts/tools/calc.sh", "invalid launch mode"),
            ("popup", "background", "scripts/tools/calc.sh", "requires command mode"),
            ("command", "wrong", "scripts/tools/calc.sh", "invalid completion"),
            ("command", "foreground", "-", "requires an executable target"),
            ("", None, "scripts/tools/calc.sh", "empty required field"),
            ("command", "", "scripts/tools/calc.sh", "empty required field"),
        ]:
            with self.subTest(mode=mode, completion=completion):
                path = self.registry(mode, completion, command)
                result = self.run_script("scripts/generate-config.sh", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(str(path) + ":1:", result.stderr)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.generated().read_bytes(), before)
                self.assertEqual(self.tmux("list-keys").stdout, keys)


if __name__ == "__main__":
    unittest.main(verbosity=2)
