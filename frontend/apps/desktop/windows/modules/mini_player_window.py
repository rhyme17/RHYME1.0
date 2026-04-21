from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class MiniPlayerWindow(QWidget):
    restore_main_window = pyqtSignal()
    play_pause_triggered = pyqtSignal()
    next_triggered = pyqtSignal()
    previous_triggered = pyqtSignal()
    volume_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._song_title = ""
        self._song_artist = ""
        self._current_lyric = ""
        self._is_playing = False
        self._current_volume = 100

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self.setMinimumWidth(320)
        self.setMaximumWidth(500)
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)
        self.resize(400, 140)

        self._drag_position = None
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_widget.setLayout(title_layout)

        self.song_info_label = QLabel("未播放")
        self.song_info_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.song_info_label.setWordWrap(False)
        title_layout.addWidget(self.song_info_label, 1)

        self.restore_btn = QPushButton("↗")
        self.restore_btn.setToolTip("恢复主窗口")
        self.restore_btn.setFixedSize(24, 24)
        self.restore_btn.clicked.connect(self._on_restore)
        title_layout.addWidget(self.restore_btn)

        main_layout.addWidget(title_widget)

        self.lyric_label = QLabel("暂无歌词")
        self.lyric_label.setFont(QFont("Microsoft YaHei", 9))
        self.lyric_label.setAlignment(Qt.AlignCenter)
        self.lyric_label.setWordWrap(True)
        self.lyric_label.setMaximumHeight(50)
        main_layout.addWidget(self.lyric_label)

        controls_widget = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        controls_widget.setLayout(controls_layout)

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.clicked.connect(self._on_previous)
        controls_layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self._on_play_pause)
        controls_layout.addWidget(self.play_btn)

        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.clicked.connect(self._on_next)
        controls_layout.addWidget(self.next_btn)

        controls_layout.addStretch()

        volume_widget = QWidget()
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(4)
        volume_widget.setLayout(volume_layout)

        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(24, 24)
        self.mute_btn.clicked.connect(self._on_mute_toggle)
        volume_layout.addWidget(self.mute_btn)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)

        controls_layout.addWidget(volume_widget)

        main_layout.addWidget(controls_widget)

    def _load_settings(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings("RHYME", "MiniPlayer")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._current_volume = settings.value("volume", 100, type=int)

    def _save_settings(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings("RHYME", "MiniPlayer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("volume", self._current_volume)

    def set_song_info(self, title, artist):
        self._song_title = title or "未知歌曲"
        self._song_artist = artist or "未知艺术家"
        self.song_info_label.setText(f"{self._song_title} - {self._song_artist}")

    def set_lyric(self, lyric):
        self._current_lyric = lyric or "暂无歌词"
        self.lyric_label.setText(self._current_lyric)

    def set_playing_state(self, is_playing):
        self._is_playing = bool(is_playing)
        self.play_btn.setText("⏸" if self._is_playing else "▶")

    def set_volume(self, value):
        self._current_volume = max(0, min(100, int(value)))
        self.volume_slider.setValue(self._current_volume)
        self._update_mute_button()

    def _update_mute_button(self):
        if self._current_volume == 0:
            self.mute_btn.setText("🔇")
        else:
            self.mute_btn.setText("🔊")

    def _on_restore(self):
        self.restore_main_window.emit()

    def _on_play_pause(self):
        self.play_pause_triggered.emit()

    def _on_next(self):
        self.next_triggered.emit()

    def _on_previous(self):
        self.previous_triggered.emit()

    def _on_volume_changed(self, value):
        self._current_volume = value
        self._update_mute_button()
        self.volume_changed.emit(value)
        self._save_settings()

    def _on_mute_toggle(self):
        if self._current_volume > 0:
            self._last_volume = self._current_volume
            self.set_volume(0)
        else:
            last_volume = getattr(self, "_last_volume", 100)
            self.set_volume(last_volume)
        self.volume_changed.emit(self._current_volume)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = None
            self._save_settings()

    def closeEvent(self, event):
        self._save_settings()
        event.accept()
