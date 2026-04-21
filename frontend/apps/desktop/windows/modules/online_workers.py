from PyQt5.QtCore import QThread, pyqtSignal


class OnlineSearchWorker(QThread):
    finished_with_result = pyqtSignal(bool, list, str)

    def __init__(self, online_service, keyword, source="netease", count=20, parent=None):
        super().__init__(parent)
        self.online_service = online_service
        self.keyword = str(keyword or "").strip()
        self.source = source
        self.count = count

    def run(self):
        if not self.keyword:
            self.finished_with_result.emit(False, [], "搜索关键词不能为空")
            return
        try:
            results = self.online_service.search(self.keyword, self.source, self.count)
            songs_data = []
            for song in results:
                songs_data.append({
                    "id": song.id,
                    "name": song.name,
                    "artist": song.artist,
                    "album": song.album,
                    "source": song.source,
                    "url_id": song.url_id,
                    "pic_id": song.pic_id,
                    "lyric_id": song.lyric_id,
                })
            self.finished_with_result.emit(True, songs_data, "")
        except Exception as exc:
            self.finished_with_result.emit(False, [], f"搜索失败: {exc}")


class OnlineDownloadWorker(QThread):
    progress_updated = pyqtSignal(str, float)
    finished_with_result = pyqtSignal(bool, str, str, str)

    def __init__(self, online_service, song_data, save_dir, parent=None):
        super().__init__(parent)
        self.online_service = online_service
        self.song_data = dict(song_data)
        self.save_dir = save_dir

    def run(self):
        from frontend.core.online_music_service import OnlineSong

        song = OnlineSong(
            id=self.song_data.get("id", ""),
            name=self.song_data.get("name", ""),
            artist=self.song_data.get("artist", ""),
            album=self.song_data.get("album", ""),
            source=self.song_data.get("source", "netease"),
            url_id=self.song_data.get("url_id", ""),
            pic_id=self.song_data.get("pic_id", ""),
            lyric_id=self.song_data.get("lyric_id", ""),
        )

        def on_progress(progress):
            self.progress_updated.emit(song.id, progress)

        try:
            task = self.online_service.download_song(song, self.save_dir, on_progress)
            if task.status == "completed":
                self.finished_with_result.emit(
                    True, song.id, task.save_path, ""
                )
            else:
                self.finished_with_result.emit(
                    False, song.id, "", task.error or "下载失败"
                )
        except Exception as exc:
            self.finished_with_result.emit(False, song.id, "", f"下载异常: {exc}")


class NetworkCheckWorker(QThread):
    finished_with_result = pyqtSignal(bool)

    def __init__(self, online_service, parent=None):
        super().__init__(parent)
        self.online_service = online_service

    def run(self):
        available = self.online_service.check_network()
        self.finished_with_result.emit(available)
