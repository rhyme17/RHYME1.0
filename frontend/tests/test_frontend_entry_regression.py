import app as frontend_entry


def test_frontend_main_delegates_to_windows_main(monkeypatch):
    calls = {}

    def _fake_windows_main(argv=None):
        calls["argv"] = argv
        return 23

    monkeypatch.setattr(frontend_entry, "_get_windows_main", lambda: _fake_windows_main)

    result = frontend_entry.main(["prog", "--demo"])

    assert result == 23
    assert calls["argv"] == ["prog", "--demo"]


def test_frontend_main_preserves_explicit_empty_argv(monkeypatch):
    calls = {}

    def _fake_windows_main(argv=None):
        calls["argv"] = argv
        return 7

    monkeypatch.setattr(frontend_entry, "_get_windows_main", lambda: _fake_windows_main)

    result = frontend_entry.main([])

    assert result == 7
    assert calls["argv"] == []


