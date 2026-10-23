"""Compare final query results after the agent container has exited."""

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import os
from pathlib import Path

from .common import digest, dumps, read_json, write_json
from .database import Database


def equal_rows(actual, expected, ordered=False):
    def canonical(value):
        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
            return {"number": str(Decimal(str(value)).normalize())}
        if isinstance(value, (list, tuple)):
            return [canonical(item) for item in value]
        return value
    left, right = [dumps(canonical(row)) for row in actual], [dumps(canonical(row)) for row in expected]
    return left == right if ordered else Counter(left) == Counter(right)


def verify_gold(database, questions, gold):
    if {q["id"] for q in questions} != set(gold["answers"]):
        raise ValueError("Question and reference IDs differ.")
    for question in questions:
        ref = gold["answers"][question["id"]]
        result = database.query(ref["sql"], 5000)
        if result["truncated"] or not equal_rows(result["rows"], ref["expected"], question["ordered"]):
            raise ValueError(f"Reference SQL disagrees with source-derived answers: {question['id']}")


def score_run(path, database, questions, gold):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    if manifest.get("pilot") or not manifest.get("complete"):
        raise ValueError("Only complete non-pilot runs can be scored.")
    controls = manifest["controls"]
    if controls["questions_sha256"] != digest(questions):
        raise ValueError("Question set changed after the run.")
    if controls["question_ids"] != [q["id"] for q in questions]:
        raise ValueError("Question order differs from the frozen manifest.")
    verify_gold(database, questions, gold)
    scores = []
    for question in questions:
        answer = read_json(path / (question["id"] + ".json"))
        if answer["id"] != question["id"]:
            raise ValueError("Answer ID does not match its question.")
        item = {"id": question["id"], "correct": False, "status": answer["status"],
                "tool_calls": answer["tool_calls"], "elapsed_seconds": answer["elapsed_seconds"]}
        if answer["status"] == "submitted":
            try:
                actual = database.query(answer["sql"], 5000)
                item["correct"] = not actual["truncated"] and equal_rows(
                    actual["rows"], gold["answers"][question["id"]]["expected"], question["ordered"])
                item["status"] = "correct" if item["correct"] else "wrong_result"
            except Exception as error:
                item.update(status="sql_error", error=str(error)[:600])
        scores.append(item)
    return {"stage": manifest["stage"], "correct": sum(s["correct"] for s in scores),
            "total": len(scores), "elapsed_seconds": manifest["elapsed_seconds"],
            "controls_sha256": digest(controls), "prompt_sha256": manifest["prompt_sha256"],
            "gold_sha256": digest(gold), "scorer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "questions": scores}


def compare(reports):
    if [r["stage"] for r in reports] != ["baseline", "improved", "regressed"]:
        raise ValueError("Provide baseline, improved, and regressed reports in order.")
    for field in ("controls_sha256", "gold_sha256", "scorer_sha256"):
        if len({r[field] for r in reports}) != 1:
            raise ValueError(f"Incomparable runs: {field} differs.")
    changes = []
    for previous, current in zip(reports, reports[1:]):
        before = {q["id"]: q["correct"] for q in previous["questions"]}
        changes.append({"from": previous["stage"], "to": current["stage"],
                        "delta": current["correct"] - previous["correct"],
                        "fixed": [q["id"] for q in current["questions"] if q["correct"] and not before[q["id"]]],
                        "regressed": [q["id"] for q in current["questions"] if not q["correct"] and before[q["id"]]]})
    return {"scores": [{k: r[k] for k in ("stage", "correct", "total", "elapsed_seconds")} for r in reports],
            "changes": changes,
            "teaching_sequence_observed": reports[1]["correct"] > reports[0]["correct"] and reports[2]["correct"] < reports[1]["correct"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run")
    parser.add_argument("--out", default="/reports/report.json")
    parser.add_argument("--verify-gold", action="store_true")
    args = parser.parse_args()
    db = Database(os.environ["EVAL_DSN"])
    questions, gold = read_json("eval/questions.json"), read_json("eval/gold/answers.json")
    if args.verify_gold:
        verify_gold(db, questions, gold)
        print("All 20 reference queries agree with independent source-derived answers.")
    else:
        report = score_run(args.run, db, questions, gold)
        write_json(args.out, report)
        print(f"{report['stage']}: {report['correct']}/{report['total']}")


if __name__ == "__main__":
    main()
