from apps.desktop.windows.modules.library_orchestration_service import LibraryOrchestrationService


def _normalize_text(value, fallback):
    text = str(value or "").strip()
    return text if text else fallback


def test_normalize_library_songs_returns_mapping_and_count():
    songs = [
        {"id": "1", "title": "", "artist": "A", "album": ""},
        {"id": "2", "title": "T", "artist": "", "album": "AL"},
    ]

    updated_count, normalized_by_id = LibraryOrchestrationService.normalize_library_songs(songs, _normalize_text)

    assert updated_count == 2
    assert normalized_by_id["1"]["title"] == "未知歌曲"
    assert normalized_by_id["2"]["artist"] == "未知艺术家"


def test_sync_playlists_song_metadata_updates_only_matched_items():
    playlists = {
        "P1": [
            {"id": "1", "title": "old", "artist": "old", "album": "old"},
            {"id": "x", "title": "keep", "artist": "keep", "album": "keep"},
        ]
    }
    normalized_by_id = {
        "1": {"title": "new", "artist": "new", "album": "new"},
    }

    updated = LibraryOrchestrationService.sync_playlists_song_metadata(playlists, normalized_by_id)

    assert updated == 1
    assert playlists["P1"][0]["title"] == "new"
    assert playlists["P1"][1]["title"] == "keep"


def test_sync_current_song_metadata_returns_normalized_snapshot():
    current_song = {"id": "1", "title": "x", "artist": "y"}
    normalized_by_id = {"1": {"title": "A", "artist": "B", "album": "C"}}

    normalized = LibraryOrchestrationService.sync_current_song_metadata(current_song, normalized_by_id)

    assert normalized is not None
    assert current_song["title"] == "A"
    assert current_song["artist"] == "B"

