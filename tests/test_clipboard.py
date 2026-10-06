#!/usr/bin/env python3
"""Clipboard history checks never write the system clipboard."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tmux-popups-clipboard-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.history = self.base / "history"
        self.history.write_bytes(b"1\tselected preview\n")
        self.decoded = self.base / "decoded"
        self.decoded.write_bytes(b"line one\nline two\0binary\xff\n\n")
        self.copied = self.base / "copied"
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        FIXTURE=str(self.base), TMPDIR=str(self.base),
                        LIST_STATUS="0", PICKER_STATUS="0", DECODE_STATUS="0")
        self.stub("cliphist", """case "$1" in
list)
  echo list >> "$FIXTURE/calls"
  cat "$FIXTURE/history"
  exit "$LIST_STATUS"
  ;;
decode)
  cat > "$FIXTURE/selection"
  cat "$FIXTURE/decoded"
  exit "$DECODE_STATUS"
  ;;
esac""")
        self.stub("fzf", """echo picker >> "$FIXTURE/calls"
if (( PICKER_STATUS != 0 )); then exit "$PICKER_STATUS"; fi
# Exit after selecting the first row, like an early picker selection.
head -n 1""")
        self.stub("wl-copy", 'cat > "$FIXTURE/copied"')
        self.stub("sleep", "exit 0")

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -euo pipefail\n" + body + "\n")
        path.chmod(0o755)

    def run_clipboard(self):
        result = subprocess.run([str(ROOT / "scripts/tools/clipboard.sh")],
                                input=b"\n", capture_output=True, env=self.env, timeout=10)
        self.assertFalse(list(self.base.glob("tmux-popups-clipboard.*")), "owned temporary files leaked")
        return result

    def test_empty_history_is_success_without_picker_or_copy(self):
        self.history.write_bytes(b"")
        result = self.run_clipboard()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"No cliphist entries yet", result.stdout)
        self.assertEqual((self.base / "calls").read_text(), "list\n")
        self.assertFalse(self.copied.exists())

    def test_small_and_large_history_are_read_once_and_copy_exact_bytes(self):
        for rows in [1, 100000]:
            with self.subTest(rows=rows):
                (self.base / "calls").unlink(missing_ok=True)
                self.history.write_bytes(b"1\tselected preview\n" + b"2\tother row\n" * (rows - 1))
                result = self.run_clipboard()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(b"Copied selected", result.stdout)
                self.assertEqual((self.base / "calls").read_text(), "list\npicker\n")
                self.assertEqual((self.base / "selection").read_bytes(), b"1\tselected preview")
                self.assertEqual(self.copied.read_bytes(), self.decoded.read_bytes())

    def test_history_failure_is_not_empty_even_after_partial_output(self):
        for output in [b"", b"1\tpartial\n"]:
            with self.subTest(output=output):
                self.history.write_bytes(output)
                self.env["LIST_STATUS"] = "23"
                result = self.run_clipboard()
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"could not read cliphist history", result.stderr)
                self.assertNotIn(b"No cliphist entries", result.stdout)
                self.assertFalse(self.copied.exists())

    def test_picker_cancellation_and_failure(self):
        for status, expected in [("1", 0), ("130", 0), ("2", 1)]:
            with self.subTest(status=status):
                self.env["PICKER_STATUS"] = status
                result = self.run_clipboard()
                self.assertEqual(result.returncode, expected)
                self.assertFalse(self.copied.exists())
                if expected:
                    self.assertIn(b"clipboard picker failed (status 2)", result.stderr)

    def test_decode_failure_does_not_copy_partial_bytes(self):
        self.env["DECODE_STATUS"] = "23"
        result = self.run_clipboard()
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"could not decode selected cliphist item", result.stderr)
        self.assertFalse(self.copied.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
