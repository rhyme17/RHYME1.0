from apps.desktop.windows.modules import bootstrap_runner


class _FakeApp:
    def __init__(self, argv):
        self.argv = argv

    def exec_(self):
        return 9


class _FakePlayer:
    def __init__(self):
        self.shown = False

    def show(self):
        self.shown = True


def test_run_windows_player_app_preserves_explicit_empty_argv(monkeypatch):
    calls = {}

    def _fake_app_factory(argv):
        app = _FakeApp(argv)
        calls["app"] = app
        return app

    monkeypatch.setattr(bootstrap_runner, "configure_basic_logging", lambda: None)

    result = bootstrap_runner.run_windows_player_app(_FakePlayer, argv=[], app_factory=_fake_app_factory)

    assert result == 9
    assert calls["app"].argv == []


def test_run_windows_player_app_reuses_existing_qapplication(monkeypatch):
    calls = {"factory_called": False}

    class _ExistingApp:
        def exec_(self):
            return 3

    existing_app = _ExistingApp()

    class _FakeQApplication:
        @staticmethod
        def instance():
            return existing_app

    def _fake_app_factory(_argv):
        calls["factory_called"] = True
        return _FakeApp(_argv)

    monkeypatch.setattr(bootstrap_runner, "configure_basic_logging", lambda: None)
    monkeypatch.setattr(bootstrap_runner, "QApplication", _FakeQApplication)

    result = bootstrap_runner.run_windows_player_app(_FakePlayer, argv=["demo"], app_factory=_fake_app_factory)

    assert result == 3
    assert calls["factory_called"] is False


