#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo 'Uruchom: sudo bash install.sh' >&2
  exit 1
fi
. /etc/os-release
if [[ ${ID:-} != ubuntu || ${VERSION_ID:-} != 24.04 ]]; then
  echo 'Ten profil wspiera obecnie Ubuntu i Kubuntu 24.04 LTS.' >&2
  exit 1
fi
packages=(kubuntu-desktop fwupd power-profiles-daemon git python3-venv libreoffice okular gwenview ark spectacle flatpak plasma-discover-backend-flatpak)
apt-get update
apt-get install "${packages[@]}"
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --system --noninteractive flathub com.valvesoftware.Steam com.discordapp.Discord com.heroicgameslauncher.hgl com.obsproject.Studio org.gimp.GIMP
install -Dm644 "$(dirname "$(realpath "$0")")/theme/kribuntu.svg" /usr/local/share/wallpapers/kribuntu.svg
echo 'Gotowe. Uruchom ponownie komputer; tapetę wybierz w ustawieniach pulpitu KDE.'
