"""
YTWERSE — DownloadManager
Wrapper around yt-dlp CLI executable with cancellation support and progress parsing.
"""

import os
import sys
import threading
import subprocess
import time
import re
import json
import glob


class DownloadError(Exception):
    """Custom exception for download errors with user-friendly messages."""
    pass


class DownloadManager:
    """Manages video/audio downloads using yt-dlp CLI."""

    SUPPORTED_BROWSERS = ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi', 'chromium']

    def __init__(self, base_dir=None):
        if base_dir is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.base_dir = base_dir
        self.tasks = {} # task_id -> {'cancel_event': Event, 'process': Popen}
        self._lock = threading.Lock()

    def _sanitize_filename(self, name):
        if not name:
            return "unknown"
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = sanitized.strip('. ')
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized if sanitized else "unknown"

    def _get_output_dir(self, media_type, playlist_title=None):
        folder = 'MP3' if media_type == 'audio' else 'Videos'
        output_dir = os.path.join(self.base_dir, folder)

        if playlist_title:
            safe_title = self._sanitize_filename(playlist_title)
            output_dir = os.path.join(output_dir, safe_title)

        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _check_ffmpeg(self):
        bin_dir = os.path.join(self.base_dir, 'bin')
        if os.path.exists(os.path.join(bin_dir, 'ffmpeg.exe')):
            return True
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def analyze(self, url, cookies_browser=None, cookiefile=None):
        if not url or not url.strip():
            raise DownloadError("URL não pode estar vazia.")

        bin_dir = os.path.join(self.base_dir, 'bin')
        ytdlp_exe = os.path.join(bin_dir, 'yt-dlp.exe')
        if not os.path.exists(ytdlp_exe):
            ytdlp_exe = 'yt-dlp'

        cmd = [ytdlp_exe, "-J", "--flat-playlist", "--no-warnings"]

        if cookiefile and os.path.exists(cookiefile):
            cmd.extend(["--cookies", cookiefile])
        elif cookies_browser and cookies_browser in self.SUPPORTED_BROWSERS:
            cmd.extend(["--cookies-from-browser", cookies_browser])

        cmd.append(url)

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Erro desconhecido"
                self._handle_yt_dlp_error(error_msg)

            info = json.loads(result.stdout)

            is_playlist = info.get('_type') == 'playlist' or 'entries' in info

            if is_playlist:
                entries = list(info.get('entries', []))
                valid_entries = [e for e in entries if e is not None]

                return {
                    'type': 'playlist',
                    'title': info.get('title', 'Playlist sem título'),
                    'uploader': info.get('uploader', 'Desconhecido'),
                    'count': len(valid_entries),
                    'thumbnail': info.get('thumbnails', [{}])[-1].get('url', '') if info.get('thumbnails') else '',
                    'url': url,
                    'entries': [
                        {
                            'title': e.get('title', f'Vídeo {i+1}'),
                            'duration': e.get('duration', 0),
                            'url': e.get('url', e.get('webpage_url', '')),
                        }
                        for i, e in enumerate(valid_entries)
                    ]
                }
            else:
                duration = info.get('duration', 0)
                duration_str = ''
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    hours, mins = divmod(mins, 60)
                    if hours:
                        duration_str = f'{hours}:{mins:02d}:{secs:02d}'
                    else:
                        duration_str = f'{mins}:{secs:02d}'

                formats = info.get('formats', [])
                available_qualities = set()
                for f in formats:
                    h = f.get('height')
                    if h and f.get('vcodec', 'none') != 'none':
                        if h >= 1080: available_qualities.add('1080p')
                        if h >= 720: available_qualities.add('720p')
                        if h >= 480: available_qualities.add('480p')
                        if h >= 360: available_qualities.add('360p')

                subtitles = info.get('subtitles', {})
                auto_captions = info.get('automatic_captions', {})
                available_subs = sorted(set(list(subtitles.keys()) + list(auto_captions.keys())))

                return {
                    'type': 'video',
                    'title': info.get('title', 'Sem título'),
                    'uploader': info.get('uploader', info.get('channel', 'Desconhecido')),
                    'duration': duration_str,
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url,
                    'available_qualities': sorted(list(available_qualities),
                                                   key=lambda x: int(x.replace('p', '')),
                                                   reverse=True),
                    'has_subtitles': len(subtitles) > 0 or len(auto_captions) > 0,
                    'available_subs': available_subs[:20],
                }

        except DownloadError:
            raise
        except json.JSONDecodeError:
            raise DownloadError("O yt-dlp retornou dados inválidos. Tente novamente.")
        except Exception as e:
            raise DownloadError(f"Erro ao executar yt-dlp: {str(e)}")

    def _handle_yt_dlp_error(self, error_msg):
        error_msg = re.sub(r'\x1b\[[0-9;]*m', '', str(error_msg))
        
        if 'cookie database' in error_msg.lower():
            raise DownloadError(
                "O navegador está bloqueando o acesso aos cookies. "
                "Feche o navegador e tente analisar novamente."
            )
        elif 'Sign in to confirm you' in error_msg or 'bot' in error_msg.lower() or '429' in error_msg:
            raise DownloadError(
                "O YouTube bloqueou o acesso por suspeita de robô. "
                "Ative a opção de Cookies Personalizados e tente novamente."
            )
        elif 'Private video' in error_msg or 'Sign in' in error_msg:
            raise DownloadError(
                "Este vídeo é privado ou requer login. Ative a opção de Cookies Personalizados."
            )
        elif 'Requested format is not available' in error_msg:
            raise DownloadError(
                "O YouTube não disponibilizou formatos válidos para este vídeo. "
                "Isso geralmente ocorre em videoclipes oficiais (VEVO) ou filmes com proteção de direitos autorais (DRM)."
            )
        elif 'Video unavailable' in error_msg:
            raise DownloadError("Este vídeo foi removido ou não está disponível.")
        elif 'is not a valid URL' in error_msg or 'Unsupported URL' in error_msg:
            raise DownloadError("URL inválida. Cole uma URL válida do YouTube.")
        else:
            raise DownloadError(f"Erro do yt-dlp: {error_msg.strip()}")

    def download(self, task_id, url, media_type='video', quality='best', audio_format='mp3_320',
                 progress_callback=None, playlist_title=None, playlist_index=None,
                 playlist_total=None, options=None, item_title=None):
        
        cancel_event = threading.Event()
        with self._lock:
            self.tasks[task_id] = {'cancel_event': cancel_event, 'process': None}
            
        options = options or {}
        self._check_ffmpeg()
        output_dir = self._get_output_dir(media_type, playlist_title)

        try:
            test_file = os.path.join(output_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except PermissionError:
            raise DownloadError(
                f"Sem permissão de escrita em: {output_dir}\n"
                "Tente executar o YTWERSE como administrador."
            )

        bin_dir = os.path.join(self.base_dir, 'bin')
        ytdlp_exe = os.path.join(bin_dir, 'yt-dlp.exe')
        if not os.path.exists(ytdlp_exe):
            ytdlp_exe = 'yt-dlp'

        cmd = [ytdlp_exe, "--newline", "--no-warnings", "--no-quiet", "--windows-filenames", "--file-access-retries", "10"]
        
        if os.path.exists(os.path.join(bin_dir, 'ffmpeg.exe')):
            cmd.extend(["--ffmpeg-location", bin_dir])

        cookiefile = options.get('cookiefile')
        cookies_browser = options.get('cookies_browser', '')
        if cookiefile and os.path.exists(cookiefile):
            cmd.extend(["--cookies", cookiefile])
        elif cookies_browser and cookies_browser in self.SUPPORTED_BROWSERS:
            cmd.extend(["--cookies-from-browser", cookies_browser])

        concurrent = options.get('concurrent_fragments', 1)
        if concurrent and int(concurrent) > 1:
            cmd.extend(["-N", str(concurrent)])

        start_time = options.get('start_time')
        end_time = options.get('end_time')
        if start_time is not None or end_time is not None:
            s = start_time if start_time is not None else 0
            e = end_time if end_time is not None else "inf"
            cmd.extend(["--download-sections", f"*{s}-{e}", "--force-keyframes-at-cuts"])

        if media_type == 'audio':
            cmd.append("-x")
            if audio_format == 'm4a':
                cmd.extend(["--audio-format", "m4a", "-f", "bestaudio[ext=m4a]/bestaudio"])
            elif audio_format in ('wav', 'opus'):
                cmd.extend(["--audio-format", audio_format, "--audio-quality", "0", "-f", "bestaudio/best"])
            else:
                bitrate = '320' if audio_format == 'mp3_320' else '192'
                cmd.extend(["--audio-format", "mp3", "--audio-quality", bitrate, "-f", "bestaudio/best"])
            cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])
        else:
            if quality == 'best':
                cmd.extend(["-f", "bv*+ba/b", "-S", "ext:mp4:m4a", "--merge-output-format", "mp4"])
            else:
                height = quality.replace('p', '')
                cmd.extend(["-f", "bv*+ba/b", "-S", f"res:{height},ext:mp4:m4a", "--merge-output-format", "mp4"])
            cmd.extend(["-o", os.path.join(output_dir, "%(title)s.%(ext)s")])

        if options.get('subtitles'):
            sub_langs = options.get('sub_langs', 'pt.*,en')
            cmd.append("--write-subs")
            if options.get('auto_subs', True):
                cmd.append("--write-auto-subs")
            cmd.extend(["--sub-langs", sub_langs, "--sub-format", "srt/best"])
            if options.get('embed_subs', True) and media_type == 'video':
                cmd.append("--embed-subs")

        if options.get('embed_thumbnail'):
            cmd.append("--embed-thumbnail")

        if options.get('embed_metadata'):
            cmd.extend(["--embed-metadata", "--parse-metadata", "comment:Downloaded with YTWERSE"])

        cmd.extend(["--print", "after_move:filepath"])
        cmd.append(url)

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, encoding='utf-8', errors='replace', bufsize=1, universal_newlines=True,
                                     startupinfo=startupinfo)
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['process'] = process

            final_filename = None
            last_error = None
            for line in process.stdout:
                if cancel_event.is_set():
                    process.terminate()
                    break

                line = line.strip()
                if not line:
                    continue

                if line.startswith('ERROR:'):
                    last_error = line.replace('ERROR:', '').strip()

                if '[download]' in line and '%' in line:
                    percent_match = re.search(r'\[download\]\s+([0-9.]+)%', line)
                    if percent_match and progress_callback:
                        try:
                            percent = float(percent_match.group(1))
                            speed_match = re.search(r'at\s+([a-zA-Z0-9.~/]+)', line)
                            eta_match = re.search(r'ETA\s+([0-9:]+)', line)
                            
                            speed_str = speed_match.group(1) if speed_match else ''
                            eta_str = eta_match.group(1) if eta_match else ''
                            
                            progress_callback({
                                'status': 'downloading',
                                'percent': percent,
                                'speed': speed_str,
                                'eta': eta_str,
                                'filename': item_title if item_title else 'Baixando arquivo...', 
                                'playlist_index': playlist_index,
                                'playlist_total': playlist_total,
                            })
                        except ValueError:
                            pass
                elif '[ExtractAudio]' in line or '[Merger]' in line or '[Metadata]' in line:
                    if progress_callback:
                        progress_callback({
                            'status': 'processing',
                            'percent': 100,
                            'filename': 'Processando...',
                            'message': line,
                            'playlist_index': playlist_index,
                            'playlist_total': playlist_total,
                        })
                elif (output_dir in line) or (os.name == 'nt' and output_dir.replace('\\', '/') in line.replace('\\', '/')):
                    clean_line = line.strip()
                    if os.path.isfile(clean_line):
                        final_filename = clean_line

            return_code = process.wait()
            
            if cancel_event.is_set():
                self._cleanup_partial_files(output_dir)
                raise DownloadError("Download cancelado pelo usuário.")
            if return_code != 0:
                if last_error:
                    raise DownloadError(last_error)
                raise DownloadError(f"Erro do yt-dlp: Processo retornou erro {return_code}")

            if not final_filename:
                list_of_files = glob.glob(os.path.join(output_dir, '*'))
                if list_of_files:
                    final_filename = max(list_of_files, key=os.path.getctime)

            return {
                'status': 'complete',
                'filename': os.path.basename(final_filename) if final_filename else 'unknown',
                'filepath': final_filename,
                'output_dir': output_dir,
                'media_type': media_type,
            }

        except DownloadError:
            raise
        except Exception as e:
            if cancel_event.is_set():
                self._cleanup_partial_files(output_dir)
                raise DownloadError("Download cancelado pelo usuário.")
            raise DownloadError(f"Erro inesperado: {str(e)}")
        finally:
            with self._lock:
                if task_id in self.tasks:
                    del self.tasks[task_id]

    def cancel(self, task_id):
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id]['cancel_event'].set()
                proc = self.tasks[task_id].get('process')
                if proc:
                    try:
                        proc.terminate()
                    except Exception:
                        pass

    def _cleanup_partial_files(self, directory):
        if not os.path.exists(directory):
            return
        patterns = ['*.part', '*.ytdl', '*.part-Frag*']
        for pattern in patterns:
            for filepath in glob.glob(os.path.join(directory, pattern)):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
