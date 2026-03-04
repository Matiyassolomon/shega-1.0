import { useEffect, useMemo, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8787'

const DEMO_AUDIO = [
  'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
  'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
  'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
  'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
]

const COVER_POOL = [
  'https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1507838153414-b4b713384a76?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1470229538611-16ba8c7ffbd7?auto=format&fit=crop&w=1200&q=80',
]

const PODCASTS = [
  { id: 1, title: 'Bible Study - Dr. Mamush', duration: '45 min', status: 'New Episode', premium: false },
  { id: 2, title: 'History of Ethiopia', duration: '1 hr 12 min', status: 'Popular', premium: true },
  { id: 3, title: 'Tech News Ethiopia', duration: '28 min', status: 'Daily Update', premium: false },
  { id: 4, title: 'Literature & Arts', duration: '54 min', status: 'Weekly', premium: true },
]

const TRACK_THEME = ['#2a3b55', '#4a5f2a', '#6a3a2a', '#2a5d63', '#5a2a63']

const LYRICS_MAP = {
  tizita: [
    'City breathes in neon light',
    'Slow drums under midnight sky',
    'Every step becomes a rhythm',
    'Hold the moment, let it ride',
  ],
  default: ['Lyrics are not available for this track yet.'],
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function pickTextColor(hex) {
  const clean = hex.replace('#', '')
  const bigint = Number.parseInt(clean, 16)
  const r = (bigint >> 16) & 255
  const g = (bigint >> 8) & 255
  const b = bigint & 255
  const luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luma > 0.63 ? '#0f1a33' : '#f2f7ff'
}

function BottomIcon({ id, active }) {
  const color = active ? '#19c955' : '#8fa0ba'
  if (id === 'home')
    return (
      <svg viewBox="0 0 24 24" className="icon-24" fill={color}>
        <path d="M12 3 3 10v10h6v-6h6v6h6V10l-9-7Z" />
      </svg>
    )
  if (id === 'search')
    return (
      <svg viewBox="0 0 24 24" className="icon-24" fill="none" stroke={color} strokeWidth="2.2">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3-3" />
      </svg>
    )
  if (id === 'podcasts')
    return (
      <svg viewBox="0 0 24 24" className="icon-24" fill="none" stroke={color} strokeWidth="2.2">
        <circle cx="12" cy="8.5" r="3" />
        <path d="M7 15a5 5 0 0 1 10 0M12 13v8" />
      </svg>
    )
  if (id === 'library')
    return (
      <svg viewBox="0 0 24 24" className="icon-24" fill={color}>
        <path d="M16 3H8v18h8V3Zm-6 2h4v14h-4V5Zm-6 2h2v12H4V7Zm14 0h2v12h-2V7Z" />
      </svg>
    )
  return (
    <svg viewBox="0 0 24 24" className="icon-24" fill={color}>
      <path d="M3 10h18l-2 11H5L3 10Zm4-4h10l1 4H6l1-4Z" />
    </svg>
  )
}

// Backward-compatible alias to prevent runtime crashes if Icon is referenced.
const Icon = BottomIcon

function ActionButton({ children, onClick, variant = 'soft' }) {
  const cls =
    variant === 'primary'
      ? 'btn btn-primary'
      : variant === 'danger'
      ? 'btn btn-danger'
      : 'btn btn-soft'
  return (
    <button onClick={onClick} className={cls}>
      {children}
    </button>
  )
}

function RowAction({ type, onClick }) {
  return (
    <button
      onClick={onClick}
      className="icon-btn-round"
      aria-label={type}
    >
      {type === 'play' && (
        <svg viewBox="0 0 24 24" className="icon-16" fill="currentColor">
          <path d="M8 6v12l10-6-10-6Z" />
        </svg>
      )}
      {type === 'pay' && <span className="icon-pay-strong">$</span>}
      {type === 'download' && (
        <svg viewBox="0 0 24 24" className="icon-16" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M12 4v10m0 0 4-4m-4 4-4-4M5 20h14" />
        </svg>
      )}
    </button>
  )
}

function FlatRowAction({ type, onClick }) {
  return (
    <button onClick={onClick} className="icon-btn-flat" aria-label={type}>
      {type === 'play' && (
        <svg viewBox="0 0 24 24" className="icon-20" fill="currentColor">
          <path d="M8 6v12l10-6-10-6Z" />
        </svg>
      )}
      {type === 'pay' && <span className="icon-pay-light">$</span>}
      {type === 'download' && (
        <svg viewBox="0 0 24 24" className="icon-20" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M12 4v10m0 0 4-4m-4 4-4-4M5 20h14" />
        </svg>
      )}
    </button>
  )
}

function PlayPauseIcon({ playing, className = 'h-5 w-5' }) {
  if (playing) {
    return (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <rect x="7" y="5" width="4" height="14" rx="1.2" />
        <rect x="13" y="5" width="4" height="14" rx="1.2" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M8 6v12l10-6-10-6Z" />
    </svg>
  )
}
export default function App() {
  const [tab, setTab] = useState('home')
  const [notice, setNotice] = useState('')
  const [songs, setSongs] = useState([])
  const [listings, setListings] = useState([])
  const [search, setSearch] = useState('')
  const [playingPodcastId, setPlayingPodcastId] = useState(null)
  const [showLyrics, setShowLyrics] = useState(false)

  const [nowAccent, setNowAccent] = useState('#2a3b55')
  const [nowText, setNowText] = useState('#f2f7ff')

  const audioRef = useRef(null)
  const [trackIndex, setTrackIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)

  const playableSongs = useMemo(
    () =>
      songs.slice(0, 10).map((song, idx) => ({
        ...song,
        audio: DEMO_AUDIO[idx % DEMO_AUDIO.length],
        cover: COVER_POOL[idx % COVER_POOL.length],
      })),
    [songs],
  )

  const currentSong = playableSongs[trackIndex] || {
    id: 0,
    title: 'Tizita',
    artist_name: 'Mahmoud Ahmed',
    genre: 'Ere Mela Mela (1975)',
    tier: 'premium',
    price: 1.49,
    audio: DEMO_AUDIO[0],
    cover: COVER_POOL[0],
  }

  const currentLyrics = LYRICS_MAP[currentSong.title?.toLowerCase()] || LYRICS_MAP.default

  useEffect(() => {
    const load = async () => {
      try {
        const [songsRes, listingsRes] = await Promise.all([
          fetch(`${API_BASE}/api/catalog/songs`),
          fetch(`${API_BASE}/api/playlists`),
        ])
        const songsData = await songsRes.json().catch(() => ({}))
        const listingsData = await listingsRes.json().catch(() => ({}))
        if (Array.isArray(songsData.songs)) setSongs(songsData.songs)
        if (Array.isArray(listingsData.listings)) setListings(listingsData.listings)
      } catch (_e) {
        setNotice('Backend offline mode')
      }
    }
    load()
  }, [])

  useEffect(() => {
    const color = TRACK_THEME[trackIndex % TRACK_THEME.length]
    setNowAccent(color)
    setNowText(pickTextColor(color))
  }, [trackIndex])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    audio.src = currentSong.audio
    audio.load()
    setProgress(0)
    if (isPlaying) audio.play().catch(() => setIsPlaying(false))
  }, [currentSong.audio, trackIndex])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) audio.play().catch(() => setIsPlaying(false))
    else audio.pause()
  }, [isPlaying])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    const onTime = () => setProgress(audio.currentTime || 0)
    const onMeta = () => setDuration(audio.duration || 0)
    const onEnd = () => setTrackIndex((i) => (playableSongs.length ? (i + 1) % playableSongs.length : i))
    audio.addEventListener('timeupdate', onTime)
    audio.addEventListener('loadedmetadata', onMeta)
    audio.addEventListener('ended', onEnd)
    return () => {
      audio.removeEventListener('timeupdate', onTime)
      audio.removeEventListener('loadedmetadata', onMeta)
      audio.removeEventListener('ended', onEnd)
    }
  }, [playableSongs.length])

  const filteredSongs = songs.filter((s) => {
    const q = search.trim().toLowerCase()
    if (!q) return true
    return s.title.toLowerCase().includes(q) || s.artist_name.toLowerCase().includes(q)
  })

  const handleSongPay = async (songId) => {
    try {
      const res = await fetch(`${API_BASE}/api/purchase-song`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_2', song_id: songId }),
      })
      const data = await res.json().catch(() => ({}))
      setNotice(data.message || data.detail || 'Payment request complete')
    } catch (_e) {
      setNotice('Payment failed')
    }
  }

  const handlePlaylistPay = async (playlistId) => {
    try {
      const res = await fetch(`${API_BASE}/api/checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlistId }),
      })
      const data = await res.json().catch(() => ({}))
      setNotice(data.message || data.detail || 'Checkout request complete')
    } catch (_e) {
      setNotice('Checkout failed')
    }
  }

  const handleDownload = (label) => setNotice(`Downloading ${label} (demo)`)
  const handlePlayNext = (songTitle) => setNotice(`Added "${songTitle}" to Play Next`)

  return (
    <main className="app-root">
      <audio ref={audioRef} preload="metadata" />
      <div className="app-frame">
        <header className="app-header">
          <p className="header-subtitle">Now Playing + Browse</p>
          <h1 className="header-title">Music Lite</h1>
          {notice && <p className="header-notice">{notice}</p>}
        </header>

        {tab === 'home' && (
          <section
            className="home-section"
            style={{
              background: `linear-gradient(180deg, ${nowAccent}22 0%, #edf1f6 55%)`,
            }}
          >
            <div className="now-cover-shell">
              <img src={currentSong.cover} alt="Now playing cover" className="cover-image-square" />
            </div>

            <div className="center-text">
              <h2 className="now-song-title" style={{ color: nowText }}>
                {currentSong.title}
              </h2>
              <p className="accent-artist">{currentSong.artist_name}</p>
              <p className="muted-line">{currentSong.genre}</p>
            </div>

            <div>
              <input
                type="range"
                min="0"
                max={duration || 0}
                step="0.1"
                value={progress}
                onChange={(e) => {
                  const v = Number(e.target.value)
                  setProgress(v)
                  if (audioRef.current) audioRef.current.currentTime = v
                }}
                className="progress-slider"
              />
              <div className="time-row">
                <span>{formatTime(progress)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            <div className="transport-row">
              <button
                className="transport-btn"
                onClick={() => setTrackIndex((i) => (playableSongs.length ? (i - 1 + playableSongs.length) % playableSongs.length : i))}
              >
                <svg viewBox="0 0 24 24" className="icon-24" fill="none" stroke="#162443" strokeWidth="2.2">
                  <path d="M18 6 9 12l9 6V6ZM6 6v12" />
                </svg>
              </button>
              <button className="transport-play-btn" onClick={() => setIsPlaying((v) => !v)}>
                <PlayPauseIcon playing={isPlaying} className="icon-32" />
              </button>
              <button
                className="transport-btn"
                onClick={() => setTrackIndex((i) => (playableSongs.length ? (i + 1) % playableSongs.length : i))}
              >
                <svg viewBox="0 0 24 24" className="icon-24" fill="none" stroke="#162443" strokeWidth="2.2">
                  <path d="m6 6 9 6-9 6V6Zm12 0v12" />
                </svg>
              </button>
            </div>

            <div className="quick-actions">
              <button className="btn btn-primary" onClick={() => setIsPlaying((v) => !v)}>
                {isPlaying ? 'Pause' : 'Play'}
              </button>
              <button className="btn btn-soft" onClick={() => handleDownload(currentSong.title)}>
                Download
              </button>
              <button className="btn btn-danger" onClick={() => handleSongPay(currentSong.id)}>
                Pay
              </button>
              <button className="btn btn-soft" onClick={() => setShowLyrics((v) => !v)}>
                {showLyrics ? 'Hide Lyrics' : 'Lyrics'}
              </button>
            </div>

            {showLyrics && (
              <div className="card-surface">
                <h3 className="section-kicker">Lyrics</h3>
                <div className="lyrics-lines">
                  {currentLyrics.map((line) => (
                    <p key={line}>{line}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="card-surface">
              <h3 className="section-kicker">Up Next</h3>
              <div className="stack-sm">
                {playableSongs.slice(0, 5).map((song, idx) => (
                  <div key={song.id} className="tile-soft">
                    <div className="row-between">
                      <div className="row-left">
                        <img src={song.cover} alt={song.title} className="cover-sm" />
                        <div>
                          <p className="title-sm">{song.title}</p>
                          <p className="caption-muted">{song.artist_name}</p>
                        </div>
                      </div>
                      <div className="row-gap-sm">
                        <RowAction type="play" onClick={() => setTrackIndex(idx)} />
                        <RowAction type="pay" onClick={() => handleSongPay(song.id)} />
                        <RowAction type="download" onClick={() => handleDownload(song.title)} />
                      </div>
                    </div>
                    <div className="stack-top-sm">
                      <button className="link-mini" onClick={() => handlePlayNext(song.title)}>
                        Play Next
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {tab === 'search' && (
          <section className="search-section">
            <div className="row-between">
              <h2 className="browse-title">Browse</h2>
              <div className="profile-badge">
                <svg viewBox="0 0 24 24" className="icon-28" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <circle cx="12" cy="9" r="4" />
                  <path d="M5 20a7 7 0 0 1 14 0" />
                </svg>
              </div>
            </div>

            <div className="search-input-wrap">
              <svg viewBox="0 0 24 24" className="search-input-icon" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3-3" />
              </svg>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="search-input"
                placeholder="Search songs, artists, or albums..."
              />
            </div>

            <div className="chip-row">
              {['Trending', 'My Playlist', 'Radio', 'Podcasts'].map((chip, idx) => (
                <button
                  key={chip}
                  className={`chip-btn ${idx === 0 ? 'chip-btn-active' : ''}`}
                >
                  {chip}
                </button>
              ))}
            </div>

            <div className="row-between">
              <h3 className="section-title-lg">New Releases</h3>
              <button className="link-accent">See All</button>
            </div>

            <div className="stack-md">
              {filteredSongs.slice(0, 8).map((song, idx) => (
                <div key={song.id} className="row-track">
                  <img src={COVER_POOL[idx % COVER_POOL.length]} alt={song.title} className="cover-md" />
                  <div className="track-text">
                    <p className="track-title">{song.title}</p>
                    <p className="track-subtitle">{song.artist_name}</p>
                  </div>
                  <div className="row-actions">
                    <FlatRowAction
                      type="play"
                      onClick={() => {
                        const found = playableSongs.findIndex((s) => s.id === song.id)
                        if (found >= 0) setTrackIndex(found)
                        setTab('home')
                        setIsPlaying(true)
                      }}
                    />
                    <FlatRowAction type="pay" onClick={() => handleSongPay(song.id)} />
                    <FlatRowAction type="download" onClick={() => handleDownload(song.title)} />
                  </div>
                </div>
              ))}
            </div>

            <div className="mini-player">
              <div className="row-track">
                <img src={currentSong.cover} alt={currentSong.title} className="cover-sm" />
                <div className="track-text">
                  <p className="mini-title">{currentSong.title}</p>
                  <p className="mini-subtitle">{currentSong.artist_name}</p>
                </div>
                <button
                  className="mini-icon-btn"
                  onClick={() => setIsPlaying((v) => !v)}
                  aria-label="Play pause mini player"
                >
                  <PlayPauseIcon playing={isPlaying} className="icon-24" />
                </button>
                <button
                  className="mini-icon-btn"
                  onClick={() => setTrackIndex((i) => (playableSongs.length ? (i + 1) % playableSongs.length : i))}
                  aria-label="Next mini player"
                >
                  <svg viewBox="0 0 24 24" className="icon-24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <path d="m6 6 9 6-9 6V6Zm12 0v12" />
                  </svg>
                </button>
              </div>
            </div>
          </section>
        )}

        {tab === 'podcasts' && (
          <section className="podcasts-section">
            <div className="row-between">
              <div>
                <h2 className="section-title-xl">Podcasts</h2>
                <p className="muted-line">Popular episodes</p>
              </div>
              <button className="btn-pill-primary">Explore</button>
            </div>

            <div className="chip-row">
              {['All', 'Education', 'Technology', 'Arts'].map((chip, idx) => (
                <button
                  key={chip}
                  className={`chip-btn ${idx === 0 ? 'chip-btn-active' : ''}`}
                >
                  {chip}
                </button>
              ))}
            </div>

            <div className="stack-md">
              {PODCASTS.map((episode, idx) => (
                <div key={episode.id} className="card-surface">
                  <div className="row-track">
                    <img src={COVER_POOL[(idx + 1) % COVER_POOL.length]} alt={episode.title} className="cover-md" />
                    <div className="track-text">
                      <p className="track-title-sm">{episode.title}</p>
                      <p className="accent-caption">{episode.premium ? 'Premium Episode' : 'Free Episode'}</p>
                      <p className="track-subtitle">
                        {episode.duration} - {episode.status}
                      </p>
                    </div>
                    <div className="row-actions-tight">
                      <FlatRowAction type="play" onClick={() => setPlayingPodcastId((id) => (id === episode.id ? null : episode.id))} />
                      <FlatRowAction
                        type="pay"
                        onClick={() => setNotice(episode.premium ? `Paid for "${episode.title}"` : `"${episode.title}" is free`)}
                      />
                      <FlatRowAction type="download" onClick={() => handleDownload(episode.title)} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {tab === 'library' && (
          <section className="simple-section">
            <div className="card-surface">
              <h3 className="section-subtitle">Playlists</h3>
              {listings.slice(0, 6).map((item) => (
                <div key={item.id} className="list-tile">
                  <div className="row-between">
                    <div>
                      <p className="title-sm">{item.name}</p>
                      <p className="caption-muted">${item.price}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => handlePlaylistPay(item.id)}>
                      Pay
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {tab === 'buy' && (
          <section className="simple-section">
            <div className="card-surface">
              <h3 className="section-subtitle">Buy Music</h3>
              {listings.slice(0, 2).map((item) => (
                <div key={item.id} className="list-tile list-tile-spaced">
                  <p className="title-sm">{item.name}</p>
                  <p className="accent-caption">${item.price}</p>
                  <button className="btn btn-primary btn-block btn-top-gap" onClick={() => handlePlaylistPay(item.id)}>
                    Pay Now
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        <nav className="bottom-nav">
          <div className={`bottom-nav-grid ${tab === 'search' ? 'bottom-nav-grid-search' : 'bottom-nav-grid-default'}`}>
            {(tab === 'search'
              ? [
                  { id: 'home', label: 'Home', icon: 'home' },
                  { id: 'search', label: 'Search', icon: 'search' },
                  { id: 'library', label: 'Library', icon: 'library' },
                  { id: 'buy', label: 'Settings', icon: 'buy' },
                ]
              : [
                  { id: 'home', label: 'Home', icon: 'home' },
                  { id: 'search', label: 'Search', icon: 'search' },
                  { id: 'podcasts', label: 'Podcasts', icon: 'podcasts' },
                  { id: 'library', label: 'Library', icon: 'library' },
                  { id: 'buy', label: 'Buy', icon: 'buy' },
                ]).map((item) => (
              <button key={item.id} className="bottom-nav-item" onClick={() => setTab(item.id)}>
                <BottomIcon id={item.icon} active={tab === item.id} />
                <span className={`bottom-nav-label ${tab === item.id ? 'is-active' : ''}`}>{item.label}</span>
              </button>
            ))}
          </div>
        </nav>
      </div>
    </main>
  )
}




