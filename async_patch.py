import re

with open("backend/main.py", "r") as f:
    content = f.read()

if "import queue" not in content:
    content = content.replace("import json", "import json\nimport threading\nimport queue")

old_func_pattern = re.compile(r"def get_video_duration\(file_path: Path\) -> float:.*?return 0\.0", re.DOTALL)

new_func = """scan_queue = queue.Queue()

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

content = old_func_pattern.sub(new_func, content)

with open("backend/main.py", "w") as f:
    f.write(content)
