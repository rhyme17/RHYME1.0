import os
import requests


TONZHON_API = "https://tonzhon.com/api.php"
TONZHON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://tonzhon.com/",
    "Accept": "*/*",
}


class OnlineSong:
    def __init__(self, id, name, artist, album, source, url_id="", pic_id="", lyric_id=""):
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album
        self.source = source
        self.url_id = url_id
        self.pic_id = pic_id
        self.lyric_id = lyric_id


class DownloadTask:
    def __init__(self, song, save_path="", lyric_path="", progress=0.0, status="pending", error=""):
        self.song = song
        self.save_path = save_path
        self.lyric_path = lyric_path
        self.progress = progress
        self.status = status
        self.error = error


class OnlineMusicService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(TONZHON_HEADERS)
        self._network_available = True

    def check_network(self) -> bool:
        try:
            resp = requests.get(TONZHON_API, headers=TONZHON_HEADERS, timeout=5)
            self._network_available = resp.status_code == 200
        except Exception:
            self._network_available = False
        return self._network_available

    @property
    def is_network_available(self) -> bool:
        return self._network_available

    def search(self, keyword, source="netease", count=20, page=1):
        try:
            resp = requests.get(
                TONZHON_API,
                params={
                    "types": "search",
                    "count": count,
                    "source": source,
                    "pages": page,
                    "name": keyword,
                },
                headers=TONZHON_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise OnlineMusicError(f"搜索失败: {e}") from e

        if not isinstance(data, list):
            raise OnlineMusicError("搜索返回数据格式异常")

        results = []
        for item in data:
            artist = self._parse_artist(item.get("artist", []))
            results.append(OnlineSong(
                id=str(item.get("id", "")),
                name=item.get("name", ""),
                artist=artist,
                album=item.get("album", ""),
                source=item.get("source", source),
                url_id=str(item.get("url_id", "")),
                pic_id=str(item.get("pic_id", "")),
                lyric_id=str(item.get("lyric_id", "")),
            ))
        return results

    def get_song_url(self, song_id, source="netease"):
        try:
            resp = requests.get(
                TONZHON_API,
                params={"types": "url", "id": song_id, "source": source},
                headers=TONZHON_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise OnlineMusicError(f"获取歌曲链接失败: {e}") from e

        url = data.get("url", "")
        if not url and source == "netease":
            url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"

        if not url:
            raise OnlineMusicError("无法获取歌曲播放链接")
        return url

    def get_lyric(self, lyric_id, source="netease"):
        try:
            resp = requests.get(
                TONZHON_API,
                params={"types": "lyric", "id": lyric_id, "source": source},
                headers=TONZHON_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise OnlineMusicError(f"获取歌词失败: {e}") from e

        return data.get("lyric", "")

    def download_song(self, song, save_dir, on_progress=None):
        task = DownloadTask(song=song)

        safe_name = self._sanitize_filename(f"{song.artist} - {song.name}")
        task.save_path = os.path.join(save_dir, f"{safe_name}.mp3")
        task.lyric_path = os.path.join(save_dir, f"{safe_name}.lrc")

        os.makedirs(save_dir, exist_ok=True)

        try:
            song_url = self.get_song_url(song.id, song.source)
        except OnlineMusicError as e:
            task.status = "failed"
            task.error = str(e)
            return task

        try:
            resp = requests.get(song_url, stream=True, headers=TONZHON_HEADERS, timeout=30)
            resp.raise_for_status()

            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(task.save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and on_progress:
                            on_progress(downloaded / total_size)

            task.progress = 1.0
        except Exception as e:
            task.status = "failed"
            task.error = f"下载失败: {e}"
            if os.path.exists(task.save_path):
                os.remove(task.save_path)
            return task

        try:
            lyric = self.get_lyric(song.lyric_id or song.id, song.source)
            if lyric:
                with open(task.lyric_path, "w", encoding="utf-8") as f:
                    f.write(lyric)
        except Exception:
            pass

        task.status = "completed"
        return task

    def _parse_artist(self, artist_data):
        if isinstance(artist_data, list):
            if len(artist_data) > 0 and isinstance(artist_data[0], list):
                return "/".join([a[0] for a in artist_data if a])
            elif len(artist_data) > 0:
                return "/".join(str(a) for a in artist_data)
        return str(artist_data) if artist_data else "未知艺术家"

    def _sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename[:200]


class OnlineMusicError(Exception):
    pass
