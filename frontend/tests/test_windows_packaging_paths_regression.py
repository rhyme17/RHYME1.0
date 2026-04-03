from pathlib import Path

from apps.desktop.windows import app_config


def test_build_default_namespace_uses_entry_dir_when_not_frozen(monkeypatch, tmp_path):
    monkeypatch.delenv("RHYME_USER_DATA_DIR", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delattr(app_config.sys, "frozen", raising=False)

    entry_file = tmp_path / "apps" / "desktop" / "windows" / "app.py"
    entry_file.parent.mkdir(parents=True, exist_ok=True)
    entry_file.write_text("# test\n", encoding="utf-8")

    namespace = app_config.build_default_namespace(str(entry_file))

    expected_dir = str(entry_file.parent.resolve())
    assert namespace["WINDOWS_APP_DIR"] == expected_dir
    assert namespace["PLAYLISTS_FILE"] == str(Path(expected_dir) / "playlists.json")
    assert namespace["SETTINGS_FILE"] == str(Path(expected_dir) / "settings.json")


def test_build_default_namespace_uses_localappdata_when_frozen(monkeypatch, tmp_path):
    monkeypatch.delenv("RHYME_USER_DATA_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    monkeypatch.setattr(app_config.sys, "frozen", True, raising=False)

    entry_file = tmp_path / "apps" / "desktop" / "windows" / "app.py"
    entry_file.parent.mkdir(parents=True, exist_ok=True)
    entry_file.write_text("# test\n", encoding="utf-8")

    namespace = app_config.build_default_namespace(str(entry_file))

    expected_dir = str((tmp_path / "LocalAppData" / "RHYME").resolve())
    assert namespace["WINDOWS_APP_DIR"] == expected_dir
    assert Path(namespace["WINDOWS_APP_DIR"]).is_dir()


def test_build_default_namespace_prefers_user_override(monkeypatch, tmp_path):
    override_dir = tmp_path / "PortableData"
    monkeypatch.setenv("RHYME_USER_DATA_DIR", str(override_dir))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    monkeypatch.setattr(app_config.sys, "frozen", True, raising=False)

    entry_file = tmp_path / "apps" / "desktop" / "windows" / "app.py"
    entry_file.parent.mkdir(parents=True, exist_ok=True)
    entry_file.write_text("# test\n", encoding="utf-8")

    namespace = app_config.build_default_namespace(str(entry_file))

    assert namespace["WINDOWS_APP_DIR"] == str(override_dir.resolve())
    assert Path(namespace["WINDOWS_APP_DIR"]).is_dir()

