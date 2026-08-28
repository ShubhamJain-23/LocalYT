import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse

app = FastAPI(title="LocalYT API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIRS_ENV = os.environ.get("DATA_DIRS", "./data")
ROOT_PATHS = [Path(d.strip()).resolve() for d in DATA_DIRS_ENV.split(",") if d.strip()]

def get_safe_path(sub_path: str) -> Path:
    decoded_path = urllib.parse.unquote(sub_path)
    for root in ROOT_PATHS:
        target = (root / decoded_path).resolve()
        if str(target).startswith(str(root)) and target.exists():
            return target
    raise HTTPException(status_code=404, detail="File not found or access denied")

VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.mkv', '.mov', '.avi'}
SUBTITLE_EXTENSIONS = {'.vtt', '.srt'}

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
    if channel_name == "Uncategorized":
        return [{"name": "Root Videos"}]
        
    playlists = []
    seen = set()
    has_loose_videos = False
    
    for root in ROOT_PATHS:
        channel_path = root / channel_name
        if channel_path.exists() and channel_path.is_dir():
            for entry in channel_path.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    if entry.name not in seen:
                        playlists.append({"name": entry.name})
                        seen.add(entry.name)
                elif entry.is_file() and entry.suffix.lower() in VIDEO_EXTENSIONS:
                    has_loose_videos = True
                    
    if has_loose_videos:
        playlists.insert(0, {"name": "Loose Videos"})
        
    if not playlists and not has_loose_videos:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    return playlists

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
            videos.append({
                "title": base_name,
                "filename": entry.name,
                "url": vid_url,
                "subtitles": subtitles
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
