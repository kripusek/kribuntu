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
from kribuntu_games import installed_games, launch_command

from PyQt5.QtCore import Qt, QTimer, QSize, QSettings, QProcess, QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

HOME = Path.home()
STATE = Path(os.environ.get('XDG_STATE_HOME', HOME / '.local/state')) / 'kribuntu' / 'activity.jsonl'
UNDO = STATE.parent / 'camera-undo.json'


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


def camera_running():
    rc, state = command('systemctl', '--user', 'is-active', 'ir-camera.service')
    if rc == 0 and state == 'active':
        return True
    if state in ('inactive', 'failed'):
        return False
    return None


def load_camera_undo():
    try:
        data = json.loads(UNDO.read_text(encoding='utf-8'))
        if (isinstance(data, dict) and isinstance(data.get('before'), bool)
                and isinstance(data.get('after'), bool) and data['before'] != data['after']):
            return data
    except (OSError, ValueError):
        pass
    return None


def save_camera_undo(before, after):
    try:
        UNDO.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = UNDO.with_suffix('.tmp')
        temporary.write_text(json.dumps({'before': before, 'after': after}), encoding='utf-8')
        os.replace(temporary, UNDO)
        return True
    except OSError:
        return False


def talos_report(home):
    config = home / 'Games/Heroic/The Talos Principle/Content/Talos/Config/CheckDriver.lua'
    backup = config.with_name('CheckDriver.lua.before-proton-fix')
    if not config.is_file():
        return ('Nie znaleziono pliku gry w domyślnym katalogu Heroica. '
                'Gra może być zainstalowana gdzie indziej; nie zmieniono żadnych plików.')
    try:
        content = config.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return 'Plik gry istnieje, ale nie udało się go odczytać. Nie zmieniono żadnych plików.'
    marker = ('local bProtonSyntheticAMD' in content and 'gfx_iDriverVersion==1011' in content
              and 'not bProtonSyntheticAMD' in content)
    if marker:
        result = ('W pliku wykryto poprawkę porównania wersji sterownika dla Proton/DXVK. '
                  'Obecność poprawki nie potwierdza, że gra uruchomi się poprawnie.')
    else:
        result = ('W pliku nie znaleziono rozpoznawalnej poprawki porównania wersji sterownika. '
                  'Aktualizacja lub sprawdzenie plików gry mogło ją zastąpić; nie zmieniono gry.')
    result += '\n\nKopia wcześniejszego pliku: ' + ('znaleziona.' if backup.is_file() else 'nie znaleziona.')
    return result


def battery_projection(battery_dir, reserve=0.15):
    """Return minutes above reserve at current draw, or an explanation."""
    if read(battery_dir / 'status') != 'Discharging':
        return None, 'Prognoza jest dostępna podczas pracy na baterii.'
    for now_name, full_name, rate_name in (
            ('energy_now', 'energy_full', 'power_now'),
            ('charge_now', 'charge_full', 'current_now')):
        try:
            now = int(read(battery_dir / now_name))
            full = int(read(battery_dir / full_name))
            rate = int(read(battery_dir / rate_name))
            if now < 0 or full <= 0 or rate <= 0 or now > full * 1.3:
                continue
            available = max(0.0, now - full * reserve)
            return available / rate * 60, None
        except ValueError:
            continue
    return None, 'Bateria nie udostępnia wiarygodnego bieżącego poboru.'


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


class GameScanSignals(QObject):
    finished = pyqtSignal(object)


