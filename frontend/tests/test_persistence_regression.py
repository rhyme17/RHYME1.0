import json
import importlib
import sys
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = TESTS_DIR.parent
PROJECT_ROOT = FRONTEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pm = importlib.import_module("apps.desktop.windows.modules.persistence_mixin")
PersistenceMixin = pm.PersistenceMixin


class _DummySlider:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _DummyPlaylistManager:
    def __init__(self, name):
        self._name = name

    def get_playlist_name(self):
        return self._name


class _DummyAudioPlayer:
    def __init__(self, is_playing=False, position=0.0):
        self.is_playing = is_playing
        self._position = position
        self.high_quality_mode = None
        self.output_strategy_calls = []
        self.uniformity_level = None

    def get_position(self):
        return self._position

    def set_high_quality_output_mode(self, enabled):
        self.high_quality_mode = bool(enabled)

    def set_output_device_strategy(self, strategy, fixed_signature=None):
        self.output_strategy_calls.append((strategy, fixed_signature))
        self.fixed_output_device_signature = fixed_signature

    def set_loudness_normalization_level(self, level):
        self.uniformity_level = str(level)


class _DummyPersistence(PersistenceMixin):
    def __init__(self, settings_file_path: Path):
        self.settings_file_path = str(settings_file_path)
        self.volume_slider = _DummySlider(55)
        self.saved_volume = 55
        self.last_volume = 55
        self.playlist_manager = _DummyPlaylistManager("RoadTrip")
        self.current_song = {"id": "song-1"}
        self.audio_player = _DummyAudioPlayer(is_playing=True, position=12.345)
        self.high_quality_output_enabled = False
        self.tray_enabled = True
        self.close_to_tray_enabled = True
        self.minimize_to_tray_enabled = False
        self.keyboard_volume_step = 5
        self.keyboard_seek_step_seconds = 5
        self.audio_output_strategy = "follow_system"
        self.fixed_output_device_signature = None
        self.volume_uniformity_level = "medium"
        self.progress_visual_pulse_enabled = True
        self.progress_visual_wave_enabled = True
        self.progress_visual_accent_enabled = True
        self.ui_font_weight = "regular"
        self.lyrics_font_size = 18
        self.lyrics_output_dir = ""
        self.last_scanned_directory = ""
        self._pending_resume_song_id = ""
        self._pending_resume_position_seconds = 0.0
        self.lyrics_service = None


class _DummyLyricsService:
    def __init__(self):
        self.output_dir = None

    def set_lyrics_output_dir(self, path):
        self.output_dir = path


def test_save_app_settings_falls_back_to_ui_progress_when_not_playing(tmp_path: Path):
    settings_file = tmp_path / "settings-ui.json"
    instance = _DummyPersistence(settings_file)
    instance.audio_player = _DummyAudioPlayer(is_playing=False, position=0.0)
    instance.current_duration = 100.0
    instance.progress_slider = _DummySlider(30)

    instance.save_app_settings()

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert abs(data["last_position_seconds"] - 30.0) < 0.001


