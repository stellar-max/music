// static/js/player.js
// Complete player logic with Socket.IO integration

// ============================================================
// 1. PLAYER STATE
// ============================================================
const audio = document.getElementById('audioPlayer');
const playBtn = document.getElementById('playBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const progressFill = document.getElementById('progressFill');
const progressContainer = document.getElementById('progressContainer');
const currentTimeEl = document.getElementById('currentTime');
const durationEl = document.getElementById('duration');
const volumeSlider = document.getElementById('volumeSlider');
const playerBar = document.getElementById('playerBar');
const playerTitle = document.getElementById('playerTitle');
const playerArtist = document.getElementById('playerArtist');
const playerCover = document.getElementById('playerCover');
const likeBtn = document.getElementById('likeBtn');

let currentTrack = null;
let currentTrackId = null;
let isPlaying = false;
let playlist = [];
let currentIndex = 0;

// ============================================================
// 2. PLAYER FUNCTIONS
// ============================================================

function playTrack(track, trackId, playlistData) {
    if (!track) return;
    
    currentTrack = track;
    currentTrackId = trackId;
    if (playlistData) playlist = playlistData;
    
    // Update UI
    playerTitle.textContent = track.title || 'Untitled';
    playerArtist.textContent = track.artist || 'Unknown Artist';
    playerCover.src = track.cover_url || track.cover_filename ? '/uploads/' + track.cover_filename : 'https://picsum.photos/200/200?random=' + trackId;
    
    audio.src = '/uploads/' + track.filename;
    audio.load();
    audio.play();
    
    playerBar.classList.remove('hidden');
    isPlaying = true;
    playBtn.innerHTML = '<i class="fas fa-pause text-lg"></i>';
    
    // Update like button
    updateLikeButton(track.is_liked || false);
    likeBtn.classList.remove('hidden');
    
    // Emit to socket if in room
    if (window.currentRoomId) {
        socket.emit('sync_playback', {
            room_id: window.currentRoomId,
            current_time: 0,
            is_playing: true
        });
    }
    
    // Count play
    fetch('/api/tracks/' + trackId + '/play', { method: 'POST' });
}

function togglePlay() {
    if (!currentTrack) return;
    
    if (audio.paused) {
        audio.play();
        isPlaying = true;
        playBtn.innerHTML = '<i class="fas fa-pause text-lg"></i>';
    } else {
        audio.pause();
        isPlaying = false;
        playBtn.innerHTML = '<i class="fas fa-play text-lg"></i>';
    }
    
    // Sync with room
    if (window.currentRoomId) {
        socket.emit('sync_playback', {
            room_id: window.currentRoomId,
            current_time: audio.currentTime,
            is_playing: !audio.paused
        });
    }
}

function toggleLike() {
    if (!currentTrackId) return;
    
    fetch('/api/tracks/' + currentTrackId + '/like', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                updateLikeButton(data.liked);
            } else if (data.auth_url) {
                window.open(data.auth_url, '_blank');
            }
        })
        .catch(e => console.error('Like error:', e));
}

function updateLikeButton(liked) {
    if (liked) {
        likeBtn.innerHTML = '<i class="fas fa-heart text-[#FF6B6B]"></i>';
        likeBtn.classList.add('text-[#FF6B6B]');
        likeBtn.classList.remove('text-gray-400');
    } else {
        likeBtn.innerHTML = '<i class="far fa-heart"></i>';
        likeBtn.classList.remove('text-[#FF6B6B]');
        likeBtn.classList.add('text-gray-400');
    }
}

function playNext() {
    if (playlist.length === 0) return;
    const nextIndex = (currentIndex + 1) % playlist.length;
    const track = playlist[nextIndex];
    if (track) {
        currentIndex = nextIndex;
        playTrack(track, track.id, playlist);
    }
}

function playPrev() {
    if (playlist.length === 0) return;
    const prevIndex = (currentIndex - 1 + playlist.length) % playlist.length;
    const track = playlist[prevIndex];
    if (track) {
        currentIndex = prevIndex;
        playTrack(track, track.id, playlist);
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return mins + ':' + (secs < 10 ? '0' : '') + secs;
}

function playTrackFromCard(trackId) {
    fetch('/api/tracks?id=' + trackId)
        .then(r => r.json())
        .then(tracks => {
            if (tracks.length > 0) {
                const track = tracks[0];
                fetch('/api/tracks')
                    .then(r => r.json())
                    .then(allTracks => {
                        const idx = allTracks.findIndex(t => t.id === trackId);
                        if (idx !== -1) {
                            currentIndex = idx;
                            playTrack(track, trackId, allTracks);
                        } else {
                            playTrack(track, trackId, [track]);
                        }
                    });
            }
        })
        .catch(e => console.error('Play error:', e));
}

function copyShareLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        alert('Link copied to clipboard!');
    }).catch(() => {
        prompt('Copy this link:', url);
    });
}

function addToQueue(trackId) {
    if (!window.currentRoomId) {
        alert('Join a room first to add to queue!');
        return;
    }
    socket.emit('add_to_queue', {
        room_id: window.currentRoomId,
        track_id: trackId
    });
}

