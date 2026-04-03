import importlib

import pytest


def test_windows_main_preserves_explicit_empty_argv():
    module = importlib.import_module("apps.desktop.windows.app")
    calls = {}

    def _fake_runner(player_cls, argv=None):
        calls["player_cls"] = player_cls
        calls["argv"] = argv
        return 17

    result = module.main(argv=[], runner=_fake_runner)

    assert result == 17
    assert calls["player_cls"] is module.MusicPlayer
    assert calls["argv"] == []


def test_create_entry_config_preserves_explicit_empty_namespace(monkeypatch):
    module = importlib.import_module("apps.desktop.windows.app")
    calls = {}

    def _fake_build_entry_config_from_namespace(namespace):
        calls["namespace"] = namespace
        return {"ok": True}

    monkeypatch.setattr(module, "build_entry_config_from_namespace", _fake_build_entry_config_from_namespace)

    result = module.create_entry_config({})

    assert result == {"ok": True}
    assert calls["namespace"] == {}


def test_runtime_windows_symbols_are_resolved_lazily(monkeypatch):
    module = importlib.import_module("apps.desktop.windows.app")
    calls = {"count": 0}

    def _fake_resolve_windows_symbols(current_module_name):
        calls["count"] += 1
        return {
            "build_core_components": lambda *args, **kwargs: None,
            "init_runtime_state": lambda *args, **kwargs: None,
            "PlayerInitOrchestrationService": type(
                "_StubService",
                (),
                {"initialize_player": staticmethod(lambda *args, **kwargs: None)},
            ),
        }

    monkeypatch.setattr(module.entry_bootstrap, "resolve_windows_symbols", _fake_resolve_windows_symbols)
    module._get_runtime_windows_symbols.cache_clear()
    try:
        symbols_first = module._get_runtime_windows_symbols()
        symbols_second = module._get_runtime_windows_symbols()

        assert symbols_first is symbols_second
        assert calls["count"] == 1
    finally:
        module._get_runtime_windows_symbols.cache_clear()


def test_require_windows_symbol_raises_when_missing():
    module = importlib.import_module("apps.desktop.windows.app")

    with pytest.raises(RuntimeError) as exc_info:
        module._require_windows_symbol({}, "build_core_components")

    assert "build_core_components" in str(exc_info.value)


def test_runtime_windows_symbols_retry_after_previous_failure(monkeypatch):
    module = importlib.import_module("apps.desktop.windows.app")
    calls = {"count": 0}

    def _fake_resolve_windows_symbols(current_module_name):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ImportError("temporary")
        return {
            "build_core_components": lambda *args, **kwargs: None,
            "init_runtime_state": lambda *args, **kwargs: None,
            "PlayerInitOrchestrationService": type(
                "_StubService",
                (),
                {"initialize_player": staticmethod(lambda *args, **kwargs: None)},
            ),
        }

    monkeypatch.setattr(module.entry_bootstrap, "resolve_windows_symbols", _fake_resolve_windows_symbols)
    module._get_runtime_windows_symbols.cache_clear()
    try:
        with pytest.raises(ImportError):
            module._get_runtime_windows_symbols()

        recovered = module._get_runtime_windows_symbols()

        assert isinstance(recovered, dict)
        assert calls["count"] == 2
    finally:
        module._get_runtime_windows_symbols.cache_clear()




