#!/usr/bin/env bash
set -u
if ! command -v kdialog >/dev/null; then echo 'Brak kdialog.' >&2; exit 1; fi
kdialog --title 'Aktualizacje Kribuntu' --yesno 'Pobrać najnowsze pliki Kribuntu z GitHuba i zaktualizować aplikację oraz motyw? Wymagane będzie hasło administratora.' || exit 0
if ! command -v pkexec >/dev/null; then kdialog --error 'Brak narzędzia pkexec.'; exit 1; fi
if pkexec /usr/local/libexec/kribuntu-update-root; then
  if kdialog --title 'Aktualizacje Kribuntu' --yesno 'Aktualizacja zakończona. Zastosować teraz ciemny motyw i tapetę Kribuntu?'; then
    if /usr/local/bin/kribuntu-apply-theme; then
      kdialog --title 'Kribuntu' --msgbox 'Zaktualizowano Kribuntu i zastosowano motyw.'
    else
      kdialog --error 'Pliki zaktualizowano, ale nie udało się zastosować motywu. Uruchom aktualizator w sesji KDE.'
      exit 1
    fi
  fi
else
  kdialog --error 'Aktualizacja nie powiodła się lub została anulowana. Sprawdź połączenie z internetem i spróbuj ponownie.'
  exit 1
fi
