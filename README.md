# Kribuntu

Pomysł na osobisty system oparty na Ubuntu i KDE Plasma, przeznaczony dla laptopa Lenovo ThinkPad. Projekt jest na etapie planowania: nie zawiera jeszcze obrazu ISO ani instalatora.

## Proponowany zestaw domyślny

- Kubuntu jako baza: Plasma, Dolphin, Discover, Konsole, ustawienia systemowe i podstawowe aplikacje KDE.
- Firefox, LibreOffice, Okular, Gwenview, Ark i Spectacle: przeglądanie, dokumenty, archiwa i zrzuty ekranu.
- NetworkManager, Bluetooth, PipeWire oraz integracja drukarek: codzienna obsługa laptopa.
- `fwupd` i `fwupd-signed` (jeśli dostępny): aktualizacje firmware przez wspierane kanały.
- `power-profiles-daemon`: profile energii dostępne w KDE.
- `git`, Python 3 i `python3-venv`: podstawy pracy programistycznej.
- Kopie zapasowe: aplikacja do kopii i konfiguracja wybrana podczas dalszego projektowania.

## Opcjonalnie

Na komputerze widać ślady pracy z Androidem, Arduino, PlatformIO, Pythonem, Dockerem i maszynami wirtualnymi. Warto przygotować osobne profile instalacji tych narzędzi zamiast wymuszać wszystkie w podstawowym systemie. Podobnie gry, sterowniki własnościowe i kodeki powinny być wybierane świadomie.

## Plan

1. Ustalić dokładny model ThinkPada i jego Wi-Fi, GPU, czytnik linii papilarnych oraz potrzeby dotyczące baterii.
2. Wybrać wspieraną wersję Kubuntu LTS i przetestować sprzęt z live USB.
3. Zweryfikować dostępność i nazwy pakietów w wybranym wydaniu; przygotować powtarzalną konfigurację i profile opcjonalne.
4. Przetestować usypianie, audio, kamerę, klawisze funkcyjne, dokowanie, aktualizacje firmware i zasilanie.
5. Dopiero potem opracować sposób budowania i testowania obrazu instalacyjnego.

Nie instaluj jednocześnie konkurujących usług zarządzania energią bez sprawdzenia ich konfiguracji. Obsługa firmware i funkcji ThinkPada zależy od modelu.

## Pierwszy prototyp

Docelowy komputer: ThinkPad L16 Gen 1 z Ryzen 5 PRO. Pierwszą bazą jest Kubuntu 24.04 LTS. `install.sh` przygotowuje profil Kribuntu na istniejącym Ubuntu lub Kubuntu 24.04; wymaga internetu i uprawnień administratora:

```bash
sudo bash install.sh
```

Najpierw sprawdź go w maszynie wirtualnej. Skrypt instaluje pakiety systemowe i może zmienić konfigurację istniejącego systemu. Nie jest instalatorem ISO. Wi-Fi, czytnik linii papilarnych, uśpienie i aktualizacje firmware trzeba sprawdzić na docelowym laptopie.

## Gaming i wygląd Kripusek

Profil instaluje przez Flathub Steam, Discord, Heroic (Epic i GOG), OBS Studio i GIMP. Wykryto także Blender, Audacity, VLC, Inkscape i narzędzia deweloperskie na komputerze źródłowym; ich dobór pozostaje do ustalenia. Dostępność gier Windows, funkcji anty-cheat i launcherów zależy od konkretnej gry. Steam z Flathub jest pakietem społecznościowym; dostęp do biblioteki na innym dysku może wymagać dodatkowych uprawnień Flatpak.

Motyw zawiera tapetę `theme/kribuntu-ubuntu.png` i ciemny schemat kolorów `KribuntuDark`. Po uruchomieniu `sudo bash install.sh` można zastosować je w sesji KDE poleceniem `bash apply-theme.sh`. Integracja jako domyślnego motywu obrazu wymaga dalszych testów.
Oryginalna animacja postaci Kripusek znajduje się w `theme/kripusek.gif` i pochodzi z osobistej strony autora. Aktualna tapeta jest wersją wstępną; integracja postaci z tapetą i pełnym motywem KDE pozostaje do wykonania.
