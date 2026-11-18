#!/bin/sh
# Записывает неизменённый вывод unittest и подлинный код возврата.
set -u
if [ "$#" -ne 1 ]; then echo 'Использование: scripts/capture.sh путь-к-журналу' >&2; exit 2; fi
(
    printf '$ python3 -B -m unittest discover -s tests -v\n'
    python3 -B -m unittest discover -s tests -v
    rc=$?
    printf '\nEXIT_CODE=%s\n' "$rc"
    exit "$rc"
) > "$1" 2>&1
rc=$?
cat "$1"
exit "$rc"
