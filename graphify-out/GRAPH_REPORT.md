# Graph Report - .  (2026-04-15)

## Corpus Check
- 7 files · ~7,758 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 40 nodes · 60 edges · 11 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `download_video_async()` - 8 edges
2. `build_ydl_opts()` - 6 edges
3. `addLog()` - 6 edges
4. `check_js_runtime()` - 5 edges
5. `ConnectionManager` - 5 edges
6. `_build_extractor_args()` - 5 edges
7. `check_ffmpeg_available()` - 4 edges
8. `HackerProgress` - 4 edges
9. `websocket_endpoint()` - 4 edges
10. `startDownload()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `health_check()` --calls--> `check_ffmpeg_available()`  [EXTRACTED]
  backend.py → backend.py  _Bridges community 2 → community 3_
- `build_ydl_opts()` --calls--> `HackerProgress`  [EXTRACTED]
  backend.py → backend.py  _Bridges community 5 → community 2_
- `download_video_async()` --calls--> `get_browser_cookies()`  [EXTRACTED]
  backend.py → backend.py  _Bridges community 6 → community 2_
- `websocket_endpoint()` --calls--> `download_video_async()`  [EXTRACTED]
  backend.py → backend.py  _Bridges community 2 → community 1_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.38
Nodes (7): addLog(), generateTaskId(), handleBuiltInCommand(), handleCommand(), handleKeyDown(), handleWebSocketMessage(), startDownload()

### Community 1 - "Community 1"
Cohesion: 0.38
Nodes (2): ConnectionManager, websocket_endpoint()

### Community 2 - "Community 2"
Cohesion: 0.47
Nodes (6): _build_extractor_args(), build_ydl_opts(), check_ffmpeg_available(), download_video_async(), Pass the detected JS runtime to yt-dlp's YouTube extractor so it can     solve, Build a complete yt-dlp options dict.      Format priority:       With ffmpeg

### Community 3 - "Community 3"
Cohesion: 0.6
Nodes (4): check_js_runtime(), get_video_info(), health_check(), Return the name of the first available JS runtime yt-dlp understands,     or No

### Community 4 - "Community 4"
Cohesion: 1.0
Nodes (2): DownloadRequest, BaseModel

### Community 5 - "Community 5"
Cohesion: 1.0
Nodes (1): HackerProgress

### Community 6 - "Community 6"
Cohesion: 1.0
Nodes (2): get_browser_cookies(), Try to find a browser that has YouTube cookies and return its name,     or None

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (0): 

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (0): 

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (0): 

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **4 isolated node(s):** `Return the name of the first available JS runtime yt-dlp understands,     or No`, `Try to find a browser that has YouTube cookies and return its name,     or None`, `Pass the detected JS runtime to yt-dlp's YouTube extractor so it can     solve`, `Build a complete yt-dlp options dict.      Format priority:       With ffmpeg`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 4`** (2 nodes): `DownloadRequest`, `BaseModel`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 5`** (2 nodes): `HackerProgress`, `.__init__()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 6`** (2 nodes): `get_browser_cookies()`, `Try to find a browser that has YouTube cookies and return its name,     or None`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 7`** (2 nodes): `HackerDownloader()`, `HackerDownloader.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (2 nodes): `App.vue`, `main.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (1 nodes): `HelloWorld.vue`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `download_video_async()` connect `Community 2` to `Community 1`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `ConnectionManager` connect `Community 1` to `Community 3`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `HackerProgress` connect `Community 5` to `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **What connects `Return the name of the first available JS runtime yt-dlp understands,     or No`, `Try to find a browser that has YouTube cookies and return its name,     or None`, `Pass the detected JS runtime to yt-dlp's YouTube extractor so it can     solve` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._