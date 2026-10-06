"""Origin routing on two synthetic clients; no real-provider qualification."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest
import test_launcher as launcher


class ContextTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    setUp = launcher.LauncherTests.setUp
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def clients(self):
        first_dir = self.home / r"first ' directory\; $(touch injected) #{session_name}"
        second_dir = self.home / "second directory"
        first_dir.mkdir()
        second_dir.mkdir()
        self.tmux("respawn-pane", "-k", "-c", str(first_dir).replace("#", "##"),
                  "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        self.tmux("new-session", "-d", "-s", "other", "-c", str(second_dir),
                  "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        first = self.attach()
        second = self.attach("other")
        origins = {}
        for session in ("fixture", "other"):
            data = self.tmux("display-message", "-p", "-t", session,
                             "#{session_id}|#{window_id}|#{pane_id}|#{pane_current_path}").stdout.strip().split("|")
            clients = self.tmux("list-clients", "-F", "#{client_name}|#{session_name}").stdout.splitlines()
            client = next(line.split("|")[0] for line in clients if line.endswith("|" + session))
            self.assertEqual(data[3], str(first_dir if session == "fixture" else second_dir))
            origins[session] = dict(zip(("SESSION", "WINDOW", "PANE", "DIRECTORY"), data), CLIENT=client)
        return first, second, origins

    def test_two_clients_direct_menu_popup_window_origin_contract(self):
        first, second, origins = self.clients()
        code = "import os,json,pathlib; pathlib.Path(" + repr(str(self.home)) + ",os.environ['TMUX_POPUPS_SESSION']).write_text(json.dumps({k:os.environ.get('TMUX_POPUPS_'+k) for k in ['CLIENT','SESSION','WINDOW','PANE','DIRECTORY']}|{'cwd':os.getcwd()}))"
        self.stub("yazi", "exec python3 -c " + shlex.quote(code))
        for mode in ("window", "popup"):
            self.tmux("set-option", "-g", "@tmux-popups-yazi-mode", mode)
            self.load()
            for source in ("direct", "menu"):
                for session, fd in (("fixture", first), ("other", second)):
                    with self.subTest(mode=mode, source=source, session=session):
                        # Change the unrelated session's active pane immediately before dispatch.
                        other = "other" if session == "fixture" else "fixture"
                        self.tmux("select-pane", "-t", origins[other]["PANE"])
                        marker = self.home / origins[session]["SESSION"]
                        if source == "direct":
                            os.write(fd, b"\x02Y")
                        else:
                            os.write(fd, b"\x02\r")
                            self.wait_until(lambda: b"Quick Menu" in self.client_output[fd])
                            self.client_output[fd].clear()
                            os.write(fd, b"r")
                        self.wait_until(marker.exists)
                        self.assertEqual(json.loads(marker.read_text()), origins[session] | {"cwd": origins[session]["DIRECTORY"]})
                        marker.unlink()
                        self.assertEqual(self.tmux("display-message", "-p", "-t", origins[other]["PANE"], "#{session_name}").stdout.strip(), other)
        self.assertFalse((Path(origins["fixture"]["DIRECTORY"]) / "injected").exists())

    def helper(self, expression, context):
        return subprocess.run(["bash", "-c", '. "$1"; ' + expression, "bash", str(launcher.ROOT / "scripts/lib.sh")],
                              env=self.env | {"TMUX_POPUPS_" + k: v for k, v in context.items()},
                              text=True, capture_output=True, timeout=12)

    def test_close_targets_origin_and_vanished_origin_cancels(self):
        first, second, origins = self.clients()
        self.tmux("set-option", "-g", "@tmux-popups-yazi-mode", "popup")
        self.stub("yazi", "touch " + shlex.quote(str(self.home)) + '/ready-"$TMUX_POPUPS_SESSION"; read -r value; printf %s \"$value\" > ' + shlex.quote(str(self.home)) + '/read-"$TMUX_POPUPS_SESSION"')
        self.load()
        os.write(first, b"\x02Y")
        os.write(second, b"\x02Y")
        self.wait_until(lambda: all((self.home / ("ready-" + origin["SESSION"])).exists() for origin in origins.values()))
        self.assertEqual(self.helper("close_origin_popup", origins["fixture"]).returncode, 0)
        # The second popup remains alive and consumes input after closing the first.
        os.write(second, b"still-open\r")
        marker = self.home / ("read-" + origins["other"]["SESSION"])
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text(), "still-open")
        self.tmux("detach-client", "-t", origins["fixture"]["CLIENT"])
        result = self.helper("close_origin_popup", origins["fixture"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("origin client", result.stderr)
        self.assertEqual(self.helper("origin_client", origins["other"]).returncode, 0)
        self.assertEqual(self.helper("close_origin_popup", origins["other"]).returncode, 0)
        self.tmux("kill-session", "-t", "fixture")
        result = self.helper("origin_pane", origins["fixture"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("vanished", result.stderr)

    def test_sessions_picker_switches_only_origin_client(self):
        first, second, origins = self.clients()
        self.tmux("new-session", "-d", "-s", "target", "exec /bin/bash --noprofile --norc")
        env = self.env | {"TMUX_POPUPS_" + k: v for k, v in origins["fixture"].items()}
        self.run_script("scripts/tools/sessions.sh", env=env)
        self.wait_until(lambda: b"target" in self.client_output[first])
        # choose-tree gives session roots labels 0, 2, 4 for these three sessions.
        os.write(first, b"4\r")
        def attached_sessions():
            return dict(line.split("|") for line in self.tmux("list-clients", "-F", "#{client_name}|#{session_name}").stdout.splitlines())
        self.wait_until(lambda: attached_sessions()[origins["fixture"]["CLIENT"]] == "target")
        self.assertEqual(attached_sessions()[origins["other"]["CLIENT"]], "other")

    def test_snapshot_survives_client_focus_change_and_missing_origin(self):
        first, second, origins = self.clients()
        marker = self.home / "snapshot"
        self.stub("yazi", "printf '%s' \"$TMUX_POPUPS_SESSION\" > " + shlex.quote(str(marker)))
        self.tmux("switch-client", "-c", origins["fixture"]["CLIENT"], "-t", "other")
        values = [origins["fixture"][k] for k in ("CLIENT", "SESSION", "WINDOW", "PANE", "DIRECTORY")]
        self.run_script("scripts/run-popup.sh", "yazi", "--launch", *values)
        self.wait_until(marker.exists)
        self.assertEqual(marker.read_text(), origins["fixture"]["SESSION"])
        marker.unlink()
        self.tmux("kill-session", "-t", "fixture")
        result = self.run_script("scripts/run-popup.sh", "yazi", "--launch", *values, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("origin pane/session vanished", result.stderr)
        self.assertFalse(marker.exists())

    def test_cli_never_infers_attached_client(self):
        self.clients()
        marker = self.home / "cli-context"
        self.stub("yazi", "printf '%s|%s' \"${TMUX_POPUPS_CLIENT-unset}\" \"$TMUX_POPUPS_DIRECTORY\" > " + shlex.quote(str(marker)))
        self.run_script("scripts/run-popup.sh", "yazi")
        self.assertEqual(marker.read_text(), "unset|" + str(self.home))
        result = self.helper("close_origin_popup", {})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not supplied", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
