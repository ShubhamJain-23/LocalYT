import { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom';
import { Folder, PlayCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function Channels() {
  const [channels, setChannels] = useState<{name: string}[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/channels`)
      .then(r => r.json())
      .then(data => setChannels(data));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Channels</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {channels.map(c => (
          <Link to={`/channel/${encodeURIComponent(c.name)}`} key={c.name} className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl flex items-center gap-4 transition-colors">
            <Folder size={32} className="text-red-500" />
            <span className="text-xl font-medium">{c.name}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function Playlists() {
  const { channel } = useParams();
  const [playlists, setPlaylists] = useState<{name: string}[]>([]);

  useEffect(() => {
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
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {playlists.map(p => (
          <Link to={`/channel/${encodeURIComponent(channel!)}/playlist/${encodeURIComponent(p.name)}`} key={p.name} className="bg-zinc-800 hover:bg-zinc-700 p-6 rounded-xl flex items-center gap-4 transition-colors">
            <Folder size={32} className="text-blue-500" />
            <span className="text-xl font-medium">{p.name}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function Videos() {
  const { channel, playlist } = useParams();
  const [videos, setVideos] = useState<any[]>([]);

  useEffect(() => {
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
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {videos.map(v => (
          <Link to={`/watch?url=${encodeURIComponent(v.url)}&title=${encodeURIComponent(v.title)}&subs=${encodeURIComponent(JSON.stringify(v.subtitles))}`} key={v.title} className="bg-zinc-800 hover:bg-zinc-700 rounded-xl overflow-hidden transition-colors flex flex-col">
            <div className="bg-black aspect-video flex items-center justify-center relative group">
              <PlayCircle size={48} className="text-white opacity-50 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="p-4">
              <span className="text-lg font-medium line-clamp-2">{v.title}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function Player() {
  const params = new URLSearchParams(window.location.search);
  const url = params.get('url');
  const title = params.get('title');
  const subsStr = params.get('subs');
  const subtitles = subsStr ? JSON.parse(subsStr) : [];
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const [alertText, setAlertText] = useState<string | null>(null);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input field (if any added later)
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
  }, []);

  if (!url) return <div className="p-8">No video selected</div>;

  const videoUrl = `http://localhost:8000${url}`;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8">
      <div className="bg-black rounded-xl overflow-hidden shadow-lg aspect-video mb-6 relative">
        <video 
          ref={videoRef}
          controls 
          className="w-full h-full"
          crossOrigin="anonymous"
          autoPlay
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
      <h1 className="text-2xl font-bold mb-4">{title}</h1>
      <div className="text-zinc-400 text-sm space-y-1">
        <p><strong>Shortcuts:</strong></p>
        <p><kbd className="bg-zinc-800 px-2 py-1 rounded">f</kbd> Full screen &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">m</kbd> Mute &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">Space / k</kbd> Play/Pause</p>
        <p><kbd className="bg-zinc-800 px-2 py-1 rounded">&uarr; / &darr;</kbd> Volume &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">Shift + . / ,</kbd> Speed &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">&larr; / &rarr;</kbd> Skip 5s &bull; <kbd className="bg-zinc-800 px-2 py-1 rounded">j / l</kbd> Skip 10s</p>
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
            <Route path="/watch" element={<Player />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
