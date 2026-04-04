from pathlib import Path

from core import library as library_module
from core.library import MusicLibrary


def test_scan_music_is_stable_between_runs(tmp_path: Path):
    album_dir = tmp_path / "album"
    album_dir.mkdir()

    song_a = album_dir / "b_track.wav"
    song_b = album_dir / "a_track.mp3"
    song_a.write_bytes(b"not-a-real-audio")
    song_b.write_bytes(b"not-a-real-audio")

    library = MusicLibrary()

    assert library.scan_music(str(tmp_path)) is True
    first_run = [(s["id"], s["path"]) for s in library.songs]

    assert library.scan_music(str(tmp_path)) is True
    second_run = [(s["id"], s["path"]) for s in library.songs]

    assert first_run == second_run
    assert len(first_run) == 2


def test_normalize_text_repairs_common_utf8_latin1_mojibake():
    library = MusicLibrary()
    garbled = (
        "\u00e6\u00b6\u0088\u00e5\u00a4\u00b1\u00e5\u009c\u00a8"
        "\u00e8\u00ae\u00b0\u00e5\u00bf\u0086\u00e9\u0087\u008c"
        "\u00e7\u009a\u0084\u00e6\u00b5\u00b7"
    )

    assert library._normalize_text(garbled, "unknown") == "消失在记忆里的海"


def test_normalize_text_keeps_valid_text_intact():
    library = MusicLibrary()
    original = "Zeihos - 未知艺术家"

    assert library._normalize_text(original, "unknown") == original


def test_normalize_text_repairs_common_gbk_latin1_mojibake():
    library = MusicLibrary()
    garbled = "ÏûÊ§ÔÚ¼ÇÒäÀïµÄº£"

    assert library._normalize_text(garbled, "unknown") == "消失在记忆里的海"


def test_scan_music_continues_when_walk_reports_inaccessible_directory(monkeypatch, tmp_path: Path):
    music_file = tmp_path / "ok.mp3"
    music_file.write_bytes(b"not-a-real-audio")

    def _fake_walk(_directory, onerror=None):
        yield str(tmp_path), ["blocked"], [music_file.name]
        if onerror is not None:
            onerror(PermissionError("blocked directory"))

    monkeypatch.setattr(library_module.os, "walk", _fake_walk)

    library = MusicLibrary()
    assert library.scan_music(str(tmp_path)) is True
    assert len(library.songs) == 1
    assert library.songs[0]["path"].lower().endswith("ok.mp3")


def test_scan_music_can_be_cancelled(monkeypatch, tmp_path: Path):
    music_file = tmp_path / "ok.mp3"
    music_file.write_bytes(b"not-a-real-audio")

    def _fake_walk(_directory, onerror=None):
        yield str(tmp_path), [], [music_file.name]

    monkeypatch.setattr(library_module.os, "walk", _fake_walk)

    library = MusicLibrary()
    should_stop = {"value": True}
    result = library.scan_music(str(tmp_path), should_stop=lambda: should_stop["value"])

    assert result is False
    assert library.last_scan_cancelled is True
    assert library.songs == []


def test_scan_music_reports_progress(monkeypatch, tmp_path: Path):
    album_dir = tmp_path / "album"
    album_dir.mkdir()
    (album_dir / "a.mp3").write_bytes(b"not-a-real-audio")
    (album_dir / "b.wav").write_bytes(b"not-a-real-audio")

    events = []
    library = MusicLibrary()
    ok = library.scan_music(str(tmp_path), on_progress=lambda scanned, total: events.append((scanned, total)))

    assert ok is True
    assert len(events) >= 2
    assert events[-1][0] == 2
    assert events[-1][1] >= 2


def test_extract_song_info_falls_back_to_full_mutagen_for_duration(monkeypatch, tmp_path: Path):
    song_file = tmp_path / "demo.mp3"
    song_file.write_bytes(b"fake")

    class _FakeEasyAudio:
        info = None

        @staticmethod
        def get(_key, default):
            return default

    class _FakeFullInfo:
        length = 125.4

    class _FakeFullAudio:
        info = _FakeFullInfo()

    def _fake_file(_file_path, easy=False):
        return _FakeEasyAudio() if easy else _FakeFullAudio()

    monkeypatch.setattr(library_module, "File", _fake_file)

    library = MusicLibrary()
    song = library._extract_song_info(str(song_file))

    assert song["duration"] == 125.4


