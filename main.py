import os
import sys
import threading
import time
import webbrowser
import subprocess
import urllib.request
import json
from functools import lru_cache
from flask import Flask, request, render_template, jsonify, redirect
from ytmusicapi import YTMusic
from waitress import serve

# --- Configuration ---
YTDLP_FILENAME = "yt-dlp.exe"
YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
INACTIVITY_TIMEOUT = 600  # 10 minutes
PLAYLISTS_FILE = "playlists.json"

# --- Global Timer ---
last_activity_time = time.time()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

template_folder = resource_path('templates')
app = Flask(__name__, template_folder=template_folder)
yt = YTMusic()

@app.before_request
def update_activity_time():
    global last_activity_time
    last_activity_time = time.time()

def get_playlists_file_path():
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, PLAYLISTS_FILE)
    except:
        return PLAYLISTS_FILE

def load_playlists():
    file_path = get_playlists_file_path()
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading playlists: {e}")
    return {}

def save_playlists(playlists):
    file_path = get_playlists_file_path()
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving playlists: {e}")
        return False

# --- Helper: Get Full HD Thumbnail ---
def get_hd_thumbnail(video_id, thumbnails_list):
    # Priority 1: Force MaxResDefault (Full HD)
    # This is usually 1280x720 or 1920x1080
    return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

# ===== Routes =====

@app.route("/")
def home():
    return render_template("index.html")

@lru_cache(maxsize=50)
def cached_search(query):
    return yt.search(query, filter="songs")[:25]

@app.route("/api/search")
def api_search():
    query = request.args.get("query", "")
    results = []
    if query:
        try:
            songs = cached_search(query)
            for s in songs:
                if s.get("videoId") and s.get("title"):
                    # Use Full HD Thumbnail logic
                    thumbnail_url = get_hd_thumbnail(s["videoId"], s.get("thumbnails"))
                    
                    results.append({
                        "title": s["title"],
                        "artist": s["artists"][0]["name"] if s.get("artists") else "Unknown",
                        "videoId": s["videoId"],
                        "thumbnail": thumbnail_url
                    })
                if len(results) >= 15:
                    break
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify(results)

# --- RECOMMENDATIONS (UPDATED) ---
@app.route("/api/recommendations")
def api_recommendations():
    video_id = request.args.get("videoId")
    if not video_id:
        return jsonify([])
    
    try:
        # Fetch 20 items for the autoplay queue
        watch_playlist = yt.get_watch_playlist(videoId=video_id, limit=20)
        tracks = watch_playlist.get('tracks', [])
        results = []
        
        for s in tracks:
            if s.get("videoId") and s.get("videoId") != video_id:
                # Use Full HD Thumbnail logic
                thumbnail_url = get_hd_thumbnail(s["videoId"], s.get("thumbnails"))
                
                results.append({
                    "title": s["title"],
                    "artist": s["artists"][0]["name"] if s.get("artists") else "Unknown",
                    "videoId": s["videoId"],
                    "thumbnail": thumbnail_url
                })
        return jsonify(results)
    except Exception as e:
        print(f"Recommendation Error: {e}")
        return jsonify([])

@app.route("/stream/<videoId>")
def stream(videoId):
    url = f"https://www.youtube.com/watch?v={videoId}"
    
    ytdlp_path = os.path.join(get_app_path(), YTDLP_FILENAME)
    if not os.path.exists(ytdlp_path):
        if os.path.exists(YTDLP_FILENAME): ytdlp_path = YTDLP_FILENAME
        else: return "Error: yt-dlp.exe is missing.", 500

    try:
        cmd = [ytdlp_path, "-f", "bestaudio[ext=m4a]/bestaudio", "-g", "--no-playlist", "--no-warnings", "--quiet", url]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        audio_url = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0).strip()
        
        return redirect(audio_url)
    except Exception as e:
        return "Error starting stream", 500

# ===== Playlist Routes =====

@app.route("/api/playlists", methods=["GET"])
def get_playlists(): return jsonify(load_playlists())

@app.route("/api/playlists", methods=["POST"])
def create_playlist():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name: return jsonify({"error": "Name required"}), 400
    playlists = load_playlists()
    if name in playlists: return jsonify({"error": "Exists"}), 400
    playlists[name] = {"songs": [], "modified": time.time()}
    save_playlists(playlists)
    return jsonify({"success": True, "playlists": playlists})

@app.route("/api/playlists/<name>", methods=["DELETE"])
def delete_playlist(name):
    playlists = load_playlists()
    if name in playlists:
        del playlists[name]
        save_playlists(playlists)
    return jsonify({"success": True, "playlists": playlists})

@app.route("/api/playlists/<name>/songs", methods=["POST"])
def add_song(name):
    song = request.get_json().get("song")
    playlists = load_playlists()
    if name in playlists:
        if not any(s['videoId'] == song['videoId'] for s in playlists[name]['songs']):
            playlists[name]['songs'].append(song)
            save_playlists(playlists)
    return jsonify({"success": True, "playlist": playlists[name]})

@app.route("/api/playlists/<name>/songs/<videoId>", methods=["DELETE"])
def remove_song(name, videoId):
    playlists = load_playlists()
    if name in playlists:
        playlists[name]['songs'] = [s for s in playlists[name]['songs'] if s['videoId'] != videoId]
        save_playlists(playlists)
    return jsonify({"success": True, "playlist": playlists[name]})

@app.route("/api/playlists/<old>", methods=["PUT"])
def rename_playlist(old):
    new = request.get_json().get("name", "").strip()
    playlists = load_playlists()
    if old in playlists and new and new not in playlists:
        playlists[new] = playlists.pop(old)
        save_playlists(playlists)
    return jsonify({"success": True, "playlists": playlists})

# ===== Startup =====

def ensure_yt_dlp():
    target_path = os.path.join(get_app_path(), YTDLP_FILENAME)
    if not os.path.exists(target_path):
        try: urllib.request.urlretrieve(YTDLP_DOWNLOAD_URL, target_path)
        except: pass
    
    marker = "last_update_check.txt"
    if not os.path.exists(marker) or (time.time() - os.path.getmtime(marker)) > 86400:
        try:
            subprocess.run([target_path, "-U"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            with open(marker, 'w') as f: f.write(str(time.time()))
        except: pass

def start_server():
    serve(app, host='127.0.0.1', port=5000, threads=6)

def check_inactivity():
    while True:
        time.sleep(60)
        if time.time() - last_activity_time > INACTIVITY_TIMEOUT: os._exit(0)

if __name__ == "__main__":
    ensure_yt_dlp()
    threading.Thread(target=start_server, daemon=True).start()
    threading.Thread(target=check_inactivity, daemon=True).start()
    
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')
    
    try: 
        while True: 
            time.sleep(1)
    except KeyboardInterrupt:
        pass