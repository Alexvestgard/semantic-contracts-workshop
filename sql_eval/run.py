"""Run one prompt stage without loading reference answers or a scorer."""

import argparse
import os
from pathlib import Path
import sys
import time

from .agent import attempt
from .common import dumps, read_json, write_json
from .database import Database

from scripts.model_client import ModelClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["baseline", "improved", "regressed"], required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--budget", default="/budget.json")
    parser.add_argument("--out", default="/out")
    args = parser.parse_args()
    root = Path("eval")
    questions = read_json(root / ("pilots.json" if args.pilot else "questions.json"))
    budget = read_json(args.budget)
    if not args.pilot and budget.get("status") != "frozen":
        parser.error("Time pilots and freeze their budget before a scored run.")
    prompt = read_json(root / "prompts" / (args.stage + ".json"))
    lock = read_json("models/gemma.lock.json")
    database = Database(os.environ["EVAL_DSN"])
    controls = {"questions": questions, "model_config": lock, "budget": budget,
                "temperature": 0, "question_ids": [q["id"] for q in questions]}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error("Output directory must be empty; preserve previous run evidence.")
    manifest = {"stage": args.stage, "pilot": args.pilot, "controls": controls,
                "prompt": prompt, "complete": False}
    write_json(out / "manifest.json", manifest)
    client = ModelClient(os.environ.get("MODEL_RUNNER_URL", "http://model-runner:12434"), lock)
    start = time.monotonic()
    for question in questions:
        with (out / (question["id"] + ".jsonl")).open("x") as trace:
            def record(event):
                trace.write(dumps(event) + "\n")
                trace.flush()
                action = event.get("action", {}).get("action", "error")
                print(f"{question['id']} turn {event['turn']}: {action}", flush=True)
            result = attempt(question, prompt, database, client, budget, record)
        write_json(out / (question["id"] + ".json"), result)
        print(f"{question['id']}: {result['status']}, {result['tool_calls']} calls, {result['elapsed_seconds']}s", flush=True)
    manifest.update(complete=True, elapsed_seconds=round(time.monotonic() - start, 3))
    write_json(out / "manifest.json", manifest)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Eval run failed: {error}", file=sys.stderr)
        sys.exit(1)
