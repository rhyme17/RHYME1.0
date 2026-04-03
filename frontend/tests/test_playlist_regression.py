import json
from pathlib import Path

from core import playlist as playlist_module
from core.playlist import PlaylistManager


def build_song(song_id: str, title: str) -> dict:
    return {
        "id": song_id,
        "title": title,
        "artist": "artist",
        "album": "album",
        "path": f"C:/music/{title}.mp3",
        "duration": 10,
    }


def test_create_playlist_from_folder_uses_folder_name_by_default(tmp_path: Path):
    album_dir = tmp_path / "MyAlbum"
    album_dir.mkdir()

    songs = [build_song("s1", "one"), build_song("s2", "two")]
    manager = PlaylistManager()

    assert manager.create_playlist_from_folder(str(album_dir), songs) is True

    assert manager.has_playlist("MyAlbum") is True
    assert manager.get_playlist_name() == "MyAlbum"
    assert manager.get_playlist_length() == 2


def test_current_playlist_add_remove_and_delete_flow():
    manager = PlaylistManager()
    song_a = build_song("a", "A")
    song_b = build_song("b", "B")

    assert manager.create_playlist("RoadTrip", [song_a], set_current=True) is True
    assert manager.add_song(song_a) is False
    assert manager.add_song(song_b) is True
    assert manager.get_playlist_length() == 2

    assert manager.remove_song("a") is True
    assert manager.get_playlist_length() == 1

    assert manager.delete_playlist("RoadTrip") is True
    assert manager.has_playlist("默认播放列表") is True
    assert manager.get_playlist_name() == "默认播放列表"


def test_load_legacy_single_playlist_format(tmp_path: Path):
    legacy_file = tmp_path / "legacy_playlist.json"
    legacy_data = {
        "name": "OldList",
        "songs": [build_song("x1", "legacy")],
    }
    legacy_file.write_text(json.dumps(legacy_data), encoding="utf-8")

    manager = PlaylistManager()
    assert manager.load(str(legacy_file)) is True

    assert manager.get_playlist_name() == "OldList"
    assert manager.get_playlist_length() == 1


def test_rename_playlist_updates_current_name():
    manager = PlaylistManager()
    song = build_song("a1", "SongA")

    assert manager.create_playlist("OldName", [song], set_current=True) is True
    assert manager.rename_playlist("OldName", "NewName") is True

    assert manager.has_playlist("OldName") is False
    assert manager.has_playlist("NewName") is True
    assert manager.get_playlist_name() == "NewName"
    assert manager.get_playlist_length() == 1


def test_save_and_load_multi_playlist_keeps_current_selection(tmp_path: Path):
    data_file = tmp_path / "playlists.json"
    manager = PlaylistManager()

    assert manager.create_playlist("ListA", [build_song("a", "A")], set_current=False) is True
    assert manager.create_playlist("ListB", [build_song("b", "B")], set_current=True) is True
    assert manager.save(str(data_file)) is True

    reloaded = PlaylistManager()
    assert reloaded.load(str(data_file)) is True

    assert reloaded.has_playlist("ListA") is True
    assert reloaded.has_playlist("ListB") is True
    assert reloaded.get_playlist_name() == "ListB"
    assert reloaded.get_playlist_length() == 1


