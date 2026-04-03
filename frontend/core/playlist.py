import json
import os
import re

try:
    from frontend.utils.import_compat import load_attr
except ModuleNotFoundError:
    from utils.import_compat import load_attr


backup_corrupted_file = load_attr(
    ["frontend.utils.json_recovery", "utils.json_recovery"],
    "backup_corrupted_file",
)
atomic_write_json = load_attr(
    ["frontend.utils.json_io", "utils.json_io"],
    "atomic_write_json",
)
get_logger = load_attr(
    ["frontend.utils.logging_utils", "utils.logging_utils"],
    "get_logger",
)


MAX_CORRUPT_PLAYLIST_BACKUPS = 10
logger = get_logger(__name__)


def _atomic_write_json(file_path, data):
    return atomic_write_json(file_path, data)


class PlaylistManager:
    def __init__(self):
        self.playlists = {}
        self.current_playlist_name = None
        self.create_playlist("默认播放列表", [], set_current=True)

    def get_default_playlist_name(self, folder_path):
        """根据文件夹路径生成默认歌单名"""
        if not folder_path:
            return "默认播放列表"
        normalized = os.path.abspath(folder_path)
        default_name = os.path.basename(normalized)
        return default_name or "默认播放列表"

    def has_playlist(self, name):
        return name in self.playlists

    def list_playlist_names(self):
        return list(self.playlists.keys())

    def create_playlist(self, name, songs=None, set_current=True, overwrite=False):
        """创建歌单，可选覆盖已有歌单"""
        name = (name or "").strip() or "默认播放列表"
        if name in self.playlists and not overwrite:
            return False

        songs = songs or []
        self.playlists[name] = self._dedupe_songs(songs)
        if set_current or self.current_playlist_name is None:
            self.current_playlist_name = name
        return True

    def create_playlist_from_folder(self, folder_path, songs, playlist_name=None, overwrite=False, set_current=True):
        """根据扫描目录创建歌单，默认名使用目录名"""
        target_name = (playlist_name or "").strip() or self.get_default_playlist_name(folder_path)
        return self.create_playlist(target_name, songs=songs, set_current=set_current, overwrite=overwrite)

    def select_playlist(self, name):
        if name not in self.playlists:
            return False
        self.current_playlist_name = name
        return True

    def rename_playlist(self, old_name, new_name):
        old_name = (old_name or "").strip()
        new_name = (new_name or "").strip() or "默认播放列表"
        if old_name not in self.playlists or new_name in self.playlists:
            return False
        self.playlists[new_name] = self.playlists.pop(old_name)
        if self.current_playlist_name == old_name:
            self.current_playlist_name = new_name
        return True

    def delete_playlist(self, name):
        if name not in self.playlists:
            return False
        del self.playlists[name]
        if not self.playlists:
            self.create_playlist("默认播放列表", [], set_current=True)
            return True
        if self.current_playlist_name == name:
            self.current_playlist_name = next(iter(self.playlists))
        return True

    def add_song_to_playlist(self, playlist_name, song):
        if playlist_name not in self.playlists:
            return False
        if not isinstance(song, dict):
            return False
        playlist = self.playlists[playlist_name]
        song_id = song.get("id")
        if not song_id:
            return False
        for existing_song in playlist:
            if existing_song.get("id") == song_id:
                return False
        playlist.append(self._sanitize_song(song))
        return True

    def remove_song_from_playlist(self, playlist_name, song_id):
        if playlist_name not in self.playlists:
            return False
        playlist = self.playlists[playlist_name]
        for index, song in enumerate(playlist):
            if song.get("id") == song_id:
                del playlist[index]
                return True
        return False

    def clear_playlist(self, playlist_name):
        if playlist_name not in self.playlists:
            return False
        self.playlists[playlist_name] = []
        return True

    def save(self, path):
        """保存播放列表到文件"""
        try:
            playlist_data = {
                "version": 2,
                "current_playlist": self.current_playlist_name,
                "playlists": [
                    {
                        "name": name,
                        "songs": [self._sanitize_song(song) for song in songs],
                    }
                    for name, songs in self.playlists.items()
                ],
            }

            _atomic_write_json(path, playlist_data)
            return True
        except Exception as e:
            logger.exception("保存播放列表失败: %s", str(e))
            return False
    
    def load(self, path):
        """从文件加载播放列表"""
        try:
            if not os.path.exists(path):
                return False

            with open(path, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)

            if not isinstance(playlist_data, dict):
                raise ValueError("播放列表文件结构无效")

            parsed_playlists = {}
            parsed_current = None

            if 'playlists' in playlist_data:
                for item in playlist_data.get('playlists', []):
                    if not isinstance(item, dict):
                        continue
                    name = (item.get('name') or '').strip() or '默认播放列表'
                    songs = item.get('songs', [])
                    parsed_playlists[name] = self._dedupe_songs(songs)
                if not parsed_playlists:
                    parsed_playlists = {'默认播放列表': []}
                current = playlist_data.get('current_playlist')
                if current in parsed_playlists:
                    parsed_current = current
                else:
                    parsed_current = next(iter(parsed_playlists))
            else:
                # 兼容旧格式: 仅包含 name + songs
                name = (playlist_data.get('name') or '').strip() or '默认播放列表'
                songs = playlist_data.get('songs', [])
                parsed_playlists = {name: self._dedupe_songs(songs)}
                parsed_current = name

            self.playlists = parsed_playlists
            self.current_playlist_name = parsed_current
            return True
        except Exception as e:
            logger.exception("加载播放列表失败: %s", str(e))
            self._backup_corrupted_file(path)
            self._reset_to_default_playlist()
            return False

    def _reset_to_default_playlist(self):
        self.playlists = {}
        self.current_playlist_name = None
        self.create_playlist('默认播放列表', [], set_current=True)

    def _backup_corrupted_file(self, path):
        return backup_corrupted_file(path, keep_latest=MAX_CORRUPT_PLAYLIST_BACKUPS)

    def _prune_corrupted_backups(self, directory, filename, keep_latest=10):
        # 保留旧方法壳，避免潜在外部调用；当前逻辑已委托到共享工具。
        return

    def get_playlist(self):
        """获取当前歌单歌曲"""
        if self.current_playlist_name not in self.playlists:
            return []
        return self.playlists[self.current_playlist_name]

    def get_playlist_length(self):
        """获取播放列表长度"""
        return len(self.get_playlist())

    def set_playlist_name(self, name):
        """设置当前歌单名称（兼容旧接口）"""
        return self.rename_playlist(self.current_playlist_name, name)

    def get_playlist_name(self):
        """获取当前歌单名称"""
        return self.current_playlist_name

    # ---- 旧接口兼容层 ----
    def add_song(self, song):
        return self.add_song_to_playlist(self.current_playlist_name, song)

    def remove_song(self, song_id):
        return self.remove_song_from_playlist(self.current_playlist_name, song_id)

    def clear(self):
        return self.clear_playlist(self.current_playlist_name)


    # ---- 内部工具 ----
    def _sanitize_song(self, song):
        if not isinstance(song, dict):
            return {
                'id': '',
                'title': '',
                'artist': '未知艺术家',
                'album': '',
                'path': '',
                'duration': 0,
            }
        path = song.get('path', '')
        artist = song.get('artist', '未知艺术家')
        return {
            'id': song.get('id', ''),
            'title': self._title_from_path(path, song.get('title', ''), artist),
            'artist': artist,
            'album': song.get('album', ''),
            'path': path,
            'duration': song.get('duration', 0),
        }

    @staticmethod
    def _title_from_path(path, fallback='', artist=''):
        raw_path = str(path or '').strip()
        raw_fallback = str(fallback or '').strip()
        if raw_path:
            title = os.path.splitext(os.path.basename(raw_path))[0].strip()
            if title:
                return PlaylistManager._strip_artist_from_title(title, artist)
        return PlaylistManager._strip_artist_from_title(raw_fallback, artist)

    @staticmethod
    def _strip_artist_from_title(title, artist):
        raw_title = str(title or '').strip()
        if not raw_title:
            return raw_title

        artist_tokens = PlaylistManager._artist_tokens(artist)
        if not artist_tokens:
            return raw_title

        parts = [p.strip() for p in re.split(r"\s*[-_–—|]+\s*", raw_title) if p.strip()]
        if len(parts) <= 1:
            return raw_title

        remaining = [p for p in parts if not PlaylistManager._is_artist_text(p, artist_tokens)]
        if not remaining or len(remaining) == len(parts):
            return raw_title
        return " - ".join(remaining).strip() or raw_title

    @staticmethod
    def _artist_tokens(artist):
        raw = str(artist or '').strip()
        if not raw:
            return []
        chunks = [c.strip() for c in re.split(r"[/,，;&、]", raw) if c.strip()]
        tokens = []
        for item in chunks:
            normalized = PlaylistManager._normalize_for_compare(item)
            if normalized:
                tokens.append(normalized)
        return tokens

    @staticmethod
    def _normalize_for_compare(text):
        return ''.join(ch.lower() for ch in str(text or '') if ch.isalnum() or ('\u4e00' <= ch <= '\u9fff'))

    @staticmethod
    def _is_artist_text(text, artist_tokens):
        normalized = PlaylistManager._normalize_for_compare(text)
        if not normalized:
            return False
        for token in artist_tokens:
            if not token:
                continue
            if normalized == token:
                return True
            if token in normalized or normalized in token:
                return True
        return False

    def _dedupe_songs(self, songs):
        deduped = []
        seen_ids = set()
        for song in songs or []:
            safe_song = self._sanitize_song(song)
            song_id = safe_song.get('id')
            if not song_id or song_id in seen_ids:
                continue
            seen_ids.add(song_id)
            deduped.append(safe_song)
        return deduped
