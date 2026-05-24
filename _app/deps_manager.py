import os
import sys
import zipfile
import requests


def _safe_print(msg):
    """Print que funciona mesmo sem console (modo noconsole do PyInstaller)."""
    try:
        if sys.stdout is not None:
            print(msg, flush=True)
    except Exception:
        pass


def _safe_write(msg):
    """sys.stdout.write seguro sem console."""
    try:
        if sys.stdout is not None:
            sys.stdout.write(msg)
            sys.stdout.flush()
    except Exception:
        pass


def download_file(url, dest_path, progress_callback=None):
    """Baixa um arquivo com progresso opcional via callback."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024  # 1 MB

    _safe_print(f"\nBaixando {os.path.basename(dest_path)}...")

    downloaded = 0
    with open(dest_path, 'wb') as f:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            f.write(data)

            if progress_callback and total_size > 0:
                pct = int(100 * downloaded / total_size)
                progress_callback(pct, downloaded, total_size)
            elif total_size > 0:
                percent = int(50 * downloaded / total_size)
                _safe_write(f"\r[{'=' * percent}{' ' * (50 - percent)}] {downloaded}/{total_size} bytes")

    _safe_print("\nDownload concluído!")


def ensure_dependencies(base_dir, progress_callback=None):
    """Verifica e baixa as dependências na pasta bin.

    Args:
        base_dir: diretório base do app (onde fica a pasta bin/)
        progress_callback: opcional — função(step: str, pct: int) para UI
    """
    def notify(step, pct=0):
        _safe_print(f"[Deps] {step}")
        if progress_callback:
            try:
                progress_callback(step, pct)
            except Exception:
                pass

    bin_dir = os.path.join(base_dir, 'bin')
    os.makedirs(bin_dir, exist_ok=True)

    ytdlp_path = os.path.join(bin_dir, 'yt-dlp.exe')
    ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')

    ytdlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

    # 1. Download yt-dlp.exe
    if not os.path.exists(ytdlp_path):
        notify("Baixando yt-dlp...", 10)
        download_file(ytdlp_url, ytdlp_path)
        notify("yt-dlp instalado!", 40)
    else:
        notify("yt-dlp OK", 40)

    # 2. Download FFmpeg
    if not os.path.exists(ffmpeg_path):
        notify("Baixando FFmpeg (pode demorar)...", 50)
        zip_path = os.path.join(bin_dir, 'ffmpeg.zip')
        download_file(ffmpeg_url, zip_path)

        notify("Extraindo FFmpeg...", 85)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('ffmpeg.exe') or member.endswith('ffprobe.exe'):
                    member_name = os.path.basename(member)
                    source = zip_ref.open(member)
                    target = open(os.path.join(bin_dir, member_name), "wb")
                    with source, target:
                        import shutil
                        shutil.copyfileobj(source, target)

        notify("Limpando arquivos temporários...", 95)
        os.remove(zip_path)
        notify("FFmpeg instalado com sucesso!", 98)
    else:
        notify("FFmpeg OK", 98)

    notify("Todas as dependências verificadas.", 100)


if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ensure_dependencies(base)
