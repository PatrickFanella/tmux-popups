#!/usr/bin/env python3
"""Chat provider/clipboard fixtures never contact a service or system clipboard."""
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import unittest

import test_launcher

ROOT = Path(__file__).resolve().parents[1]


class ChatTests(test_launcher.LauncherTests):
    def setUp(self):
        super().setUp()
        self.env.update(FIXTURE=str(self.home), TMPDIR=str(self.home), NO_COLOR="1")
        self.stub("clear", "exit 0")
        self.stub("wl-copy", 'cat > "$FIXTURE/copied"; exit "${COPY_STATUS:-0}"')
        self.stub("ocq", '''printf '%s\\n' "$@" >> "$FIXTURE/args"
if [[ "${SLOW:-}" == yes ]]; then
  echo $$ > "$FIXTURE/request-pid"
  exec /bin/sleep 60
fi
if [[ "${PROVIDER_STATUS:-0}" != 0 ]]; then exit "$PROVIDER_STATUS"; fi
cat "$FIXTURE/response"''')
        self.response = self.home / "response"
        self.response.write_text(json.dumps(dict(sessionID="session-1", text="answer\n\n")))

    def chat(self, text, **options):
        result = self.run_script("scripts/tools/chat.sh", input=text, check=False,
                                 env=dict(self.env, **options))
        self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))
        self.assertNotIn("unbound variable", result.stderr)
        self.assertNotIn("SyntaxError", result.stderr)
        return result

    def test_success_continuation_copy_and_quit(self):
        result = self.chat("first\n\nsecond\nc\n/quit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("Assistant"), 2)
        self.assertEqual((self.home / "copied").read_bytes(), b"answer\n\n")
        self.assertEqual((self.home / "args").read_text().splitlines(),
                         ["--json", "--model", "openai/gpt-5.4-mini", "first",
                          "--json", "--model", "openai/gpt-5.4-mini", "--session", "session-1", "second"])

    def test_malformed_missing_empty_and_nonstring_response(self):
        for response in ["not JSON", "null", "{}", '{"sessionID":"s"}',
                         '{"sessionID":"s","text":" "}',
                         '{"sessionID":3,"text":"bad"}']:
            with self.subTest(response=response):
                self.response.write_text(response)
                result = self.chat("hello\n/quit\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("invalid or empty response", result.stderr)
                self.assertNotIn("Assistant", result.stdout)

    def test_provider_failure_and_copy_failure_are_visible(self):
        result = self.chat("hello\n/quit\n", PROVIDER_STATUS="23")
        self.assertIn("ocq failed (status 23)", result.stderr)
        self.assertNotIn("Assistant", result.stdout)
        for action in ["c", "cq"]:
            result = self.chat(f"hello\n{action}\n/quit\n", COPY_STATUS="42")
            self.assertIn("Copy failed", result.stderr)
            self.assertNotIn("Copied.", result.stdout)
        result = self.chat("hello\ncq\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / "copied").read_bytes(), b"answer\n\n")

    def test_invalid_reply_preserves_last_valid_session(self):
        self.stub("ocq", '''printf '%s\\n' "$@" >> "$FIXTURE/args"
if [[ "${!#}" == broken ]]; then printf 'invalid'; else cat "$FIXTURE/response"; fi''')
        result = self.chat("first\n\nbroken\nthird\nq\n")
        self.assertEqual(result.stdout.count("Assistant"), 2)
        self.assertEqual((self.home / "args").read_text().count("session-1"), 2)
        self.assertIn("invalid or empty response", result.stderr)

    def test_quit_and_missing_provider(self):
        for text in ["q\n", "/quit\n", "\x1b[200~/quit\x1b[201~\r\n"]:
            result = self.chat(text)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((self.home / "args").exists())
        (self.bin / "ocq").unlink()
        result = self.chat("hello\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ocq not found", result.stderr)

    def test_dispatcher_popup_quit_returns_success(self):
        self.tmux("set-environment", "-g", "FIXTURE", str(self.home))
        self.tmux("set-environment", "-g", "TMPDIR", str(self.home))
        client = self.attach()
        target = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        ids = self.tmux("display-message", "-p", "-t", "fixture",
                        "#{session_id}|#{window_id}|#{pane_id}").stdout.strip().split("|")
        for copy in [False, True]:
            self.terminal_output.clear()
            process = subprocess.Popen([str(ROOT / "scripts/run-popup.sh"), "chat", "--launch",
                                        target, *ids, str(self.home)], env=self.env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            self.addCleanup(lambda process=process: process.poll() is None and process.terminate())
            self.wait_until(lambda: b"You" in self.terminal_output)
            if copy:
                os.write(client, b"qualification\r")
                self.wait_until(lambda: b"answer" in self.terminal_output)
            os.write(client, b"cq\r" if copy else b"q\r")
            _, error = process.communicate(timeout=3)
            self.assertEqual(process.returncode, 0, error)
            if copy: self.assertEqual((self.home / "copied").read_bytes(), b"answer\n\n")
            self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))

    def test_successful_provider_stops_stubborn_owned_descendant(self):
        marker = self.home / "descendant"
        child_code = "import os,pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(" + repr(str(marker)) + ").write_text(str(os.getpid())); time.sleep(60)"
        provider = self.home / "provider.py"
        provider.write_text("import pathlib,subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c'," + repr(child_code) + "])\nwhile not pathlib.Path(" + repr(str(marker)) + ").exists(): time.sleep(.01)\nprint(" + repr(self.response.read_text()) + ")\n")
        self.stub("ocq", "exec python3 " + shlex.quote(str(provider)))
        def cleanup():
            if marker.exists():
                try: os.kill(int(marker.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass
        self.addCleanup(cleanup)
        result = self.chat("hello\nq\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        pid = int(marker.read_text())
        self.wait_until(lambda: not Path(f"/proc/{pid}/stat").exists() or
                        Path(f"/proc/{pid}/stat").read_text().split()[2] == "Z")

    def test_missing_json_runtime_is_reported(self):
        for command in ["bash", "dirname"]:
            (self.bin / command).symlink_to("/usr/bin/" + command)
        result = self.run_script("scripts/tools/chat.sh", input="", check=False,
                                 env=dict(self.env, PATH=str(self.bin)))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("node not found", result.stderr)
        self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))

    def test_term_reaps_owned_request_and_files(self):
        process = subprocess.Popen([str(ROOT / "scripts/tools/chat.sh")],
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, env=dict(self.env, SLOW="yes"))
        self.addCleanup(lambda: process.poll() is None and process.kill())
        try:
            process.stdin.write(b"hello\n")
            process.stdin.flush()
            marker = self.home / "request-pid"
            self.wait_until(marker.exists)
            pid = int(marker.read_text())
            process.terminate()
            process.wait(timeout=3)
            self.assertEqual(process.returncode, 143)
            self.assertFalse(Path(f"/proc/{pid}").exists())
            self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))
        finally:
            process.stdin.close()

    def test_attached_popup_input_copy_quit_and_ctrl_c(self):
        self.tmux("set-environment", "-g", "FIXTURE", str(self.home))
        self.tmux("set-environment", "-g", "TMPDIR", str(self.home))
        client = self.attach()
        target = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        def launch():
            return subprocess.Popen([test_launcher.REAL_TMUX, "-S", str(self.socket),
                                     "display-popup", "-E", "-c", target, "-w", "95%", "-h", "80%",
                                     shlex.quote(str(ROOT / "scripts/tools/chat.sh"))],
                                    env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        popup = launch()
        self.addCleanup(lambda: popup.poll() is None and popup.terminate())
        self.wait_until(lambda: b"You" in self.terminal_output)
        os.write(client, b"hello from popup\r")
        self.wait_until(lambda: b"answer" in self.terminal_output)
        os.write(client, b"cq\r")
        popup.wait(timeout=3)
        self.assertNotIn(b"unbound variable", self.terminal_output)
        self.assertEqual((self.home / "copied").read_bytes(), b"answer\n\n")
        self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))
        self.tmux("set-environment", "-g", "SLOW", "yes")
        self.terminal_output.clear()
        popup = launch()
        self.addCleanup(lambda: popup.poll() is None and popup.terminate())
        self.wait_until(lambda: b"You" in self.terminal_output)
        os.write(client, b"slow\r")
        marker = self.home / "request-pid"
        self.wait_until(marker.exists)
        pid = int(marker.read_text())
        os.write(client, b"\x03")
        popup.wait(timeout=3)
        self.wait_until(lambda: not Path(f"/proc/{pid}").exists())
        self.assertFalse(list(self.home.glob("tmux-popups-chat.*")))


def load_tests(loader, tests, pattern):
    names = [name for name in ChatTests.__dict__ if name.startswith("test_")]
    return unittest.TestSuite(ChatTests(name) for name in names)
