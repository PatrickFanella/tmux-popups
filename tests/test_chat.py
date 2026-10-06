#!/usr/bin/env python3
"""Chat request checks with substitute providers and clipboards."""
import os
import pty
import select
import shlex
import signal
import shutil
import subprocess
import time
import unittest
from pathlib import Path
import test_launcher as launcher
ROOT = launcher.ROOT

class ChatTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    setUp = launcher.LauncherTests.setUp
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def launch(self, popup):
        self.env["TMPDIR"] = str(self.base / "requests")
        Path(self.env["TMPDIR"]).mkdir(exist_ok=True)
        script = ROOT / "scripts/tools/chat.sh"
        if popup:
            master = self.attach()
            command = "env " + " ".join(shlex.quote(k + "=" + self.env[k]) for k in ("PATH", "TMPDIR"))
            command += " " + shlex.quote(str(script))
            self.popup_process = subprocess.Popen([launcher.REAL_TMUX, "-S", str(self.socket), "display-popup", "-E", "-w", "90%", "-h", "90%", command], env=self.env)
            process = self.popup_process
            self.owned_cleanup(lambda: process.poll() is not None or process.terminate())
            self.output = self.terminal_output
            self.process = None
        else:
            master, slave = pty.openpty()
            self.process = subprocess.Popen([str(script)], stdin=slave, stdout=slave, stderr=slave,
                                            env=self.env, start_new_session=True)
            os.close(slave)
            self.output = bytearray()
            process = self.process
            def cleanup():
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)
                os.close(master)
            self.owned_cleanup(cleanup)
        self.master = master
        self.popup = popup
        self.expect(b"Quick Chat")

    def drain(self):
        if not self.popup:
            try:
                while select.select([self.master], [], [], 0.01)[0]:
                    chunk = os.read(self.master, 65536)
                    if not chunk:
                        break
                    self.output.extend(chunk)
            except OSError:
                pass
        return bytes(self.output)

    def expect(self, text, after=0):
        try:
            self.wait_until(lambda: text in self.drain()[after:])
        except AssertionError:
            self.fail(f"Missing {text!r} in terminal output: {self.drain()[after:]!r}")

    def send(self, text):
        os.write(self.master, text.encode())

    def closed(self):
        if self.popup:
            self.popup_process.wait(timeout=3)
        else:
            self.process.wait(timeout=3)
            self.drain()
        self.wait_until(lambda: not list(Path(self.env["TMPDIR"]).iterdir()))
        self.assertNotIn(b"unbound variable", self.output)
        self.assertNotIn(b"SyntaxError", self.output)

    def test_valid_continuation_copy_and_quit(self):
        for popup in (False, True):
            with self.subTest(popup=popup):
                self.stub("ocq", "printf '%s\\n' \"$*\" >> \"$HOME/calls\"; printf '%s' '{\"sessionID\":\"session-9\",\"text\":\"answer-nine\"}'")
                self.stub("wl-copy", 'cat > "$HOME/copied"')
                self.launch(popup)
                self.send("first prompt\n")
                self.expect(b"answer-nine")
                self.send("c\n")
                self.expect(b"Copied.")
                after = len(self.output)
                self.send("second prompt\n")
                self.expect(b"answer-nine", after)
                self.send("/quit\n")
                self.closed()
                self.assertIn("--session session-9 second prompt", (self.home / "calls").read_text())
                self.assertEqual((self.home / "copied").read_text(), "answer-nine")

    def test_invalid_provider_and_copy_failures_recover(self):
        for popup in (False, True):
            with self.subTest(popup=popup):
                self.stub("ocq", """case "${!#}" in
bad) printf 'not JSON';;
missing) printf '%s' '{"sessionID":"wrong"}';;
empty) : ;;
fail) exit 7;;
*) printf '%s\\n' "$*" >> "$HOME/valid-calls"; printf '%s' '{"sessionID":"valid-session","text":"valid-answer"}';;
esac""")
                self.stub("wl-copy", "exit 3")
                self.launch(popup)
                for prompt in ("bad", "missing", "empty", "fail"):
                    after = len(self.output)
                    self.send(prompt + "\n")
                    self.expect(b"Try again.", after)
                    self.assertNotIn(b"Assistant", self.output[after:])
                self.send("valid\n")
                self.expect(b"valid-answer")
                self.send("cq\n")
                self.expect(b"Copy failed.")
                after = len(self.output)
                self.send("bad\n")
                self.expect(b"Try again.", after)
                after = len(self.output)
                self.send("valid-again\n")
                self.expect(b"valid-answer", after)
                self.send("q\n")
                self.closed()
                calls = (self.home / "valid-calls").read_text().splitlines()
                self.assertNotIn("--session", calls[0])
                self.assertIn("--session valid-session valid-again", calls[1])

    def test_queued_input_and_copy_quit(self):
        for popup in (False, True):
            with self.subTest(popup=popup):
                self.stub("ocq", "sleep 0.3; printf '%s\\n' \"$*\" >> \"$HOME/queued\"; printf '%s' '{\"sessionID\":\"queued-session\",\"text\":\"queued-answer\"}'")
                self.stub("wl-copy", 'cat > "$HOME/queued-copy"')
                self.launch(popup)
                self.send("first\n\nsecond typed during wait\ncq\n")
                self.closed()
                self.assertIn("second typed during wait", (self.home / "queued").read_text())
                self.assertEqual((self.home / "queued-copy").read_text(), "queued-answer")

    def test_missing_dependencies_are_visible(self):
        # A restricted path prevents host-installed provider commands from hiding a missing tool.
        for tool in ("bash", "dirname", "node", "setsid"):
            (self.bin / tool).symlink_to(shutil.which(tool))
        for dependency in ("ocq", "node", "setsid"):
            if dependency == "node":
                (self.bin / "node").unlink()
                self.stub("ocq", ":")
            elif dependency == "setsid":
                (self.bin / "node").symlink_to(shutil.which("node"))
                (self.bin / "setsid").unlink()
            env = dict(self.env, PATH=str(self.bin))
            result = subprocess.run([str(ROOT / "scripts/tools/chat.sh")], env=env,
                                    input="", capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Required chat dependency missing: " + dependency, result.stderr)

    def test_interruption_stops_owned_request_only(self):
        sentinel = subprocess.Popen(["sleep", "30"])
        self.owned_cleanup(lambda: (sentinel.terminate(), sentinel.wait()))
        for popup, close in ((False, "interrupt"), (True, "interrupt"), (False, "hangup"), (True, "popup-close")):
            with self.subTest(popup=popup, close=close):
                self.stub("ocq", 'echo "$$" > "$HOME/provider-pid"; sleep 30 & echo "$!" > "$HOME/child-pid"; wait')
                self.launch(popup)
                self.send("slow\n")
                self.wait_until(lambda: (self.home / "child-pid").exists())
                if popup:
                    if close == "popup-close":
                        self.tmux("display-popup", "-C")
                    else:
                        self.send("\x03")
                else:
                    os.kill(self.process.pid, signal.SIGHUP if close == "hangup" else signal.SIGINT)
                self.closed()
                self.assertIsNone(sentinel.poll())
                for name in ("provider-pid", "child-pid"):
                    pid = int((self.home / name).read_text())
                    def stopped():
                        path = Path(f"/proc/{pid}/stat")
                        return not path.exists() or path.read_text().split()[2] == "Z"
                    self.wait_until(stopped)
                (self.home / "child-pid").unlink()

if __name__ == "__main__":
    unittest.main()
