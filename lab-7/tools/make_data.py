#!/usr/bin/env python3
"""Генератор данных по спецификации; не запускает и не имитирует приложение."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
POSITIVE = [
    ("D01", "Купить хлеб"),
    ("D02", "Prepare report"),
    ("D03", "2026-11-18"),
    ("D04", "a,b"),
    ("D05", 'Проверить "кавычки"'),
    ("D06", "Тест №7: пункт (А)"),
    ("D07", "Да/Нет? 42!"),
    ("D08", "café"),
    ("D09", "задача-01"),
    ("D10", "задача-01"),
    ("D11", "1234567890"),
    ("D12", "Заказ-ABC_01"),
]
NEGATIVE = [
    ("N01", "empty", "", "Текст задачи не может быть пустым!"),
    ("N02", "space1", " ", "Текст задачи не может быть пустым!"),
    ("N03", "space3", "   ", "Текст задачи не может быть пустым!"),
]

def write_csv(name, header, rows):
    with (DATA / name).open("w", encoding="utf-8", newline="") as f:
        out = csv.writer(f, lineterminator="\n")
        out.writerow(header)
        out.writerows(rows)

def main():
    DATA.mkdir(parents=True, exist_ok=True)
    write_csv("positive.csv", ["id", "taskText", "expectedRow"],
              [(key, title, "[ ] " + title) for key, title in POSITIVE])
    write_csv("negative.csv", ["id", "kind", "taskText", "expectedWarning"], NEGATIVE)
    write_csv("mass_100.csv", ["id", "taskText", "expectedRow"],
              [(f"M{i:03}", f"Mass-{i:03}", f"[ ] Mass-{i:03}") for i in range(1, 101)])
    print(f"Созданы данные: положительных={len(POSITIVE)}, отрицательных={len(NEGATIVE)}, массовых=100")
    print("Это не запуск тестируемого приложения и не результаты RFT.")

if __name__ == "__main__":
    main()
