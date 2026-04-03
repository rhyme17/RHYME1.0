from apps.desktop.windows.modules.scan_orchestration_service import ScanOrchestrationService


class _DummyWorker:
    def __init__(self, running):
        self._running = running

    def isRunning(self):
        return self._running


def test_should_cancel_running_worker_only_for_same_dialog():
    worker = _DummyWorker(True)
    dialog = object()

    assert ScanOrchestrationService.should_cancel_running_worker(worker, dialog, dialog) is True
    assert ScanOrchestrationService.should_cancel_running_worker(worker, dialog, object()) is False


def test_format_scan_failure_message_contains_reason():
    message = ScanOrchestrationService.format_scan_failure_message("bad path")
    assert "扫描音乐失败" in message
    assert "bad path" in message

