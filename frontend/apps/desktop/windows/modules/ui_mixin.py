import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from frontend.apps.desktop.windows.modules.animated_slider import AnimatedProgressSlider
except ModuleNotFoundError:
    from apps.desktop.windows.modules.animated_slider import AnimatedProgressSlider

try:
    from frontend.apps.desktop.windows.modules.audio_visualizer import AudioVisualizerWidget
except ModuleNotFoundError:
    from apps.desktop.windows.modules.audio_visualizer import AudioVisualizerWidget

try:
    from frontend.apps.desktop.windows.modules.ui_binding_orchestration_service import UiBindingOrchestrationService
except ModuleNotFoundError:
    from apps.desktop.windows.modules.ui_binding_orchestration_service import UiBindingOrchestrationService

try:
    from frontend.apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar
except ModuleNotFoundError:
    from apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar

try:
    from frontend.apps.desktop.windows.modules.font_manager import FontManager
except ModuleNotFoundError:
    from apps.desktop.windows.modules.font_manager import FontManager

try:
    from frontend.apps.desktop.windows.modules.theme_manager import ThemeManager
except ModuleNotFoundError:
    from apps.desktop.windows.modules.theme_manager import ThemeManager

try:
    from frontend.apps.desktop.windows.modules.button_style_manager import ButtonStyleManager
except ModuleNotFoundError:
    from apps.desktop.windows.modules.button_style_manager import ButtonStyleManager

try:
    from frontend.apps.desktop.windows.modules.song_info_display import SongInfoDisplay
except ModuleNotFoundError:
    from apps.desktop.windows.modules.song_info_display import SongInfoDisplay

try:
    from frontend.apps.desktop.windows.modules.status_notifier import StatusNotifier
except ModuleNotFoundError:
    from apps.desktop.windows.modules.status_notifier import StatusNotifier


class PlaylistTreeWidget(QTreeWidget):
    sort_requested = pyqtSignal(str)

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

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        sort_menu = menu.addMenu("排序歌单")

        sort_name_asc = sort_menu.addAction("按名称升序")
        sort_name_asc.triggered.connect(lambda: self.sort_requested.emit("name_asc"))

        sort_name_desc = sort_menu.addAction("按名称降序")
        sort_name_desc.triggered.connect(lambda: self.sort_requested.emit("name_desc"))

        sort_menu.addSeparator()

        sort_count_asc = sort_menu.addAction("按歌曲数升序")
        sort_count_asc.triggered.connect(lambda: self.sort_requested.emit("count_asc"))

        sort_count_desc = sort_menu.addAction("按歌曲数降序")
        sort_count_desc.triggered.connect(lambda: self.sort_requested.emit("count_desc"))

        menu.exec_(event.globalPos())


class PlaylistSongsWidget(QTreeWidget):
    files_dropped = pyqtSignal(list)
    play_next_requested = pyqtSignal(object)

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self._supported_audio_extensions = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma", ".ape"}

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in self._supported_audio_extensions:
                        file_paths.append(file_path)
            if file_paths and hasattr(self, "files_dropped") and self.files_dropped is not None:
                self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

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

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            return

        try:
            song = item.data(0, Qt.UserRole)
        except (TypeError, AttributeError):
            song = None

        if not song:
            return

        menu = QMenu(self)
        play_next_action = menu.addAction("下一首播放")
        play_next_action.triggered.connect(lambda: self.play_next_requested.emit(song))

        menu.exec_(event.globalPos())


