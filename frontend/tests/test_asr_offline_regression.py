from types import SimpleNamespace

from core import asr_offline


class _FailingCudaModel:
    def transcribe(self, *_args, **_kwargs):
        raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")


class _OkCpuModel:
    def transcribe(self, *_args, **_kwargs):
        segment = SimpleNamespace(start=0.0, text="测试歌词")
        return [segment], None


class _TraditionalModel:
    def transcribe(self, *_args, **_kwargs):
        segment = SimpleNamespace(start=0.0, text="這個世界沒有如果")
        return [segment], None


class _NoSpeechModel:
    def transcribe(self, *_args, **_kwargs):
        return [], None


def test_transcribe_falls_back_to_cpu_when_cuda_cublas_missing(monkeypatch, tmp_path):
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"fake")
    output_file = tmp_path / "song.lrc"

    monkeypatch.setattr(asr_offline, "asr_available", lambda: True)

    def fake_get_model(_model_size, device, _compute_type):
        if device == "cuda":
            return _FailingCudaModel()
        return _OkCpuModel()

    monkeypatch.setattr(asr_offline, "_get_model", fake_get_model)

    success, error_message = asr_offline.transcribe_file_to_lrc(
        audio_path=str(audio_file),
        lrc_output_path=str(output_file),
        model_size="small",
        language="zh",
        device="cuda",
        compute_type="float16",
        beam_size=5,
        vad_filter=False,
    )

    assert success is True
    assert error_message == ""
    assert output_file.exists()
    assert "测试歌词" in output_file.read_text(encoding="utf-8")


def test_transcribe_converts_traditional_to_simplified(monkeypatch, tmp_path):
    audio_file = tmp_path / "song2.mp3"
    audio_file.write_bytes(b"fake")
    output_file = tmp_path / "song2.lrc"

    monkeypatch.setattr(asr_offline, "asr_available", lambda: True)
    monkeypatch.setattr(asr_offline, "_get_model", lambda *_args, **_kwargs: _TraditionalModel())
    monkeypatch.setattr(asr_offline, "_get_opencc_converter", lambda: None)

    success, error_message = asr_offline.transcribe_file_to_lrc(
        audio_path=str(audio_file),
        lrc_output_path=str(output_file),
        device="cpu",
        compute_type="float32",
        to_simplified=True,
    )

    assert success is True
    assert error_message == ""
    content = output_file.read_text(encoding="utf-8")
    assert "这个世界没有如果" in content


def test_transcribe_keeps_original_text_when_simplified_disabled(monkeypatch, tmp_path):
    audio_file = tmp_path / "song3.mp3"
    audio_file.write_bytes(b"fake")
    output_file = tmp_path / "song3.lrc"

    monkeypatch.setattr(asr_offline, "asr_available", lambda: True)
    monkeypatch.setattr(asr_offline, "_get_model", lambda *_args, **_kwargs: _TraditionalModel())

    success, _ = asr_offline.transcribe_file_to_lrc(
        audio_path=str(audio_file),
        lrc_output_path=str(output_file),
        device="cpu",
        compute_type="float32",
        to_simplified=False,
    )

    assert success is True
    content = output_file.read_text(encoding="utf-8")
    assert "這個世界沒有如果" in content


def test_transcribe_returns_instrumental_hint_when_no_speech(monkeypatch, tmp_path):
    audio_file = tmp_path / "song4.mp3"
    audio_file.write_bytes(b"fake")
    output_file = tmp_path / "song4.lrc"

    monkeypatch.setattr(asr_offline, "asr_available", lambda: True)
    monkeypatch.setattr(asr_offline, "_get_model", lambda *_args, **_kwargs: _NoSpeechModel())

    success, error_message = asr_offline.transcribe_file_to_lrc(
        audio_path=str(audio_file),
        lrc_output_path=str(output_file),
        device="cpu",
        compute_type="float32",
        instrumental_guard=True,
    )

    assert success is False
    assert "疑似纯音乐" in error_message


def test_transcribe_safe_uses_in_process_path_when_frozen(monkeypatch, tmp_path):
    audio_file = tmp_path / "song5.mp3"
    audio_file.write_bytes(b"fake")
    output_file = tmp_path / "song5.lrc"

    monkeypatch.setattr(asr_offline.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        asr_offline,
        "transcribe_file_to_lrc",
        lambda **_kwargs: (True, ""),
    )

    called = {"run": 0}

    def _should_not_run(*_args, **_kwargs):
        called["run"] += 1
        raise AssertionError("subprocess.run should not be called in frozen mode")

    monkeypatch.setattr(asr_offline.subprocess, "run", _should_not_run)

    success, error_message = asr_offline.transcribe_file_to_lrc_safe(
        audio_path=str(audio_file),
        lrc_output_path=str(output_file),
    )

    assert success is True
    assert error_message == ""
    assert called["run"] == 0


