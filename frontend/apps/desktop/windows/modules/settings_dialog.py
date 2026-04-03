from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, initial_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(420, 320)

        root = QVBoxLayout(self)

        tray_group = QGroupBox("托盘与窗口")
        tray_form = QFormLayout(tray_group)
        self.tray_enabled_checkbox = QCheckBox("启用系统托盘")
        self.tray_enabled_checkbox.setChecked(bool(initial_settings.get("tray_enabled", True)))
        tray_form.addRow(self.tray_enabled_checkbox)

        self.close_to_tray_checkbox = QCheckBox("点击关闭时隐藏到托盘")
        self.close_to_tray_checkbox.setChecked(bool(initial_settings.get("close_to_tray_enabled", False)))
        tray_form.addRow(self.close_to_tray_checkbox)
        root.addWidget(tray_group)

        keyboard_group = QGroupBox("键盘控制")
        keyboard_form = QFormLayout(keyboard_group)
        self.keyboard_volume_step_spin = QSpinBox()
        self.keyboard_volume_step_spin.setRange(1, 20)
        self.keyboard_volume_step_spin.setValue(int(initial_settings.get("keyboard_volume_step", 5)))
        keyboard_form.addRow("音量步长", self.keyboard_volume_step_spin)

        self.keyboard_seek_step_spin = QSpinBox()
        self.keyboard_seek_step_spin.setRange(1, 30)
        self.keyboard_seek_step_spin.setValue(int(initial_settings.get("keyboard_seek_step_seconds", 5)))
        keyboard_form.addRow("快进/快退步长(秒)", self.keyboard_seek_step_spin)
        root.addWidget(keyboard_group)

        audio_group = QGroupBox("音频")
        audio_form = QFormLayout(audio_group)
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
        root.addWidget(audio_group)

        visual_group = QGroupBox("进度条动效")
        visual_form = QFormLayout(visual_group)
        self.visual_pulse_checkbox = QCheckBox("脉冲动效")
        self.visual_pulse_checkbox.setChecked(bool(initial_settings.get("progress_visual_pulse_enabled", True)))
        visual_form.addRow(self.visual_pulse_checkbox)

        self.visual_wave_checkbox = QCheckBox("波浪动效")
        self.visual_wave_checkbox.setChecked(bool(initial_settings.get("progress_visual_wave_enabled", True)))
        visual_form.addRow(self.visual_wave_checkbox)

        self.visual_accent_checkbox = QCheckBox("重音抖动")
        self.visual_accent_checkbox.setChecked(bool(initial_settings.get("progress_visual_accent_enabled", True)))
        visual_form.addRow(self.visual_accent_checkbox)
        root.addWidget(visual_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

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
        }



