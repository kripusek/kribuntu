#!/usr/bin/env python3
"""Watch Steam's local counters without controlling Steam or any game."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0, '/usr/local/lib/kribuntu')
from kribuntu_steam import steam_downloads


def notify(name):
    state = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'kribuntu' / 'activity.jsonl'
    try:
        state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with state.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': datetime.datetime.now().isoformat(timespec='seconds'),
                                     'event': 'Steam: zakończono pobieranie i przygotowanie: ' + name}, ensure_ascii=False) + '\n')
    except OSError:
        pass
    if shutil.which('notify-send'):
        try:
            subprocess.run(['notify-send', 'Kribuntu: Steam', name + ' — pobieranie zakończone'],
                           timeout=5, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass


def completed(previous, current):
    return [name for key, (name, busy, _status) in current.items()
            if not busy and key in previous and previous[key][1]]


def main():
    previous = steam_downloads()
    while True:
        time.sleep(20)
        current = steam_downloads()
        for name in completed(previous, current):
            notify(name)
        previous = current


if __name__ == '__main__':
    main()
