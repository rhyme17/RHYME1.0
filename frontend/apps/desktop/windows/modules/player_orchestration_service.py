import math
import random


class PlayerOrchestrationService:
    @staticmethod
    def map_slider_volume_to_gain(slider_value, min_non_zero_gain=0.02, gamma=0.65):
        try:
            value = int(slider_value)
        except Exception:
            value = 0
        value = max(0, min(100, value))
        if value <= 0:
            return 0.0

        normalized = value / 100.0
        curved = normalized ** float(gamma)
        return max(float(min_non_zero_gain), min(1.0, curved))

    @staticmethod
    def resolve_song_index_by_id(playlist, song_id):
        target_id = str(song_id or "")
        if not target_id:
            return -1
        for index, song in enumerate(playlist or []):
            if str(song.get("id", "") or "") == target_id:
                return index
        return -1

    @staticmethod
    def normalize_resume_seconds(resume_seconds, duration_seconds):
        value = float(resume_seconds or 0.0)
        if not math.isfinite(value):
            value = 0.0
        value = max(0.0, value)

        duration = float(duration_seconds or 0.0)
        if duration <= 0.0:
            return value

        value = min(value, duration)
        # Resuming near the end is treated as completed playback.
        if value >= max(0.0, duration - 0.5):
            return 0.0
        return value

    @staticmethod
    def next_track_index(current_index, playlist_length, playback_mode):
        if playlist_length <= 0:
            return 0

        index = int(current_index or 0)
        mode = str(playback_mode or "顺序播放")

        if mode == "随机播放":
            return random.randint(0, playlist_length - 1)
        if mode == "单曲循环":
            return max(0, min(index, playlist_length - 1))
        return (index + 1) % playlist_length

    @staticmethod
    def resolve_same_song_action(force_restart, current_song_id, target_song_id, is_playing, is_paused):
        if force_restart:
            return "restart"
        if not current_song_id or current_song_id != target_song_id:
            return "restart"
        if not is_playing:
            return "restart"
        if is_paused:
            return "resume"
        return "keep"

    @staticmethod
    def resolve_duration_hint(song_duration, hinted_duration):
        duration = max(0.0, float(song_duration or 0.0))
        if duration > 0.0:
            return duration
        return max(0.0, float(hinted_duration or 0.0))

