import pytest

from apps.desktop.windows.modules import entry_bootstrap


def test_windows_module_candidates_prefers_apps_prefix_when_imported_as_apps():
    values = entry_bootstrap.windows_module_candidates(
        "modules.ui_mixin",
        current_module_name="apps.desktop.windows.app",
    )
    assert values == ["frontend.apps.desktop.windows.modules.ui_mixin"]


def test_windows_module_candidates_prefers_frontend_prefix_when_not_apps():
    values = entry_bootstrap.windows_module_candidates(
        "modules.ui_mixin",
        current_module_name="frontend.apps.desktop.windows.app",
    )
    assert values == ["frontend.apps.desktop.windows.modules.ui_mixin"]


def test_export_entry_namespace_only_exports_declared_keys():
    namespace = {
        "WINDOWS_APP_DIR": "A",
        "FRONTEND_DIR": "B",
        "PROJECT_ROOT": "C",
        "PLAYLISTS_FILE": "D",
        "SETTINGS_FILE": "E",
        "ASR_DEVICE": "cpu",
        "ASR_COMPUTE_TYPE": "float32",
        "ASR_MODEL_SIZE": "small",
        "ASR_BEAM_SIZE": 5,
        "ASR_VAD_FILTER": False,
        "AUDIO_EXCLUSIVE_MODE": False,
        "UNUSED": "ignore",
    }
    target_globals = {}

    project_root = entry_bootstrap.export_entry_namespace(namespace, target_globals)

    assert project_root == "C"
    assert "UNUSED" not in target_globals
    for key in entry_bootstrap.ENTRY_NAMESPACE_KEYS:
        assert target_globals[key] == namespace[key]


def test_resolve_windows_symbols_includes_player_init_orchestration_service():
    symbols = entry_bootstrap.resolve_windows_symbols("apps.desktop.windows.app")
    assert "PlayerInitOrchestrationService" in symbols
    assert set(symbols.keys()) == {
        "build_core_components",
        "init_runtime_state",
        "PlayerInitOrchestrationService",
    }


def test_resolve_windows_symbols_error_contains_symbol_context(monkeypatch):
    def _fake_load_windows_attr(module_suffix, attr_name, current_module_name):
        raise ModuleNotFoundError("missing")

    monkeypatch.setattr(entry_bootstrap, "load_windows_attr", _fake_load_windows_attr)

    with pytest.raises(ImportError) as exc_info:
        entry_bootstrap.resolve_windows_symbols("apps.desktop.windows.app")

    message = str(exc_info.value)
    assert "build_core_components" in message
    assert "modules.app_setup" in message
    assert "build_core_components" in message


