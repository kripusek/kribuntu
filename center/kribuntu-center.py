#!/usr/bin/env python3
"""Centrum Kribuntu: gry, stan laptopa i diagnostyka."""
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

from PyQt5.QtCore import Qt, QTimer, QSize, QSettings
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget)

HOME = Path.home()
STATE = Path(os.environ.get('XDG_STATE_HOME', HOME / '.local/state')) / 'kribuntu' / 'activity.jsonl'


def command(*args, timeout=2):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False,
                                env={**os.environ, 'LC_ALL': 'C'})
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 127, ''


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, ValueError):
        return ''


def cpu_counters():
    lines = read('/proc/stat').splitlines()
    try:
        total = sum(int(value) for value in lines[0].split()[1:9])
    except (IndexError, ValueError):
        return None
    processes = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        data = read(path)
        pos = data.rfind(')')
        if pos < 0:
            continue
        fields = data[pos + 1:].split()
        try:
            processes[path.parent.name] = (fields[19], int(fields[11]) + int(fields[12]),
                                           data[data.find('(') + 1:pos])
        except (IndexError, ValueError):
            continue
    return time.monotonic(), total, processes


def cpu_changes(previous, current):
    if previous is None or current is None:
        return 'Zbieram pierwszy pomiar procesora.'
    elapsed = current[0] - previous[0]
    total = current[1] - previous[1]
    if total <= 0 or elapsed <= 0:
        return 'Brak danych z kolejnego pomiaru.'
    cores = os.cpu_count() or 1
    usage = []
    for pid, (started, ticks, name) in current[2].items():
        old = previous[2].get(pid)
        if old and old[0] == started and ticks >= old[1]:
            pct = 100 * cores * (ticks - old[1]) / total
            if pct >= 0.1:
                usage.append((pct, name))
    rows = [f'{pct:.1f}%  {name}' for pct, name in sorted(usage, reverse=True)[:4]]
    return f'Ostatnie {elapsed:.0f} s (100% = jeden rdzeń)\n' + ('\n'.join(rows) if rows else 'Brak mierzalnego obciążenia procesów.')


def record(event):
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with STATE.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': datetime.datetime.now().isoformat(timespec='seconds'),
                                     'event': event}, ensure_ascii=False) + '\n')
    except OSError:
        pass


def history():
    try:
        with STATE.open(encoding='utf-8') as f:
            rows = f.readlines()[-12:]
        entries = []
        for row in reversed(rows):
            try:
                item = json.loads(row)
                entries.append(item['time'].replace('T', ' ') + '  ·  ' + item['event'])
            except (ValueError, KeyError, TypeError):
                continue
        return '\n'.join(entries) or 'Tu pojawią się działania wykonane w Centrum.'
    except OSError:
        return 'Tu pojawią się działania wykonane w Centrum.'


def snapshot():
    power = Path('/sys/class/power_supply')
    batteries = sorted(power.glob('BAT*')) if power.exists() else []
    if batteries:
        b = batteries[0]
        capacity = read(b / 'capacity')
        status = {'Charging': 'ładowanie', 'Discharging': 'na baterii', 'Full': 'naładowana',
                  'Not charging': 'nie ładuje'}.get(read(b / 'status'), read(b / 'status') or 'stan nieznany')
        charge = f'{capacity}% · {status}' if capacity else status
        full, design = read(b / 'energy_full'), read(b / 'energy_full_design')
        try:
            if int(design) > 0:
                charge += f'\nKondycja według baterii: {100 * int(full) / int(design):.0f}% pojemności projektowej'
        except ValueError:
            pass
        start, end = read(b / 'charge_start_threshold'), read(b / 'charge_stop_threshold')
        if start and end:
            charge += f'\nProgi ładowania: {start}–{end}%'
    else:
        charge = 'Nie wykryto baterii'
    sensors = []
    sensor_names = {'k10temp': 'CPU (Tctl)', 'amdgpu': 'GPU (edge)', 'nvme': 'SSD'}
    for zone in Path('/sys/class/hwmon').glob('hwmon*'):
        typ, val = read(zone / 'name'), read(zone / 'temp1_input')
        try:
            temp = int(val) / 1000
            if typ in sensor_names and 0 < temp < 120:
                sensors.append((sensor_names[typ], temp))
        except ValueError:
            pass
    temptext = ', '.join(f'{n}: {v:.0f}°C' for n, v in sensors[:3]) or 'Brak odczytu temperatury'
    try:
        disk = shutil.disk_usage(HOME)
        storage = f'{disk.free / (1024 ** 3):.0f} GiB wolnego w systemie plików katalogu domowego'
    except OSError:
        storage = 'Brak odczytu wolnego miejsca'
    rc, active = command('systemctl', '--user', 'is-active', 'ir-camera.service')
    ir = rc == 0 and active == 'active'
    _, gaze = command('systemctl', 'is-active', 'gazed.service')
    if ir:
        camera = 'Kamera IR dla Discorda: WŁĄCZONA. Może zajmować kamerę potrzebną Gaze.'
    elif active == 'failed':
        camera = 'Kamera IR dla Discorda: usługa zatrzymana ze stanem błędu.'
    else:
        camera = 'Kamera IR dla Discorda: wyłączona lub niedostępna.'
    if gaze == 'active':
        camera += '\nGaze: usługa działa. Rozpoznanie zależy od dostępności kamery.'
    sink_rc, sink = command('pactl', 'get-default-sink')
    mute_rc, mute = command('pactl', 'get-sink-mute', '@DEFAULT_SINK@')
    if sink_rc != 0 or not sink:
        audio = 'Nie udało się odczytać domyślnego wyjścia dźwięku.'
    else:
        mute_text = {'Mute: yes': 'wyciszone', 'Mute: no': 'niewyciszone'}.get(mute, 'stan wyciszenia nieznany') if mute_rc == 0 else 'stan wyciszenia nieznany'
        audio = f'Wyjście: {sink}\nStan: {mute_text}. Nie sprawdzono, czy dźwięk jest słyszalny.'
    return charge, temptext, camera, storage, audio


