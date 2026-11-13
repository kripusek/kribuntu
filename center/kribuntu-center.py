#!/usr/bin/env python3
"""Kribuntu launcher for the KDE desktop."""
import shutil
import subprocess
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

class Center(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Centrum Kribuntu')
        self.resize(960, 600)
        self.setMinimumSize(650, 440)
        base = QWidget()
        self.setCentralWidget(base)
        outer = QVBoxLayout(base)
        outer.setContentsMargins(38, 32, 38, 32)
        outer.setSpacing(18)
        title = QLabel('KRIBUNTU')
        title.setObjectName('title')
        outer.addWidget(title)
        subtitle = QLabel('Twoje gry i narzędzia w jednym miejscu')
        subtitle.setObjectName('subtitle')
        outer.addWidget(subtitle)
        grid = QGridLayout()
        grid.setSpacing(14)
        outer.addLayout(grid, 1)
        items = [
            ('STEAM', 'Tryb gier', ['flatpak', 'run', 'com.valvesoftware.Steam', '-gamepadui']),
            ('HEROIC', 'Epic Games i GOG', ['flatpak', 'run', 'com.heroicgameslauncher.hgl']),
            ('DISCORD', 'Rozmowy ze znajomymi', ['flatpak', 'run', 'com.discordapp.Discord']),
            ('AKTUALIZACJE', 'Motyw i narzędzia Kribuntu', ['/usr/local/bin/kribuntu-update']),
            ('TEST SPRZĘTU', 'Sieć, kamera i czytnik', ['/usr/local/bin/kribuntu-hardware-check']),
            ('USTAWIENIA', 'Ustawienia KDE', [shutil.which('systemsettings') or 'systemsettings5']),
        ]
        for index, (name, desc, command) in enumerate(items):
            button = QPushButton(name + '\n' + desc)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, cmd=command: self.launch(cmd))
            grid.addWidget(button, index // 3, index % 3)
        self.setStyleSheet('''
            QMainWindow, QWidget { background: #14141c; color: #f7f7fa; font-family: sans-serif; }
            QLabel#title { color: #ffffff; font-size: 34px; font-weight: 800; letter-spacing: 3px; }
            QLabel#subtitle { color: #c4c4ce; font-size: 16px; }
            QPushButton { background: #252631; border: 1px solid #494653; border-radius: 14px;
              padding: 20px; text-align: left; font-size: 18px; font-weight: bold; min-height: 90px; }
            QPushButton:hover, QPushButton:focus { background: #8d1f35; border: 2px solid #ff4e68; }
        ''')

    def launch(self, command):
        if not shutil.which(command[0]):
            QMessageBox.warning(self, 'Kribuntu', 'Brakuje programu potrzebnego do uruchomienia tej funkcji.')
            return
        try:
            subprocess.Popen(command, start_new_session=True)
        except OSError as exc:
            QMessageBox.warning(self, 'Kribuntu', 'Nie udało się uruchomić aplikacji: ' + str(exc))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Center()
    window.show()
    sys.exit(app.exec_())
