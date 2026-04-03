import sys

from PyQt5.QtWidgets import QApplication

try:
    from frontend.utils.logging_utils import configure_basic_logging
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.logging_utils import configure_basic_logging
    from utils.logging_utils import get_logger


logger = get_logger(__name__)


def run_windows_player_app(player_class, argv=None, app_factory=QApplication):
    configure_basic_logging()
    effective_argv = sys.argv if argv is None else argv
    logger.debug("启动 Windows 播放器入口，argv_len=%d", len(effective_argv))
    existing_app = QApplication.instance()
    app = existing_app if existing_app is not None else app_factory(effective_argv)
    player = player_class()
    player.show()
    exit_code = app.exec_()
    logger.debug("Windows 播放器入口退出，exit_code=%s", exit_code)
    return exit_code