def test_extract_song_info_prefers_filename_when_title_is_mojibake(monkeypatch, tmp_path: Path):
    song_file = tmp_path / "周杰伦-夜曲.mp3"
    song_file.write_bytes(b"fake")

    class _FakeInfo:
        length = 10.0

    class _FakeAudio:
        info = _FakeInfo()

        @staticmethod
        def get(key, default):
            if key == "title":
                return ["ÃÃÃÃ"]
            if key == "artist":
                return ["ÃÃ"]
            if key == "album":
                return ["Ã"]
            return default

    monkeypatch.setattr(library_module, "File", lambda *_args, **_kwargs: _FakeAudio())

    library = MusicLibrary()
    song = library._extract_song_info(str(song_file))

    assert song["title"] == "周杰伦-夜曲"


def test_extract_song_info_uses_filename_as_title_even_when_tag_title_exists(monkeypatch, tmp_path: Path):
    song_file = tmp_path / "Slow Down.mp3"
    song_file.write_bytes(b"fake")

    class _FakeInfo:
        length = 245.0

    class _FakeAudio:
        info = _FakeInfo()

        @staticmethod
        def get(key, default):
            if key == "title":
                return ["kuwo"]
            if key == "artist":
                return ["kuwo-artist"]
            if key == "album":
                return ["kuwo-album"]
            return default

    monkeypatch.setattr(library_module, "File", lambda *_args, **_kwargs: _FakeAudio())

    library = MusicLibrary()
    song = library._extract_song_info(str(song_file))

    assert song["title"] == "Slow Down"
    assert song["artist"] == "kuwo-artist"
    assert song["album"] == "kuwo-album"
    assert song["duration"] == 245.0


def test_extract_song_info_strips_track_number_prefix_from_filename(monkeypatch, tmp_path: Path):
    song_file = tmp_path / "01. Slow Down.mp3"
    song_file.write_bytes(b"fake")

    class _FakeInfo:
        length = 120.0

    class _FakeAudio:
        info = _FakeInfo()

        @staticmethod
        def get(_key, default):
            return default

    monkeypatch.setattr(library_module, "File", lambda *_args, **_kwargs: _FakeAudio())

    library = MusicLibrary()
    song = library._extract_song_info(str(song_file))

    assert song["title"] == "Slow Down"


def test_extract_song_info_strips_bracketed_chunks_from_filename(monkeypatch, tmp_path: Path):
    song_file = tmp_path / "01. Slow Down（Live）[Demo](2024).mp3"
    song_file.write_bytes(b"fake")

    class _FakeInfo:
        length = 120.0

    class _FakeAudio:
        info = _FakeInfo()

        @staticmethod
        def get(_key, default):
            return default

    monkeypatch.setattr(library_module, "File", lambda *_args, **_kwargs: _FakeAudio())

    library = MusicLibrary()
    song = library._extract_song_info(str(song_file))

    assert song["title"] == "Slow Down"


def test_extract_song_info_strips_artist_prefix_or_suffix_from_filename(monkeypatch, tmp_path: Path):
    song_file_a = tmp_path / "Taylor Swift - Love Story.mp3"
    song_file_b = tmp_path / "Because of You - Kelly Clarkson.mp3"
    song_file_a.write_bytes(b"fake")
    song_file_b.write_bytes(b"fake")

    class _FakeInfo:
        length = 200.0

    class _FakeAudioA:
        info = _FakeInfo()

        @staticmethod
        def get(key, default):
            if key == "artist":
                return ["Taylor Swift"]
            return default

    class _FakeAudioB:
        info = _FakeInfo()

        @staticmethod
        def get(key, default):
            if key == "artist":
                return ["Kelly Clarkson"]
            return default

    calls = {"count": 0}

    def _fake_file(_file_path, easy=True):
        calls["count"] += 1
        return _FakeAudioA() if calls["count"] == 1 else _FakeAudioB()

    monkeypatch.setattr(library_module, "File", _fake_file)

    library = MusicLibrary()
    song_a = library._extract_song_info(str(song_file_a))
    song_b = library._extract_song_info(str(song_file_b))

    assert song_a["title"] == "Love Story"
    assert song_b["title"] == "Because of You"


