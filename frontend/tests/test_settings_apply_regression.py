import importlib
import os
import sys

from PyQt5.QtWidgets import QApplication

settings_mixin_module = importlib.import_module("apps.desktop.windows.modules.settings_mixin")
SettingsMixin = settings_mixin_module.SettingsMixin


app = QApplication.instance() or QApplication(sys.argv)


class _DummyAudioPlayer:
    def __init__(self):
        self.high_quality_mode = None
        self.strategy_calls = []
        self.uniformity_calls = []

    def set_high_quality_output_mode(self, enabled):
        self.high_quality_mode = bool(enabled)

    def set_output_device_strategy(self, strategy, fixed_signature=None):
        self.strategy_calls.append((strategy, fixed_signature))
        self.fixed_output_device_signature = fixed_signature

    def set_loudness_normalization_level(self, level):
        self.uniformity_calls.append(level)


class _DummyLyricsService:
    def __init__(self):
        self.output_dir = None

    def set_lyrics_output_dir(self, path):
        self.output_dir = path


class _DummySettingsTarget(SettingsMixin):
    def __init__(self):
        self.tray_enabled = True
        self.close_to_tray_enabled = False
        self.close_behavior_configured = False
        self.high_quality_output_enabled = False
        self.keyboard_volume_step = 5
        self.keyboard_seek_step_seconds = 5
        self.audio_output_strategy = "follow_system"
        self.volume_uniformity_level = "medium"
        self.progress_visual_pulse_enabled = True
        self.progress_visual_wave_enabled = True
        self.progress_visual_accent_enabled = True
        self.ui_font_weight = "regular"
        self.lyrics_font_size = 18
        self.lyrics_output_dir = ""
        self.audio_player = _DummyAudioPlayer()
        self.lyrics_service = _DummyLyricsService()
        self.saved = False
        self.status_messages = []
        self.font_weight_applied = None

    def schedule_save_app_settings(self):
        self.saved = True

    def show_status_hint(self, message, timeout_ms=0):
        self.status_messages.append((message, timeout_ms))

    def apply_ui_font(self, font_weight, reapply_theme=False):
        self.font_weight_applied = (str(font_weight), bool(reapply_theme))

    def apply_ui_theme(self, theme_name):
        self.theme_applied = str(theme_name)


def test_apply_settings_syncs_custom_lyrics_dir_to_service_and_persists():
    target = _DummySettingsTarget()

    target.apply_settings(
        {
            "lyrics_output_dir": "D:/Lyrics/Custom",
            "tray_enabled": True,
            "close_to_tray_enabled": False,
        },
        persist=True,
    )

    expected = os.path.normcase(os.path.abspath("D:/Lyrics/Custom"))
    assert os.path.normcase(target.lyrics_output_dir) == expected
    assert os.path.normcase(target.lyrics_service.output_dir) == expected
    assert target.saved is True


def test_apply_settings_rejects_invalid_lyrics_dir_and_falls_back(monkeypatch):
    target = _DummySettingsTarget()

    def _broken_makedirs(*_args, **_kwargs):
        raise OSError("nope")

    monkeypatch.setattr(settings_mixin_module.os, "makedirs", _broken_makedirs)

    target.apply_settings({"lyrics_output_dir": "D:/Lyrics/Invalid"}, persist=False)

    assert target.lyrics_output_dir == ""
    assert target.lyrics_service.output_dir == ""
    assert target.status_messages


def test_apply_settings_updates_ui_font_weight():
    target = _DummySettingsTarget()
    target.apply_settings({"ui_font_weight": "light"}, persist=False)

    assert target.ui_font_weight == "light"
    assert target.font_weight_applied == ("light", False)


def test_apply_settings_updates_lyrics_font_size():
    target = _DummySettingsTarget()
    target.apply_settings({"lyrics_font_size": 24}, persist=False)

    assert target.lyrics_font_size == 24


