import sys

from PyQt5.QtWidgets import QApplication

from apps.desktop.windows.modules import settings_dialog as sd
from apps.desktop.windows.modules.settings_dialog import SettingsDialog


app = QApplication.instance() or QApplication(sys.argv)


def test_settings_dialog_exposes_lyrics_output_dir_and_browse_path(monkeypatch):
    captured = {"start_dir": None}

    def _fake_get_existing_directory(_parent, _title, start_dir=""):
        captured["start_dir"] = start_dir
        return "D:/Lyrics/Custom"

    monkeypatch.setattr(sd.QFileDialog, "getExistingDirectory", _fake_get_existing_directory)

    dialog = SettingsDialog({"lyrics_output_dir": "D:/Lyrics/Old"})
    dialog._choose_lyrics_output_dir()

    assert captured["start_dir"] == "D:/Lyrics/Old"
    assert dialog.lyrics_output_dir_input.text() == "D:/Lyrics/Custom"
    values = dialog.values()
    assert values["lyrics_output_dir"] == "D:/Lyrics/Custom"


def test_settings_dialog_allows_clearing_custom_lyrics_output_dir():
    dialog = SettingsDialog({"lyrics_output_dir": "D:/Lyrics/Old"})
    dialog.lyrics_output_dir_input.setText("")

    assert dialog.values()["lyrics_output_dir"] == ""

