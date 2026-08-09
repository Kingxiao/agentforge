#!/usr/bin/env python3
"""Check the AgentForge uncalibrated-threshold output contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


VARIABLES = (
    "max_total_steps",
    "max_identical_call_repeats",
    "max_stagnant_results",
    "timeout_seconds",
)

REQUIRED_LINES = (
    "THRESHOLD_STATUS: UNCALIBRATED",
    *(f"{variable}: TBD" for variable in VARIABLES),
    "CALIBRATION_BASIS:",
    "THRESHOLD_OUTPUT_END",
)


def check(path: Path) -> list[str]:
    text = path.read_text(errors="replace")
    errors: list[str] = []

    for required in REQUIRED_LINES:
        if required not in text:
            errors.append(f"missing required contract text: {required}")

    if text.rstrip().splitlines()[-1:] != ["THRESHOLD_OUTPUT_END"]:
        errors.append("THRESHOLD_OUTPUT_END must be the final non-empty line")

    for variable in VARIABLES:
        numeric_assignment = re.compile(
            rf"(?im)^[^\n]*`?{re.escape(variable)}`?\s*(?:[:=]|\|)\s*"
            rf"(?:\*{{0,2}})?(?:about\s+|approximately\s+|约\s*)?\d[^\s|,;)]*"
        )
        for match in numeric_assignment.finditer(text):
            errors.append(
                f"unsupported numeric assignment for {variable}: {match.group(0).strip()}"
            )

    unsupported_calibration_patterns = {
        "numeric percentile": re.compile(r"(?i)\bP\d{1,3}\b"),
        "numeric multiplier": re.compile(r"(?i)\b\d+(?:\.\d+)?\s*(?:x|倍)\b"),
        "numeric sample count": re.compile(r"(?:至少|最少|采集|收集)\s*\d+\s*(?:条|个|次|份)?"),
        "numeric percentage": re.compile(r"\d+(?:\.\d+)?\s*%"),
    }
    for label, pattern in unsupported_calibration_patterns.items():
        for match in pattern.finditer(text):
            errors.append(f"unsupported {label}: {match.group(0)}")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check-threshold-output.py OUTPUT.txt [OUTPUT.txt ...]", file=sys.stderr)
        return 2

    failed = False
    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        errors = check(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
