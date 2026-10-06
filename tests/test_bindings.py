#!/usr/bin/env python3
"""Binding ownership and restoration on isolated tmux servers."""
import re
import shlex
import shutil
import unittest
import test_launcher as launcher


class BindingTests(unittest.TestCase):
    setUp = launcher.LauncherTests.setUp
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    run_script = launcher.LauncherTests.run_script
    tmux = launcher.LauncherTests.tmux
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load

    def bindings(self):
        result = {}
        for line in self.tmux("list-keys", "-T", "prefix").stdout.splitlines():
            match = re.search(r"-T prefix\s+(\S+)\s+", line)
            if match:
                result[match[1]] = line
        return result

    def test_reconcile_changed_disabled_removed_and_replaced_keys(self):
        self.tmux("bind-key", "-r", "-N", "saved owner note", "g", "display-message", "original g")
        self.tmux("bind-key", "Q", "display-message", "unrelated")
        before = self.bindings()
        registry = self.home / "local.tsv"
        registry.write_text("fixture\tX\tx\tfixture\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        self.load()
        self.tmux("bind-key", "X", "display-message", "replacement X")
        self.tmux("bind-key", "Y", "display-message", "replacement Y")
        replaced = self.bindings()
        registry.write_text("lazygit\t-\ty\tlazygit\t80%\t80%\tscripts/tools/lazygit.sh\n")
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        self.tmux("set-option", "-g", "@tmux-popups-reload-key", "M-r")
        self.load()
        after = self.bindings()
        self.assertEqual(after["g"], before["g"])
        self.assertEqual(after.get("R"), before.get("R"))
        self.assertEqual(after.get("Enter"), before.get("Enter"))
        self.assertEqual(after["Q"], before["Q"])
        self.assertEqual(after["X"], replaced["X"])
        self.assertEqual(after["Y"], replaced["Y"])
        self.assertIn("M-m", after)
        self.assertIn("M-r", after)
        self.load()
        self.assertEqual(after, self.bindings())

    def test_changed_entry_key_restores_previous_and_removes_unowned_slot(self):
        registry = self.home / "local.tsv"
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        registry.write_text("fixture\tX\tx\tfixture\t70%\t70%\t-\n")
        before = self.bindings()
        self.load()
        registry.write_text("fixture\tM-x\tx\tfixture changed\t70%\t70%\t-\n")
        self.load()
        after = self.bindings()
        self.assertEqual(after.get("X"), before.get("X"))
        self.assertIn("M-x", after)
        registry.write_text("")
        self.load()
        self.assertNotIn("M-x", self.bindings())

    def test_active_intervening_unbind_is_preserved(self):
        self.load()
        self.tmux("unbind-key", "Y")
        self.load()
        self.assertNotIn("Y", self.bindings())
        self.load()
        self.assertNotIn("Y", self.bindings())

    def ownership(self):
        return [
            line for line in self.tmux("show-options", "-g").stdout.splitlines()
            if line.startswith("@tmux-popups-owned-")
        ]

    def test_restore_notes_repeat_and_other_tables(self):
        note = 'saved "owner" \\ $HOME; $(touch note-injection)\nnext\tline'
        self.tmux("bind-key", "-r", "-N", note, "g", "display-message", "original g")
        self.tmux("bind-key", "-T", "root", "-r", "-N", "root note", "g", "display-message", "root g")
        self.tmux("bind-key", "-T", "custom", "-N", "custom note", "g", "display-message", "custom g")
        root = self.tmux("list-keys", "-T", "root").stdout
        custom = self.tmux("list-keys", "-T", "custom").stdout
        self.load()
        registry = self.home / "local.tsv"
        registry.write_text("lazygit\t-\ty\tlazygit\t80%\t80%\tscripts/tools/lazygit.sh\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        self.load()
        if "-F " in self.tmux("list-commands", "list-keys").stdout:
            notes = self.tmux("list-keys", "-T", "prefix", "-F", "#{key_string}|#{key_repeat}|#{key_note}").stdout
            self.assertIn("g|1|" + note + "\n", notes)
        else:
            notes = self.tmux("list-keys", "-N", "-T", "prefix", "g").stdout
            self.assertEqual("g " + note + "\n", notes)
        self.assertIn('display-message "original g"', self.bindings()["g"])
        self.assertEqual(root, self.tmux("list-keys", "-T", "root").stdout)
        self.assertEqual(custom, self.tmux("list-keys", "-T", "custom").stdout)
        self.assertFalse((self.home / "note-injection").exists())

    def test_alias_and_duplicate_slot_restore_once(self):
        self.tmux("bind-key", "-N", "prior tab", "Tab", "display-message", "prior tab")
        before = self.bindings()
        registry = self.home / "local.tsv"
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        registry.write_text("fixture\tC-i\tx\tfixture\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "Tab")
        self.load()
        self.load()
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        registry.write_text("")
        self.load()
        self.assertEqual(before.get("Tab"), self.bindings().get("Tab"))
        self.assertIn("prior tab", self.tmux("list-keys", "-N", "-T", "prefix").stdout)

    def test_invalid_key_does_not_remove_old_bindings_or_state(self):
        self.load()
        before, owned = self.bindings(), self.ownership()
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "not-a-tmux-key")
        self.tmux("set-option", "-g", "@tmux-popups-reload-key", "M-r")
        result = self.run_script("tmux-popups.tmux", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown key", result.stdout + result.stderr)
        self.assertEqual(before, self.bindings())
        self.assertEqual(owned, self.ownership())
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        self.load()  # Failed validation releases the lock.
        self.assertNotIn("tmux-popups-stage-", self.tmux("list-keys").stdout)

    def test_partial_apply_failure_rolls_back_bindings_and_state(self):
        self.load()
        before, owned = self.bindings(), self.ownership()
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        self.tmux("set-option", "-g", "@tmux-popups-reload-key", "M-r")
        # Apply one real plan command, then simulate a failed tmux invocation.
        real = f"{shlex.quote(launcher.REAL_TMUX)} -S {shlex.quote(str(self.socket))}"
        self.stub("tmux", f'''if [[ "$1" == source-file && "$#" == 2 && "$2" == */plan ]]; then
  : > "$2.partial"
  while IFS= read -r line; do
    printf '%s\\n' "$line" >> "$2.partial"
    [[ "$line" == bind-key* || "$line" == unbind-key* ]] && break
  done < "$2"
  {real} source-file "$2.partial"
  exit 73
fi
exec {real} "$@"''')
        result = self.run_script("tmux-popups.tmux", check=False)
        self.assertEqual(result.returncode, 73)
        self.assertEqual(before, self.bindings())
        self.assertEqual(owned, self.ownership())
        self.stub("tmux", f'exec {real} "$@"')
        self.load()
        self.assertIn("M-m", self.bindings())

    def test_ownership_survives_new_checkout_and_cache(self):
        self.tmux("bind-key", "-r", "-N", "prior g", "g", "display-message", "prior g")
        before = self.bindings()
        self.load()
        checkout = self.home / "copy with 'quote';$(touch checkout-injection)\\;tail"
        shutil.copytree(launcher.ROOT, checkout, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        cache = self.home / "new cache 'quote'"
        registry = self.home / "local.tsv"
        registry.write_text("lazygit\t-\ty\tlazygit\t80%\t80%\tscripts/tools/lazygit.sh\n")
        env = dict(self.env, XDG_CACHE_HOME=str(cache), TMUX_POPUPS_LOCAL_REGISTRY=str(registry))
        self.run_script(str(checkout / "tmux-popups.tmux"), env=env)
        self.assertEqual(before["g"], self.bindings()["g"])
        self.assertIn("copy with", self.bindings()["Y"])
        self.assertNotIn(str(launcher.ROOT), self.bindings()["Y"])
        owned, bindings = self.ownership(), self.bindings()
        self.run_script(str(checkout / "tmux-popups.tmux"), env=env)
        self.assertEqual(bindings, self.bindings())
        self.assertEqual(owned, self.ownership())
        self.assertFalse((self.home / "checkout-injection").exists())

    def test_printable_special_keys_restore_literal_notes(self):
        keys = ["$", "#", '"', "\\", "\\;"]
        for key in keys:
            self.tmux("bind-key", "-r", "-N", "prior " + key, key, "display-message", "prior")
        before = self.bindings()
        for key in keys:
            self.tmux("set-option", "-g", "@tmux-popups-menu-key", key)
            self.load()
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        self.load()
        after = self.bindings()
        for key, line in before.items():
            if "display-message prior" in line:
                self.assertEqual(line, after[key])
        notes = self.tmux("list-keys", "-N", "-T", "prefix").stdout
        for key in keys:
            self.assertIn("prior " + key.replace("\\;", ";"), notes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
