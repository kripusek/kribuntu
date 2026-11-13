#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo 'Uruchom: sudo bash install.sh' >&2
  exit 1
fi
. /etc/os-release
if [[ ${ID:-} != ubuntu || ( ${VERSION_ID:-} != 24.04 && ${VERSION_ID:-} != 26.04 ) ]]; then
  echo 'Ten profil wspiera obecnie Ubuntu i Kubuntu 24.04 oraz 26.04 LTS.' >&2
  exit 1
fi
packages=(kubuntu-desktop fwupd power-profiles-daemon git python3-venv libreoffice okular gwenview ark spectacle vlc audacity blender inkscape fprintd v4l-utils flatpak plasma-discover-backend-flatpak)
apt-get update
apt-get install -y "${packages[@]}"
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --system --noninteractive flathub com.valvesoftware.Steam com.discordapp.Discord com.heroicgameslauncher.hgl com.obsproject.Studio org.gimp.GIMP
install -Dm644 "$(dirname "$(realpath "$0")")/theme/kribuntu-ubuntu.png" /usr/local/share/wallpapers/kribuntu.png
install -Dm644 "$(dirname "$(realpath "$0")")/theme/KribuntuDark.colors" /usr/share/color-schemes/KribuntuDark.colors
install -Dm755 "$(dirname "$(realpath "$0")")/theme/autostart/kribuntu-first-login" /usr/local/bin/kribuntu-first-login
install -Dm644 "$(dirname "$(realpath "$0")")/theme/autostart/kribuntu-theme.desktop" /etc/skel/.config/autostart/kribuntu-theme.desktop
install -Dm755 "$(dirname "$(realpath "$0")")/hardware/kribuntu-hardware-check" /usr/local/bin/kribuntu-hardware-check
install -Dm644 "$(dirname "$(realpath "$0")")/hardware/kribuntu-hardware-check.desktop" /usr/share/applications/kribuntu-hardware-check.desktop
echo 'Gotowe. Uruchom ponownie komputer; tapetę wybierz w ustawieniach pulpitu KDE.'
