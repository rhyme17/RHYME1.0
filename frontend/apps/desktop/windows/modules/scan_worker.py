from PyQt5.QtCore import QThread, pyqtSignal
import time

try:
    from frontend.apps.desktop.windows.modules.scan_progress_throttle import ScanProgressThrottle
except ModuleNotFoundError:
    from apps.desktop.windows.modules.scan_progress_throttle import ScanProgressThrottle


class ScanWorker(QThread):
    finished = pyqtSignal(bool, bool, str)
    progress = pyqtSignal(int, int)

    def __init__(self, library, directory):
        super().__init__()
        self.library = library
        self.directory = directory

    def run(self):
        throttle = ScanProgressThrottle()

        def _on_progress(scanned, total):
            scanned_i = int(scanned)
            total_i = int(total)
            now = time.monotonic()
            if not throttle.should_emit(scanned_i, total_i, now):
                return
            throttle.mark_emitted(scanned_i, now)
            self.progress.emit(scanned_i, total_i)

        success = self.library.scan_music(
            self.directory,
            should_stop=self.isInterruptionRequested,
            on_progress=_on_progress,
        )
        cancelled = bool(getattr(self.library, "last_scan_cancelled", False)) or self.isInterruptionRequested()
        error_message = str(getattr(self.library, "last_scan_error", "") or "")
        self.finished.emit(success, cancelled, error_message)

