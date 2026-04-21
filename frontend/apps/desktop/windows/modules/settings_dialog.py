from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QSpinBox,
    QWidget,
    QVBoxLayout,
)

try:
    from frontend.apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar
except ModuleNotFoundError:
    from apps.desktop.windows.modules.windows_titlebar import set_immersive_dark_title_bar


class SettingsDialog(QDialog):
    def __init__(self, initial_settings, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(760, 520)
        self.setMinimumSize(680, 460)
        self.setSizeGripEnabled(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("settingsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.viewport().setObjectName("settingsScrollViewport")
        root.addWidget(self.scroll_area, 1)

        content = QWidget()
        content.setObjectName("settingsScrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        self.scroll_area.setWidget(content)

        tray_group = QGroupBox("托盘与窗口")
        tray_form = QFormLayout(tray_group)
        tray_desc = QLabel("控制关闭窗口时的行为与托盘驻留方式")
        tray_desc.setWordWrap(True)
        tray_form.addRow(tray_desc)
        self.tray_enabled_checkbox = QCheckBox("启用系统托盘")
        self.tray_enabled_checkbox.setChecked(bool(initial_settings.get("tray_enabled", True)))
        tray_form.addRow(self.tray_enabled_checkbox)

        self.close_to_tray_checkbox = QCheckBox("点击关闭时隐藏到托盘")
        self.close_to_tray_checkbox.setChecked(bool(initial_settings.get("close_to_tray_enabled", False)))
        tray_form.addRow(self.close_to_tray_checkbox)
        content_layout.addWidget(tray_group)

        keyboard_group = QGroupBox("键盘控制")
        keyboard_form = QFormLayout(keyboard_group)
        keyboard_desc = QLabel("快捷键步长：上/下调音量，左/右调进度")
        keyboard_desc.setWordWrap(True)
        keyboard_form.addRow(keyboard_desc)
        self.keyboard_volume_step_spin = QSpinBox()
        self.keyboard_volume_step_spin.setRange(1, 20)
        self.keyboard_volume_step_spin.setValue(int(initial_settings.get("keyboard_volume_step", 5)))
        keyboard_form.addRow("音量步长", self.keyboard_volume_step_spin)

        self.keyboard_seek_step_spin = QSpinBox()
        self.keyboard_seek_step_spin.setRange(1, 30)
        self.keyboard_seek_step_spin.setValue(int(initial_settings.get("keyboard_seek_step_seconds", 5)))
        keyboard_form.addRow("快进/快退步长(秒)", self.keyboard_seek_step_spin)
        content_layout.addWidget(keyboard_group)

        audio_group = QGroupBox("音频")
        audio_form = QFormLayout(audio_group)
        audio_desc = QLabel("输出策略和响度统一仅影响本播放器，不改系统全局设置")
        audio_desc.setWordWrap(True)
        audio_form.addRow(audio_desc)
        self.audio_output_strategy_combo = QComboBox()
        self.audio_output_strategy_combo.addItem("跟随系统默认", "follow_system")
        self.audio_output_strategy_combo.addItem("固定当前输出设备", "fixed_current")
        strategy_value = str(initial_settings.get("audio_output_strategy", "follow_system") or "follow_system")
        strategy_index = self.audio_output_strategy_combo.findData(strategy_value)
        self.audio_output_strategy_combo.setCurrentIndex(strategy_index if strategy_index >= 0 else 0)
        audio_form.addRow("输出设备策略", self.audio_output_strategy_combo)

        self.high_quality_output_checkbox = QCheckBox("启用高音质输出")
        self.high_quality_output_checkbox.setChecked(bool(initial_settings.get("high_quality_output", False)))
        audio_form.addRow(self.high_quality_output_checkbox)

        self.volume_uniformity_level_combo = QComboBox()
        self.volume_uniformity_level_combo.addItem("关闭", "off")
        self.volume_uniformity_level_combo.addItem("轻度", "light")
        self.volume_uniformity_level_combo.addItem("中度", "medium")
        self.volume_uniformity_level_combo.addItem("强", "strong")
        uniformity_value = str(initial_settings.get("volume_uniformity_level", "medium") or "medium")
        uniformity_index = self.volume_uniformity_level_combo.findData(uniformity_value)
        self.volume_uniformity_level_combo.setCurrentIndex(uniformity_index if uniformity_index >= 0 else 2)
        audio_form.addRow("音量统一强度", self.volume_uniformity_level_combo)
        content_layout.addWidget(audio_group)

        visual_group = QGroupBox("界面与动效")
        visual_form = QFormLayout(visual_group)
        self.ui_font_weight_combo = QComboBox()
        self.ui_font_weight_combo.addItem("细体", "light")
        self.ui_font_weight_combo.addItem("常规", "regular")
        self.ui_font_weight_combo.addItem("中粗", "medium")
        ui_font_weight_value = str(initial_settings.get("ui_font_weight", "regular") or "regular")
        ui_font_weight_index = self.ui_font_weight_combo.findData(ui_font_weight_value)
        self.ui_font_weight_combo.setCurrentIndex(ui_font_weight_index if ui_font_weight_index >= 0 else 1)
        visual_form.addRow("界面字重", self.ui_font_weight_combo)

        self.ui_theme_combo = QComboBox()
        self.ui_theme_combo.addItem("浅色", "light")
        self.ui_theme_combo.addItem("深色", "dark")
        ui_theme_value = str(initial_settings.get("ui_theme", "light") or "light")
        ui_theme_index = self.ui_theme_combo.findData(ui_theme_value)
        self.ui_theme_combo.setCurrentIndex(ui_theme_index if ui_theme_index >= 0 else 0)
        visual_form.addRow("界面主题", self.ui_theme_combo)

        self.lyrics_font_size_spin = QSpinBox()
        self.lyrics_font_size_spin.setRange(12, 28)
        self.lyrics_font_size_spin.setValue(int(initial_settings.get("lyrics_font_size", 18)))
        visual_form.addRow("歌词字号", self.lyrics_font_size_spin)

        self.visual_pulse_checkbox = QCheckBox("脉冲动效")
        self.visual_pulse_checkbox.setChecked(bool(initial_settings.get("progress_visual_pulse_enabled", True)))
        visual_form.addRow(self.visual_pulse_checkbox)

        self.visual_wave_checkbox = QCheckBox("波浪动效")
        self.visual_wave_checkbox.setChecked(bool(initial_settings.get("progress_visual_wave_enabled", True)))
        visual_form.addRow(self.visual_wave_checkbox)

        self.visual_accent_checkbox = QCheckBox("重音抖动")
        self.visual_accent_checkbox.setChecked(bool(initial_settings.get("progress_visual_accent_enabled", True)))
        visual_form.addRow(self.visual_accent_checkbox)

        self.audio_visualizer_checkbox = QCheckBox("音频可视化")
        self.audio_visualizer_checkbox.setChecked(bool(initial_settings.get("audio_visualizer_enabled", True)))
        visual_form.addRow(self.audio_visualizer_checkbox)

        lyrics_dir_row = QHBoxLayout()
        self.lyrics_output_dir_input = QLineEdit()
        self.lyrics_output_dir_input.setPlaceholderText("留空则保存到歌曲同级 lyrics 目录")
        self.lyrics_output_dir_input.setText(str(initial_settings.get("lyrics_output_dir", "") or ""))
        self.lyrics_output_dir_browse_btn = QPushButton("浏览")
        self.lyrics_output_dir_clear_btn = QPushButton("默认")
        self.lyrics_output_dir_browse_btn.clicked.connect(self._choose_lyrics_output_dir)
        self.lyrics_output_dir_clear_btn.clicked.connect(lambda: self.lyrics_output_dir_input.setText(""))
        lyrics_dir_row.addWidget(self.lyrics_output_dir_input, 1)
        lyrics_dir_row.addWidget(self.lyrics_output_dir_browse_btn)
        lyrics_dir_row.addWidget(self.lyrics_output_dir_clear_btn)
        visual_form.addRow("歌词保存目录", lyrics_dir_row)
        content_layout.addWidget(visual_group)
        content_layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._apply_theme_styles(initial_settings)
        self._apply_titlebar_theme(initial_settings)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_titlebar_theme({"ui_theme": getattr(self, "_ui_theme", "light")})

    def values(self):
        return {
            "tray_enabled": self.tray_enabled_checkbox.isChecked(),
            "close_to_tray_enabled": self.close_to_tray_checkbox.isChecked(),
            "keyboard_volume_step": int(self.keyboard_volume_step_spin.value()),
            "keyboard_seek_step_seconds": int(self.keyboard_seek_step_spin.value()),
            "audio_output_strategy": str(self.audio_output_strategy_combo.currentData()),
            "high_quality_output": self.high_quality_output_checkbox.isChecked(),
            "volume_uniformity_level": str(self.volume_uniformity_level_combo.currentData()),
            "progress_visual_pulse_enabled": self.visual_pulse_checkbox.isChecked(),
            "progress_visual_wave_enabled": self.visual_wave_checkbox.isChecked(),
            "progress_visual_accent_enabled": self.visual_accent_checkbox.isChecked(),
            "audio_visualizer_enabled": self.audio_visualizer_checkbox.isChecked(),
            "ui_font_weight": str(self.ui_font_weight_combo.currentData()),
            "ui_theme": str(self.ui_theme_combo.currentData()),
            "lyrics_font_size": int(self.lyrics_font_size_spin.value()),
            "lyrics_output_dir": self.lyrics_output_dir_input.text().strip(),
        }

    def _choose_lyrics_output_dir(self):
        start_dir = self.lyrics_output_dir_input.text().strip()
        directory = QFileDialog.getExistingDirectory(self, "选择歌词保存目录", start_dir)
        if directory:
            self.lyrics_output_dir_input.setText(directory)

    def _apply_theme_styles(self, initial_settings):
        theme = str(initial_settings.get("ui_theme", "light") or "light").strip().lower()
        self._ui_theme = theme if theme in ("light", "dark") else "light"
        if theme != "dark":
            return

        self.scroll_area.setStyleSheet("QScrollArea#settingsScrollArea { background: #11151d; border: none; }")
        self.scroll_area.viewport().setStyleSheet("QWidget#settingsScrollViewport { background: #11151d; }")
        content = self.scroll_area.widget()
        if content is not None:
            content.setStyleSheet("QWidget#settingsScrollContent { background: #11151d; color: #ffffff; }")

        self.setStyleSheet(
            "\n".join(
                [
                    "QDialog#settingsDialog { background: #11151d; color: #ffffff; border: 1px solid #2d3a4f; }",
                    "QWidget { background: #11151d; color: #ffffff; }",
                    "QScrollArea#settingsScrollArea { border: none; background: #11151d; }",
                    "QWidget#settingsScrollViewport { background: #11151d; }",
                    "QScrollArea > QWidget > QWidget { background: #11151d; color: #ffffff; }",
                    "QWidget#settingsScrollContent { background: #11151d; color: #ffffff; }",
                    "QGroupBox { background: #161b25; color: #ffffff; border: 1px solid #4a4a4a; border-radius: 8px; margin-top: 12px; padding-top: 8px; }",
                    "QGroupBox::title { color: #ffffff; subcontrol-origin: margin; left: 10px; padding: 0 4px; }",
                    "QLabel { color: #ffffff; }",
                    "QCheckBox { color: #ffffff; }",
                    "QLineEdit, QComboBox, QSpinBox { background: #20293a; color: #ffffff; border: 1px solid #2d3a4f; border-radius: 7px; padding: 4px 8px; }",
                    "QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #2f7bff; }",
                    "QComboBox QAbstractItemView { background: #161b25; color: #ffffff; selection-background-color: #2057c9; selection-color: #ffffff; }",
                    "QPushButton { background: #232b39; color: #ffffff; border: 1px solid #3e4a60; border-radius: 6px; padding: 4px 10px; }",
                    "QPushButton:hover { background: #2a3445; }",
                    "QDialogButtonBox { background: #11151d; }",
                    "QDialogButtonBox QPushButton { min-width: 72px; }",
                ]
            )
        )

    def _apply_titlebar_theme(self, initial_settings):
        theme = str(initial_settings.get("ui_theme", "light") or "light").strip().lower()
        set_immersive_dark_title_bar(self, theme == "dark")