class UiMixin:
    def __init__(self):
        super().__init__()
        self._init_managers()

    def _init_managers(self):
        self.font_manager = FontManager()
        self.theme_manager = ThemeManager(self.font_manager)
        self.button_style_manager = ButtonStyleManager()
        self.song_info_display = SongInfoDisplay()
        self.status_notifier = StatusNotifier(lambda: self.statusBar() if hasattr(self, "statusBar") else None)

    def show_status_hint(self, message, timeout_ms=2800):
        self.status_notifier.show_status_hint(message, timeout_ms)

    def show_nonblocking_error(self, message, timeout_ms=4200):
        self.status_notifier.show_nonblocking_error(message, timeout_ms)

    def update_song_info_labels(self, title="", artist=""):
        self.song_info_display.update_song_info_labels(
            getattr(self, "song_title_label", None),
            getattr(self, "song_artist_label", None),
            title,
            artist
        )

    def refresh_song_info_labels(self):
        if getattr(self, "_is_closing", False):
            return
        self.song_info_display.refresh_song_info_labels(
            getattr(self, "song_title_label", None),
            getattr(self, "song_artist_label", None)
        )

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        self.refresh_song_info_labels()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("rootCentralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # 顶部第一层：全局操作区。
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(10)
        top_layout.addWidget(QLabel("全局操作"))
        self.open_scan_dialog_btn = QPushButton("添加音乐")
        self.open_scan_dialog_btn.setToolTip("打开扫描窗口，导入本地音乐")
        top_layout.addWidget(self.open_scan_dialog_btn)
        self.online_search_btn = QPushButton("在线搜索")
        self.online_search_btn.setToolTip("搜索并下载在线音乐")
        top_layout.addWidget(self.online_search_btn)
        self.create_playlist_btn = QPushButton("新建歌单")
        self.create_playlist_btn.setToolTip("创建空歌单")
        top_layout.addWidget(self.create_playlist_btn)
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setToolTip("打开设置")
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
        playlist_widget.setObjectName("playlistPanel")
        playlist_layout = QVBoxLayout(playlist_widget)
        playlist_layout.setContentsMargins(8, 8, 8, 8)
        playlist_layout.setSpacing(6)

        # 顶部第二层：当前歌单操作区。
        songlist_header = QHBoxLayout()
        songlist_header.setContentsMargins(2, 2, 2, 2)
        songlist_header.setSpacing(10)
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
        self.playlists_tree.setObjectName("playlistTree")
        self.playlists_tree.setHeaderHidden(True)
        self.playlists_tree.setRootIsDecorated(False)
        self.playlists_tree.setItemsExpandable(False)
        self.playlists_tree.setIndentation(0)

        # 兼容旧字段名，复用现有业务方法。
        self.playlists_list = self.playlists_tree

        self.playlist_list = PlaylistSongsWidget()
        self.playlist_list.setObjectName("playlistSongs")
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
        self.playlist_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.playlist_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.playlist_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlist_list.setDefaultDropAction(Qt.MoveAction)
        self.playlist_list.setDragEnabled(True)
        self.playlist_list.setAcceptDrops(True)
        self.playlist_list.setDropIndicatorShown(True)

        self.playlist_empty_hint = QLabel("当前歌单暂无歌曲，请点击“添加音乐”或“添加”导入")
        self.playlist_empty_hint.setAlignment(Qt.AlignCenter)
        self.playlist_empty_hint.setObjectName("emptyHint")
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
        control_widget.setObjectName("controlPanel")
        control_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(8, 8, 8, 8)
        control_layout.setSpacing(8)

        song_info_widget = QWidget()
        song_info_widget.setObjectName("songInfoRow")
        song_info_widget.setMinimumHeight(38)
        song_info_layout = QHBoxLayout()
        song_info_layout.setContentsMargins(2, 1, 2, 1)
        song_info_layout.setSpacing(2)
        song_info_widget.setLayout(song_info_layout)
        self.song_title_label = QLabel("未播放")
        self.song_title_label.setObjectName("songTitle")
        self.song_title_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.song_title_label.setMinimumWidth(0)
        self.song_artist_label = QLabel("-")
        self.song_artist_label.setObjectName("songArtist")
        self.song_artist_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.song_artist_label.setMinimumWidth(0)
        song_info_layout.addWidget(self.song_title_label, 0)
        song_info_layout.addWidget(self.song_artist_label, 0)
        song_info_layout.addStretch(1)
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
        progress_widget.setObjectName("progressRow")
        progress_widget.setFixedHeight(34)
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(2, 1, 2, 1)
        progress_layout.setSpacing(8)
        progress_widget.setLayout(progress_layout)
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("currentTimeLabel")
        self.progress_slider = AnimatedProgressSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        if hasattr(self.progress_slider, "set_pulse_enabled"):
            self.progress_slider.set_pulse_enabled(bool(getattr(self, "progress_visual_pulse_enabled", True)))
        if hasattr(self.progress_slider, "set_wave_enabled"):
            self.progress_slider.set_wave_enabled(bool(getattr(self, "progress_visual_wave_enabled", True)))
        if hasattr(self.progress_slider, "set_accent_enabled"):
            self.progress_slider.set_accent_enabled(bool(getattr(self, "progress_visual_accent_enabled", True)))
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setObjectName("totalTimeLabel")
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)

        buttons_widget = QWidget()
        buttons_widget.setObjectName("playButtonsRow")
        buttons_widget.setFixedHeight(36)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(8)
        buttons_widget.setLayout(buttons_layout)
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        self.replay_btn = QPushButton("重播")

        self.prev_btn.setFixedWidth(38)
        self.play_btn.setFixedWidth(46)
        self.next_btn.setFixedWidth(38)

        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(4)
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(30, 24)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.saved_volume)
        self.volume_slider.setFixedWidth(118)
        volume_layout.addWidget(self.mute_btn)
        volume_layout.addWidget(self.volume_slider)

        self.mode_btn = QPushButton("顺序播放")
        self.high_quality_btn = QPushButton("高音质：关")

        self.lyrics_offset_backward_btn = QPushButton("◀ 提前0.5s")
        self.lyrics_offset_backward_btn.setToolTip("歌词提前显示0.5秒")
        self.lyrics_offset_label = QLabel("偏移: 0ms")
        self.lyrics_offset_label.setObjectName("lyricsOffsetLabel")
        self.lyrics_offset_forward_btn = QPushButton("延后0.5s ▶")
        self.lyrics_offset_forward_btn.setToolTip("歌词延后显示0.5秒")
        self.lyrics_offset_reset_btn = QPushButton("重置")
        self.lyrics_offset_reset_btn.setToolTip("重置歌词偏移")
        self.edit_lyrics_btn = QPushButton("编辑歌词")
        self.edit_lyrics_btn.setToolTip("打开歌词编辑器")
        self.desktop_lyrics_btn = QPushButton("桌面歌词")
        self.desktop_lyrics_btn.setToolTip("显示/隐藏桌面歌词")
        self.mini_mode_btn = QPushButton("迷你模式")
        self.mini_mode_btn.setToolTip("切换到迷你播放器")

        buttons_layout.addWidget(self.prev_btn)
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.next_btn)
        buttons_layout.addWidget(self.replay_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.lyrics_offset_backward_btn)
        buttons_layout.addWidget(self.lyrics_offset_label)
        buttons_layout.addWidget(self.lyrics_offset_forward_btn)
        buttons_layout.addWidget(self.lyrics_offset_reset_btn)
        buttons_layout.addWidget(self.edit_lyrics_btn)
        buttons_layout.addWidget(self.desktop_lyrics_btn)
        buttons_layout.addWidget(self.mini_mode_btn)
        buttons_layout.addStretch()
        buttons_layout.addLayout(volume_layout)
        buttons_layout.addWidget(self.mode_btn)
        buttons_layout.addWidget(self.high_quality_btn)

        control_layout.addWidget(song_info_widget)

        self.audio_visualizer = AudioVisualizerWidget()
        self.audio_visualizer.setObjectName("audioVisualizer")
        self.audio_visualizer.set_visualizer_visible(False)
        control_layout.addWidget(self.audio_visualizer)

        lyrics_widget = QWidget()
        lyrics_layout = QVBoxLayout()
        lyrics_layout.setContentsMargins(2, 2, 2, 2)
        lyrics_layout.setSpacing(6)
        lyrics_widget.setLayout(lyrics_layout)

        lyrics_text_widget = QWidget()
        lyrics_text_widget.setMinimumHeight(42)
        lyrics_text_layout = QHBoxLayout()
        lyrics_text_layout.setContentsMargins(2, 2, 2, 2)
        lyrics_text_widget.setLayout(lyrics_text_layout)
        self.lyric_label = QLabel("暂无歌词")
        self.lyric_label.setObjectName("lyricLabel")
        self.lyric_label.setAlignment(Qt.AlignCenter)
        self.lyric_label.setWordWrap(False)
        lyrics_text_layout.addWidget(self.lyric_label)

        lyrics_layout.addWidget(lyrics_text_widget)

        control_layout.addWidget(progress_widget)
        control_layout.addWidget(lyrics_widget)
        control_layout.addWidget(buttons_widget)

        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(control_widget, 0)

        UiBindingOrchestrationService.bind_all(self)

        # 统一按钮尺寸与层级样式，避免页面显得杂乱。
        self._apply_button_roles()
        self.apply_ui_font(getattr(self, "ui_font_weight", "regular"), reapply_theme=False)
        self.apply_lyrics_font_size(getattr(self, "lyrics_font_size", 18), reapply_theme=False)
        self.apply_ui_theme(getattr(self, "ui_theme", "light"))
        self.update_scan_cache_hint()
        self.update_song_info_labels(getattr(self, "_current_song_title_text", "未播放"), getattr(self, "_current_song_artist_text", "-"))

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

    def _apply_button_roles(self):
        primary_buttons = [
            getattr(self, "open_scan_dialog_btn", None),
            getattr(self, "online_search_btn", None),
            getattr(self, "create_playlist_btn", None),
            getattr(self, "settings_btn", None),
            getattr(self, "add_to_playlist_btn", None),
            getattr(self, "save_playlist_btn", None),
            getattr(self, "play_btn", None),
        ]
        
        danger_buttons = [
            getattr(self, "remove_from_playlist_btn", None),
            getattr(self, "clear_playlist_btn", None),
            getattr(self, "delete_playlist_btn", None),
        ]
        
        secondary_buttons = [
            getattr(self, "rename_playlist_btn", None),
            getattr(self, "undo_reorder_btn", None),
            getattr(self, "reload_lyrics_btn", None),
            getattr(self, "select_lyrics_btn", None),
            getattr(self, "manual_lyrics_fetch_btn", None),
            getattr(self, "lyrics_asr_btn", None),
            getattr(self, "prev_btn", None),
            getattr(self, "play_btn", None),
            getattr(self, "next_btn", None),
            getattr(self, "replay_btn", None),
            getattr(self, "mute_btn", None),
            getattr(self, "mode_btn", None),
            getattr(self, "high_quality_btn", None),
        ]
        
        for button in primary_buttons:
            self.button_style_manager.set_button_role(button, "primary")
        
        for button in danger_buttons:
            self.button_style_manager.set_button_role(button, "danger")
        
        for button in secondary_buttons:
            self.button_style_manager.set_button_role(button, "secondary")
        
        all_buttons = primary_buttons + danger_buttons + secondary_buttons
        self.button_style_manager.apply_minimum_height(all_buttons)

    def update_scan_cache_hint(self):
        return

    def apply_ui_font(self, font_weight="regular", reapply_theme=True):
        self.font_manager.apply_font(font_weight)
        if reapply_theme and hasattr(self, "apply_ui_theme"):
            self.apply_ui_theme(getattr(self, "ui_theme", "light"))

    def apply_lyrics_font_size(self, font_size=18, reapply_theme=True):
        normalized_size = self.song_info_display.normalize_lyrics_font_size(font_size)
        self.lyrics_font_size = normalized_size
        if reapply_theme and hasattr(self, "apply_ui_theme"):
            self.apply_ui_theme(getattr(self, "ui_theme", "light"))

    def apply_ui_theme(self, theme_name="light"):
        theme = str(theme_name or "light").strip().lower()
        if theme not in ("light", "dark"):
            theme = "light"
        self.ui_theme = theme
        set_immersive_dark_title_bar(self, theme == "dark")
        
        font_rule = self.font_manager.get_current_css_rule()
        theme_css = self.theme_manager.build_theme_stylesheet(
            theme, 
            getattr(self, "lyrics_font_size", 18)
        )
        
        if font_rule:
            self.setStyleSheet(f"{font_rule}\n{theme_css}")
        else:
            self.setStyleSheet(theme_css)
            
        if hasattr(self, "progress_slider"):
            self.progress_slider.setStyleSheet(
                self.theme_manager.build_progress_slider_stylesheet(theme)
            )
        self.refresh_song_info_labels()

