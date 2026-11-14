# Kribuntu

## Aktualny obraz: 26.04.1 LTS

Kribuntu ma eksperymentalny obraz na bazie Kubuntu 26.04.1 LTS dla komputerów amd64. Zawiera ekran startowy i instalator Kribuntu, Centrum Kribuntu, aktualizator oraz aplikacje Steam, Discord i Heroic z Flathub. Test UEFI doszedł do okna instalatora i sesji Plasma; pełna instalacja, aplikacje i sprzęt nie zostały jeszcze kompleksowo przetestowane. W sesji live może pojawić się standardowe okno powitalne KDE/Ubuntu.

Obraz jest dzielony na części z powodu limitu wielkości pliku w GitHub Releases. Instrukcja połączenia i suma kontrolna znajdują się w opisie wydania. Nie należy używać poszczególnych części jako osobnych obrazów ISO.

Czytnik odcisku jest obsługiwany przez fprintd, zależnie od sprzętu. Rozpoznawanie twarzy nie jest włączone. Skrypt `hardware/install-howdy-26.sh` przygotowuje testową wersję Howdy dla 26.04 bez modyfikowania PAM; przed włączeniem logowania wymaga konfiguracji kamery IR, zapisania twarzy oraz osobnego testu.

Poniższe sekcje opisują także wcześniejszy prototyp i plan prac na bazie 24.04.

Pomysł na osobisty system oparty na Ubuntu i KDE Plasma, przeznaczony dla laptopa Lenovo ThinkPad. Powstał eksperymentalny obraz ISO oparty na instalatorze Kubuntu; nie jest jeszcze wydaniem gotowym do instalacji na laptopie. Test instalacji trwa.

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

Profil instaluje przez Flathub Steam, Discord, Heroic (Epic i GOG), OBS Studio i GIMP. Profil zawiera także Blender, Audacity, VLC i Inkscape, znalezione na komputerze źródłowym. Dostępność gier Windows, funkcji anty-cheat i launcherów zależy od konkretnej gry. Steam z Flathub jest pakietem społecznościowym; dostęp do biblioteki na innym dysku może wymagać dodatkowych uprawnień Flatpak.

Motyw zawiera tapetę `theme/kribuntu-ubuntu.png` i ciemny schemat kolorów `KribuntuDark`. Po uruchomieniu `sudo bash install.sh` można zastosować je w sesji KDE poleceniem `bash apply-theme.sh`. Integracja jako domyślnego motywu obrazu wymaga dalszych testów.
Oryginalna animacja postaci Kripusek znajduje się w `theme/kripusek.gif` i pochodzi z osobistej strony autora. Aktualna tapeta jest wersją wstępną; integracja postaci z tapetą i pełnym motywem KDE pozostaje do wykonania.

## Aktualizator na zainstalowanym systemie

Na komputerze z Ubuntu/Kubuntu 24.04 i KDE otwórz Konsole i wykonaj:

```bash
git clone https://github.com/kripusek/kribuntu.git ~/kribuntu-source
bash ~/kribuntu-source/setup-updater.sh
```

System poprosi o hasło administratora. Potem w menu aplikacji uruchom **Aktualizacje Kribuntu**, aby pobrać nowsze pliki i wybrać zastosowanie ciemnego motywu, kolorów i tapety. W menu pojawi się też **Kribuntu — tryb gier**, uruchamiający interfejs Steam; wymaga Steama z Flathub. Aktualizator nie instaluje pełnych aktualizacji Ubuntu — te nadal obsługuje Discover. W razie problemów aktualizator można wywołać w terminalu jako `kribuntu-update`.
Po aktualizacji uruchom z menu **Centrum Kribuntu** — to okno z kafelkami gier, Discorda, diagnostyki i ustawień. Program nie zastępuje pulpitu KDE.

Centrum odczytuje lokalne listy zainstalowanych gier Steama i Heroica (Epic, GOG i Amazon), pokazuje bibliotekę i pozwala uruchamiać znalezione gry. Kripusek odświeża bibliotekę w tle; monitor sprawdza ją także przy zamkniętym Centrum i zgłasza nowe gry powiadomieniem. Wykrywanie zależy od danych zapisywanych przez obsługiwane launchery.

Zakładka **Retro** wyświetla własne pliki gier z `~/Games/Retro`. Do uruchamiania obsługiwanych formatów potrzebne są pakiety `retroarch`, `libretro-mgba`, `libretro-snes9x` i `libretro-genesisplusgx`. Same gry oraz firmware nie są dołączone do Kribuntu. Pakiety instalowane są osobno; aktualizator Centrum ich nie instaluje.

W Centrum zakładka **Laptop i kamera** pokazuje baterię, dostępne temperatury, procesy i stan przełącznika kamery IR dla Discorda. Gaze i Discord mogą rywalizować o tę samą kamerę; przełącznik nie zmienia konfiguracji logowania. Zakładka **Ślady** zapisuje lokalnie tylko działania uruchomione w Centrum i powiadomienia Steama, a nie historię całego systemu. Wskazania procesów pokazują wykorzystanie CPU od poprzedniego odczytu (100% oznacza jeden rdzeń).

W zakładce **Ślady** można cofnąć ostatnią potwierdzoną zmianę stanu przełącznika kamery IR wykonaną przez Centrum. Cofanie nie nastąpi, jeśli aktualny stan różni się od zapisanego stanu po tej zmianie. Nie jest to przywracanie dowolnych zmian systemu.

W zakładce **Gry** Kripusek sprawdza znaną poprawkę Proton/DXVK dla The Talos Principle w domyślnym katalogu Heroica. Samodzielnie nie zmienia plików gry; obecność poprawki nie gwarantuje uruchomienia.

Centrum wyświetla animację Kripuska, którą można zatrzymać przełącznikiem w nagłówku.

Zakładka **Czy zdążę?** porównuje czas wpisany przez użytkownika z szacunkowym czasem do osiągnięcia 15% baterii, przy założeniu stałego aktualnego poboru. Wynik jest orientacyjny i nie zmienia ustawień energii; podczas ładowania oraz bez danych o poborze prognoza nie jest pokazywana.

Zakładka **Pobieranie** odczytuje liczby zapisane przez Steam w domyślnych bibliotekach użytkownika (Flatpak i standardowa lokalizacja). Lekka usługa użytkownika sprawdza je w tle i wysyła powiadomienie, gdy zauważy przejście pobierania oraz przygotowania do stanu zakończonego. Biblioteki w innych katalogach nie są jeszcze wykrywane. Stan usługi jest widoczny w Centrum.

Przy uśpieniu usługa Kribuntu zapisuje lokalnie poziom baterii i aktywne pobierania Steama w domyślnych bibliotekach. Po wznowieniu przypomina o tych informacjach i o grach online. Nie zatrzymuje gry, nie tworzy zapisu gry i nie zmienia ustawień uśpienia. Wymaga działającej sesji użytkownika i usług D-Bus systemd.
