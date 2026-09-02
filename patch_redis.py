import re

with open("backend/main.py", "r") as f:
    content = f.read()

# Add redis import
if "import redis" not in content:
    content = content.replace("import threading", "import threading\nimport redis")

# Add redis client instantiation and json migration
redis_setup = """
# Initialize Redis
try:
    r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    
    # Migrate old JSON data if present
    if PROGRESS_FILE.exists():
        try:
            data = json.loads(PROGRESS_FILE.read_text())
            for k, v in data.items():
                if not r.exists(f"progress:{k}"):
                    r.set(f"progress:{k}", v)
            # rename to prevent re-migration
            PROGRESS_FILE.rename(PROGRESS_FILE.with_suffix('.json.bak'))
        except:
            pass
            
    if DURATIONS_FILE.exists():
        try:
            data = json.loads(DURATIONS_FILE.read_text())
            for k, v in data.items():
                if not r.exists(f"duration:{k}"):
                    r.set(f"duration:{k}", v)
            DURATIONS_FILE.rename(DURATIONS_FILE.with_suffix('.json.bak'))
        except:
            pass
except Exception as e:
    print("Redis connection failed:", e)

"""

# Insert redis setup before progress endpoints
content = content.replace('class ProgressUpdate', redis_setup + 'class ProgressUpdate')

# Replace progress endpoints
old_progress_endpoints = """@app.post("/api/progress")
def save_progress(progress: ProgressUpdate):
    data = {}
    if PROGRESS_FILE.exists():
        try:
            data = json.loads(PROGRESS_FILE.read_text())
        except:
            pass
    data[progress.url] = progress.time
    PROGRESS_FILE.write_text(json.dumps(data))
    return {"status": "ok"}

@app.get("/api/progress")
def get_progress(url: str):
    if PROGRESS_FILE.exists():
        try:
            data = json.loads(PROGRESS_FILE.read_text())
            return {"time": data.get(url, 0)}
        except:
            pass
    return {"time": 0}"""

new_progress_endpoints = """@app.post("/api/progress")
def save_progress(progress: ProgressUpdate):
    try:
        r.set(f"progress:{progress.url}", progress.time)
    except:
        pass
    return {"status": "ok"}

@app.get("/api/progress")
def get_progress_api(url: str):
    try:
        val = r.get(f"progress:{url}")
        return {"time": float(val) if val else 0}
    except:
        return {"time": 0}

def get_progress_val(url: str) -> float:
    try:
        val = r.get(f"progress:{url}")
        return float(val) if val else 0.0
    except:
        return 0.0"""

content = content.replace(old_progress_endpoints, new_progress_endpoints)

# Replace the async worker
old_worker = """scan_queue = queue.Queue()

def duration_worker():
    while True:
        path_str = scan_queue.get()
        if path_str is None:
            break
            
        durations = {}
        if DURATIONS_FILE.exists():
            try: durations = json.loads(DURATIONS_FILE.read_text())
            except: pass
            
        if path_str in durations:
            scan_queue.task_done()
            continue
            
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", path_str
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            duration = float(result.stdout)
            
            if DURATIONS_FILE.exists():
                try: durations = json.loads(DURATIONS_FILE.read_text())
                except: pass
                
            durations[path_str] = duration
            DURATIONS_FILE.write_text(json.dumps(durations))
        except Exception:
            pass
            
        scan_queue.task_done()

threading.Thread(target=duration_worker, daemon=True).start()

def get_video_duration(file_path: Path) -> float:
    path_str = file_path.as_posix()
    
    # Try cache first
    durations = {}
    if DURATIONS_FILE.exists():
        try:
            durations = json.loads(DURATIONS_FILE.read_text())
            if path_str in durations:
                return durations[path_str]
        except:
            pass
            
    # Not in cache, queue it for background processing
    scan_queue.put(path_str)
    return 0.0"""

new_worker = """scan_queue = queue.Queue()

def duration_worker():
    while True:
        path_str = scan_queue.get()
        if path_str is None:
            break
            
        try:
            if r.exists(f"duration:{path_str}"):
                scan_queue.task_done()
                continue
                
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", path_str
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            
            duration = float(result.stdout)
            r.set(f"duration:{path_str}", duration)
        except Exception:
            pass
            
        scan_queue.task_done()

threading.Thread(target=duration_worker, daemon=True).start()

def get_video_duration(file_path: Path) -> float:
    path_str = file_path.as_posix()
    try:
        val = r.get(f"duration:{path_str}")
        if val is not None:
            return float(val)
    except:
        pass
        
    scan_queue.put(path_str)
    return 0.0"""

content = content.replace(old_worker, new_worker)


# Now we have to fix get_folder_progress, list_channels, list_playlists, parse_video_files
# Because they still use PROGRESS_FILE manually!

# Fix get_folder_progress
old_get_folder = """    progress_data = {}
    if PROGRESS_FILE.exists():
        try:
            progress_data = json.loads(PROGRESS_FILE.read_text())
        except:
            pass
            
    for entry in folder_path.rglob("*"):
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
            # Build relative path for url
            rel_path = entry.relative_to(root)
            vid_url = f"/api/stream?path={urllib.parse.quote(str(rel_path).replace('\\\\', '/'))}"
            
            duration = get_video_duration(entry)
            watched = progress_data.get(vid_url, 0.0)"""

new_get_folder = """    for entry in folder_path.rglob("*"):
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
            # Build relative path for url
            rel_path = entry.relative_to(root)
            vid_url = f"/api/stream?path={urllib.parse.quote(rel_path.as_posix())}"
            
            duration = get_video_duration(entry)
            watched = get_progress_val(vid_url)"""

content = content.replace(old_get_folder, new_get_folder)


# Fix list_channels loose videos
old_list_channels = """                    progress_data = {}
                    if PROGRESS_FILE.exists():
                        try:
                            progress_data = json.loads(PROGRESS_FILE.read_text())
                        except:
                            pass
                    watch = progress_data.get(vid_url, 0.0)"""

new_list_channels = """                    watch = get_progress_val(vid_url)"""

content = content.replace(old_list_channels, new_list_channels)

# Fix list_playlists root videos
old_list_playlists_root = """                        progress_data = {}
                        if PROGRESS_FILE.exists():
                            try: progress_data = json.loads(PROGRESS_FILE.read_text())
                            except: pass
                        watch = progress_data.get(vid_url, 0.0)"""

new_list_playlists_root = """                        watch = get_progress_val(vid_url)"""
content = content.replace(old_list_playlists_root, new_list_playlists_root)

# Fix list_playlists loose videos
old_list_playlists_loose = """                    progress_data = {}
                    if PROGRESS_FILE.exists():
                        try: progress_data = json.loads(PROGRESS_FILE.read_text())
                        except: pass
                    watch = progress_data.get(vid_url, 0.0)"""

content = content.replace(old_list_playlists_loose, new_list_playlists_root)

# Fix parse_video_files
old_parse = """    # Read progress to inject watched time directly
    progress_data = {}
    if PROGRESS_FILE.exists():
        try:
            progress_data = json.loads(PROGRESS_FILE.read_text())
        except:
            pass
            
    for entry in files:"""

new_parse = """    for entry in files:"""
content = content.replace(old_parse, new_parse)

old_parse_2 = """            duration = get_video_duration(entry)
            watched = progress_data.get(vid_url, 0)"""

new_parse_2 = """            duration = get_video_duration(entry)
            watched = get_progress_val(vid_url)"""

content = content.replace(old_parse_2, new_parse_2)

with open("backend/main.py", "w") as f:
    f.write(content)