function logout() {
    fetch('/api/auth/logout', { method: 'POST' })
        .then(() => location.reload())
        .catch(() => location.reload());
}

// ============================================================
// 3. EVENT LISTENERS
// ============================================================

// Play/Pause
playBtn.addEventListener('click', togglePlay);

// Audio Events
audio.addEventListener('timeupdate', function() {
    if (audio.duration) {
        const percent = (audio.currentTime / audio.duration) * 100;
        progressFill.style.width = percent + '%';
        currentTimeEl.textContent = formatTime(audio.currentTime);
    }
});

audio.addEventListener('loadedmetadata', function() {
    durationEl.textContent = formatTime(audio.duration);
});

audio.addEventListener('ended', function() {
    playNext();
});

// Progress Bar
progressContainer.addEventListener('click', function(e) {
    if (!audio.duration) return;
    const rect = this.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audio.currentTime = percent * audio.duration;
});

// Volume
volumeSlider.addEventListener('input', function() {
    audio.volume = this.value;
});

// Like
likeBtn.addEventListener('click', toggleLike);

// Next/Prev
nextBtn.addEventListener('click', playNext);
prevBtn.addEventListener('click', playPrev);

// ============================================================
// 4. KEYBOARD SHORTCUTS
// ============================================================

document.addEventListener('keydown', function(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
    }
    if (e.code === 'ArrowRight') {
        audio.currentTime = Math.min(audio.currentTime + 5, audio.duration || 0);
    }
    if (e.code === 'ArrowLeft') {
        audio.currentTime = Math.max(audio.currentTime - 5, 0);
    }
});

// ============================================================
// 5. SOCKET.IO - ROOM SYNC
// ============================================================

const socket = io();

socket.on('connect', function() {
    console.log('Socket connected');
    if (window.currentRoomId) {
        socket.emit('join_room', { room_id: window.currentRoomId });
    }
});

socket.on('room_state', function(data) {
    console.log('Room state:', data);
    if (data.current_track) {
        const track = data.current_track;
        playerTitle.textContent = track.title;
        playerArtist.textContent = track.artist;
        playerCover.src = track.cover_filename ? '/uploads/' + track.cover_filename : 'https://picsum.photos/200/200';
        audio.src = '/uploads/' + track.filename;
        audio.currentTime = data.current_time || 0;
        if (data.is_playing) {
            audio.play();
            playBtn.innerHTML = '<i class="fas fa-pause text-lg"></i>';
        }
        playerBar.classList.remove('hidden');
    }
});

socket.on('queue_updated', function(queue) {
    console.log('Queue updated:', queue);
    const queueContainer = document.getElementById('queueList');
    if (queueContainer) {
        queueContainer.innerHTML = queue.map((item, idx) => 
            `<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition">
                <span class="text-gray-400 text-sm">${idx + 1}</span>
                <span class="text-white text-sm truncate flex-1">${item.title}</span>
                <span class="text-gray-400 text-xs">${item.artist}</span>
            </div>`
        ).join('');
    }
});

socket.on('track_changed', function(data) {
    console.log('Track changed:', data);
    if (data.track) {
        playTrack(data.track, data.track.id, []);
        if (data.current_time) audio.currentTime = data.current_time;
        if (data.is_playing) {
            audio.play();
            playBtn.innerHTML = '<i class="fas fa-pause text-lg"></i>';
        }
    }
});

socket.on('playback_sync', function(data) {
    console.log('Playback sync:', data);
    audio.currentTime = data.current_time;
    if (data.is_playing && audio.paused) {
        audio.play();
        playBtn.innerHTML = '<i class="fas fa-pause text-lg"></i>';
    } else if (!data.is_playing && !audio.paused) {
        audio.pause();
        playBtn.innerHTML = '<i class="fas fa-play text-lg"></i>';
    }
});

socket.on('telegram_play', function(data) {
    console.log('Telegram play request:', data);
    // Search and play the song
    fetch('/api/tracks?search=' + encodeURIComponent(data.song))
        .then(r => r.json())
        .then(tracks => {
            if (tracks.length > 0) {
                playTrack(tracks[0], tracks[0].id, tracks);
            }
        });
});

// ============================================================
// 6. UPLOAD FORM HANDLER
// ============================================================

document.getElementById('uploadForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    
    fetch('/api/tracks', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('Track uploaded successfully!');
            location.reload();
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(e => alert('Upload failed: ' + e.message));
});

// ============================================================
// 7. TAB SWITCHING
// ============================================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active', 'bg-[#6C63FF]/20', 'text-white'));
        this.classList.add('active', 'bg-[#6C63FF]/20', 'text-white');
        
        const tab = this.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
        document.getElementById(tab + '-tab').classList.remove('hidden');
    });
});

// ============================================================
// 8. EXPOSE GLOBALLY
// ============================================================

window.playTrackFromCard = playTrackFromCard;
window.togglePlay = togglePlay;
window.toggleLike = toggleLike;
window.playNext = playNext;
window.playPrev = playPrev;
window.addToQueue = addToQueue;
window.copyShareLink = copyShareLink;
window.logout = logout;

console.log('🎵 swagPlayer loaded successfully!');
