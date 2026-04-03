from apps.desktop.windows.modules.playback_orchestration_service import PlaybackOrchestrationService


class _DummyAudioPlayer:
    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self.mode = False
        self.position = 0.0
        self.reopen_result = True
        self.reopen_calls = 0
        self.play_calls = 0
        self.pause_calls = 0

    def set_high_quality_output_mode(self, enabled):
        self.mode = bool(enabled)

    def reopen_stream_from_current_buffer(self, keep_pause_state=True):
        self.reopen_calls += 1
        return bool(self.reopen_result)

    def get_position(self):
        return float(self.position)

    def play(self, _path, start_position=0):
        self.play_calls += 1
        return True

    def pause(self):
        self.pause_calls += 1
        self.is_paused = True
        return True


def test_switch_high_quality_mode_succeeds_without_playing_song():
    player = _DummyAudioPlayer()
    result = PlaybackOrchestrationService.switch_high_quality_mode(player, None, False, True)

    assert result["success"] is True
    assert result["final_mode"] is True
    assert "已切换" in result["message"]


def test_switch_high_quality_mode_rolls_back_when_reopen_fails():
    player = _DummyAudioPlayer()
    player.is_playing = True
    player.is_paused = False
    player.reopen_result = False
    song = {"path": "C:/a.mp3"}

    result = PlaybackOrchestrationService.switch_high_quality_mode(player, song, False, True)

    assert result["success"] is False
    assert result["final_mode"] is False
    assert player.play_calls == 1
    assert "回退" in result["message"]

