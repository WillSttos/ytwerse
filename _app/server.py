"""
YTWERSE — Flask Server
Serves the web interface and handles download requests via yt-dlp.
Uses Waitress as the production WSGI server.
"""

import os
import sys
import json
import threading
import time

from flask import Flask, request, jsonify, render_template

# Adjust import path — this module lives inside _app/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from downloader import DownloadManager, DownloadError


# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------

def _get_app_root():
    """Return the _app directory path — works in dev and frozen (.exe) mode."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, '_app')
    return os.path.dirname(os.path.abspath(__file__))

_APP_ROOT = _get_app_root()

app = Flask(
    __name__,
    template_folder=os.path.join(_APP_ROOT, 'templates'),
    static_folder=os.path.join(_APP_ROOT, 'static'),
)

# Determine the base directory for saving files (where the .exe / launcher lives)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

download_manager = DownloadManager(base_dir=BASE_DIR)

import uuid

# ---------------------------------------------------------------------------
# Task State
#
# Each download group (a video or playlist) is a "group" with:
#   group_id: str
#   title: str (playlist name or video title)
#   type: 'playlist' | 'video'
#   is_active: bool
#   media_type: 'audio' | 'video'
#   output_dir: str
#   items: list of item dicts
#
# Each item has:
#   item_id: str
#   title: str
#   status: 'waiting' | 'downloading' | 'processing' | 'complete' | 'error' | 'cancelled'
#   percent: float (0-100)
#   speed: str
#   eta: str
#   error: str | None
# ---------------------------------------------------------------------------

groups = {}       # group_id -> group dict
groups_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Serve the main interface."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for the launcher."""
    return jsonify({'status': 'ok'})


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a URL and return video/playlist metadata."""
    data = request.get_json(silent=True)
    if not data or not data.get('url'):
        return jsonify({'error': 'URL é obrigatória.'}), 400

    url = data['url'].strip()
    cookies_browser = data.get('cookies_browser', '')
    cookies_content = data.get('cookies_content', '')
    
    cookiefile = None
    if cookies_browser == 'custom' and cookies_content:
        cookiefile = os.path.join(app.root_path, '..', 'youtube_cookies.txt')
        with open(cookiefile, 'w', encoding='utf-8') as f:
            f.write(cookies_content)

    try:
        result = download_manager.analyze(url, cookies_browser=cookies_browser, cookiefile=cookiefile)
        return jsonify(result)
    except DownloadError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Erro inesperado: {str(e)}'}), 500


@app.route('/start-download', methods=['POST'])
def start_download_route():
    """
    Start a download group in a background thread.
    Returns immediately with a group_id.
    """
    data = request.get_json(silent=True)
    if not data or not data.get('url'):
        return jsonify({'error': 'URL é obrigatória.'}), 400

    url = data['url'].strip()
    media_type = data.get('type', 'video')
    quality_val = data.get('quality', 'best')
    audio_format = data.get('audio_format', 'mp3_320')
    is_playlist = data.get('is_playlist', False)
    playlist_title = data.get('playlist_title', None)
    entries = data.get('entries', [])
    adv_options = data.get('options', {})
    group_title = data.get('title', 'Download')

    cookies_browser = adv_options.get('cookies_browser', '')
    cookies_content = data.get('cookies_content', '')

    if cookies_browser == 'custom' and cookies_content:
        cookiefile = os.path.join(app.root_path, '..', 'youtube_cookies.txt')
        with open(cookiefile, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        adv_options['cookiefile'] = cookiefile

    group_id = str(uuid.uuid4())

    if is_playlist and entries:
        # Build item list for playlist
        items = [
            {
                'item_id': str(uuid.uuid4()),
                'title': e.get('title', f'Item {i+1}'),
                'url': e.get('url', ''),
                'status': 'waiting',
                'percent': 0,
                'speed': '',
                'eta': '',
                'error': None,
            }
            for i, e in enumerate(entries)
        ]
        output_dir = download_manager._get_output_dir(media_type, playlist_title)
    else:
        items = [
            {
                'item_id': str(uuid.uuid4()),
                'title': group_title,
                'url': url,
                'status': 'waiting',
                'percent': 0,
                'speed': '',
                'eta': '',
                'error': None,
            }
        ]
        output_dir = download_manager._get_output_dir(media_type, None)

    with groups_lock:
        groups[group_id] = {
            'group_id': group_id,
            'title': playlist_title if is_playlist else group_title,
            'type': 'playlist' if is_playlist else 'video',
            'is_active': True,
            'media_type': media_type,
            'output_dir': output_dir,
            'items': items,
            'playlist_title': playlist_title,
        }

    def run_group():
        grp_items = items  # reference to same list
        try:
            for idx, item in enumerate(grp_items):
                item_id = item['item_id']
                entry_url = item['url']

                if not entry_url:
                    with groups_lock:
                        item['status'] = 'error'
                        item['error'] = 'URL inválida'
                    continue

                # Mark as downloading
                with groups_lock:
                    item['status'] = 'downloading'
                    item['percent'] = 0

                def make_progress_cb(the_item):
                    def progress_callback(info):
                        with groups_lock:
                            status = info.get('status', 'downloading')
                            if status == 'downloading':
                                the_item['status'] = 'downloading'
                                the_item['percent'] = round(info.get('percent', 0), 1)
                                the_item['speed'] = info.get('speed', '')
                                the_item['eta'] = info.get('eta', '')
                            elif status == 'processing':
                                the_item['status'] = 'processing'
                                the_item['percent'] = 100
                                the_item['speed'] = ''
                                the_item['eta'] = ''
                    return progress_callback

                cb = make_progress_cb(item)

                try:
                    result = download_manager.download(
                        task_id=f"{group_id}_{item_id}",
                        url=entry_url,
                        media_type=media_type,
                        quality=quality_val,
                        audio_format=audio_format,
                        progress_callback=cb,
                        playlist_title=playlist_title,
                        playlist_index=idx + 1,
                        playlist_total=len(grp_items),
                        options=adv_options,
                        item_title=item['title'],
                    )
                    with groups_lock:
                        item['status'] = 'complete'
                        item['percent'] = 100
                        item['speed'] = ''
                        item['eta'] = ''
                        # Update output_dir if we got a real result
                        if result.get('output_dir'):
                            groups[group_id]['output_dir'] = result['output_dir']

                except DownloadError as e:
                    with groups_lock:
                        if 'cancelado' in str(e).lower():
                            item['status'] = 'cancelled'
                        else:
                            item['status'] = 'error'
                            item['error'] = str(e)
                    # If cancelled, stop processing remaining items
                    if 'cancelado' in str(e).lower():
                        # Cancel remaining waiting items
                        with groups_lock:
                            for remaining in grp_items[idx+1:]:
                                remaining['status'] = 'cancelled'
                        break

        except Exception as e:
            # Mark any waiting items as error
            with groups_lock:
                for item in grp_items:
                    if item['status'] == 'waiting':
                        item['status'] = 'error'
                        item['error'] = str(e)
        finally:
            with groups_lock:
                if group_id in groups:
                    groups[group_id]['is_active'] = False

    thread = threading.Thread(target=run_group, daemon=True)
    thread.start()

    return jsonify({'status': 'started', 'group_id': group_id})


@app.route('/progress', methods=['GET'])
def get_progress():
    """Return the status of all current groups."""
    with groups_lock:
        result = []
        for gid, g in groups.items():
            result.append({
                'group_id': g['group_id'],
                'title': g['title'],
                'type': g['type'],
                'is_active': g['is_active'],
                'media_type': g['media_type'],
                'output_dir': g['output_dir'],
                'playlist_title': g.get('playlist_title'),
                'items': [dict(item) for item in g['items']],
            })
    return jsonify({'groups': result})


@app.route('/cancel', methods=['POST'])
def cancel():
    """Cancel all active downloads in a group."""
    data = request.get_json(silent=True) or {}
    group_id = data.get('group_id')
    item_id = data.get('item_id')

    if not group_id:
        return jsonify({'error': 'group_id não fornecido.'}), 400

    with groups_lock:
        if group_id not in groups:
            return jsonify({'error': 'Grupo não encontrado.'}), 404

        g = groups[group_id]
        # Build a list of task_ids to cancel
        task_ids_to_cancel = []
        for item in g['items']:
            if item['status'] in ('downloading', 'processing', 'waiting'):
                if item_id is None or item['item_id'] == item_id:
                    task_ids_to_cancel.append(f"{group_id}_{item['item_id']}")
                    item['status'] = 'cancelled'

    for tid in task_ids_to_cancel:
        download_manager.cancel(tid)

    return jsonify({'message': 'Cancelamento solicitado.'})


@app.route('/clear-group', methods=['POST'])
def clear_group():
    """Remove a finished group from server state."""
    data = request.get_json(silent=True) or {}
    group_id = data.get('group_id')
    with groups_lock:
        if group_id in groups:
            del groups[group_id]
    return jsonify({'status': 'cleared'})


@app.route('/clear-completed', methods=['POST'])
def clear_completed():
    """Remove all finished (non-active) groups from server state."""
    with groups_lock:
        to_delete = [gid for gid, g in groups.items() if not g['is_active']]
        for gid in to_delete:
            del groups[gid]
    return jsonify({'status': 'cleared', 'count': len(to_delete)})


@app.route('/open-folder')
def open_folder():
    """Open the destination folder in Windows Explorer."""
    folder_type = request.args.get('type', 'video')
    playlist = request.args.get('playlist', '')

    if folder_type == 'audio':
        folder_name = 'MP3'
    else:
        folder_name = 'Videos'

    folder_path = os.path.join(BASE_DIR, folder_name)

    if playlist:
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', playlist).strip('. ')
        playlist_path = os.path.join(folder_path, safe_name)
        if os.path.exists(playlist_path):
            folder_path = playlist_path

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    try:
        os.startfile(folder_path)
        return jsonify({'message': 'Pasta aberta.'})
    except Exception as e:
        return jsonify({'error': f'Não foi possível abrir a pasta: {str(e)}'}), 500


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def start_server(port=9731):
    """Start the Flask app with Waitress."""
    from waitress import serve
    print(f"[YTWERSE] Servidor iniciando na porta {port}...")
    serve(app, host='127.0.0.1', port=port, threads=8, channel_timeout=120,
          _quiet=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9731)
    args = parser.parse_args()
    start_server(args.port)
