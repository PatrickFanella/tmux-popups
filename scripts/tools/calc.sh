#!/usr/bin/env bash
set -euo pipefail
python3 -c '
import math, statistics, random, datetime, decimal, fractions
ns = {"math": math, "statistics": statistics, "random": random, "datetime": datetime, "decimal": decimal, "fractions": fractions}
ns.update({name: getattr(math, name) for name in dir(math) if not name.startswith("_")})
print("Calculator. Empty line or /exit to quit.")
print("Examples: 2**10, sin(pi/2), 15*0.2, datetime.date.today()")
while True:
    try: expr = input("calc › ").strip()
    except EOFError: break
    if not expr or expr in {"/exit", "/quit", "q", "quit", "exit"}: break
    try: print(eval(expr, {"__builtins__": {}}, ns))
    except Exception as exc: print(f"error: {exc}")
'
