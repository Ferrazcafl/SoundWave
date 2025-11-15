# SoundWave – Desktop Web Music Player (.EXE)

SoundWave is a local web music player built with Flask and Waitress that you can run as a Windows executable. It provides a modern UI (Tailwind via CDN), fast search powered by `ytmusicapi`, streaming via `yt-dlp`, and simple local playlists.

## Overview
- Serves a local site at `http://127.0.0.1:5000`
- Opens your default browser automatically
- Streams audio directly from YouTube using `yt-dlp`
- Stores playlists in a local `playlists.json`

## Key Features
- Fast song search with caching (`cached_search` in `main.py` at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:86)
- Recommendations and autoplay queue (`/api/recommendations` at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:115)
- Stream best audio (`/stream/<videoId>` at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:143)
- Playlists: create, rename, delete, add/remove songs (routes at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:167–214)
- Production-grade serving using Waitress
- Auto-download/update of `yt-dlp.exe` on first run

## How It Works
- Backend: Flask app served by Waitress (`serve(...)` at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:231–233)
- Search: `ytmusicapi` for song search (`/api/search` at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:90–113)
- Streaming: Fetches a direct audio URL using `yt-dlp` and redirects the browser audio element (`/stream/<videoId>`)
- UI: Single-page HTML in `templates/index.html` with Tailwind CDN and rich player interactions
- Playlists: JSON file written next to the executable (`playlists.json`) via helpers at c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:54–73

## Requirements
- Windows (tested as a packaged `.exe`)
- Python 3.9+ (for running from source)
- Internet access (for search, recommendations, streaming, and first-run `yt-dlp.exe` download)
- Dependencies (see `requirements.txt`):
  - Flask
  - ytmusicapi
  - fuzzywuzzy
  - python-Levenshtein
  - waitress

## Run From Source
1. Open a terminal in `c:\Users\shiva\OneDrive\Desktop\SoundWave`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python main.py`
4. Your browser opens to `http://127.0.0.1:5000`

Notes:
- On first run, the app downloads `yt-dlp.exe` automatically and checks for updates daily (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:218–230).
- Templates are loaded via a PyInstaller-friendly `resource_path(...)` helper.

## Build the Windows .EXE
Packaging is optional; running from source works fine. To create a single-file executable with PyInstaller:

1. Install PyInstaller: `pip install pyinstaller`
2. From the project folder, run:
   - `pyinstaller --noconsole --onefile --add-data "templates;templates" --name SoundWave main.py`
3. The output `.exe` appears in the `dist` folder. Place `yt-dlp.exe` next to the `.exe` for immediate streaming, or let the app download it on first run.

Tips:
- `--add-data "templates;templates"` ensures the HTML is bundled. The app’s `resource_path` uses `sys._MEIPASS` when frozen.
- If antivirus or SmartScreen warns on first run, allow the app; it only serves on `127.0.0.1`.

## Using the App
- Search: Type at least 2 characters to search songs; click a result to play.
- Queue: Clicking results appends to the queue; use next/previous, shuffle, repeat.
- Autoplay: Toggle the infinity icon to automatically add similar songs at the end of your queue.
- Playlists: Create/rename/delete playlists, add/remove songs directly from search or playlist views. Data persists to `playlists.json` next to the app.

## Files
- `templates/index.html` – UI and player interactions
- `main.py` – Flask routes, streaming, playlist persistence, `yt-dlp` handling
- `requirements.txt` – Python dependencies

## API Endpoints
- `GET /api/search?query=...` – Top song results (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:90–113)
- `GET /api/recommendations?videoId=...` – Similar songs for autoplay (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:115–142)
- `GET /stream/<videoId>` – Redirects to a direct audio URL (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:143–163)
- `GET /api/playlists` – List playlists (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:167–168)
- `POST /api/playlists` – Create playlist (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:170–179)
- `DELETE /api/playlists/<name>` – Delete playlist (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:181–187)
- `POST /api/playlists/<name>/songs` – Add song (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:189–197)
- `DELETE /api/playlists/<name>/songs/<videoId>` – Remove song (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:199–205)
- `PUT /api/playlists/<old>` – Rename playlist (c:\Users\shiva\OneDrive\Desktop\SoundWave\main.py:207–214)

## Troubleshooting
- Audio doesn’t play: Ensure Internet access and that `yt-dlp.exe` exists next to the app or allow the first-run download.
- Port in use: The app binds to `127.0.0.1:5000`; close other services using that port.
- Templates not found: When packaging, ensure `--add-data "templates;templates"` is provided.
- Firewall/AV prompts: Allow local network access; the app serves only to your machine.

## License and Content
This project streams from YouTube. Please follow YouTube’s Terms of Service in your region.