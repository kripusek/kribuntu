#!/usr/bin/env python3
"""Watch local launcher data without controlling Steam, Heroic or games."""
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
from kribuntu_games import installed_games

STATE_DIR = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'kribuntu'
GAME_INDEX = STATE_DIR / 'games-index.json'


def notify(name):
    state = STATE_DIR / 'activity.jsonl'
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


def load_known_games():
    try:
        data = json.loads(GAME_INDEX.read_text(encoding='utf-8'))
        known = data.get('known') if isinstance(data, dict) else None
        if isinstance(known, list) and all(isinstance(key, str) for key in known):
            return set(known)
    except (OSError, ValueError):
        pass
    return None


def save_known_games(known):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = GAME_INDEX.with_suffix('.tmp')
        temporary.write_text(json.dumps({'known': sorted(known)}), encoding='utf-8')
        os.replace(temporary, GAME_INDEX)
    except OSError:
        pass


def notify_games(games, initial=False):
    if not games:
        return
    names = [game['title'][:100] for game in games[:3]]
    text = ('Znalazłem gry: ' if initial else 'Wykryłem grę: ') + ', '.join(names)
    if len(games) > len(names):
        text += f' i {len(games) - len(names)} więcej'
    text += '. Zobacz bibliotekę w Centrum Kribuntu.'
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (STATE_DIR / 'activity.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': datetime.datetime.now().isoformat(timespec='seconds'),
                                     'event': text}, ensure_ascii=False) + '\n')
    except OSError:
        pass
    if shutil.which('notify-send'):
        try:
            subprocess.run(['notify-send', 'Kripusek', text], timeout=5, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass


def main():
    previous = steam_downloads()
    games = installed_games()
    current_keys = {game['key'] for game in games}
    known = load_known_games()
    if known is None:
        known = current_keys
        save_known_games(known)
        notify_games(games, initial=True)
    missing_counts = {}
    while True:
        time.sleep(20)
        current = steam_downloads()
        for name in completed(previous, current):
            notify(name)
        previous = current
        games = installed_games()
        current_keys = {game['key'] for game in games}
        new = [game for game in games if game['key'] not in known]
        if new:
            notify_games(new)
        updated = known | current_keys
        for key in known - current_keys:
            missing_counts[key] = missing_counts.get(key, 0) + 1
            if missing_counts[key] >= 3:
                updated.discard(key)
                missing_counts.pop(key, None)
        for key in current_keys:
            missing_counts.pop(key, None)
        if updated != known:
            known = updated
            save_known_games(known)


if __name__ == '__main__':
    main()
