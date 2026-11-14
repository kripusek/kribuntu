#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Uruchom przez sudo lub pkexec.' >&2; exit 1; fi
. /etc/os-release
if [[ ${ID:-} != ubuntu || ( ${VERSION_ID:-} != 24.04 && ${VERSION_ID:-} != 26.04 ) ]]; then echo 'Aktualizator obsluguje Ubuntu/Kubuntu 24.04 i 26.04.' >&2; exit 1; fi
command -v git >/dev/null || { echo 'Brak git. Zainstaluj pakiet git.' >&2; exit 1; }
work=$(mktemp -d /tmp/kribuntu-update.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
git clone --quiet --depth 1 --branch main https://github.com/kripusek/kribuntu.git "$work/repo"
repo=$work/repo
bash "$repo/install-system-branding.sh"
install -Dm644 "$repo/theme/kribuntu-ubuntu.png" /usr/local/share/wallpapers/kribuntu.png
install -Dm644 "$repo/theme/KribuntuDark.colors" /usr/share/color-schemes/KribuntuDark.colors
install -Dm644 "$repo/theme/kripusek.gif" /usr/local/share/kribuntu/kripusek.gif
install -Dm755 "$repo/apply-theme.sh" /usr/local/bin/kribuntu-apply-theme
install -Dm755 "$repo/hardware/kribuntu-hardware-check" /usr/local/bin/kribuntu-hardware-check
install -Dm644 "$repo/hardware/kribuntu-hardware-check.desktop" /usr/local/share/applications/kribuntu-hardware-check.desktop
install -Dm755 "$repo/updater/update-root.sh" /usr/local/libexec/kribuntu-update-root.new
mv -f /usr/local/libexec/kribuntu-update-root.new /usr/local/libexec/kribuntu-update-root
install -Dm755 "$repo/updater/update-gui.sh" /usr/local/bin/kribuntu-update.new
mv -f /usr/local/bin/kribuntu-update.new /usr/local/bin/kribuntu-update
install -Dm644 "$repo/updater/kribuntu-update.desktop" /usr/local/share/applications/kribuntu-update.desktop
install -Dm644 "$repo/updater/kribuntu-gaming.desktop" /usr/local/share/applications/kribuntu-gaming.desktop
install -Dm644 "$repo/center/kribuntu_steam.py" /usr/local/lib/kribuntu/kribuntu_steam.py
install -Dm644 "$repo/center/kribuntu_games.py" /usr/local/lib/kribuntu/kribuntu_games.py
install -Dm755 "$repo/center/kribuntu-steam-watch.py" /usr/local/lib/kribuntu/kribuntu-steam-watch.py
install -Dm644 "$repo/center/kribuntu-steam-watch.service" /usr/lib/systemd/user/kribuntu-steam-watch.service
install -Dm755 "$repo/center/kribuntu-sleep-watch.py" /usr/local/lib/kribuntu/kribuntu-sleep-watch.py
install -Dm644 "$repo/center/kribuntu-sleep-watch.service" /usr/lib/systemd/user/kribuntu-sleep-watch.service
install -Dm755 "$repo/center/kribuntu-center.py" /usr/local/bin/kribuntu-center
install -Dm644 "$repo/center/kribuntu-center.desktop" /usr/local/share/applications/kribuntu-center.desktop
if command -v systemctl >/dev/null; then
  systemctl --global enable kribuntu-steam-watch.service || echo 'Nie udało się włączyć monitora Steama na przyszłe sesje.' >&2
  systemctl --global enable kribuntu-sleep-watch.service || echo 'Nie udało się włączyć przypomnień po uśpieniu na przyszłe sesje.' >&2
fi
git -C "$repo" rev-parse --short HEAD > /usr/local/share/kribuntu-version
command -v update-desktop-database >/dev/null && update-desktop-database /usr/local/share/applications || true
printf 'Aktualizacja plikow Kribuntu zakonczona.\n'
