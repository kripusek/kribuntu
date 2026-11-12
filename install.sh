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
packages=(kubuntu-desktop fwupd power-profiles-daemon git python3-venv libreoffice okular gwenview ark spectacle)
apt-get update
apt-get install "${packages[@]}"
echo 'Profil Kribuntu został zainstalowany. Uruchom ponownie komputer.'
