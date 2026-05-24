"""
YTWERSE — Launcher
Checks dependencies, starts the Flask/Waitress server, shows a splash screen,
then opens the app in a PyWebView window.
This file is compiled into YTWERSE.exe via PyInstaller.
"""

import os
import sys
import time
import socket
import threading
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PORT = 9731
MAX_PORT_ATTEMPTS = 10
SERVER_TIMEOUT = 20  # seconds

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_base_dir():
    """Get the directory where the .exe (or script) is located."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_app_dir():
    """Get the _app directory — handles both frozen and dev modes."""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundles _app inside _MEIPASS
        return os.path.join(sys._MEIPASS, '_app')
    return os.path.join(get_base_dir(), '_app')


BASE_DIR = get_base_dir()
APP_DIR = get_app_dir()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg):
    """Print a timestamped log message."""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[YTWERSE {timestamp}] {msg}")


# ---------------------------------------------------------------------------
# Splash Screen
# ---------------------------------------------------------------------------

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YTWERSE")
        self.root.overrideredirect(True)

        bg = "#050505" # Very dark background to match the provided banner
        self.root.configure(bg=bg)

        # Banner or Title
        self.banner_img = None
        banner_path = self._find_asset('banner.png')
        
        final_w, final_h = 500, 300
        
        if banner_path:
            try:
                self.banner_img = tk.PhotoImage(file=banner_path)
                img_w = self.banner_img.width()
                img_h = self.banner_img.height()
                
                # Subsample if too big (adjust threshold to make banner reasonable size)
                factor = 1
                while img_w / factor > 650 or img_h / factor > 400:
                    factor += 1
                
                if factor > 1:
                    self.banner_img = self.banner_img.subsample(factor, factor)
                
                final_w = self.banner_img.width()
                final_h = self.banner_img.height()
            except Exception:
                banner_path = None

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - final_w) // 2
        y = (sh - final_h) // 2
        self.root.geometry(f"{final_w}x{final_h}+{x}+{y}")

        try:
            icon_path = self._find_asset('icon.ico')
            if icon_path:
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.canvas = tk.Canvas(self.root, width=final_w, height=final_h, highlightthickness=0, bg=bg)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        if banner_path and self.banner_img:
            self.canvas.create_image(final_w // 2, final_h // 2, image=self.banner_img)
        else:
            self.canvas.create_text(final_w // 2, final_h // 2, text="YTWERSE", font=("Segoe UI", 26, "bold"), fill="#ffffff")

        # Animation state
        self.loader_angle = 0
        self.loader_speed = 15
        self.loader_running = True
        
        loader_size = 30
        loader_thickness = 4
        
        lx = final_w // 2
        ly = final_h - 45
        
        # Loader (More "destaque": thicker, brighter, longer extent)
        self.arc_id = self.canvas.create_arc(
            lx - loader_size//2, ly - loader_size//2,
            lx + loader_size//2, ly + loader_size//2,
            start=self.loader_angle, extent=150,
            outline="#c084fc", width=loader_thickness, style=tk.ARC
        )
        
        # Status Text (Tech/Coding font, transparent background on canvas)
        self.text_id = self.canvas.create_text(
            final_w // 2, final_h - 15,
            text="Loading...",
            fill="#a5b4fc",
            font=("Consolas", 9)
        )

        self.root.attributes('-topmost', True)
        self.root.update()
        
        self._animate()

    def _animate(self):
        if not self.loader_running: return
        self.loader_angle = (self.loader_angle - self.loader_speed) % 360
        self.canvas.itemconfigure(self.arc_id, start=self.loader_angle)
        self.root.after(30, self._animate)

    def _find_asset(self, filename):
        candidates = [
            os.path.join(BASE_DIR, 'assets', filename),
            os.path.join(os.path.dirname(__file__), 'assets', filename),
            os.path.join(APP_DIR, 'static', filename),
            os.path.join(BASE_DIR, filename),
        ]
        if getattr(sys, 'frozen', False):
            candidates.insert(0, os.path.join(sys._MEIPASS, 'assets', filename))
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def set_status(self, msg):
        self.canvas.itemconfigure(self.text_id, text=msg)
        self.root.update()

    def close(self):
        self.loader_running = False
        self.root.destroy()


# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------

def find_free_port(start_port=DEFAULT_PORT, max_attempts=MAX_PORT_ATTEMPTS):
    """Find a free port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            log(f"Porta {port} em uso, tentando próxima...")
    return None


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def start_server(port):
    """Start the Flask/Waitress server in a background thread."""
    server_path = os.path.join(APP_DIR, 'server.py')

    if not os.path.exists(server_path):
        return False

    # Add _app to sys.path so imports work
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    def run_server():
        try:
            spec = importlib.util.spec_from_file_location("server", server_path)
            server_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server_module)
            server_module.start_server(port=port)
        except Exception as e:
            log(f"Erro fatal no servidor: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return True


def wait_for_server(port, timeout=SERVER_TIMEOUT):
    """Poll the server health endpoint until it responds or timeout."""
    import urllib.request
    import urllib.error

    url = f"http://127.0.0.1:{port}/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=2)
            if req.status == 200:
                return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.4)

    return False


