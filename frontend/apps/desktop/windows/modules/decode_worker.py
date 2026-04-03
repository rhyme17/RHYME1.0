from PyQt5.QtCore import QThread, pyqtSignal


class DecodeWorker(QThread):
    finished = pyqtSignal(int, bool, object, str)

    def __init__(self, audio_player, file_path, request_id):
        super().__init__()
        self.audio_player = audio_player
        self.file_path = file_path
        self.request_id = int(request_id)

    def run(self):
        try:
            if self.isInterruptionRequested():
                self.finished.emit(self.request_id, False, None, "cancelled")
                return
            payload = self.audio_player.prepare_predecoded_audio(self.file_path)
            if self.isInterruptionRequested():
                self.finished.emit(self.request_id, False, None, "cancelled")
                return
            self.finished.emit(self.request_id, True, payload, "")
        except Exception as exc:
            self.finished.emit(self.request_id, False, None, str(exc))