class Center(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Centrum Kribuntu')
        self.resize(1000, 720)
        self.setMinimumSize(680, 520)
        base = QWidget(); self.setCentralWidget(base)
        outer = QVBoxLayout(base); outer.setContentsMargins(32, 26, 32, 26); outer.setSpacing(14)
        header = QHBoxLayout(); title_area = QVBoxLayout()
        title = QLabel('KRIBUNTU'); title.setObjectName('title'); title_area.addWidget(title)
        subtitle = QLabel('Twój laptop, gry i ostatnie działania'); subtitle.setObjectName('subtitle'); title_area.addWidget(subtitle)
        title_area.addStretch(); header.addLayout(title_area, 1)
        self.settings = QSettings('Kribuntu', 'Center')
        mascot_path = Path('/usr/local/share/kribuntu/kripusek.gif')
        if not mascot_path.is_file():
            mascot_path = Path(__file__).resolve().parent.parent / 'theme/kripusek.gif'
        self.movie = QMovie(str(mascot_path))
        if self.movie.isValid():
            mascot_area = QVBoxLayout(); mascot = QLabel(); mascot.setFixedSize(76, 76)
            self.movie.setScaledSize(QSize(76, 76)); mascot.setMovie(self.movie); mascot_area.addWidget(mascot, alignment=Qt.AlignHCenter)
            animation = QCheckBox('Animacja'); animation.setChecked(self.settings.value('animate_mascot', True, type=bool))
            animation.toggled.connect(self.set_animation); mascot_area.addWidget(animation); header.addLayout(mascot_area)
            self.set_animation(animation.isChecked(), save=False)
        outer.addLayout(header)
        self.tabs = QTabWidget(); outer.addWidget(self.tabs)
        home = QWidget(); layout = QVBoxLayout(home); grid = QGridLayout(); layout.addLayout(grid)
        items = [
            ('STEAM', 'Tryb gier', ['flatpak', 'run', 'com.valvesoftware.Steam', '-gamepadui']),
            ('HEROIC', 'Epic Games i GOG', ['flatpak', 'run', 'com.heroicgameslauncher.hgl']),
            ('DISCORD', 'Rozmowy ze znajomymi', ['flatpak', 'run', 'com.discordapp.Discord']),
            ('AKTUALIZACJE', 'Motyw i narzędzia Kribuntu', ['/usr/local/bin/kribuntu-update']),
            ('TEST SPRZĘTU', 'Sieć, kamera i czytnik', ['/usr/local/bin/kribuntu-hardware-check']),
            ('USTAWIENIA', 'Ustawienia KDE', [shutil.which('systemsettings') or 'systemsettings5']),
        ]
        for index, (name, desc, cmd) in enumerate(items):
            button = QPushButton(name + '\n' + desc); button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, c=cmd, n=name: self.launch(c, n))
            grid.addWidget(button, index // 3, index % 3)
        layout.addStretch(); self.tabs.addTab(home, 'Start')
        info = QWidget(); il = QVBoxLayout(info)
        heading = QLabel('Co się dzieje na laptopie?'); heading.setObjectName('heading'); il.addWidget(heading)
        note = QLabel('Bieżące odczyty pomagają znaleźć przyczynę. Same nie są diagnozą.'); note.setWordWrap(True); il.addWidget(note)
        self.battery = QLabel(); self.temperature = QLabel(); self.processes = QLabel(); self.camera = QLabel(); self.storage = QLabel(); self.audio = QLabel(); self.changes = QLabel()
        for widget in (self.battery, self.temperature, self.processes, self.camera, self.storage, self.audio, self.changes):
            widget.setTextFormat(Qt.PlainText); widget.setWordWrap(True); widget.setObjectName('card'); widget.setTextInteractionFlags(Qt.TextSelectableByMouse); il.addWidget(widget)
        row = QHBoxLayout()
        refresh = QPushButton('Odśwież'); refresh.clicked.connect(self.refresh); row.addWidget(refresh)
        toggle = QPushButton('Kamera IR dla Discorda'); toggle.clicked.connect(self.toggle_camera); row.addWidget(toggle)
        gaze = QPushButton('Ustawienia twarzy'); gaze.clicked.connect(lambda: self.launch(['gaze-gui'], 'Ustawienia twarzy'))
        row.addWidget(gaze)
        il.addLayout(row); il.addStretch()
        explain_button = QPushButton('Kripusek wyjaśnia kamerę i dźwięk'); explain_button.clicked.connect(self.explain)
        il.addWidget(explain_button)
        info_scroll = QScrollArea(); info_scroll.setWidgetResizable(True); info_scroll.setWidget(info)
        self.tabs.addTab(info_scroll, 'Laptop i kamera')
        logtab = QWidget(); ll = QVBoxLayout(logtab)
        lh = QLabel('Ostatnie działania w Centrum'); lh.setObjectName('heading'); ll.addWidget(lh)
        explain = QLabel('Zapis lokalny obejmuje tylko przyciski użyte w Centrum. Nie jest historią całego systemu.'); explain.setWordWrap(True); ll.addWidget(explain)
        self.log = QLabel(); self.log.setWordWrap(True); self.log.setAlignment(Qt.AlignTop | Qt.AlignLeft); self.log.setObjectName('card'); self.log.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(self.log); ll.addWidget(scroll)
        self.tabs.addTab(logtab, 'Ślady')
        downloads_tab = QWidget(); dl = QVBoxLayout(downloads_tab)
        dh = QLabel('Kripusek pilnuje Steama'); dh.setObjectName('heading'); dl.addWidget(dh)
        dn = QLabel('Dane pochodzą z plików lokalnych bibliotek Steam w domyślnych lokalizacjach. Powiadomienia wysyła usługa użytkownika; inne biblioteki mogą nie być widoczne.')
        dn.setWordWrap(True); dl.addWidget(dn)
        self.watch_status = QLabel(); self.watch_status.setWordWrap(True); dl.addWidget(self.watch_status)
        self.downloads = QLabel(); self.downloads.setObjectName('card'); self.downloads.setTextFormat(Qt.PlainText); self.downloads.setWordWrap(True); self.downloads.setAlignment(Qt.AlignTop | Qt.AlignLeft); dl.addWidget(self.downloads)
        dl.addStretch(); self.tabs.addTab(downloads_tab, 'Pobieranie')
        self.setStyleSheet('''
          QMainWindow, QWidget { background:#14141c; color:#f7f7fa; font-family:sans-serif; }
          QLabel#title { font-size:34px; font-weight:800; letter-spacing:3px; }
          QLabel#subtitle { color:#c4c4ce; font-size:16px; }
          QLabel#heading { font-size:22px; font-weight:bold; }
          QLabel#card { background:#22232d; border:1px solid #48424c; border-radius:10px; padding:13px; font-size:14px; }
          QPushButton { background:#252631; border:1px solid #494653; border-radius:10px; padding:14px; text-align:left; font-size:15px; font-weight:bold; min-height:38px; }
          QPushButton:hover, QPushButton:focus { background:#8d1f35; border:2px solid #ff4e68; }
          QTabBar::tab { background:#252631; padding:10px 22px; border-radius:6px; }
          QTabBar::tab:selected { background:#a41d38; }
        ''')
        self.previous = None
        self.previous_cpu = None
        self.refresh(); self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(15000)

    def set_animation(self, enabled, save=True):
        if enabled:
            self.movie.start()
        else:
            self.movie.stop()
            self.movie.jumpToFrame(0)
        if save:
            self.settings.setValue('animate_mascot', enabled)

    def refresh(self):
        charge, temp, camera, storage, audio = snapshot()
        current_cpu = cpu_counters()
        proc = cpu_changes(self.previous_cpu, current_cpu)
        self.previous_cpu = current_cpu
        self.battery.setText('BATERIA  ·  ' + charge)
        self.temperature.setText('TEMPERATURA  ·  ' + temp)
        self.processes.setText('PROCESY  ·  bieżący pomiar CPU\n' + proc)
        self.camera.setText(camera)
        self.storage.setText('DYSK  ·  ' + storage)
        self.audio.setText('DŹWIĘK  ·  ' + audio)
        current = (charge, camera)
        if self.previous is None:
            changes = 'ZMIANY  ·  Czekam na kolejny odczyt baterii i kamery.'
        else:
            details = []
            if current[0] != self.previous[0]:
                details.append('Zmienił się odczyt baterii: ' + charge.split('\n')[0])
            if current[1] != self.previous[1]:
                details.append('Zmienił się stan kamery lub usługi Gaze.')
            changes = 'ZMIANY  ·  ' + (' '.join(details) if details else 'Bateria i stan kamery bez zmian od poprzedniego odczytu.')
        self.changes.setText(changes)
        self.previous = current
        downloads = steam_downloads()
        watch_rc, watch_state = command('systemctl', '--user', 'is-active', 'kribuntu-steam-watch.service')
        self.watch_status.setText('Monitor w tle: działa.' if watch_rc == 0 and watch_state == 'active'
                                  else 'Monitor w tle: nie jest uruchomiony. Uruchom go lub wyloguj się i zaloguj ponownie po aktualizacji.')
        rows = [f'{name}\n{status}' for name, busy, status in downloads.values()]
        self.downloads.setText('\n\n'.join(rows) if rows else 'Brak danych o pobieraniu w domyślnych bibliotekach Steam.')
        self.log.setText(history())

    def explain(self):
        self.refresh()
        camera = self.camera.text()
        audio = self.audio.text()
        advice = []
        if 'WŁĄCZONA' in camera and 'Gaze: usługa działa' in camera:
            advice.append('Konwerter Discorda i Gaze używają tej samej kamery IR. Jeśli rozpoznawanie nie rusza, wyłącz konwerter przyciskiem w Centrum i spróbuj ponownie.')
        elif 'stanem błędu' in camera:
            advice.append('Usługa kamery Discorda zakończyła się błędem lub została zatrzymana w sposób zgłoszony jako błąd. Sprawdź jej stan przed ponownym uruchomieniem.')
        else:
            advice.append('Konwerter Discorda nie jest obecnie aktywny według systemd. To samo nie dowodzi, że kamera jest dostępna dla Gaze.')
        if 'Stan: wyciszone.' in audio:
            advice.append('Domyślne wyjście dźwięku jest wyciszone. Możesz je odciszyć w ustawieniach dźwięku.')
        elif 'niewyciszone' in audio:
            advice.append('Domyślne wyjście nie jest wyciszone. Jeśli nadal nic nie słychać, sprawdź wybrane urządzenie i jego połączenie.')
        else:
            advice.append('Nie udało się ustalić stanu wyciszenia. Sprawdź ustawienia dźwięku.')
        QMessageBox.information(self, 'Kripusek wyjaśnia', '\n\n'.join(advice))

    def toggle_camera(self):
        script = HOME / '.local/bin/ir-camera'
        if not script.is_file():
            QMessageBox.information(self, 'Kamera IR', 'Nie znaleziono przełącznika kamery Discorda. Gaze nadal działa niezależnie.')
            return
        if QMessageBox.question(self, 'Kamera IR', 'Przełączyć kamerę IR dla Discorda? Gdy jest włączona, Gaze może nie móc użyć kamery do logowania.') != QMessageBox.Yes:
            return
        self.launch([str(script)], 'Przełącznik kamery IR dla Discorda')
        QTimer.singleShot(2500, self.refresh)

    def launch(self, command_line, name):
        if not shutil.which(command_line[0]):
            QMessageBox.warning(self, 'Kribuntu', 'Brakuje programu potrzebnego do uruchomienia tej funkcji.')
            return
        try:
            subprocess.Popen(command_line, start_new_session=True)
            record('Uruchomiono: ' + name)
            self.log.setText(history())
        except OSError as exc:
            QMessageBox.warning(self, 'Kribuntu', 'Nie udało się uruchomić aplikacji: ' + str(exc))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Center(); window.show()
    sys.exit(app.exec_())
