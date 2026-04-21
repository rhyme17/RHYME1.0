class StatusNotifier:
    def __init__(self, status_bar_provider):
        self.status_bar_provider = status_bar_provider

    def show_status_hint(self, message, timeout_ms=2800):
        text = str(message or "").strip()
        if not text:
            return
        try:
            bar = self.status_bar_provider()
            if bar is not None:
                bar.showMessage(text, int(timeout_ms))
                return
        except Exception:
            pass

    def show_nonblocking_error(self, message, timeout_ms=4200):
        text = str(message or "").strip()
        if not text:
            return
        self.show_status_hint(f"提示：{text}", timeout_ms=timeout_ms)