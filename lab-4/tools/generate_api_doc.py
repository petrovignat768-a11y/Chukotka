#!/usr/bin/env python3
"""Extract documented public C++ declarations into a short Markdown API reference."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / "include" / "tracker" / "task_tracker.h"
OUTPUT = ROOT / "APIDOC.md"


def main() -> None:
    rows = []
    description = None
    for raw in HEADER.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("/// "):
            if description is not None:
                raise ValueError("Expected a declaration after a documentation comment")
            description = line[4:].strip()
        elif description is not None:
            if not line or line in {"private:", "public:"}:
                raise ValueError("Documentation comment is not followed by a declaration")
            declaration = line.rstrip("{,;").strip()
            rows.append((declaration, description))
            description = None
    if description is not None or not rows:
        raise ValueError("Incomplete or empty API documentation")

    output = [
        "# Документация публичного API модели",
        "",
        "Автоматически извлечено скриптом `tools/generate_api_doc.py` из `include/tracker/task_tracker.h`. "
        "Полные контракты и допущения: [SPECIFICATION.md](SPECIFICATION.md).",
        "",
        "| Объявление | Описание |",
        "|---|---|",
    ]
    for declaration, text in rows:
        output.append(f"| `{declaration}` | {text} |")
    OUTPUT.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Written {OUTPUT} ({len(rows)} documented declarations)")


if __name__ == "__main__":
    main()
