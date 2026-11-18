#!/usr/bin/env python3
"""Локальный демонстрационный Web-аналог; исходный Windows EXE не используется."""
from __future__ import annotations

import argparse
import html
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "demo.sqlite3"


def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)))")


def read_tasks(db_path: Path) -> list[tuple[int, str, int]]:
    with sqlite3.connect(db_path) as db:
        return db.execute("SELECT id, title, completed FROM tasks ORDER BY id").fetchall()


def page(db_path: Path, warning: str | None = None) -> bytes:
    items = []
    for task_id, title, completed in read_tasks(db_path):
        status = "[✓]" if completed else "[ ]"
        items.append(f'<li data-id="{task_id}"><label><input type="radio" name="task_id" value="{task_id}"> <span class="task-status">{status}</span> <span class="task-title">{html.escape(title)}</span></label></li>')
    warning_script = ("<script>window.addEventListener('load', function () { alert(" + json.dumps(warning, ensure_ascii=True) + "); });</script>") if warning else ""
    document = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Командный трекер задач — демо</title><style>
*{{box-sizing:border-box}} body{{font-family:system-ui,sans-serif;background:#eef2f6;color:#172434;margin:0;padding:28px}}
main{{max-width:650px;margin:auto;background:white;border:1px solid #ccd5e0;border-radius:12px;padding:24px;box-shadow:0 4px 20px #17243412}}
h1{{font-size:1.45rem;margin-top:0}} .hint{{color:#536579;font-size:.9rem}} .row{{display:flex;gap:8px;flex-wrap:wrap}}
input[type=text]{{flex:1;min-width:200px;padding:10px;border:1px solid #99aabe;border-radius:6px}}
button{{padding:10px 14px;border:0;border-radius:6px;background:#2459a8;color:white;cursor:pointer}} button:hover{{background:#1e477f}}
#delete{{background:#913c45}} ul{{padding:0;list-style:none;min-height:100px}} li{{border-bottom:1px solid #e0e7ef;padding:10px 4px;overflow-wrap:anywhere}}
label{{cursor:pointer}} .task-status{{font-family:monospace;font-size:1.1rem}} footer{{margin-top:24px;color:#65778a;font-size:.8rem}}
</style></head><body><main>
<h1>Командный трекер задач</h1><p class="hint">Локальное демонстрационное Web-приложение по пользовательской спецификации.</p>
<form method="post" action="/add" id="add-form"><label for="task-input">Текст задачи</label><div class="row"><input id="task-input" name="title" type="text" autocomplete="off"><button id="add" type="submit">Добавить задачу</button></div></form>
<h2>Список задач</h2><form method="post" id="action-form"><ul id="task-list">{''.join(items)}</ul><div class="row"><button id="complete" type="submit" formaction="/complete">Отметить выполненной</button><button id="delete" type="submit" formaction="/delete">Удалить задачу</button></div></form>
<footer>Данные сохраняются локально в SQLite. Выберите одну запись перед изменением.</footer></main>{warning_script}</body></html>'''
    return document.encode("utf-8")


class TaskHandler(BaseHTTPRequestHandler):
    server: "TaskServer"

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        self.show()

    def show(self, warning: str | None = None) -> None:
        body = page(self.server.db_path, warning)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path not in {"/add", "/complete", "/delete"}:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 1_000_000:
                raise ValueError("Некорректная длина запроса")
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        except (ValueError, UnicodeDecodeError):
            self.send_error(400)
            return
        warning = None
        with sqlite3.connect(self.server.db_path) as db:
            if self.path == "/add":
                title = fields.get("title", [""])[0]
                if not title.strip():
                    warning = "Текст задачи не может быть пустым!"
                else:
                    db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
            else:
                selected = fields.get("task_id", [""])[0]
                task = db.execute("SELECT completed FROM tasks WHERE id = ?", (selected,)).fetchone()
                if task is None:
                    warning = "Выберите задачу из списка!" if self.path == "/complete" else "Выберите задачу для удаления!"
                elif self.path == "/complete":
                    if task[0]:
                        warning = "Эта задача уже выполнена"
                    else:
                        db.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (selected,))
                else:
                    db.execute("DELETE FROM tasks WHERE id = ?", (selected,))
        if warning:
            self.show(warning)
        else:
            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()


class TaskServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], db_path: Path):
        self.db_path = Path(db_path).resolve()
        initialize(self.db_path)
        super().__init__(address, TaskHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Локальный демонстрационный трекер задач")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    server = TaskServer((args.host, args.port), args.db)
    print(f"Трекер доступен: http://{args.host}:{server.server_port}/; БД: {server.db_path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
