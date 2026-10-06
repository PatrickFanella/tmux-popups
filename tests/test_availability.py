"""Enablement, effective dependencies and migration on private tmux servers."""
import shlex
import shutil
import subprocess
import unittest
import test_launcher as launcher


class AvailabilityTests(unittest.TestCase):
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
        self.tmux("set-option", "-gu", "@tmux-popups-profile")
        self.tmux("set-option", "-gu", "@tmux-popups-availability")

    def registry(self, enabled="on", deps="auto", command="scripts/tools/calc.sh", id="fixture"):
        path = self.home / "availability.tsv"
        path.write_text("\t".join([id, "X", "x", "availability fixture", "70%", "70%",
                                   command, "command", "foreground", enabled, deps]) + "\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(path))
        return path

    def states(self, env=None):
        return {r[0]: r for r in (line.split("\t") for line in
                self.run_script("scripts/list-popups.sh", "--state-tsv", env=env).stdout.splitlines())}

    def test_small_default_optional_discovery_and_full_compatibility(self):
        states = self.states()
        self.assertEqual({id for id, row in states.items() if row[9] == "on"},
                         {"help", "shell", "notes", "timer", "keys"})
        self.load()
        self.assertNotIn("quick chat", self.generated().read_text())
        self.stub("less", "exec cat")
        help = self.run_script("scripts/popup-help.sh").stdout
        self.assertIn("Optional adapters", help)
        self.assertIn("quick chat", help)
        self.assertIn("off/", help)
        self.tmux("set-option", "-g", "@tmux-popups-profile", "full")
        self.tmux("set-option", "-g", "@tmux-popups-availability", "ignore")
        self.load()
        self.assertIn("quick chat", self.generated().read_text())
        self.assertIn('bind-key "O"', self.generated().read_text())
        # Legacy local rows explicitly enable the named adapter in the small profile.
        self.tmux("set-option", "-g", "@tmux-popups-profile", "small")
        path = self.registry()
        path.write_text("chat\tO\tg\tlocal chat\t80%\t80%\tscripts/tools/chat.sh\n")
        self.assertEqual(self.states()["chat"][9], "on")

    def test_disabled_row_reload_restores_prior_binding_and_honors_user_replacement(self):
        self.registry(deps="-")
        self.tmux("bind-key", "X", "display-message", "prior")
        self.load()
        self.registry(enabled="off", deps="-")
        self.load()
        self.assertIn("prior", self.tmux("list-keys", "-T", "prefix").stdout)
        self.assertNotIn("availability fixture", self.generated().read_text())
        self.assertEqual(self.states()["fixture"][9], "off")
        result = self.run_script("scripts/run-popup.sh", "fixture", check=False)
        self.assertIn("disabled", result.stderr)
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "on")
        self.load()
        self.assertIn('bind-key "X"', self.generated().read_text())
        self.tmux("bind-key", "X", "display-message", "user replacement")
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "off")
        self.load()
        self.assertIn("user replacement", self.tmux("list-keys", "-T", "prefix").stdout)

    def test_missing_alternative_dependencies_and_explicit_override(self):
        missing = "tmux_popups_missing_fixture"
        self.registry(deps=missing + "|tmux_popups_alternative_fixture")
        self.load()
        config = self.generated().read_text()
        self.assertIn("-availability fixture [missing:", config)
        self.assertNotIn('bind-key "X"', config)
        result = self.run_script("scripts/run-popup.sh", "fixture", check=False)
        self.assertEqual(result.returncode, 127)
        self.assertIn(missing, result.stderr)
        self.tmux("set-option", "-g", "@tmux-popups-availability", "hide-unavailable")
        self.load()
        self.assertNotIn("availability fixture", self.generated().read_text())
        alternative = self.stub("tmux_popups_alternative_fixture", "exit 0")
        self.load()
        self.assertIn('bind-key "X"', self.generated().read_text())
        self.attach()
        self.wait_until(lambda: self.tmux("list-clients", "-F", "#{client_name}").stdout.strip())
        client = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        origin = self.tmux("display-message", "-p", "-t", "fixture", "#{session_id} #{window_id} #{pane_id}").stdout.split()
        alternative.unlink()
        result = self.run_script("scripts/run-popup.sh", "fixture", "--launch", client,
                                 *origin, str(self.home), check=False)
        self.assertEqual(result.returncode, 127)
        self.wait_until(lambda: b"unavailable" in self.terminal_output)
        self.assertIn(missing, result.stderr)
        self.registry(deps="-")
        self.assertEqual(self.states()["fixture"][-1], "ok")
        self.assertEqual(self.run_script("scripts/run-popup.sh", "fixture", input="").returncode, 0)

    def test_effective_command_renames_and_custom_executable(self):
        self.registry(id="chat", command="scripts/tools/calc.sh")
        self.assertEqual(self.states()["chat"][10:], ["python3", "ok"])
        self.registry(command="scripts/tools/chat.sh")
        self.assertEqual(self.states()["fixture"][10], "ocq node")
        # A copied checkout preserves the plugin-relative executable contract.
        root = self.home / "checkout"
        shutil.copytree(launcher.ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        custom = root / "scripts/tools/custom.sh"
        custom.write_text("#!/bin/bash\nprintf custom-ok\n")
        custom.chmod(0o755)
        self.registry(id="chat", command="scripts/tools/custom.sh")
        result = subprocess.run([str(root / "scripts/run-popup.sh"), "chat"], env=self.env,
                                text=True, capture_output=True, check=True, timeout=12)
        self.assertEqual(result.stdout, "custom-ok")

    def test_editor_only_fallback_and_invalid_explicit_editor_shell(self):
        # Restrict PATH to fixture tools; vi is the only installed editor.
        isolated = self.home / "isolated-bin"
        isolated.mkdir()
        for name in ["bash", "dirname", "awk", "mktemp", "rm", "cut", "wc", "cat", "sleep", "date", "mkdir"]:
            (isolated / name).symlink_to(shutil.which(name))
        (isolated / "tmux").symlink_to(self.bin / "tmux")
        marker = self.home / "editor-call"
        vi = isolated / "vi"
        vi.write_text("#!/bin/bash\nprintf '%s' \"$1\" > " + shlex.quote(str(marker)) + "\n")
        vi.chmod(0o755)
        env = dict(self.env, PATH=str(isolated))
        env.pop("EDITOR", None)
        env.pop("SHELL", None)
        self.registry(command="scripts/tools/notes.sh")
        self.assertEqual(self.states(env)["fixture"][10:], ["editor", "ok"])
        self.run_script("scripts/run-popup.sh", "fixture", env=env)
        self.assertEqual(marker.read_text(), str(self.home / "Notes/daily") + "/" +
                         subprocess.check_output(["date", "+%F"], text=True).strip() + ".md")
        for variable, value, id in [("EDITOR", "absent-editor", "fixture"),
                                    ("SHELL", "/absent/shell", "shell")]:
            bad_env = dict(env, **{variable: value})
            self.assertTrue(self.states(bad_env)[id][-1].startswith("missing:"))
            result = self.run_script("scripts/run-popup.sh", id, env=bad_env, check=False)
            self.assertEqual(result.returncode, 127)
        self.assertEqual(self.states(env)["shell"][-1], "ok")
        result = self.run_script("scripts/run-popup.sh", "shell", env=env,
                                 input="printf shell-fallback; exit 0\n")
        self.assertEqual(result.stdout, "shell-fallback")

    def test_calendar_falls_back_when_khal_is_not_runnable(self):
        isolated = self.home / "calendar-bin"
        isolated.mkdir()
        for name in ["bash", "dirname", "awk", "mktemp", "rm", "cut", "wc", "cat", "sleep"]:
            (isolated / name).symlink_to(shutil.which(name))
        (isolated / "tmux").symlink_to(self.bin / "tmux")
        khal = isolated / "khal"
        khal.write_text("#!/bin/bash\nexit 1\n")
        khal.chmod(0o755)
        env = dict(self.env, PATH=str(isolated))
        self.registry(command="scripts/tools/calendar.sh")
        self.assertEqual(self.states(env)["fixture"][-1], "missing:khal|cal")
        cal = isolated / "cal"
        cal.write_text("#!/bin/bash\nprintf cal-fallback\n")
        cal.chmod(0o755)
        self.assertEqual(self.states(env)["fixture"][-1], "ok")
        result = self.run_script("scripts/run-popup.sh", "fixture", env=env, input="\n")
        self.assertIn("cal-fallback", result.stdout)

    def test_invalid_disabled_metadata_is_not_hidden_and_cache_is_preserved(self):
        self.load()
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        for enabled, deps in [("false", "auto"), ("off", "a||b"), ("off", "auto "),
                              ("off", "$(touch injected)"), ("", "auto")]:
            path = self.registry(enabled=enabled, deps=deps)
            result = self.run_script("scripts/generate-config.sh", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(str(path) + ":1:", result.stderr)
            self.assertEqual(before, self.generated().read_bytes())
            self.assertEqual(keys, self.tmux("list-keys").stdout)
        self.registry(enabled="off", deps="-")
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "false")
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertIn("invalid enabled override", result.stderr)
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "")
        result = self.run_script("scripts/generate-config.sh", check=False)
        self.assertIn("invalid enabled override", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
