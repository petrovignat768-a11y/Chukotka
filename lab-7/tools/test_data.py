#!/usr/bin/env python3
"""Самопроверки CSV и ожидаемых значений; к исполняемому файлу не обращаются."""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def rows(name):
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

class DataTests(unittest.TestCase):
    def test_positive_count_and_ids(self):
        r = rows("positive.csv")
        self.assertEqual(len(r), 12)
        self.assertEqual([x["id"] for x in r], [f"D{i:02}" for i in range(1, 13)])

    def test_positive_nonempty_and_expected(self):
        for x in rows("positive.csv"):
            self.assertTrue(x["taskText"].strip())
            self.assertEqual(x["expectedRow"], "[ ] " + x["taskText"])

    def test_csv_special_characters_round_trip(self):
        r = {x["id"]: x["taskText"] for x in rows("positive.csv")}
        self.assertEqual(r["D04"], "a,b")
        self.assertEqual(r["D05"], 'Проверить "кавычки"')
        self.assertEqual(r["D08"], "café")

    def test_duplicate_is_present(self):
        r = {x["id"]: x["taskText"] for x in rows("positive.csv")}
        self.assertEqual(r["D09"], r["D10"])

    def test_negative_whitespace_and_warning(self):
        r = rows("negative.csv")
        self.assertEqual([x["taskText"] for x in r], ["", " ", "   "])
        self.assertTrue(all(x["expectedWarning"] == "Текст задачи не может быть пустым!" for x in r))

    def test_mass_count_and_order(self):
        r = rows("mass_100.csv")
        self.assertEqual(len(r), 100)
        for i, x in enumerate(r, 1):
            self.assertEqual(x["id"], f"M{i:03}")
            self.assertEqual(x["taskText"], f"Mass-{i:03}")
            self.assertEqual(x["expectedRow"], f"[ ] Mass-{i:03}")

    def test_headers(self):
        self.assertEqual(list(rows("positive.csv")[0]), ["id", "taskText", "expectedRow"])
        self.assertEqual(list(rows("negative.csv")[0]), ["id", "kind", "taskText", "expectedWarning"])
        self.assertEqual(list(rows("mass_100.csv")[0]), ["id", "taskText", "expectedRow"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
