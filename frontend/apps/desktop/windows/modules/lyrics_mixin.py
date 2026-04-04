import os
import shutil

from PyQt5.QtWidgets import QFileDialog

from frontend.apps.desktop.windows.modules.lyrics_worker import LyricsAsrWorker, LyricsFetchWorker, LyricsFetchPreviewWorker
from frontend.apps.desktop.windows.modules.manual_lyrics_fetch_dialog import ManualLyricsFetchDialog
from frontend.core.lrc_parser import parse_lrc_text
from frontend.utils.logging_utils import get_logger


logger = get_logger(__name__)


class LyricsMixin:
    def init_lyrics_state(self):
        self.current_lyrics_lines = []
        self.current_lyrics_index = -1
        self.current_lyrics_source = "none"
        self.lyrics_asr_worker = None
        self.lyrics_song_id = ""
        self.lyrics_asr_available = False
        self.lyrics_asr_running = False
        self._lyrics_asr_worker_token = 0
        self.lyrics_fetch_worker = None
        self.lyrics_fetch_running = False
        self._lyrics_fetch_worker_token = 0

    def clear_lyrics(self, text="暂无歌词"):
        self.current_lyrics_lines = []
        self.current_lyrics_index = -1
        self.current_lyrics_source = "none"
        self.lyrics_song_id = ""
        self.lyrics_asr_available = False
        self.lyrics_asr_running = False
        self.lyrics_fetch_running = False
        if getattr(self, "_is_closing", False):
            return
        self.lyric_label.setText(text)
        self._refresh_lyrics_asr_button()

    def load_lyrics_for_song(self, song):
        if not song:
            self.clear_lyrics()
            return
        if getattr(self, "_is_closing", False):
            return

        self.lyrics_song_id = song.get("id", "")
        self._stop_lyrics_worker_if_running()
        self._stop_online_lyrics_worker_if_running()

        try:
            result = self.lyrics_service.resolve_for_song(song)
            logger.info("歌词解析完成: song_id=%s source=%s lines=%s", song.get("id", ""), result.source, len(result.lines))
            self.current_lyrics_lines = result.lines
            self.current_lyrics_index = -1
            self.current_lyrics_source = result.source
            self.lyrics_asr_available = bool(self.lyrics_service.is_asr_available())
        except Exception as exc:
            logger.exception("歌词加载失败: song_id=%s", song.get("id", ""))
            self.clear_lyrics(f"暂无歌词（加载失败：{exc}）")
            self._show_lyrics_hint("歌词加载失败")
            return

        if self.current_lyrics_lines:
            self.update_lyrics_view(0)
            self._refresh_lyrics_asr_button()
            if self.current_lyrics_source == "local":
                self._show_lyrics_hint("已加载本地歌词", timeout_ms=1800)
            elif self.current_lyrics_source == "asr-cache":
                self._show_lyrics_hint("已加载缓存歌词", timeout_ms=1800)
            return

        if self.lyrics_asr_available:
            self.lyric_label.setText("未找到本地歌词，正在尝试在线获取...")
            self._show_lyrics_hint("正在尝试在线获取歌词", timeout_ms=2200)
            self._start_online_lyrics_fetch(song)
        else:
            self.lyric_label.setText("暂无歌词（离线识别不可用）")
            self._show_lyrics_hint("离线识别不可用，请检查依赖", timeout_ms=2500)
        self._refresh_lyrics_asr_button()

    def _start_online_lyrics_fetch(self, song, query_title="", query_artist=""):
        if getattr(self, "_is_closing", False):
            return
        if self.lyrics_fetch_running:
            return
        try:
            self.lyrics_fetch_running = True
            self._refresh_lyrics_asr_button()
            self._lyrics_fetch_worker_token += 1
            token = self._lyrics_fetch_worker_token
            worker = LyricsFetchWorker(
                self.lyrics_service,
                song,
                query_title=query_title,
                query_artist=query_artist,
                parent=self,
            )
            self.lyrics_fetch_worker = worker
            worker.finished_with_result.connect(
                lambda success, song_id, output_path, error_message, _worker=worker, _token=token: self.on_online_lyrics_finished(
                    success,
                    song_id,
                    output_path,
                    error_message,
                    worker_ref=_worker,
                    worker_token=_token,
                )
            )
            worker.start()
        except Exception:
            self.lyrics_fetch_worker = None
            self.lyrics_fetch_running = False
            self._refresh_lyrics_asr_button()

    def request_manual_online_lyrics(self):
        if getattr(self, "_is_closing", False):
            return
        if self.lyrics_fetch_running:
            self._show_lyrics_hint("在线歌词获取中，请稍候...", timeout_ms=2200)
            return
        if self.lyrics_asr_running:
            self._show_lyrics_hint("离线识别进行中，请稍候...", timeout_ms=2200)
            return

        current = dict(self.current_song or {})
        default_title = str(current.get("title", "") or "").strip()
        if not default_title:
            path = str(current.get("path", "") or "")
            default_title = os.path.splitext(os.path.basename(path))[0].strip()
        default_artist = str(current.get("artist", "") or "").strip()

        dialog = ManualLyricsFetchDialog(self, default_title=default_title, default_artist=default_artist)
        if dialog.exec_() != dialog.Accepted:
            return

        title = dialog.title_text
        artist = dialog.artist_text
        self.lyric_label.setText("正在在线获取歌词，请稍候...")
        self._show_lyrics_hint("开始手动在线获取歌词", timeout_ms=2200)

        if self.current_song:
            self._start_online_lyrics_fetch(self.current_song, query_title=title, query_artist=artist)
        else:
            self._start_online_lyrics_preview_fetch(query_title=title, query_artist=artist)

    def request_manual_local_lyrics_for_current_song(self):
        if getattr(self, "_is_closing", False):
            return
        if not self.current_song:
            self._show_lyrics_hint("请先播放歌曲", timeout_ms=2200)
            return
        if self.lyrics_fetch_running:
            self._show_lyrics_hint("在线歌词获取中，请稍候...", timeout_ms=2200)
            return
        if self.lyrics_asr_running:
            self._show_lyrics_hint("离线识别进行中，请稍候...", timeout_ms=2200)
            return

        song_path = str(self.current_song.get("path", "") or "")
        initial_dir = os.path.dirname(song_path) if song_path else ""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择歌词文件",
            initial_dir,
            "歌词文件 (*.lrc);;所有文件 (*.*)",
        )
        if not selected_path:
            return

        lines, _meta = self.lyrics_service.parse_lrc_safe(selected_path)
        if not lines:
            self._show_lyrics_hint("所选歌词文件为空或格式无效", timeout_ms=2800)
            return

        saved_path, save_error = self._save_selected_lyrics_for_song(self.current_song, selected_path)
        self.current_lyrics_lines = lines
        self.current_lyrics_index = -1
        self.current_lyrics_source = "manual-local"
        self.lyrics_asr_available = bool(self.lyrics_service.is_asr_available())
        self.update_lyrics_view(self.audio_player.get_position())
        self._refresh_lyrics_asr_button()
        if save_error:
            self._show_lyrics_hint(f"已加载歌词，但保存失败：{save_error}", timeout_ms=3200)
            return
        if saved_path:
            self._show_lyrics_hint("已加载并保存所选歌词", timeout_ms=2200)
            return
        self._show_lyrics_hint("已加载所选歌词", timeout_ms=2200)

    def _save_selected_lyrics_for_song(self, song, selected_path):
        audio_path = str((song or {}).get("path", "") or "")
        if not audio_path:
            return "", "当前歌曲路径无效"
        try:
            song_dir = os.path.dirname(audio_path)
            lyrics_dir = os.path.join(song_dir, "lyrics")
            os.makedirs(lyrics_dir, exist_ok=True)
            audio_name = os.path.splitext(os.path.basename(audio_path))[0].strip()
            if not audio_name:
                return "", "歌曲文件名无效"
            target_path = os.path.join(lyrics_dir, f"{audio_name}.lrc")
            if os.path.normcase(os.path.abspath(selected_path)) != os.path.normcase(os.path.abspath(target_path)):
                shutil.copyfile(selected_path, target_path)
            return target_path, ""
        except Exception as exc:
            logger.exception("保存手动选择歌词失败: song_id=%s path=%s", (song or {}).get("id", ""), selected_path)
            return "", str(exc)

    def _start_online_lyrics_preview_fetch(self, query_title, query_artist=""):
        if getattr(self, "_is_closing", False):
            return
        if self.lyrics_fetch_running:
            return
        try:
            self.lyrics_fetch_running = True
            self._refresh_lyrics_asr_button()
            self._lyrics_fetch_worker_token += 1
            token = self._lyrics_fetch_worker_token
            worker = LyricsFetchPreviewWorker(
                self.lyrics_service,
                query_title=query_title,
                query_artist=query_artist,
                parent=self,
            )
            self.lyrics_fetch_worker = worker
            worker.finished_with_result.connect(
                lambda success, lrc_text, error_message, _worker=worker, _token=token: self.on_online_lyrics_preview_finished(
                    success,
                    lrc_text,
                    error_message,
                    worker_ref=_worker,
                    worker_token=_token,
                )
            )
            worker.start()
        except Exception:
            self.lyrics_fetch_worker = None
            self.lyrics_fetch_running = False
            self._refresh_lyrics_asr_button()

    def on_online_lyrics_preview_finished(self, success, lrc_text, error_message, worker_ref=None, worker_token=None):
        if getattr(self, "_is_closing", False):
            self.lyrics_fetch_running = False
            return
        if worker_ref is not None and worker_ref is not self.lyrics_fetch_worker:
            try:
                worker_ref.deleteLater()
            except Exception:
                pass
            return
        if worker_token is not None and int(worker_token) != int(self._lyrics_fetch_worker_token):
            return

        self.lyrics_fetch_running = False
        if self.lyrics_fetch_worker:
            self.lyrics_fetch_worker.deleteLater()
            self.lyrics_fetch_worker = None

        if not success:
            self.lyric_label.setText("暂无歌词，可点击“识别歌词”手动生成")
            self._show_lyrics_hint(f"在线歌词获取失败：{error_message}", timeout_ms=3200)
            self._refresh_lyrics_asr_button()
            return

        lines, _metadata = parse_lrc_text(str(lrc_text or ""))
        if not lines:
            self.lyric_label.setText("在线歌词获取成功，但内容无时间轴")
            self._show_lyrics_hint("歌词获取成功，但无法按时间同步显示", timeout_ms=3200)
            self._refresh_lyrics_asr_button()
            return

        self.current_lyrics_lines = lines
        self.current_lyrics_index = -1
        self.current_lyrics_source = "online-manual-preview"
        self.lyrics_song_id = ""
        self.update_lyrics_view(0)
        self._show_lyrics_hint("手动在线歌词获取成功（仅预览，未保存）", timeout_ms=2600)
        self._refresh_lyrics_asr_button()

    def on_online_lyrics_finished(self, success, song_id, _output_path, error_message, worker_ref=None, worker_token=None):
        if getattr(self, "_is_closing", False):
            self.lyrics_fetch_running = False
            return
        if worker_ref is not None and worker_ref is not self.lyrics_fetch_worker:
            try:
                worker_ref.deleteLater()
            except Exception:
                pass
            return
        if worker_token is not None and int(worker_token) != int(self._lyrics_fetch_worker_token):
            return

        self.lyrics_fetch_running = False
        if self.lyrics_fetch_worker:
            self.lyrics_fetch_worker.deleteLater()
            self.lyrics_fetch_worker = None

        if not self.current_song or self.current_song.get("id", "") != song_id:
            self._refresh_lyrics_asr_button()
            return

        if not success:
            self.lyric_label.setText("暂无歌词，可点击“识别歌词”手动生成")
            self._show_lyrics_hint(f"在线歌词获取失败：{error_message}", timeout_ms=3200)
            self._refresh_lyrics_asr_button()
            return

        try:
            result = self.lyrics_service.resolve_for_song(self.current_song)
            self.current_lyrics_lines = result.lines
            self.current_lyrics_index = -1
            self.current_lyrics_source = "online"
            self.lyrics_asr_available = bool(self.lyrics_service.is_asr_available())
        except Exception as exc:
            self.clear_lyrics(f"暂无歌词（在线歌词刷新失败：{exc}）")
            self._show_lyrics_hint("在线歌词刷新失败", timeout_ms=3200)
            return

        if not self.current_lyrics_lines:
            self.lyric_label.setText("暂无歌词，可点击“识别歌词”手动生成")
            self._show_lyrics_hint("在线歌词获取成功，但内容不可用", timeout_ms=3200)
            self._refresh_lyrics_asr_button()
            return

        self.update_lyrics_view(self.audio_player.get_position())
        self._show_lyrics_hint("在线歌词获取成功", timeout_ms=2200)
        self._refresh_lyrics_asr_button()

    def request_lyrics_asr_for_current_song(self):
        if getattr(self, "_is_closing", False):
            return
        if self.lyrics_fetch_running:
            self._show_lyrics_hint("在线歌词获取中，请稍候...", timeout_ms=2200)
            return
        if self.lyrics_asr_running:
            logger.info("忽略重复识别请求：已有任务进行中")
            self._show_lyrics_hint("歌词识别进行中，请稍候...")
            return
        if not self.current_song:
            self.lyric_label.setText("请先播放歌曲")
            self._refresh_lyrics_asr_button()
            self._show_lyrics_hint("请先播放歌曲")
            return
        if not self.lyrics_asr_available:
            self.lyric_label.setText("离线识别不可用，请检查依赖")
            self._refresh_lyrics_asr_button()
            self._show_lyrics_hint("离线识别不可用，请检查依赖")
            return

        self.lyric_label.setText("正在离线识别歌词，请稍候...")
        self._show_lyrics_hint("开始识别歌词，请稍候...", timeout_ms=2200)
        logger.info("开始歌词识别: song_id=%s", self.current_song.get("id", "") if self.current_song else "")
        self._start_lyrics_asr(self.current_song)

    def reload_local_lyrics_for_current_song(self):
        if getattr(self, "_is_closing", False):
            return
        if not self.current_song:
            self._show_lyrics_hint("请先播放歌曲", timeout_ms=2200)
            return
        if self.lyrics_asr_running:
            self._show_lyrics_hint("歌词识别进行中，请稍候再重载", timeout_ms=2600)
            return

        song = self.current_song
        local_path = ""
        try:
            local_path = self.lyrics_service.find_local_lrc(song)
        except Exception:
            local_path = ""

        if not local_path or not os.path.exists(local_path):
            self._show_lyrics_hint("未找到本地歌词文件", timeout_ms=2600)
            return

        lines, _meta = self.lyrics_service.parse_lrc_safe(local_path)
        if not lines:
            self.current_lyrics_lines = []
            self.current_lyrics_index = -1
            self.current_lyrics_source = "none"
            self.lyric_label.setText("本地歌词为空或格式无效")
            self._refresh_lyrics_asr_button()
            self._show_lyrics_hint("本地歌词解析失败", timeout_ms=2600)
            return

        self.current_lyrics_lines = lines
        self.current_lyrics_index = -1
        self.current_lyrics_source = "local"
        self.lyrics_asr_available = bool(self.lyrics_service.is_asr_available())
        self.update_lyrics_view(self.audio_player.get_position())
        self._refresh_lyrics_asr_button()
        self._show_lyrics_hint("已重新加载本地歌词", timeout_ms=2000)

    def _show_lyrics_hint(self, message, timeout_ms=2500):
        if hasattr(self, "show_status_hint"):
            self.show_status_hint(message, timeout_ms=timeout_ms)
            return
        try:
            if hasattr(self, "statusBar"):
                bar = self.statusBar()
                if bar is not None:
                    bar.showMessage(message, int(timeout_ms))
                    return
        except Exception:
            pass

    def update_lyrics_view(self, current_seconds):
        if not self.current_lyrics_lines:
            return
        if getattr(self, "_is_closing", False):
            return

        position_ms = int(max(0.0, current_seconds) * 1000)
        target_index = self.lyrics_service.current_line_index(self.current_lyrics_lines, position_ms)
        if target_index == self.current_lyrics_index:
            return

        self.current_lyrics_index = target_index
        if target_index < 0:
            self.lyric_label.setText("...")
            return

        line = self.current_lyrics_lines[target_index]
        self.lyric_label.setText(line.text or "...")

    def _start_lyrics_asr(self, song):
        if getattr(self, "_is_closing", False):
            return
        try:
            self.lyrics_asr_running = True
            self._refresh_lyrics_asr_button()
            self._lyrics_asr_worker_token += 1
            token = self._lyrics_asr_worker_token
            worker = LyricsAsrWorker(self.lyrics_service, song, self)
            self.lyrics_asr_worker = worker
            logger.debug("歌词识别线程已启动: song_id=%s token=%s", song.get("id", ""), token)
            worker.finished_with_result.connect(
                lambda success, song_id, output_path, error_message, _worker=worker, _token=token: self.on_lyrics_asr_finished(
                    success,
                    song_id,
                    output_path,
                    error_message,
                    worker_ref=_worker,
                    worker_token=_token,
                )
            )
            worker.start()
        except Exception as exc:
            logger.exception("歌词识别线程启动失败: song_id=%s", song.get("id", ""))
            self.lyrics_asr_worker = None
            self.lyrics_asr_running = False
            self.lyric_label.setText(f"暂无歌词（识别未启动：{exc}）")
            self._refresh_lyrics_asr_button()

    def on_lyrics_asr_finished(self, success, song_id, _output_path, error_message, worker_ref=None, worker_token=None):
        if getattr(self, "_is_closing", False):
            self.lyrics_asr_running = False
            return
        if worker_ref is not None and worker_ref is not self.lyrics_asr_worker:
            logger.debug("忽略过期歌词回调: song_id=%s token=%s", song_id, worker_token)
            try:
                worker_ref.deleteLater()
            except Exception:
                pass
            return
        if worker_token is not None and int(worker_token) != int(self._lyrics_asr_worker_token):
            return

        self.lyrics_asr_running = False
        if self.lyrics_asr_worker:
            self.lyrics_asr_worker.deleteLater()
            self.lyrics_asr_worker = None

        if not self.current_song or self.current_song.get("id", "") != song_id:
            self._refresh_lyrics_asr_button()
            return

        if not success:
            logger.warning("歌词识别失败: song_id=%s error=%s", song_id, error_message)
            self.lyric_label.setText(f"暂无歌词（识别失败：{error_message}）")
            if "疑似纯音乐" in str(error_message or ""):
                self._show_lyrics_hint("检测到疑似纯音乐，已跳过离线识别", timeout_ms=3200)
            else:
                self._show_lyrics_hint(f"歌词识别失败：{error_message}", timeout_ms=3500)
            self._refresh_lyrics_asr_button()
            return

        try:
            result = self.lyrics_service.resolve_for_song(self.current_song)
            self.current_lyrics_lines = result.lines
            self.current_lyrics_index = -1
            self.current_lyrics_source = result.source
            self.lyrics_asr_available = bool(self.lyrics_service.is_asr_available())
        except Exception as exc:
            logger.exception("歌词识别后刷新失败: song_id=%s", song_id)
            self.clear_lyrics(f"暂无歌词（刷新失败：{exc}）")
            self._show_lyrics_hint("歌词刷新失败", timeout_ms=3200)
            return
        if not self.current_lyrics_lines:
            self.lyric_label.setText("暂无歌词")
            self._show_lyrics_hint("识别完成，但未生成可用歌词", timeout_ms=3200)
            self._refresh_lyrics_asr_button()
            return

        self.update_lyrics_view(self.audio_player.get_position())
        self._show_lyrics_hint("歌词识别成功", timeout_ms=2200)
        self._refresh_lyrics_asr_button()
        logger.info("歌词识别成功: song_id=%s lines=%s", song_id, len(self.current_lyrics_lines))

    def _stop_lyrics_worker_if_running(self):
        worker = getattr(self, "lyrics_asr_worker", None)
        if worker and hasattr(worker, "isRunning") and worker.isRunning():
            if hasattr(worker, "requestInterruption"):
                worker.requestInterruption()
            if hasattr(worker, "quit"):
                worker.quit()
            if hasattr(worker, "wait"):
                worker.wait(200)
        self.lyrics_asr_running = False
        if not getattr(self, "_is_closing", False):
            self._refresh_lyrics_asr_button()

    def _stop_online_lyrics_worker_if_running(self):
        worker = getattr(self, "lyrics_fetch_worker", None)
        if worker and hasattr(worker, "isRunning") and worker.isRunning():
            if hasattr(worker, "requestInterruption"):
                worker.requestInterruption()
            if hasattr(worker, "quit"):
                worker.quit()
            if hasattr(worker, "wait"):
                worker.wait(200)
        self.lyrics_fetch_running = False
        if not getattr(self, "_is_closing", False):
            self._refresh_lyrics_asr_button()

    def _refresh_lyrics_asr_button(self):
        if not hasattr(self, "lyrics_asr_btn"):
            return
        if getattr(self, "_is_closing", False):
            return
        if self.lyrics_fetch_running:
            self.lyrics_asr_btn.setEnabled(False)
            self.lyrics_asr_btn.setText("获取中...")
            return
        if self.lyrics_asr_running:
            self.lyrics_asr_btn.setEnabled(False)
            self.lyrics_asr_btn.setText("识别中...")
            return
        can_trigger = bool(self.current_song) and self.lyrics_asr_available
        self.lyrics_asr_btn.setEnabled(can_trigger)
        if self.current_lyrics_lines:
            self.lyrics_asr_btn.setText("重新识别")
        else:
            self.lyrics_asr_btn.setText("识别歌词")

    def cleanup_lyrics(self):
        self._stop_lyrics_worker_if_running()
        self._stop_online_lyrics_worker_if_running()
        worker = getattr(self, "lyrics_asr_worker", None)
        if worker and hasattr(worker, "deleteLater"):
            worker.deleteLater()
        if worker is not None:
            self.lyrics_asr_worker = None
        fetch_worker = getattr(self, "lyrics_fetch_worker", None)
        if fetch_worker and hasattr(fetch_worker, "deleteLater"):
            fetch_worker.deleteLater()
        if fetch_worker is not None:
            self.lyrics_fetch_worker = None

