class PlayerInitOrchestrationService:
    @staticmethod
    def initialize_player(
        player,
        *,
        create_entry_config,
        namespace,
        window_context_help_flag,
        build_core_components,
        init_runtime_state,
    ):
        # 每次实例化都从模块全局读取，确保测试 monkeypatch 后仍生效。
        player.entry_config = create_entry_config(namespace)
        player.setWindowTitle("本地音乐播放器")
        player.setWindowFlag(window_context_help_flag, False)
        player.setGeometry(100, 100, 1000, 700)

        build_core_components(
            player,
            entry_config=player.entry_config,
        )
        init_runtime_state(player)

        player.load_app_settings()
        player.init_lyrics_state()
        player.init_ui()
        if hasattr(player, "init_system_tray"):
            player.init_system_tray()
        player.restore_last_played_song()

