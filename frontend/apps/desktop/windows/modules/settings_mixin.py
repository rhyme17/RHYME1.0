import os

from PyQt5.QtWidgets import QDialog

try:
    from frontend.apps.desktop.windows.modules.settings_dialog import SettingsDialog
    from frontend.apps.desktop.windows.modules.settings_contract import (
        clamp_int,
        normalize_audio_output_strategy,
        normalize_volume_uniformity_level,
    )
except ModuleNotFoundError:
    from apps.desktop.windows.modules.settings_dialog import SettingsDialog
    from apps.desktop.windows.modules.settings_contract import (
        clamp_int,
        normalize_audio_output_strategy,
        normalize_volume_uniformity_level,
    )


class SettingsMixin:
    def get_settings_snapshot(self):
        return {
            "tray_enabled": bool(getattr(self, "tray_enabled", True)),
            "close_to_tray_enabled": bool(getattr(self, "close_to_tray_enabled", False)),
            "close_behavior_configured": bool(getattr(self, "close_behavior_configured", False)),
            "high_quality_output": bool(getattr(self, "high_quality_output_enabled", False)),
            "keyboard_volume_step": int(getattr(self, "keyboard_volume_step", 5)),
            "keyboard_seek_step_seconds": int(getattr(self, "keyboard_seek_step_seconds", 5)),
            "audio_output_strategy": str(getattr(self, "audio_output_strategy", "follow_system")),
            "volume_uniformity_level": str(getattr(self, "volume_uniformity_level", "medium")),
            "progress_visual_pulse_enabled": bool(getattr(self, "progress_visual_pulse_enabled", True)),
            "progress_visual_wave_enabled": bool(getattr(self, "progress_visual_wave_enabled", True)),
            "progress_visual_accent_enabled": bool(getattr(self, "progress_visual_accent_enabled", True)),
            "lyrics_output_dir": str(getattr(self, "lyrics_output_dir", "") or ""),
        }

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.get_settings_snapshot(), self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self.apply_settings(dialog.values(), persist=True)

    def apply_settings(self, values, persist=True):
        self.tray_enabled = bool(values.get("tray_enabled", self.tray_enabled))
        self.close_to_tray_enabled = bool(values.get("close_to_tray_enabled", self.close_to_tray_enabled))
        if "close_to_tray_enabled" in values:
            self.close_behavior_configured = True
        self.high_quality_output_enabled = bool(
            values.get("high_quality_output", getattr(self, "high_quality_output_enabled", False))
        )

        self.keyboard_volume_step = clamp_int(
            values.get("keyboard_volume_step", self.keyboard_volume_step),
            default=self.keyboard_volume_step,
            minimum=1,
            maximum=20,
        )
        self.keyboard_seek_step_seconds = clamp_int(
            values.get("keyboard_seek_step_seconds", self.keyboard_seek_step_seconds),
            default=self.keyboard_seek_step_seconds,
            minimum=1,
            maximum=30,
        )

        strategy = normalize_audio_output_strategy(
            values.get("audio_output_strategy", self.audio_output_strategy),
            default="follow_system",
        )
        self.audio_output_strategy = strategy

        uniformity = normalize_volume_uniformity_level(
            values.get("volume_uniformity_level", self.volume_uniformity_level),
            default="medium",
        )
        self.volume_uniformity_level = uniformity

        if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_high_quality_output_mode"):
            self.audio_player.set_high_quality_output_mode(self.high_quality_output_enabled)
        if hasattr(self, "refresh_high_quality_output_button"):
            self.refresh_high_quality_output_button()

        if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_output_device_strategy"):
            fixed_signature = getattr(self, "fixed_output_device_signature", None)
            self.audio_player.set_output_device_strategy(strategy, fixed_signature=fixed_signature)
            self.fixed_output_device_signature = getattr(self.audio_player, "fixed_output_device_signature", fixed_signature)
        if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_loudness_normalization_level"):
            self.audio_player.set_loudness_normalization_level(uniformity)

        self.progress_visual_pulse_enabled = bool(
            values.get("progress_visual_pulse_enabled", self.progress_visual_pulse_enabled)
        )
        self.progress_visual_wave_enabled = bool(
            values.get("progress_visual_wave_enabled", self.progress_visual_wave_enabled)
        )
        self.progress_visual_accent_enabled = bool(
            values.get("progress_visual_accent_enabled", self.progress_visual_accent_enabled)
        )
        lyrics_output_dir = str(values.get("lyrics_output_dir", getattr(self, "lyrics_output_dir", "")) or "").strip()
        if lyrics_output_dir:
            try:
                lyrics_output_dir = os.path.abspath(lyrics_output_dir)
                os.makedirs(lyrics_output_dir, exist_ok=True)
            except Exception:
                if hasattr(self, "show_status_hint"):
                    self.show_status_hint("歌词目录不可用，已回退默认路径", timeout_ms=2200)
                lyrics_output_dir = ""
        self.lyrics_output_dir = lyrics_output_dir

        if hasattr(self, "set_progress_visual_pulse_enabled"):
            self.set_progress_visual_pulse_enabled(self.progress_visual_pulse_enabled)
        if hasattr(self, "set_progress_visual_wave_enabled"):
            self.set_progress_visual_wave_enabled(self.progress_visual_wave_enabled)
        if hasattr(self, "set_progress_visual_accent_enabled"):
            self.set_progress_visual_accent_enabled(self.progress_visual_accent_enabled)

        if hasattr(self, "lyrics_service") and hasattr(self.lyrics_service, "set_lyrics_output_dir"):
            self.lyrics_service.set_lyrics_output_dir(self.lyrics_output_dir)

        if self.tray_enabled:
            if hasattr(self, "init_system_tray"):
                self.init_system_tray()
        else:
            if hasattr(self, "teardown_system_tray"):
                self.teardown_system_tray()

        if hasattr(self, "show_status_hint"):
            self.show_status_hint("设置已应用", timeout_ms=1800)
        if persist and hasattr(self, "schedule_save_app_settings"):
            self.schedule_save_app_settings()




