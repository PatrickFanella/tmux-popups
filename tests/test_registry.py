#!/usr/bin/env python3
"""Registry rejection and last-good publication on disposable resources."""
import os
from pathlib import Path
import shlex
import subprocess
import unittest
import test_launcher as launcher


class RegistryTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    generated = launcher.LauncherTests.generated
    run_script = launcher.LauncherTests.run_script
    wait_until = launcher.LauncherTests.wait_until
    setUp = launcher.LauncherTests.setUp

    def registry(self, text, name="local.tsv"):
        path = self.home / name
        path.write_text(text)
        return dict(self.env, TMUX_POPUPS_LOCAL_REGISTRY=str(path))

    def row(self, **values):
        fields = dict(id="fixture", direct="X", menu="x", title="fixture",
                      width="70%", height="70%", command="-")
        fields.update(values)
        return "\t".join(fields.values()) + "\n"

    def test_invalid_rows_report_source_line_and_preserve_last_good(self):
        self.run_script("scripts/generate-config.sh")
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        cases = [
            ("fixture\tX\tx\ttitle\t70%\t70%\n", "7 TSV fields"),
            (self.row().rstrip() + "\textra\n", "7 TSV fields"),
            (self.row(id="bad;touch injected"), "unsupported popup id"),
            *[(self.row(**{field: ""}), "empty required field")
              for field in ["id", "direct", "menu", "title", "width", "height", "command"]],
            *[(self.row(width=dimension), "invalid dimension")
              for dimension in ["0", "0%", "101%", "-2", "80%%", "#{pane_width}", "2147483648", "9999999999999999999999"]],
            (self.row(height="wide"), "invalid dimension"),
            (self.row(direct="NotAKey"), "invalid key"),
            (self.row(menu="NotAKey"), "invalid key"),
            (self.row(command="missing tool; $(touch injected)"), "executable target"),
            (self.row(command="README.md"), "executable target"),
            (self.row(title="#(touch injected)"), "unsupported tmux format"),
        ]
        for row, message in cases:
            with self.subTest(row=row):
                env = self.registry("# comment\n\n" + row)
                for script, args in [("scripts/list-popups.sh", ["--tsv"]),
                                     ("scripts/generate-config.sh", [])]:
                    result = self.run_script(script, *args, env=env, check=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(str(self.home / "local.tsv") + ":3:", result.stderr)
                    self.assertIn(message, result.stderr)
                    self.assertEqual(result.stdout, "")
                self.assertEqual(self.generated().read_bytes(), before)
                self.assertEqual(self.tmux("list-keys").stdout, keys)
        self.tmux("source-file", "-n", str(self.generated()))
        self.run_script("scripts/apply-config.sh", str(self.generated()))
        self.assertFalse((self.home / "injected").exists())
        self.assertEqual(list(self.generated().parent.glob(".generated.*")), [])

    def test_effective_overrides_and_shortcut_collisions(self):
        env = self.registry(self.row() + self.row(title="replacement"))
        result = self.run_script("scripts/list-popups.sh", "--tsv", env=env)
        self.assertEqual(result.stdout.count("fixture\t"), 1)
        self.assertIn("replacement", result.stdout)
        self.run_script("scripts/generate-config.sh", env=env)
        before = self.generated().read_bytes()
        for row in [self.row(direct="Y"), self.row(menu="r"),
                    self.row(menu="R"), self.row(menu="q"), self.row(direct="Enter"),
                    self.row(direct="R"), self.row(direct="C-m"),
                    self.row() + self.row(id="second")]:
            with self.subTest(row=row):
                env = self.registry(row)
                result = self.run_script("scripts/generate-config.sh", env=env, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("duplicate", result.stderr)
                self.assertEqual(self.generated().read_bytes(), before)
        self.tmux("set-option", "-g", "@tmux-popups-enable-vscode", "on")
        env = self.registry(self.row(menu="v"))
        result = self.run_script("scripts/list-popups.sh", "--tsv", env=env, check=False)
        self.assertIn("built-in vscode", result.stderr)
        self.assertNotEqual(result.returncode, 0)
        # Bad overridden rows still fail instead of disappearing during merging.
        env = self.registry(self.row(width="bad") + self.row())
        self.assertNotEqual(self.run_script("scripts/list-popups.sh", "--tsv", env=env, check=False).returncode, 0)

    def test_target_invalid_source_keys_cannot_hide_behind_overrides(self):
        self.run_script("tmux-popups.tmux")
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        ownership = self.tmux("show-option", "-g").stdout
        for key in ["F63", "KPPlus"]:
            for field in ["direct", "menu"]:
                for override in [False, True]:
                    with self.subTest(key=key, field=field, override=override):
                        text = "# comment\n\n" + self.row(**{field: key})
                        if override:
                            text += self.row(title="valid replacement")
                        env = self.registry(text)
                        for script, args in [("scripts/list-popups.sh", ["--tsv"]),
                                             ("scripts/generate-config.sh", [])]:
                            result = self.run_script(script, *args, env=env, check=False)
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn(str(self.home / "local.tsv") + ":3:", result.stderr)
                            self.assertIn("fixture", result.stderr)
                            self.assertIn(field, result.stderr)
                            self.assertIn(key, result.stderr)
                            self.assertEqual(result.stdout, "")
                        self.assertEqual(self.generated().read_bytes(), before)
                        self.assertEqual(self.tmux("list-keys").stdout, keys)
                        self.assertEqual(self.tmux("show-option", "-g").stdout, ownership)
        self.assertEqual(list(self.generated().parent.glob(".generated.*")), [])
        self.tmux("source-file", "-n", str(self.generated()))
        self.run_script("scripts/apply-config.sh", str(self.generated()))

    def test_target_alias_collisions_keep_competing_source_locations(self):
        self.run_script("scripts/generate-config.sh")
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        for field in ["direct", "menu"]:
            with self.subTest(field=field):
                second = {"id": "second", "direct": "-", "menu": "s", field: "C-M-x"}
                env = self.registry("# comment\n\n" + self.row(**{field: "M-C-x"})
                                    + self.row(**second))
                for script, args in [("scripts/list-popups.sh", ["--tsv"]),
                                     ("scripts/generate-config.sh", [])]:
                    result = self.run_script(script, *args, env=env, check=False)
                    self.assertNotEqual(result.returncode, 0)
                    for location in [":3", ":4"]:
                        self.assertIn(str(self.home / "local.tsv") + location, result.stderr)
                    for detail in ["fixture", "second", field, "normalization"]:
                        self.assertIn(detail, result.stderr)
                    self.assertEqual(result.stdout, "")
                self.assertEqual(self.generated().read_bytes(), before)
                self.assertEqual(self.tmux("list-keys").stdout, keys)
        # A target-normalized collision can also belong to a built-in slot.
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-C-x")
        env = self.registry("# comment\n\n" + self.row(direct="C-M-x"))
        result = self.run_script("scripts/generate-config.sh", env=env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(self.home / "local.tsv") + ":3", result.stderr)
        self.assertIn("fixture", result.stderr)
        self.assertIn("built-in quick menu", result.stderr)
        self.assertEqual(self.generated().read_bytes(), before)
        self.assertEqual(list(self.generated().parent.glob(".generated.*")), [])

    def test_server_validation_failure_keeps_cache_and_binding_ownership(self):
        self.run_script("tmux-popups.tmux")
        before = self.generated().read_bytes()
        keys = self.tmux("list-keys").stdout
        ownership = self.tmux("show-option", "-g").stdout
        real = self.bin / "real-tmux"
        (self.bin / "tmux").rename(real)
        self.stub("tmux", 'if [[ "$1" == source-file && "$2" == *.stage ]]; then exit 23; fi\n'
                  + f'exec {shlex.quote(str(real))} "$@"')
        result = self.run_script("tmux-popups.tmux", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.generated().read_bytes(), before)
        self.assertEqual(self.tmux("list-keys").stdout, keys)
        self.assertEqual(self.tmux("show-option", "-g").stdout, ownership)
        self.assertEqual(list(self.generated().parent.glob(".generated.*")), [])

    def test_overlapping_writers_publish_complete_valid_configs(self):
        self.run_script("scripts/generate-config.sh")
        original = self.generated().read_bytes()
        real = self.bin / "real-tmux"
        (self.bin / "tmux").rename(real)
        ready = self.home / "ready"
        release = self.home / "release"
        self.stub("tmux", f'''if [[ "${{BLOCK_WRITER:-}}" == yes && "$1" == source-file && "$2" == -n ]]; then
  touch {shlex.quote(str(ready))}
  for ((i=0; i<500; i++)); do
    [[ -e {shlex.quote(str(release))} ]] && break
    sleep 0.01
  done
  [[ -e {shlex.quote(str(release))} ]] || exit 99
  [[ "${{FAIL_WRITER:-}}" != yes ]] || exit 24
fi
exec {shlex.quote(str(real))} "$@"''')
        for fail in [False, True]:
            with self.subTest(failing_writer=fail):
                ready.unlink(missing_ok=True)
                release.unlink(missing_ok=True)
                env_a = self.registry(self.row(title="writer A"), "a.tsv")
                env_a.update(BLOCK_WRITER="yes", FAIL_WRITER="yes" if fail else "no")
                writer = subprocess.Popen([str(launcher.ROOT / "scripts/generate-config.sh")],
                                          env=env_a, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.addCleanup(lambda p=writer: p.kill() if p.poll() is None else None)
                self.wait_until(ready.exists)
                self.assertEqual(self.generated().read_bytes(), original)
                env_b = self.registry(self.row(title="writer B"), "b.tsv")
                self.run_script("scripts/generate-config.sh", env=env_b)
                complete_b = self.generated().read_bytes()
                self.assertIn(b"writer B", complete_b)
                self.tmux("source-file", "-n", str(self.generated()))
                release.touch()
                stdout, stderr = writer.communicate(timeout=8)
                self.assertEqual(writer.returncode, 24 if fail else 0, stderr)
                self.assertEqual(stdout, b"")
                if fail:
                    self.assertEqual(self.generated().read_bytes(), complete_b)
                else:
                    self.assertIn(b"writer A", self.generated().read_bytes())
                self.run_script("scripts/apply-config.sh", str(self.generated()))
                original = self.generated().read_bytes()
                self.assertEqual(list(self.generated().parent.glob(".generated.*")), [])

    def test_dimensions_defaults_and_target_key_aliases(self):
        env = self.registry(self.row(width="100%", height="24"))
        self.run_script("scripts/generate-config.sh", env=env)
        for key, value in [("@tmux-popups-default-width", "101%"),
                           ("@tmux-popups-default-height", "0"),
                           ("@tmux-popups-menu-key", "NotAKey")]:
            before = self.generated().read_bytes()
            self.tmux("set-option", "-g", key, value)
            self.assertNotEqual(self.run_script("scripts/generate-config.sh", env=env, check=False).returncode, 0)
            self.assertEqual(self.generated().read_bytes(), before)
            self.tmux("set-option", "-gu", key)
        # tmux normalizes modifier order beyond the lexical alias checks.
        env = self.registry(self.row(direct="M-C-x") + self.row(id="second", direct="C-M-x", menu="s"))
        result = self.run_script("scripts/generate-config.sh", env=env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("normalization", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
