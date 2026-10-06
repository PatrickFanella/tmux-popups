#!/usr/bin/env python3
"""Controlled-time timer checks and an attached tmux popup cancellation."""
import os
from pathlib import Path
import shlex
import signal
import subprocess
import tempfile
import time
import unittest

import test_launcher

ROOT = Path(__file__).resolve().parents[1]


class TimerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tmux-popups-timer-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        self.stub("clear", "exit 0")
        self.stub("sleep", "exit 0")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)

    def run_timer(self, value):
        return subprocess.run([str(ROOT / "scripts/tools/timer.sh")],
                              input=value + "\n\n", text=True, capture_output=True,
                              env=self.env, timeout=15)

    def test_decimal_and_default(self):
        self.stub("sleep", "exit 73")
        for value, expected in [("08", "08:00"), ("09", "09:00"),
                                ("", "25:00"), ("00008", "08:00")]:
            with self.subTest(value=value):
                result = self.run_timer(value)
                self.assertEqual(result.returncode, 73, result.stderr)
                self.assertIn(expected + " remaining", result.stdout)

    def test_maximum_is_accepted_before_controlled_sleep_failure(self):
        self.stub("sleep", "exit 73")
        result = self.run_timer("1440")
        self.assertEqual(result.returncode, 73)
        self.assertIn("1440:00 remaining", result.stdout)

    def test_zero_invalid_and_out_of_range(self):
        for value in ["0", "000", "invalid", "-1", "1.5", "1441", "999999999999999999999999999"]:
            with self.subTest(value=value):
                result = self.run_timer(value)
                self.assertEqual(result.returncode, 1)
                self.assertIn("whole number from 1 to 1440", result.stderr)
                self.assertNotIn("remaining", result.stdout)
                self.assertNotIn("value too great", result.stderr)

    def test_one_minute_sleeps_exactly_sixty_times(self):
        calls = self.base / "calls"
        self.stub("sleep", f"printf '%s\\n' \"$1\" >> {shlex.quote(str(calls))}")
        result = self.run_timer("1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls.read_text().splitlines(), ["1"] * 60)

    def test_eof_cancels_input(self):
        result = subprocess.run([str(ROOT / "scripts/tools/timer.sh")], input="",
                                text=True, capture_output=True, env=self.env, timeout=3)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("remaining", result.stdout)

    def test_termination_reaps_owned_sleep(self):
        marker = self.base / "sleep-pid"
        self.stub("sleep", f"echo $$ > {shlex.quote(str(marker))}\nexec /bin/sleep 60")
        process = subprocess.Popen([str(ROOT / "scripts/tools/timer.sh")],
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, env=self.env)
        try:
            process.stdin.write(b"08\n")
            process.stdin.flush()
            end = time.monotonic() + 3
            while not marker.exists() and time.monotonic() < end:
                time.sleep(.01)
            self.assertTrue(marker.exists())
            child = int(marker.read_text())
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=3)
            self.assertEqual(process.returncode, 143)
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            process.stdin.close()
            process.stderr.close()


class TimerPopupTests(test_launcher.LauncherTests):
    def test_attached_popup_decimal_input_and_ctrl_c(self):
        marker = self.home / "sleep-pid"
        self.stub("sleep", f"echo $$ > {shlex.quote(str(marker))}\nexec /bin/sleep 60")
        client = self.attach()
        target = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        popup = subprocess.Popen([test_launcher.REAL_TMUX, "-S", str(self.socket),
                                  "display-popup", "-E", "-c", target, "-w", "80%", "-h", "80%",
                                  shlex.quote(str(ROOT / "scripts/tools/timer.sh"))],
                                 env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: popup.poll() is None and popup.terminate())
        self.wait_until(lambda: b"Minutes [25]" in self.terminal_output)
        os.write(client, b"09\r")
        self.wait_until(lambda: b"09:00 remaining" in self.terminal_output)
        self.wait_until(marker.exists)
        child = int(marker.read_text())
        os.write(client, b"\x03")
        self.wait_until(lambda: not Path(f"/proc/{child}").exists())
        # The popup has closed and the attached client's parent shell still runs.
        popup.wait(timeout=3)
        self.assertTrue(self.tmux("list-clients").stdout.strip())


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromTestCase(TimerTests)
    suite.addTest(TimerPopupTests("test_attached_popup_decimal_input_and_ctrl_c"))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
