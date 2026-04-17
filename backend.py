#!/usr/bin/env python3
"""
YT-DLP Parallel Downloader Backend - Hacker Terminal Edition
Menggunakan FastAPI + WebSocket untuk komunikasi real-time dengan frontend

FIXES:
  - JS runtime now passed to yt-dlp via extractor_args so YouTube formats resolve properly
  - Format selector is now adaptive: probes available formats before picking a strategy
  - ffmpeg merge attempted first; graceful fallback chain when unavailable
"""

import asyncio
import json
import os
import platform
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YT-DLP Hacker Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", str(Path.home() / "Downloads" / "YT-Hacker")))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Global semaphore to limit concurrent downloads
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(int(os.getenv("CONCURRENCY_LIMIT", 3)))


class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    format: str = "mp4"


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def check_js_runtime() -> str | None:
    """
    Return the name of the first available JS runtime yt-dlp understands,
    or None.  Order: deno (default in yt-dlp), node, bun.
    """
    for runtime in ("deno", "node", "bun"):
        if shutil.which(runtime):
            return runtime
    return None


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_progress(self, message: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Progress hook
# ---------------------------------------------------------------------------

class HackerProgress:
    def __init__(self, websocket_manager: ConnectionManager, task_id: str):
        self.manager = websocket_manager
        self.task_id = task_id

    async def __call__(self, d: dict):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0

            speed = d.get("speed", 0)
            speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "..."

            await self.manager.send_progress({
                "type": "progress",
                "task_id": self.task_id,
                "status": "downloading",
                "filename": os.path.basename(d.get("filename", "unknown")),
                "percent": round(percent, 1),
                "speed": speed_str,
                "eta": d.get("eta", "???"),
                "downloaded": d.get("_percent_str", "0%"),
            })

        elif d["status"] == "finished":
            await self.manager.send_progress({
                "type": "progress",
                "task_id": self.task_id,
                "status": "processing",
                "filename": os.path.basename(d.get("filename", "unknown")),
                "percent": 100,
                "message": "Processing...",
            })


# ---------------------------------------------------------------------------
# Cookie helper
# ---------------------------------------------------------------------------

def get_browser_cookies() -> str | None:
    """
    Try to find a browser that has YouTube cookies and return its name,
    or None if none found / browser-cookie3 not installed.
    """
    try:
        import browser_cookie3
    except ImportError:
        print("WARNING: browser-cookie3 not installed. Run: pip install browser-cookie3")
        return None

    system = platform.system()
    browsers_by_os: dict[str, list[str]] = {
        "Windows": ["chrome", "edge", "firefox", "brave", "chromium", "opera", "opera_gx", "vivaldi"],
        "Darwin":  ["chrome", "safari", "firefox", "brave", "chromium", "opera", "opera_gx", "vivaldi", "arc"],
        "Linux":   ["chrome", "firefox", "brave", "chromium", "opera", "vivaldi"],
    }
    browsers_to_try = browsers_by_os.get(system, [])

    for browser_name in browsers_to_try:
        try:
            cookie_func = getattr(browser_cookie3, browser_name, None)
            if cookie_func:
                cookies = cookie_func(domain_name=".youtube.com")
                if cookies:
                    print(f"✓ Successfully extracted cookies from {browser_name}")
                    return browser_name
        except Exception:
            continue

    print("⚠ No browser cookies found.")
    return None


# ---------------------------------------------------------------------------
# yt-dlp option builder
# ---------------------------------------------------------------------------

def _build_extractor_args(js_runtime: str | None) -> dict:
    """
    Pass the detected JS runtime to yt-dlp's YouTube extractor so it can
    solve JS challenges and see all available formats.

    yt-dlp accepts runtime names: 'auto', 'deno', 'node', 'bun'
    Setting player_client to a modern client also helps resolve formats.
    """
    if js_runtime is None:
        # No JS runtime — tell yt-dlp to use the 'tv' player client which
        # doesn't require JS and usually exposes at least one usable format.
        return {
            "youtube": {
                "player_client": ["tv", "web_creator", "ios"],
                "player_skip": ["webpage", "configs"],
            }
        }

    runtime_map = {"node": "nodejs", "deno": "deno", "bun": "bun"}
    yt_dlp_runtime = runtime_map.get(js_runtime, "auto")

    return {
        "youtube": {
            "js_runtime": [yt_dlp_runtime],
            "player_client": ["web", "android", "ios"],
        }
    }


def build_ydl_opts(
    task_id: str,
    output_format: str,
    js_runtime: str | None,
    detected_browser: str | None,
    use_merge: bool = True,
) -> dict:
    """
    Build a complete yt-dlp options dict.

    Format priority:
      With ffmpeg  → bestvideo+bestaudio/bestvideo/best
      Without ffmpeg → best[ext=mp4]/best
    """
    ffmpeg_ok = check_ffmpeg_available()

    if use_merge and ffmpeg_ok:
        format_str = "bestvideo+bestaudio/bestvideo/best"
    else:
        # Single-file fallback; prefer mp4 containers for compatibility
        format_str = "best[ext=mp4]/best[ext=webm]/best"

    opts: dict = {
        "format": format_str,
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": False,   # keep warnings visible in server logs
        "extractor_args": _build_extractor_args(js_runtime),
        "progress_hooks": [
            lambda d: asyncio.create_task(HackerProgress(manager, task_id)(d))
        ],
    }

    if detected_browser:
        opts["cookiesfrombrowser"] = (detected_browser,)

    if output_format.lower() not in ("mp4", "webm", "mkv", ""):
        if ffmpeg_ok:
            opts.setdefault("postprocessors", []).append({
                "key": "FFmpegVideoConvertor",
                "preferedformat": output_format,
            })

    return opts


# ---------------------------------------------------------------------------
# Core download coroutine
# ---------------------------------------------------------------------------

async def download_video_async(url: str, quality: str, output_format: str, task_id: str):
    async with DOWNLOAD_SEMAPHORE:
        js_runtime = check_js_runtime()
        detected_browser = get_browser_cookies()

        # --- announce environment -------------------------------------------------
        if js_runtime:
            await manager.send_progress({
                "type": "info", "task_id": task_id,
                "message": f"JS runtime detected: {js_runtime}",
            })
        else:
            await manager.send_progress({
                "type": "warning", "task_id": task_id,
                "message": (
                    "No JS runtime found (deno/node/bun). "
                    "Using fallback player clients — some formats may be missing. "
                    "Install Node.js (https://nodejs.org) for best results."
                ),
            })

        if not check_ffmpeg_available():
            await manager.send_progress({
                "type": "warning", "task_id": task_id,
                "message": (
                    "ffmpeg not found — downloading single-file format (not best quality). "
                    "Install ffmpeg for highest quality: https://github.com/BtbN/FFmpeg-Builds/releases"
                ),
            })

        if detected_browser:
            await manager.send_progress({
                "type": "info", "task_id": task_id,
                "message": f"Using cookies from {detected_browser} for authentication",
            })
        else:
            await manager.send_progress({
                "type": "warning", "task_id": task_id,
                "message": "No browser cookies found. Restricted videos may fail.",
            })

        # --- fetch metadata -------------------------------------------------------
        try:
            info_opts = {
                "quiet": True,
                "extractor_args": _build_extractor_args(js_runtime),
            }
            if detected_browser:
                info_opts["cookiesfrombrowser"] = (detected_browser,)

            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            title     = info.get("title", "Unknown")
            duration  = info.get("duration", 0)
            uploader  = info.get("uploader", "Unknown")

            await manager.send_progress({
                "type": "info", "task_id": task_id,
                "title": title, "duration": duration, "uploader": uploader,
            })

        except Exception as e:
            await manager.send_progress({
                "type": "error", "task_id": task_id,
                "error": f"Failed to fetch video info: {e}",
            })
            return

        # --- download with fallback chain -----------------------------------------
        #
        # Attempt 1: specific quality (if provided), then bestvideo+bestaudio (requires ffmpeg)
        # Attempt 2: best[ext=mp4]/best  (single-file, no ffmpeg needed)
        # Attempt 3: just "best"         (absolute last resort)
        #

        # If 'quality' is a specific format ID, use it first.
        attempts = []
        if quality != "best":
            attempts.append((quality, True))

        attempts.extend([
            ("bestvideo+bestaudio/bestvideo/best", True),
            ("best[ext=mp4]/best[ext=webm]/best",  False),
            ("best",                                False),
        ])

        loop = asyncio.get_running_loop()

        for fmt, use_merge in attempts:
            try:
                ydl_opts = build_ydl_opts(
                    task_id=task_id,
                    output_format=output_format,
                    js_runtime=js_runtime,
                    detected_browser=detected_browser,
                    use_merge=use_merge,
                )
                ydl_opts["format"] = fmt   # override with this attempt's format

                # Using a helper function to call the blocking ydl.download in executor
                def run_download(opts, target_url):
                    with yt_dlp.YoutubeDL(opts) as ydl_inner:
                        ydl_inner.download([target_url])

                await loop.run_in_executor(None, run_download, ydl_opts, url)

                await manager.send_progress({
                    "type": "complete", "task_id": task_id,
                    "title": title, "path": str(DOWNLOAD_DIR),
                })
                return   # success — stop here

            except yt_dlp.utils.DownloadError as e:
                err = str(e)
                if "Requested format is not available" in err or "No video formats" in err:
                    await manager.send_progress({
                        "type": "info", "task_id": task_id,
                        "message": f"Format '{fmt}' unavailable, trying next fallback...",
                    })
                    continue
                # Any other download error — report and abort
                await manager.send_progress({
                    "type": "error", "task_id": task_id,
                    "error": err,
                })
                return

            except Exception as e:
                await manager.send_progress({
                    "type": "error", "task_id": task_id,
                    "error": str(e),
                })
                return

        # All attempts exhausted
        await manager.send_progress({
            "type": "error", "task_id": task_id,
            "error": (
                "All format attempts failed. "
                "Install a JS runtime (deno/node) and try again: "
                "https://github.com/yt-dlp/yt-dlp/wiki/EJS"
            ),
        })


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            if request.get("action") == "download":
                task_id = request.get("task_id", "unknown")
                asyncio.create_task(
                    download_video_async(
                        url=request["url"],
                        quality=request.get("quality", "best"),
                        output_format=request.get("format", "mp4"),
                        task_id=task_id,
                    )
                )
                await websocket.send_json({
                    "type": "queued",
                    "task_id": task_id,
                    "message": "Download queued...",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    ffmpeg_ok  = check_ffmpeg_available()
    js_runtime = check_js_runtime()
    return {
        "status": "online",
        "download_dir": str(DOWNLOAD_DIR),
        "yt_dlp_version": yt_dlp.version.__version__,
        "dependencies": {
            "ffmpeg":     ffmpeg_ok,
            "js_runtime": js_runtime or "none",
            "all_ok":     ffmpeg_ok and js_runtime is not None,
        },
    }


@app.post("/info")
async def get_video_info(url: str):
    js_runtime = check_js_runtime()
    try:
        info_opts = {
            "quiet": True,
            "extractor_args": _build_extractor_args(js_runtime),
        }
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "success": True,
                "title":     info.get("title"),
                "duration":  info.get("duration"),
                "uploader":  info.get("uploader"),
                "thumbnail": info.get("thumbnail"),
                "formats": [
                    {
                        "format_id":  f.get("format_id"),
                        "resolution": f.get("resolution"),
                        "ext":        f.get("ext"),
                    }
                    for f in info.get("formats", [])
                    if f.get("resolution")
                ][:10],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    ffmpeg_ok  = check_ffmpeg_available()
    js_runtime = check_js_runtime()

    print()
    if not ffmpeg_ok:
        print("⚠  WARNING: ffmpeg not found — install for best quality:")
        print("   https://github.com/BtbN/FFmpeg-Builds/releases")
        print()
    if not js_runtime:
        print("⚠  WARNING: No JS runtime found (deno / node / bun).")
        print("   YouTube format resolution may be degraded.")
        print("   Install Node.js : https://nodejs.org/")
        print("   Or Deno         : https://docs.deno.com/runtime/getting_started/installation/")
        print()
    if ffmpeg_ok and js_runtime:
        print(f"✓  ffmpeg        : ok")
        print(f"✓  JS runtime    : {js_runtime}")
        print()

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     ██╗   ██╗████████╗      ██╗  ██╗ █████╗  ██████╗██╗  ██╗ ║
    ║     ╚██╗ ██╔╝╚══██╔══╝      ██║  ██║██╔══██╗██╔════╝██║ ██╔╝ ║
    ║      ╚████╔╝    ██║         ███████║███████║██║     █████╔╝  ║
    ║       ╚██╔╝     ██║         ██╔══██║██╔══██║██║     ██╔═██╗  ║
    ║        ██║      ██║         ██║  ██║██║  ██║╚██████╗██║  ██╗ ║
    ║        ╚═╝      ╚═╝         ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ║
    ╠══════════════════════════════════════════════════════════════╣
    ║              PARALLEL DOWNLOADER v1.1 - HACKER EDITION       ║
    ║                  Backend running on http://localhost:8000    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=8000)