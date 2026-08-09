#!/usr/bin/env python3
"""Deterministic integrity checks for the AgentForge series."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "agentforge"
MANIFEST = json.loads((ENTRY / "series-manifest.json").read_text())
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


phases = MANIFEST["phases"]
phase_by_skill = {phase["skill"]: phase["id"] for phase in phases}
expected_ids = list(range(13))
actual_ids = [phase["id"] for phase in phases]
if actual_ids != expected_ids:
    fail(f"phase ids must be {expected_ids}, got {actual_ids}")

all_skills = [MANIFEST["entrypoint"]]
all_skills += [phase["skill"] for phase in phases]
all_skills += [item["skill"] for item in MANIFEST["cross_cutting"]]
if len(all_skills) != len(set(all_skills)):
    fail("manifest contains duplicate skill names")

for index, phase in enumerate(phases):
    expected_previous = phases[index - 1]["skill"] if index else None
    expected_next = phases[index + 1]["skill"] if index + 1 < len(phases) else None
    if phase["previous"] != expected_previous:
        fail(f"{phase['skill']}: previous should be {expected_previous}")
    if phase["next"] != expected_next:
        fail(f"{phase['skill']}: next should be {expected_next}")

for skill in all_skills:
    skill_file = ROOT / skill / "SKILL.md"
    if not skill_file.is_file():
        fail(f"missing {skill_file}")
        continue
    text = skill_file.read_text()
    if not text.startswith("---\n") or text.count("\n---\n") < 1:
        fail(f"{skill}: invalid YAML frontmatter boundary")
    name_match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
    if not name_match or name_match.group(1) != skill:
        fail(f"{skill}: frontmatter name does not match directory")
    if 'version: "3.0.0"' not in text:
        fail(f"{skill}: version is not 3.0.0")
    if 'last_updated: "2026-08-08"' not in text:
        fail(f"{skill}: last_updated is not 2026-08-08")
    if skill != MANIFEST["entrypoint"] and "disable-model-invocation: true" not in text:
        fail(f"{skill}: phase skills must be router/explicit-only")

for phase in phases:
    text = (ROOT / phase["skill"] / "SKILL.md").read_text()
    heading = re.compile(rf"(?m)^# .*Phase {phase['id']}\b")
    if not heading.search(text):
        fail(f"{phase['skill']}: missing canonical Phase {phase['id']} heading")

phase_aliases = {
    "spec": 0,
    "architecture": 1,
    "tools": 2,
    "context": 3,
    "memory": 4,
    "security": 5,
    "harness": 6,
    "multiagent": 7,
    "multi-agent": 7,
    "ship": 8,
    "production": 9,
    "autoplan": 10,
    "evolution": 11,
    "benchmark": 12,
}

for skill in all_skills:
    for path in (ROOT / skill).rglob("*.md"):
        text = path.read_text()
        relative = path.relative_to(ROOT)
        for target_skill, stated_phase in re.findall(
            r"/(agentforge-[a-z]+)`?[^\n]{0,100}?\(Phase\s+(\d+)\)", text
        ):
            expected = phase_by_skill.get(target_skill)
            if expected is not None and int(stated_phase) != expected:
                fail(f"{relative}: {target_skill} labeled Phase {stated_phase}, expected {expected}")
        for stated_phase, alias in re.findall(
            r"Phase\s+(\d+)\s*\((spec|architecture|tools|context|memory|security|harness|multiagent|multi-agent|ship|production|autoplan|evolution|benchmark)\)",
            text,
            flags=re.IGNORECASE,
        ):
            expected = phase_aliases[alias.lower()]
            if int(stated_phase) != expected:
                fail(f"{relative}: {alias} labeled Phase {stated_phase}, expected {expected}")

for skill in all_skills:
    base = ROOT / skill
    for path in base.rglob("*.md"):
        text = path.read_text()
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", prose):
            clean = target.split("#", 1)[0]
            if not clean or re.match(r"^[a-z]+://", clean) or clean.startswith("/"):
                continue
            if not (path.parent / clean).resolve().exists():
                fail(f"{path.relative_to(ROOT)}: broken relative link {target}")

security_text = (ROOT / "agentforge-security" / "SKILL.md").read_text()
for stale_claim in ("5 malicious documents", "73.2%", "data not leaving China principle"):
    if stale_claim in security_text:
        fail(f"agentforge-security: forbidden stale claim remains: {stale_claim}")

evolution_text = (ROOT / "agentforge-evolution" / "SKILL.md").read_text()
for unsupported in ("DynamicToolSet.hot_swap_tool", "uses formal proofs"):
    if unsupported in evolution_text:
        fail(f"agentforge-evolution: unsupported implementation claim remains: {unsupported}")

eval_cases = json.loads((ENTRY / "tests" / "eval-cases.json").read_text())
case_ids = [case["id"] for case in eval_cases.get("cases", [])]
if len(case_ids) < 4 or len(case_ids) != len(set(case_ids)):
    fail("eval cases must contain at least four unique ids")
for case in eval_cases.get("cases", []):
    if not case.get("prompt") or not case.get("required") or not case.get("forbidden"):
        fail(f"eval case {case.get('id')}: prompt/required/forbidden must be non-empty")

threshold_case = next(
    (case for case in eval_cases.get("cases", []) if case.get("id") == "uncalibrated-threshold-gate"),
    None,
)
if threshold_case is None:
    fail("eval cases must include uncalibrated-threshold-gate")
else:
    required_variables = {
        "max_total_steps",
        "max_identical_call_repeats",
        "max_stagnant_results",
        "timeout_seconds",
    }
    missing_variables = required_variables - set(re.findall(r"[a-z_]+", threshold_case["prompt"]))
    if missing_variables:
        fail(f"uncalibrated-threshold-gate missing variables: {sorted(missing_variables)}")

threshold_checker = ENTRY / "scripts" / "check-threshold-output.py"
if not threshold_checker.is_file():
    fail("missing threshold output checker")

threshold_pass_fixture = ENTRY / "tests" / "fixtures" / "threshold-pass.txt"
threshold_fail_fixture = ENTRY / "tests" / "fixtures" / "threshold-fail.txt"
if not threshold_pass_fixture.is_file() or not threshold_fail_fixture.is_file():
    fail("missing threshold checker fixtures")
elif threshold_checker.is_file():
    pass_result = subprocess.run(
        [sys.executable, str(threshold_checker), str(threshold_pass_fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    fail_result = subprocess.run(
        [sys.executable, str(threshold_checker), str(threshold_fail_fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    if pass_result.returncode != 0:
        fail("threshold checker rejected its passing fixture")
    if fail_result.returncode == 0:
        fail("threshold checker accepted its failing fixture")

registry = Path.home() / ".agents" / "skills"
if registry.is_dir():
    for skill in all_skills:
        registered = registry / skill
        if not registered.exists():
            fail(f"runtime registry missing {skill}")

if ERRORS:
    print("AgentForge validation FAILED")
    for error in ERRORS:
        print(f"- {error}")
    sys.exit(1)

print(f"AgentForge validation PASSED: {len(all_skills)} skills, {len(phases)} phases")
