from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QAbstractItemView, QProgressBar


class OnlineSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("搜索音乐")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(700, 560)
        self.setMinimumSize(500, 400)

        self._results_data = []
        self._search_worker = None

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入歌曲名、歌手或专辑")
        self.search_input.returnPressed.connect(self._on_search)
        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedWidth(70)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)

        self.library_label = QLabel("📚 音乐库")
        self.library_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px 0;")
        self.library_label.hide()
        layout.addWidget(self.library_label)

        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderLabels(["歌曲", "歌手", "专辑"])
        self.library_tree.setRootIsDecorated(False)
        self.library_tree.setAlternatingRowColors(True)
        self.library_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.library_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.library_tree.setUniformRowHeights(True)
        self.library_tree.setMaximumHeight(180)
        lib_header = self.library_tree.header()
        lib_header.setStretchLastSection(False)
        lib_header.setSectionResizeMode(0, lib_header.Stretch)
        lib_header.setSectionResizeMode(1, lib_header.Interactive)
        lib_header.setSectionResizeMode(2, lib_header.Interactive)
        lib_header.resizeSection(1, 140)
        lib_header.resizeSection(2, 140)
        self.library_tree.itemDoubleClicked.connect(self._on_library_double_click)
        self.library_tree.hide()
        layout.addWidget(self.library_tree)

        self.online_label = QLabel("🌐 在线搜索")
        self.online_label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px 0;")
        self.online_label.hide()
        layout.addWidget(self.online_label)

        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["歌曲", "歌手", "专辑", "来源"])
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_tree.setUniformRowHeights(True)
        header = self.result_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.Stretch)
        header.setSectionResizeMode(1, header.Interactive)
        header.setSectionResizeMode(2, header.Interactive)
        header.setSectionResizeMode(3, header.ResizeToContents)
        header.resizeSection(1, 140)
        header.resizeSection(2, 140)
        self.result_tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.result_tree, 1)

        self.hint_label = QLabel("输入关键词搜索，优先从音乐库查找")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setObjectName("hintLabel")
        layout.addWidget(self.hint_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.play_btn = QPushButton("播放")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._on_play)
        self.download_btn = QPushButton("下载到音乐库")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._on_download)
        self.download_lyric_btn = QPushButton("下载歌词")
        self.download_lyric_btn.setEnabled(False)
        self.download_lyric_btn.clicked.connect(self._on_download_lyric)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        action_row.addWidget(self.play_btn)
        action_row.addWidget(self.download_btn)
        action_row.addWidget(self.download_lyric_btn)
        action_row.addStretch()
        action_row.addWidget(self.close_btn)
        layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(18)
        layout.addWidget(self.progress_bar)

        self.library_tree.itemSelectionChanged.connect(self._on_library_selection_changed)
        self.result_tree.itemSelectionChanged.connect(self._on_online_selection_changed)
        self._apply_theme_styles()

    def _detect_theme(self):
        parent = self.parent()
        theme = "light"
        if parent is not None:
            theme = str(getattr(parent, "ui_theme", "light") or "light")
        return theme.strip().lower() if theme.strip().lower() in ("light", "dark") else "light"

    def _apply_theme_styles(self):
        if self._detect_theme() != "dark":
            return
        self.setStyleSheet(
            "\n".join([
                "QDialog { background: #11151d; color: #ffffff; border: 1px solid #4a4a4a; }",
                "QLabel { color: #ffffff; }",
                "QLineEdit { background: #20293a; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px 8px; }",
                "QLineEdit:focus { border: 1px solid #2f7bff; }",
                "QTreeWidget { background: #11151d; color: #ffffff; border: 1px solid #4a4a4a; alternate-background-color: #161b26; }",
                "QTreeWidget::item:selected { background: #2f7bff; }",
                "QTreeWidget::item:hover { background: #1e2738; }",
                "QHeaderView::section { background: #161b26; color: #ffffff; border: 1px solid #4a4a4a; padding: 4px; }",
                "QPushButton { background: #232b39; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px 10px; }",
                "QPushButton:hover { background: #2a3445; }",
                "QPushButton:disabled { background: #1a1f2a; color: #5a5a6a; }",
                "QProgressBar { background: #20293a; border: 1px solid #4a4a4a; border-radius: 4px; text-align: center; color: #ffffff; }",
                "QProgressBar::chunk { background: #2f7bff; border-radius: 3px; }",
            ])
        )

    def _on_search(self):
        keyword = str(self.search_input.text() or "").strip()
        if not keyword:
            self.hint_label.setText("请输入搜索关键词")
            return

        self.search_btn.setEnabled(False)
        self.hint_label.setText("搜索中...")
        self.library_tree.clear()
        self.result_tree.clear()
        self._results_data = []

        parent = self.parent()
        if parent and hasattr(parent, "music_library"):
            local_results = parent.music_library.search(keyword)
            if local_results:
                self.library_label.show()
                self.library_tree.show()
                for song in local_results:
                    item = QTreeWidgetItem([
                        song.get("title", ""),
                        song.get("artist", ""),
                        song.get("album", ""),
                    ])
                    item.setData(0, Qt.UserRole, {"source": "library", **song})
                    self.library_tree.addTopLevelItem(item)
                self.library_label.setText(f"📚 音乐库 ({len(local_results)})")
            else:
                self.library_label.hide()
                self.library_tree.hide()

        if not self._check_network():
            self.hint_label.setText("网络未连接，仅显示本地音乐库结果")
            self.search_btn.setEnabled(True)
            return

        from frontend.apps.desktop.windows.modules.online_workers import OnlineSearchWorker
        self._search_worker = OnlineSearchWorker(
            parent.online_music_service, keyword, "netease", parent=self
        )
        self._search_worker.finished_with_result.connect(self._on_search_finished)
        self._search_worker.start()

    def _on_search_finished(self, success, songs_data, error):
        self.search_btn.setEnabled(True)
        if not success:
            self.hint_label.setText(f"在线搜索失败: {error}")
            self.online_label.hide()
            return

        self._results_data = songs_data
        if not songs_data:
            self.online_label.hide()
            self.hint_label.setText("在线搜索无结果")
            return

        self.online_label.show()
        self.online_label.setText(f"🌐 在线搜索 ({len(songs_data)})")
        for song in songs_data:
            item = QTreeWidgetItem([
                song.get("name", ""),
                song.get("artist", ""),
                song.get("album", ""),
                "网易云",
            ])
            item.setData(0, Qt.UserRole, {"source": "online", **song})
            self.result_tree.addTopLevelItem(item)

        self.hint_label.setText(f"找到 {len(songs_data)} 首在线歌曲")

    def _on_library_selection_changed(self):
        has_selection = self.library_tree.currentItem() is not None
        if has_selection:
            self.result_tree.clearSelection()
        self.play_btn.setEnabled(has_selection)
        self.download_btn.setEnabled(False)
        self.download_lyric_btn.setEnabled(False)

    def _on_online_selection_changed(self):
        has_selection = self.result_tree.currentItem() is not None
        if has_selection:
            self.library_tree.clearSelection()
        self.download_btn.setEnabled(has_selection)
        self.download_lyric_btn.setEnabled(has_selection)
        self.play_btn.setEnabled(has_selection)

    def _get_selected(self):
        lib_item = self.library_tree.currentItem()
        if lib_item:
            return lib_item.data(0, Qt.UserRole)
        online_item = self.result_tree.currentItem()
        if online_item:
            return online_item.data(0, Qt.UserRole)
        return None

    def _on_library_double_click(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data and data.get("source") == "library":
            parent = self.parent()
            if parent and hasattr(parent, "_play_song"):
                parent._play_song(data)
                self.hint_label.setText(f"正在播放: {data.get('artist', '')} - {data.get('title', '')}")

    def _on_double_click(self, item, column):
        song = item.data(0, Qt.UserRole)
        if song and song.get("source") == "online":
            self._play_preview(song)

    def _on_play(self):
        data = self._get_selected()
        if not data:
            return
        if data.get("source") == "library":
            parent = self.parent()
            if parent and hasattr(parent, "_play_song"):
                parent._play_song(data)
                self.hint_label.setText(f"正在播放: {data.get('artist', '')} - {data.get('title', '')}")
        else:
            self._play_preview(data)

    def _play_preview(self, song):
        if not self._check_network():
            self.hint_label.setText("网络未连接，无法试听")
            return
        parent = self.parent()
        if parent and hasattr(parent, "play_online_preview"):
            parent.play_online_preview(song)
            self.hint_label.setText(f"正在试听: {song.get('artist', '')} - {song.get('name', '')}")

    def _on_download(self):
        song = self._get_selected()
        if not song or song.get("source") != "online":
            return
        if not self._check_network():
            self.hint_label.setText("网络未连接，无法下载")
            return
        parent = self.parent()
        if parent and hasattr(parent, "download_online_song"):
            parent.download_online_song(song)
            self.hint_label.setText(f"正在下载: {song.get('artist', '')} - {song.get('name', '')}")

    def _on_download_lyric(self):
        song = self._get_selected()
        if not song or song.get("source") != "online":
            return
        if not self._check_network():
            self.hint_label.setText("网络未连接，无法下载歌词")
            return
        parent = self.parent()
        if parent and hasattr(parent, "download_online_lyric"):
            parent.download_online_lyric(song)
            self.hint_label.setText(f"正在下载歌词: {song.get('name', '')}")

    def _check_network(self):
        parent = self.parent()
        if parent and hasattr(parent, "online_music_service"):
            return parent.online_music_service.is_network_available
        return True
