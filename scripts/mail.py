#!/usr/bin/env python3
"""Compatibility shim — the engine moved to skills/local-email/scripts/mail.py
(issue #9, Agent Skills standard: resources live inside the skill directory).
This forwarder keeps old invocations of scripts/mail.py working; update your
paths, it may be removed in a future release."""
import os
import runpy
import sys

TARGET = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.pardir, "skills", "local-email", "scripts", "mail.py",
)

print("[deprecated] scripts/mail.py moved to skills/local-email/scripts/mail.py; "
      "update your path.", file=sys.stderr)
sys.argv[0] = TARGET
runpy.run_path(TARGET, run_name="__main__")
