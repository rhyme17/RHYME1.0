import sys

from PyQt5.QtWidgets import QApplication

from apps.desktop.windows.modules import scan_dialog as sd
from apps.desktop.windows.modules.scan_dialog import ScanDialog


app = QApplication.instance() or QApplication(sys.argv)


def test_browse_directory_uses_initial_path_and_updates_callback(monkeypatch):
    captured = {"start_dir": None, "saved": None}

    def _fake_get_existing_directory(_parent, _title, start_dir=""):
        captured["start_dir"] = start_dir
        return "D:/Music/Test"

    monkeypatch.setattr(sd.QFileDialog, "getExistingDirectory", _fake_get_existing_directory)

    dialog = ScanDialog(initial_directory="D:/Music")
    dialog.on_directory_selected = lambda path: captured.__setitem__("saved", path)

    dialog._browse_directory()

    assert captured["start_dir"] == "D:/Music"
    assert dialog.directory_input.text() == "D:/Music/Test"
    assert dialog.initial_directory == "D:/Music/Test"
    assert captured["saved"] == "D:/Music/Test"


def test_browse_directory_prefers_current_input_path(monkeypatch):
    captured = {"start_dir": None}

    def _fake_get_existing_directory(_parent, _title, start_dir=""):
        captured["start_dir"] = start_dir
        return ""

    monkeypatch.setattr(sd.QFileDialog, "getExistingDirectory", _fake_get_existing_directory)

    dialog = ScanDialog(initial_directory="D:/Music")
    dialog.directory_input.setText("D:/Music/Child")

    dialog._browse_directory()

    assert captured["start_dir"] == "D:/Music/Child"

