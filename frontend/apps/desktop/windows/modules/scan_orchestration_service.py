import os


class ScanOrchestrationService:
    @staticmethod
    def resolve_directory(preferred_directory, choose_directory_callable, set_directory_callable=None):
        directory = str(preferred_directory or "").strip()
        if not directory and callable(choose_directory_callable):
            selected = choose_directory_callable()
            directory = str(selected or "").strip()
            if directory and callable(set_directory_callable):
                set_directory_callable(directory)
        return directory

    @staticmethod
    def is_valid_directory(directory):
        return bool(directory) and os.path.isdir(directory)

    @staticmethod
    def should_cancel_running_worker(scan_worker, active_dialog, incoming_dialog):
        if not scan_worker or not scan_worker.isRunning():
            return False
        return active_dialog is incoming_dialog

    @staticmethod
    def format_scan_failure_message(error_message):
        reason = str(error_message or "").strip()
        return f"扫描音乐失败\n\n原因：{reason}" if reason else "扫描音乐失败"

