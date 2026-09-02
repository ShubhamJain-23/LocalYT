import { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { Folder, PlayCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function formatTime(seconds: number) {
  if (!seconds || isNaN(seconds)) return "0m";
  const m = Math.floor(seconds / 60);
  const h = Math.floor(m / 60);
  if (h > 0) {
    return `${h}h ${m % 60}m`;
  }
  return `${m}m`;
}

function ProgressIndicator({ watched, duration }: { watched: number, duration: number }) {
  if (!duration || duration <= 0) return null;
  const percentage = Math.min(Math.round((watched / duration) * 100), 100);
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs text-zinc-400 mb-1">
        <span>{percentage}%</span>
        <span>{formatTime(watched)} / {formatTime(duration)}</span>
      </div>
      <div className="w-full bg-zinc-700 h-1.5 rounded-full overflow-hidden">
        <div className="bg-red-500 h-full rounded-full" style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}


function Channels() {
  const [channels, setChannels] = useState<any[] | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/channels`)
      .then(r => r.json())
      .then(data => setChannels(data));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Channels</h1>
      {channels === null ? (
        <div className="text-center py-20">
          <div className="animate-spin w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading channels... (Scanning entire library for the first time may take a few moments)</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {channels.map((c: any) => (
            <Link to={`/channel/${encodeURIComponent(c.name)}`} key={c.name} className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl flex flex-col transition-colors">
              <div className="flex items-center gap-4 mb-2">
                <Folder size={32} className="text-red-500 shrink-0" />
                <span className="text-xl font-medium truncate">{c.name}</span>
              </div>
              <ProgressIndicator watched={c.watched} duration={c.duration} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function Playlists() {
  const { channel } = useParams();
  const [playlists, setPlaylists] = useState<any[] | null>(null);

  useEffect(() => {
    setPlaylists(null);
    fetch(`${API_BASE}/channels/${encodeURIComponent(channel!)}/playlists`)
      .then(r => r.json())
      .then(data => setPlaylists(data));
  }, [channel]);

  return (
    <div className="p-8">
      <div className="flex items-center gap-4 mb-6 text-zinc-400 text-sm">
        <Link to="/" className="hover:text-white">Home</Link>
        <span>/</span>
        <span className="text-white">{channel}</span>
      </div>
      <h1 className="text-3xl font-bold mb-6">Playlists</h1>
      
      {playlists === null ? (
        <div className="text-center py-20">
          <div className="animate-spin w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading playlists... (Scanning files for the first time may take a few moments)</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {playlists.map((p: any) => (
            <Link to={`/channel/${encodeURIComponent(channel!)}/playlist/${encodeURIComponent(p.name)}`} key={p.name} className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl flex flex-col transition-colors">
              <div className="flex items-center gap-4 mb-2">
                <Folder size={32} className="text-blue-500 shrink-0" />
                <span className="text-xl font-medium truncate">{p.name}</span>
              </div>
              <ProgressIndicator watched={p.watched} duration={p.duration} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function Videos() {
  const { channel, playlist } = useParams();
  const [videos, setVideos] = useState<any[] | null>(null);

  useEffect(() => {
    setVideos(null); // Reset when changing playlist
    fetch(`${API_BASE}/channels/${encodeURIComponent(channel!)}/playlists/${encodeURIComponent(playlist!)}/videos`)
      .then(r => r.json())
      .then(data => setVideos(data));
  }, [channel, playlist]);

  return (
    <div className="p-8">
      <div className="flex items-center gap-4 mb-6 text-zinc-400 text-sm">
        <Link to="/" className="hover:text-white">Home</Link>
        <span>/</span>
        <Link to={`/channel/${encodeURIComponent(channel!)}`} className="hover:text-white">{channel}</Link>
        <span>/</span>
        <span className="text-white">{playlist}</span>
      </div>
      <h1 className="text-3xl font-bold mb-6">Videos</h1>
      
      {videos === null ? (
        <div className="text-center py-20">
          <div className="animate-spin w-12 h-12 border-4 border-red-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading videos... (Scanning files for the first time may take a few moments)</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {videos.map((v: any) => (
            <Link to={`/watch/${encodeURIComponent(channel!)}/${encodeURIComponent(playlist!)}?url=${encodeURIComponent(v.url)}&title=${encodeURIComponent(v.title)}&subs=${encodeURIComponent(JSON.stringify(v.subtitles))}`} key={v.title} className="bg-zinc-800 hover:bg-zinc-700 rounded-xl overflow-hidden transition-colors flex flex-col">
              <div className="bg-black aspect-video flex items-center justify-center relative group shrink-0">
                <PlayCircle size={48} className="text-white opacity-50 group-hover:opacity-100 transition-opacity" />
              </div>
              <div className="p-4 flex flex-col h-full justify-between">
                <span className="text-lg font-medium line-clamp-2 mb-2">{v.title}</span>
                <ProgressIndicator watched={v.watched} duration={v.duration} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function Player() {
  const { channel, playlist } = useParams();
  const navigate = useNavigate();
  const params = new URLSearchParams(window.location.search);
  const url = params.get('url');
  const title = params.get('title');
  const subsStr = params.get('subs');
  const subtitles = subsStr ? JSON.parse(subsStr) : [];
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const [alertText, setAlertText] = useState<string | null>(null);
  const [playlistVideos, setPlaylistVideos] = useState<any[]>([]);
  
  const stateRef = useRef({ url, playlistVideos });
  useEffect(() => {
    stateRef.current = { url, playlistVideos };
  }, [url, playlistVideos]);

  useEffect(() => {
    if (channel && playlist) {
      fetch(`${API_BASE}/channels/${encodeURIComponent(channel)}/playlists/${encodeURIComponent(playlist)}/videos`)
        .then(r => r.json())
        .then(data => setPlaylistVideos(data))
        .catch(() => {});
    }
  }, [channel, playlist]);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input field
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
      
      if (!videoRef.current) return;
      let changed = false;

      if (e.key === '>' || (e.shiftKey && e.key === '.')) {
        videoRef.current.playbackRate = Math.min(videoRef.current.playbackRate + 0.25, 4.0);
        changed = true;
        setAlertText(`Speed: ${videoRef.current.playbackRate}x`);
      } else if (e.key === '<' || (e.shiftKey && e.key === ',')) {
        videoRef.current.playbackRate = Math.max(videoRef.current.playbackRate - 0.25, 0.25);
        changed = true;
        setAlertText(`Speed: ${videoRef.current.playbackRate}x`);
      } else if (e.key.toLowerCase() === 'f') {
        if (document.fullscreenElement) {
          document.exitFullscreen();
        } else {
          videoRef.current.parentElement?.requestFullscreen();
        }
      } else if (e.key.toLowerCase() === 'm') {
        videoRef.current.muted = !videoRef.current.muted;
        changed = true;
        setAlertText(videoRef.current.muted ? 'Muted' : 'Unmuted');
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        videoRef.current.volume = Math.min(videoRef.current.volume + 0.05, 1.0);
        changed = true;
        setAlertText(`Volume: ${Math.round(videoRef.current.volume * 100)}%`);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        videoRef.current.volume = Math.max(videoRef.current.volume - 0.05, 0.0);
        changed = true;
        setAlertText(`Volume: ${Math.round(videoRef.current.volume * 100)}%`);
      } else if (e.key === ' ' || e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (videoRef.current.paused) {
          videoRef.current.play();
        } else {
          videoRef.current.pause();
        }
        changed = true;
        setAlertText(videoRef.current.paused ? 'Paused' : 'Playing');
      } else if (e.key === 'ArrowRight') {
        videoRef.current.currentTime = Math.min(videoRef.current.currentTime + 5, videoRef.current.duration);
        changed = true;
        setAlertText('Forward 5s');
      } else if (e.key === 'ArrowLeft') {
        videoRef.current.currentTime = Math.max(videoRef.current.currentTime - 5, 0);
        changed = true;
        setAlertText('Back 5s');
      } else if (e.key.toLowerCase() === 'l') {
        videoRef.current.currentTime = Math.min(videoRef.current.currentTime + 10, videoRef.current.duration);
        changed = true;
        setAlertText('Forward 10s');
      } else if (e.key.toLowerCase() === 'j') {
        videoRef.current.currentTime = Math.max(videoRef.current.currentTime - 10, 0);
        changed = true;
        setAlertText('Back 10s');
      } else if (e.key.toLowerCase() === 'n') {
        const { url: currentUrl, playlistVideos: videos } = stateRef.current;
        const idx = videos.findIndex((v: any) => v.url === currentUrl);
        if (idx !== -1 && idx < videos.length - 1) {
          const nextV = videos[idx + 1];
          navigate(`/watch/${encodeURIComponent(channel!)}/${encodeURIComponent(playlist!)}?url=${encodeURIComponent(nextV.url)}&title=${encodeURIComponent(nextV.title)}&subs=${encodeURIComponent(JSON.stringify(nextV.subtitles))}`);
        }
      } else if (e.key.toLowerCase() === 'p' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const { url: currentUrl, playlistVideos: videos } = stateRef.current;
        const idx = videos.findIndex((v: any) => v.url === currentUrl);
        if (idx > 0) {
          const prevV = videos[idx - 1];
          navigate(`/watch/${encodeURIComponent(channel!)}/${encodeURIComponent(playlist!)}?url=${encodeURIComponent(prevV.url)}&title=${encodeURIComponent(prevV.title)}&subs=${encodeURIComponent(JSON.stringify(prevV.subtitles))}`);
        }
      }

      if (changed) {
        clearTimeout(timeout);
        timeout = setTimeout(() => setAlertText(null), 1500);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timeout);
    };
  }, [channel, playlist, navigate]);

  if (!url) return <div className="p-8">No video selected</div>;

  const videoUrl = `http://localhost:8000${url}`;

  const lastSavedTime = useRef(0);

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const currentTime = videoRef.current.currentTime;
    
    localStorage.setItem(`progress_${url}`, currentTime.toString());
    
    // Save to backend every 5 seconds
    if (Math.abs(currentTime - lastSavedTime.current) > 5) {
      lastSavedTime.current = currentTime;
      fetch(`${API_BASE}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, time: currentTime })
      }).catch(() => {});
    }
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    
    fetch(`${API_BASE}/progress?url=${encodeURIComponent(url)}`)
      .then(r => r.json())
      .then(data => {
        if (data.time > 0) {
          videoRef.current!.currentTime = data.time;
          lastSavedTime.current = data.time;
        } else {
          const saved = localStorage.getItem(`progress_${url}`);
          if (saved) {
            videoRef.current!.currentTime = parseFloat(saved);
          }
        }
      })
      .catch(() => {
        const saved = localStorage.getItem(`progress_${url}`);
        if (saved) {
          videoRef.current!.currentTime = parseFloat(saved);
        }
      });
  };

  const currentIndex = playlistVideos.findIndex(v => v.url === url);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex !== -1 && currentIndex < playlistVideos.length - 1;

  const goPrev = () => {
    if (hasPrev) {
      const prevV = playlistVideos[currentIndex - 1];
      navigate(`/watch/${encodeURIComponent(channel!)}/${encodeURIComponent(playlist!)}?url=${encodeURIComponent(prevV.url)}&title=${encodeURIComponent(prevV.title)}&subs=${encodeURIComponent(JSON.stringify(prevV.subtitles))}`);
    }
  };
  
  const goNext = () => {
    if (hasNext) {
      const nextV = playlistVideos[currentIndex + 1];
      navigate(`/watch/${encodeURIComponent(channel!)}/${encodeURIComponent(playlist!)}?url=${encodeURIComponent(nextV.url)}&title=${encodeURIComponent(nextV.title)}&subs=${encodeURIComponent(JSON.stringify(nextV.subtitles))}`);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="bg-black rounded-xl overflow-hidden shadow-lg aspect-video mb-6 relative">
        <video 
          key={url}
          ref={videoRef}
          controls 
          className="w-full h-full"
          crossOrigin="anonymous"
          autoPlay
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
        >
          <source src={videoUrl} type="video/mp4" />
          {subtitles.map((sub: any, i: number) => (
            <track 
              key={i} 
              kind="subtitles" 
              src={`http://localhost:8000${sub.url}`} 
              srcLang="en" 
              label={sub.name} 
              default={i === 0} 
            />
          ))}
          Your browser does not support the video tag.
        </video>
        
        {/* Indicator Overlay */}
        {alertText && (
          <div className="absolute top-8 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg text-lg font-bold pointer-events-none transition-opacity z-50">
            {alertText}
          </div>
        )}
      </div>
      
      <div className="flex justify-between items-center mb-4 gap-4">
        <h1 className="text-2xl font-bold line-clamp-1">{title}</h1>
        <div className="flex gap-2 shrink-0">
          <button 
            onClick={goPrev} 
            disabled={!hasPrev} 
            className="px-4 py-2 bg-zinc-800 rounded-lg hover:bg-zinc-700 disabled:opacity-30 disabled:hover:bg-zinc-800 transition-colors font-medium text-sm text-white"
          >
            Prev (P)
          </button>
          <button 
            onClick={goNext} 
            disabled={!hasNext} 
            className="px-4 py-2 bg-zinc-800 rounded-lg hover:bg-zinc-700 disabled:opacity-30 disabled:hover:bg-zinc-800 transition-colors font-medium text-sm text-white"
          >
            Next (N)
          </button>
        </div>
      </div>
      
      <div className="text-zinc-400 text-sm space-y-1">
        <p><strong>Shortcuts:</strong></p>
        <p><kbd className="bg-zinc-800 px-2 py-1 rounded">f</kbd> Full screen &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">m</kbd> Mute &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">Space / k</kbd> Play/Pause</p>
        <p><kbd className="bg-zinc-800 px-2 py-1 rounded">&uarr; / &darr;</kbd> Volume &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">Shift + . / ,</kbd> Speed &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">&larr; / &rarr;</kbd> Skip 5s &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">j / l</kbd> Skip 10s &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">n / p</kbd> Next/Prev</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <nav className="bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
          <Link to="/" className="flex items-center gap-2 text-white font-bold text-2xl tracking-tighter">
            <div className="bg-red-600 text-white p-1 rounded-lg">
              <PlayCircle size={24} fill="currentColor" className="text-white" />
            </div>
            LocalYT
          </Link>
        </nav>
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Channels />} />
            <Route path="/channel/:channel" element={<Playlists />} />
            <Route path="/channel/:channel/playlist/:playlist" element={<Videos />} />
            <Route path="/watch/:channel/:playlist" element={<Player />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
