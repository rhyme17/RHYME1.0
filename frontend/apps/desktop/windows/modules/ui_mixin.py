from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QToolButton,
    QTreeWidget,
    QTabWidget,
    QSizePolicy,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

try:
    from frontend.apps.desktop.windows.modules.animated_slider import AnimatedProgressSlider
except ModuleNotFoundError:
    from apps.desktop.windows.modules.animated_slider import AnimatedProgressSlider

try:
    from frontend.apps.desktop.windows.modules.ui_binding_orchestration_service import UiBindingOrchestrationService
except ModuleNotFoundError:
    from apps.desktop.windows.modules.ui_binding_orchestration_service import UiBindingOrchestrationService


class PlaylistTreeWidget(QTreeWidget):
    class _ItemAdapter:
        def __init__(self, item):
            self._item = item

        def data(self, *args):
            if len(args) == 1:
                return self._item.data(0, args[0])
            if len(args) == 2:
                return self._item.data(args[0], args[1])
            raise TypeError("data() expects role or (column, role)")

        def setData(self, *args):
            if len(args) == 2:
                self._item.setData(0, args[0], args[1])
                return
            if len(args) == 3:
                self._item.setData(args[0], args[1], args[2])
                return
            raise TypeError("setData() expects (role, value) or (column, role, value)")

        def __getattr__(self, name):
            return getattr(self._item, name)

    def count(self):
        return self.topLevelItemCount()

    def item(self, row):
        item = self.topLevelItem(row)
        if item is None:
            return None
        return PlaylistTreeWidget._ItemAdapter(item)

    def setCurrentRow(self, row):
        item = self.topLevelItem(row)
        if item is not None:
            self.setCurrentItem(item)

    def takeItem(self, row):
        item = self.takeTopLevelItem(row)
        if item is None:
            return None
        return PlaylistTreeWidget._ItemAdapter(item)


class PlaylistSongsWidget(QTreeWidget):
    class _ItemAdapter:
        def __init__(self, item):
            self._item = item

        def data(self, *args):
            if len(args) == 1:
                return self._item.data(0, args[0])
            if len(args) == 2:
                return self._item.data(args[0], args[1])
            raise TypeError("data() expects role or (column, role)")

        def setData(self, *args):
            if len(args) == 2:
                self._item.setData(0, args[0], args[1])
                return
            if len(args) == 3:
                self._item.setData(args[0], args[1], args[2])
                return
            raise TypeError("setData() expects (role, value) or (column, role, value)")

        def __getattr__(self, name):
            return getattr(self._item, name)

    def count(self):
        return self.topLevelItemCount()

    def item(self, row):
        item = self.topLevelItem(row)
        if item is None:
            return None
        return PlaylistSongsWidget._ItemAdapter(item)

    def setCurrentRow(self, row):
        item = self.topLevelItem(row)
        if item is not None:
            self.setCurrentItem(item)

    def takeItem(self, row):
        item = self.takeTopLevelItem(row)
        if item is None:
            return None
        return PlaylistSongsWidget._ItemAdapter(item)