def test_save_keeps_previous_file_when_atomic_replace_fails(monkeypatch, tmp_path: Path):
    data_file = tmp_path / "playlists.json"
    data_file.write_text(
        json.dumps({"version": 2, "current_playlist": "Old", "playlists": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    manager = PlaylistManager()
    assert manager.create_playlist("RoadTrip", [build_song("a", "A")], set_current=True) is True

    def _broken_replace(_src, _dst):
        raise OSError("replace failed")

    monkeypatch.setattr(playlist_module.os, "replace", _broken_replace)

    assert manager.save(str(data_file)) is False

    raw = json.loads(data_file.read_text(encoding="utf-8"))
    assert raw.get("current_playlist") == "Old"

    leftovers = list(tmp_path.glob("playlists.json.*.tmp"))
    assert leftovers == []


def test_load_corrupted_json_falls_back_to_default_playlist(tmp_path: Path):
    broken_file = tmp_path / "broken_playlists.json"
    broken_content = "{bad-json"
    broken_file.write_text(broken_content, encoding="utf-8")

    manager = PlaylistManager()
    assert manager.create_playlist("Temp", [build_song("t", "T")], set_current=True) is True

    assert manager.load(str(broken_file)) is False
    assert manager.get_playlist_name() == "默认播放列表"
    assert manager.get_playlist_length() == 0

    backups = list(tmp_path.glob("broken_playlists.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == broken_content


def test_load_invalid_root_structure_falls_back_to_default_playlist(tmp_path: Path):
    invalid_file = tmp_path / "invalid_playlists.json"
    invalid_content = json.dumps([{"name": "x"}], ensure_ascii=False)
    invalid_file.write_text(invalid_content, encoding="utf-8")

    manager = PlaylistManager()
    assert manager.load(str(invalid_file)) is False
    assert manager.get_playlist_name() == "默认播放列表"
    assert manager.get_playlist_length() == 0

    backups = list(tmp_path.glob("invalid_playlists.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == invalid_content


def test_corrupted_backup_keeps_recent_limit_of_ten(tmp_path: Path):
    broken_file = tmp_path / "many_backups.json"
    broken_content = "{bad-json"
    broken_file.write_text(broken_content, encoding="utf-8")

    old_backups = []
    for i in range(11):
        backup = tmp_path / f"many_backups.json.corrupt-20240101-0000{i:02d}-000.bak"
        backup.write_text(f"old-{i}", encoding="utf-8")
        # 按顺序设置mtime，i越小越旧。
        mtime = 1000 + i
        playlist_module.os.utime(str(backup), (mtime, mtime))
        old_backups.append(backup)

    manager = PlaylistManager()
    assert manager.load(str(broken_file)) is False

    backups = sorted(tmp_path.glob("many_backups.json.corrupt-*.bak"))
    assert len(backups) == 10
    assert any(path.read_text(encoding="utf-8") == broken_content for path in backups)
    # 原本最旧的两份应被裁剪掉（11旧备份 + 1新备份 -> 保留10份）。
    assert old_backups[0].exists() is False
    assert old_backups[1].exists() is False


def test_load_playlist_skips_malformed_song_items(tmp_path: Path):
    data_file = tmp_path / "playlists_malformed_songs.json"
    payload = {
        "version": 2,
        "current_playlist": "RoadTrip",
        "playlists": [
            {
                "name": "RoadTrip",
                "songs": [
                    build_song("s1", "good"),
                    "broken-item",
                    None,
                    {"title": "missing-id"},
                ],
            }
        ],
    }
    data_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    manager = PlaylistManager()
    assert manager.load(str(data_file)) is True
    assert manager.get_playlist_name() == "RoadTrip"
    assert manager.get_playlist_length() == 1
    assert manager.get_playlist()[0]["id"] == "s1"


def test_sanitize_song_title_uses_filename_instead_of_tag_title():
    manager = PlaylistManager()
    song = {
        "id": "s1",
        "title": "kuwo",
        "artist": "artist",
        "album": "album",
        "path": "C:/music/Slow Down.mp3",
        "duration": 10,
    }

    assert manager.create_playlist("RoadTrip", [song], set_current=True, overwrite=True) is True
    saved = manager.get_playlist()[0]
    assert saved["title"] == "Slow Down"


def test_load_playlist_normalizes_title_from_path(tmp_path: Path):
    data_file = tmp_path / "playlists_title_fix.json"
    payload = {
        "version": 2,
        "current_playlist": "RoadTrip",
        "playlists": [
            {
                "name": "RoadTrip",
                "songs": [
                    {
                        "id": "s1",
                        "title": "kuwo",
                        "artist": "artist",
                        "album": "album",
                        "path": "C:/music/Slow Down.mp3",
                        "duration": 10,
                    }
                ],
            }
        ],
    }
    data_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    manager = PlaylistManager()
    assert manager.load(str(data_file)) is True
    assert manager.get_playlist()[0]["title"] == "Slow Down"


def test_sanitize_song_title_strips_artist_prefix_or_suffix_from_filename():
    manager = PlaylistManager()
    song_a = {
        "id": "s1",
        "title": "ignored",
        "artist": "Taylor Swift",
        "album": "album",
        "path": "C:/music/Taylor Swift - Love Story.mp3",
        "duration": 10,
    }
    song_b = {
        "id": "s2",
        "title": "ignored",
        "artist": "Kelly Clarkson",
        "album": "album",
        "path": "C:/music/Because of You - Kelly Clarkson.mp3",
        "duration": 10,
    }

    assert manager.create_playlist("RoadTrip", [song_a, song_b], set_current=True, overwrite=True) is True
    playlist = manager.get_playlist()
    assert playlist[0]["title"] == "Love Story"
    assert playlist[1]["title"] == "Because of You"


