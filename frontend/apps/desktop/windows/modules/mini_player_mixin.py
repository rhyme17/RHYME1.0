from PyQt5.QtCore import Qt

try:
    from frontend.apps.desktop.windows.modules.mini_player_window import MiniPlayerWindow
except ModuleNotFoundError:
    from apps.desktop.windows.modules.mini_player_window import MiniPlayerWindow


class MiniPlayerMixin:
    def _init_mini_player(self):
        if hasattr(self, "_mini_player_window"):
            return

        self._mini_player_window = MiniPlayerWindow(self)
        self._mini_player_visible = False

        self._mini_player_window.restore_main_window.connect(self._on_restore_from_mini_player)
        self._mini_player_window.play_pause_triggered.connect(self.toggle_play)
        self._mini_player_window.next_triggered.connect(self.play_next)
        self._mini_player_window.previous_triggered.connect(self.play_previous)
        self._mini_player_window.volume_changed.connect(self._on_mini_player_volume_changed)

    def toggle_mini_mode(self):
        self._init_mini_player()

        if self._mini_player_visible:
            self._hide_mini_player()
            self.show()
            self._mini_player_visible = False
        else:
            self._show_mini_player()
            self.hide()
            self._mini_player_visible = True

    def _show_mini_player(self):
        if not hasattr(self, "_mini_player_window"):
            return

        self._update_mini_player_state()
        self._mini_player_window.show()
        self._mini_player_window.activateWindow()

    def _hide_mini_player(self):
        if not hasattr(self, "_mini_player_window"):
            return

        self._mini_player_window.hide()

    def _on_restore_from_mini_player(self):
        self._hide_mini_player()
        self.show()
        self.activateWindow()
        self._mini_player_visible = False

    def _on_mini_player_volume_changed(self, value):
        if hasattr(self, "volume_slider"):
            self.volume_slider.setValue(value)

    def _update_mini_player_state(self):
        if not hasattr(self, "_mini_player_window"):
            return

        if hasattr(self, "current_song") and self.current_song:
            title = self.current_song.get("title", "未知歌曲")
            artist = self.current_song.get("artist", "未知艺术家")
            self._mini_player_window.set_song_info(title, artist)

        if hasattr(self, "audio_player"):
            is_playing = getattr(self.audio_player, "is_playing", False)
            is_paused = getattr(self.audio_player, "is_paused", False)
            self._mini_player_window.set_playing_state(is_playing and not is_paused)

        if hasattr(self, "lyric_label"):
            current_lyric = self.lyric_label.text()
            self._mini_player_window.set_lyric(current_lyric)

        if hasattr(self, "volume_slider"):
            volume = self.volume_slider.value()
            self._mini_player_window.set_volume(volume)

    def _update_mini_player_song_info(self, title, artist):
        if not hasattr(self, "_mini_player_window"):
            return
        self._mini_player_window.set_song_info(title, artist)

    def _update_mini_player_lyric(self, lyric):
        if not hasattr(self, "_mini_player_window"):
            return
        self._mini_player_window.set_lyric(lyric)

    def _update_mini_player_playing_state(self, is_playing):
        if not hasattr(self, "_mini_player_window"):
            return
        self._mini_player_window.set_playing_state(is_playing)

    def _update_mini_player_volume(self, volume):
        if not hasattr(self, "_mini_player_window"):
            return
        self._mini_player_window.set_volume(volume)
