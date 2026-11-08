"""Search selects effective entries and dispatches after the picker closes."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import unittest
import test_launcher as launcher


class SearchTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def setUp(self):
        launcher.LauncherTests.setUp(self)
        self.tmux("set-option", "-g", "@tmux-popups-profile", "small")
        self.tmux("set-option", "-g", "@tmux-popups-availability", "show-disabled")
        self.env.update(FIXTURE=str(self.home), TMPDIR=str(self.home), FZF_DEFAULT_OPTS="")
        for name in ["FIXTURE", "TMPDIR", "FZF_DEFAULT_OPTS"]:
            self.tmux("set-environment", "-g", name, self.env[name])
        self.marker = self.home / "launched"
        code = "import os,json,pathlib; pathlib.Path("+repr(str(self.marker))+").write_text(json.dumps({k:os.environ.get('TMUX_POPUPS_'+k) for k in ['CLIENT','SESSION','WINDOW','PANE','DIRECTORY']}|{'cwd':os.getcwd()}))"
        self.probe = self.stub("probe", "exec python3 -c " + shlex.quote(code))
        self.registry = self.home / "search.tsv"
        self.registry.write_text(
            "search\tM-Space\t/\tsearch popups\t90%\t80%\tscripts/search-popups.sh\tcommand\tforeground\ton\t-\n"
            + "fixture\tX\tx\tFixture ' $(review_payload) α\t70%\t70%\t" + str(self.probe) + "\tcommand\tforeground\ton\t-\tabsolute\n"
            + "disabled\t-\t-\tdisabled fixture\t70%\t70%\t-\tpopup\tforeground\toff\t-\n"
            + "unavailable\t-\t-\tunavailable fixture\t70%\t70%\t-\tpopup\tforeground\ton\tmissing_search_tool\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(self.registry))
        self.client = self.attach()
        values = self.tmux("display-message", "-p", "-t", "fixture", "#{session_id}|#{window_id}|#{pane_id}").stdout.strip().split("|")
        client = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        self.directory = self.home / "origin ' \\; $(review_payload) #{session_name}\t\n\n"
        self.directory.mkdir()
        self.context = [client, *values, str(self.directory)]
        self.env['EXPECTED_DIRECTORY'] = str(self.directory)
        self.stub("fzf", '''cat > "$FIXTURE/seen-choices"
case "${PICK_STATUS:-0}" in 0) ;; *) exit "$PICK_STATUS";; esac
if [[ -n "${PICK_RESULT:-}" ]]; then printf '%s\\n' "$PICK_RESULT"; exit; fi
awk -F '\\t' '$1 == "fixture" {print; exit}' "$FIXTURE/seen-choices"''')

    def launch(self, check=True):
        return self.run_script("scripts/run-popup.sh", "search", "--launch", *self.context, check=check)

    def assert_origin(self):
        self.wait_until(self.marker.exists)
        expected = dict(zip(["CLIENT", "SESSION", "WINDOW", "PANE", "DIRECTORY"], self.context), cwd=str(self.directory))
        self.assertEqual(json.loads(self.marker.read_text()), expected)
        self.assertFalse(list(self.home.glob("tmux-popups-search.*")))

    def start(self):
        process = subprocess.Popen([str(launcher.ROOT / "scripts/run-popup.sh"), "search", "--launch", *self.context],
                                   cwd=self.home, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        return process

    def test_selection_labels_enabled_availability_and_exact_context(self):
        self.launch()
        self.assert_origin()
        choices = (self.home / "seen-choices").read_text()
        self.assertIn("Fixture ' $(review_payload) α\tprefix:X/menu:x\tcommand\tok", choices)
        self.assertIn("missing:missing_search_tool", choices)
        self.assertNotIn("disabled fixture", choices)
        self.assertNotIn("search popups", choices)
        self.marker.unlink()
        self.tmux("set-option", "-g", "@tmux-popups-availability", "hide-unavailable")
        self.launch()
        self.assert_origin()
        self.assertNotIn("unavailable fixture", (self.home / "seen-choices").read_text())

    def test_cancel_no_match_error_and_unlisted_selection(self):
        for status in ["1", "130", "2"]:
            self.tmux("set-environment", "-g", "PICK_STATUS", status)
            result = self.launch(check=False)
            self.assertEqual(result.returncode, 0 if status != "2" else 1, result.stderr)
            self.assertFalse(self.marker.exists())
            self.assertFalse(list(self.home.glob("tmux-popups-search.*")))
        self.tmux("set-environment", "-g", "PICK_STATUS", "0")
        for selected in ["disabled", "not-listed", "fixture\nhelp"]:
            self.tmux("set-environment", "-g", "PICK_RESULT", selected)
            result = self.launch(check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.marker.exists())
            self.assertFalse(list(self.home.glob("tmux-popups-search.*")))

    def test_selected_popup_opens_after_picker_closes(self):
        text = self.registry.read_text().replace("\tcommand\tforeground\ton\t-\tabsolute", "\tpopup\tforeground\ton\t-\tabsolute")
        self.registry.write_text(text)
        result = self.launch()
        self.assert_origin()
        self.assertNotIn("popup", result.stderr)

    def test_selected_unavailable_entry_uses_dispatcher_rejection(self):
        self.tmux("set-environment", "-g", "PICK_RESULT", "unavailable")
        result = self.launch(check=False)
        self.assertEqual(result.returncode, 127)
        self.assertIn("missing:missing_search_tool", result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertFalse(list(self.home.glob("tmux-popups-search.*")))

    def test_empty_list_returns_without_picker_or_dispatch(self):
        rows = self.run_script("scripts/list-popups.sh", "--tsv").stdout.splitlines()
        for row in rows:
            id = row.split("\t")[0]
            if id != "search": self.tmux("set-option", "-g", f"@tmux-popups-{id}-enabled", "off")
        self.launch()
        self.assertFalse(self.marker.exists())
        self.assertFalse((self.home / "seen-choices").exists())

    def test_native_fallback_preserves_literal_context(self):
        (self.bin / "fzf").unlink()
        # Keep required standard commands, excluding the host's optional fzf.
        for command in ["bash", "dirname", "awk", "mktemp", "cat", "rm", "sleep", "grep", "cut", "tr", "sed", "wc", "sort", "mv", "od", "python3"]:
            if not (self.bin / command).exists(): (self.bin / command).symlink_to(shutil.which(command))
        self.env['PATH'] = str(self.bin)
        self.tmux("set-environment", "-g", "PATH", str(self.bin))
        process = self.start()
        self.wait_until(lambda: b"fzf unavailable" in self.terminal_output)
        os.write(self.client, b"x")
        _, error = process.communicate(timeout=8)
        self.assertEqual(process.returncode, 0, error)
        self.assert_origin()

    def test_real_fzf_input_and_popup_transition_when_installed(self):
        real_fzf = shutil.which("fzf", path=os.environ['PATH'])
        if not real_fzf: self.skipTest("optional real fzf is not installed")
        (self.bin / "fzf").unlink()
        (self.bin / "fzf").symlink_to(real_fzf)
        process = self.start()
        self.wait_until(lambda: b"Popup>" in self.terminal_output)
        self.terminal_output.clear()
        os.write(self.client, b"Fixture")
        self.wait_until(lambda: b"Fixture" in self.terminal_output)
        os.write(self.client, b"\r")
        _, error = process.communicate(timeout=8)
        self.assertEqual(process.returncode, 0, error)
        self.assert_origin()
