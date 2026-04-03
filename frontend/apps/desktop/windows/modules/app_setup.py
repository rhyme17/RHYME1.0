import os
import sys

try:
    from frontend.core.library import MusicLibrary
    from frontend.core.lyrics_service import LyricsService
    from frontend.core.player import AudioPlayer
    from frontend.core.playlist import PlaylistManager
except ModuleNotFoundError:
    from core.library import MusicLibrary
    from core.lyrics_service import LyricsService
    from core.player import AudioPlayer
    from core.playlist import PlaylistManager


def build_core_components(
    player,
    entry_config,
):
    player.music_library = MusicLibrary()
    player.audio_player = AudioPlayer()
    player.playlist_manager = PlaylistManager()
    player.high_quality_output_enabled = bool(getattr(entry_config, "audio_exclusive_mode", False))
    player.audio_player.set_high_quality_output_mode(player.high_quality_output_enabled)
    player.lyrics_service = LyricsService(
        cache_dir=os.path.join(entry_config.windows_app_dir, ".lyrics_cache"),
        asr_model_size=entry_config.asr_model_size,
        asr_device=entry_config.asr_device,
        asr_compute_type=entry_config.asr_compute_type,
        asr_beam_size=entry_config.asr_beam_size,
        asr_vad_filter=entry_config.asr_vad_filter,
    )
    player.playlists_file_path = entry_config.playlists_file
    player.settings_file_path = entry_config.settings_file
    player.load_playlists()


def init_runtime_state(player):
    player.current_track_index = 0
    player.playback_mode = "顺序播放"
    player.is_muted = False
    player.last_volume = 80
    player.saved_volume = 80
    player.current_song = None
    player.progress_timer = None
    player.current_duration = 0
    player.scan_worker = None
    player.scan_dialog = None
    player.scan_results_cache = []
    player.last_scanned_directory = ""
    player.is_rendering_playlist = False
    player.last_reorder_snapshot = None
    player.keyboard_volume_step = 5
    player.keyboard_seek_step_seconds = 5
    player.file_size_warning_mb = AudioPlayer.DEFAULT_FILE_SIZE_WARNING_MB
    player.decode_memory_warning_mb = AudioPlayer.DEFAULT_PCM_MEMORY_WARNING_MB
    player._restored_last_playlist_name = ""
    player._restored_last_song_id = ""
    player._restored_last_position_seconds = 0.0
    player._pending_resume_song_id = ""
    player._pending_resume_position_seconds = 0.0
    player._progress_persist_interval_seconds = 5
    player._last_progress_save_bucket = -1
    player._ui_tick = 0
    player._ui_timer_started = False
    player._shortcuts_initialized = False
    player._settings_save_timer = None
    player._is_closing = False
    player._progress_anim = None
    player.progress_visual_pulse_enabled = True
    player.progress_visual_wave_enabled = True
    player.progress_visual_accent_enabled = True
    player.async_decode_on_play = bool(getattr(sys, "frozen", False))
    player._decode_request_id = 0
    player.decode_worker = None
    player._is_track_switching = False
    player.tray_enabled = True
    player.close_to_tray_enabled = False
    player.close_behavior_configured = False
    player.fixed_output_device_signature = None
    player._tray_icon = None
    player._tray_menu = None
    player._tray_hint_shown = False
    player._quit_requested = False

