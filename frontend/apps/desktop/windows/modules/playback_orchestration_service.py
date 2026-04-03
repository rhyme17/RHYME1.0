class PlaybackOrchestrationService:
    @staticmethod
    def switch_high_quality_mode(audio_player, current_song, old_mode, target_mode):
        audio_player.set_high_quality_output_mode(target_mode)

        if not (getattr(audio_player, "is_playing", False) and current_song):
            return {
                "success": True,
                "final_mode": bool(target_mode),
                "message": "高音质模式已切换",
            }

        was_paused = bool(getattr(audio_player, "is_paused", False))
        playback_applied = bool(audio_player.reopen_stream_from_current_buffer(keep_pause_state=was_paused))
        if playback_applied:
            return {
                "success": True,
                "final_mode": bool(target_mode),
                "message": "高音质模式已切换",
            }

        audio_player.set_high_quality_output_mode(old_mode)
        if current_song:
            rollback_paused = bool(getattr(audio_player, "is_paused", False))
            rollback_applied = bool(audio_player.reopen_stream_from_current_buffer(keep_pause_state=rollback_paused))
            if not rollback_applied:
                resume_seconds = max(0.0, float(audio_player.get_position()))
                rollback_applied = bool(
                    audio_player.play(
                        current_song.get("path", ""),
                        start_position=int(resume_seconds * 1000),
                    )
                )
                if rollback_applied and rollback_paused:
                    audio_player.pause()

        return {
            "success": False,
            "final_mode": bool(old_mode),
            "message": "高音质模式切换失败，已自动回退",
        }

