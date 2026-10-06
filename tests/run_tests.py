#!/usr/bin/env python3
"""Discover regressions while retaining cleanup on the outer timeout."""
from pathlib import Path
import signal
import sys
import unittest


def terminate(signum, frame):
    raise KeyboardInterrupt("verification deadline reached")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    unittest.main(module=None, argv=[sys.argv[0], "discover", "-s",
                  str(Path(__file__).resolve().parent), "-p", "test_*.py", "-v", *sys.argv[1:]])
