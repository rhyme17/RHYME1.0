from apps.desktop.windows.modules.player_init_orchestration_service import PlayerInitOrchestrationService


class _DummyPlayer:
    def __init__(self):
        self.calls = []
        self.entry_config = None

    def setWindowTitle(self, title):
        self.calls.append(("setWindowTitle", title))

    def setWindowFlag(self, flag, enabled):
        self.calls.append(("setWindowFlag", flag, enabled))

    def setGeometry(self, x, y, w, h):
        self.calls.append(("setGeometry", x, y, w, h))

    def load_app_settings(self):
        self.calls.append(("load_app_settings",))

    def init_lyrics_state(self):
        self.calls.append(("init_lyrics_state",))

    def init_ui(self):
        self.calls.append(("init_ui",))

    def restore_last_played_song(self):
        self.calls.append(("restore_last_played_song",))


def test_initialize_player_applies_expected_order_and_dependencies():
    player = _DummyPlayer()
    call_order = []

    def _create_entry_config(ns):
        assert ns["MARKER"] == "ok"
        call_order.append("create_entry_config")
        return {"config": 1}

    def _build_core_components(target, entry_config):
        call_order.append("build_core_components")
        assert target is player
        assert entry_config == {"config": 1}

    def _init_runtime_state(target):
        call_order.append("init_runtime_state")
        assert target is player

    PlayerInitOrchestrationService.initialize_player(
        player,
        create_entry_config=_create_entry_config,
        namespace={"MARKER": "ok"},
        window_context_help_flag=123,
        build_core_components=_build_core_components,
        init_runtime_state=_init_runtime_state,
    )

    assert player.entry_config == {"config": 1}
    assert call_order == [
        "create_entry_config",
        "build_core_components",
        "init_runtime_state",
    ]
    assert player.calls == [
        ("setWindowTitle", "本地音乐播放器"),
        ("setWindowFlag", 123, False),
        ("setGeometry", 100, 100, 1000, 700),
        ("load_app_settings",),
        ("init_lyrics_state",),
        ("init_ui",),
        ("restore_last_played_song",),
    ]

