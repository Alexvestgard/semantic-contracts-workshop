#!/usr/bin/env python3
"""Build and run the five-step museum SQL exercise (host Python stdlib only)."""

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sql_eval.common import read_json, write_json
from sql_eval.prompts import protect


def compose(*args):
    command = [os.environ.get("DOCKER", "docker"), "compose", "-p", "workshop-sql-eval",
               "-f", str(ROOT / "compose.models.yaml"), "-f", str(ROOT / "compose.eval.yaml"), *map(str, args)]
    subprocess.run(command, cwd=ROOT, check=True)


def workshop_database():
    container = os.environ.get("SQL_EVAL_DB_CONTAINER")
    if container:
        return container
    result = subprocess.run(
        [os.environ.get("DOCKER", "docker"), "ps", "--filter",
         "label=com.docker.compose.service=postgres", "--format", "{{.Names}}"],
        check=True, capture_output=True, text=True)
    containers = result.stdout.split()
    if len(containers) != 1:
        raise ValueError("Start the workshop database first. If several are running, set "
                         "SQL_EVAL_DB_CONTAINER to its container name. Found: "
                         + (", ".join(containers) or "none"))
    return containers[0]


def prepare_database():
    container = workshop_database()
    docker = os.environ.get("DOCKER", "docker")
    result = subprocess.run([docker, "inspect", container], check=True, capture_output=True, text=True)
    info = json.loads(result.stdout)[0]
    if not info["State"]["Running"]:
        raise ValueError("Start the workshop database before preparing eval access.")
    # Use the existing schema and data; setup only grants the reader access.
    subprocess.run([docker, "exec", "-i", container, "psql", "-U", "postgres", "-d", "postgres",
                    "-v", "ON_ERROR_STOP=1", "--single-transaction"],
                   input=(ROOT / "eval/read-only.sql").read_text(), text=True, check=True)
    compose("create", "eval-scorer")
    network = "workshop-sql-eval_eval-network"
    if network not in info["NetworkSettings"]["Networks"]:
        subprocess.run([docker, "network", "connect", "--alias", "workshop-db", network, container], check=True)
    print(f"Eval uses the existing workshop database in {container} with read-only access.")


def container_run(service, mounts, *args):
    uid, gid = (os.getuid(), os.getgid()) if os.getuid() else (1000, 1000)
    options = ["--user", f"{uid}:{gid}"]
    for source, target, readonly in mounts:
        if not readonly and os.getuid() == 0:
            os.chown(source, uid, gid)
        options += ["-v", f"{host_path(source)}:{target}" + (":ro" if readonly else "")]
    compose("run", "--rm", "--no-deps", *options, service, *args)


def host_path(path):
    path = Path(path).resolve()
    host_root = os.environ.get("SQL_EVAL_HOST_ROOT")
    if not host_root:
        return path
    try:
        return Path(host_root) / path.relative_to(ROOT)
    except ValueError:
        raise ValueError("Inside the devcontainer, keep eval artifacts within the repository.") from None


def restore_prompt(destination):
    source = ROOT / "eval/prompts/improved.json"
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if destination.read_bytes() != source.read_bytes():
        raise RuntimeError("Restored prompt differs from the improved prompt.")


def freeze_budget(pilot_dir, destination):
    pilot_dir = Path(pilot_dir)
    manifest = read_json(pilot_dir / "manifest.json")
    if not manifest.get("pilot") or not manifest.get("complete"):
        raise ValueError("A complete pilot run is required.")
    answers = [read_json(pilot_dir / (id + ".json")) for id in manifest["controls"]["question_ids"]]
    if not answers:
        raise ValueError("The pilot must contain recorded attempts.")
    budget = dict(manifest["controls"]["budget"])
    budget.update(status="frozen", max_tool_calls=max(6, max(a["tool_calls"] for a in answers) + 3),
                  question_timeout_seconds=max(60, math.ceil(max(a["elapsed_seconds"] for a in answers) * 1.5)),
                  pilot_outcomes=dict(Counter(a["status"] for a in answers)))
    write_json(destination, budget)
    return budget


