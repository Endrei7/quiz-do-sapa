"""Launcher desktop PyWebView 100% off-line para o Quiz do S.A.P.A."""

import ctypes
import os
import sys
import webview

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def resource_path(relative_path: str) -> str:
    """Resolve caminhos tanto no Python local quanto dentro do .exe (sys._MEIPASS)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class DesktopApi:
    """API Python exposta para o JavaScript da janela nativa (sem atributos CLR expostos)."""

    def toggle_fullscreen(self):
        if webview.windows:
            webview.windows[0].toggle_fullscreen()

    def close_app(self):
        if webview.windows:
            webview.windows[0].destroy()


def create_app_window(api: DesktopApi, title: str = "Quiz do S.A.P.A. — Expedição na Floresta"):
    index_file = resource_path(os.path.join("web", "index.html"))
    window = webview.create_window(
        title=title,
        url=index_file,
        js_api=api,
        width=1280,
        height=760,
        min_size=(1024, 680),
        background_color="#1a5343",
    )
    return window


def main():
    api = DesktopApi()
    create_app_window(api)
    webview.start(gui="edgechromium", http_server=False)


if __name__ == "__main__":
    main()
