"""
desktop_tray.py — Desktop Runner and System Tray Daemon for FirstReply PC.
Runs the local FastAPI sidecar server and provides a tray icon with quick actions.
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from firstreply_pc.engine import database
from firstreply_pc.engine.capture import CaptureLayer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FirstReplyPC-Tray")

SERVER_PORT = 8123
SERVER_HOST = "127.0.0.1"


def run_fastapi_server() -> None:
    """Run uvicorn server in dedicated thread."""
    from firstreply_pc.engine.server import app

    config = uvicorn.Config(
        app=app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def open_user_ui() -> None:
    """Open User Draft Card in default desktop browser."""
    webbrowser.open(f"http://{SERVER_HOST}:{SERVER_PORT}/")


def open_dev_ui() -> None:
    """Open CCCO Dev Dashboard in default desktop browser."""
    webbrowser.open(f"http://{SERVER_HOST}:{SERVER_PORT}/dev")


def start_tray() -> None:
    """Start desktop system tray or fallback to clean console loop."""
    logger.info("Initializing FirstReply PC Desktop Daemon...")
    database.init_db()

    # Start FastAPI server in background daemon thread
    server_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    server_thread.start()
    time.sleep(1.0)  # Wait for server bind

    logger.info(f"FirstReply PC Server running at http://{SERVER_HOST}:{SERVER_PORT}/")
    logger.info(f"CCCO Dev Dashboard running at http://{SERVER_HOST}:{SERVER_PORT}/dev")

    # Try importing pystray for native system tray icon if available
    try:
        import pystray
        from PIL import Image, ImageDraw

        # Generate a clean 64x64 blue & green icon
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([4, 4, 60, 60], radius=14, fill=(37, 99, 235))
        draw.ellipse([20, 20, 44, 44], fill=(16, 185, 129))

        def on_open_draft(icon, item):
            open_user_ui()

        def on_open_dev(icon, item):
            open_dev_ui()

        def on_exit(icon, item):
            icon.stop()
            sys.exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open Draft Card (Ctrl+Shift+R)", on_open_draft, default=True),
            pystray.MenuItem("Dev & Quota Dashboard", on_open_dev),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit FirstReply PC", on_exit),
        )

        icon = pystray.Icon("FirstReplyPC", img, "FirstReply PC (Active)", menu)
        logger.info("System Tray icon active. Opening UI...")
        open_user_ui()
        icon.run()

    except Exception as e:
        logger.info(f"Pystray or PIL not installed ({e}) — running in lightweight standalone desktop mode.")
        open_user_ui()
        print("\n" + "=" * 64)
        print("  ⚡ FirstReply PC is running locally!")
        print(f"  • User Draft UI   : http://{SERVER_HOST}:{SERVER_PORT}/")
        print(f"  • Dev Dashboard   : http://{SERVER_HOST}:{SERVER_PORT}/dev")
        print("  • Core Cost       : $0.00 (Free Forever)")
        print("  Press Ctrl+C in this terminal to stop.")
        print("=" * 64 + "\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down FirstReply PC...")


if __name__ == "__main__":
    start_tray()
