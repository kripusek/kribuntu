#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -eq 0 ]]; then echo 'Uruchom bez sudo. System poprosi o hasło administratora.' >&2; exit 1; fi
command -v pkexec >/dev/null || { echo 'Brak pkexec.' >&2; exit 1; }
echo 'Pobieranie i instalowanie aktualizatora Kribuntu...'
pkexec /bin/bash "$(cd "$(dirname "$0")" && pwd)/updater/update-root.sh"
echo 'Gotowe. Otwórz Aktualizacje Kribuntu w menu aplikacji.'
