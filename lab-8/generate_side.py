#!/usr/bin/env python3
"""Генератор переносимого проекта Selenium IDE; тесты введены вручную, не записаны в IDE."""
import json
import uuid
from pathlib import Path


def uid():
    return str(uuid.uuid4())


def command(name, target="", value=""):
    return {"id": uid(), "comment": "", "command": name, "target": target, "targets": [], "value": value}


def row(title):
    return "xpath=//li[.//span[@class='task-title' and text()='" + title + "']]"


def scenario(name, instructions):
    return {"id": uid(), "name": name, "commands": [command(*item) for item in instructions]}


one = "IDE создание и удаление"
two = "IDE выполнение задачи"
tests = [
    scenario("Создание и удаление", [
        ("open", "/"),
        ("assertTitle", "Командный трекер задач — демо"),
        ("type", "id=task-input", one),
        ("click", "id=add"),
        ("waitForElementPresent", row(one), "5000"),
        ("assertValue", "id=task-input", ""),
        ("assertText", row(one) + "//span[@class='task-status']", "[ ]"),
        ("click", row(one) + "//input"),
        ("click", "id=delete"),
        ("waitForElementNotPresent", row(one), "5000"),
        ("assertElementNotPresent", row(one)),
    ]),
    scenario("Завершение, повтор, очистка", [
        ("open", "/"),
        ("type", "id=task-input", two),
        ("click", "id=add"),
        ("waitForElementPresent", row(two), "5000"),
        ("click", row(two) + "//input"),
        ("click", "id=complete"),
        ("waitForElementPresent", row(two) + "//span[@class='task-status' and text()='[✓]']", "5000"),
        ("assertText", row(two) + "//span[@class='task-status']", "[✓]"),
        ("click", row(two) + "//input"),
        ("click", "id=complete"),
        ("pause", "500"),
        ("assertAlert", "Эта задача уже выполнена"),
        ("acceptAlert", ""),
        ("click", row(two) + "//input"),
        ("click", "id=delete"),
        ("waitForElementNotPresent", row(two), "5000"),
        ("assertElementNotPresent", row(two)),
    ]),
    scenario("Предупреждение при пустом вводе", [
        ("open", "/"),
        ("type", "id=task-input", ""),
        ("click", "id=add"),
        ("pause", "500"),
        ("assertAlert", "Текст задачи не может быть пустым!"),
        ("acceptAlert", ""),
        ("assertElementPresent", "id=task-input"),
    ]),
]
project = {
    "id": uid(), "version": "2.0", "name": "Трекер задач — лабораторная 8",
    "url": "http://127.0.0.1:8765", "tests": tests,
    "suites": [{"id": uid(), "name": "Основной набор", "persistSession": False,
                "parallel": False, "timeout": 300, "tests": [test["id"] for test in tests]}],
    "urls": ["http://127.0.0.1:8765/"], "plugins": [],
}
Path(__file__).with_name("tracker.side").write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
