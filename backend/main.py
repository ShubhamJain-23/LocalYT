import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.parse
import json
import threading
import redis
import queue
import subprocess


app = FastAPI(title="LocalYT API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_DIR = Path("/app/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = DB_DIR / "progress.json"

DURATIONS_FILE = DB_DIR / "durations.json"
scan_queue = queue.Queue()

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
    return 0.0




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

class ProgressUpdate(BaseModel):
    url: str
    time: float

@app.post("/api/progress")
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
        return 0.0

DATA_DIRS_ENV = os.environ.get("DATA_DIRS", "./data")
ROOT_PATHS = [Path(d.strip()).resolve() for d in DATA_DIRS_ENV.split(",") if d.strip()]


def get_folder_progress(folder_path: Path, channel_name: str, root: Path):
    total_duration = 0.0
    total_watched = 0.0
    
    progress_data = {}
    if PROGRESS_FILE.exists():
        try:
            progress_data = json.loads(PROGRESS_FILE.read_text())
        except:
            pass
            
    for entry in folder_path.rglob("*"):
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
            # Build relative path for url
            rel_path = entry.relative_to(root)
            vid_url = f"/api/stream?path={urllib.parse.quote(rel_path.as_posix())}"
            
            duration = get_video_duration(entry)
            watched = progress_data.get(vid_url, 0.0)
            
            total_duration += duration
            total_watched += min(watched, duration) # Cap watched at duration
            
    return total_duration, total_watched

def get_safe_path(sub_path: str) -> Path:
    decoded_path = urllib.parse.unquote(sub_path)
    for root in ROOT_PATHS:
        target = (root / decoded_path).resolve()
        if str(target).startswith(str(root)) and target.exists():
            return target
    raise HTTPException(status_code=404, detail="File not found or access denied")

VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.mkv', '.mov', '.avi'}
SUBTITLE_EXTENSIONS = {'.vtt', '.srt'}
NOTE_EXTENSIONS = {'.pdf', '.md', '.txt', '.docx', '.doc', '.rst', '.csv', '.rtf'}

# ─── Note helpers ────────────────────────────────────────────────────────────

def _get_notes_folder(channel: str, playlist: str, root: Path) -> Path | None:
    if channel == "Uncategorized" and playlist == "Root Videos":
        return root
    if playlist == "Loose Videos":
        p = root / channel
        return p if p.exists() and p.is_dir() else None
    p = root / channel / playlist
    return p if p.exists() and p.is_dir() else None


@app.get("/api/notes/video")
def get_video_notes(channel: str, playlist: str, filename: str):
    """Return notes that share the same stem as the given video filename."""
    stem = Path(filename).stem
    notes = []
    for root in ROOT_PATHS:
        folder = _get_notes_folder(channel, playlist, root)
        if not folder:
            continue
        for search_dir in [folder, folder / "notes"]:
            if not search_dir.exists():
                continue
            for f in sorted(search_dir.iterdir()):
                if f.is_file() and f.stem == stem and f.suffix.lower() in NOTE_EXTENSIONS:
                    notes.append({
                        "title": f.name,
                        "path": f.relative_to(root).as_posix(),
                        "type": f.suffix.lower().lstrip('.'),
                    })
    return notes


@app.get("/api/notes/playlist")
def get_playlist_notes(channel: str, playlist: str):
    """Return all note files found in the playlist folder."""
    notes = []
    for root in ROOT_PATHS:
        folder = _get_notes_folder(channel, playlist, root)
        if not folder:
            continue
        for search_dir in [folder, folder / "notes"]:
            if not search_dir.exists():
                continue
            for f in sorted(search_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in NOTE_EXTENSIONS:
                    notes.append({
                        "title": f.stem,
                        "filename": f.name,
                        "path": f.relative_to(root).as_posix(),
                        "type": f.suffix.lower().lstrip('.'),
                    })
    return notes


@app.get("/api/notes/raw")
def get_note_raw(path: str):
    """Serve the raw note file (used for PDF iframe embedding)."""
    file_path = get_safe_path(path)
    ext = file_path.suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain; charset=utf-8',
        '.md':  'text/plain; charset=utf-8',
        '.rst': 'text/plain; charset=utf-8',
        '.csv': 'text/plain; charset=utf-8',
        '.rtf': 'application/rtf',
    }
    return FileResponse(
        file_path,
        media_type=media_types.get(ext, 'application/octet-stream'),
        headers={"Content-Disposition": "inline"},
    )


@app.get("/api/notes/content")
def get_note_content(path: str):
    """Return parsed text content for txt/md/docx notes."""
    file_path = get_safe_path(path)
    ext = file_path.suffix.lower()

    if ext in ('.txt', '.md', '.rst', '.csv'):
        content = file_path.read_text(encoding='utf-8', errors='replace')
        return {"type": ext.lstrip('.'), "content": content}

    if ext in ('.docx', '.doc'):
        try:
            from docx import Document
            doc = Document(str(file_path))
            text = '\n'.join(p.text for p in doc.paragraphs)
            return {"type": "txt", "content": text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse docx: {e}")

    raise HTTPException(status_code=400, detail="Use /api/notes/raw for binary files like PDF")

@app.get("/api/channels")
def list_channels():
    channels = []
    seen = set()
    has_root_videos = False
    
    for root in ROOT_PATHS:
        if root.exists():
            for entry in root.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    if entry.name not in seen:
                        channels.append({"name": entry.name})
                        seen.add(entry.name)
                elif entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
                    has_root_videos = True
                    
    if has_root_videos:
        channels.insert(0, {"name": "Uncategorized"})
        
    return channels

@app.get("/api/channels/{channel_name}/playlists")
def list_playlists(channel_name: str):
    playlists = {}
    has_loose_videos = False
    loose_dur = 0.0
    loose_watch = 0.0
    
    if channel_name == "Uncategorized":
        for root in ROOT_PATHS:
            if root.exists():
                for entry in root.iterdir():
                    if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
                        has_loose_videos = True
                        dur = get_video_duration(entry)
                        rel_path = entry.relative_to(root)
                        vid_url = f"/api/stream?path={urllib.parse.quote(rel_path.as_posix())}"
                        watch = get_progress_val(vid_url)
                        loose_dur += dur
                        loose_watch += min(watch, dur)
        return [{"name": "Root Videos", "duration": loose_dur, "watched": loose_watch}]

    for root in ROOT_PATHS:
        channel_path = root / channel_name
        if channel_path.exists() and channel_path.is_dir():
            for entry in channel_path.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    dur, watch = get_folder_progress(entry, channel_name, root)
                    if entry.name not in playlists:
                        playlists[entry.name] = {"name": entry.name, "duration": dur, "watched": watch}
                    else:
                        playlists[entry.name]["duration"] += dur
                        playlists[entry.name]["watched"] += watch
                elif entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
                    has_loose_videos = True
                    dur = get_video_duration(entry)
                    rel_path = entry.relative_to(root)
                    vid_url = f"/api/stream?path={urllib.parse.quote(rel_path.as_posix())}"
                    watch = get_progress_val(vid_url)
                    loose_dur += dur
                    loose_watch += min(watch, dur)
                    
    res = list(playlists.values())
    if has_loose_videos:
        res.insert(0, {"name": "Loose Videos", "duration": loose_dur, "watched": loose_watch})
        
    if not res:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    return res

def parse_video_files(files, rel_parent_path: str):
    videos = []
    
    for entry in files:
        if entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
            base_name = entry.stem
            subtitles = []
            for f in files:
                if f.is_file() and f.stem == base_name and f.suffix.lower() in SUBTITLE_EXTENSIONS:
                    # Construct relative path using forward slashes
                    rel_file = f"{rel_parent_path}/{f.name}" if rel_parent_path else f.name
                    sub_url = f"/api/subtitle?path={urllib.parse.quote(rel_file)}"
                    subtitles.append({"name": f.name, "url": sub_url})
            
            rel_vid = f"{rel_parent_path}/{entry.name}" if rel_parent_path else entry.name
            vid_url = f"/api/stream?path={urllib.parse.quote(rel_vid)}"
            
            duration = get_video_duration(entry)
            watched = get_progress_val(vid_url)
            
            videos.append({
                "title": base_name,
                "filename": entry.name,
                "url": vid_url,
                "subtitles": subtitles,
                "duration": duration,
                "watched": watched
            })
    return videos

@app.get("/api/channels/{channel_name}/playlists/{playlist_name}/videos")
def list_videos(channel_name: str, playlist_name: str):
    videos = []
    
    if channel_name == "Uncategorized" and playlist_name == "Root Videos":
        for root in ROOT_PATHS:
            if root.exists():
                videos.extend(parse_video_files(list(root.iterdir()), ""))
        return videos
        
    if playlist_name == "Loose Videos":
        for root in ROOT_PATHS:
            channel_path = root / channel_name
            if channel_path.exists() and channel_path.is_dir():
                videos.extend(parse_video_files(list(channel_path.iterdir()), channel_name))
        return videos

    # Normal playlist
    for root in ROOT_PATHS:
        playlist_path = root / channel_name / playlist_name
        if playlist_path.exists() and playlist_path.is_dir():
            rel_path = f"{channel_name}/{playlist_name}"
            videos.extend(parse_video_files(list(playlist_path.iterdir()), rel_path))
            
    return videos

def stream_file(path: Path, start: int, end: int):
    with open(path, "rb") as video:
        video.seek(start)
        remaining = end - start + 1
        chunk_size = 1024 * 1024 * 1 # 1MB chunks
        while remaining > 0:
            bytes_to_read = min(chunk_size, remaining)
            data = video.read(bytes_to_read)
            if not data:
                break
            remaining -= len(data)
            yield data

@app.get("/api/stream")
def stream_video(path: str, request: Request):
    file_path = get_safe_path(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
        
        if start >= file_size or end >= file_size:
            return JSONResponse(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                content={"detail": "Invalid Range"},
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        end = min(end, file_size - 1)
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            stream_file(file_path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            stream_file(file_path, 0, file_size - 1),
            status_code=status.HTTP_200_OK,
            headers=headers
        )

@app.get("/api/subtitle")
def get_subtitle(path: str):
    file_path = get_safe_path(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return FileResponse(file_path)
