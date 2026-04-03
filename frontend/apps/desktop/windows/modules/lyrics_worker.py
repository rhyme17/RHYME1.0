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

    def __init__(self, lyrics_service, song, parent=None):
        super().__init__(parent)
        self.lyrics_service = lyrics_service
        self.song = dict(song)

    def run(self):
        song_id = self.song.get("id", "")
        try:
            success, output_path, error_message = self.lyrics_service.try_fetch_online_lrc(self.song)
        except Exception as exc:
            success = False
            output_path = ""
            error_message = f"歌词在线获取线程异常: {exc}"
        self.finished_with_result.emit(success, song_id, output_path, error_message)


