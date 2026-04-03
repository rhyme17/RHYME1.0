from types import SimpleNamespace

from core import player as player_module
from core.player import AudioPlayer
import time
import numpy as np


class DummyStream:
    def __init__(self):
        self.stopped = False
        self.closed = False

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


def test_pause_resume_state_machine_without_device():
    player = AudioPlayer()
    player.is_playing = True
    player.is_paused = False

    assert player.pause() is True
    assert player.is_paused is True

    assert player.resume() is True
    assert player.is_paused is False


def test_seek_clamps_to_valid_duration_range():
    player = AudioPlayer()
    player._sample_rate = 100
    player._total_frames = 1000
    player._duration_seconds = 10.0

    assert player.seek(12.5) is True
    assert player._position_frames == 1000

    assert player.seek(-5.0) is True
    assert player._position_frames == 0


def test_stop_resets_flags_and_closes_stream():
    player = AudioPlayer()
    dummy = DummyStream()
    player._stream = dummy
    player.is_playing = True
    player.is_paused = True
    player._position_frames = 123

    assert player.stop() is True
    assert player.is_playing is False
    assert player.is_paused is False
    assert player._position_frames == 0
    assert dummy.stopped is True
    assert dummy.closed is True
    assert player._stream is None


def test_recover_on_device_change_restarts_playback_from_current_position(monkeypatch):
    player = AudioPlayer()
    player.is_playing = True
    player.is_paused = False
    player.current_file = "D:/music/a.mp3"
    player._active_output_device_signature = (1, "old")

    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (2, "new"))
    monkeypatch.setattr(player, "get_position", lambda: 12.34)

    captured = {}

    def fake_play(file_path, start_position=0):
        captured["file_path"] = file_path
        captured["start_position"] = start_position
        return True

    monkeypatch.setattr(player, "play", fake_play)

    assert player.recover_on_device_change() is True
    assert captured["file_path"] == "D:/music/a.mp3"
    assert captured["start_position"] == 12340


def test_recover_on_device_change_restores_paused_state(monkeypatch):
    player = AudioPlayer()
    player.is_playing = True
    player.is_paused = True
    player.current_file = "D:/music/a.mp3"
    player._active_output_device_signature = (1, "old")

    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (2, "new"))
    monkeypatch.setattr(player, "get_position", lambda: 1.0)
    monkeypatch.setattr(player, "play", lambda *_args, **_kwargs: True)

    paused_called = {"value": False}

    def fake_pause():
        paused_called["value"] = True
        return True

    monkeypatch.setattr(player, "pause", fake_pause)

    assert player.recover_on_device_change() is True
    assert paused_called["value"] is True


def test_recover_on_device_change_is_throttled(monkeypatch):
    player = AudioPlayer()
    player.is_playing = True
    player.is_paused = False
    player.current_file = "D:/music/a.mp3"
    player._active_output_device_signature = (1, "old")
    player._last_recover_attempt_monotonic = time.monotonic()

    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (2, "new"))

    play_called = {"value": False}

    def fake_play(*_args, **_kwargs):
        play_called["value"] = True
        return True

    monkeypatch.setattr(player, "play", fake_play)

    assert player.recover_on_device_change() is False
    assert play_called["value"] is False


def test_recover_on_device_change_is_suppressed_temporarily_after_resume_start(monkeypatch):
    player = AudioPlayer()
    player.is_playing = True
    player.current_file = "D:/music/a.mp3"
    player._active_output_device_signature = (1, "old")
    player._suppress_recover_until_monotonic = time.monotonic() + 10.0

    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (2, "new"))

    play_called = {"value": False}

    def fake_play(*_args, **_kwargs):
        play_called["value"] = True
        return True

    monkeypatch.setattr(player, "play", fake_play)

    assert player.recover_on_device_change() is False
    assert play_called["value"] is False


def test_get_duration_hint_prefers_mutagen_metadata_without_full_decode(monkeypatch):
    player = AudioPlayer()

    monkeypatch.setattr(
        player_module,
        "MutagenFile",
        lambda _path: SimpleNamespace(info=SimpleNamespace(length=12.5)),
    )

    def _unexpected_decode(_path):
        raise AssertionError("full decode should not run when metadata duration exists")

    monkeypatch.setattr(player_module.AudioSegment, "from_file", _unexpected_decode)

    assert abs(player.get_duration_hint("D:/music/a.mp3") - 12.5) < 0.001