def test_save_app_settings_uses_atomic_write(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    instance = _DummyPersistence(settings_file)

    instance.save_app_settings()

    assert settings_file.exists()
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["volume"] == 55
    assert data["last_playlist_name"] == "RoadTrip"
    assert data["last_song_id"] == "song-1"
    assert abs(data["last_position_seconds"] - 12.345) < 0.001


def test_save_app_settings_keeps_previous_file_when_replace_fails(monkeypatch, tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps({"volume": 11, "last_playlist_name": "Old", "last_song_id": "old"}, ensure_ascii=False),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)

    def _broken_replace(_src, _dst):
        raise OSError("replace failed")

    monkeypatch.setattr(pm.os, "replace", _broken_replace)

    instance.save_app_settings()

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["volume"] == 11
    assert data["last_playlist_name"] == "Old"

    leftovers = list(tmp_path.glob("settings.json.*.tmp"))
    assert leftovers == []


def test_load_app_settings_backs_up_corrupted_json(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    broken_content = "{bad-json"
    settings_file.write_text(broken_content, encoding="utf-8")

    instance = _DummyPersistence(settings_file)
    instance.saved_volume = 80
    instance.last_volume = 80
    instance.load_app_settings()

    backups = list(tmp_path.glob("settings.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == broken_content
    assert instance.saved_volume == 80
    assert instance.last_volume == 80


def test_load_app_settings_corrupted_backup_keeps_recent_limit_of_ten(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    broken_content = "{bad-json"
    settings_file.write_text(broken_content, encoding="utf-8")

    old_backups = []
    for i in range(11):
        backup = tmp_path / f"settings.json.corrupt-20240101-0000{i:02d}-000.bak"
        backup.write_text(f"old-{i}", encoding="utf-8")
        mtime = 1000 + i
        pm.os.utime(str(backup), (mtime, mtime))
        old_backups.append(backup)

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    backups = sorted(tmp_path.glob("settings.json.corrupt-*.bak"))
    assert len(backups) == 10
    assert any(path.read_text(encoding="utf-8") == broken_content for path in backups)
    assert old_backups[0].exists() is False
    assert old_backups[1].exists() is False


def test_load_app_settings_normalizes_strategy_uniformity_and_step_values(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "volume": 66,
                "high_quality_output": True,
                "keyboard_volume_step": 999,
                "keyboard_seek_step_seconds": -1,
                "audio_output_strategy": "invalid",
                "fixed_output_device_signature": ["a", "b", "c", "d"],
                "volume_uniformity_level": "bad-level",
                "progress_visual_pulse_enabled": False,
                "progress_visual_wave_enabled": False,
                "progress_visual_accent_enabled": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    assert instance.saved_volume == 66
    assert instance.last_volume == 66
    assert instance.high_quality_output_enabled is True
    assert instance.audio_player.high_quality_mode is True
    assert instance.keyboard_volume_step == 20
    assert instance.keyboard_seek_step_seconds == 1
    assert instance.audio_output_strategy == "follow_system"
    assert instance.volume_uniformity_level == "medium"
    assert instance.audio_player.output_strategy_calls[-1][0] == "follow_system"
    assert instance.audio_player.uniformity_level == "medium"
    assert instance.progress_visual_pulse_enabled is False
    assert instance.progress_visual_wave_enabled is False
    assert instance.progress_visual_accent_enabled is False


def test_load_app_settings_accepts_legacy_strategy_and_uniformity_aliases(tmp_path: Path):
    settings_file = tmp_path / "settings-legacy.json"
    settings_file.write_text(
        json.dumps(
            {
                "audio_output_strategy": "fixed",
                "fixed_output_device_signature": [2, "Speaker", 1, 2],
                "volume_uniformity_level": "low",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    assert instance.audio_output_strategy == "fixed_current"
    assert instance.audio_player.output_strategy_calls[-1][0] == "fixed_current"
    assert instance.volume_uniformity_level == "light"
    assert instance.audio_player.uniformity_level == "light"


def test_save_app_settings_persists_extended_settings_fields(tmp_path: Path):
    settings_file = tmp_path / "settings-save-full.json"
    instance = _DummyPersistence(settings_file)
    instance.keyboard_volume_step = 7
    instance.keyboard_seek_step_seconds = 9
    instance.audio_output_strategy = "fixed_current"
    instance.fixed_output_device_signature = (1, "Device", 0, 2)
    instance.volume_uniformity_level = "strong"
    instance.progress_visual_pulse_enabled = False
    instance.progress_visual_wave_enabled = True
    instance.progress_visual_accent_enabled = False
    instance.ui_font_weight = "medium"
    instance.lyrics_font_size = 21
    instance.lyrics_output_dir = "D:/lyrics-custom"
    instance.last_scanned_directory = "D:/music-last"

    instance.save_app_settings()

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["keyboard_volume_step"] == 7
    assert data["keyboard_seek_step_seconds"] == 9
    assert data["audio_output_strategy"] == "fixed_current"
    assert data["fixed_output_device_signature"] == [1, "Device", 0, 2]
    assert data["volume_uniformity_level"] == "strong"
    assert data["progress_visual_pulse_enabled"] is False
    assert data["progress_visual_wave_enabled"] is True
    assert data["progress_visual_accent_enabled"] is False
    assert data["ui_font_weight"] == "medium"
    assert data["lyrics_font_size"] == 21
    assert data["lyrics_output_dir"] == "D:/lyrics-custom"
    assert data["last_scanned_directory"] == "D:/music-last"


def test_load_app_settings_restores_lyrics_output_dir_and_last_scan_dir(tmp_path: Path):
    settings_file = tmp_path / "settings-custom-paths.json"
    settings_file.write_text(
        json.dumps(
            {
                "lyrics_output_dir": "D:/lyrics-save",
                "last_scanned_directory": "D:/music-folder",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    assert instance.lyrics_output_dir == "D:/lyrics-save"
    assert instance.last_scanned_directory == "D:/music-folder"


def test_load_app_settings_syncs_lyrics_output_dir_to_service(tmp_path: Path):
    settings_file = tmp_path / "settings-lyrics-service.json"
    settings_file.write_text(
        json.dumps(
            {
                "lyrics_output_dir": "D:/lyrics-save",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.lyrics_service = _DummyLyricsService()
    instance.load_app_settings()

    assert instance.lyrics_output_dir == "D:/lyrics-save"
    assert instance.lyrics_service.output_dir == "D:/lyrics-save"


def test_load_app_settings_restores_ui_font_weight(tmp_path: Path):
    settings_file = tmp_path / "settings-font-weight.json"
    settings_file.write_text(
        json.dumps(
            {
                "ui_font_weight": "light",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    assert instance.ui_font_weight == "light"


def test_load_app_settings_restores_lyrics_font_size(tmp_path: Path):
    settings_file = tmp_path / "settings-lyrics-font-size.json"
    settings_file.write_text(
        json.dumps(
            {
                "lyrics_font_size": 26,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    instance = _DummyPersistence(settings_file)
    instance.load_app_settings()

    assert instance.lyrics_font_size == 26