# ---------------------------------------------------------------------------
# Error dialog
# ---------------------------------------------------------------------------

def show_error(title, message):
    """Show an error dialog using tkinter."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        log(f"ERRO: {message}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    splash = SplashScreen()
    app_state = {'url': None, 'error': None}

    def background_init():
        try:
            # Step 1: Ensure dependencies (yt-dlp, ffmpeg)
            splash.set_status("Verificando dependências...")
            if APP_DIR not in sys.path:
                sys.path.insert(0, APP_DIR)

            import deps_manager

            def deps_progress(step, pct=0):
                splash.set_status(step)

            deps_manager.ensure_dependencies(BASE_DIR, progress_callback=deps_progress)

            # Step 2: Find free port
            splash.set_status("Procurando porta disponível...")
            port = find_free_port()
            if port is None:
                app_state['error'] = "Não foi possível encontrar uma porta livre.\nFeche outros programas e tente novamente."
                return

            # Step 3: Start server
            splash.set_status("Iniciando servidor...")
            log(f"Iniciando servidor na porta {port}...")
            if not start_server(port):
                app_state['error'] = f"Arquivo server.py não encontrado em:\n{APP_DIR}"
                return

            # Step 4: Wait for server
            splash.set_status("Aguardando servidor ficar pronto...")
            if not wait_for_server(port):
                app_state['error'] = f"O servidor não respondeu em {SERVER_TIMEOUT} segundos.\nTente fechar e abrir novamente."
                return

            # Step 5: Open in PyWebView
            splash.set_status("Abrindo interface...")
            app_state['url'] = f"http://127.0.0.1:{port}"
            log(f"Servidor pronto. Abrindo: {app_state['url']}")
        except Exception as e:
            app_state['error'] = f"Erro inesperado: {str(e)}"
            log(app_state['error'])

    import threading
    t = threading.Thread(target=background_init, daemon=True)
    t.start()

    def check_thread():
        if t.is_alive():
            splash.root.after(100, check_thread)
        else:
            splash.close()

    splash.root.after(100, check_thread)
    splash.root.mainloop()
    
    try:
        splash.root.destroy()
    except Exception:
        pass

    if app_state['error']:
        show_error("YTWERSE - Erro", app_state['error'])
        sys.exit(1)

    url = app_state.get('url')
    if not url:
        sys.exit(1)

    try:
        import webview

        # Find icon for webview
        icon_path = None
        icon_candidates = [
            os.path.join(BASE_DIR, 'assets', 'icon.ico'),
            os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico'),
            os.path.join(APP_DIR, 'static', 'icon.ico'),
            os.path.join(BASE_DIR, 'icon.ico'),
        ]
        if getattr(sys, 'frozen', False):
            icon_candidates.insert(0, os.path.join(sys._MEIPASS, 'assets', 'icon.ico'))
        for p in icon_candidates:
            if os.path.exists(p):
                icon_path = p
                break

        window = webview.create_window(
            title='YTWERSE',
            url=url,
            width=1100,
            height=720,
            min_size=(800, 600),
            resizable=True,
            maximized=True,
        )

        webview.start(debug=False, icon=icon_path)

    except Exception as e:
        pass
        show_error("YTWERSE - Erro Inesperado", str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