def test_get_duration_hint_does_not_full_decode_when_metadata_missing(monkeypatch):
    player = AudioPlayer()

    monkeypatch.setattr(player_module, "MutagenFile", lambda _path: SimpleNamespace(info=SimpleNamespace(length=0.0)))

    def _unexpected_decode(_path):
        raise AssertionError("duration hint should not trigger full decode")

    monkeypatch.setattr(player_module.AudioSegment, "from_file", _unexpected_decode)

    assert player.get_duration_hint("D:/music/no-meta.mp3") == 0.0


def test_high_quality_output_mode_toggle():
    player = AudioPlayer()
    assert player.get_high_quality_output_mode() is False

    player.set_high_quality_output_mode(True)
    assert player.get_high_quality_output_mode() is True


def test_build_stream_falls_back_to_shared_mode_when_exclusive_fails(monkeypatch):
    player = AudioPlayer()
    player.set_high_quality_output_mode(True)
    player._audio_data = np.zeros((8, 2), dtype=np.float32)
    player._sample_rate = 44100

    monkeypatch.setattr(player_module.sys, "platform", "win32", raising=False)
    monkeypatch.setattr(player_module.sd, "WasapiSettings", lambda exclusive=True: SimpleNamespace(exclusive=exclusive), raising=False)
    monkeypatch.setattr(player, "_default_output_hostapi_name", lambda: "wasapi")

    calls = []

    class _FakeStream:
        def __init__(self):
            self.started = False

        def start(self):
            self.started = True

    def _fake_output_stream(**kwargs):
        calls.append(kwargs)
        if "extra_settings" in kwargs:
            raise RuntimeError("exclusive unavailable")
        return _FakeStream()

    monkeypatch.setattr(player_module.sd, "OutputStream", _fake_output_stream)

    player._build_stream()

    assert len(calls) == 2
    assert "extra_settings" in calls[0]
    assert "extra_settings" not in calls[1]


def test_build_stream_skips_exclusive_when_default_hostapi_not_wasapi(monkeypatch):
    player = AudioPlayer()
    player.set_high_quality_output_mode(True)
    player._audio_data = np.zeros((8, 2), dtype=np.float32)
    player._sample_rate = 44100

    monkeypatch.setattr(player_module.sys, "platform", "win32", raising=False)

    wasapi_called = {"count": 0}

    def _fake_wasapi_settings(*_args, **_kwargs):
        wasapi_called["count"] += 1
        return SimpleNamespace(exclusive=True)

    monkeypatch.setattr(player_module.sd, "WasapiSettings", _fake_wasapi_settings, raising=False)
    monkeypatch.setattr(player, "_default_output_hostapi_name", lambda: "mme")

    calls = []

    class _FakeStream:
        def __init__(self):
            self.started = False

        def start(self):
            self.started = True

    def _fake_output_stream(**kwargs):
        calls.append(kwargs)
        return _FakeStream()

    monkeypatch.setattr(player_module.sd, "OutputStream", _fake_output_stream)

    player._build_stream()

    assert len(calls) == 1
    assert "extra_settings" not in calls[0]


def test_set_output_device_strategy_fixed_alias_is_compatible(monkeypatch):
    player = AudioPlayer()
    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (9, "Speaker"))

    player.set_output_device_strategy("fixed")

    assert player.audio_output_strategy == "fixed_current"
    assert player.fixed_output_device_signature == (9, "Speaker")


def test_set_output_device_strategy_fixed_current_captures_signature_when_missing(monkeypatch):
    player = AudioPlayer()
    monkeypatch.setattr(player, "get_default_output_device_signature", lambda: (3, "Headset"))

    player.set_output_device_strategy("fixed_current")

    assert player.fixed_output_device_signature == (3, "Headset")


def test_set_loudness_normalization_level_accepts_legacy_aliases():
    player = AudioPlayer()

    player.set_loudness_normalization_level("low")
    assert player.loudness_normalization_level == "light"

    player.set_loudness_normalization_level("high")
    assert player.loudness_normalization_level == "strong"


