from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QLineEdit, QShortcut


class ShortcutMixin:
    def setup_keyboard_shortcuts(self):
        self.shortcut_play_pause = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut_play_pause.activated.connect(self.on_shortcut_play_pause)

        self.shortcut_volume_up = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.shortcut_volume_up.activated.connect(self.on_shortcut_volume_up)

        self.shortcut_volume_down = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.shortcut_volume_down.activated.connect(self.on_shortcut_volume_down)

        self.shortcut_seek_backward = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut_seek_backward.activated.connect(self.on_shortcut_seek_backward)

        self.shortcut_seek_forward = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut_seek_forward.activated.connect(self.on_shortcut_seek_forward)

        self.shortcut_prev = QShortcut(QKeySequence("Ctrl+Left"), self)
        self.shortcut_prev.activated.connect(self.on_shortcut_previous)

        self.shortcut_next = QShortcut(QKeySequence("Ctrl+Right"), self)
        self.shortcut_next.activated.connect(self.on_shortcut_next)

        self.shortcut_remove_from_playlist = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.shortcut_remove_from_playlist.activated.connect(self.on_shortcut_remove_from_playlist)

        self.shortcut_reload_lyrics = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_reload_lyrics.activated.connect(self.on_shortcut_reload_local_lyrics)

        for shortcut in (
            self.shortcut_play_pause,
            self.shortcut_volume_up,
            self.shortcut_volume_down,
            self.shortcut_seek_backward,
            self.shortcut_seek_forward,
            self.shortcut_prev,
            self.shortcut_next,
            self.shortcut_remove_from_playlist,
            self.shortcut_reload_lyrics,
        ):
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.setAutoRepeat(False)

    def _is_text_input_focused(self):
        focused = self.focusWidget()
        return isinstance(focused, QLineEdit)

    def on_shortcut_play_pause(self):
        if self._is_text_input_focused():
            return
        self.toggle_play()

    def on_shortcut_volume_up(self):
        if self._is_text_input_focused():
            return
        self.volume_slider.setValue(min(100, self.volume_slider.value() + self.keyboard_volume_step))

    def on_shortcut_volume_down(self):
        if self._is_text_input_focused():
            return
        self.volume_slider.setValue(max(0, self.volume_slider.value() - self.keyboard_volume_step))

    def on_shortcut_seek_backward(self):
        if self._is_text_input_focused():
            return
        self._seek_by_delta_seconds(-self.keyboard_seek_step_seconds)

    def on_shortcut_seek_forward(self):
        if self._is_text_input_focused():
            return
        self._seek_by_delta_seconds(self.keyboard_seek_step_seconds)

    def on_shortcut_previous(self):
        if self._is_text_input_focused():
            return
        self.play_previous()

    def on_shortcut_next(self):
        if self._is_text_input_focused():
            return
        self.play_next()

    def on_shortcut_remove_from_playlist(self):
        if self._is_text_input_focused():
            return
        self.remove_selected_from_playlist()

    def on_shortcut_reload_local_lyrics(self):
        if self._is_text_input_focused():
            return
        if hasattr(self, "reload_local_lyrics_for_current_song"):
            self.reload_local_lyrics_for_current_song()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

