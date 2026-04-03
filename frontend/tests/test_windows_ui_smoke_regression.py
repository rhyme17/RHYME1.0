import importlib
from types import SimpleNamespace
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication


QAPP_INSTANCE = None
USER_ROLE = getattr(Qt, "UserRole", 32)


def _get_qapp():
    global QAPP_INSTANCE
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    QAPP_INSTANCE = app
    return app


def _load_windows_app_module(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    module = importlib.import_module("apps.desktop.windows.app")

    sandbox_dir = tmp_path / "windows-sandbox"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(module, "WINDOWS_APP_DIR", str(sandbox_dir))
    monkeypatch.setattr(module, "PLAYLISTS_FILE", str(sandbox_dir / "playlists.json"))
    monkeypatch.setattr(module, "SETTINGS_FILE", str(sandbox_dir / "settings.json"))
    return module


def _assert_has_positive_size(sizes):
    assert len(sizes) >= 1
    assert sum(sizes) > 0


def _find_playlist_item(player, playlist_name):
    for row in range(player.playlists_list.count()):
        item = player.playlists_list.item(row)
        if item.data(USER_ROLE) == playlist_name:
            return item
    return None


def test_music_player_can_initialize_with_key_widgets(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.tab_widget.count() == 3
        assert player.playlists_list is not None
        assert player.playlist_list is not None
        assert player.volume_slider.minimum() == 0
        assert player.volume_slider.maximum() == 100
        assert player.play_btn.text() in ("▶", "⏸")
    finally:
        player.close()


def test_initial_volume_is_applied_to_audio_backend_on_startup(monkeypatch, tmp_path):
    from apps.desktop.windows.modules.player_orchestration_service import PlayerOrchestrationService

    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        expected = PlayerOrchestrationService.map_slider_volume_to_gain(player.volume_slider.value())
        assert abs(float(player.audio_player.volume) - float(expected)) < 1e-9
    finally:
        player.close()



def test_splitter_initial_size_is_stable(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    app = _get_qapp()

    player = module.MusicPlayer()
    try:
        player.show()
        app.processEvents()

        _assert_has_positive_size(player.main_splitter.sizes())
    finally:
        player.close()


def test_shortcuts_do_not_trigger_when_text_input_is_focused(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        original_volume = player.volume_slider.value()
        original_progress = player.progress_slider.value()

        monkeypatch.setattr(player, "focusWidget", lambda: player.search_input)

        player.on_shortcut_volume_up()
        player.on_shortcut_seek_forward()

        assert player.volume_slider.value() == original_volume
        assert player.progress_slider.value() == original_progress
    finally:
        player.close()


def test_delete_shortcut_does_not_remove_when_text_input_is_focused(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 10},
            {"id": "b", "title": "B", "artist": "BB", "album": "AL", "path": "C:/b.mp3", "duration": 10},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist()
        player.playlist_list.setCurrentRow(0)

        monkeypatch.setattr(player, "focusWidget", lambda: player.search_input)
        player.on_shortcut_remove_from_playlist()

        assert len(player.playlist_manager.get_playlist()) == 2
    finally:
        player.close()


def test_reload_local_lyrics_for_current_song_uses_latest_local_file(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song_dir = tmp_path / "lyrics-reload"
        song_dir.mkdir(parents=True, exist_ok=True)
        song_path = song_dir / "demo.mp3"
        lrc_path = song_dir / "demo.lrc"
        lrc_path.write_text("[00:00.00]手动修正后的歌词\n", encoding="utf-8")

        player.current_song = {
            "id": "demo-song",
            "title": "demo",
            "artist": "artist",
            "album": "album",
            "path": str(song_path),
            "duration": 30,
        }
        monkeypatch.setattr(player.audio_player, "get_position", lambda: 0.0)

        player.reload_local_lyrics_for_current_song()

        assert player.current_lyrics_source == "local"
        assert len(player.current_lyrics_lines) == 1
        assert "手动修正后的歌词" in player.lyric_label.text()
    finally:
        player.close()


def test_delete_shortcut_removes_selected_song_from_playlist(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 10},
            {"id": "b", "title": "B", "artist": "BB", "album": "AL", "path": "C:/b.mp3", "duration": 10},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist()
        player.playlist_list.setCurrentRow(0)

        monkeypatch.setattr(player, "focusWidget", lambda: None)
        player.on_shortcut_remove_from_playlist()

        playlist = player.playlist_manager.get_playlist()
        assert len(playlist) == 1
        assert playlist[0]["id"] == "b"
    finally:
        player.close()


def test_switch_playlist_keeps_splitter_sizes(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    app = _get_qapp()

    player = module.MusicPlayer()
    try:
        player.playlist_manager.create_playlist("A", songs=[], set_current=True, overwrite=True)
        player.playlist_manager.create_playlist("B", songs=[], set_current=False, overwrite=True)
        player.render_playlist_names(select_name="A")

        player.show()
        app.processEvents()

        player.main_splitter.setSizes([1000])
        before_main = list(player.main_splitter.sizes())

        item_b = _find_playlist_item(player, "B")
        assert item_b is not None
        player.on_playlist_selected(item_b)
        app.processEvents()

        after_main = player.main_splitter.sizes()

        assert all(abs(a - b) <= 2 for a, b in zip(before_main, after_main))
    finally:
        player.close()


def test_playlist_tree_is_collapsed_by_default_and_can_toggle(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.is_playlist_tree_expanded is False
        assert player.playlists_tree.isHidden() is True
        assert player.playlist_tree_toggle_btn.arrowType() == Qt.RightArrow

        player.toggle_playlist_tree_visibility()

        assert player.is_playlist_tree_expanded is True
        assert player.playlists_tree.isHidden() is False
        assert player.playlist_tree_toggle_btn.arrowType() == Qt.DownArrow
    finally:
        player.close()


def test_playlist_tree_contains_only_playlist_names(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 10},
            {"id": "b", "title": "B", "artist": "BB", "album": "AL", "path": "C:/b.mp3", "duration": 10},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist_names(select_name="RoadTrip")

        item = _find_playlist_item(player, "RoadTrip")
        assert item is not None
        assert item.childCount() == 0
    finally:
        player.close()


def test_playlist_song_view_is_structured_columns(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.playlist_list.columnCount() == 4
        assert player.playlist_list.headerItem().text(0) == "序号"
        assert player.playlist_list.headerItem().text(1) == "歌曲"
        assert player.playlist_list.headerItem().text(2) == "歌手"
        assert player.playlist_list.headerItem().text(3) == "时长"
    finally:
        player.close()


def test_playlist_song_columns_match_rendered_song(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 65},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist()

        item = player.playlist_list.item(0)
        assert item is not None
        assert item.text(0) == "1"
        assert item.text(1) == "a"
        assert item.text(2) == "AA"
        assert item.text(3) == "01:05"
    finally:
        player.close()


def test_render_playlist_backfills_zero_duration_with_hint(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 0},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        monkeypatch.setattr(player.audio_player, "get_duration_hint", lambda _path: 65.0)

        player.render_playlist()

        item = player.playlist_list.item(0)
        assert item is not None
        assert item.text(3) == "01:05"
        assert float(player.playlist_manager.get_playlist()[0]["duration"]) == 65.0
    finally:
        player.close()


def test_add_music_button_opens_scan_dialog(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        calls = {"exec": 0}
        scan_dialog_cls = player.open_scan_dialog.__func__.__globals__["ScanDialog"]

        class _DialogSpy(scan_dialog_cls):
            def exec_(self):
                calls["exec"] += 1
                return 0

        monkeypatch.setitem(player.open_scan_dialog.__func__.__globals__, "ScanDialog", _DialogSpy)

        player.open_scan_dialog()

        assert calls["exec"] == 1
        assert player.scan_dialog is not None
        assert hasattr(player.scan_dialog, "save_playlist_btn")
        assert player.scan_dialog.save_playlist_btn.text() == "保存为歌单"
    finally:
        player.close()


def test_main_page_has_create_playlist_button(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.create_playlist_btn is not None
        assert player.create_playlist_btn.text() == "新建歌单"
    finally:
        player.close()


def test_main_page_has_high_quality_button_and_can_toggle(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.high_quality_btn is not None
        assert player.high_quality_btn.text() in ("高音质：开", "高音质：关")

        called = {"save": 0, "mode": None}
        monkeypatch.setattr(player, "schedule_save_app_settings", lambda: called.__setitem__("save", called["save"] + 1))
        monkeypatch.setattr(player.audio_player, "set_high_quality_output_mode", lambda enabled: called.__setitem__("mode", bool(enabled)))

        initial = bool(player.high_quality_output_enabled)
        player.toggle_high_quality_output()

        assert bool(player.high_quality_output_enabled) is (not initial)
        assert called["mode"] is (not initial)
        assert called["save"] >= 1
    finally:
        player.close()


def test_main_page_has_replay_button_and_can_trigger_restart(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    called = {"count": 0}
    monkeypatch.setattr(
        module.PlaybackMixin,
        "restart_current_song",
        lambda self: called.__setitem__("count", called["count"] + 1) or True,
    )

    player = module.MusicPlayer()
    try:
        assert player.replay_btn is not None
        assert player.replay_btn.text() == "重播"
        player.replay_btn.click()

        assert called["count"] == 1
    finally:
        player.close()


def test_lyrics_buttons_are_on_song_info_row_and_lyrics_stays_centered(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert player.reload_lyrics_btn is not None
        assert player.reload_lyrics_btn.text() == "重载歌词"
        assert player.lyrics_asr_btn is not None
        assert bool(player.lyric_label.alignment() & Qt.AlignCenter)
        assert player.song_title_label.parent() is player.lyrics_asr_btn.parent()
    finally:
        player.close()


def test_double_click_current_playlist_song_restarts_instead_of_replay_path(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "song-1",
            "title": "A",
            "artist": "AA",
            "album": "AL",
            "path": "C:/a.mp3",
            "duration": 10,
        }
        player.playlist_manager.create_playlist("RoadTrip", [song], set_current=True, overwrite=True)
        player.render_playlist()
        player.current_song = song

        restart_called = {"count": 0}
        play_called = {"count": 0}
        monkeypatch.setattr(player, "restart_current_song", lambda: restart_called.__setitem__("count", restart_called["count"] + 1) or True)
        monkeypatch.setattr(player, "play_current_song", lambda *args, **kwargs: play_called.__setitem__("count", play_called["count"] + 1) or True)

        item = player.playlist_list.item(0)
        player.play_song_from_playlist(item)

        assert restart_called["count"] == 1
        assert play_called["count"] == 0
    finally:
        player.close()


def test_double_click_other_song_clears_resume_pending_and_forces_restart(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song_a = {
            "id": "song-a",
            "title": "A",
            "artist": "AA",
            "album": "AL",
            "path": "C:/a.mp3",
            "duration": 10,
        }
        song_b = {
            "id": "song-b",
            "title": "B",
            "artist": "BB",
            "album": "AL",
            "path": "C:/b.mp3",
            "duration": 20,
        }
        player.playlist_manager.create_playlist("RoadTrip", [song_a, song_b], set_current=True, overwrite=True)
        player.render_playlist()
        player.current_song = song_a
        player._pending_resume_song_id = "song-a"
        player._pending_resume_position_seconds = 7.2

        called = {"force_restart": None}

        def _fake_play_current_song(*args, **kwargs):
            called["force_restart"] = kwargs.get("force_restart", False)
            return True

        monkeypatch.setattr(player, "play_current_song", _fake_play_current_song)

        item = player.playlist_list.item(1)
        player.play_song_from_playlist(item)

        assert called["force_restart"] is True
        assert player.current_track_index == 1
        assert player._pending_resume_song_id == ""
        assert player._pending_resume_position_seconds == 0.0
    finally:
        player.close()


def test_double_click_current_library_song_restarts(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "song-lib-1",
            "title": "LibSong",
            "artist": "Artist",
            "album": "Album",
            "path": "C:/lib.mp3",
            "duration": 10,
        }
        player.current_song = song
        player.music_library.songs = [song]
        player.render_song_list(player.music_library.songs)

        restart_called = {"count": 0}
        monkeypatch.setattr(player, "restart_current_song", lambda: restart_called.__setitem__("count", restart_called["count"] + 1) or True)
        monkeypatch.setattr(player, "play_current_song", lambda *args, **kwargs: False)

        item = player.all_songs_list.item(0)
        player.play_song_from_library(item)

        assert restart_called["count"] == 1
    finally:
        player.close()


def test_restart_current_song_prefers_buffer_reopen_path(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "song-fast-restart",
            "title": "Fast",
            "artist": "Artist",
            "album": "Album",
            "path": "C:/fast.mp3",
            "duration": 10,
        }
        player.playlist_manager.create_playlist("RoadTrip", [song], set_current=True, overwrite=True)
        player.current_track_index = 0
        player.current_song = song
        player.audio_player.current_file = song["path"]
        player.audio_player._audio_data = object()

        calls = {"seek": 0, "reopen": 0, "play_current": 0}
        monkeypatch.setattr(player.audio_player, "seek", lambda _v: calls.__setitem__("seek", calls["seek"] + 1) or True)
        monkeypatch.setattr(
            player.audio_player,
            "reopen_stream_from_current_buffer",
            lambda **kwargs: calls.__setitem__("reopen", calls["reopen"] + 1) or True,
        )
        monkeypatch.setattr(
            player,
            "play_current_song",
            lambda *args, **kwargs: calls.__setitem__("play_current", calls["play_current"] + 1) or True,
        )

        assert player.restart_current_song() is True
        assert calls["seek"] == 1
        assert calls["reopen"] == 1
        assert calls["play_current"] == 0
    finally:
        player.close()


def test_progress_slider_preview_does_not_seek_until_release(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        player.current_duration = 100.0
        seek_calls = {"count": 0}
        monkeypatch.setattr(player.audio_player, "seek", lambda _v: seek_calls.__setitem__("count", seek_calls["count"] + 1) or True)

        player.set_position_preview(30)
        assert seek_calls["count"] == 0

        player.progress_slider.setValue(30)
        player.apply_slider_position()
        assert seek_calls["count"] == 1
    finally:
        player.close()


def test_update_progress_uses_animated_progress_path(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        called = {"target": None}

        monkeypatch.setattr(player.audio_player, "is_playing", True)
        monkeypatch.setattr(player.audio_player, "get_position", lambda: 25.0)
        player.current_duration = 100.0
        monkeypatch.setattr(player, "_animate_progress_to", lambda value: called.__setitem__("target", int(value)))

        player.update_progress()

        assert called["target"] == 25
    finally:
        player.close()


def test_set_position_stops_animation_before_seek(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        player.current_duration = 100.0
        stopped = {"count": 0}
        seek_calls = {"count": 0}

        monkeypatch.setattr(player, "_stop_progress_animation", lambda: stopped.__setitem__("count", stopped["count"] + 1))
        monkeypatch.setattr(player.audio_player, "seek", lambda _v: seek_calls.__setitem__("count", seek_calls["count"] + 1) or True)

        player.set_position(30)

        assert stopped["count"] == 1
        assert seek_calls["count"] == 1
    finally:
        player.close()


def test_toggle_play_updates_progress_visual_active_flag(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        states = []
        monkeypatch.setattr(player, "_set_progress_visual_active", lambda active: states.append(bool(active)))

        player.audio_player.is_playing = True
        player.audio_player.is_paused = True
        monkeypatch.setattr(player.audio_player, "resume", lambda: True)

        player.toggle_play()

        assert states[-1] is True
    finally:
        player.close()


def test_update_progress_disables_progress_visual_when_stopped(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        states = []
        monkeypatch.setattr(player, "_set_progress_visual_active", lambda active: states.append(bool(active)))
        player.audio_player.is_playing = False
        player.current_duration = 120.0

        player.update_progress()

        assert states[-1] is False
    finally:
        player.close()


def test_set_progress_visual_pulse_enabled_delegates_to_slider(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        calls = []
        monkeypatch.setattr(player.progress_slider, "set_pulse_enabled", lambda enabled: calls.append(bool(enabled)))

        player.set_progress_visual_pulse_enabled(False)
        player.set_progress_visual_pulse_enabled(True)

        assert calls == [False, True]
    finally:
        player.close()


def test_progress_slider_receives_default_pulse_enabled_from_runtime_state(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        assert hasattr(player, "progress_visual_pulse_enabled")
        assert player.progress_visual_pulse_enabled is True
        assert hasattr(player.progress_slider, "_pulse_enabled")
        assert player.progress_slider._pulse_enabled is True
    finally:
        player.close()


def test_set_progress_visual_wave_enabled_delegates_to_slider(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        calls = []
        monkeypatch.setattr(player.progress_slider, "set_wave_enabled", lambda enabled: calls.append(bool(enabled)))

        player.set_progress_visual_wave_enabled(False)
        player.set_progress_visual_wave_enabled(True)

        assert calls == [False, True]
    finally:
        player.close()


def test_update_progress_pushes_audio_intensity_to_slider(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        values = []
        player.current_duration = 100.0
        player.audio_player.is_playing = True
        monkeypatch.setattr(player.audio_player, "get_position", lambda: 20.0)
        monkeypatch.setattr(player.audio_player, "get_visual_intensity", lambda: 0.42)
        monkeypatch.setattr(player, "_animate_progress_to", lambda _v: None)
        monkeypatch.setattr(player.progress_slider, "set_audio_intensity", lambda value: values.append(float(value)))

        player.update_progress()

        assert values
        assert abs(values[-1] - 0.42) < 1e-6
    finally:
        player.close()


def test_set_progress_visual_accent_enabled_delegates_to_slider(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        calls = []
        monkeypatch.setattr(player.progress_slider, "set_accent_enabled", lambda enabled: calls.append(bool(enabled)))

        player.set_progress_visual_accent_enabled(False)
        player.set_progress_visual_accent_enabled(True)

        assert calls == [False, True]
    finally:
        player.close()


def test_update_progress_pushes_audio_accent_to_slider(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        values = []
        player.current_duration = 100.0
        player.audio_player.is_playing = True
        monkeypatch.setattr(player.audio_player, "get_position", lambda: 18.0)
        monkeypatch.setattr(player.audio_player, "get_visual_intensity", lambda: 0.4)
        monkeypatch.setattr(player.audio_player, "get_visual_accent", lambda: 0.67)
        monkeypatch.setattr(player, "_animate_progress_to", lambda _v: None)
        monkeypatch.setattr(player.progress_slider, "set_audio_intensity", lambda _v: None)
        monkeypatch.setattr(player.progress_slider, "set_audio_accent", lambda value: values.append(float(value)))

        player.update_progress()

        assert values
        assert abs(values[-1] - 0.67) < 1e-6
    finally:
        player.close()


def test_toggle_high_quality_output_failure_uses_hint_not_messagebox(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "hq-song-1",
            "title": "HQ",
            "artist": "Artist",
            "album": "Album",
            "path": "C:/hq.mp3",
            "duration": 30,
        }
        player.current_song = song
        player.audio_player.is_playing = True
        player.audio_player.is_paused = False

        calls = {"msgbox": 0, "hint": ""}

        class _FakeStatusBar:
            def showMessage(self, text, _timeout):
                calls["hint"] = text

        monkeypatch.setattr(player, "statusBar", lambda: _FakeStatusBar())
        msgbox = player.toggle_high_quality_output.__func__.__globals__["QMessageBox"]
        monkeypatch.setattr(msgbox, "warning", lambda *args, **kwargs: calls.__setitem__("msgbox", calls["msgbox"] + 1))

        monkeypatch.setattr(player.audio_player, "reopen_stream_from_current_buffer", lambda **kwargs: False)
        monkeypatch.setattr(player.audio_player, "play", lambda *_args, **_kwargs: False)

        player.toggle_high_quality_output()

        assert calls["msgbox"] == 0
        assert "回退" in calls["hint"]
    finally:
        player.close()


def test_high_quality_setting_is_persisted_across_instances(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    first = module.MusicPlayer()
    try:
        first.high_quality_output_enabled = True
        first.audio_player.set_high_quality_output_mode(True)
        first.save_app_settings()
    finally:
        first.close()

    second = module.MusicPlayer()
    try:
        assert second.high_quality_output_enabled is True
        assert second.audio_player.get_high_quality_output_mode() is True
        assert second.high_quality_btn.text() == "高音质：开"
    finally:
        second.close()


def test_play_current_song_skips_redecode_when_same_song_already_playing(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "same-song-id",
            "title": "Same",
            "artist": "Artist",
            "album": "Album",
            "path": "C:/music/same.mp3",
            "duration": 120,
        }
        player.playlist_manager.create_playlist("RoadTrip", [song], set_current=True, overwrite=True)
        player.current_track_index = 0
        player.current_song = song
        player.audio_player.is_playing = True
        player.audio_player.is_paused = False

        monkeypatch.setattr(player.audio_player, "stop", lambda: (_ for _ in ()).throw(AssertionError("stop should not be called")))
        monkeypatch.setattr(player.audio_player, "play", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("play should not be called")))

        assert player.play_current_song() is True
        assert player.play_btn.text() == "⏸"
    finally:
        player.close()


def test_create_empty_playlist_creates_empty_current_playlist(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        qinput = player.create_empty_playlist.__func__.__globals__["QInputDialog"]
        monkeypatch.setattr(qinput, "getText", lambda *args, **kwargs: ("测试空歌单", True))

        player.create_empty_playlist()

        assert player.playlist_manager.get_playlist_name() == "测试空歌单"
        assert player.playlist_manager.get_playlist() == []
    finally:
        player.close()


def test_scan_dialog_can_toggle_scanning_state(monkeypatch, tmp_path):
    _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    from apps.desktop.windows.modules.scan_dialog import ScanDialog

    dialog = ScanDialog()
    try:
        dialog.set_scanning_state(True, "正在扫描")
        assert dialog.scan_btn.text() == "取消扫描"
        assert dialog.directory_input.isEnabled() is False
        assert dialog.browse_btn.isEnabled() is False

        dialog.set_scanning_state(False, "扫描完成")
        assert dialog.scan_btn.text() == "开始扫描"
        assert dialog.directory_input.isEnabled() is True
        assert dialog.browse_btn.isEnabled() is True

        dialog.set_scanning_state(True, "正在扫描")
        dialog.set_scan_progress(3, 10)
        assert "3/10" in dialog.hint_label.text()

        dialog.set_cancelling_state()
        assert dialog.scan_btn.text() == "取消中..."
        assert dialog.scan_btn.isEnabled() is False
    finally:
        dialog.close()


def test_ctrl_left_right_do_not_switch_song_when_text_input_is_focused(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        player.current_track_index = 3
        called = {"prev": False, "next": False}

        def _prev():
            called["prev"] = True

        def _next():
            called["next"] = True

        monkeypatch.setattr(player, "focusWidget", lambda: player.search_input)
        monkeypatch.setattr(player, "play_previous", _prev)
        monkeypatch.setattr(player, "play_next", _next)

        player.on_shortcut_previous()
        player.on_shortcut_next()

        assert called["prev"] is False
        assert called["next"] is False
        assert player.current_track_index == 3
    finally:
        player.close()


def test_volume_setting_is_persisted_across_instances(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    first = module.MusicPlayer()
    try:
        first.volume_slider.setValue(36)
        first.save_app_settings()
    finally:
        first.close()

    second = module.MusicPlayer()
    try:
        assert second.saved_volume == 36
        assert second.volume_slider.value() == 36
    finally:
        second.close()


def test_last_played_song_is_restored_on_next_start(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    song_a = {
        "id": "song-a",
        "title": "A",
        "artist": "ArtistA",
        "album": "AlbumA",
        "path": "C:/music/A.mp3",
        "duration": 10,
    }
    song_b = {
        "id": "song-b",
        "title": "B",
        "artist": "ArtistB",
        "album": "AlbumB",
        "path": "C:/music/B.mp3",
        "duration": 20,
    }

    first = module.MusicPlayer()
    try:
        first.playlist_manager.create_playlist("RoadTrip", [song_a, song_b], set_current=True, overwrite=True)
        first.current_track_index = 1
        first.current_song = song_b
        first._pending_resume_song_id = "song-b"
        first._pending_resume_position_seconds = 7.25
        first.save_playlists()
        first.save_app_settings()
    finally:
        first.close()

    second = module.MusicPlayer()
    try:
        assert second.playlist_manager.get_playlist_name() == "RoadTrip"
        assert second.current_song is not None
        assert second.current_song.get("id") == "song-b"
        assert second.current_track_index == 1
        assert second._pending_resume_song_id == "song-b"
        assert abs(second._pending_resume_position_seconds - 7.25) < 0.01
        assert second.progress_slider.value() > 0
    finally:
        second.close()


def test_update_ui_persists_progress_with_bucket_throttle(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        saved = {"count": 0}

        def _save():
            saved["count"] += 1

        monkeypatch.setattr(player, "schedule_save_app_settings", _save)
        monkeypatch.setattr(player.audio_player, "recover_on_device_change", lambda: False)
        player.audio_player.is_playing = True
        player.audio_player.is_paused = False
        player._progress_persist_interval_seconds = 5
        player._last_progress_save_bucket = -1

        pos = {"value": 6.0}
        monkeypatch.setattr(player.audio_player, "get_position", lambda: pos["value"])

        player.update_ui()
        assert saved["count"] == 1

        player.update_ui()
        assert saved["count"] == 1

        pos["value"] = 11.2
        player.update_ui()
        assert saved["count"] == 2
    finally:
        player.close()


def test_update_ui_does_not_persist_progress_when_paused_or_stopped(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        saved = {"count": 0}

        def _save():
            saved["count"] += 1

        monkeypatch.setattr(player, "schedule_save_app_settings", _save)
        monkeypatch.setattr(player.audio_player, "recover_on_device_change", lambda: False)
        monkeypatch.setattr(player.audio_player, "get_position", lambda: 12.0)

        player.audio_player.is_playing = True
        player.audio_player.is_paused = True
        player.update_ui()

        player.audio_player.is_playing = False
        player.audio_player.is_paused = False
        player.update_ui()

        assert saved["count"] == 0
    finally:
        player.close()


def test_sync_playlist_order_skips_when_order_unchanged(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 10},
            {"id": "b", "title": "B", "artist": "BB", "album": "AL", "path": "C:/b.mp3", "duration": 10},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist()

        called = {"save": 0}
        monkeypatch.setattr(player, "save_playlists", lambda: called.__setitem__("save", called["save"] + 1))

        player.sync_playlist_order_from_ui()

        assert called["save"] == 0
        assert player.last_reorder_snapshot is None
    finally:
        player.close()


def test_sync_playlist_order_rolls_back_when_ui_items_incomplete(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        songs = [
            {"id": "a", "title": "A", "artist": "AA", "album": "AL", "path": "C:/a.mp3", "duration": 10},
            {"id": "b", "title": "B", "artist": "BB", "album": "AL", "path": "C:/b.mp3", "duration": 10},
        ]
        player.playlist_manager.create_playlist("RoadTrip", songs=songs, set_current=True, overwrite=True)
        player.render_playlist()

        # 模拟拖拽异常导致 UI 列表缺项，应自动回滚为原歌单。
        player.playlist_list.takeItem(0)
        player.sync_playlist_order_from_ui()

        assert player.playlist_list.count() == 2
        assert player.playlist_list.item(0).data(USER_ROLE).get("id") == "a"
        assert player.playlist_list.item(1).data(USER_ROLE).get("id") == "b"
    finally:
        player.close()


def test_lyrics_can_re_recognize_even_when_local_lrc_exists(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        song = {
            "id": "lyric-song-1",
            "title": "demo",
            "artist": "demo",
            "path": "C:/music/demo.mp3",
            "duration": 10,
        }
        player.current_song = song

        fake_result = SimpleNamespace(
            lines=[SimpleNamespace(time_ms=0, text="hello")],
            source="local",
            pending_asr=False,
        )
        monkeypatch.setattr(player.lyrics_service, "resolve_for_song", lambda _song: fake_result)
        monkeypatch.setattr(player.lyrics_service, "is_asr_available", lambda: True)

        player.load_lyrics_for_song(song)

        assert player.lyrics_asr_btn.isEnabled() is True
        assert player.lyrics_asr_btn.text() == "重新识别"
    finally:
        player.close()


def test_lyrics_request_while_running_shows_hint_and_not_restart(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        player.current_song = {
            "id": "lyric-song-2",
            "title": "demo2",
            "artist": "demo2",
            "path": "C:/music/demo2.mp3",
            "duration": 10,
        }
        player.lyrics_asr_available = True
        player.lyrics_asr_running = True

        calls = {"start": 0, "message": ""}

        def _fake_start(_song):
            calls["start"] += 1

        class _FakeStatusBar:
            def showMessage(self, text, _timeout):
                calls["message"] = text

        monkeypatch.setattr(player, "_start_lyrics_asr", _fake_start)
        monkeypatch.setattr(player, "statusBar", lambda: _FakeStatusBar())

        player.request_lyrics_asr_for_current_song()

        assert calls["start"] == 0
        assert "进行中" in calls["message"]
    finally:
        player.close()


def test_stale_lyrics_worker_callback_does_not_override_active_state(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        stale_worker = object()
        active_worker = object()
        player.lyrics_asr_worker = active_worker
        player.lyrics_asr_running = True
        player._lyrics_asr_worker_token = 2

        player.on_lyrics_asr_finished(
            True,
            "song-id",
            "",
            "",
            worker_ref=stale_worker,
            worker_token=1,
        )

        assert player.lyrics_asr_running is True
        assert player.lyrics_asr_worker is active_worker
    finally:
        player.close()


def test_settings_snapshot_contains_high_quality_field(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        snapshot = player.get_settings_snapshot()
        assert "high_quality_output" in snapshot
        assert snapshot["high_quality_output"] == bool(player.high_quality_output_enabled)
    finally:
        player.close()


def test_apply_settings_updates_high_quality_button_and_persists(monkeypatch, tmp_path):
    module = _load_windows_app_module(monkeypatch, tmp_path)
    _get_qapp()

    player = module.MusicPlayer()
    try:
        calls = {"save": 0}
        monkeypatch.setattr(player, "schedule_save_app_settings", lambda *_args, **_kwargs: calls.__setitem__("save", calls["save"] + 1))

        target = not bool(player.high_quality_output_enabled)
        player.apply_settings({"high_quality_output": target}, persist=True)

        assert player.high_quality_output_enabled is target
        assert player.high_quality_btn.text() == ("高音质：开" if target else "高音质：关")
        assert calls["save"] == 1
    finally:
        player.close()



