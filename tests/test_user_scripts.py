"""User executable and argv contract on disposable files, sockets and PTYs."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import unittest
import test_launcher as launcher


class UserScriptTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    setUp = launcher.LauncherTests.setUp
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def script(self, directory=None):
        directory = directory or self.home / "outside user's scripts"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "record user's argv"
        self.marker = self.home / "record.json"
        code = "import sys,json,pathlib; pathlib.Path(" + repr(str(self.marker)) + ").write_text(json.dumps(sys.argv[1:]))"
        path.write_text("#!/bin/bash\nexec " + shlex.quote(shutil.which("python3")) + " -c " + shlex.quote(code) + ' "$@"\n')
        path.chmod(0o755)
        return path

    def registry(self, command, kind="absolute", args="-", mode="command", completion="foreground"):
        path = self.home / "local user's entries.tsv"
        path.write_text("\t".join(["fixture", "X", "x", "user script", "61", "17", str(command),
                                   mode, completion, "on", "auto", kind, args]) + "\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(path))
        return path

    def test_absolute_argv_cli_and_each_launcher_mode(self):
        path = self.script()
        args = ["two words", "it's literal", "", "$(touch injected)", "$HOME", "~", "a\nb\tc", "\\", "#{pane_id}"]
        self.registry(path, args=json.dumps(args))
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(json.loads(self.marker.read_text()), args)
        client = self.attach()
        for mode, completion in [("popup", "foreground"), ("window", "foreground"),
                                 ("command", "foreground"), ("command", "background")]:
            self.registry(path, args=json.dumps(args), mode=mode, completion=completion)
            self.load()
            for source in ("direct", "menu"):
                with self.subTest(mode=mode, completion=completion, source=source):
                    self.marker.unlink(missing_ok=True)
                    self.tmux("select-window", "-t", "fixture:0")
                    if source == "direct":
                        os.write(client, b"\x02X")
                    else:
                        self.client_output[client].clear()
                        os.write(client, b"\x02\r")
                        self.wait_until(lambda: b"Quick Menu" in self.client_output[client])
                        os.write(client, b"x")
                    self.wait_until(self.marker.exists)
                    self.assertEqual(json.loads(self.marker.read_text()), args)
        self.assertFalse((self.home / "injected").exists())
        self.assertEqual(list(self.base.rglob("tmux-popups-argv.*")), [])

    def test_user_directory_default_option_environment_and_home_expansion(self):
        default = Path(self.env["XDG_CONFIG_HOME"]) / "tmux-popups/scripts"
        path = self.script(default)
        self.registry(path.name, "user", '["default"]')
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(json.loads(self.marker.read_text()), ["default"])
        option = self.script(self.home / "option user's directory")
        explicit = self.script(self.home / "explicit user's directory")
        self.tmux("set-option", "-g", "@tmux-popups-user-script-directory", "~/option user's directory")
        option.write_text("#!/bin/bash\nprintf option > " + shlex.quote(str(self.marker)) + "\n")
        self.registry(option.name, "user")
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(self.marker.read_text(), "option")
        env = dict(self.env, TMUX_POPUPS_USER_SCRIPT_DIRECTORY="~/explicit user's directory")
        self.run_script("scripts/run-popup.sh", "fixture", env=env)
        self.assertEqual(json.loads(self.marker.read_text()), [])
        self.registry("~/explicit user's directory/" + explicit.name)
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(json.loads(self.marker.read_text()), [])
        self.registry("$HOME/explicit user's directory/" + explicit.name)
        result = self.run_script("scripts/list-popups.sh", "--tsv", check=False)
        self.assertIn("absolute target", result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_invalid_targets_metadata_and_shell_opt_in_preserve_cache(self):
        path = self.script()
        self.registry(path)
        self.load()
        cache = self.generated().read_bytes()
        bindings = self.tmux("list-keys").stdout
        for command, kind, args in [(path.parent / "missing", "absolute", "-"),
                                    (launcher.ROOT / "README.md", "absolute", "-"),
                                    (path, "unknown", "-"), (path, "user", "-"),
                                    (path, "plugin", "-"), (path, "absolute", '[1]'),
                                    (path, "absolute", '["\\u0000"]'), (path, "absolute", '["\\ud800"]'),
                                    (path, "absolute", '{}'), (path, "absolute", 'not json'),
                                    ("echo unsafe", "shell", '[]')]:
            with self.subTest(command=command, kind=kind, args=args):
                self.registry(command, kind, args)
                result = self.run_script("scripts/generate-config.sh", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(":1:", result.stderr)
                self.assertEqual(self.generated().read_bytes(), cache)
                self.assertEqual(self.tmux("list-keys").stdout, bindings)
        self.registry("printf opted-in > " + shlex.quote(str(self.marker)), "shell")
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(self.marker.read_text(), "opted-in")
        # Removed executables fail again at dispatch, including ignore policy.
        self.registry(path)
        self.load()
        path.chmod(0o644)
        result = self.run_script("scripts/run-popup.sh", "fixture", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not executable", result.stderr)

    def test_plugin_arguments_legacy_outputs_and_registry_precedence(self):
        marker = self.home / "plugin-args"
        self.stub("yazi", "printf '%s\\0' \"$@\" > " + shlex.quote(str(marker)))
        local = self.registry("scripts/tools/yazi.sh", "plugin", '["two words", "apostrophe\'s"]')
        self.run_script("scripts/run-popup.sh", "fixture")
        self.assertEqual(marker.read_bytes(), b"two words\0apostrophe's\0")
        for output, count in [("--tsv", 9), ("--deps-tsv", 11), ("--state-tsv", 12), ("--execution-tsv", 14)]:
            rows = self.run_script("scripts/list-popups.sh", output).stdout.splitlines()
            self.assertTrue(all(len(row.split("\t")) == count for row in rows))
        explicit = self.home / "override.tsv"
        explicit.write_text(local.read_text().replace('["two words", "apostrophe\'s"]', '["override"]'))
        self.run_script("scripts/run-popup.sh", "fixture", env=dict(self.env, TMUX_POPUPS_LOCAL_REGISTRY=str(explicit)))
        self.assertEqual(marker.read_bytes(), b"override\0")
        # Existing 7/8/9/11-column rows still resolve to the same launch values.
        for count in (7, 8, 9, 11):
            fields = ["fixture", "X", "x", "legacy", "61", "17", "scripts/tools/yazi.sh", "window", "foreground", "on", "auto"]
            local.write_text("\t".join(fields[:count]) + "\n")
            row = next(row for row in self.run_script("scripts/list-popups.sh", "--tsv").stdout.splitlines() if row.startswith("fixture\t"))
            self.assertEqual(row.split("\t")[6:], [fields[6], "window", "foreground"])

    def test_plugin_update_and_reload_preserve_user_bytes(self):
        path = self.script(Path(self.env["XDG_CONFIG_HOME"]) / "tmux-popups/scripts")
        registry = self.registry(path.name, "user", '["after update"]')
        before = {file: file.read_bytes() for file in (path, registry)}
        install = self.base / "installed plugin"
        shutil.copytree(launcher.ROOT, install, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        def reload():
            subprocess.run([str(install / "scripts/generate-config.sh")], env=self.env,
                           cwd=self.home, capture_output=True, check=True, timeout=12)
            subprocess.run([str(install / "scripts/run-popup.sh"), "fixture"], env=self.env,
                           cwd=self.home, capture_output=True, check=True, timeout=12)
        reload()
        shutil.rmtree(install)
        shutil.copytree(launcher.ROOT, install, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        reload()
        self.assertEqual(json.loads(self.marker.read_text()), ["after update"])
        self.assertEqual({file: file.read_bytes() for file in before}, before)
