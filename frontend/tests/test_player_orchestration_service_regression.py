from apps.desktop.windows.modules.player_orchestration_service import PlayerOrchestrationService


def test_resolve_same_song_action_keep_when_same_song_playing_not_paused():
    action = PlayerOrchestrationService.resolve_same_song_action(
        force_restart=False,
        current_song_id="a",
        target_song_id="a",
        is_playing=True,
        is_paused=False,
    )
    assert action == "keep"


def test_resolve_same_song_action_resume_when_same_song_paused():
    action = PlayerOrchestrationService.resolve_same_song_action(
        force_restart=False,
        current_song_id="a",
        target_song_id="a",
        is_playing=True,
        is_paused=True,
    )
    assert action == "resume"


def test_resolve_duration_hint_prefers_song_duration():
    value = PlayerOrchestrationService.resolve_duration_hint(12.5, 8.0)
    assert abs(value - 12.5) < 0.001


def test_map_slider_volume_to_gain_has_non_zero_floor_for_small_values():
    assert PlayerOrchestrationService.map_slider_volume_to_gain(0) == 0.0
    assert PlayerOrchestrationService.map_slider_volume_to_gain(1) >= 0.03
    assert PlayerOrchestrationService.map_slider_volume_to_gain(5) > 0.1


def test_map_slider_volume_to_gain_is_monotonic_until_max():
    low = PlayerOrchestrationService.map_slider_volume_to_gain(10)
    mid = PlayerOrchestrationService.map_slider_volume_to_gain(50)
    high = PlayerOrchestrationService.map_slider_volume_to_gain(100)

    assert 0.0 < low < mid <= high <= 1.0


