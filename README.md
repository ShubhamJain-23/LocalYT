# LocalYT

LocalYT is a fast, lightweight, open-source YouTube clone designed to serve your local video files over a beautiful web interface. It runs entirely via Docker and requires zero complicated database setups—it simply reads your media files directly from the filesystem!

## Features

- **Folder-based Library**: Automatically organizes your videos.
  - Root folders act as "Channels".
  - Sub-folders act as "Playlists".
  - Any loose videos are smartly grouped into an "Uncategorized" section.
- **High-Performance Streaming**: Uses a Python FastAPI backend capable of HTTP 206 Partial Content range requests, allowing seamless video seeking and skipping without buffering the whole file.
- **Native Video Player**: Fast HTML5 video player with YouTube-like keyboard shortcuts.
- **Automatic Subtitles**: Just name your `.srt` or `.vtt` files the same as your `.mp4` files, and they will automatically load into the player.
- **Multi-Drive Support**: Easily mount multiple hard drives or external storage via Docker Compose.

## Keyboard Shortcuts

- `Space` or `k`: Play/Pause
- `f`: Full Screen
- `m`: Mute
- `Shift` + `.` / `,`: Increase/Decrease Playback Speed
- `←` / `→`: Skip backward/forward 5 seconds
- `j` / `l`: Skip backward/forward 10 seconds
- `↑` / `↓`: Volume Up/Down

## Installation & Usage

### Prerequisites
- [Docker](https://www.docker.com/) installed and running.

### 1. Clone the repository
```bash
git clone https://github.com/ShubhamJain-23/LocalYT.git
cd LocalYT
```

### 2. Configure Your Video Folders
By default, the app looks for videos inside the `data/` folder in the project directory.

**The Easy Way (Windows only):**
Simply double-click the `add_folder.bat` file in the project folder! It will prompt you to paste the path to your video folder (e.g. `D:\Movies`), and it will automatically reconfigure and restart Docker for you safely. You can run this file as many times as you want to add multiple drives.

**The Manual Way:**
1. Open `folders.txt` and add your absolute paths (one per line).
2. Run `powershell.exe -ExecutionPolicy Bypass -File generate_override.ps1` to generate the configuration.
3. Restart docker with `docker-compose up -d`.

### 3. Run the App
Start the containers in the background:
```bash
docker-compose up --build -d
```

### 4. Access LocalYT
Open your browser and navigate to:
**[http://localhost:3000](http://localhost:3000)**

## Tech Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** React, Vite, Tailwind CSS (v4), TypeScript
- **Deployment:** Docker, Docker Compose, Nginx