def compare_reports(paths):
    # Keep this command independent of psycopg on the participant host.
    reports = [read_json(path) for path in paths]
    if [r["stage"] for r in reports] != ["baseline", "improved", "regressed"]:
        raise ValueError("Expected baseline, improved, and regressed reports in that order.")
    if any(report["controls"] != reports[0]["controls"] for report in reports[1:]):
        raise ValueError("Run controls differ between stages.")
    lines = ["# SQL eval results", "", "| Prompt | Correct | Seconds |", "| --- | ---: | ---: |"]
    for r in reports:
        lines.append(f"| {r['stage']} | {r['correct']}/{r['total']} | {r['elapsed_seconds']} |")
    for old, new in zip(reports, reports[1:]):
        before = {q["id"]: q["correct"] for q in old["questions"]}
        fixed = [q["id"] for q in new["questions"] if q["correct"] and not before[q["id"]]]
        broken = [q["id"] for q in new["questions"] if not q["correct"] and before[q["id"]]]
        lines += ["", f"{old['stage']} → {new['stage']}: {new['correct'] - old['correct']:+d} correct.",
                  "Fixed: " + (", ".join(fixed) or "none") + ".",
                  "Regressed: " + (", ".join(broken) or "none") + "."]
    observed = reports[1]["correct"] > reports[0]["correct"] and reports[2]["correct"] < reports[1]["correct"]
    lines += ["", "Improvement then regression observed: " + ("yes." if observed else "no; revise the rehearsal, not the scores."),
              "", "These 20 questions are a teaching diagnostic. One run does not establish a reliable capability difference."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "start", "prepare-db", "pilot", "freeze", "run", "score", "compare", "revert", "protect", "verify-gold", "isolation"])
    parser.add_argument("--stage", choices=["baseline", "improved", "regressed"], default="baseline")
    parser.add_argument("--artifacts", type=Path, default=ROOT / "artifacts/sql-eval")
    parser.add_argument("--prompt", type=Path)
    args = parser.parse_args()
    artifacts = args.artifacts.resolve()
    if args.action == "build":
        compose("build", "eval-agent", "eval-scorer")
    elif args.action == "start":
        prepare_database()
        compose("up", "-d", "model-init")
        compose("wait", "model-init")
    elif args.action == "prepare-db":
        prepare_database()
    elif args.action in {"pilot", "run"}:
        pilot = args.action == "pilot"
        out = artifacts / ("pilot" if pilot else args.stage)
        out.mkdir(parents=True, exist_ok=True)
        budget = ROOT / "eval/pilot-budget.json" if pilot else artifacts / "budget.json"
        if not budget.is_file():
            raise ValueError("Run pilots and freeze the budget first.")
        lock = artifacts / (out.name + ".running")
        with lock.open("x") as handle:
            handle.write("Agent process has not exited.\n")
        try:
            container_run("eval-agent", [(out, "/out", False), (budget, "/budget.json", True)],
                          "--stage", args.stage, *(["--pilot"] if pilot else []))
        finally:
            lock.unlink()
    elif args.action == "freeze":
        budget = freeze_budget(artifacts / "pilot", artifacts / "budget.json")
        print(f"Frozen limits: {budget['max_tool_calls']} database calls and {budget['question_timeout_seconds']} seconds per question.")
    elif args.action == "score":
        if (artifacts / (args.stage + ".running")).exists():
            raise ValueError("Wait for the agent process to exit before scoring.")
        out = artifacts / "reports"
        out.mkdir(parents=True, exist_ok=True)
        container_run("eval-scorer", [(artifacts / args.stage, "/run", True), (out, "/reports", False)],
                      "--run", "/run", "--out", "/reports/" + args.stage + ".json")
    elif args.action == "verify-gold":
        container_run("eval-scorer", [], "--verify-gold")
    elif args.action == "compare":
        report = compare_reports([artifacts / "reports" / (stage + ".json") for stage in ("baseline", "improved", "regressed")])
        (artifacts / "comparison.md").write_text(report)
        print(report)
    elif args.action == "revert":
        restore_prompt(artifacts / "active-prompt.json")
        print("Restored improved prompt exactly. No model or scorer was invoked.")
    elif args.action == "protect":
        prompt = read_json(args.prompt or artifacts / "active-prompt.json")
        contract = read_json(ROOT / "eval/prompt-contract.json")
        result = protect(prompt, contract)
        artifacts.mkdir(parents=True, exist_ok=True)
        write_json(artifacts / "contract-check.json", result)
        print("Prompt contract passed. No model or scorer was invoked.")
    elif args.action == "isolation":
        code = """from pathlib import Path
assert not Path('/app/eval/gold').exists()
assert not Path('/app/sql_eval/score.py').exists()
assert not Path('/var/run/docker.sock').exists()
assert not Path('/workspace').exists()
for path in Path('/app').rglob('*'):
    if path.is_file():
        assert b'GOLD_ONLY_8b45b406_reference_answers' not in path.read_bytes(), str(path)
print('Gold sentinel, scorer, repository mount, and Docker socket are absent from the agent image.')
"""
        compose("run", "--rm", "--no-deps", "--entrypoint", "python", "eval-agent", "-c", code)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Eval command failed: {error}", file=sys.stderr)
        sys.exit(1)
