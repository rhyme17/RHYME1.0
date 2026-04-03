// API基础URL
const API_BASE = 'http://localhost:5000/api';

// 全局变量
let currentSong = null;
let isPlaying = false;
let currentTime = 0;
let duration = 0;
let audioElement = null;

// 页面加载完成后执行
window.onload = function() {
    // 初始化事件监听器
    initEventListeners();
    // 初始化标签页切换
    initTabs();
    // 加载播放状态
    loadPlaybackStatus();
};

// 初始化事件监听器
function initEventListeners() {
    // 扫描按钮
    document.getElementById('scan-btn').addEventListener('click', function() {
        const directory = document.getElementById('directory-input').value || '.';
        scanMusic(directory);
    });

    // 搜索按钮
    document.getElementById('search-btn').addEventListener('click', function() {
        const query = document.getElementById('search-input').value;
        searchMusic(query);
    });

    // 清空播放列表
    document.getElementById('clear-playlist').addEventListener('click', function() {
        clearPlaylist();
    });

    // 播放控制按钮
    document.getElementById('play-btn').addEventListener('click', function() {
        togglePlay();
    });

    document.getElementById('prev-btn').addEventListener('click', function() {
        playPrevious();
    });

    document.getElementById('next-btn').addEventListener('click', function() {
        playNext();
    });

    // 音量控制
    document.getElementById('volume-slider').addEventListener('input', function() {
        const volume = parseInt(this.value);
        setVolume(volume);
        if (audioElement) {
            audioElement.volume = volume / 100;
        }
    });

    // 静音按钮
    document.getElementById('mute-btn').addEventListener('click', function() {
        if (audioElement) {
            audioElement.muted = !audioElement.muted;
            this.textContent = audioElement.muted ? '🔇' : '🔊';
        }
    });

    // 播放模式切换
    document.getElementById('mode-btn').addEventListener('click', function() {
        const modes = ['顺序播放', '随机播放', '单曲循环'];
        const currentMode = this.textContent;
        const currentIndex = modes.indexOf(currentMode);
        const nextIndex = (currentIndex + 1) % modes.length;
        const newMode = modes[nextIndex];
        this.textContent = newMode;
        setPlaybackMode(newMode);
    });

    // 进度条点击
    document.getElementById('progress-bar').addEventListener('click', function(e) {
        if (audioElement) {
            const rect = this.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percentage = clickX / rect.width;
            const newTime = percentage * duration;
            audioElement.currentTime = newTime;
            updateProgress(newTime);
        }
    });
}

// 初始化标签页切换
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有标签页的活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // 添加当前标签页的活动状态
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            // 如果切换到艺术家或专辑标签，加载对应数据
            if (tabId === 'artists') {
                loadArtists();
            } else if (tabId === 'albums') {
                loadAlbums();
            }
        });
    });
}

// 扫描音乐
function scanMusic(directory) {
    fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ directory: directory })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`扫描完成，找到 ${data.count} 首音乐`);
            loadMusicLibrary();
        }
    })
    .catch(error => {
        console.error('扫描音乐失败:', error);
        alert('扫描音乐失败，请检查后端服务是否运行');
    });
}

// 加载音乐库
function loadMusicLibrary() {
    fetch(`${API_BASE}/library`)
    .then(response => response.json())
    .then(data => {
        renderSongList(data);
    })
    .catch(error => {
        console.error('加载音乐库失败:', error);
    });
}

// 搜索音乐
function searchMusic(query) {
    fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        renderSongList(data);
    })
    .catch(error => {
        console.error('搜索音乐失败:', error);
    });
}

// 加载艺术家列表
function loadArtists() {
    fetch(`${API_BASE}/categories`)
    .then(response => response.json())
    .then(data => {
        renderArtistsList(data.artists);
    })
    .catch(error => {
        console.error('加载艺术家列表失败:', error);
    });
}

// 加载专辑列表
function loadAlbums() {
    fetch(`${API_BASE}/categories`)
    .then(response => response.json())
    .then(data => {
        renderAlbumsList(data.albums);
    })
    .catch(error => {
        console.error('加载专辑列表失败:', error);
    });
}

// 渲染歌曲列表
function renderSongList(songs) {
    const songList = document.getElementById('all-songs');
    songList.innerHTML = '';
    
    songs.forEach(song => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="song-info">
                <div class="song-title">${song.title}</div>
                <div class="song-artist">${song.artist} - ${song.album}</div>
            </div>
            <div class="song-duration">${formatTime(song.duration)}</div>
        `;
        
        // 点击播放歌曲
        li.addEventListener('click', function() {
            playSong(song.id);
        });
        
        // 右键菜单
        li.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            addToPlaylist(song.id);
        });
        
        songList.appendChild(li);
    });
}

// 渲染艺术家列表
function renderArtistsList(artists) {
    const artistList = document.getElementById('artists');
    artistList.innerHTML = '';
    
    Object.keys(artists).forEach(artist => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>${artist}</div>
            <div>${artists[artist].length} 首歌曲</div>
        `;
        
        li.addEventListener('click', function() {
            renderSongList(artists[artist]);
        });
        
        artistList.appendChild(li);
    });
}

