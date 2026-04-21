import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from frontend.core.lrc_parser import LyricLine, format_timestamp, parse_lrc_file, write_lrc_file
except ModuleNotFoundError:
    from core.lrc_parser import LyricLine, format_timestamp, parse_lrc_file, write_lrc_file


class LyricsEditorDialog(QDialog):
    lyrics_saved = pyqtSignal(str)

    def __init__(self, parent=None, lyrics_lines=None, song_info=None, lrc_file_path=""):
        super().__init__(parent)
        self.lyrics_lines = lyrics_lines or []
        self.song_info = song_info or {}
        self.lrc_file_path = lrc_file_path
        self._is_modified = False

        self.setWindowTitle(f"歌词编辑器 - {self.song_info.get('title', '未知歌曲')}")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self._init_ui()
        self._load_lyrics_to_editor()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)

        info_widget = QWidget()
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_widget.setLayout(info_layout)

        title_label = QLabel(f"歌曲: {self.song_info.get('title', '未知')}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(title_label)

        artist_label = QLabel(f"艺术家: {self.song_info.get('artist', '未知')}")
        artist_label.setStyleSheet("color: #888; font-size: 12px;")
        info_layout.addWidget(artist_label)
        info_layout.addStretch()

        layout.addWidget(info_widget)

        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(5)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_widget.setLayout(editor_layout)

        editor_label = QLabel("歌词内容 (格式: [mm:ss.xx]歌词文本):")
        editor_layout.addWidget(editor_label)

        self.lyrics_editor = QTextEdit()
        self.lyrics_editor.setFont(QFont("Consolas", 10))
        self.lyrics_editor.setPlaceholderText("[00:00.00]第一句歌词\n[00:05.50]第二句歌词\n...")
        self.lyrics_editor.textChanged.connect(self._on_text_changed)
        editor_layout.addWidget(self.lyrics_editor)

        layout.addWidget(editor_widget)

        offset_widget = QWidget()
        offset_layout = QHBoxLayout()
        offset_layout.setContentsMargins(0, 0, 0, 0)
        offset_layout.setSpacing(10)
        offset_widget.setLayout(offset_layout)

        offset_label = QLabel("全局时间偏移 (毫秒):")
        offset_layout.addWidget(offset_label)

        self.offset_input = QLineEdit("0")
        self.offset_input.setMaximumWidth(100)
        self.offset_input.setToolTip("正数=延后，负数=提前")
        offset_layout.addWidget(self.offset_input)

        apply_offset_btn = QPushButton("应用偏移")
        apply_offset_btn.clicked.connect(self._apply_global_offset)
        offset_layout.addWidget(apply_offset_btn)

        offset_layout.addStretch()
        layout.addWidget(offset_widget)

        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_widget.setLayout(button_layout)

        button_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(80)
        save_btn.clicked.connect(self._save_lyrics)
        button_layout.addWidget(save_btn)

        save_as_btn = QPushButton("另存为...")
        save_as_btn.setMinimumWidth(80)
        save_as_btn.clicked.connect(self._save_lyrics_as)
        button_layout.addWidget(save_as_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addWidget(button_widget)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _load_lyrics_to_editor(self):
        if not self.lyrics_lines:
            return

        lines_text = []
        for line in self.lyrics_lines:
            timestamp = format_timestamp(line.time_ms)
            lines_text.append(f"{timestamp}{line.text}")

        self.lyrics_editor.setPlainText("\n".join(lines_text))
        self._is_modified = False
        self._update_status()

    def _on_text_changed(self):
        self._is_modified = True
        self._update_status()

    def _update_status(self):
        text = self.lyrics_editor.toPlainText()
        line_count = len([l for l in text.split("\n") if l.strip()])
        modified_text = " (已修改)" if self._is_modified else ""
        self.status_label.setText(f"歌词行数: {line_count}{modified_text}")

    def _parse_editor_text(self):
        text = self.lyrics_editor.toPlainText()
        lines = []
        for line_text in text.split("\n"):
            line_text = line_text.strip()
            if not line_text:
                continue

            if line_text.startswith("["):
                end_bracket = line_text.find("]")
                if end_bracket > 0:
                    time_str = line_text[1:end_bracket]
                    lyric_text = line_text[end_bracket + 1 :].strip()
                    time_ms = self._parse_time_string(time_str)
                    if time_ms >= 0:
                        lines.append(LyricLine(time_ms=time_ms, text=lyric_text))
            else:
                lines.append(LyricLine(time_ms=len(lines) * 5000, text=line_text))

        lines.sort(key=lambda x: x.time_ms)
        return lines

    def _parse_time_string(self, time_str):
        try:
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    minutes = int(parts[0])
                    second_parts = parts[1].split(".")
                    seconds = int(second_parts[0])
                    centiseconds = int(second_parts[1]) if len(second_parts) > 1 else 0
                    return minutes * 60000 + seconds * 1000 + centiseconds * 10
        except (ValueError, IndexError):
            pass
        return -1

    def _apply_global_offset(self):
        try:
            offset_ms = int(self.offset_input.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的偏移量（整数）")
            return

        lines = self._parse_editor_text()
        if not lines:
            QMessageBox.warning(self, "错误", "没有可调整的歌词")
            return

        adjusted_lines = []
        for line in lines:
            new_time = line.time_ms + offset_ms
            if new_time >= 0:
                adjusted_lines.append(LyricLine(time_ms=new_time, text=line.text))

        adjusted_lines.sort(key=lambda x: x.time_ms)

        lines_text = []
        for line in adjusted_lines:
            timestamp = format_timestamp(line.time_ms)
            lines_text.append(f"{timestamp}{line.text}")

        self.lyrics_editor.setPlainText("\n".join(lines_text))
        self.offset_input.setText("0")
        QMessageBox.information(self, "成功", f"已应用偏移 {offset_ms}ms")

    def _save_lyrics(self):
        lines = self._parse_editor_text()
        if not lines:
            QMessageBox.warning(self, "错误", "没有可保存的歌词")
            return

        if not self.lrc_file_path:
            return self._save_lyrics_as()

        if write_lrc_file(self.lrc_file_path, lines):
            self._is_modified = False
            self._update_status()
            self.lyrics_saved.emit(self.lrc_file_path)
            QMessageBox.information(self, "成功", f"歌词已保存到:\n{self.lrc_file_path}")
            return True
        else:
            QMessageBox.critical(self, "错误", "保存歌词失败")
            return False

    def _save_lyrics_as(self):
        from PyQt5.QtWidgets import QFileDialog

        default_name = f"{self.song_info.get('title', 'lyrics')}.lrc"
        if self.lrc_file_path:
            default_dir = os.path.dirname(self.lrc_file_path)
        else:
            default_dir = os.getcwd()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存歌词文件", os.path.join(default_dir, default_name), "LRC歌词文件 (*.lrc);;所有文件 (*.*)"
        )

        if not file_path:
            return False

        lines = self._parse_editor_text()
        if not lines:
            QMessageBox.warning(self, "错误", "没有可保存的歌词")
            return False

        if write_lrc_file(file_path, lines):
            self.lrc_file_path = file_path
            self._is_modified = False
            self._update_status()
            self.lyrics_saved.emit(file_path)
            QMessageBox.information(self, "成功", f"歌词已保存到:\n{file_path}")
            return True
        else:
            QMessageBox.critical(self, "错误", "保存歌词失败")
            return False

    def closeEvent(self, event):
        if self._is_modified:
            reply = QMessageBox.question(
                self,
                "确认",
                "歌词已修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                if not self._save_lyrics():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()
