#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -eq 0 ]]; then
  echo 'Uruchom jako użytkownik pulpitu KDE, bez sudo.' >&2
  exit 1
fi
if [[ ${XDG_CURRENT_DESKTOP:-} != *KDE* ]]; then
  echo 'Uruchom w sesji KDE Plasma.' >&2
  exit 1
fi
plasma-apply-desktoptheme breeze-dark
plasma-apply-colorscheme KribuntuDark
plasma-apply-wallpaperimage /usr/local/share/wallpapers/kribuntu.png
echo 'Zastosowano kolory i tapetę Kribuntu.'
