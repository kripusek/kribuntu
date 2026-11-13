#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")" && pwd)
install -d /usr/share/sddm/themes/kribuntu /usr/share/plymouth/themes/kribuntu /usr/local/share/icons/hicolor/scalable/places
cp -a /usr/share/sddm/themes/breeze/. /usr/share/sddm/themes/kribuntu/
install -m 644 "$repo/theme/kribuntu-ubuntu.png" /usr/share/sddm/themes/kribuntu/background.png
cat > /usr/share/sddm/themes/kribuntu/theme.conf.user <<'EOF'
[General]
background=/usr/share/sddm/themes/kribuntu/background.png
showlogo=hidden
type=image
color=#160b10
EOF
cat > /etc/sddm.conf.d/99-kribuntu.conf <<'EOF'
[Theme]
Current=kribuntu
EOF
cp -a /usr/share/plymouth/themes/spinner/. /usr/share/plymouth/themes/kribuntu/
python3 - <<'PY'
from PIL import Image, ImageDraw, ImageFont
p='/usr/share/plymouth/themes/kribuntu/'
im=Image.new('RGBA',(700,150),(0,0,0,0)); d=ImageDraw.Draw(im)
d.ellipse((12,15,120,123),outline='#e52339',width=5)
d.line([(47,40),(47,98)],fill='white',width=7);d.line([(48,70),(85,40)],fill='white',width=7);d.line([(48,70),(87,99)],fill='white',width=7)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',53)
d.text((147,31),'KRIBUNTU',font=f,fill='white',stroke_width=0)
im.save(p+'watermark.png')
PY
sed -e 's|ImageDir=.*|ImageDir=/usr/share/plymouth/themes/kribuntu|' -e 's/^Name=Spinner/Name=Kribuntu/' -e 's/WatermarkVerticalAlignment=.96/WatermarkVerticalAlignment=.5/' /usr/share/plymouth/themes/spinner/spinner.plymouth > /usr/share/plymouth/themes/kribuntu/kribuntu.plymouth
cat > /usr/local/share/icons/hicolor/scalable/places/start-here-kribuntu.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="#151318" stroke="#e52339" stroke-width="3"/><path d="M23 16v32m1-16 18-16M24 32l19 16" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>
EOF
update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/kribuntu/kribuntu.plymouth 160
update-alternatives --set default.plymouth /usr/share/plymouth/themes/kribuntu/kribuntu.plymouth
update-initramfs -u
