import json
import os

from PyQt5.QtCore import QTimer

from frontend.utils.helpers import format_time
from frontend.utils.import_compat import load_attr
from frontend.utils.logging_utils import get_logger
from frontend.apps.desktop.windows.modules.settings_contract import (
    clamp_int,
    normalize_audio_output_strategy,
    normalize_volume_uniformity_level,
)


backup_corrupted_file = load_attr(
    ["frontend.utils.json_recovery", "utils.json_recovery"],
    "backup_corrupted_file",
)
atomic_write_json = load_attr(
    ["frontend.utils.json_io", "utils.json_io"],
    "atomic_write_json",
)


MAX_CORRUPT_SETTINGS_BACKUPS = 10
logger = get_logger(__name__)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _atomic_write_json(file_path, data):
    return atomic_write_json(file_path, data)


def _json_safe_signature(signature):
    if isinstance(signature, tuple):
        return list(signature)
    return signature


class PersistenceMixin:
    def _ui_position_seconds(self):
        if not hasattr(self, "progress_slider"):
            return 0.0
        duration = max(0.0, float(getattr(self, "current_duration", 0.0) or 0.0))
        if duration <= 0.0:
            return 0.0
        progress = int(self.progress_slider.value())
        progress = max(0, min(100, progress))
        return (progress / 100.0) * duration

    def load_playlists(self):
        if os.path.exists(self.playlists_file_path):
            self.playlist_manager.load(self.playlists_file_path)

    def save_playlists(self):
        self.playlist_manager.save(self.playlists_file_path)

    def load_app_settings(self):
        if not os.path.exists(self.settings_file_path):
            return
        try:
            with open(self.settings_file_path, "r", encoding="utf-8") as handler:
                data = json.load(handler)
            if not isinstance(data, dict):
                raise ValueError("设置文件结构无效")
        except Exception:
            backup_corrupted_file(self.settings_file_path, keep_latest=MAX_CORRUPT_SETTINGS_BACKUPS)
            return

        volume = data.get("volume")
        if isinstance(volume, int) and 0 <= volume <= 100:
            self.saved_volume = volume
            self.last_volume = volume

        self._restored_last_playlist_name = (data.get("last_playlist_name") or "").strip()
        self._restored_last_song_id = (data.get("last_song_id") or "").strip()
        self._restored_last_position_seconds = max(0.0, _safe_float(data.get("last_position_seconds"), 0.0))

        high_quality_output = data.get("high_quality_output")
        if isinstance(high_quality_output, bool):
            self.high_quality_output_enabled = high_quality_output
            if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_high_quality_output_mode"):
                self.audio_player.set_high_quality_output_mode(high_quality_output)

        tray_enabled = data.get("tray_enabled")
        if isinstance(tray_enabled, bool):
            self.tray_enabled = tray_enabled

        close_to_tray_enabled = data.get("close_to_tray_enabled")
        if isinstance(close_to_tray_enabled, bool):
            self.close_to_tray_enabled = close_to_tray_enabled

        close_behavior_configured = data.get("close_behavior_configured")
        if isinstance(close_behavior_configured, bool):
            self.close_behavior_configured = close_behavior_configured

        self.keyboard_volume_step = clamp_int(
            data.get("keyboard_volume_step", getattr(self, "keyboard_volume_step", 5)),
            default=getattr(self, "keyboard_volume_step", 5),
            minimum=1,
            maximum=20,
        )
        self.keyboard_seek_step_seconds = clamp_int(
            data.get("keyboard_seek_step_seconds", getattr(self, "keyboard_seek_step_seconds", 5)),
            default=getattr(self, "keyboard_seek_step_seconds", 5),
            minimum=1,
            maximum=30,
        )

        self.audio_output_strategy = normalize_audio_output_strategy(
            data.get("audio_output_strategy", getattr(self, "audio_output_strategy", "follow_system")),
            default="follow_system",
        )
        if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_output_device_strategy"):
            fixed_signature = data.get("fixed_output_device_signature", getattr(self, "fixed_output_device_signature", None))
            self.audio_player.set_output_device_strategy(self.audio_output_strategy, fixed_signature=fixed_signature)
            self.fixed_output_device_signature = getattr(self.audio_player, "fixed_output_device_signature", fixed_signature)

        self.volume_uniformity_level = normalize_volume_uniformity_level(
            data.get("volume_uniformity_level", getattr(self, "volume_uniformity_level", "medium")),
            default="medium",
        )
        if hasattr(self, "audio_player") and hasattr(self.audio_player, "set_loudness_normalization_level"):
            self.audio_player.set_loudness_normalization_level(self.volume_uniformity_level)

        pulse_enabled = data.get("progress_visual_pulse_enabled")
        if isinstance(pulse_enabled, bool):
            self.progress_visual_pulse_enabled = pulse_enabled

        wave_enabled = data.get("progress_visual_wave_enabled")
        if isinstance(wave_enabled, bool):
            self.progress_visual_wave_enabled = wave_enabled

        accent_enabled = data.get("progress_visual_accent_enabled")
        if isinstance(accent_enabled, bool):
            self.progress_visual_accent_enabled = accent_enabled

    def save_app_settings(self):
        current_song_id = ""
        if getattr(self, "current_song", None):
            current_song_id = str(self.current_song.get("id", "") or "")

        current_playlist_name = ""
        if hasattr(self, "playlist_manager"):
            current_playlist_name = str(self.playlist_manager.get_playlist_name() or "")

        current_position_seconds = 0.0
        if current_song_id:
            if getattr(self.audio_player, "is_playing", False):
                current_position_seconds = max(0.0, float(self.audio_player.get_position()))
            elif getattr(self, "_pending_resume_song_id", "") == current_song_id:
                current_position_seconds = max(0.0, float(getattr(self, "_pending_resume_position_seconds", 0.0)))
            else:
                current_position_seconds = max(0.0, float(self._ui_position_seconds()))

        data = {
            "volume": int(self.volume_slider.value()) if hasattr(self, "volume_slider") else int(self.saved_volume),
            "last_playlist_name": current_playlist_name,
            "last_song_id": current_song_id,
            "last_position_seconds": round(current_position_seconds, 3),
            "high_quality_output": bool(getattr(self, "high_quality_output_enabled", False)),
            "tray_enabled": bool(getattr(self, "tray_enabled", True)),
            "close_to_tray_enabled": bool(getattr(self, "close_to_tray_enabled", False)),
            "close_behavior_configured": bool(getattr(self, "close_behavior_configured", False)),
            "keyboard_volume_step": int(getattr(self, "keyboard_volume_step", 5)),
            "keyboard_seek_step_seconds": int(getattr(self, "keyboard_seek_step_seconds", 5)),
            "audio_output_strategy": str(getattr(self, "audio_output_strategy", "follow_system")),
            "fixed_output_device_signature": _json_safe_signature(
                getattr(self, "fixed_output_device_signature", None)
            ),
            "volume_uniformity_level": str(getattr(self, "volume_uniformity_level", "medium")),
            "progress_visual_pulse_enabled": bool(getattr(self, "progress_visual_pulse_enabled", True)),
            "progress_visual_wave_enabled": bool(getattr(self, "progress_visual_wave_enabled", True)),
            "progress_visual_accent_enabled": bool(getattr(self, "progress_visual_accent_enabled", True)),
        }
        try:
            _atomic_write_json(self.settings_file_path, data)
        except Exception:
            logger.exception("保存应用设置失败")

    def restore_last_played_song(self):
        last_song_id = str(getattr(self, "_restored_last_song_id", "") or "")
        last_playlist_name = str(getattr(self, "_restored_last_playlist_name", "") or "")
        last_position_seconds = max(0.0, float(getattr(self, "_restored_last_position_seconds", 0.0) or 0.0))
        if not last_song_id:
            return

        if last_playlist_name and self.playlist_manager.has_playlist(last_playlist_name):
            self.playlist_manager.select_playlist(last_playlist_name)

        playlist_name = self.playlist_manager.get_playlist_name()
        playlist = self.playlist_manager.get_playlist()
        for index, song in enumerate(playlist):
            if str(song.get("id", "")) != last_song_id:
                continue

            self.current_track_index = index
            self.current_song = song
            self._pending_resume_song_id = last_song_id
            self._pending_resume_position_seconds = last_position_seconds
            self.song_title_label.setText(song.get("title", "未播放"))
            self.song_artist_label.setText(song.get("artist", "-"))

            duration = max(0.0, float(song.get("duration", 0.0) or 0.0))
            restore_pos = min(last_position_seconds, duration) if duration > 0 else last_position_seconds
            self.current_time_label.setText(format_time(restore_pos))
            if duration > 0:
                progress = int((restore_pos / duration) * 100)
                self.progress_slider.setValue(max(0, min(100, progress)))

            self.render_playlist_names(select_name=playlist_name)
            self.render_playlist()
            self.playlist_list.setCurrentRow(index)
            return

    def schedule_save_app_settings(self, delay_ms=300):
        if not hasattr(self, "_settings_save_timer") or self._settings_save_timer is None:
            self._settings_save_timer = QTimer(self)
            self._settings_save_timer.setSingleShot(True)
            self._settings_save_timer.timeout.connect(self.save_app_settings)
        self._settings_save_timer.start(max(50, int(delay_ms)))