// 渲染专辑列表
function renderAlbumsList(albums) {
    const albumList = document.getElementById('albums');
    albumList.innerHTML = '';
    
    Object.keys(albums).forEach(album => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>${album}</div>
            <div>${albums[album].length} 首歌曲</div>
        `;
        
        li.addEventListener('click', function() {
            renderSongList(albums[album]);
        });
        
        albumList.appendChild(li);
    });
}

// 加载播放列表
function loadPlaylist() {
    fetch(`${API_BASE}/playlist`)
    .then(response => response.json())
    .then(data => {
        renderPlaylist(data);
    })
    .catch(error => {
        console.error('加载播放列表失败:', error);
    });
}

// 渲染播放列表
function renderPlaylist(songs) {
    const playlist = document.getElementById('playlist');
    playlist.innerHTML = '';
    
    songs.forEach((song, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="song-info">
                <div class="song-title">${song.title}</div>
                <div class="song-artist">${song.artist}</div>
            </div>
            <div class="song-duration">${formatTime(song.duration)}</div>
        `;
        
        // 点击播放歌曲
        li.addEventListener('click', function() {
            playSong(song.id);
        });
        
        playlist.appendChild(li);
    });
}

// 添加到播放列表
function addToPlaylist(songId) {
    fetch(`${API_BASE}/playlist`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ song_id: songId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadPlaylist();
        }
    })
    .catch(error => {
        console.error('添加到播放列表失败:', error);
    });
}

// 清空播放列表
function clearPlaylist() {
    fetch(`${API_BASE}/playlist/clear`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadPlaylist();
        }
    })
    .catch(error => {
        console.error('清空播放列表失败:', error);
    });
}

// 播放歌曲
function playSong(songId) {
    fetch(`${API_BASE}/play/${songId}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.song) {
            currentSong = data.song;
            updateCurrentSongDisplay();
            
            // 创建音频元素
            if (audioElement) {
                audioElement.pause();
                audioElement.src = '';
            }
            
            audioElement = new Audio(data.song.path);
            audioElement.volume = document.getElementById('volume-slider').value / 100;
            
            // 音频事件监听
            audioElement.addEventListener('play', function() {
                isPlaying = true;
                document.getElementById('play-btn').textContent = '⏸';
            });
            
            audioElement.addEventListener('pause', function() {
                isPlaying = false;
                document.getElementById('play-btn').textContent = '▶';
            });
            
            audioElement.addEventListener('ended', function() {
                playNext();
            });
            
            audioElement.addEventListener('timeupdate', function() {
                updateProgress(this.currentTime);
            });
            
            audioElement.addEventListener('loadedmetadata', function() {
                duration = this.duration;
                document.getElementById('total-time').textContent = formatTime(duration);
            });
            
            audioElement.play();
        }
    })
    .catch(error => {
        console.error('播放歌曲失败:', error);
    });
}

// 切换播放/暂停
function togglePlay() {
    if (audioElement) {
        if (isPlaying) {
            audioElement.pause();
        } else {
            audioElement.play();
        }
    } else {
        // 如果没有音频元素，尝试播放当前播放列表的第一首歌
        fetch(`${API_BASE}/playlist`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                playSong(data[0].id);
            }
        });
    }
}

// 播放上一首
function playPrevious() {
    fetch(`${API_BASE}/playback/control`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'prev' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.current_song) {
            currentSong = data.current_song;
            updateCurrentSongDisplay();
            if (audioElement) {
                audioElement.src = currentSong.path;
                audioElement.play();
            }
        }
    })
    .catch(error => {
        console.error('播放上一首失败:', error);
    });
}

// 播放下一首
function playNext() {
    fetch(`${API_BASE}/playback/control`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'next' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.current_song) {
            currentSong = data.current_song;
            updateCurrentSongDisplay();
            if (audioElement) {
                audioElement.src = currentSong.path;
                audioElement.play();
            }
        }
    })
    .catch(error => {
        console.error('播放下一首失败:', error);
    });
}

// 设置音量
function setVolume(volume) {
    fetch(`${API_BASE}/playback/volume`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ volume: volume })
    })
    .catch(error => {
        console.error('设置音量失败:', error);
    });
}

// 设置播放模式
function setPlaybackMode(mode) {
    fetch(`${API_BASE}/playback/mode`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ mode: mode })
    })
    .catch(error => {
        console.error('设置播放模式失败:', error);
    });
}

// 加载播放状态
function loadPlaybackStatus() {
    fetch(`${API_BASE}/playback/status`)
    .then(response => response.json())
    .then(data => {
        if (data.current_song) {
            currentSong = data.current_song;
            updateCurrentSongDisplay();
        }
        
        document.getElementById('mode-btn').textContent = data.mode;
        document.getElementById('volume-slider').value = data.volume;
        
        if (data.status === 'playing') {
            isPlaying = true;
            document.getElementById('play-btn').textContent = '⏸';
        } else {
            isPlaying = false;
            document.getElementById('play-btn').textContent = '▶';
        }
    })
    .catch(error => {
        console.error('加载播放状态失败:', error);
    });
}

// 更新当前歌曲显示
function updateCurrentSongDisplay() {
    if (currentSong) {
        document.getElementById('current-title').textContent = currentSong.title;
        document.getElementById('current-artist').textContent = currentSong.artist;
        document.getElementById('total-time').textContent = formatTime(currentSong.duration);
    }
}

// 更新进度条
function updateProgress(time) {
    currentTime = time;
    document.getElementById('current-time').textContent = formatTime(time);
    
    if (duration > 0) {
        const percentage = (time / duration) * 100;
        document.getElementById('progress-fill').style.width = `${percentage}%`;
    }
}

// 格式化时间
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