class GameScan(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = GameScanSignals()

    def run(self):
        try:
            games = installed_games()
        except Exception:
            games = None
        self.signals.finished.emit(games)


class LaunchCard(QPushButton):
    def __init__(self, title, description, index):
        super().__init__(title + '\n' + description + '\n\nOTWÓRZ  →')
        self.setObjectName('launchCard')
        self.setAccessibleName(title + ': ' + description)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(130)
        self.setToolTip(description)


class Center(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Centrum Kribuntu')
        self.resize(1000, 720)
        self.setMinimumSize(680, 520)
        base = QWidget(); self.setCentralWidget(base)
        outer = QVBoxLayout(base); outer.setContentsMargins(28, 22, 28, 22); outer.setSpacing(14)
        header = QHBoxLayout(); title_area = QVBoxLayout()
        eyebrow = QLabel('TWOJA PRZESTRZEŃ'); eyebrow.setObjectName('eyebrow'); title_area.addWidget(eyebrow)
        title = QLabel('KRIBUNTU'); title.setObjectName('title'); title_area.addWidget(title)
        subtitle = QLabel('Centrum gier i laptopa'); subtitle.setObjectName('subtitle'); title_area.addWidget(subtitle)
        header.addLayout(title_area, 1)
        self.settings = QSettings('Kribuntu', 'Center')
        assistant = QFrame(); assistant.setObjectName('assistant'); assistant_layout = QHBoxLayout(assistant)
        assistant_layout.setContentsMargins(12, 10, 12, 10); assistant_layout.setSpacing(10)
        mascot_path = Path('/usr/local/share/kribuntu/kripusek.gif')
        if not mascot_path.is_file():
            mascot_path = Path(__file__).resolve().parent.parent / 'theme/kripusek.gif'
        self.movie = QMovie(str(mascot_path))
        if self.movie.isValid():
            mascot = QLabel(); mascot.setFixedSize(58, 58)
            self.movie.setScaledSize(QSize(58, 58)); mascot.setMovie(self.movie); assistant_layout.addWidget(mascot)
        assistant_words = QVBoxLayout(); assistant_words.setSpacing(3)
        assistant_title = QLabel('KRIPUSEK  ·  POMOCNIK'); assistant_title.setObjectName('assistantTitle'); assistant_words.addWidget(assistant_title)
        self.assistant_text = QLabel('Cześć! Zaraz sprawdzę Twoje gry.'); self.assistant_text.setObjectName('assistantText')
        self.assistant_text.setTextFormat(Qt.PlainText); self.assistant_text.setWordWrap(True); self.assistant_text.setMaximumWidth(300)
        assistant_words.addWidget(self.assistant_text)
        assistant_actions = QHBoxLayout(); assistant_actions.setSpacing(12)
        tip_button = QPushButton('Podpowiedź'); tip_button.setObjectName('assistantButton'); tip_button.clicked.connect(self.show_tip)
        assistant_actions.addWidget(tip_button)
        if self.movie.isValid():
            animation = QCheckBox('Animacja'); animation.setChecked(self.settings.value('animate_mascot', True, type=bool))
            animation.toggled.connect(self.set_animation); assistant_actions.addWidget(animation)
            self.set_animation(animation.isChecked(), save=False)
        assistant_actions.addStretch(); assistant_words.addLayout(assistant_actions); assistant_layout.addLayout(assistant_words)
        header.addWidget(assistant)
        outer.addLayout(header)
        self.tabs = QTabWidget(); outer.addWidget(self.tabs, 1)
        home = QWidget(); layout = QVBoxLayout(home); layout.setContentsMargins(18, 18, 18, 18); layout.setSpacing(14)
        hero = QFrame(); hero.setObjectName('hero'); hero_layout = QVBoxLayout(hero); hero_layout.setContentsMargins(22, 18, 22, 18); hero_layout.setSpacing(4)
        hero_eyebrow = QLabel('CENTRUM  /  START'); hero_eyebrow.setObjectName('heroEyebrow'); hero_layout.addWidget(hero_eyebrow)
        hero_title = QLabel('Wszystko w jednym miejscu.'); hero_title.setObjectName('heroTitle'); hero_title.setWordWrap(True); hero_layout.addWidget(hero_title)
        self.home_status = QLabel('Sprawdzam stan laptopa…'); self.home_status.setObjectName('heroStatus'); self.home_status.setWordWrap(True); hero_layout.addWidget(self.home_status)
        layout.addWidget(hero)
        games_head = QHBoxLayout(); games_label = QLabel('Twoje gry'); games_label.setObjectName('sectionTitle'); games_head.addWidget(games_label)
        games_head.addStretch(); self.library_link = QPushButton('Zobacz bibliotekę  →'); self.library_link.setObjectName('textButton')
        self.library_link.clicked.connect(lambda: self.tabs.setCurrentWidget(self.games_page)); games_head.addWidget(self.library_link); layout.addLayout(games_head)
        self.featured_layout = QHBoxLayout(); self.featured_layout.setSpacing(10); layout.addLayout(self.featured_layout)
        quick_label = QLabel('SZYBKI DOSTĘP'); quick_label.setObjectName('sectionEyebrow'); layout.addWidget(quick_label)
        grid = QGridLayout(); grid.setSpacing(10); layout.addLayout(grid)
        items = [
            ('STEAM', 'Tryb gier', ['flatpak', 'run', 'com.valvesoftware.Steam', '-gamepadui']),
            ('HEROIC', 'Epic Games i GOG', ['flatpak', 'run', 'com.heroicgameslauncher.hgl']),
            ('DISCORD', 'Rozmowy ze znajomymi', ['flatpak', 'run', 'com.discordapp.Discord']),
            ('AKTUALIZACJE', 'Motyw i narzędzia Kribuntu', ['/usr/local/bin/kribuntu-update']),
            ('TEST SPRZĘTU', 'Sieć, kamera i czytnik', ['/usr/local/bin/kribuntu-hardware-check']),
            ('USTAWIENIA', 'Ustawienia KDE', [shutil.which('systemsettings') or 'systemsettings5']),
            ('BLENDER', 'Modele 3D i animacje', ['blender']),
            ('OBS STUDIO', 'Nagrywanie i streaming', ['flatpak', 'run', 'com.obsproject.Studio']),
            ('AUDACITY', 'Nagrywanie i edycja dźwięku', ['audacity']),
            ('GIMP', 'Grafika i tekstury', ['flatpak', 'run', 'org.gimp.GIMP']),
            ('INKSCAPE', 'Grafika wektorowa', ['inkscape']),
        ]
        for index, (name, desc, cmd) in enumerate(items):
            button = LaunchCard(name, desc, index + 1)
            button.clicked.connect(lambda checked=False, c=cmd, n=name: self.launch(c, n))
            grid.addWidget(button, index // 3, index % 3)
        layout.addStretch()
        home_scroll = QScrollArea(); home_scroll.setWidgetResizable(True); home_scroll.setWidget(home)
        self.tabs.addTab(home_scroll, 'Start')
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
        undo_button = QPushButton('Cofnij ostatnią zmianę kamery IR z Centrum'); undo_button.clicked.connect(self.undo_camera); ll.addWidget(undo_button)
        self.tabs.addTab(logtab, 'Ślady')
        games_tab = QWidget(); gl = QVBoxLayout(games_tab)
        gh = QLabel('Twoja biblioteka'); gh.setObjectName('heading'); gl.addWidget(gh)
        gd = QLabel('Zainstalowane gry ze Steama i Heroica. Lista odświeża się automatycznie; wybierz grę, aby ją uruchomić.')
        gd.setWordWrap(True); gl.addWidget(gd)
        self.library_status = QLabel('Szukam zainstalowanych gier…'); self.library_status.setObjectName('subtitle'); gl.addWidget(self.library_status)
        self.library = QListWidget(); self.library.setObjectName('library'); self.library.setMinimumHeight(170)
        self.library.itemDoubleClicked.connect(lambda _item: self.launch_selected_game())
        gl.addWidget(self.library)
        library_actions = QHBoxLayout()
        play = QPushButton('Uruchom wybraną grę'); play.clicked.connect(self.launch_selected_game); library_actions.addWidget(play)
        refresh_games = QPushButton('Odśwież bibliotekę'); refresh_games.clicked.connect(self.request_game_scan); library_actions.addWidget(refresh_games)
        gl.addLayout(library_actions)
        diag_label = QLabel('SPRAWDŹ GRĘ'); diag_label.setObjectName('sectionEyebrow'); gl.addWidget(diag_label)
        check_talos = QPushButton('Sprawdź poprawkę The Talos Principle')
        check_talos.clicked.connect(self.check_talos); gl.addWidget(check_talos)
        self.game_report = QLabel('Wybierz sprawdzenie, aby zobaczyć wynik.'); self.game_report.setTextFormat(Qt.PlainText)
        self.game_report.setWordWrap(True); self.game_report.setObjectName('card'); self.game_report.setTextInteractionFlags(Qt.TextSelectableByMouse); gl.addWidget(self.game_report)
        gl.addStretch(); self.games_page = QScrollArea(); self.games_page.setWidgetResizable(True); self.games_page.setWidget(games_tab)
        self.tabs.addTab(self.games_page, 'Gry')
        plan_tab = QWidget(); pl = QVBoxLayout(plan_tab)
        ph = QLabel('Kripusek: czy zdążę?'); ph.setObjectName('heading'); pl.addWidget(ph)
        pn = QLabel('Porównaj swój plan z szacowanym czasem na baterii. Kripusek zostawia 15% zapasu i zakłada taki sam pobór energii jak w tej chwili.')
        pn.setWordWrap(True); pl.addWidget(pn)
        plan_row = QHBoxLayout(); plan_row.addWidget(QLabel('Potrzebuję jeszcze:'))
        self.plan_minutes = QSpinBox(); self.plan_minutes.setRange(5, 480); self.plan_minutes.setSingleStep(15); self.plan_minutes.setSuffix(' min')
        self.plan_minutes.setValue(self.settings.value('plan_minutes', 60, type=int)); plan_row.addWidget(self.plan_minutes); plan_row.addStretch(); pl.addLayout(plan_row)
        self.plan_result = QLabel(); self.plan_result.setTextFormat(Qt.PlainText); self.plan_result.setWordWrap(True); self.plan_result.setObjectName('card'); pl.addWidget(self.plan_result)
        pl.addStretch(); self.tabs.addTab(plan_tab, 'Czy zdążę?')
        self.plan_minutes.valueChanged.connect(self.update_plan)
        downloads_tab = QWidget(); dl = QVBoxLayout(downloads_tab)
        dh = QLabel('Kripusek pilnuje Steama'); dh.setObjectName('heading'); dl.addWidget(dh)
        dn = QLabel('Dane pochodzą z plików lokalnych bibliotek Steam w domyślnych lokalizacjach. Powiadomienia wysyła usługa użytkownika; inne biblioteki mogą nie być widoczne.')
        dn.setWordWrap(True); dl.addWidget(dn)
        self.watch_status = QLabel(); self.watch_status.setWordWrap(True); dl.addWidget(self.watch_status)
        self.downloads = QLabel(); self.downloads.setObjectName('card'); self.downloads.setTextFormat(Qt.PlainText); self.downloads.setWordWrap(True); self.downloads.setAlignment(Qt.AlignTop | Qt.AlignLeft); dl.addWidget(self.downloads)
        dl.addStretch(); self.tabs.addTab(downloads_tab, 'Pobieranie')
        self.setStyleSheet('''
          QMainWindow, QWidget { background:#101014; color:#f4f2f3; font-family:'Noto Sans',sans-serif; font-size:13px; }
          QLabel { background:transparent; }
          QLabel#eyebrow, QLabel#sectionEyebrow { color:#f35a68; font-size:10px; font-weight:700; letter-spacing:2px; }
          QLabel#title { color:#ffffff; font-size:30px; font-weight:800; letter-spacing:4px; }
          QLabel#subtitle { color:#a8a3a9; font-size:13px; }
          QLabel#heading, QLabel#sectionTitle { color:#ffffff; font-size:20px; font-weight:700; }
          QLabel#card { background:#1b1a20; border:1px solid #353039; border-radius:12px; padding:15px; font-size:13px; }
          QFrame#assistant { background:#21181e; border:1px solid #59323c; border-radius:14px; }
          QFrame#assistant QLabel, QFrame#assistant QCheckBox { background:transparent; border:none; }
          QLabel#assistantTitle { color:#fa7180; font-size:10px; font-weight:800; letter-spacing:1px; }
          QLabel#assistantText { color:#f1e8eb; font-size:12px; }
          QFrame#hero { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #561728,stop:0.52 #2c1921,stop:1 #1b1a20); border:1px solid #6b303e; border-radius:16px; }
          QFrame#hero QLabel { background:transparent; border:none; }
          QLabel#heroEyebrow { color:#ff8d99; font-size:10px; font-weight:700; letter-spacing:2px; }
          QLabel#heroTitle { color:#ffffff; font-size:24px; font-weight:800; }
          QLabel#heroStatus { color:#e0cbd0; font-size:12px; }
          QPushButton { background:#25232a; border:1px solid #48414b; border-radius:10px; padding:11px 14px; text-align:left; font-size:13px; font-weight:700; min-height:30px; }
          QPushButton:hover { background:#3c242c; border:1px solid #bd4659; }
          QPushButton:focus { border:2px solid #ff6679; }
          QPushButton#launchCard { background:#1c1b20; border:1px solid #353039; border-radius:14px; padding:16px; color:#f5e9ed; font-size:13px; }
          QPushButton#launchCard:hover { background:#302127; border:1px solid #bb4659; }
          QPushButton#launchCard:focus { border:2px solid #ff6679; }
          QPushButton#launchCard QLabel { background:transparent; border:none; }
          QLabel#cardEyebrow { color:#a36d79; font-size:9px; font-weight:700; letter-spacing:1px; }
          QLabel#cardTitle { color:#ffffff; font-size:15px; font-weight:800; }
          QLabel#cardDetail { color:#b6afb6; font-size:12px; font-weight:400; }
          QLabel#cardAction { color:#f36a7d; font-size:10px; font-weight:800; letter-spacing:1px; }
          QPushButton#textButton, QPushButton#assistantButton { background:transparent; border:none; padding:3px 5px; min-height:0; color:#ff8794; font-size:11px; }
          QPushButton#textButton:hover, QPushButton#assistantButton:hover { color:#ffffff; }
          QPushButton#featuredGame { background:#2a2026; border:1px solid #5c353e; border-radius:10px; min-height:44px; font-size:12px; }
          QTabWidget::pane { background:#151419; border:1px solid #302a31; border-radius:12px; top:-1px; }
          QTabBar::tab { background:#1e1c22; color:#c9c1c9; padding:10px 12px; margin-right:3px; border-top-left-radius:8px; border-top-right-radius:8px; font-weight:600; }
          QTabBar::tab:selected { background:#a82138; color:white; }
          QTabBar::tab:hover:!selected { background:#34252c; }
          QScrollArea { border:0; background:transparent; }
          QListWidget#library { background:#1b1a20; border:1px solid #353039; border-radius:12px; padding:5px; }
          QListWidget#library::item { padding:12px; border-radius:7px; color:#f4f2f3; }
          QListWidget#library::item:selected { background:#78263a; color:white; }
          QSpinBox { background:#25232a; border:1px solid #5a4b55; border-radius:7px; padding:6px; }
          QCheckBox { color:#c9c1c9; font-size:11px; }
        ''')
        self.previous = None
        self.previous_cpu = None
        self.camera_job = None
        self.game_by_key = {}
        self.previous_game_keys = None
        self.library_signature = None
        self.game_scan = None
        self.tip_index = 0
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
        self.home_status.setText('BATERIA  ·  ' + charge.split('\n')[0] + '     /     ' + ('GAZE  ·  USŁUGA DZIAŁA' if 'Gaze: usługa działa' in camera else 'GAZE  ·  BRAK ODCZYTU'))
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
        self.update_plan()
        downloads = steam_downloads()
        self.current_downloads = downloads
        watch_rc, watch_state = command('systemctl', '--user', 'is-active', 'kribuntu-steam-watch.service')
        self.watch_status.setText('Monitor w tle: działa.' if watch_rc == 0 and watch_state == 'active'
                                  else 'Monitor w tle: nie jest uruchomiony. Uruchom go lub wyloguj się i zaloguj ponownie po aktualizacji.')
        rows = [f'{name}\n{status}' for name, busy, status in downloads.values()]
        self.downloads.setText('\n\n'.join(rows) if rows else 'Brak danych o pobieraniu w domyślnych bibliotekach Steam.')
        self.log.setText(history())
        self.request_game_scan()

    def request_game_scan(self):
        if self.game_scan is not None:
            return
        worker = GameScan()
        self.game_scan = worker
        worker.signals.finished.connect(self.games_scanned)
        QThreadPool.globalInstance().start(worker)

    def games_scanned(self, games):
        self.game_scan = None
        if games is None:
            self.library_status.setText('Nie udało się odczytać biblioteki. Spróbuj odświeżyć.')
            return
        signature = tuple((g['key'], g['title'], g['source'], g['available']) for g in games)
        if signature == self.library_signature:
            return
        self.library_signature = signature
        selected = self.library.currentItem()
        selected_key = selected.data(Qt.UserRole) if selected else None
        old_keys = self.previous_game_keys
        self.game_by_key = {game['key']: game for game in games}
        keys = set(self.game_by_key)
        self.previous_game_keys = keys
        self.library.clear()
        for game in games:
            status = game['source'] if game['available'] else game['source'] + '  ·  katalog niedostępny'
            item = QListWidgetItem(game['title'] + '\n' + status)
            item.setData(Qt.UserRole, game['key']); item.setToolTip(status); self.library.addItem(item)
            if game['key'] == selected_key:
                self.library.setCurrentItem(item)
        if self.library.count() and self.library.currentItem() is None:
            self.library.setCurrentRow(0)
        self.library_status.setText(f'Wykryto {len(games)} gier. Źródła: Steam i Heroic.')
        self.library_link.setText(f'Biblioteka  ·  {len(games)}  →')
        while self.featured_layout.count():
            item = self.featured_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if games:
            for game in games[:3]:
                card = QPushButton(game['title'] + '\n' + game['source']); card.setObjectName('featuredGame')
                card.setToolTip(game['title'] + ' — ' + game['source']); card.setEnabled(game['available'])
                card.clicked.connect(lambda checked=False, item=game: self.launch_game(item))
                self.featured_layout.addWidget(card)
        else:
            empty = QLabel('Nie znaleziono jeszcze gier w obsługiwanych bibliotekach.'); empty.setWordWrap(True)
            self.featured_layout.addWidget(empty)
        new = keys - old_keys if old_keys is not None else set()
        if new:
            names = [g['title'] for g in games if g['key'] in new]
            self.assistant_text.setText('Zauważyłem nową grę: ' + names[0] + (f' i {len(names) - 1} kolejnych.' if len(names) > 1 else '.'))
        elif old_keys is None:
            self.assistant_text.setText(f'Znalazłem {len(games)} gier. Otwórz bibliotekę, żeby je zobaczyć.')

    def launch_selected_game(self):
        item = self.library.currentItem()
        if item is None:
            QMessageBox.information(self, 'Biblioteka', 'Wybierz grę z listy.')
            return
        game = self.game_by_key.get(item.data(Qt.UserRole))
        if game:
            self.launch_game(game)

    def launch_game(self, game):
        command_line = launch_command(game)
        if command_line is None:
            QMessageBox.warning(self, 'Biblioteka', 'Katalog gry jest niedostępny albo nie można ustalić sposobu uruchomienia. Sprawdź ją w launcherze.')
            return
        self.launch(command_line, 'Gra: ' + game['title'])

    def show_tip(self):
        tips = ['Twoje gry ze Steama i Heroica znajdziesz w zakładce Gry.',
                'W zakładce Laptop i kamera sprawdzisz baterię, temperatury i dźwięk.',
                'W Śladach możesz cofnąć ostatnią zmianę kamery wykonaną w Centrum.']
        if 'WŁĄCZONA' in self.camera.text() and 'Gaze: usługa działa' in self.camera.text():
            tips.insert(0, 'Discord i Gaze mogą potrzebować tej samej kamery IR. Sprawdź przełącznik kamery.')
        active = [name for name, busy, _status in getattr(self, 'current_downloads', {}).values() if busy]
        if active:
            tips.insert(0, 'Steam pobiera: ' + active[0] + '. Postęp jest w zakładce Pobieranie.')
        self.assistant_text.setText(tips[self.tip_index % len(tips)])
        self.tip_index += 1

    def update_plan(self):
        minutes = self.plan_minutes.value()
        self.settings.setValue('plan_minutes', minutes)
        batteries = sorted(Path('/sys/class/power_supply').glob('BAT*'))
        if not batteries:
            self.plan_result.setText('Nie wykryto baterii, więc nie mogę wyliczyć czasu.')
            return
        estimate, reason = battery_projection(batteries[0])
        if estimate is None:
            self.plan_result.setText(reason)
            return
        outcome = ('Przy obecnym poborze szacunek wystarcza na Twój plan.' if estimate >= minutes else
                   'Przy obecnym poborze szacunek jest krótszy od Twojego planu.')
        self.plan_result.setText(f'{outcome}\n\nSzacunkowo {estimate:.0f} min do osiągnięcia 15% zapasu. '
                                 'Pobór może się zmienić, zwłaszcza po uruchomieniu gry; to nie jest gwarancja.')

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

    def check_talos(self):
        self.game_report.setText(talos_report(HOME))
        record('Sprawdzono plik The Talos Principle')
        self.log.setText(history())

    def toggle_camera(self):
        script = HOME / '.local/bin/ir-camera'
        if not script.is_file():
            QMessageBox.information(self, 'Kamera IR', 'Nie znaleziono przełącznika kamery Discorda. Gaze nadal działa niezależnie.')
            return
        if QMessageBox.question(self, 'Kamera IR', 'Przełączyć kamerę IR dla Discorda? Gdy jest włączona, Gaze może nie móc użyć kamery do logowania.') != QMessageBox.Yes:
            return
        before = camera_running()
        if before is None:
            QMessageBox.warning(self, 'Kamera IR', 'Nie udało się ustalić stanu usługi kamery. Nie zmieniono jej ustawień.')
            return
        self.run_camera_toggle(before, undoing=False)

    def undo_camera(self):
        entry = load_camera_undo()
        if entry is None:
            QMessageBox.information(self, 'Cofnij kamerę', 'Brak zmiany kamery z Centrum, którą można cofnąć.')
            return
        if camera_running() != entry['after']:
            QMessageBox.warning(self, 'Cofnij kamerę', 'Stan kamery zmienił się od ostatniej operacji w Centrum. Sprawdź go przed kolejną zmianą.')
            return
        if QMessageBox.question(self, 'Cofnij kamerę', 'Przywrócić poprzedni stan kamery IR? Włączenie jej dla Discorda może zająć kamerę potrzebną Gaze.') != QMessageBox.Yes:
            return
        self.run_camera_toggle(entry['after'], undoing=True)

    def run_camera_toggle(self, before, undoing):
        script = HOME / '.local/bin/ir-camera'
        if not script.is_file():
            QMessageBox.warning(self, 'Kamera IR', 'Nie znaleziono przełącznika kamery Discorda.')
            return
        if self.camera_job is not None:
            QMessageBox.information(self, 'Kamera IR', 'Poprzednia operacja kamery jeszcze trwa.')
            return
        job = QProcess(self)
        self.camera_job = job
        def finished(code, status):
            after = camera_running()
            if code == 0 and status == QProcess.NormalExit and isinstance(after, bool) and after != before:
                if undoing:
                    try:
                        UNDO.unlink(missing_ok=True)
                    except OSError:
                        pass
                    record('Cofnięto zmianę kamery IR dla Discorda')
                else:
                    saved = save_camera_undo(before, after)
                    record('Kamera IR dla Discorda: ' + ('włączona' if after else 'wyłączona'))
                    if not saved:
                        QMessageBox.warning(self, 'Kamera IR', 'Stan kamery zmieniono, ale nie udało się zapisać informacji do cofnięcia.')
            else:
                QMessageBox.warning(self, 'Kamera IR', 'Nie udało się potwierdzić zmiany stanu kamery. Sprawdź jej status i komunikaty systemu.')
            self.camera_job = None
            job.deleteLater()
            self.refresh()
        def failed(error):
            if error == QProcess.FailedToStart:
                self.camera_job = None
                job.deleteLater()
                QMessageBox.warning(self, 'Kamera IR', 'Nie udało się uruchomić przełącznika kamery.')
        job.finished.connect(finished)
        job.errorOccurred.connect(failed)
        job.start(str(script), [])

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
