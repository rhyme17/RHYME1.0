from PyQt5.QtWidgets import QFileDialog, QMessageBox

from frontend.apps.desktop.windows.modules.scan_orchestration_service import ScanOrchestrationService
from frontend.apps.desktop.windows.modules.scan_worker import ScanWorker
from frontend.utils.logging_utils import get_logger


logger = get_logger(__name__)


class ScanController:
    def __init__(self, owner):
        self.owner = owner

    def start_scan_from_dialog(self, dialog):
        owner = self.owner
        if ScanOrchestrationService.should_cancel_running_worker(
            owner.scan_worker,
            getattr(owner, "scan_dialog", None),
            dialog,
        ):
            self.cancel_scan_from_dialog(dialog)
            return

        if owner.scan_worker and owner.scan_worker.isRunning():
            QMessageBox.information(owner, "提示", "当前已有扫描任务在进行中")
            return

        directory = ScanOrchestrationService.resolve_directory(
            dialog.directory_input.text(),
            lambda: QFileDialog.getExistingDirectory(owner, "选择音乐文件夹"),
            dialog.directory_input.setText,
        )

        if not ScanOrchestrationService.is_valid_directory(directory):
            QMessageBox.warning(owner, "错误", "请选择有效的音乐文件夹")
            return
        if hasattr(owner, "_remember_last_scanned_directory"):
            owner._remember_last_scanned_directory(directory)
        else:
            owner.last_scanned_directory = directory
            if hasattr(owner, "schedule_save_app_settings"):
                owner.schedule_save_app_settings()
        dialog.set_scanning_state(True, "正在扫描，请稍候...")
        logger.info("开始扫描目录: %s", directory)

        worker = ScanWorker(owner.music_library, directory)
        owner.scan_worker = worker
        worker.progress.connect(lambda scanned, total: self.on_dialog_scan_progress(dialog, scanned, total))
        worker.finished.connect(
            lambda success, cancelled, error_message: self.on_dialog_scan_finished(
                dialog,
                success,
                cancelled,
                error_message,
            )
        )
        worker.start()

    def cancel_scan_from_dialog(self, dialog):
        owner = self.owner
        if not owner.scan_worker or not owner.scan_worker.isRunning():
            return
        if getattr(dialog, "is_cancelling", False):
            return
        logger.info("收到取消扫描请求")
        owner.scan_worker.requestInterruption()
        dialog.set_cancelling_state("正在取消扫描...")

    def on_dialog_scan_progress(self, dialog, scanned_count, total_count):
        if hasattr(dialog, "set_scan_progress"):
            dialog.set_scan_progress(scanned_count, total_count)

    def on_dialog_scan_finished(self, dialog, success, cancelled=False, error_message=""):
        owner = self.owner
        if owner.scan_worker:
            owner.scan_worker.deleteLater()
            owner.scan_worker = None

        if hasattr(dialog, "set_scanning_state"):
            dialog.set_scanning_state(False)

        if cancelled:
            if hasattr(dialog, "hint_label"):
                dialog.hint_label.setText("扫描已取消")
            logger.info("扫描已取消")
            return

        if not success:
            dialog.hint_label.setText("扫描失败，请检查目录后重试")
            logger.warning("扫描失败: %s", error_message or "unknown")
            if not getattr(owner, "_is_closing", False):
                QMessageBox.warning(owner, "错误", ScanOrchestrationService.format_scan_failure_message(error_message))
            return

        owner.repair_imported_song_text(show_message=False)
        songs = [dict(song) for song in owner.music_library.songs]
        owner.scan_results_cache = songs
        if hasattr(owner, "update_scan_cache_hint"):
            owner.update_scan_cache_hint()
        dialog.set_scan_results(songs)
        default_name = owner.playlist_manager.get_default_playlist_name(owner.last_scanned_directory)
        if hasattr(dialog, "new_playlist_input") and not dialog.new_playlist_input.text().strip():
            dialog.new_playlist_input.setText(default_name)
        dialog.set_playlist_names(
            owner.playlist_manager.list_playlist_names(),
            selected_name=owner.playlist_manager.get_playlist_name(),
        )
        owner.render_song_list(owner.music_library.songs)
        owner.update_artists_list()
        owner.update_albums_list()
        logger.info("扫描完成，曲目数: %s", len(songs))

