import sys
from importlib import import_module
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = TESTS_DIR.parent
PROJECT_ROOT = FRONTEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    TrayMixin = import_module("frontend.apps.desktop.windows.modules.tray_mixin").TrayMixin
except ModuleNotFoundError:
    TrayMixin = import_module("apps.desktop.windows.modules.tray_mixin").TrayMixin


class _DummyTray(TrayMixin):
    def __init__(self):
        self.tray_enabled = True
        self.close_to_tray_enabled = False
        self.close_behavior_configured = False
        self._quit_requested = False
        self.saved_calls = 0
        self._tray_supported = True

    def _is_tray_supported(self):
        return bool(self._tray_supported)

    def schedule_save_app_settings(self):
        self.saved_calls += 1


def test_first_close_can_choose_hide_and_remember(monkeypatch):
    player = _DummyTray()
    monkeypatch.setattr(player, "_prompt_first_close_action", lambda: (True, True))

    assert player.should_hide_to_tray_on_close() is True
    assert player.close_to_tray_enabled is True
    assert player.close_behavior_configured is True
    assert player.saved_calls == 1


def test_first_close_can_choose_quit_and_remember(monkeypatch):
    player = _DummyTray()
    monkeypatch.setattr(player, "_prompt_first_close_action", lambda: (False, True))

    assert player.should_hide_to_tray_on_close() is False
    assert player.close_to_tray_enabled is False
    assert player.close_behavior_configured is True
    assert player.saved_calls == 1


def test_first_close_without_remember_keeps_unconfigured(monkeypatch):
    player = _DummyTray()
    monkeypatch.setattr(player, "_prompt_first_close_action", lambda: (True, False))

    assert player.should_hide_to_tray_on_close() is True
    assert player.close_to_tray_enabled is True
    assert player.close_behavior_configured is False
    assert player.saved_calls == 0


def test_first_close_cancel_like_path_does_not_persist(monkeypatch):
    player = _DummyTray()
    monkeypatch.setattr(player, "_prompt_first_close_action", lambda: (False, False))

    assert player.should_hide_to_tray_on_close() is False
    assert player.close_to_tray_enabled is False
    assert player.close_behavior_configured is False
    assert player.saved_calls == 0


def test_configured_close_behavior_skips_prompt(monkeypatch):
    player = _DummyTray()
    player.close_behavior_configured = True
    player.close_to_tray_enabled = True

    def _should_not_be_called():
        raise AssertionError("prompt should not be called")

    monkeypatch.setattr(player, "_prompt_first_close_action", _should_not_be_called)
    assert player.should_hide_to_tray_on_close() is True


def test_first_close_with_tray_disabled_sets_close_mode_and_persists():
    player = _DummyTray()
    player.tray_enabled = False

    assert player.should_hide_to_tray_on_close() is False
    assert player.close_to_tray_enabled is False
    assert player.close_behavior_configured is True
    assert player.saved_calls == 1


def test_quit_requested_always_disables_hide_on_close():
    player = _DummyTray()
    player._quit_requested = True

    assert player.should_hide_to_tray_on_close() is False



