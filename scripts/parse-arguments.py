#!/usr/bin/env python3
"""Decode registry argument data to hexadecimal UTF-8 byte escapes, never shell code."""
import json
import sys

try:
    values = json.loads(sys.argv[1])
    if not isinstance(values, list) or any(
        not isinstance(value, str) or "\0" in value for value in values
    ):
        raise ValueError("expected strings without NUL")
    encoded = [value.encode("utf-8") for value in values]
except (ValueError, UnicodeError):
    sys.exit(1)
for value in encoded:
    print(":" + "".join(f"\\x{byte:02x}" for byte in value))
