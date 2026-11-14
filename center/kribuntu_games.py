"""Read installed game manifests without changing launcher data."""
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlencode


def read_json(path):
    try:
        if path.stat().st_size > 20 * 1024 * 1024:
            return None
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return None


def valid_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9._:-]{1,200}', value))


def steam_libraries(home):
    roots = [
        (home / '.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps', True),
        (home / '.steam/steam/steamapps', False),
        (home / '.local/share/Steam/steamapps', False),
    ]
    result, seen = [], set()
    for root, is_flatpak in roots:
        candidates = [root]
        try:
            data = (root / 'libraryfolders.vdf').read_text(encoding='utf-8', errors='replace')
            for path in re.findall(r'^\s*"path"\s*"((?:\\.|[^"\\])*)"', data, re.MULTILINE):
                path = path.replace('\\\\', '\\').replace('\\"', '"')
                library = Path(path)
                if library.is_absolute():
                    candidates.append(library / 'steamapps')
        except OSError:
            pass
        for candidate in candidates:
            resolved = candidate.resolve(strict=False)
            if resolved not in seen:
                seen.add(resolved)
                result.append((candidate, is_flatpak))
    return result


def steam_games(home):
    found = []
    for root, is_flatpak in steam_libraries(home):
        try:
            manifests = list(root.glob('appmanifest_*.acf'))
        except OSError:
            continue
        for path in manifests:
            game_id = path.stem.removeprefix('appmanifest_')
            if not game_id.isdigit():
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='replace')
                def field(key):
                    match = re.search(r'^\s*"' + re.escape(key) + r'"\s*"([^"\n]*)"', text, re.MULTILINE)
                    return match.group(1) if match else ''
                title, install_dir = field('name'), field('installdir')
                flags = int(field('StateFlags') or '0')
                if not title or not install_dir or not flags & 4:
                    continue
                if title.casefold().startswith(('steam linux runtime', 'proton ', 'steamworks common redistributables')):
                    continue
                games_path = root / 'common' / install_dir
                found.append({'key': 'steam:' + game_id, 'title': title, 'source': 'Steam',
                              'id': game_id, 'runner': 'steam', 'flatpak': is_flatpak,
                              'available': games_path.is_dir()})
            except (OSError, ValueError):
                continue
    return found


def cache_titles(root, runner):
    filename = {'legendary': 'legendary_library.json', 'gog': 'gog_library.json',
                'nile': 'nile_library.json'}[runner]
    data = read_json(root / 'store_cache' / filename)
    if not isinstance(data, dict):
        return {}
    entries = data.get('games', data.get('library', []))
    if not isinstance(entries, list):
        return {}
    return {str(item.get('app_name')): item.get('title') for item in entries
            if isinstance(item, dict) and item.get('app_name') and isinstance(item.get('title'), str)}


def heroic_games(home):
    roots = [(home / '.var/app/com.heroicgameslauncher.hgl/config/heroic', True),
             (home / '.config/heroic', False)]
    found = []
    for root, is_flatpak in roots:
        stores = [
            ('legendary', root / 'legendaryConfig/legendary/installed.json'),
            ('gog', root / 'gog_store/installed.json'),
            ('nile', root / 'nile_config/nile/installed.json'),
        ]
        if not is_flatpak:
            stores.append(('legendary', home / '.config/legendary/installed.json'))
        for runner, path in stores:
            data = read_json(path)
            if isinstance(data, dict) and isinstance(data.get('installed'), list):
                entries = [(None, item) for item in data['installed']]
            elif isinstance(data, dict):
                entries = list(data.items())
            elif isinstance(data, list):
                entries = [(None, item) for item in data]
            else:
                continue
            titles = cache_titles(root, runner)
            for key, info in entries:
                if not isinstance(info, dict) or info.get('is_dlc') or info.get('isDLC') or info.get('is_preloaded'):
                    continue
                game_id = info.get('app_name') or info.get('appName') or info.get('id') or key
                if isinstance(game_id, int):
                    game_id = str(game_id)
                if not valid_id(game_id):
                    continue
                title = info.get('title') or info.get('game_title') or titles.get(game_id) or game_id
                if not isinstance(title, str):
                    continue
                install_path = info.get('install_path') or info.get('installPath')
                available = isinstance(install_path, str) and Path(install_path).is_dir()
                found.append({'key': 'heroic:' + runner + ':' + game_id, 'title': title,
                              'source': {'legendary': 'Heroic · Epic', 'gog': 'Heroic · GOG', 'nile': 'Heroic · Amazon'}[runner],
                              'id': game_id, 'runner': runner, 'flatpak': is_flatpak,
                              'available': available})
    return found


def installed_games(home=None):
    home = Path.home() if home is None else Path(home)
    unique = {}
    for game in steam_games(home) + heroic_games(home):
        old = unique.get(game['key'])
        if old is None or (game['available'] and not old['available']):
            unique[game['key']] = game
    return sorted(unique.values(), key=lambda game: (game['title'].casefold(), game['key']))


def launch_command(game):
    game_id, runner = game.get('id'), game.get('runner')
    if not valid_id(game_id) or not game.get('available'):
        return None
    if runner == 'steam' and game_id.isdigit():
        uri = 'steam://rungameid/' + game_id
        if game.get('flatpak') and shutil.which('flatpak'):
            return ['flatpak', 'run', 'com.valvesoftware.Steam', uri]
        return ['steam', uri] if shutil.which('steam') else ['xdg-open', uri]
    if runner in ('legendary', 'gog', 'nile'):
        uri = 'heroic://launch?' + urlencode({'appName': game_id, 'runner': runner})
        if game.get('flatpak') and shutil.which('flatpak'):
            return ['flatpak', 'run', 'com.heroicgameslauncher.hgl', uri]
        return ['heroic', uri] if shutil.which('heroic') else ['xdg-open', uri]
    return None