def test_prepare_predecoded_audio_uses_cache_when_signature_matches(monkeypatch):
    player = AudioPlayer()
    path = "D:/music/cache.mp3"

    monkeypatch.setattr(player, "_get_file_signature", lambda _path: (1, 2))

    calls = {"decode": 0}

    class _Segment:
        frame_rate = 44100

    monkeypatch.setattr(player, "_decode_audio_segment", lambda _path: calls.__setitem__("decode", calls["decode"] + 1) or _Segment())
    monkeypatch.setattr(player, "_segment_to_float_array", lambda _segment: np.zeros((4, 2), dtype=np.float32))

    payload1 = player.prepare_predecoded_audio(path)
    payload2 = player.prepare_predecoded_audio(path)

    assert calls["decode"] == 1
    assert payload1["audio_data"].shape == (4, 2)
    assert payload2["audio_data"].shape == (4, 2)


def test_visual_accent_detects_transient_and_decays():
    player = AudioPlayer()

    strong_chunk = np.ones((512, 2), dtype=np.float32) * 0.28
    player._update_visual_metrics_from_chunk(strong_chunk)
    accent_peak = player.get_visual_accent()
    assert accent_peak > 0.0

    silent_chunk = np.zeros((512, 2), dtype=np.float32)
    for _ in range(4):
        player._update_visual_metrics_from_chunk(silent_chunk)

    accent_after = player.get_visual_accent()
    assert accent_after < accent_peak


def test_pause_and_stop_reset_visual_accent():
    player = AudioPlayer()
    player.is_playing = True
    player._visual_accent = 0.8
    player._visual_intensity = 0.6

    assert player.pause() is True
    assert player.get_visual_accent() == 0.0

    player._visual_accent = 0.7
    player._visual_intensity = 0.5
    player._stream = DummyStream()
    assert player.stop() is True
    assert player.get_visual_accent() == 0.0


def test_suppress_ffmpeg_console_window_is_ref_counted(monkeypatch):
    player = AudioPlayer()
    monkeypatch.setattr(player_module.sys, "platform", "win32", raising=False)

    calls = {"audio_segment": [], "utils": []}

    def _original_audio_segment_popen(*_args, **kwargs):
        calls["audio_segment"].append(kwargs)
        return object()

    def _original_utils_popen(*_args, **kwargs):
        calls["utils"].append(kwargs)
        return object()

    class _StartupInfo:
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = 1

    fake_subprocess = SimpleNamespace(
        Popen=_original_audio_segment_popen,
        CREATE_NO_WINDOW=0x08000000,
        STARTUPINFO=_StartupInfo,
        STARTF_USESHOWWINDOW=1,
    )
    fake_utils = SimpleNamespace(Popen=_original_utils_popen)
    monkeypatch.setattr(player_module.pydub_audio_segment, "subprocess", fake_subprocess, raising=False)
    monkeypatch.setattr(player_module, "pydub_utils", fake_utils, raising=False)

    with player._suppress_ffmpeg_console_window():
        wrapped_audio_segment = fake_subprocess.Popen
        wrapped_utils = fake_utils.Popen
        assert wrapped_audio_segment is not _original_audio_segment_popen
        assert wrapped_utils is not _original_utils_popen

        with player._suppress_ffmpeg_console_window():
            assert fake_subprocess.Popen is wrapped_audio_segment
            assert fake_utils.Popen is wrapped_utils

        assert fake_subprocess.Popen is wrapped_audio_segment
        assert fake_utils.Popen is wrapped_utils
        fake_subprocess.Popen(["ffmpeg"])
        fake_utils.Popen(["ffprobe"])

    assert fake_subprocess.Popen is _original_audio_segment_popen
    assert fake_utils.Popen is _original_utils_popen

    assert len(calls["audio_segment"]) == 1
    assert int(calls["audio_segment"][0].get("creationflags", 0)) & int(fake_subprocess.CREATE_NO_WINDOW) == int(fake_subprocess.CREATE_NO_WINDOW)
    assert calls["audio_segment"][0].get("startupinfo") is not None
    assert calls["audio_segment"][0]["startupinfo"].wShowWindow == 0

    assert len(calls["utils"]) == 1
    assert int(calls["utils"][0].get("creationflags", 0)) & int(fake_subprocess.CREATE_NO_WINDOW) == int(fake_subprocess.CREATE_NO_WINDOW)
    assert calls["utils"][0].get("startupinfo") is not None
    assert calls["utils"][0]["startupinfo"].wShowWindow == 0


