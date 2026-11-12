#!/usr/bin/env bash
set -euo pipefail
root=${1:?Podaj katalog rozpakowanego systemu}
repo=$(cd "$(dirname "$0")" && pwd)
test -f "$root/usr/share/plasma/look-and-feel/org.kubuntu.desktop/contents/defaults"
install -Dm644 "$repo/theme/kribuntu-ubuntu.png" "$root/usr/share/wallpapers/Kribuntu/contents/images/1920x1080.png"
install -Dm644 "$repo/theme/KribuntuDark.colors" "$root/usr/share/color-schemes/KribuntuDark.colors"
install -Dm644 "$repo/theme/wallpaper-metadata.json" "$root/usr/share/wallpapers/Kribuntu/metadata.json"
python3 - "$root" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'usr/share/plasma/look-and-feel/org.kubuntu.desktop/contents/defaults'
s=p.read_text().replace('ColorScheme=KubuntuLight','ColorScheme=KribuntuDark').replace('name=kubuntu','name=default').replace('Image=KubuntuLight','Image=Kribuntu').replace('defaultWallpaperTheme=KubuntuLight','defaultWallpaperTheme=Kribuntu')
p.write_text(s)
p=root/'etc/calamares/branding/kubuntu/branding.desc'
s=p.read_text().replace('productName:         Kubuntu','productName:         Kribuntu').replace('shortProductName:    Kubuntu','shortProductName:    Kribuntu').replace('versionedName:       Kubuntu','versionedName:       Kribuntu').replace('shortVersionedName:  Kubuntu','shortVersionedName:  Kribuntu').replace('SidebarBackground:    "#6C7B93"','SidebarBackground:    "#1c1c25"').replace('SidebarTextCurrent:   "#0068C8"','SidebarTextCurrent:   "#ef344f"')
p.write_text(s)
PY
