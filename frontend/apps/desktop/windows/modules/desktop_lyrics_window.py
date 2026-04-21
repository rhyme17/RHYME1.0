from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QMenu, QWidget


class DesktopLyricsWindow(QWidget):
    lyrics_updated = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_line = ""
        self._next_line = ""
        self._font_size = 18
        self._text_color = QColor(255, 255, 255)
        self._outline_color = QColor(0, 0, 0)
        self._background_color = QColor(0, 0, 0, 120)
        self._is_locked = False
        self._drag_position = None
        self._is_visible = False

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setMinimumWidth(400)
        self.setMinimumHeight(60)
        self.setMaximumHeight(120)
        self.resize(600, 80)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        self.setMouseTracking(True)

    def _load_settings(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings("RHYME", "DesktopLyrics")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._is_locked = settings.value("locked", False, type=bool)
        self._font_size = settings.value("fontSize", 18, type=int)

    def _save_settings(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings("RHYME", "DesktopLyrics")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("locked", self._is_locked)
        settings.setValue("fontSize", self._font_size)

    def set_lyrics(self, current_line, next_line=""):
        self._current_line = current_line
        self._next_line = next_line
        self.update()

    def set_font_size(self, size):
        self._font_size = max(12, min(36, int(size)))
        self.update()
        self._save_settings()

    def set_text_color(self, color):
        if isinstance(color, QColor):
            self._text_color = color
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            self._text_color = QColor(*color[:3])
        self.update()

    def set_background_color(self, color):
        if isinstance(color, QColor):
            self._background_color = color
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            self._background_color = QColor(*color[:3])
        self.update()

    def set_locked(self, locked):
        self._is_locked = bool(locked)
        self._save_settings()

    def toggle_lock(self):
        self.set_locked(not self._is_locked)

    def show_lyrics(self):
        if not self._is_visible:
            self.show()
            self._is_visible = True

    def hide_lyrics(self):
        if self._is_visible:
            self.hide()
            self._is_visible = False

    def toggle_visible(self):
        if self._is_visible:
            self.hide_lyrics()
        else:
            self.show_lyrics()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), self._background_color)

        if not self._current_line:
            return

        font = QFont("Microsoft YaHei", self._font_size, QFont.Bold)
        painter.setFont(font)

        text_height = self._font_size + 10
        current_y = (self.height() - text_height) // 2

        if self._next_line:
            current_y -= text_height // 2

        self._draw_text_with_outline(painter, self._current_line, self.height() // 2 - 5, self._text_color)

        if self._next_line:
            small_font = QFont("Microsoft YaHei", int(self._font_size * 0.75))
            painter.setFont(small_font)
            next_color = QColor(self._text_color)
            next_color.setAlpha(180)
            self._draw_text_with_outline(
                painter, self._next_line, self.height() // 2 + self._font_size + 5, next_color
            )

    def _draw_text_with_outline(self, painter, text, y, color):
        from PyQt5.QtCore import QRect

        outline_pen = QPen(self._outline_color)
        outline_pen.setWidth(2)
        painter.setPen(outline_pen)

        rect = QRect(5, y - self._font_size, self.width() - 10, self._font_size + 10)
        painter.drawText(rect, Qt.AlignCenter, text)

        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._is_locked:
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position and not self._is_locked:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = None
            self._save_settings()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        lock_action = menu.addAction("锁定窗口" if not self._is_locked else "解锁窗口")
        lock_action.triggered.connect(self.toggle_lock)

        menu.addSeparator()

        font_size_menu = menu.addMenu("字体大小")
        for size in [14, 16, 18, 20, 22, 24]:
            action = font_size_menu.addAction(f"{size}px")
            action.triggered.connect(lambda checked, s=size: self.set_font_size(s))

        menu.addSeparator()

        hide_action = menu.addAction("隐藏桌面歌词")
        hide_action.triggered.connect(self.hide_lyrics)

        menu.exec_(event.globalPos())

    def closeEvent(self, event):
        self._save_settings()
        event.accept()
