from pathlib import Path
import re

HOME = Path.home()


def steam_downloads():
    roots = [HOME / '.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps',
             HOME / '.steam/steam/steamapps']
    seen = set()
    downloads = {}
    for root in roots:
        try:
            manifests = list(root.glob('appmanifest_*.acf'))
        except OSError:
            continue
        for path in manifests:
            try:
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                text = path.read_text(encoding='utf-8', errors='replace')
                def field(key):
                    match = re.search(r'^\s*"' + re.escape(key) + r'"\s*"([^"\n]*)"', text, re.MULTILINE)
                    return match.group(1) if match else ''
                total = int(field('BytesToDownload') or '0')
                downloaded = int(field('BytesDownloaded') or '0')
                staged_total = int(field('BytesToStage') or '0')
                staged = int(field('BytesStaged') or '0')
                if total <= 0:
                    continue
                name = field('name') or path.stem
                busy = downloaded < total or (staged_total > 0 and staged < staged_total)
                if downloaded < total:
                    status = f'{100 * max(0, min(downloaded, total)) / total:.0f}% pobrano'
                elif staged_total > 0 and staged < staged_total:
                    status = f'{100 * max(0, min(staged, staged_total)) / staged_total:.0f}% przygotowano'
                else:
                    status = 'pobieranie i przygotowanie zakończone'
                downloads[str(resolved)] = (name, busy, status)
            except (OSError, ValueError):
                continue
    return downloads


