import os

from PyQt5.QtCore import Qt

try:
    from frontend.apps.desktop.windows.modules.online_search_dialog import OnlineSearchDialog
    from frontend.apps.desktop.windows.modules.online_workers import (
        NetworkCheckWorker,
        OnlineDownloadWorker,
        OnlineSearchWorker,
    )
except ModuleNotFoundError:
    from apps.desktop.windows.modules.online_search_dialog import OnlineSearchDialog
    from apps.desktop.windows.modules.online_workers import (
        NetworkCheckWorker,
        OnlineDownloadWorker,
        OnlineSearchWorker,
    )


class OnlineSearchMixin:
    def open_online_search(self):
        if not self.online_music_service.is_network_available:
            self.show_nonblocking_error("网络未连接，请检查网络设置")
            return
        dialog = OnlineSearchDialog(self)
        dialog.exec_()

    def play_online_preview(self, song_data):
        try:
            song_url = self.online_music_service.get_song_url(
                song_data.get("id", ""), song_data.get("source", "netease")
            )
        except Exception as e:
            self.show_nonblocking_error(f"获取播放链接失败: {e}")
            return

        preview_song = {
            "id": f"online_{song_data.get('id', '')}",
            "title": song_data.get("name", ""),
            "artist": song_data.get("artist", ""),
            "album": song_data.get("album", ""),
            "path": song_url,
            "duration": 0,
        }

        self.current_song = preview_song
        self._play_song(preview_song)
        self.show_status_hint(f"在线试听: {preview_song['artist']} - {preview_song['title']}")

    def download_online_song(self, song_data):
        save_dir = self._get_download_dir()
        self._download_worker = OnlineDownloadWorker(
            self.online_music_service, song_data, save_dir, parent=self
        )
        self._download_worker.progress_updated.connect(self._on_download_progress)
        self._download_worker.finished_with_result.connect(self._on_download_finished)
        self._download_worker.start()
        self.show_status_hint(f"开始下载: {song_data.get('artist', '')} - {song_data.get('name', '')}")

    def download_online_lyric(self, song_data):
        try:
            lyric = self.online_music_service.get_lyric(
                song_data.get("lyric_id", "") or song_data.get("id", ""),
                song_data.get("source", "netease"),
            )
        except Exception as e:
            self.show_nonblocking_error(f"获取歌词失败: {e}")
            return

        if not lyric:
            self.show_nonblocking_error("未找到歌词")
            return

        save_dir = self._get_download_dir()
        safe_name = self.online_music_service._sanitize_filename(
            f"{song_data.get('artist', '')} - {song_data.get('name', '')}"
        )
        lyric_path = os.path.join(save_dir, f"{safe_name}.lrc")
        os.makedirs(save_dir, exist_ok=True)
        with open(lyric_path, "w", encoding="utf-8") as f:
            f.write(lyric)
        self.show_status_hint(f"歌词已保存: {lyric_path}")

    def _on_download_progress(self, song_id, progress):
        pct = int(progress * 100)
        self.show_status_hint(f"下载中... {pct}%")

    def _on_download_finished(self, success, song_id, file_path, error):
        if success:
            self.show_status_hint(f"下载完成: {os.path.basename(file_path)}")
            self._import_downloaded_song(file_path)
        else:
            self.show_nonblocking_error(f"下载失败: {error}")

    def _import_downloaded_song(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return

        song_info = self.music_library._extract_song_info(file_path)
        if song_info:
            song_dict = {
                "id": song_info.get("id", ""),
                "title": song_info.get("title", ""),
                "artist": song_info.get("artist", ""),
                "album": song_info.get("album", ""),
                "path": song_info.get("path", file_path),
                "duration": song_info.get("duration", 0),
            }
            self.playlist_manager.add_song(song_dict)
            self.render_playlist()
            self.show_status_hint(f"已添加到歌单: {song_dict['title']}")

    def _get_download_dir(self):
        if hasattr(self, "download_dir") and self.download_dir:
            return self.download_dir
        app_dir = getattr(self, "app_data_dir", "")
        if app_dir:
            return os.path.join(app_dir, "downloads")
        return os.path.join(os.path.expanduser("~"), "Music", "RHYME")