class UiMixin:
    def show_status_hint(self, message, timeout_ms=2800):
        text = str(message or "").strip()
        if not text:
            return
        try:
            if hasattr(self, "statusBar"):
                bar = self.statusBar()
                if bar is not None:
                    bar.showMessage(text, int(timeout_ms))
                    return
        except Exception:
            pass

    def show_nonblocking_error(self, message, timeout_ms=4200):
        text = str(message or "").strip()
        if not text:
            return
        self.show_status_hint(f"提示：{text}", timeout_ms=timeout_ms)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # 顶部第一层：全局操作区。
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        top_layout.addWidget(QLabel("全局操作"))
        self.open_scan_dialog_btn = QPushButton("添加音乐")
        top_layout.addWidget(self.open_scan_dialog_btn)
        self.create_playlist_btn = QPushButton("新建歌单")
        top_layout.addWidget(self.create_playlist_btn)
        self.settings_btn = QPushButton("设置")
        top_layout.addWidget(self.settings_btn)
        top_layout.addStretch()

        # 旧字段保留用于兼容历史逻辑，不再出现在顶部区域。
        self.playlist_name_input = QLineEdit()
        self.playlist_name_input.setPlaceholderText("修改当前歌单名")
        self.rename_playlist_btn = QPushButton("重命名")
        self.delete_playlist_btn = QPushButton("删除歌单")
        main_layout.addLayout(top_layout)

        # 保留旧字段兼容既有逻辑；页面上不再展示搜索和目录输入。
        self.search_input = QLineEdit()
        self.directory_input = QLineEdit()
        self.scan_btn = QPushButton("扫描音乐")
        self.browse_btn = QPushButton("浏览")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.main_splitter = splitter

        # 兼容旧逻辑保留数据列表，但主页面不再展示这个库视图。
        self.all_songs_list = QListWidget()
        self.artists_list = QListWidget()
        self.albums_list = QListWidget()
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.all_songs_list, "全部音乐")
        self.tab_widget.addTab(self.artists_list, "艺术家")
        self.tab_widget.addTab(self.albums_list, "专辑")

        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout(playlist_widget)
        playlist_layout.setContentsMargins(0, 0, 0, 0)
        playlist_layout.setSpacing(4)

        # 顶部第二层：当前歌单操作区。
        songlist_header = QHBoxLayout()
        songlist_header.setContentsMargins(0, 0, 0, 0)
        songlist_header.setSpacing(8)
        self.playlist_tree_toggle_btn = QToolButton()
        self.playlist_tree_toggle_btn.setArrowType(Qt.RightArrow)
        self.playlist_tree_toggle_btn.setAutoRaise(True)
        self.playlist_tree_toggle_btn.setToolTip("展开/收起歌单")
        self.current_playlist_label = QLabel("当前歌单：默认播放列表")
        self.add_to_playlist_btn = QPushButton("添加")
        self.remove_from_playlist_btn = QPushButton("移除")
        self.clear_playlist_btn = QPushButton("清空")
        self.undo_reorder_btn = QPushButton("撤销移动")
        self.undo_reorder_btn.setEnabled(False)
        songlist_header.addWidget(QLabel("当前歌单操作"))
        songlist_header.addWidget(self.playlist_tree_toggle_btn)
        songlist_header.addWidget(self.current_playlist_label)
        songlist_header.addStretch()
        songlist_header.addWidget(self.rename_playlist_btn)
        songlist_header.addWidget(self.delete_playlist_btn)
        songlist_header.addWidget(self.add_to_playlist_btn)
        songlist_header.addWidget(self.remove_from_playlist_btn)
        songlist_header.addWidget(self.clear_playlist_btn)
        songlist_header.addWidget(self.undo_reorder_btn)

        self.playlists_tree = PlaylistTreeWidget()
        self.playlists_tree.setHeaderHidden(True)
        self.playlists_tree.setRootIsDecorated(False)
        self.playlists_tree.setItemsExpandable(False)
        self.playlists_tree.setIndentation(0)

        # 兼容旧字段名，复用现有业务方法。
        self.playlists_list = self.playlists_tree

        self.playlist_list = PlaylistSongsWidget()
        self.playlist_list.setColumnCount(4)
        self.playlist_list.setHeaderLabels(["序号", "歌曲", "歌手", "时长"])
        self.playlist_list.setRootIsDecorated(False)
        self.playlist_list.setItemsExpandable(False)
        self.playlist_list.setIndentation(0)
        header = self.playlist_list.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.Interactive)
        header.setSectionResizeMode(3, header.ResizeToContents)
        header.resizeSection(2, 180)
        self.playlist_list.setAlternatingRowColors(True)
        self.playlist_list.setUniformRowHeights(True)
        self.playlist_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlist_list.setDefaultDropAction(Qt.MoveAction)
        self.playlist_list.setDragEnabled(True)
        self.playlist_list.setAcceptDrops(True)
        self.playlist_list.setDropIndicatorShown(True)

        self.playlist_empty_hint = QLabel("当前歌单暂无歌曲，请点击“添加音乐”或“添加”导入")
        self.playlist_empty_hint.setAlignment(Qt.AlignCenter)
        self.playlist_empty_hint.setStyleSheet("color: #777;")
        self.playlist_empty_hint.setVisible(False)

        playlist_layout.addLayout(songlist_header)
        playlist_layout.addWidget(self.playlists_tree)
        playlist_layout.addWidget(self.playlist_list)
        playlist_layout.addWidget(self.playlist_empty_hint)
        playlist_layout.setStretch(0, 0)
        playlist_layout.setStretch(1, 0)
        playlist_layout.setStretch(2, 1)
        playlist_layout.setStretch(3, 0)
        splitter.addWidget(playlist_widget)
        splitter.setSizes([1000])

        control_widget = QWidget()
        control_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(6)

        song_info_widget = QWidget()
        song_info_widget.setFixedHeight(32)
        song_info_layout = QHBoxLayout()
        song_info_layout.setContentsMargins(0, 0, 0, 0)
        song_info_widget.setLayout(song_info_layout)
        self.song_title_label = QLabel("未播放")
        self.song_artist_label = QLabel("-")
        song_info_layout.addWidget(self.song_title_label)
        song_info_layout.addWidget(self.song_artist_label)
        song_info_layout.addStretch()
        self.reload_lyrics_btn = QPushButton("重载歌词")
        song_info_layout.addWidget(self.reload_lyrics_btn)
        self.select_lyrics_btn = QPushButton("选择歌词")
        song_info_layout.addWidget(self.select_lyrics_btn)
        self.manual_lyrics_fetch_btn = QPushButton("在线获取歌词")
        song_info_layout.addWidget(self.manual_lyrics_fetch_btn)
        self.lyrics_asr_btn = QPushButton("识别歌词")
        self.lyrics_asr_btn.setEnabled(False)
        song_info_layout.addWidget(self.lyrics_asr_btn)

        progress_widget = QWidget()
        progress_widget.setFixedHeight(34)
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_widget.setLayout(progress_layout)
        self.current_time_label = QLabel("0:00")
        self.progress_slider = AnimatedProgressSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        if hasattr(self.progress_slider, "set_pulse_enabled"):
            self.progress_slider.set_pulse_enabled(bool(getattr(self, "progress_visual_pulse_enabled", True)))
        if hasattr(self.progress_slider, "set_wave_enabled"):
            self.progress_slider.set_wave_enabled(bool(getattr(self, "progress_visual_wave_enabled", True)))
        if hasattr(self.progress_slider, "set_accent_enabled"):
            self.progress_slider.set_accent_enabled(bool(getattr(self, "progress_visual_accent_enabled", True)))
        self.progress_slider.setStyleSheet(
            "\n".join(
                [
                    "QSlider::groove:horizontal {",
                    "    height: 6px;",
                    "    background: #d9dbe1;",
                    "    border-radius: 3px;",
                    "}",
                    "QSlider::sub-page:horizontal {",
                    "    background: #3b82f6;",
                    "    border-radius: 3px;",
                    "}",
                    "QSlider::add-page:horizontal {",
                    "    background: #d9dbe1;",
                    "    border-radius: 3px;",
                    "}",
                    "QSlider::handle:horizontal {",
                    "    background: #3b82f6;",
                    "    width: 6px;",
                    "    margin: -3px 0;",
                    "    border-radius: 3px;",
                    "}",
                ]
            )
        )
        self.total_time_label = QLabel("0:00")
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)

        buttons_widget = QWidget()
        buttons_widget.setFixedHeight(36)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_widget.setLayout(buttons_layout)
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        self.replay_btn = QPushButton("重播")

        volume_layout = QHBoxLayout()
        self.mute_btn = QPushButton("🔊")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.saved_volume)
        volume_layout.addWidget(self.mute_btn)
        volume_layout.addWidget(self.volume_slider)

        self.mode_btn = QPushButton("顺序播放")
        self.high_quality_btn = QPushButton("高音质：关")

        buttons_layout.addWidget(self.prev_btn)
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.next_btn)
        buttons_layout.addWidget(self.replay_btn)
        buttons_layout.addStretch()
        buttons_layout.addLayout(volume_layout)
        buttons_layout.addWidget(self.mode_btn)
        buttons_layout.addWidget(self.high_quality_btn)

        control_layout.addWidget(song_info_widget)

        lyrics_widget = QWidget()
        lyrics_layout = QVBoxLayout()
        lyrics_layout.setContentsMargins(0, 0, 0, 0)
        lyrics_layout.setSpacing(4)
        lyrics_widget.setLayout(lyrics_layout)

        lyrics_text_widget = QWidget()
        lyrics_text_widget.setFixedHeight(28)
        lyrics_text_layout = QHBoxLayout()
        lyrics_text_layout.setContentsMargins(0, 0, 0, 0)
        lyrics_text_widget.setLayout(lyrics_text_layout)
        self.lyric_label = QLabel("暂无歌词")
        self.lyric_label.setAlignment(Qt.AlignCenter)
        lyrics_text_layout.addWidget(self.lyric_label)

        lyrics_layout.addWidget(lyrics_text_widget)

        control_layout.addWidget(progress_widget)
        control_layout.addWidget(lyrics_widget)
        control_layout.addWidget(buttons_widget)

        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(control_widget, 0)

        UiBindingOrchestrationService.bind_all(self)

        # 确保启动时立即把滑块音量同步到底层音频输出，避免首次播放过响。
        if hasattr(self, "set_volume"):
            self.set_volume(int(self.volume_slider.value()), persist=False)

        self.set_playlist_tree_expanded(False)
        self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
        self.render_playlist()
        if hasattr(self, "refresh_high_quality_output_button"):
            self.refresh_high_quality_output_button()

    def set_playlist_tree_expanded(self, expanded):
        self.is_playlist_tree_expanded = bool(expanded)
        if hasattr(self, "playlists_tree"):
            self.playlists_tree.setVisible(self.is_playlist_tree_expanded)
        if hasattr(self, "playlist_tree_toggle_btn"):
            arrow = Qt.DownArrow if self.is_playlist_tree_expanded else Qt.RightArrow
            self.playlist_tree_toggle_btn.setArrowType(arrow)

    def toggle_playlist_tree_visibility(self):
        self.set_playlist_tree_expanded(not getattr(self, "is_playlist_tree_expanded", False))

