import os
import sys
from collections.abc import Mapping
from typing import Any

try:
    from frontend.utils.import_compat import load_attr
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.import_compat import load_attr
    from utils.logging_utils import get_logger


logger = get_logger(__name__)


def ensure_project_root_on_sys_path() -> str:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.debug("已将项目根目录加入 sys.path: %s", project_root)
    return project_root


ENTRY_NAMESPACE_KEYS = (
    "WINDOWS_APP_DIR",
    "FRONTEND_DIR",
    "PROJECT_ROOT",
    "PLAYLISTS_FILE",
    "SETTINGS_FILE",
    "ASR_DEVICE",
    "ASR_COMPUTE_TYPE",
    "ASR_MODEL_SIZE",
    "ASR_BEAM_SIZE",
    "ASR_VAD_FILTER",
    "AUDIO_EXCLUSIVE_MODE",
)


def windows_module_candidates(module_suffix: str, current_module_name: str) -> list[str]:
    # 参数保留仅为兼容旧调用；统一使用 frontend.* 命名空间。
    _ = current_module_name
    return [f"frontend.apps.desktop.windows.{module_suffix}"]


def load_windows_attr(module_suffix: str, attr_name: str, current_module_name: str):
    return load_attr(windows_module_candidates(module_suffix, current_module_name), attr_name)


def resolve_runner(current_module_name: str):
    return load_windows_attr("modules.bootstrap_runner", "run_windows_player_app", current_module_name)


def export_entry_namespace(namespace: Mapping[str, Any], module_globals: dict) -> str:
    module_globals.update({key: namespace[key] for key in ENTRY_NAMESPACE_KEYS})
    logger.debug("已导出入口命名空间，键数量=%d", len(ENTRY_NAMESPACE_KEYS))
    return namespace["PROJECT_ROOT"]


def resolve_windows_symbols(current_module_name: str) -> Mapping[str, Any]:
    ensure_project_root_on_sys_path()
    symbol_specs = (
        ("build_core_components", "modules.app_setup", "build_core_components"),
        ("init_runtime_state", "modules.app_setup", "init_runtime_state"),
        ("PlayerInitOrchestrationService", "modules.player_init_orchestration_service", "PlayerInitOrchestrationService"),
    )
    resolved = {}
    for symbol_name, module_suffix, attr_name in symbol_specs:
        try:
            resolved[symbol_name] = load_windows_attr(module_suffix, attr_name, current_module_name)
        except Exception as exc:
            raise ImportError(
                f"解析 Windows 入口符号失败: symbol={symbol_name}, module={module_suffix}, attr={attr_name}"
            ) from exc
    logger.debug("Windows 入口符号解析完成，数量=%d", len(resolved))
    return resolved




