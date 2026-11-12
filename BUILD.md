# Przygotowanie obrazu Kribuntu — etap eksperymentalny

Punktem wyjścia jest oficjalny obraz Kubuntu 24.04 LTS amd64. Sprawdź sumę SHA256 i podpis obrazu zgodnie z instrukcjami wydawcy. Budowę wykonuj na osobnym systemie Ubuntu 24.04 lub w maszynie wirtualnej z odpowiednią ilością miejsca. WSL nie stanowi tutaj przetestowanego środowiska budowania.

Do personalizacji można użyć Cubic (Custom Ubuntu ISO Creator). Wybierz obraz źródłowy oraz pusty katalog projektu, a następnie skopiuj zawartość repozytorium do środowiska obrazu zgodnie z interfejsem Cubic. W terminalu obrazu uruchom `bash install.sh` z katalogu repozytorium. Po zakończeniu usuń kopię repozytorium z systemu obrazu, jeśli nie ma być dostępna użytkownikom. Wygeneruj ISO w Cubic.

Ta procedura nie została jeszcze zweryfikowana: instalacja Flatpak w chroot i przeniesienie aplikacji do systemu po instalacji wymagają sprawdzenia. Nie traktuj wygenerowanego obrazu jako gotowego wydania. Sprawdź w VM start UEFI, sesję live, instalację na wirtualnym dysku, aplikacje, sieć i aktualizacje po restarcie. Dopiero potem przetestuj na ThinkPadzie. Nie nadpisuj dysku z danymi podczas prób.

Tapeta `theme/kribuntu-ubuntu.png` jest instalowana do `/usr/local/share/wallpapers/kribuntu.png`. Obecnie należy wybrać ją w ustawieniach pulpitu; automatyczna konfiguracja KDE wymaga dalszych prac.