from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class SongSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加已扫描音乐")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(680, 480)
        self._all_songs = []
        self._build_ui()
        self._apply_theme_styles()

    def _detect_theme(self):
        parent = self.parent()
        theme = "light"
        if parent is not None:
            theme = str(getattr(parent, "ui_theme", "light") or "light")
        theme = theme.strip().lower()
        return theme if theme in ("light", "dark") else "light"

    def _apply_theme_styles(self):
        if self._detect_theme() != "dark":
            return
        self.setStyleSheet(
            "\n".join(
                [
                    "QDialog { background: #11151d; color: #ffffff; border: 1px solid #4a4a4a; }",
                    "QLabel { color: #ffffff; }",
                    "QLineEdit { background: #20293a; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px 8px; }",
                    "QLineEdit:focus { border: 1px solid #2f7bff; }",
                    "QListWidget { background: #10141b; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 8px; }",
                    "QListWidget::item { color: #ffffff; }",
                    "QListWidget::item:selected { background: #2057c9; color: #ffffff; }",
                    "QPushButton { background: #232b39; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px 10px; }",
                    "QPushButton:hover { background: #2a3445; }",
                ]
            )
        )

    def _build_ui(self):
        layout = QVBoxLayout(self)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("搜索："))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("按歌曲名/歌手/专辑过滤")
        search_row.addWidget(self.search_input, 1)

        result_label = QLabel("扫描缓存歌曲（可多选）：")
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        action_row = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.invert_selection_btn = QPushButton("反选")
        self.confirm_btn = QPushButton("加入当前歌单")
        self.cancel_btn = QPushButton("取消")
        action_row.addWidget(self.select_all_btn)
        action_row.addWidget(self.invert_selection_btn)
        action_row.addStretch()
        action_row.addWidget(self.confirm_btn)
        action_row.addWidget(self.cancel_btn)

        self.hint_label = QLabel("请选择要加入的歌曲")
        self.hint_label.setAlignment(Qt.AlignLeft)

        layout.addLayout(search_row)
        layout.addWidget(result_label)
        layout.addWidget(self.results_list, 1)
        layout.addLayout(action_row)
        layout.addWidget(self.hint_label)

        self.search_input.textChanged.connect(self.apply_filter)
        self.select_all_btn.clicked.connect(self.select_all_visible)
        self.invert_selection_btn.clicked.connect(self.invert_visible_selection)
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.cancel_btn.clicked.connect(self.reject)

    def set_songs(self, songs):
        self._all_songs = [dict(song) for song in (songs or [])]
        self.apply_filter(self.search_input.text())

    def apply_filter(self, query=""):
        keyword = (query or "").strip().lower()
        self.results_list.clear()
        filtered_count = 0
        for song in self._all_songs:
            haystack = " ".join(
                [
                    str(song.get("title", "")),
                    str(song.get("artist", "")),
                    str(song.get("album", "")),
                ]
            ).lower()
            if keyword and keyword not in haystack:
                continue
            text = f"{song.get('title', '')} - {song.get('artist', '')}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, song)
            self.results_list.addItem(item)
            filtered_count += 1

        total_count = len(self._all_songs)
        self.hint_label.setText(f"显示 {filtered_count} / {total_count} 首")

    def selected_songs(self):
        items = self.results_list.selectedItems()
        return [item.data(Qt.UserRole) for item in items if item.data(Qt.UserRole)]

    def select_all_visible(self):
        self.results_list.selectAll()

    def invert_visible_selection(self):
        for index in range(self.results_list.count()):
            item = self.results_list.item(index)
            item.setSelected(not item.isSelected())

    def _on_confirm(self):
        if not self.selected_songs():
            self.hint_label.setText("请先选择至少一首歌曲")
            return
        self.accept()


