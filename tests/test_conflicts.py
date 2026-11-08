"""Conflict policy and provenance on private tmux sockets."""
import unittest
import test_bindings as binding_tests
import test_launcher as launcher


class ConflictTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    generated = launcher.LauncherTests.generated
    load = launcher.LauncherTests.load
    bindings = binding_tests.BindingTests.bindings
    ownership = binding_tests.BindingTests.ownership

    def setUp(self):
        launcher.LauncherTests.setUp(self)
        self.tmux("set-option", "-gu", "@tmux-popups-conflicts")
        self.registry = self.home / "owner ' registry.tsv"
        self.registry.write_text("# local fixture\nfixture\tX\tx\tfixture\t70%\t70%\t-\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(self.registry))
        for key in ["X", "Enter", "R"]:
            self.tmux("bind-key", "-r", "-N", "original note", key,
                      "display-message", "original " + key)
        self.original = self.bindings()

    def test_default_skip_preserves_all_conflicts_and_reports_source(self):
        result = self.run_script("tmux-popups.tmux")
        for key in ["X", "Enter", "R"]:
            self.assertEqual(self.bindings()[key], self.original[key])
        self.assertIn("skip conflict", result.stderr)
        self.assertIn(str(self.registry) + ":2 (fixture)", result.stderr)
        self.assertIn("built-in quick menu", result.stderr)
        self.assertIn("built-in reload", result.stderr)
        self.assertIn("original X", result.stderr)
        self.assertNotIn("owned", self.tmux("list-keys", "-N", "-T", "prefix", "X").stdout)
        self.tmux("unbind-key", "X")
        self.load()
        self.assertIn("run-popup.sh fixture", self.bindings()["X"])
        self.load()
        self.assertIn("run-popup.sh fixture", self.bindings()["X"])
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "off")
        self.load()
        self.assertNotIn("X", self.bindings())

    def test_warn_replaces_with_diagnostics_and_restores_on_disable(self):
        self.tmux("set-option", "-g", "@tmux-popups-conflicts", "warn")
        result = self.run_script("tmux-popups.tmux")
        self.assertIn("warn conflict", result.stderr)
        self.assertIn(str(self.registry) + ":2 (fixture)", result.stderr)
        self.assertIn("run-popup.sh fixture", self.bindings()["X"])
        notes = self.tmux("list-keys", "-N", "-T", "prefix", "X").stdout
        self.assertIn(str(self.registry) + ":2 (fixture)", notes)
        self.tmux("set-option", "-g", "@tmux-popups-fixture-enabled", "off")
        self.tmux("set-option", "-g", "@tmux-popups-menu-key", "M-m")
        self.tmux("set-option", "-g", "@tmux-popups-reload-key", "M-r")
        self.load()
        for key in ["X", "Enter", "R"]:
            self.assertEqual(self.bindings()[key], self.original[key])

    def test_replace_and_later_user_replacement_remain_protected(self):
        self.tmux("set-option", "-g", "@tmux-popups-conflicts", "replace")
        result = self.run_script("tmux-popups.tmux")
        self.assertNotIn("conflict", result.stderr)
        self.assertIn("run-popup.sh fixture", self.bindings()["X"])
        self.tmux("bind-key", "X", "display-message", "later owner")
        changed = self.bindings()["X"]
        self.load()
        self.assertEqual(self.bindings()["X"], changed)
        result = self.run_script("scripts/apply-config.sh", "--explain", str(self.generated()))
        self.assertIn("preserve later user change", result.stdout)
        self.assertIn("later owner", result.stdout)
        self.registry.write_text("")
        self.load()
        self.assertEqual(self.bindings()["X"], changed)

    def test_explanation_does_not_change_cache_bindings_or_ownership(self):
        self.run_script("scripts/generate-config.sh")
        before = self.bindings(), self.ownership(), self.generated().read_bytes()
        result = self.run_script("scripts/apply-config.sh", "--explain", str(self.generated()))
        self.assertIn("skip conflict", result.stderr)
        self.assertIn("original X", result.stderr)
        self.assertIn(str(self.registry) + ":2 (fixture)", result.stderr)
        self.assertEqual(before, (self.bindings(), self.ownership(), self.generated().read_bytes()))
        self.assertNotIn("tmux-popups-stage-", self.tmux("list-keys").stdout)

    def test_invalid_policy_leaves_last_good_cache_and_bindings(self):
        self.load()
        before = self.bindings(), self.ownership(), self.generated().read_bytes()
        self.tmux("set-option", "-g", "@tmux-popups-conflicts", "unknown")
        result = self.run_script("tmux-popups.tmux", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid binding conflict policy", result.stderr)
        self.assertEqual(before, (self.bindings(), self.ownership(), self.generated().read_bytes()))

    def test_reserved_menu_conflicts_reject_every_policy(self):
        self.load()
        before = self.bindings(), self.ownership(), self.generated().read_bytes()
        self.registry.write_text("fixture\tX\tq\treserved conflict\t70%\t70%\t-\n")
        for policy in ["skip", "warn", "replace"]:
            with self.subTest(policy=policy):
                self.tmux("set-option", "-g", "@tmux-popups-conflicts", policy)
                result = self.run_script("tmux-popups.tmux", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("built-in Exit", result.stderr)
                self.assertEqual(before, (self.bindings(), self.ownership(), self.generated().read_bytes()))

    def test_origin_output_keeps_legacy_layouts_and_override_location(self):
        rows = self.run_script("scripts/list-popups.sh", "--origin-tsv").stdout.splitlines()
        row = next(r.split("\t") for r in rows if r.startswith("fixture\t"))
        self.assertEqual(len(row), 15)
        self.assertEqual(row[-1], str(self.registry) + ":2")
        for flag, count in [("--tsv", 9), ("--deps-tsv", 11),
                            ("--state-tsv", 12), ("--execution-tsv", 14)]:
            rows = self.run_script("scripts/list-popups.sh", flag).stdout.splitlines()
            self.assertTrue(all(len(r.split("\t")) == count for r in rows))
