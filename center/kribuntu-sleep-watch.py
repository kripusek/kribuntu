#!/usr/bin/env python3
"""Remember a small amount of context around suspend; never control games."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

sys.path.insert(0, '/usr/local/lib/kribuntu')
from kribuntu_steam import steam_downloads

STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'kribuntu' / 'sleep-context.json'


def battery():
    for path in sorted(Path('/sys/class/power_supply').glob('BAT*/capacity')):
        try:
            value = int(path.read_text().strip())
            if 0 <= value <= 100:
                return value
        except (OSError, ValueError):
            continue
    return None


def save_context():
    active = [name for name, busy, _status in steam_downloads().values() if busy][:3]
    data = {'time': datetime.datetime.now().isoformat(timespec='seconds'),
            'battery': battery(), 'downloads': active}
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temp = STATE.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, STATE)
    except OSError:
        pass


def wake_message(data):
    parts = []
    if isinstance(data.get('battery'), int):
        parts.append(f"Przed uśpieniem bateria miała {data['battery']}%.")
    downloads = data.get('downloads')
    if isinstance(downloads, list) and downloads:
        parts.append('Steam pobierał: ' + ', '.join(str(x) for x in downloads[:3]) + '.')
    parts.append('Sprawdź grę online — uśpienie nie zatrzymuje serwera gry.')
    return ' '.join(parts)


def notify_wake():
    try:
        data = json.loads(STATE.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return
        STATE.unlink()
    except (OSError, ValueError):
        return
    if shutil.which('notify-send'):
        try:
            subprocess.run(['notify-send', 'Kribuntu: witaj ponownie', wake_message(data)],
                           timeout=5, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            pass


def on_sleep(preparing):
    if preparing:
        save_context()
    else:
        notify_wake()


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    bus.add_signal_receiver(on_sleep, signal_name='PrepareForSleep',
                            dbus_interface='org.freedesktop.login1.Manager',
                            bus_name='org.freedesktop.login1', path='/org/freedesktop/login1')
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()
