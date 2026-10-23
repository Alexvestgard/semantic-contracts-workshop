"""Check the eval reader against the seeded workshop database without changing data."""

import os
from pathlib import Path
import tempfile
import unittest

import psycopg

from sql_eval.database import Database
from sql_eval.common import read_json, write_json
from sql_eval.score import score_run


@unittest.skipUnless(os.environ.get("EVAL_TEST_DSN"), "Set EVAL_TEST_DSN for the database checks.")
class DatabaseIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["EVAL_TEST_DSN"]
        self.db = Database(self.dsn)

    def test_schema_and_row_limits(self):
        self.assertEqual(len(self.db.schema()["tables"]), 8)
        self.assertIn("department", self.db.schema()["tables"]["object_gallery_info"])
        self.assertEqual(self.db.schema("unknown")["tables"], self.db.schema()["tables"])
        self.assertIn("object_id", [row[0] for row in self.db.schema("object")["columns"]])
        result = self.db.query("SELECT object_id FROM object ORDER BY object_id", 3)
        self.assertEqual(len(result["rows"]), 3)
        self.assertTrue(result["truncated"])

    def test_role_blocks_writes_even_without_parser(self):
        with psycopg.connect(self.dsn) as conn:
            with self.assertRaises(psycopg.errors.ReadOnlySqlTransaction):
                conn.execute("DELETE FROM object WHERE false")
        with psycopg.connect(self.dsn) as conn:
            conn.execute("SET TRANSACTION READ WRITE")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                conn.execute("DELETE FROM object WHERE false")

    def test_server_timeout_even_without_parser(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute("SET LOCAL statement_timeout = '25ms'")
            with self.assertRaises(psycopg.errors.QueryCanceled):
                conn.execute("SELECT pg_sleep(1)")

    def test_gold_is_not_a_database_table(self):
        with psycopg.connect(self.dsn) as conn:
            names = {row[0] for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        self.assertTrue(set(self.db.schema()["tables"]).issubset(names))
        self.assertFalse({"answers", "gold"} & names)
        with self.assertRaises(ValueError):
            self.db.query("SELECT * FROM answers")

    def test_scorer_checks_all_twenty_and_detects_changed_answers(self):
        questions = read_json("eval/questions.json")
        gold = read_json("eval/gold/answers.json")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = {"complete":True,"pilot":False,"stage":"baseline","elapsed_seconds":0,
                        "prompt":{"instructions":"Integration fixture; not a model run"}, "controls":{
                            "questions":questions, "question_ids":[q["id"] for q in questions]}}
            write_json(path / "manifest.json", manifest)
            for question in questions:
                write_json(path / (question["id"] + ".json"), {"id":question["id"], "status":"submitted",
                           "sql":gold["answers"][question["id"]]["sql"], "tool_calls":0,"elapsed_seconds":0})
            self.assertEqual(score_run(path, self.db, questions, gold)["correct"], 20)
            answer = read_json(path / "q01.json")
            answer["sql"] = "SELECT 0"
            write_json(path / "q01.json", answer)
            answer = read_json(path / "q02.json")
            answer["sql"] = "DELETE FROM object"
            write_json(path / "q02.json", answer)
            report = score_run(path, self.db, questions, gold)
            self.assertEqual(report["correct"], 18)
            self.assertEqual(report["questions"][0]["status"], "wrong_result")
            self.assertEqual(report["questions"][1]["status"], "sql_error")


if __name__ == "__main__":
    unittest.main()
