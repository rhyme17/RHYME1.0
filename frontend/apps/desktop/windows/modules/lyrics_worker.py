from PyQt5.QtCore import QThread, pyqtSignal


class LyricsAsrWorker(QThread):
    finished_with_result = pyqtSignal(bool, str, str, str)

    def __init__(self, lyrics_service, song, parent=None):
        super().__init__(parent)
        self.lyrics_service = lyrics_service
        self.song = dict(song)

    def run(self):
        song_id = self.song.get("id", "")
        try:
            success, output_path, error_message = self.lyrics_service.generate_lrc_with_asr(self.song)
        except Exception as exc:
            success = False
            output_path = ""
            error_message = f"歌词识别线程异常: {exc}"
        self.finished_with_result.emit(success, song_id, output_path, error_message)


class LyricsFetchWorker(QThread):
    finished_with_result = pyqtSignal(bool, str, str, str)

    def __init__(self, lyrics_service, song, query_title="", query_artist="", parent=None):
        super().__init__(parent)
        self.lyrics_service = lyrics_service
        self.song = dict(song)
        self.query_title = str(query_title or "").strip()
        self.query_artist = str(query_artist or "").strip()

    def run(self):
        song_id = self.song.get("id", "")
        try:
            success, output_path, error_message = self.lyrics_service.try_fetch_online_lrc(
                self.song,
                query_title=self.query_title,
                query_artist=self.query_artist,
            )
        except Exception as exc:
            success = False
            output_path = ""
            error_message = f"歌词在线获取线程异常: {exc}"
        self.finished_with_result.emit(success, song_id, output_path, error_message)


class LyricsFetchPreviewWorker(QThread):
    finished_with_result = pyqtSignal(bool, str, str)

    def __init__(self, lyrics_service, query_title="", query_artist="", parent=None):
        super().__init__(parent)
        self.lyrics_service = lyrics_service
        self.query_title = str(query_title or "").strip()
        self.query_artist = str(query_artist or "").strip()

    def run(self):
        try:
            success, lrc_text, error_message = self.lyrics_service.fetch_online_lrc_text(
                query_title=self.query_title,
                query_artist=self.query_artist,
            )
        except Exception as exc:
            success = False
            lrc_text = ""
            error_message = f"歌词在线获取线程异常: {exc}"
        self.finished_with_result.emit(success, lrc_text, error_message)


