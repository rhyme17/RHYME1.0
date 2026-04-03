import os
from collections import Counter

from PyQt5.QtWidgets import QMessageBox, QTreeWidgetItem, QInputDialog
from PyQt5.QtCore import Qt

from frontend.apps.desktop.windows.modules.song_select_dialog import SongSelectDialog
from frontend.utils.helpers import format_time


class PlaylistMixin:
    @staticmethod
    def _song_identity(song):
        song_id = str(song.get("id", "") or "").strip()
        if song_id:
            return f"id:{song_id}"
        return f"path:{str(song.get('path', '') or '').strip().lower()}"

    @staticmethod
    def _display_song_title(song):
        title = str(song.get('title', '') or '').strip()
        if title:
            return title
        path = str(song.get('path', '') or '').strip()
        if path:
            filename = os.path.splitext(os.path.basename(path))[0].strip()
            if filename:
                return filename
        return ""

    def clear_reorder_snapshot(self):
        self.last_reorder_snapshot = None
        self.undo_reorder_btn.setEnabled(False)

    def _selected_playlist_name(self):
        item = self.playlists_tree.currentItem() if hasattr(self, "playlists_tree") else None
        if not item:
            return ""
        parent = item.parent()
        target = parent if parent is not None else item
        return str(target.data(0, Qt.UserRole) or "")

    @staticmethod
    def _song_from_playlist_item(item):
        if item is None:
            return None
        try:
            song = item.data(Qt.UserRole)
        except TypeError:
            song = item.data(0, Qt.UserRole)
        return song

    def on_playlist_tree_item_clicked(self, item, _column=0):
        target = item.parent() or item
        name = str(target.data(0, Qt.UserRole) or "")
        if not name:
            return
        if self.playlist_manager.select_playlist(name):
            self.current_track_index = 0
            self.clear_reorder_snapshot()
            self.playlist_name_input.setText(name)
            self.render_playlist()

    def on_playlist_tree_item_double_clicked(self, item, _column=0):
        self.play_selected_playlist(target_name=str(item.data(0, Qt.UserRole) or ""))

    def recalculate_current_track_index_by_song_id(self):
        if not self.current_song:
            return
        song_id = self.current_song.get('id')
        playlist = self.playlist_manager.get_playlist()
        for index, song in enumerate(playlist):
            if song.get('id') == song_id:
                self.current_track_index = index
                return

    def on_playlist_rows_moved(self, *_):
        if self.is_rendering_playlist:
            return
        self.sync_playlist_order_from_ui()

    def sync_playlist_order_from_ui(self):
        playlist_name = self.playlist_manager.get_playlist_name()
        old_songs = [dict(song) for song in self.playlist_manager.get_playlist()]
        if not playlist_name or not old_songs:
            return

        ordered_songs = []
        for row in range(self.playlist_list.count()):
            item = self.playlist_list.item(row)
            song = self._song_from_playlist_item(item)
            if song:
                ordered_songs.append(song)

        if len(ordered_songs) != len(old_songs):
            self.render_playlist()
            return

        old_keys = [self._song_identity(song) for song in old_songs]
        new_keys = [self._song_identity(song) for song in ordered_songs]
        if Counter(old_keys) != Counter(new_keys):
            # 拖拽结果异常时回滚，避免持久化出错歌单。
            self.render_playlist()
            return
        if new_keys == old_keys:
            return

        self.playlist_manager.create_playlist(
            playlist_name,
            songs=ordered_songs,
            set_current=True,
            overwrite=True,
        )
        self.last_reorder_snapshot = {
            "playlist_name": playlist_name,
            "songs": old_songs,
        }
        self.undo_reorder_btn.setEnabled(True)
        self.recalculate_current_track_index_by_song_id()
        self.render_playlist_names(select_name=playlist_name)
        self.save_playlists()

    def undo_last_reorder(self):
        if not self.last_reorder_snapshot:
            return

        current_name = self.playlist_manager.get_playlist_name()
        snapshot_name = self.last_reorder_snapshot.get("playlist_name")
        if current_name != snapshot_name:
            QMessageBox.information(self, "提示", "请切换回刚刚排序的歌单后再撤销")
            return

        songs = self.last_reorder_snapshot.get("songs", [])
        self.playlist_manager.create_playlist(
            current_name,
            songs=songs,
            set_current=True,
            overwrite=True,
        )
        self.recalculate_current_track_index_by_song_id()
        self.render_playlist_names(select_name=current_name)
        self.render_playlist()
        self.save_playlists()
        self.clear_reorder_snapshot()

    def add_selected_to_playlist(self):
        current_name = self.playlist_manager.get_playlist_name()
        if not current_name:
            QMessageBox.warning(self, "错误", "请先选择当前歌单")
            return

        source, confirmed = QInputDialog.getItem(
            self,
            "选择来源",
            "添加来源：",
            ["扫描缓存", "其他歌单"],
            0,
            False,
        )
        if not confirmed:
            return

        if source == "扫描缓存":
            source_songs = list(getattr(self, "scan_results_cache", []) or [])
            if not source_songs:
                QMessageBox.information(self, "提示", "扫描缓存为空，请先点击“添加音乐”并扫描")
                return
        else:
            candidate_playlists = [
                name for name in self.playlist_manager.list_playlist_names()
                if name != current_name
            ]
            if not candidate_playlists:
                QMessageBox.information(self, "提示", "暂无其他歌单可供添加")
                return

            source_playlist_name, ok = QInputDialog.getItem(
                self,
                "选择歌单",
                "来源歌单：",
                candidate_playlists,
                0,
                False,
            )
            if not ok:
                return

            source_songs = [dict(song) for song in self.playlist_manager.playlists.get(source_playlist_name, [])]
            if not source_songs:
                QMessageBox.information(self, "提示", "来源歌单为空")
                return

        dialog = SongSelectDialog(self)
        dialog.setWindowTitle("选择要加入当前歌单的歌曲")
        dialog.confirm_btn.setText("加入当前歌单")
        dialog.set_songs(source_songs)
        if dialog.exec_() != dialog.Accepted:
            return

        selected = dialog.selected_songs()
        added = 0
        skipped = 0
        for song in selected:
            if self.playlist_manager.add_song(song):
                added += 1
            else:
                skipped += 1

        self.clear_reorder_snapshot()
        self.render_playlist()
        self.render_playlist_names(select_name=current_name)
        self.save_playlists()
        QMessageBox.information(self, "完成", f"已加入 {added} 首，跳过 {skipped} 首")

    def create_empty_playlist(self):
        default_name = "新建歌单"
        name, confirmed = QInputDialog.getText(self, "新建歌单", "歌单名称：", text=default_name)
        if not confirmed:
            return

        target_name = (name or "").strip() or default_name
        if self.playlist_manager.has_playlist(target_name):
            QMessageBox.warning(self, "错误", f"歌单“{target_name}”已存在")
            return

        if not self.playlist_manager.create_playlist(target_name, songs=[], set_current=True, overwrite=False):
            QMessageBox.warning(self, "错误", "新建歌单失败")
            return

        self.current_track_index = 0
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=target_name)
        self.render_playlist()
        self.save_playlists()

    def add_songs_to_named_playlist(self, playlist_name, songs):
        if not playlist_name or not self.playlist_manager.has_playlist(playlist_name):
            return 0, len(songs or [])
        added = 0
        skipped = 0
        for song in songs or []:
            if self.playlist_manager.add_song_to_playlist(playlist_name, song):
                added += 1
            else:
                skipped += 1
        return added, skipped

    def remove_selected_from_playlist(self):
        current_item = self.playlist_list.currentItem()
        if not current_item:
            return
        song = self._song_from_playlist_item(current_item)
        if not song:
            return
        if self.playlist_manager.remove_song(song['id']):
            self.clear_reorder_snapshot()
            playlist = self.playlist_manager.get_playlist()
            if playlist:
                self.current_track_index = min(self.current_track_index, len(playlist) - 1)
            else:
                self.current_track_index = 0
            self.render_playlist()
            self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
            self.save_playlists()

    def create_playlist_from_scan(self):
        songs = self.music_library.songs
        if not songs:
            QMessageBox.warning(self, "错误", "请先扫描音乐后再创建歌单")
            return

        directory = self.last_scanned_directory or self.directory_input.text().strip()
        target_name = self.playlist_name_input.text().strip() or self.playlist_manager.get_default_playlist_name(directory)

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

        success = self.playlist_manager.create_playlist_from_folder(
            folder_path=directory,
            songs=songs,
            playlist_name=target_name,
            overwrite=overwrite,
            set_current=True,
        )
        if not success:
            QMessageBox.warning(self, "错误", "创建歌单失败")
            return

        self.current_track_index = 0
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=target_name)
        self.render_playlist()
        self.save_playlists()

    def rename_selected_playlist(self):
        old_name = self._selected_playlist_name()
        if not old_name:
            return
        new_name, confirmed = self._get_rename_text(old_name)
        if not confirmed:
            return

        new_name = new_name.strip() or old_name
        if new_name == old_name:
            return

        if self.playlist_manager.has_playlist(new_name):
            QMessageBox.warning(self, "错误", f"歌单“{new_name}”已存在")
            return

        if not self.playlist_manager.rename_playlist(old_name, new_name):
            QMessageBox.warning(self, "错误", "重命名失败")
            return

        self.playlist_name_input.setText(new_name)
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=new_name)
        self.render_playlist()
        self.save_playlists()

    def _get_rename_text(self, old_name):
        from PyQt5.QtWidgets import QInputDialog

        return QInputDialog.getText(self, "重命名歌单", "新的歌单名：", text=old_name)

    def delete_selected_playlist(self):
        name = self._selected_playlist_name()
        if not name:
            return
        answer = QMessageBox.question(
            self,
            "删除歌单",
            f"确定删除歌单“{name}”？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        if self.playlist_manager.delete_playlist(name):
            self.current_track_index = 0
            self.clear_reorder_snapshot()
            self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
            self.render_playlist()
            self.playlist_name_input.setText(self.playlist_manager.get_playlist_name())
            self.save_playlists()

    def on_playlist_selected(self, item):
        # 兼容旧信号入口，转发到树形选择逻辑。
        self.on_playlist_tree_item_clicked(item)

    def play_selected_playlist(self, item=None, target_name=""):
        if target_name:
            target_name = str(target_name)
        elif item is not None:
            if hasattr(item, "parent") and item.parent() is not None:
                item = item.parent()
            target_name = str(item.data(0, Qt.UserRole) or "")
        else:
            target_name = self._selected_playlist_name()
        if not target_name:
            return

        if not self.playlist_manager.select_playlist(target_name):
            return

        playlist = self.playlist_manager.get_playlist()
        self.current_track_index = 0
        self.clear_reorder_snapshot()
        self.render_playlist_names(select_name=target_name)
        self.render_playlist()
        if playlist:
            self.play_current_song()

    def render_playlist_names(self, select_name=None):
        tree = self.playlists_tree
        current_name = select_name or self.playlist_manager.get_playlist_name()
        selected_item = None

        tree.blockSignals(True)
        tree.setUpdatesEnabled(False)
        try:
            tree.clear()
            for name in self.playlist_manager.list_playlist_names():
                songs = self.playlist_manager.playlists.get(name, [])
                song_count = len(songs)
                top_item = QTreeWidgetItem()
                top_item.setText(0, f"{name} ({song_count} 首)")
                top_item.setData(0, Qt.UserRole, name)
                tree.addTopLevelItem(top_item)
                if name == current_name:
                    selected_item = top_item
            if selected_item is not None:
                tree.setCurrentItem(selected_item)
                tree.scrollToItem(selected_item)
        finally:
            tree.setUpdatesEnabled(True)
            tree.blockSignals(False)

    def render_playlist(self):
        playlist_widget = self.playlist_list
        self.is_rendering_playlist = True
        playlist_widget.blockSignals(True)
        playlist_widget.setUpdatesEnabled(False)
        try:
            playlist_widget.clear()
            playlist_name = self.playlist_manager.get_playlist_name() or "默认播放列表"
            self.current_playlist_label.setText(f"当前歌单：{playlist_name}")
            playlist = self.playlist_manager.get_playlist()
            self.playlist_empty_hint.setVisible(len(playlist) == 0)
            updated_duration = False
            for index, song in enumerate(playlist, start=1):
                duration = float(song.get('duration', 0.0) or 0.0)
                if duration <= 0:
                    duration_hint = 0.0
                    try:
                        duration_hint = float(self.audio_player.get_duration_hint(song.get('path', '')) or 0.0)
                    except Exception:
                        duration_hint = 0.0
                    if duration_hint > 0:
                        duration = duration_hint
                        song['duration'] = duration_hint
                        updated_duration = True
                item = QTreeWidgetItem([
                    str(index),
                    self._display_song_title(song),
                    str(song.get('artist', '') or ''),
                    format_time(duration),
                ])
                item.setData(0, Qt.UserRole, song)
                playlist_widget.addTopLevelItem(item)
            if updated_duration:
                self.save_playlists()
        finally:
            playlist_widget.setUpdatesEnabled(True)
            playlist_widget.blockSignals(False)
            self.is_rendering_playlist = False

    def clear_playlist(self):
        self.playlist_manager.clear()
        self.current_track_index = 0
        self.clear_reorder_snapshot()
        self.render_playlist()
        self.render_playlist_names(select_name=self.playlist_manager.get_playlist_name())
        self.save_playlists()

