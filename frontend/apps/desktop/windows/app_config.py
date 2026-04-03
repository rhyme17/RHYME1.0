import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class WindowsEntryConfig:
    windows_app_dir: str
    playlists_file: str
    settings_file: str
    asr_model_size: str
    asr_device: str
    asr_compute_type: str
    asr_beam_size: int
    asr_vad_filter: bool
    audio_exclusive_mode: bool


def _parse_int_env(name, default):
    try:
        return int((os.getenv(name, str(default)) or str(default)).strip())
    except Exception:
        return int(default)


def _parse_bool_env(name, default):
    raw = os.getenv(name, default)
    return (raw or default).strip().lower() in ("1", "true", "yes", "on")


def _resolve_windows_runtime_data_dir(entry_dir):
    override_dir = (os.getenv("RHYME_USER_DATA_DIR", "") or "").strip()
    if override_dir:
        return os.path.abspath(override_dir)

    if getattr(sys, "frozen", False):
        local_app_data = (os.getenv("LOCALAPPDATA", "") or "").strip()
        if local_app_data:
            return os.path.join(local_app_data, "RHYME")

    return entry_dir


def build_default_namespace(entry_file):
    """Build default module globals for windows entry with env overrides."""
    entry_dir = os.path.dirname(os.path.abspath(entry_file))
    frontend_dir = os.path.abspath(os.path.join(entry_dir, "..", "..", ".."))
    project_root = os.path.abspath(os.path.join(frontend_dir, ".."))
    windows_app_dir = _resolve_windows_runtime_data_dir(entry_dir)
    os.makedirs(windows_app_dir, exist_ok=True)
    return {
        "WINDOWS_APP_DIR": windows_app_dir,
        "FRONTEND_DIR": frontend_dir,
        "PROJECT_ROOT": project_root,
        "PLAYLISTS_FILE": os.path.join(windows_app_dir, "playlists.json"),
        "SETTINGS_FILE": os.path.join(windows_app_dir, "settings.json"),
        "ASR_DEVICE": (os.getenv("RHYME_ASR_DEVICE", "cpu") or "cpu").strip(),
        "ASR_COMPUTE_TYPE": (os.getenv("RHYME_ASR_COMPUTE_TYPE", "float32") or "float32").strip(),
        "ASR_MODEL_SIZE": (os.getenv("RHYME_ASR_MODEL_SIZE", "small") or "small").strip(),
        "ASR_BEAM_SIZE": _parse_int_env("RHYME_ASR_BEAM_SIZE", 5),
        "ASR_VAD_FILTER": _parse_bool_env("RHYME_ASR_VAD_FILTER", "false"),
        "AUDIO_EXCLUSIVE_MODE": _parse_bool_env("RHYME_AUDIO_EXCLUSIVE_MODE", "false"),
    }


def build_entry_config_from_namespace(namespace):
    """从给定命名空间动态读取配置，便于测试 monkeypatch 后即时生效。"""
    return WindowsEntryConfig(
        windows_app_dir=namespace["WINDOWS_APP_DIR"],
        playlists_file=namespace["PLAYLISTS_FILE"],
        settings_file=namespace["SETTINGS_FILE"],
        asr_model_size=namespace["ASR_MODEL_SIZE"],
        asr_device=namespace["ASR_DEVICE"],
        asr_compute_type=namespace["ASR_COMPUTE_TYPE"],
        asr_beam_size=int(namespace["ASR_BEAM_SIZE"]),
        asr_vad_filter=bool(namespace["ASR_VAD_FILTER"]),
        audio_exclusive_mode=bool(namespace["AUDIO_EXCLUSIVE_MODE"]),
    )


