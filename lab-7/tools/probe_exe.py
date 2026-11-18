#!/usr/bin/env python3
"""Диагностика запуска копии PE на Linux. Не выполняет UI или RFT-тесты."""
from pathlib import Path
import hashlib
import os
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'original' / 'todo_app.exe'
RUN = ROOT / 'test_run'

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    if platform.system() != 'Linux':
        print('Этот диагностический сценарий рассчитан на Linux; остановка.')
        return 2
    for name in ('home', 'tmp', 'config', 'cache', 'data'):
        (RUN / name).mkdir(parents=True, exist_ok=True)
    copy = RUN / 'todo_app.exe'
    shutil.copyfile(SOURCE, copy)
    copy.chmod(copy.stat().st_mode | 0o100)
    original_sha, copy_sha = digest(SOURCE), digest(copy)
    print('Source SHA256:   ', original_sha, flush=True)
    print('Test copy SHA256:', copy_sha, flush=True)
    print('Hashes equal:    ', original_sha == copy_sha, flush=True)
    if original_sha != copy_sha:
        print('BLOCKED: checksum mismatch')
        return 2
    env = os.environ.copy()
    env.update(HOME=str(RUN/'home'), TMPDIR=str(RUN/'tmp'), XDG_CONFIG_HOME=str(RUN/'config'),
               XDG_CACHE_HOME=str(RUN/'cache'), XDG_DATA_HOME=str(RUN/'data'))
    print('Command: ', copy, flush=True)
    print('CWD: ', RUN, flush=True)
    try:
        proc = subprocess.run([str(copy)], cwd=RUN, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        print('EXIT CODE:', proc.returncode)
        print('STDOUT:', repr(proc.stdout))
        print('STDERR:', repr(proc.stderr))
        print('Даже успешный запуск не равен функциональному или RFT-тесту.')
        return 0 if proc.returncode == 0 else 2
    except OSError as e:
        print('BLOCKED:', type(e).__name__, 'errno=', e.errno, ':', str(e))
        return 2
    except subprocess.TimeoutExpired as e:
        print('TIMEOUT after', e.timeout, 'seconds; UI not verified')
        return 2

if __name__ == '__main__':
    sys.exit(main())
