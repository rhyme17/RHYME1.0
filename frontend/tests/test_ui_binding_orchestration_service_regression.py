from apps.desktop.windows.modules.ui_binding_orchestration_service import UiBindingOrchestrationService


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _FakeModel:
    def __init__(self):
        self.rowsMoved = _FakeSignal()


class _FakeWidget:
    def __init__(self):
        self.clicked = _FakeSignal()
        self.textChanged = _FakeSignal()
        self.itemDoubleClicked = _FakeSignal()
        self.itemClicked = _FakeSignal()


class _FakePlaylistList(_FakeWidget):
    def __init__(self):
        super().__init__()
        self._model = _FakeModel()

    def model(self):
        return self._model


class _FakePlayer:
    def __init__(self):
        self.open_scan_dialog_btn = _FakeWidget()
        self.create_playlist_btn = _FakeWidget()
        self.rename_playlist_btn = _FakeWidget()
        self.delete_playlist_btn = _FakeWidget()
        self.search_input = _FakeWidget()
        self.scan_btn = _FakeWidget()
        self.browse_btn = _FakeWidget()

        self.all_songs_list = _FakeWidget()
        self.artists_list = _FakeWidget()
        self.albums_list = _FakeWidget()

        self.playlist_tree_toggle_btn = _FakeWidget()
        self.add_to_playlist_btn = _FakeWidget()
        self.remove_from_playlist_btn = _FakeWidget()
        self.clear_playlist_btn = _FakeWidget()
        self.undo_reorder_btn = _FakeWidget()
        self.playlists_tree = _FakeWidget()
        self.playlist_list = _FakePlaylistList()

        self.reload_lyrics_btn = _FakeWidget()
        self.lyrics_asr_btn = _FakeWidget()
        self.progress_slider = type("_Progress", (), {"sliderMoved": _FakeSignal(), "sliderReleased": _FakeSignal()})()
        self.prev_btn = _FakeWidget()
        self.play_btn = _FakeWidget()
        self.next_btn = _FakeWidget()
        self.replay_btn = _FakeWidget()
        self.mute_btn = _FakeWidget()
        self.volume_slider = type("_Volume", (), {"valueChanged": _FakeSignal()})()
        self.mode_btn = _FakeWidget()
        self.high_quality_btn = _FakeWidget()

    # handlers
    def open_scan_dialog(self):
        pass

    def create_empty_playlist(self):
        pass

    def rename_selected_playlist(self):
        pass

    def delete_selected_playlist(self):
        pass

    def search_music(self):
        pass

    def scan_music(self):
        pass

    def browse_directory(self):
        pass

    def play_song_from_library(self):
        pass

    def show_artist_songs(self):
        pass

    def show_album_songs(self):
        pass

    def toggle_playlist_tree_visibility(self):
        pass

    def add_selected_to_playlist(self):
        pass

    def remove_selected_from_playlist(self):
        pass

    def clear_playlist(self):
        pass

    def undo_last_reorder(self):
        pass

    def on_playlist_tree_item_clicked(self):
        pass

    def on_playlist_tree_item_double_clicked(self):
        pass

    def play_song_from_playlist(self):
        pass

    def on_playlist_rows_moved(self):
        pass

    def reload_local_lyrics_for_current_song(self):
        pass

    def request_lyrics_asr_for_current_song(self):
        pass

    def set_position_preview(self):
        pass

    def apply_slider_position(self):
        pass

    def play_previous(self):
        pass

    def toggle_play(self):
        pass

    def play_next(self):
        pass

    def restart_current_song(self):
        pass

    def toggle_mute(self):
        pass

    def set_volume(self):
        pass

    def toggle_playback_mode(self):
        pass

    def toggle_high_quality_output(self):
        pass


def test_bind_all_only_runs_once_for_same_player():
    player = _FakePlayer()

    UiBindingOrchestrationService.bind_all(player)
    UiBindingOrchestrationService.bind_all(player)

    assert len(player.open_scan_dialog_btn.clicked.callbacks) == 1
    assert len(player.playlist_list.itemDoubleClicked.callbacks) == 1
    assert len(player.playlist_list.model().rowsMoved.callbacks) == 1
    assert len(player.progress_slider.sliderMoved.callbacks) == 1
    assert len(player.volume_slider.valueChanged.callbacks) == 1

