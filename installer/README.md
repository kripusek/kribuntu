Zmiany ekranu powitalnego bazują na kodzie źródłowym Ubuntu `kubuntu-installer-prompt` 24.04.10 (GPL-3.0): https://packages.ubuntu.com/source/noble/kubuntu-installer-prompt. Skrypt `patch-prompt.py` wymaga rozpakowanego oryginalnego źródła i zastępuje zasoby oraz dodaje przycisk diagnostyki. `logo.svg` i tło są zasobami Kribuntu. Obraz `ventoy-theme/select_c.png` pochodzi z projektu Ventoy: https://github.com/ventoy/Ventoy.
Budowa na Ubuntu 24.04 z pakietami `build-essential`, `cmake`, `extra-cmake-modules`, `libkf5networkmanagerqt-dev`, `libkf5widgetsaddons-dev`, `qtbase5-dev` i `qttools5-dev`:

```bash
python3 installer/patch-prompt.py /sciezka/do/rozpakowanego-zrodla
cmake -S /sciezka/do/rozpakowanego-zrodla -B /sciezka/do/katalogu-build
cmake --build /sciezka/do/katalogu-build
```

Wynikowy program wymaga testu w sesji live przed dołączeniem do obrazu. Przycisk diagnostyki wykrywa urządzenia; nie konfiguruje ani nie potwierdza działania rozpoznawania twarzy.