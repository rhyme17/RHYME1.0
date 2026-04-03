import importlib
import os
import sys
from functools import lru_cache

APP_INSTANCE = None
try:
    entry_bootstrap = importlib.import_module("frontend.apps.desktop.windows.modules.entry_bootstrap")
except ModuleNotFoundError:
    entry_bootstrap = importlib.import_module("apps.desktop.windows.modules.entry_bootstrap")


def _load_windows_attr(module_suffix, attr_name):
    try:
        return entry_bootstrap.load_windows_attr(module_suffix, attr_name, current_module_name=__name__)
    except Exception as exc:
        raise ImportError(f"加载 Windows 属性失败: module={module_suffix}, attr={attr_name}") from exc


def _normalized_path(path):
    return os.path.normcase(os.path.abspath(str(path or "")))


def _ensure_project_root_on_syspath(project_root):
    normalized_root = _normalized_path(project_root)
    existing = {_normalized_path(item) for item in sys.path}
    if normalized_root not in existing:
        sys.path.insert(0, project_root)


build_default_namespace = _load_windows_attr("app_config", "build_default_namespace")
build_entry_config_from_namespace = _load_windows_attr("app_config", "build_entry_config_from_namespace")

def _bootstrap_entry_namespace(module_globals):
    namespace = build_default_namespace(__file__)
    project_root = entry_bootstrap.export_entry_namespace(namespace, module_globals)
    _ensure_project_root_on_syspath(project_root)
    return project_root


PROJECT_ROOT = _bootstrap_entry_namespace(globals())


def _require_windows_symbol(symbols, name):
    value = symbols.get(name)
    if value is None:
        raise RuntimeError(f"缺少 Windows 入口符号: {name}")
    return value


@lru_cache(maxsize=1)
def _get_runtime_windows_symbols():
    return entry_bootstrap.resolve_windows_symbols(__name__)

def create_entry_config(namespace=None):
    return build_entry_config_from_namespace(globals() if namespace is None else namespace)


@lru_cache(maxsize=1)
def _build_music_player_class():
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMainWindow

    LibraryMixin = _load_windows_attr("modules.library_mixin", "LibraryMixin")
    LifecycleMixin = _load_windows_attr("modules.lifecycle_mixin", "LifecycleMixin")
    LyricsMixin = _load_windows_attr("modules.lyrics_mixin", "LyricsMixin")
    PersistenceMixin = _load_windows_attr("modules.persistence_mixin", "PersistenceMixin")
    PlaybackMixin = _load_windows_attr("modules.playback_mixin", "PlaybackMixin")
    PlaylistMixin = _load_windows_attr("modules.playlist_mixin", "PlaylistMixin")
    SettingsMixin = _load_windows_attr("modules.settings_mixin", "SettingsMixin")
    ShortcutMixin = _load_windows_attr("modules.shortcut_mixin", "ShortcutMixin")
    TrayMixin = _load_windows_attr("modules.tray_mixin", "TrayMixin")
    UiMixin = _load_windows_attr("modules.ui_mixin", "UiMixin")

    class MusicPlayer(
        ShortcutMixin,
        PlaybackMixin,
        LibraryMixin,
        PlaylistMixin,
        SettingsMixin,
        LyricsMixin,
        PersistenceMixin,
        TrayMixin,
        LifecycleMixin,
        UiMixin,
        QMainWindow,
    ):
        def __init__(self):
            super().__init__()
            global APP_INSTANCE
            APP_INSTANCE = QApplication.instance()
            runtime_symbols = _get_runtime_windows_symbols()
            window_context_help_flag = getattr(Qt, "WindowContextHelpButtonHint", 0)
            _require_windows_symbol(runtime_symbols, "PlayerInitOrchestrationService").initialize_player(
                self,
                create_entry_config=create_entry_config,
                namespace=globals(),
                window_context_help_flag=window_context_help_flag,
                build_core_components=_require_windows_symbol(runtime_symbols, "build_core_components"),
                init_runtime_state=_require_windows_symbol(runtime_symbols, "init_runtime_state"),
            )

    return MusicPlayer


def __getattr__(name):
    if name == "MusicPlayer":
        return _build_music_player_class()
    raise AttributeError(name)


def main(argv=None, runner=None):
    if runner is None:
        runner = entry_bootstrap.resolve_runner(__name__)
    effective_argv = sys.argv if argv is None else argv
    return runner(_build_music_player_class(), argv=effective_argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
