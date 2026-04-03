import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

from frontend.apps.desktop.windows.modules.scan_controller import ScanController
from frontend.apps.desktop.windows.modules.player_orchestration_service import PlayerOrchestrationService
from frontend.apps.desktop.windows.modules.library_orchestration_service import LibraryOrchestrationService
from frontend.apps.desktop.windows.modules.scan_dialog import ScanDialog


class LibraryMixin:
    @staticmethod
    def _resolve_song_index_by_id_or_path(playlist, song):
        index = PlayerOrchestrationService.resolve_song_index_by_id(playlist, song.get("id", ""))
        if index >= 0:
            return index
        target_path = str(song.get("path", "") or "").strip().lower()
        if not target_path:
            return -1
        for i, playlist_song in enumerate(playlist or []):
            song_path = str(playlist_song.get("path", "") or "").strip().lower()
            if song_path == target_path:
                return i
        return -1

    def _get_scan_controller(self):
        controller = getattr(self, "_scan_controller", None)
        if controller is None:
            controller = ScanController(self)
            self._scan_controller = controller
        return controller

    def open_scan_dialog(self):
        dialog = ScanDialog(self)
        self.scan_dialog = dialog
        dialog.set_playlist_names(
            self.playlist_manager.list_playlist_names(),
            selected_name=self.playlist_manager.get_playlist_name(),
        )
        if self.last_scanned_directory:
            dialog.directory_input.setText(self.last_scanned_directory)
        if getattr(self, "scan_results_cache", None):
            dialog.set_scan_results(self.scan_results_cache)

        dialog.scan_btn.clicked.connect(lambda: self.scan_music_from_dialog(dialog))
        dialog.add_all_btn.clicked.connect(lambda: self.add_scanned_songs_from_dialog(dialog, selected_only=False))
        dialog.add_selected_btn.clicked.connect(lambda: self.add_scanned_songs_from_dialog(dialog, selected_only=True))
        dialog.save_playlist_btn.clicked.connect(lambda: self.create_playlist_from_dialog(dialog))
        dialog.exec_()

    def scan_music_from_dialog(self, dialog):
        self._get_scan_controller().start_scan_from_dialog(dialog)

    def cancel_scan_from_dialog(self, dialog):
        self._get_scan_controller().cancel_scan_from_dialog(dialog)

    def on_dialog_scan_progress(self, dialog, scanned_count, total_count):
        self._get_scan_controller().on_dialog_scan_progress(dialog, scanned_count, total_count)

    def on_dialog_scan_finished(self, dialog, success, cancelled=False, error_message=""):
        self._get_scan_controller().on_dialog_scan_finished(dialog, success, cancelled, error_message)

    def create_playlist_from_dialog(self, dialog):
        songs = list(dialog.scanned_songs or [])
        if not songs:
            QMessageBox.information(self, "提示", "请先扫描音乐")
            return

        directory = (dialog.directory_input.text() or self.last_scanned_directory).strip()
        target_name = dialog.suggested_playlist_name() or self.playlist_manager.get_default_playlist_name(directory)

        overwrite = False
        if self.playlist_manager.has_playlist(target_name):
            answer = QMessageBox.question(
                self,
                "歌单已存在",
                f"歌单“{target_name}”已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
            overwrite = True

        success = self.playlist_manager.create_playlist(
            target_name,
            songs=songs,
            set_current=True,
            overwrite=overwrite,
        )
        if not success:
            QMessageBox.warning(self, "错误", "保存为歌单失败")
            return

        self.current_track_index = 0
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=target_name)
        self.render_playlist()
        self.save_playlists()

        dialog.set_playlist_names(
            self.playlist_manager.list_playlist_names(),
            selected_name=target_name,
        )
        dialog.hint_label.setText(f"已保存歌单：{target_name}（{len(songs)} 首）")

    def add_scanned_songs_from_dialog(self, dialog, selected_only=False):
        target_name = dialog.selected_playlist_name()
        if not target_name:
            QMessageBox.warning(self, "错误", "请选择目标歌单")
            return

        songs = dialog.selected_songs() if selected_only else list(dialog.scanned_songs)
        if not songs:
            QMessageBox.information(self, "提示", "没有可加入的歌曲")
            return

        added, skipped = self.add_songs_to_named_playlist(target_name, songs)
        if added <= 0:
            QMessageBox.information(self, "提示", f"未新增歌曲，已跳过 {skipped} 首重复歌曲")
            return

        self.playlist_manager.select_playlist(target_name)
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=target_name)
        self.render_playlist()
        self.save_playlists()
        dialog.hint_label.setText(f"已加入 {added} 首，跳过 {skipped} 首")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if directory:
            self.directory_input.setText(directory)

    def scan_music(self):
        directory = self.directory_input.text()
        if not directory:
            directory = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
            if directory:
                self.directory_input.setText(directory)

        if not directory or not os.path.exists(directory):
            QMessageBox.warning(self, "错误", "请选择有效的音乐文件夹")
            return

        self.last_scanned_directory = directory

        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        self.scan_worker = ScanWorker(self.music_library, directory)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.start()

    def on_scan_finished(self, success, cancelled=False, error_message=""):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("扫描音乐")
        if self.scan_worker:
            self.scan_worker.deleteLater()
            self.scan_worker = None
        if cancelled:
            return
        if success:
            # 扫描后自动做一轮文本修复，避免历史乱码标签直接进入 UI
            self.repair_imported_song_text(show_message=False)
            self.render_song_list(self.music_library.songs)
            self.update_artists_list()
            self.update_albums_list()
            default_name = self.playlist_manager.get_default_playlist_name(self.last_scanned_directory)
            self.playlist_name_input.setText(default_name)
            QMessageBox.information(self, "扫描完成", f"找到 {len(self.music_library.songs)} 首音乐")
        else:
            details = f"\n\n原因：{error_message}" if error_message else ""
            QMessageBox.warning(self, "错误", f"扫描音乐失败{details}")

    def repair_imported_song_text(self, show_message=True):
        if not self.music_library.songs:
            if show_message:
                QMessageBox.information(self, "提示", "当前音乐库为空，请先扫描音乐")
            return 0, 0

        updated_count, normalized_by_id = LibraryOrchestrationService.normalize_library_songs(
            self.music_library.songs,
            self.music_library._normalize_text,
        )

        playlist_updated = LibraryOrchestrationService.sync_playlists_song_metadata(
            self.playlist_manager.playlists,
            normalized_by_id,
        )

        normalized_current_song = LibraryOrchestrationService.sync_current_song_metadata(self.current_song, normalized_by_id)
        if normalized_current_song:
            self.song_title_label.setText(normalized_current_song['title'])
            self.song_artist_label.setText(normalized_current_song['artist'])

        if self.search_input.text().strip():
            self.search_music()
        else:
            self.render_song_list(self.music_library.songs)
        self.update_artists_list()
        self.update_albums_list()
        self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
        self.render_playlist()
        self.save_playlists()

        if show_message:
            QMessageBox.information(
                self,
                "修复完成",
                f"音乐库修复 {updated_count} 首，歌单同步 {playlist_updated} 条。",
            )

        return updated_count, playlist_updated

    def render_song_list(self, songs):
        self.all_songs_list.clear()
        for song in songs:
            item_text = f"{song['title']} - {song['artist']}"
            self.all_songs_list.addItem(item_text)
            self.all_songs_list.item(self.all_songs_list.count() - 1).setData(Qt.UserRole, song)

    def search_music(self):
        query = self.search_input.text()
        results = self.music_library.search(query)
        self.render_song_list(results)

    def update_artists_list(self):
        artists = self.music_library.get_artists()
        self.artists_list.clear()
        for artist, songs in artists.items():
            item_text = f"{artist} ({len(songs)} 首歌曲)"
            self.artists_list.addItem(item_text)
            self.artists_list.item(self.artists_list.count() - 1).setData(Qt.UserRole, artist)

    def update_albums_list(self):
        albums = self.music_library.get_albums()
        self.albums_list.clear()
        for album, songs in albums.items():
            item_text = f"{album} ({len(songs)} 首歌曲)"
            self.albums_list.addItem(item_text)
            self.albums_list.item(self.albums_list.count() - 1).setData(Qt.UserRole, album)

    def show_artist_songs(self, item):
        artist = item.data(Qt.UserRole)
        songs = self.music_library.get_songs_by_artist(artist)
        self.render_song_list(songs)
        self.tab_widget.setCurrentIndex(0)

    def show_album_songs(self, item):
        album = item.data(Qt.UserRole)
        songs = self.music_library.get_songs_by_album(album)
        self.render_song_list(songs)
        self.tab_widget.setCurrentIndex(0)

    def play_song_from_library(self, item):
        song = item.data(Qt.UserRole)
        if getattr(self, "current_song", None) and self.current_song.get("id") == song.get("id"):
            self.restart_current_song()
            return
        self.playlist_manager.add_song(song)
        self.clear_reorder_snapshot()
        playlist = self.playlist_manager.get_playlist()
        index = self._resolve_song_index_by_id_or_path(playlist, song)
        if index >= 0:
            self.current_track_index = index
        # 用户主动双击点播时，清空启动恢复态，确保从头播放目标歌曲。
        self._pending_resume_song_id = ""
        self._pending_resume_position_seconds = 0.0
        self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
        self.render_playlist()
        self.save_playlists()
        self.play_current_song(force_restart=True)

    def play_song_from_playlist(self, item):
        try:
            song = item.data(Qt.UserRole)
        except TypeError:
            song = item.data(0, Qt.UserRole)
        if not song:
            return
        if getattr(self, "current_song", None) and self.current_song.get("id") == song.get("id"):
            self.restart_current_song()
            return
        playlist = self.playlist_manager.get_playlist()
        index = self._resolve_song_index_by_id_or_path(playlist, song)
        if index >= 0:
            self.current_track_index = index
        self._pending_resume_song_id = ""
        self._pending_resume_position_seconds = 0.0
        self.play_current_song(force_restart=True)

