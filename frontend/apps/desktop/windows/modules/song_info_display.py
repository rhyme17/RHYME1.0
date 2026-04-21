from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics


class SongInfoDisplay:
    def __init__(self):
        self._current_song_title_text = "未播放"
        self._current_song_artist_text = "-"

    def normalize_lyrics_font_size(self, value):
        try:
            parsed = int(value)
        except Exception:
            parsed = 18
        return max(12, min(28, parsed))

    def elide_label_text(self, label, text):
        raw = str(text or "").strip()
        if not raw or label is None:
            return raw
        try:
            available_width = max(0, int(label.width()))
            if available_width <= 0:
                return raw
            metrics = QFontMetrics(label.font())
            return metrics.elidedText(raw, Qt.ElideRight, available_width)
        except Exception:
            return raw

    def update_song_info_labels(self, title_label, artist_label, title="", artist=""):
        self._current_song_title_text = str(title or "未播放").strip() or "未播放"
        self._current_song_artist_text = str(artist or "-").strip() or "-"
        
        if title_label is not None:
            title_label.setText(self.elide_label_text(title_label, self._current_song_title_text))
        if artist_label is not None:
            artist_label.setText(self.elide_label_text(artist_label, self._current_song_artist_text))

    def refresh_song_info_labels(self, title_label, artist_label):
        if title_label is not None:
            title_label.setText(
                self.elide_label_text(title_label, self._current_song_title_text)
            )
        if artist_label is not None:
            artist_label.setText(
                self.elide_label_text(artist_label, self._current_song_artist_text)
            )