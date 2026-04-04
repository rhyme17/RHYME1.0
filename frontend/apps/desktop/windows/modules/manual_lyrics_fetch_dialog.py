from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout


class ManualLyricsFetchDialog(QDialog):
    def __init__(self, parent=None, default_title="", default_artist=""):
        super().__init__(parent)
        self.setWindowTitle("手动在线获取歌词")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(460, 160)

        self.title_input = QLineEdit(str(default_title or "").strip())
        self.title_input.setPlaceholderText("歌曲名（必填）")
        self.artist_input = QLineEdit(str(default_artist or "").strip())
        self.artist_input.setPlaceholderText("歌手（可留空）")
        self.hint_label = QLabel("请输入歌曲名，可选填写歌手提高匹配准确度")

        layout = QVBoxLayout(self)

        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("歌曲名："))
        title_row.addWidget(self.title_input, 1)

        artist_row = QHBoxLayout()
        artist_row.addWidget(QLabel("歌手："))
        artist_row.addWidget(self.artist_input, 1)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.confirm_btn = QPushButton("获取")
        self.cancel_btn = QPushButton("取消")
        action_row.addWidget(self.confirm_btn)
        action_row.addWidget(self.cancel_btn)

        layout.addLayout(title_row)
        layout.addLayout(artist_row)
        layout.addWidget(self.hint_label)
        layout.addLayout(action_row)

        self.confirm_btn.clicked.connect(self._on_confirm)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_confirm(self):
        if not self.title_text:
            self.hint_label.setText("歌曲名不能为空")
            self.title_input.setFocus()
            return
        self.accept()

    @property
    def title_text(self):
        return str(self.title_input.text() or "").strip()

    @property
    def artist_text(self):
        return str(self.artist_input.text() or "").strip()

