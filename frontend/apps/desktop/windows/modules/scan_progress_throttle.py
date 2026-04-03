class ScanProgressThrottle:
    def __init__(self, *, min_emit_interval_seconds=0.1, min_emit_delta=20):
        self.min_emit_interval_seconds = float(min_emit_interval_seconds)
        self.min_emit_delta = int(min_emit_delta)
        self.last_emit_time = 0.0
        self.last_emit_scanned = 0

    def should_emit(self, scanned, total, now):
        scanned_i = int(scanned)
        total_i = int(total)
        now_f = float(now)
        return (
            scanned_i >= total_i
            or (scanned_i - self.last_emit_scanned) >= self.min_emit_delta
            or (now_f - self.last_emit_time) >= self.min_emit_interval_seconds
        )

    def mark_emitted(self, scanned, now):
        self.last_emit_scanned = int(scanned)
        self.last_emit_time = float(now)

