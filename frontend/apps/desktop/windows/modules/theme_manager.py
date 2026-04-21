try:
    from frontend.apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar
except ModuleNotFoundError:
    from apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar


class ThemeManager:
    def __init__(self, font_manager):
        self.font_manager = font_manager
        self._current_theme = "light"
        self._lyrics_font_size = 18

    def build_theme_stylesheet(self, theme, lyrics_font_size=18):
        self._lyrics_font_size = lyrics_font_size
        theme = str(theme or "light").strip().lower()
        if theme not in ("light", "dark"):
            theme = "light"
        self._current_theme = theme
        
        if theme == "dark":
            return self._build_dark_theme()
        return self._build_light_theme()

    def build_progress_slider_stylesheet(self, theme):
        theme = str(theme or "light").strip().lower()
        if theme == "dark":
            return "\n".join([
                "QSlider::groove:horizontal {",
                "    height: 8px;",
                "    background: #2a3242;",
                "    border: 1px solid #3b465b;",
                "    border-radius: 4px;",
                "}",
                "QSlider::sub-page:horizontal {",
                "    background: #2f7bff;",
                "    border-radius: 4px;",
                "}",
                "QSlider::add-page:horizontal {",
                "    background: #1b2230;",
                "    border-radius: 4px;",
                "}",
                "QSlider::handle:horizontal {",
                "    background: #c7d2e6;",
                "    border: 1px solid #5f6f8b;",
                "    width: 12px;",
                "    margin: -4px 0;",
                "    border-radius: 6px;",
                "}",
            ])
        return "\n".join([
            "QSlider::groove:horizontal {",
            "    height: 8px;",
            "    background: #d6e6ff;",
            "    border-radius: 4px;",
            "}",
            "QSlider::sub-page:horizontal {",
            "    background: #2f7bff;",
            "    border-radius: 4px;",
            "}",
            "QSlider::add-page:horizontal {",
            "    background: #d6e6ff;",
            "    border-radius: 4px;",
            "}",
            "QSlider::handle:horizontal {",
            "    background: #ffffff;",
            "    border: 2px solid #2f7bff;",
            "    width: 12px;",
            "    margin: -4px 0;",
            "    border-radius: 6px;",
            "}",
        ])

    def _build_dark_theme(self):
        lyrics_font_size = self._lyrics_font_size
        song_title_size = 16
        song_artist_size = 12
        return "\n".join([
            "QMainWindow { background: #11151d; color: #ffffff; }",
            "QStatusBar { background: #11151d; color: #ffffff; border-top: 1px solid #4a4a4a; }",
            "QWidget#rootCentralWidget { background: #11151d; color: #ffffff; }",
            "QWidget#rootCentralWidget QLabel { color: #ffffff; }",
            "QWidget#playlistPanel, QWidget#controlPanel { background: #161b25; border: 1px solid #4a4a4a; border-radius: 10px; }",
            "QWidget#songInfoRow, QWidget#progressRow, QWidget#playButtonsRow { background: transparent; }",
            f"QLabel#songTitle {{ font-size: {song_title_size}px; font-weight: 700; color: #ffffff; }}",
            f"QLabel#songArtist {{ font-size: {song_artist_size}px; color: #ffffff; }}",
            "QLabel#currentTimeLabel, QLabel#totalTimeLabel { color: #ffffff; }",
            f"QLabel#lyricLabel {{ font-size: {lyrics_font_size}px; color: #ffffff; font-weight: 600; }}",
            "QLabel#emptyHint { color: #ffffff; }",
            "QTreeWidget#playlistTree, QTreeWidget#playlistSongs, QListWidget {",
            "  background: #10141b; border: 1px solid #2c3648; border-radius: 8px; color: #ffffff; alternate-background-color: #1b1f26;",
            "}",
            "QTreeWidget#playlistTree::viewport, QTreeWidget#playlistSongs::viewport, QListWidget::viewport { background: #10141b; }",
            "QTreeWidget#playlistTree::item, QTreeWidget#playlistSongs::item, QListWidget::item { color: #ffffff; padding: 2px 2px; }",
            "QTreeWidget#playlistSongs::item:alternate, QListWidget::item:alternate { background: #1b1f26; }",
            "QTreeWidget#playlistSongs::item:!alternate, QListWidget::item:!alternate { background: #10141b; }",
            "QTreeWidget#playlistTree::item:selected, QTreeWidget#playlistSongs::item:selected, QListWidget::item:selected {",
            "  background: #2057c9; color: #ffffff;",
            "}",
            "QPushButton { border-radius: 6px; padding: 5px 11px; border: 1px solid #3e4a60; background: #232b39; color: #e9f1ff; font-size: 13px; }",
            "QPushButton:hover { background: #2a3445; }",
            "QPushButton[btnRole='primary'] { background: #2f7bff; border-color: #2f7bff; color: #ffffff; }",
            "QPushButton[btnRole='primary']:hover { background: #245fd1; }",
            "QPushButton[text='▶'] { border-radius: 14px; padding: 3px 0; font-weight: 700; font-size: 14px; }",
            "QPushButton[btnRole='danger'] { background: #d94d5c; border-color: #d94d5c; color: #ffffff; }",
            "QPushButton[btnRole='danger']:hover { background: #c83d4c; }",
            "QHeaderView::section { background: #20293a; color: #e8f0ff; border: 1px solid #4a4a4a; padding: 6px 5px; font-weight: 600; }",
            "QLineEdit, QComboBox, QSpinBox { background: #20293a; color: #ffffff; border: 1px solid #2d3a4f; border-radius: 7px; padding: 4px 8px; }",
            "QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #2f7bff; }",
            "QComboBox QAbstractItemView { background: #161b25; color: #ffffff; selection-background-color: #2057c9; selection-color: #ffffff; }",
            "QSlider#volumeSlider::groove:horizontal { height: 6px; background: #364357; border-radius: 3px; }",
            "QSlider#volumeSlider::sub-page:horizontal { background: #2f7bff; border-radius: 3px; }",
            "QSlider#volumeSlider::handle:horizontal { width: 10px; margin: -3px 0; border-radius: 5px; background: #ffffff; border: 1px solid #2f7bff; }",
            "QScrollBar:vertical { background: #161b25; width: 10px; margin: 0; border: 1px solid #3a4559; }",
            "QScrollBar::handle:vertical { background: #4a556d; min-height: 24px; border-radius: 4px; }",
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }",
            "QScrollBar:horizontal { background: #161b25; height: 10px; margin: 0; border: 1px solid #3a4559; }",
            "QScrollBar::handle:horizontal { background: #4a556d; min-width: 24px; border-radius: 4px; }",
            "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }",
        ])

    def _build_light_theme(self):
        lyrics_font_size = self._lyrics_font_size
        song_title_size = 17
        song_artist_size = 12
        return "\n".join([
            "QWidget#rootCentralWidget { background: #edf4ff; color: #0f2547; }",
            "QWidget#playlistPanel, QWidget#controlPanel { background: #ffffff; border: 1px solid #c8dbff; border-radius: 12px; }",
            "QWidget#songInfoRow, QWidget#progressRow, QWidget#playButtonsRow { background: transparent; }",
            f"QLabel#songTitle {{ font-size: {song_title_size}px; font-weight: 700; color: #0b2f74; }}",
            f"QLabel#songArtist {{ font-size: {song_artist_size}px; color: #4d6491; font-weight: 500; }}",
            f"QLabel#lyricLabel {{ color: #1a376b; font-size: {lyrics_font_size}px; font-weight: 600; }}",
            "QLabel#emptyHint { color: #5f79a6; }",
            "QTreeWidget#playlistTree, QTreeWidget#playlistSongs, QListWidget {",
            "  background: #ffffff; border: 1px solid #c8dbff; border-radius: 10px; color: #143263;",
            "}",
            "QTreeWidget#playlistTree::item, QTreeWidget#playlistSongs::item, QListWidget::item { color: #143263; padding: 2px 2px; }",
            "QTreeWidget#playlistTree::item:selected, QTreeWidget#playlistSongs::item:selected, QListWidget::item:selected {",
            "  background: #d8e8ff; color: #0b3a91;",
            "}",
            "QTreeWidget#playlistTree::item:hover, QTreeWidget#playlistSongs::item:hover, QListWidget::item:hover {",
            "  background: #edf4ff;",
            "}",
            "QPushButton { border-radius: 7px; padding: 5px 11px; border: 1px solid #b9d2ff; background: #ffffff; color: #24457d; font-weight: 500; font-size: 13px; }",
            "QPushButton:hover { background: #e9f2ff; border-color: #8cb4ff; }",
            "QPushButton:pressed { background: #dceaff; }",
            "QPushButton[btnRole='primary'] { background: #2f7bff; border-color: #2f7bff; color: #ffffff; font-weight: 700; }",
            "QPushButton[btnRole='primary']:hover { background: #2468dc; }",
            "QPushButton[text='▶'] { border-radius: 14px; padding: 3px 0; font-size: 14px; }",
            "QPushButton[btnRole='danger'] { background: #ff5b69; border-color: #ff5b69; color: #ffffff; font-weight: 700; }",
            "QPushButton[btnRole='danger']:hover { background: #ea4a58; }",
            "QHeaderView::section { background: #eaf2ff; color: #2f4e86; border: none; padding: 6px 5px; font-weight: 600; }",
            "QToolButton { border-radius: 6px; padding: 2px 4px; color: #2f5fb0; }",
            "QToolButton:hover { background: #e1eeff; }",
            "QLineEdit { border: 1px solid #bfd6ff; border-radius: 7px; padding: 4px 8px; background: #ffffff; color: #143263; }",
            "QLineEdit:focus { border: 1px solid #2f7bff; }",
            "QTabWidget::pane { border: 1px solid #c8dbff; border-radius: 8px; background: #ffffff; }",
            "QTabBar::tab { background: #eaf2ff; color: #305285; border: 1px solid #c8dbff; padding: 4px 10px; border-top-left-radius: 7px; border-top-right-radius: 7px; }",
            "QTabBar::tab:selected { background: #ffffff; color: #1c4ea1; }",
            "QSlider#volumeSlider::groove:horizontal { height: 6px; background: #d6e6ff; border-radius: 3px; }",
            "QSlider#volumeSlider::sub-page:horizontal { background: #2f7bff; border-radius: 3px; }",
            "QSlider#volumeSlider::handle:horizontal { width: 10px; margin: -3px 0; border-radius: 5px; background: #ffffff; border: 1px solid #2f7bff; }",
        ])

    def get_current_theme(self):
        return self._current_theme