#!/usr/bin/env bash
set -euo pipefail
# Builds the tested Howdy beta on Ubuntu 26.04, without changing PAM.
if [[ $EUID -ne 0 ]]; then echo 'Uruchom przez sudo.' >&2; exit 1; fi
. /etc/os-release
if [[ ${ID:-} != ubuntu || ${VERSION_ID:-} != 26.04 ]]; then
  echo 'Ten instalator jest przygotowany tylko dla Ubuntu 26.04.' >&2; exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3-venv python3-opencv python3-numpy python3-dev cmake g++ make meson ninja-build libpam0g-dev libinih-dev libevdev-dev pkgconf git curl bzip2
venv=/opt/kribuntu-howdy-venv
python3 -m venv --system-site-packages "$venv"
CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2 "$venv/bin/pip" install 'dlib==20.0.1'
"$venv/bin/python" -c 'import dlib, cv2, numpy; print("Howdy: zaleznosci dzialaja")'
work=$(mktemp -d /tmp/kribuntu-howdy.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
git init -q "$work/source"
git -C "$work/source" remote add origin https://github.com/boltgolt/howdy.git
git -C "$work/source" fetch --quiet --depth=1 origin d8bba3cf06d35d6a873758bb09aa6e8c47526be1
git -C "$work/source" checkout --quiet --detach FETCH_HEAD
meson setup "$work/build" "$work/source/howdy" --prefix=/usr/local -Dpython_path="$venv/bin/python" -Dconfig_dir=/etc/howdy -Dpam_dir=/usr/local/lib/security
meson compile -C "$work/build" -j 2
meson install -C "$work/build"
install -d -m 755 /usr/local/share/dlib-data
for model in dlib_face_recognition_resnet_model_v1 shape_predictor_5_face_landmarks mmod_human_face_detector; do
  curl -fL --retry 3 -o "$work/$model.dat.bz2" "https://github.com/davisking/dlib-models/raw/master/$model.dat.bz2"
  bzip2 -dc "$work/$model.dat.bz2" > "$work/$model.dat"
  install -m 644 "$work/$model.dat" "/usr/local/share/dlib-data/$model.dat"
done
printf '%s\n' 'Howdy zainstalowano. Nie wlaczono logowania twarza ani nie zmieniono PAM.'
printf '%s\n' 'Przed wlaczeniem skonfiguruj kamere IR, dodaj model twarzy i przetestuj rozpoznawanie.'
