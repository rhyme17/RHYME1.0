from apps.desktop.windows.modules.scan_progress_throttle import ScanProgressThrottle


def test_should_emit_when_completed_even_without_delta_or_interval():
    throttle = ScanProgressThrottle(min_emit_interval_seconds=10, min_emit_delta=100)

    assert throttle.should_emit(5, 5, now=0.01) is True


def test_should_emit_when_delta_reaches_threshold():
    throttle = ScanProgressThrottle(min_emit_interval_seconds=10, min_emit_delta=3)
    throttle.mark_emitted(scanned=1, now=1.0)

    assert throttle.should_emit(4, 10, now=1.01) is True


def test_should_emit_when_time_reaches_threshold():
    throttle = ScanProgressThrottle(min_emit_interval_seconds=0.1, min_emit_delta=100)
    throttle.mark_emitted(scanned=1, now=1.0)

    assert throttle.should_emit(2, 10, now=1.11) is True
    assert throttle.should_emit(2, 10, now=1.05) is False

