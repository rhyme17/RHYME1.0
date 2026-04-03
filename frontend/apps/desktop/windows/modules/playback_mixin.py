import os

from PyQt5.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, QTimer
from PyQt5.QtWidgets import QMessageBox

from frontend.apps.desktop.windows.modules.player_orchestration_service import PlayerOrchestrationService
from frontend.apps.desktop.windows.modules.playback_orchestration_service import PlaybackOrchestrationService
try:
    from frontend.apps.desktop.windows.modules.decode_worker import DecodeWorker
except ModuleNotFoundError:
    from apps.desktop.windows.modules.decode_worker import DecodeWorker
from frontend.utils.helpers import format_time


class PlaybackMixin:
    PROGRESS_TIMER_INTERVAL_MS = 200
    PROGRESS_ANIMATION_DURATION_MS = 140

    def _set_progress_visual_active(self, active):
        slider = getattr(self, "progress_slider", None)
        if slider is None or not hasattr(slider, "set_playback_active"):
            return
        try:
            slider.set_playback_active(bool(active))
        except Exception:
            return

    def set_progress_visual_pulse_enabled(self, enabled):
        slider = getattr(self, "progress_slider", None)
        if slider is None or not hasattr(slider, "set_pulse_enabled"):
            return
        try:
            slider.set_pulse_enabled(bool(enabled))
        except Exception:
            return

    def set_progress_visual_wave_enabled(self, enabled):
        slider = getattr(self, "progress_slider", None)
        if slider is None or not hasattr(slider, "set_wave_enabled"):
            return
        try:
            slider.set_wave_enabled(bool(enabled))
        except Exception:
            return

    def set_progress_visual_accent_enabled(self, enabled):
        slider = getattr(self, "progress_slider", None)
        if slider is None or not hasattr(slider, "set_accent_enabled"):
            return
        try:
            slider.set_accent_enabled(bool(enabled))
        except Exception:
            return

    def _push_progress_visual_intensity(self):
        slider = getattr(self, "progress_slider", None)
        if slider is None or not hasattr(slider, "set_audio_intensity"):
            return
        intensity = 0.0
        accent = 0.0
        if hasattr(self, "audio_player") and hasattr(self.audio_player, "get_visual_intensity"):
            try:
                intensity = float(self.audio_player.get_visual_intensity())
            except Exception:
                intensity = 0.0
        if hasattr(self, "audio_player") and hasattr(self.audio_player, "get_visual_accent"):
            try:
                accent = float(self.audio_player.get_visual_accent())
            except Exception:
                accent = 0.0
        slider.set_audio_intensity(max(0.0, min(1.0, intensity)))
        if hasattr(slider, "set_audio_accent"):
            slider.set_audio_accent(max(0.0, min(1.0, accent)))

    def _show_playback_hint(self, message, timeout_ms=2500):
        try:
            if hasattr(self, "statusBar"):
                bar = self.statusBar()
                if bar is not None:
                    bar.showMessage(message, int(timeout_ms))
                    return
        except Exception:
            return

    def _align_track_index_with_current_song(self):
        current = getattr(self, "current_song", None)
        if not current:
            return
        playlist = self.playlist_manager.get_playlist()
        if not playlist:
            return
        target_id = str(current.get("id", "") or "")
        target_path = str(current.get("path", "") or "").strip().lower()
        for idx, song in enumerate(playlist):
            song_id = str(song.get("id", "") or "")
            song_path = str(song.get("path", "") or "").strip().lower()
            if target_id and song_id == target_id:
                self.current_track_index = idx
                return
            if target_path and song_path == target_path:
                self.current_track_index = idx
                return

    def _cancel_decode_worker(self):
        worker = getattr(self, "decode_worker", None)
        if worker is None:
            return
        if worker.isRunning():
            worker.requestInterruption()
            worker.quit()
            # 不阻塞主线程等待解码结束；由 finished 回调再安全释放。
            return
        worker.deleteLater()
        self.decode_worker = None

    def _finish_play_after_start(self, song, pending_song_id, resume_seconds):
        self.current_duration = max(self.current_duration, float(getattr(self.audio_player, "_duration_seconds", 0.0) or 0.0))
        self.total_time_label.setText(format_time(self.current_duration))
        self.current_song = song
        self._last_progress_save_bucket = -1
        # 统一在实际开始播放后回写按钮状态，避免残留“加载中...”。
        if getattr(self.audio_player, "is_playing", False):
            self.play_btn.setText("▶" if getattr(self.audio_player, "is_paused", False) else "⏸")
        else:
            self.play_btn.setText("▶")
        if pending_song_id and pending_song_id == str(song.get("id", "") or ""):
            self._pending_resume_song_id = ""
            self._pending_resume_position_seconds = 0.0
        self.load_lyrics_for_song(song)
        self.update_lyrics_view(resume_seconds)
        self._set_progress_visual_active(True)
        self._push_progress_visual_intensity()
        self.start_progress_timer()

    def _on_decode_worker_finished(self, request_id, success, payload, error_message):
        worker = self.sender() if hasattr(self, "sender") else None
        if worker is not None and worker is getattr(self, "decode_worker", None):
            self.decode_worker = None
        if worker is not None and hasattr(worker, "deleteLater"):
            worker.deleteLater()

        if int(request_id) != int(getattr(self, "_decode_request_id", 0)):
            # 过期回调直接丢弃，不能改写当前请求的切歌状态。
            if getattr(self.audio_player, "is_playing", False):
                self.play_btn.setText("▶" if getattr(self.audio_player, "is_paused", False) else "⏸")
            return
        context = getattr(self, "_pending_decode_context", None) or {}
        self._pending_decode_context = None

        if not success:
            self._is_track_switching = False
            self.play_btn.setText("▶")
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            self._show_playback_hint(f"解码失败：{error_message}", timeout_ms=3200)
            return

        song = context.get("song")
        if not song:
            return
        start_position_ms = int(context.get("start_position_ms", 0) or 0)
        pending_song_id = str(context.get("pending_song_id", "") or "")
        resume_seconds = float(context.get("resume_seconds", 0.0) or 0.0)

        started = self.audio_player.play_predecoded(song.get("path", ""), payload, start_position=start_position_ms)
        if not started:
            self._is_track_switching = False
            self.play_btn.setText("▶")
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            self._show_playback_hint("播放失败", timeout_ms=3000)
            return

        self._is_track_switching = False
        self._finish_play_after_start(song, pending_song_id, resume_seconds)

    def _start_async_decode_play(self, song, start_position_ms, pending_song_id, resume_seconds):
        # 新请求先提升代次，保证旧 worker 回调全部作废。
        self._decode_request_id = int(getattr(self, "_decode_request_id", 0)) + 1
        self._cancel_decode_worker()
        request_id = self._decode_request_id
        self._pending_decode_context = {
            "song": song,
            "start_position_ms": int(start_position_ms),
            "pending_song_id": pending_song_id,
            "resume_seconds": float(resume_seconds),
        }

        self.play_btn.setText("加载中...")
        self._set_progress_visual_active(False)
        self._push_progress_visual_intensity()

        worker = DecodeWorker(self.audio_player, song.get("path", ""), request_id)
        worker.finished.connect(self._on_decode_worker_finished)
        self.decode_worker = worker
        worker.start()

    def restart_current_song(self):
        playlist = self.playlist_manager.get_playlist()
        if not playlist:
            return False

        self._align_track_index_with_current_song()

        if self.current_track_index < 0 or self.current_track_index >= len(playlist):
            self.current_track_index = 0

        song = playlist[self.current_track_index]
        self._pending_resume_song_id = ""
        self._pending_resume_position_seconds = 0.0
        self.current_song = song

        # 同曲目重播优先复用已解码缓冲，减少重复解码卡顿。
        same_loaded_file = str(getattr(self.audio_player, "current_file", "") or "") == str(song.get("path", "") or "")
        has_buffer = getattr(self.audio_player, "_audio_data", None) is not None
        if same_loaded_file and has_buffer:
            self.audio_player.seek(0.0)
            if self.audio_player.reopen_stream_from_current_buffer(keep_pause_state=False):
                self._is_track_switching = False
                self.play_btn.setText("⏸")
                self._set_progress_visual_active(True)
                self._push_progress_visual_intensity()
                self.current_time_label.setText("0:00")
                self._stop_progress_animation()
                self.progress_slider.setValue(0)
                self.update_lyrics_view(0)
                self.start_progress_timer()
                return True

        self._is_track_switching = True
        return self.play_current_song(force_restart=True)

    def refresh_high_quality_output_button(self):
        if not hasattr(self, "high_quality_btn"):
            return
        enabled = bool(getattr(self, "high_quality_output_enabled", False))
        self.high_quality_btn.setText("高音质：开" if enabled else "高音质：关")

    def toggle_high_quality_output(self):
        old_mode = bool(getattr(self, "high_quality_output_enabled", False))
        target_mode = not old_mode

        result = PlaybackOrchestrationService.switch_high_quality_mode(
            self.audio_player,
            self.current_song,
            old_mode,
            target_mode,
        )
        self.high_quality_output_enabled = bool(result.get("final_mode", old_mode))
        if getattr(self.audio_player, "is_playing", False):
            self.play_btn.setText("▶" if getattr(self.audio_player, "is_paused", False) else "⏸")
        self._show_playback_hint(result.get("message", ""))

        self.refresh_high_quality_output_button()
        if hasattr(self, "schedule_save_app_settings"):
            self.schedule_save_app_settings()

    def play_current_song(self, force_restart=False):
        try:
            playlist = self.playlist_manager.get_playlist()
            if not playlist or self.current_track_index >= len(playlist):
                return False

            song = playlist[self.current_track_index]
            file_path = song['path']
            song_id = str(song.get('id', '') or '')

            # 避免对“当前正在播放的同一首歌”重复执行 stop + 重新解码，减少双击卡顿。
            current_song_id = ""
            if getattr(self, "current_song", None):
                current_song_id = str(self.current_song.get("id", "") or "")
            same_song_action = PlayerOrchestrationService.resolve_same_song_action(
                force_restart,
                current_song_id,
                song_id,
                getattr(self.audio_player, "is_playing", False),
                getattr(self.audio_player, "is_paused", False),
            )
            if same_song_action == "resume":
                if self.audio_player.resume():
                    self.play_btn.setText("⏸")
                    self._set_progress_visual_active(True)
                    self._push_progress_visual_intensity()
                return True
            if same_song_action == "keep":
                self.play_btn.setText("⏸")
                self._set_progress_visual_active(True)
                self._push_progress_visual_intensity()
                return True

            if not os.path.exists(file_path):
                QMessageBox.warning(self, "错误", f"文件不存在: {file_path}")
                return False

            file_size_bytes = os.path.getsize(file_path)
            # 优先使用扫描阶段已提取的 duration，避免播放前重复探测。
            hinted_duration = self.audio_player.get_duration_hint(file_path)
            self.current_duration = PlayerOrchestrationService.resolve_duration_hint(song.get("duration", 0.0), hinted_duration)
            should_warn, file_size_mb, estimated_pcm_mb = self.audio_player.should_warn_heavy_decode(
                file_size_bytes,
                self.current_duration,
                file_size_threshold_mb=self.file_size_warning_mb,
                pcm_threshold_mb=self.decode_memory_warning_mb,
            )
            if should_warn:
                if bool(getattr(self, "async_decode_on_play", False)):
                    self._show_playback_hint(
                        f"大文件播放：{file_size_mb:.1f}MB，预估解码内存 {estimated_pcm_mb:.1f}MB",
                        timeout_ms=2600,
                    )
                else:
                    answer = QMessageBox.question(
                        self,
                        "大文件播放提示",
                        (
                            f"该文件体积约 {file_size_mb:.1f} MB，"
                            f"预计解码峰值内存约 {estimated_pcm_mb:.1f} MB。\n"
                            "继续播放可能导致卡顿或较高内存占用，是否继续？"
                        ),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if answer != QMessageBox.Yes:
                        return False

            previous_song_id = ""
            if getattr(self, "current_song", None):
                previous_song_id = str(self.current_song.get("id", "") or "")
            if previous_song_id and previous_song_id != song_id and hasattr(self, "save_app_settings"):
                self.save_app_settings()

            self._is_track_switching = True
            self.audio_player.stop()

            resume_seconds = 0.0
            pending_song_id = str(getattr(self, "_pending_resume_song_id", "") or "")
            if pending_song_id and pending_song_id == song_id:
                resume_seconds = PlayerOrchestrationService.normalize_resume_seconds(
                    getattr(self, "_pending_resume_position_seconds", 0.0),
                    self.current_duration,
                )

            start_position_ms = int(resume_seconds * 1000)

            self.song_title_label.setText(song['title'])
            self.song_artist_label.setText(song['artist'])
            self.play_btn.setText("⏸")

            self.total_time_label.setText(format_time(self.current_duration))
            self._stop_progress_animation()
            if self.current_duration > 0:
                progress = int((resume_seconds / self.current_duration) * 100)
                self.progress_slider.setValue(max(0, min(100, progress)))
            else:
                self.progress_slider.setValue(0)
            self.current_time_label.setText(format_time(resume_seconds))

            if bool(getattr(self, "async_decode_on_play", False)) and not self.audio_player.has_decoded_cache(file_path):
                self._start_async_decode_play(song, start_position_ms, pending_song_id, resume_seconds)
                return True

            success = self.audio_player.play(file_path, start_position=start_position_ms)
            if success:
                self._is_track_switching = False
                self._finish_play_after_start(song, pending_song_id, resume_seconds)
                return True

            self._is_track_switching = False
            QMessageBox.warning(self, "错误", "播放失败")
            self.play_btn.setText("▶")
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            return False
        except Exception as exc:
            self._is_track_switching = False
            QMessageBox.warning(self, "错误", f"播放发生异常：{exc}")
            self.play_btn.setText("▶")
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            return False

    def start_progress_timer(self):
        if self.progress_timer:
            self.progress_timer.stop()

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(self.PROGRESS_TIMER_INTERVAL_MS)

    def _stop_progress_animation(self):
        anim = getattr(self, "_progress_anim", None)
        if anim is None:
            return
        try:
            if anim.state() != QAbstractAnimation.Stopped:
                anim.stop()
        except Exception:
            return

    def _animate_progress_to(self, target_progress):
        if not hasattr(self, "progress_slider"):
            return
        target = max(0, min(100, int(target_progress)))
        if self.progress_slider.isSliderDown():
            return

        current = int(self.progress_slider.value())
        if abs(target - current) <= 1:
            self.progress_slider.setValue(target)
            return

        if getattr(self, "_progress_anim", None) is None:
            self._progress_anim = QPropertyAnimation(self.progress_slider, b"value", self)
            self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._progress_anim.stop()
        self._progress_anim.setDuration(self.PROGRESS_ANIMATION_DURATION_MS)
        self._progress_anim.setStartValue(current)
        self._progress_anim.setEndValue(target)
        self._progress_anim.start()

    def update_progress(self):
        if not self.audio_player.is_playing:
            if bool(getattr(self, "_is_track_switching", False)):
                return
            if self.progress_timer:
                self.progress_timer.stop()
            self.play_btn.setText("▶")
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            self._stop_progress_animation()
            self.progress_slider.setValue(0)
            self.current_time_label.setText("0:00")
            self.update_lyrics_view(0)
            self.play_next()
            return

        if self.current_duration <= 0:
            self._set_progress_visual_active(False)
            self._push_progress_visual_intensity()
            self._stop_progress_animation()
            self.current_time_label.setText("0:00")
            self.progress_slider.setValue(0)
            return

        current_time = self.audio_player.get_position()
        current_time = max(0.0, min(current_time, self.current_duration))
        progress = int((current_time / self.current_duration) * 100)
        self._animate_progress_to(progress)
        self._push_progress_visual_intensity()
        self.current_time_label.setText(format_time(current_time))
        self.update_lyrics_view(current_time)

    def toggle_play(self):
        if self.audio_player.is_playing and self.audio_player.is_paused:
            if self.audio_player.resume():
                self.play_btn.setText("⏸")
                self._set_progress_visual_active(True)
                self._push_progress_visual_intensity()
            return

        if self.audio_player.is_playing:
            if self.audio_player.pause():
                self.play_btn.setText("▶")
                self._set_progress_visual_active(False)
                self._push_progress_visual_intensity()
                if hasattr(self, "schedule_save_app_settings"):
                    self.schedule_save_app_settings()
            return

        if not self.current_song:
            playlist = self.playlist_manager.get_playlist()
            if playlist:
                self.current_track_index = 0
                self.play_current_song()
        else:
            if self.play_current_song():
                self.play_btn.setText("⏸")

    def play_previous(self):
        playlist = self.playlist_manager.get_playlist()
        if not playlist:
            return

        self.current_track_index = (self.current_track_index - 1) % len(playlist)
        self.play_current_song()

    def play_next(self):
        playlist = self.playlist_manager.get_playlist()
        if not playlist:
            return

        self.current_track_index = PlayerOrchestrationService.next_track_index(
            self.current_track_index,
            len(playlist),
            self.playback_mode,
        )

        self.play_current_song()

    def set_volume(self, value, persist=True):
        volume = PlayerOrchestrationService.map_slider_volume_to_gain(value)
        self.audio_player.set_volume(volume)

        if value == 0:
            self.mute_btn.setText("🔇")
            self.is_muted = True
        else:
            self.mute_btn.setText("🔊")
            self.is_muted = False
            self.last_volume = value

        if persist:
            if hasattr(self, "schedule_save_app_settings"):
                self.schedule_save_app_settings()
            elif hasattr(self, "save_app_settings"):
                self.save_app_settings()

    def toggle_mute(self):
        if self.is_muted:
            self.volume_slider.setValue(self.last_volume)
            self.mute_btn.setText("🔊")
            self.is_muted = False
        else:
            self.last_volume = self.volume_slider.value()
            self.volume_slider.setValue(0)
            self.mute_btn.setText("🔇")
            self.is_muted = True

    def toggle_playback_mode(self):
        modes = ["顺序播放", "随机播放", "单曲循环"]
        current_index = modes.index(self.playback_mode)
        next_index = (current_index + 1) % len(modes)
        self.playback_mode = modes[next_index]
        self.mode_btn.setText(self.playback_mode)

    def set_position(self, position):
        self._stop_progress_animation()
        if self.current_duration <= 0:
            self.progress_slider.setValue(0)
            self.current_time_label.setText("0:00")
            return

        self.progress_slider.setValue(position)
        current_time = (position / 100) * self.current_duration
        self.current_time_label.setText(format_time(current_time))
        self.audio_player.seek(current_time)
        self.update_lyrics_view(current_time)
        if hasattr(self, "schedule_save_app_settings"):
            self.schedule_save_app_settings()

    def set_position_preview(self, position):
        if self.current_duration <= 0:
            self.current_time_label.setText("0:00")
            return
        current_time = (max(0, min(100, int(position))) / 100.0) * self.current_duration
        self.current_time_label.setText(format_time(current_time))

    def apply_slider_position(self):
        if not hasattr(self, "progress_slider"):
            return
        self._stop_progress_animation()
        self.set_position(self.progress_slider.value())

    def _seek_by_delta_seconds(self, delta_seconds):
        self._stop_progress_animation()
        if self.current_duration <= 0:
            return
        current_time = self.audio_player.get_position()
        target = max(0.0, min(current_time + delta_seconds, self.current_duration))
        progress = int((target / self.current_duration) * 100) if self.current_duration > 0 else 0
        self.progress_slider.setValue(progress)
        self.current_time_label.setText(format_time(target))
        self.audio_player.seek(target)
        self.update_lyrics_view(target)
        if hasattr(self, "schedule_save_app_settings"):
            self.schedule_save_app_settings()

