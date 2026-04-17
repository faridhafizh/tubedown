# 🖥️ Tubedown - Parallel YouTube Downloader

> ⚡ A sleek **hacker-themed terminal UI** for downloading YouTube videos at maximum speed with parallel processing.

![Version](https://img.shields.io/badge/version-1.0.0-00ff41?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)
![Vue](https://img.shields.io/badge/Vue.js-3.x-42b883?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## 📸 Preview

> Hacker-style terminal interface with real-time download progress (Matrix vibes 🟢)

---

## 📦 Project Structure

```
project/
├── backend.py                  # FastAPI backend
├── vue-hacker-downloader.vue   # Vue 3 component
├── HackerDownloader.jsx        # React component
├── HackerDownloader.css        # React styles
└── README.md
```

---

## ⚡ Features

- 🟢 Real-time progress via WebSocket  
- 🔄 Parallel downloads (max 3 concurrent)  
- 🎨 Hacker terminal UI (Matrix-green aesthetic)  
- 📊 Live progress bars (speed, ETA, status)  
- 🛡️ Robust error handling & auto-reconnect  
- 📁 Auto-save to `~/Downloads/YT-Hacker`  

---

## 🚀 Quick Start

### 1️⃣ Install Backend Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install fastapi uvicorn yt-dlp websockets browser-cookie3
```

> ⚠️ **Requirement:** Install FFmpeg
Download: https://ffmpeg.org

---

### 🔐 YouTube Authentication (Bot Protection)

YouTube now requires authentication for some videos. The backend **automatically detects and uses your browser cookies** for authentication.

**Supported Browsers:**
- Chrome, Edge, Firefox, Brave, Opera, Opera GX, Vivaldi

**How it works:**
- The backend automatically tries to extract cookies from your installed browsers
- No manual setup required - just make sure you're logged into YouTube in one of your browsers
- If no browser cookies are found, you'll see a warning message

**Alternative: Manual Cookie Export**

If automatic detection fails, you can manually export cookies:

```bash
# Using yt-dlp's cookie export feature
yt-dlp --cookies-from-browser chrome  # Extract from Chrome
# OR
yt-dlp --cookies cookies.txt "URL"   # Use a cookie file
```

To use a cookie file, add this to `backend.py` in the `ydl_opts`:
```python
"cookies": "path/to/cookies.txt"
```

---

### 2️⃣ Run Backend

```bash
python backend.py
```

Backend runs at:  
👉 http://localhost:8000

---

### 3️⃣ Run Frontend

#### Option A — Vue 3 (Vite)

```bash
npm create vite@latest yt-hacker-vue -- --template vue
cd yt-hacker-vue
npm install
```

- Copy `vue-hacker-downloader.vue` → `src/components/`
- Import & use it inside `App.vue`

```bash
npm run dev
```

---

#### Option B — React (Vite)

```bash
npm create vite@latest yt-hacker-react -- --template react
cd yt-hacker-react
npm install
```

- Copy:
  - `HackerDownloader.jsx`
  - `HackerDownloader.css`
- Import component in your app

```bash
npm run dev
```

---

## 🎮 Terminal Commands

| Command              | Description                          |
|---------------------|--------------------------------------|
| `[YouTube URL]`     | Start download                       |
| `/help`, `help`     | Show help panel                      |
| `/clear`, `clear`   | Clear terminal                       |
| `/status`           | Check backend & download status      |
| `/exit`, `quit`     | Exit (refresh page)                  |
| `Ctrl + C`          | Clear input                          |
| `ESC`               | Close help panel                     |

---

## 🔧 Configuration

### Backend (`backend.py`)

```python
from pathlib import Path

DOWNLOAD_DIR = Path.home() / "Downloads" / "YT-Hacker"
```

---

### Frontend

```javascript
// Vue
const maxParallel = ref(3);

// React
const maxParallel = 3;
```

---

## 🧪 Troubleshooting

| Issue                | Solution |
|---------------------|----------|
| Backend offline      | Ensure `python backend.py` is running on port 8000 |
| yt-dlp not found     | `pip install yt-dlp` |
| ffmpeg not found     | Install FFmpeg |
| CORS error           | Ensure frontend connects to `http://localhost:8000` |
| **"Sign in to confirm you're not a bot"** | Make sure you're logged into YouTube in your browser. The app will automatically use your browser cookies. |
| **No browser cookies detected** | Install Chrome/Edge/Firefox and log into YouTube, or manually export cookies (see Authentication section) |
| **browser_cookie3 import error** | Run `pip install browser-cookie3` |

---

## 🎯 Usage

1. Start backend  
2. Run frontend (Vue or React)  
3. Open browser (`http://localhost:5173`)  
4. Paste a YouTube URL  
5. 🚀 Downloads start in parallel!

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

## 💡 Credits

Made with ⚡ by **Hacker Terminal Studio**
