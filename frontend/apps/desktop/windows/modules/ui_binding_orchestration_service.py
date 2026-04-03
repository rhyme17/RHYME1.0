class UiBindingOrchestrationService:
    @staticmethod
    def _connect_if_present(player, widget_name, signal_name, handler_name):
        widget = getattr(player, widget_name, None)
        handler = getattr(player, handler_name, None)
        if widget is None or handler is None:
            return
        signal = getattr(widget, signal_name, None)
        if signal is None:
            return
        signal.connect(handler)

    @staticmethod
    def bind_all(player):
        if getattr(player, "_ui_bindings_initialized", False):
            return
        UiBindingOrchestrationService.bind_top_actions(player)
        UiBindingOrchestrationService.bind_library_actions(player)
        UiBindingOrchestrationService.bind_playlist_actions(player)
        UiBindingOrchestrationService.bind_lyrics_and_playback_actions(player)
        player._ui_bindings_initialized = True

    @staticmethod
    def bind_top_actions(player):
        UiBindingOrchestrationService._connect_if_present(player, "open_scan_dialog_btn", "clicked", "open_scan_dialog")
        UiBindingOrchestrationService._connect_if_present(player, "create_playlist_btn", "clicked", "create_empty_playlist")
        UiBindingOrchestrationService._connect_if_present(player, "settings_btn", "clicked", "open_settings_dialog")
        UiBindingOrchestrationService._connect_if_present(player, "rename_playlist_btn", "clicked", "rename_selected_playlist")
        UiBindingOrchestrationService._connect_if_present(player, "delete_playlist_btn", "clicked", "delete_selected_playlist")
        UiBindingOrchestrationService._connect_if_present(player, "search_input", "textChanged", "search_music")
        UiBindingOrchestrationService._connect_if_present(player, "scan_btn", "clicked", "scan_music")
        UiBindingOrchestrationService._connect_if_present(player, "browse_btn", "clicked", "browse_directory")

    @staticmethod
    def bind_library_actions(player):
        player.all_songs_list.itemDoubleClicked.connect(player.play_song_from_library)
        player.artists_list.itemClicked.connect(player.show_artist_songs)
        player.albums_list.itemClicked.connect(player.show_album_songs)

    @staticmethod
    def bind_playlist_actions(player):
        player.playlist_tree_toggle_btn.clicked.connect(player.toggle_playlist_tree_visibility)
        player.add_to_playlist_btn.clicked.connect(player.add_selected_to_playlist)
        player.remove_from_playlist_btn.clicked.connect(player.remove_selected_from_playlist)
        player.clear_playlist_btn.clicked.connect(player.clear_playlist)
        player.undo_reorder_btn.clicked.connect(player.undo_last_reorder)
        player.playlists_tree.itemClicked.connect(player.on_playlist_tree_item_clicked)
        player.playlists_tree.itemDoubleClicked.connect(player.on_playlist_tree_item_double_clicked)
        player.playlist_list.itemDoubleClicked.connect(lambda item, _column: player.play_song_from_playlist(item))
        player.playlist_list.model().rowsMoved.connect(player.on_playlist_rows_moved)

    @staticmethod
    def bind_lyrics_and_playback_actions(player):
        player.reload_lyrics_btn.clicked.connect(player.reload_local_lyrics_for_current_song)
        player.lyrics_asr_btn.clicked.connect(player.request_lyrics_asr_for_current_song)
        player.progress_slider.sliderMoved.connect(player.set_position_preview)
        player.progress_slider.sliderReleased.connect(player.apply_slider_position)
        player.prev_btn.clicked.connect(player.play_previous)
        player.play_btn.clicked.connect(player.toggle_play)
        player.next_btn.clicked.connect(player.play_next)
        player.replay_btn.clicked.connect(player.restart_current_song)
        player.mute_btn.clicked.connect(player.toggle_mute)
        player.volume_slider.valueChanged.connect(player.set_volume)
        player.mode_btn.clicked.connect(player.toggle_playback_mode)
        player.high_quality_btn.clicked.connect(player.toggle_high_quality_output)

