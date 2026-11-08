"""Explicit tool-window reuse never identifies a window by title alone."""
import os
from pathlib import Path
import shlex
import subprocess
import unittest
import test_launcher as launcher


class ReuseTests(unittest.TestCase):
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
        self.marker = self.home / "launches"
        self.stub("yazi", "printf 'started\\n' >> " + shlex.quote(str(self.marker)) + "; read -r value")
        self.registry = self.home / "reuse.tsv"
        self.registry.write_text("fixture\tX\tx\tshared tool\t70%\t70%\tscripts/tools/yazi.sh\twindow\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(self.registry))
        self.tmux("set-option", "-g", "@tmux-popups-fixture-reuse", "session")
        self.attach()
        self.context = self.origin("fixture")

    def origin(self, session):
        data = self.tmux("display-message", "-p", "-t", session,
                         "#{session_id}|#{window_id}|#{pane_id}").stdout.strip().split("|")
        clients = self.tmux("list-clients", "-F", "#{client_name}|#{session_name}").stdout.splitlines()
        client = next(line.split("|")[0] for line in clients if line.endswith("|" + session))
        return [client, *data, str(self.home)]

    def windows(self, session="fixture"):
        return self.tmux("list-windows", "-t", session, "-F", "#{window_id}").stdout.splitlines()

    def launch(self, context=None):
        return self.run_script("scripts/run-popup.sh", "fixture", "--launch", *(context or self.context))

    def launches(self):
        return len(self.marker.read_text().splitlines()) if self.marker.exists() else 0

    def owned(self, session="fixture"):
        return [window for window in self.windows(session)
                if self.tmux("show-option", "-w", "-t", window, "-qv", "@tmux-popups-entry", check=False).stdout.strip() == "fixture"]

    def test_repeat_rename_same_title_and_closed_window(self):
        self.launch()
        self.wait_until(lambda: self.launches() == 1)
        window = self.owned()[0]
        self.tmux("rename-window", "-t", window, "renamed by user")
        user = self.tmux("new-window", "-P", "-F", "#{window_id}", "-t", "fixture:",
                         "-n", "shared tool", "exec /bin/bash --noprofile --norc").stdout.strip()
        self.launch()
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.owned(), [window])
        self.assertEqual(self.tmux("display-message", "-p", "-t", "fixture", "#{window_id}").stdout.strip(), window)
        self.tmux("kill-window", "-t", window)
        self.launch()
        self.wait_until(lambda: self.launches() == 2)
        self.assertNotEqual(self.owned(), [window])
        self.assertIn(user, self.windows())

    def test_moved_tool_pane_does_not_reuse_its_previous_window(self):
        self.launch()
        self.wait_until(lambda: self.launches() == 1)
        old = self.owned()[0]
        tool = self.tmux("show-option", "-w", "-t", old, "-qv",
                         "@tmux-popups-tool-pane").stdout.strip()
        self.tmux("split-window", "-t", old,
                  "exec /bin/bash --noprofile --norc")
        user = self.tmux("new-window", "-P", "-F", "#{window_id}",
                         "-t", "fixture:", "-n", "user window",
                         "exec /bin/bash --noprofile --norc").stdout.strip()
        self.tmux("join-pane", "-s", tool, "-t", user)
        self.launch()
        self.wait_until(lambda: self.launches() == 2)
        self.assertNotIn(old, self.owned())
        self.assertNotIn(user, self.owned())
        self.assertEqual(len(self.owned()), 1)
        self.assertIn(old, self.windows())
        self.assertIn(user, self.windows())
        self.assertEqual(self.tmux("display-message", "-p", "-t", tool,
                                  "#{window_id}").stdout.strip(), user)

    def test_directory_scope_keeps_literal_paths_separate(self):
        self.tmux("set-option", "-g", "@tmux-popups-fixture-reuse", "directory")
        first = self.home / "project ' one\t\n"
        second = self.home / r"project two\n"
        first.mkdir(); second.mkdir()
        for directory in [first, second, first]:
            context = self.context[:-1] + [str(directory)]
            self.launch(context)
        self.wait_until(lambda: self.launches() == 2)
        windows = self.owned()
        self.assertEqual(len(windows), 2)
        encoded = {self.tmux("show-option", "-w", "-qv", "-t", window,
                             "@tmux-popups-directory").stdout.strip() for window in windows}
        self.assertEqual(encoded, {os.fsencode(str(path)).hex() for path in [first, second]})

    def test_two_sessions_are_independent(self):
        self.launch()
        first = self.owned()[0]
        self.tmux("new-session", "-d", "-s", "other", "printf 'fixture-ready\\n'; exec /bin/bash --noprofile --norc")
        self.attach("other")
        context = self.origin("other")
        self.launch(context)
        self.launch(context)
        self.wait_until(lambda: self.launches() == 2)
        self.assertEqual(self.owned(), [first])
        self.assertEqual(len(self.owned("other")), 1)
        self.assertNotEqual(self.owned("other"), [first])

    def test_simultaneous_launches_create_one_tool(self):
        processes = [subprocess.Popen([str(launcher.ROOT / "scripts/run-popup.sh"), "fixture", "--launch", *self.context],
                                      env=self.env, cwd=self.home, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.PIPE) for _ in range(4)]
        for process in processes:
            self.addCleanup(lambda process=process: process.poll() is None and process.kill())
            _, error = process.communicate(timeout=12)
            self.assertEqual(process.returncode, 0, error)
        self.wait_until(lambda: self.launches() == 1)
        self.assertEqual(len(self.owned()), 1)

    def test_exited_remain_on_exit_pane_is_retained_and_recreated(self):
        self.tmux("set-option", "-gw", "remain-on-exit", "on")
        self.launch()
        self.wait_until(lambda: self.launches() == 1)
        old = self.owned()[0]
        self.tmux("send-keys", "-t", old, "done", "Enter")
        self.wait_until(lambda: self.tmux("display-message", "-p", "-t", old, "#{pane_dead}").stdout.strip() == "1")
        self.launch()
        self.wait_until(lambda: self.launches() == 2)
        self.assertIn(old, self.windows())
        self.assertNotIn(old, self.owned())
        self.assertEqual(len(self.owned()), 1)

    def test_disabled_reuse_keeps_new_window_behavior_and_invalid_policy_rejects(self):
        self.tmux("set-option", "-g", "@tmux-popups-fixture-reuse", "off")
        self.launch(); self.launch()
        self.wait_until(lambda: self.launches() == 2)
        self.assertEqual(len(self.windows()), 3)
        self.assertEqual(self.owned(), [])
        self.run_script("scripts/generate-config.sh")
        before = self.generated().read_bytes()
        for policy in ["unknown", "session"]:
            self.tmux("set-option", "-g", "@tmux-popups-fixture-reuse", policy)
            if policy == "session":
                self.registry.write_text("fixture\tX\tx\tshared tool\t70%\t70%\tscripts/tools/yazi.sh\tpopup\n")
            result = self.run_script("scripts/generate-config.sh", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, self.generated().read_bytes())

    def test_fast_exiting_tool_does_not_fail_while_tagging(self):
        self.stub("yazi", "exit 0")
        for _ in range(8):
            self.launch()
        self.wait_until(lambda: len(self.windows()) == 1)
