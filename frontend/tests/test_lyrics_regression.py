import os

from core.lrc_parser import parse_lrc_text
from core.lyrics_service import LyricsService


def test_parse_lrc_supports_multi_timestamp_and_metadata():
    content = """
[ti:测试歌曲]
[ar:测试歌手]
[00:01.00]第一句
[00:03.50][00:05.00]副歌
""".strip()

    lines, metadata = parse_lrc_text(content)

    assert metadata["ti"] == "测试歌曲"
    assert metadata["ar"] == "测试歌手"
    assert [line.time_ms for line in lines] == [1000, 3500, 5000]
    assert [line.text for line in lines] == ["第一句", "副歌", "副歌"]


def test_lyrics_service_resolves_local_lrc(tmp_path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()

    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    lrc_file = music_dir / "demo.lrc"
    lrc_file.write_text("[00:00.00]hello\n[00:02.00]world\n", encoding="utf-8")

    service = LyricsService(cache_dir=str(tmp_path / "cache"))
    song = {
        "id": "song-1",
        "title": "demo",
        "artist": "tester",
        "path": str(audio_file),
    }

    result = service.resolve_for_song(song)
    assert result.source == "local"
    assert result.pending_asr is False
    assert len(result.lines) == 2
    assert result.lines[1].text == "world"


def test_lyrics_service_line_index_binary_search():
    service = LyricsService(cache_dir=".")
    lines, _ = parse_lrc_text("[00:01.00]a\n[00:02.00]b\n[00:04.00]c")

    assert service.current_line_index(lines, 0) == -1
    assert service.current_line_index(lines, 1000) == 0
    assert service.current_line_index(lines, 2500) == 1
    assert service.current_line_index(lines, 7000) == 2


def test_generate_lrc_with_asr_handles_internal_exception(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))
    audio_file = tmp_path / "a.mp3"
    audio_file.write_bytes(b"fake")

    song = {
        "id": "song-x",
        "title": "demo",
        "artist": "demo",
        "path": str(audio_file),
    }

    def fake_safe_transcribe(**_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.lyrics_service.transcribe_file_to_lrc_safe", fake_safe_transcribe)

    success, output_path, error_message = service.generate_lrc_with_asr(song)
    assert success is False
    assert output_path == ""
    assert "离线歌词识别异常" in error_message


def test_export_cache_lyrics_to_song_dir_uses_song_title(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "track.mp3"
    audio_file.write_bytes(b"fake")

    cache_file = tmp_path / "cache.lrc"
    cache_file.write_text("[00:00.00]hello\n", encoding="utf-8")

    song = {
        "id": "song-2",
        "title": "刚刚好",
        "artist": "demo",
        "path": str(audio_file),
    }

    target = service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    assert target.endswith("lyrics\\刚刚好.lrc")
    assert (music_dir / "lyrics" / "刚刚好.lrc").exists()


def test_generate_lrc_with_asr_passes_tuning_parameters(monkeypatch, tmp_path):
    service = LyricsService(
        cache_dir=str(tmp_path / "cache"),
        asr_model_size="medium",
        asr_beam_size=8,
        asr_vad_filter=False,
        asr_device="cpu",
        asr_compute_type="float32",
    )
    audio_file = tmp_path / "b.mp3"
    audio_file.write_bytes(b"fake")
    song = {
        "id": "song-3",
        "title": "demo",
        "artist": "demo",
        "path": str(audio_file),
    }

    captured = {}

    def fake_safe_transcribe(**kwargs):
        captured.update(kwargs)
        return False, "mock"

    monkeypatch.setattr("core.lyrics_service.transcribe_file_to_lrc_safe", fake_safe_transcribe)

    success, output_path, error_message = service.generate_lrc_with_asr(song)
    assert success is False
    assert output_path == ""
    assert error_message == "mock"
    assert captured["model_size"] == "medium"
    assert captured["beam_size"] == 8
    assert captured["vad_filter"] is False
    assert captured["device"] == "cpu"
    assert captured["compute_type"] == "float32"


def test_resolve_finds_exported_title_lrc_in_lyrics_dir(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "origin-file-name.mp3"
    audio_file.write_bytes(b"fake")

    lyrics_dir = music_dir / "lyrics"
    lyrics_dir.mkdir()
    title_lrc = lyrics_dir / "标题歌曲.lrc"
    title_lrc.write_text("[00:00.00]line\n", encoding="utf-8")

    song = {
        "id": "song-4",
        "title": "标题歌曲",
        "artist": "demo",
        "path": str(audio_file),
    }
    result = service.resolve_for_song(song)
    assert result.source == "local"
    assert result.file_path.endswith("标题歌曲.lrc")
    assert len(result.lines) == 1


def test_fallback_song_id_is_stable_for_same_song(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))
    song = {
        "title": "same",
        "artist": "demo",
        "path": str(tmp_path / "song.mp3"),
    }

    id1 = service.get_cache_lrc_path(song)
    id2 = service.get_cache_lrc_path(song)
    assert id1 == id2


def test_export_cache_lyrics_uses_audio_basename_when_title_is_hash(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "周杰伦-晴天.mp3"
    audio_file.write_bytes(b"fake")

    cache_file = tmp_path / "cache_hash.lrc"
    cache_file.write_text("[00:00.00]hello\n", encoding="utf-8")

    song = {
        "id": "song-5",
        "title": "6ee2dc774c88dd11c567d923cef48561",
        "artist": "demo",
        "path": str(audio_file),
    }

    target = service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    assert target.endswith("lyrics\\周杰伦-晴天.lrc")


def test_resolve_from_asr_cache_keeps_pending_asr_true(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))
    monkeypatch.setattr(service, "_asr_available", lambda: True)

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    cache_path = service.get_cache_lrc_path({"id": "song-6", "path": str(audio_file), "title": "demo"})
    with open(cache_path, "w", encoding="utf-8") as handler:
        handler.write("[00:00.00]line\n")

    song = {
        "id": "song-6",
        "title": "demo",
        "artist": "demo",
        "path": str(audio_file),
    }
    result = service.resolve_for_song(song)
    assert result.source == "asr-cache"
    assert result.pending_asr is True


def test_export_cache_lyrics_marks_managed_and_allows_managed_overwrite(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    cache_file = tmp_path / "cache_marked.lrc"
    cache_file.write_text("[00:00.00]line-a\n", encoding="utf-8")

    song = {
        "id": "song-marked",
        "title": "Demo",
        "artist": "demo",
        "path": str(audio_file),
    }

    target = service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    content_first = (music_dir / "lyrics" / "Demo.lrc").read_text(encoding="utf-8")
    assert target.endswith("Demo.lrc")
    assert content_first.startswith("[re:RHYME-ASR]\n")

    cache_file.write_text("[00:00.00]line-b\n", encoding="utf-8")
    service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    content_second = (music_dir / "lyrics" / "Demo.lrc").read_text(encoding="utf-8")
    assert "line-b" in content_second


def test_export_cache_lyrics_keeps_user_local_file_when_not_managed(tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    lyrics_dir = music_dir / "lyrics"
    lyrics_dir.mkdir()
    target = lyrics_dir / "Demo.lrc"
    target.write_text("[00:00.00]user-fixed\n", encoding="utf-8")

    cache_file = tmp_path / "cache_user_keep.lrc"
    cache_file.write_text("[00:00.00]asr-content\n", encoding="utf-8")

    song = {
        "id": "song-user-keep",
        "title": "Demo",
        "artist": "demo",
        "path": str(audio_file),
    }

    service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    kept = target.read_text(encoding="utf-8")
    assert kept == "[00:00.00]user-fixed\n"


def test_try_fetch_online_lrc_saves_cache_and_song_dir(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    class _Result:
        success = True
        lrc_text = "[00:00.00]line"
        song_name = "在线歌曲"
        artist = "在线歌手"
        detail_url = ""
        error = ""
        debug_search_path = ""
        debug_detail_path = ""

    monkeypatch.setattr(service.online_lyrics_client, "fetch", lambda *_args, **_kwargs: _Result())
    song = {"id": "song-online", "title": "demo", "artist": "artist", "path": str(audio_file)}

    ok, saved_path, err = service.try_fetch_online_lrc(song)
    assert ok is True
    assert err == ""
    assert saved_path.endswith("lyrics\\demo.lrc")
    assert (music_dir / "lyrics" / "demo.lrc").exists()
    assert os.path.exists(service.get_cache_lrc_path(song))


def test_try_fetch_online_lrc_returns_debug_error(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    class _Result:
        success = False
        lrc_text = ""
        song_name = ""
        artist = ""
        detail_url = ""
        error = "未提取到歌词"
        debug_search_path = "x\\debug_search.html"
        debug_detail_path = "x\\debug_detail.html"

    monkeypatch.setattr(service.online_lyrics_client, "fetch", lambda *_args, **_kwargs: _Result())
    song = {"id": "song-online-fail", "title": "demo", "artist": "artist", "path": str(tmp_path / "demo.mp3")}

    ok, saved_path, err = service.try_fetch_online_lrc(song)
    assert ok is False
    assert saved_path == ""
    assert "debug_search.html" in err


def test_try_fetch_online_lrc_prefers_manual_query(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "origin.mp3"
    audio_file.write_bytes(b"fake")

    captured = {}

    class _Result:
        success = True
        lrc_text = "[00:00.00]line"
        song_name = "手动标题"
        artist = "手动歌手"
        detail_url = ""
        error = ""
        debug_search_path = ""
        debug_detail_path = ""

    def _fake_fetch(title, artist):
        captured["title"] = title
        captured["artist"] = artist
        return _Result()

    monkeypatch.setattr(service.online_lyrics_client, "fetch", _fake_fetch)
    song = {"id": "song-manual", "title": "默认标题", "artist": "默认歌手", "path": str(audio_file)}

    ok, _saved_path, err = service.try_fetch_online_lrc(song, query_title="手动标题", query_artist="")
    assert ok is True
    assert err == ""
    assert captured["title"] == "手动标题"
    assert captured["artist"] == "默认歌手"


def test_fetch_online_lrc_text_by_query(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))

    class _Result:
        success = True
        lrc_text = "[00:00.00]line"
        song_name = "标题"
        artist = "歌手"
        detail_url = ""
        error = ""
        debug_search_path = ""
        debug_detail_path = ""

    captured = {}

    def _fake_fetch(title, artist):
        captured["title"] = title
        captured["artist"] = artist
        return _Result()

    monkeypatch.setattr(service.online_lyrics_client, "fetch", _fake_fetch)
    ok, lrc_text, err = service.fetch_online_lrc_text("手动歌名", "")
    assert ok is True
    assert lrc_text == "[00:00.00]line"
    assert err == ""
    assert captured["title"] == "手动歌名"
    assert captured["artist"] == ""


def test_export_cache_lyrics_uses_custom_output_dir_and_can_resolve(tmp_path):
    custom_dir = tmp_path / "custom-lyrics"
    service = LyricsService(cache_dir=str(tmp_path / "cache"), lyrics_output_dir=str(custom_dir))

    music_dir = tmp_path / "music"
    music_dir.mkdir()
    audio_file = music_dir / "demo.mp3"
    audio_file.write_bytes(b"fake")

    cache_file = tmp_path / "cache_custom.lrc"
    cache_file.write_text("[00:00.00]hello\n", encoding="utf-8")

    song = {
        "id": "song-custom-dir",
        "title": "DemoSong",
        "artist": "demo",
        "path": str(audio_file),
    }

    target = service.export_cache_lyrics_to_song_dir(song, str(cache_file))
    assert os.path.exists(target)
    assert str(custom_dir) in target

    resolved = service.find_local_lrc(song)
    assert resolved == target


def test_generate_lrc_with_asr_skips_repeated_instrumental_song(monkeypatch, tmp_path):
    service = LyricsService(cache_dir=str(tmp_path / "cache"))
    audio_file = tmp_path / "instrumental.mp3"
    audio_file.write_bytes(b"fake")
    song = {
        "id": "instrumental-1",
        "title": "纯音乐",
        "artist": "demo",
        "path": str(audio_file),
    }

    called = {"count": 0}

    def fake_safe_transcribe(**_kwargs):
        called["count"] += 1
        return False, "疑似纯音乐或无人声，已跳过识别"

    monkeypatch.setattr("core.lyrics_service.transcribe_file_to_lrc_safe", fake_safe_transcribe)

    first_success, _, first_error = service.generate_lrc_with_asr(song)
    second_success, _, second_error = service.generate_lrc_with_asr(song)

    assert first_success is False
    assert "疑似纯音乐" in first_error
    assert second_success is False
    assert "已跳过重复识别" in second_error
    assert called["count"] == 1


