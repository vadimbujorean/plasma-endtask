#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise only disposable child processes, never the user's applications."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

helper, automation = sys.argv[1:3]
env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_FORCE_STDERR_LOGGING': '1'}

result = subprocess.run([helper, '--check', '0', '1', '-1', 'invalid'], env=env, capture_output=True, text=True, timeout=5)
assert result.returncode == 1 and not result.stdout.strip()
print('PASS: invalid/system PIDs rejected')

for choice in ('cancel', 'terminate'):
    victim = subprocess.Popen(['sleep', '30'])
    try:
        check = subprocess.run([helper, '--check', str(victim.pid), str(victim.pid)], env=env, capture_output=True, text=True, timeout=5)
        assert check.returncode == 0, check.stderr
        assert len(check.stdout.strip().splitlines()) == 1
        assert victim.poll() is None
        dialog_env = {**env, 'LD_PRELOAD': automation, 'ENDTASK_TEST_CHOICE': choice}
        result = subprocess.run([helper, str(victim.pid)], env=dialog_env, capture_output=True, text=True, timeout=5)
        assert result.returncode == 0, result.stderr
        if choice == 'cancel':
            assert victim.poll() is None, 'Cancel unexpectedly killed the child'
        else:
            assert victim.wait(timeout=2) == -signal.SIGKILL
        print(f'PASS: confirmation {choice}; duplicate PID deduplicated')
    finally:
        if victim.poll() is None:
            victim.terminate()
            victim.wait()

# A disposable process deliberately named plasmashell verifies the denylist.
protected = subprocess.Popen([sys.executable, '-c',
    'import ctypes,time; ctypes.CDLL(None).prctl(15,b"plasmashell",0,0,0); time.sleep(30)'])
try:
    comm = Path(f'/proc/{protected.pid}/comm')
    for _ in range(100):
        if comm.read_text().strip() == 'plasmashell':
            break
        time.sleep(0.01)
    else:
        raise AssertionError('Could not set test process name')
    result = subprocess.run([helper, '--check', str(protected.pid)], env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and not result.stdout.strip()
    assert protected.poll() is None
    print('PASS: plasmashell-named process protected')
finally:
    protected.terminate()
    protected.wait()
