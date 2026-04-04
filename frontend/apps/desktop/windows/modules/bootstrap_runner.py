import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

try:
    from frontend.utils.logging_utils import configure_basic_logging
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.logging_utils import configure_basic_logging
    from utils.logging_utils import get_logger


logger = get_logger(__name__)


# 统一运行时图标来源，确保源码运行与打包运行都能正确显示任务栏/托盘图标。
def _resolve_runtime_icon_path() -> str:
    env_icon = (os.getenv("RHYME_APP_ICON", "") or "").strip()
    if env_icon and os.path.exists(env_icon):
        return env_icon

    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.extend(
            [
                os.path.join(exe_dir, "app.ico"),
                os.path.join(exe_dir, "_internal", "app.ico"),
            ]
        )
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(os.path.join(meipass, "app.ico"))

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
    candidates.extend(
        [
            os.path.join(project_root, "build", "windows", "app.ico"),
            os.path.join(project_root, "img.png"),
        ]
    )

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return ""


# 设置 AppUserModelID，减少 Windows 任务栏图标偶发不一致问题。
def _set_windows_app_user_model_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RHYME.Desktop.App")
    except Exception as exc:
        logger.debug("设置 AppUserModelID 失败，继续运行: %s", exc)


def run_windows_player_app(player_class, argv=None, app_factory=QApplication):
    configure_basic_logging()
    effective_argv = sys.argv if argv is None else argv
    logger.debug("启动 Windows 播放器入口，argv_len=%d", len(effective_argv))
    existing_app = QApplication.instance()
    app = existing_app if existing_app is not None else app_factory(effective_argv)

    _set_windows_app_user_model_id()
    icon_path = _resolve_runtime_icon_path()
    if icon_path:
        icon = QIcon(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)
        else:
            logger.warning("运行时图标加载失败(空图标): %s", icon_path)
    else:
        logger.warning("未找到运行时图标文件，使用系统默认图标")

    player = player_class()
    if not app.windowIcon().isNull():
        player.setWindowIcon(app.windowIcon())
    player.show()
    exit_code = app.exec_()
    logger.debug("Windows 播放器入口退出，exit_code=%s", exit_code)
    return exit_code

