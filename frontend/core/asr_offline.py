import argparse
import importlib.util
import os
import subprocess
import sys
from threading import Lock

try:
    from .lrc_parser import format_timestamp
except Exception:
    # 允许本文件以脚本方式被子进程直接执行。
    from lrc_parser import format_timestamp


_MODEL_CACHE = {}
_MODEL_CACHE_LOCK = Lock()
DEFAULT_ASR_DEVICE = (os.getenv("RHYME_ASR_DEVICE", "cpu") or "cpu").strip()
DEFAULT_ASR_COMPUTE_TYPE = (os.getenv("RHYME_ASR_COMPUTE_TYPE", "float32") or "float32").strip()
DEFAULT_ASR_MODEL_SIZE = (os.getenv("RHYME_ASR_MODEL_SIZE", "small") or "small").strip()


def _parse_int_env(name, default):
    try:
        return int((os.getenv(name, str(default)) or str(default)).strip())
    except Exception:
        return int(default)


DEFAULT_ASR_BEAM_SIZE = _parse_int_env("RHYME_ASR_BEAM_SIZE", 5)
DEFAULT_ASR_VAD_FILTER = (os.getenv("RHYME_ASR_VAD_FILTER", "false") or "false").strip().lower() in ("1", "true", "yes", "on")
DEFAULT_ASR_INSTRUMENTAL_GUARD = (os.getenv("RHYME_ASR_INSTRUMENTAL_GUARD", "true") or "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
DEFAULT_ASR_TO_SIMPLIFIED = (os.getenv("RHYME_ASR_TO_SIMPLIFIED", "true") or "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)

_OPENCC_CONVERTER = None
_OPENCC_READY = False

_FALLBACK_T2S_MAP = str.maketrans(
    {
        "為": "为",
        "這": "这",
        "個": "个",
        "來": "来",
        "說": "说",
        "愛": "爱",
        "會": "会",
        "沒": "没",
        "風": "风",
        "聽": "听",
        "讓": "让",
        "裡": "里",
        "時": "时",
        "開": "开",
        "關": "关",
        "學": "学",
        "間": "间",
        "麼": "么",
        "對": "对",
        "後": "后",
        "當": "当",
        "們": "们",
    }
)


def _is_cublas_related_error(message):
    text = (message or "").lower()
    return "cublas" in text or "cublas64_12.dll" in text or "cuda" in text


def _get_opencc_converter():
    global _OPENCC_CONVERTER, _OPENCC_READY
    if _OPENCC_READY:
        return _OPENCC_CONVERTER

    _OPENCC_READY = True
    try:
        from opencc import OpenCC

        _OPENCC_CONVERTER = OpenCC("t2s")
    except Exception:
        _OPENCC_CONVERTER = None
    return _OPENCC_CONVERTER


def _to_simplified_text(text):
    content = (text or "").strip()
    if not content:
        return ""

    converter = _get_opencc_converter()
    if converter is not None:
        try:
            converted = converter.convert(content)
            if converted:
                return converted
        except Exception:
            pass

    return content.translate(_FALLBACK_T2S_MAP)


def asr_available():
    try:
        return importlib.util.find_spec("faster_whisper") is not None
    except Exception:
        return False


def _get_model(model_size, device, compute_type):
    with _MODEL_CACHE_LOCK:
        cache_key = (model_size, device, compute_type)
        model = _MODEL_CACHE.get(cache_key)
        if model is not None:
            return model

        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        _MODEL_CACHE[cache_key] = model
        return model


def transcribe_file_to_lrc(
    audio_path,
    lrc_output_path,
    model_size=DEFAULT_ASR_MODEL_SIZE,
    language="zh",
    device=None,
    compute_type=None,
    beam_size=DEFAULT_ASR_BEAM_SIZE,
    vad_filter=DEFAULT_ASR_VAD_FILTER,
    instrumental_guard=DEFAULT_ASR_INSTRUMENTAL_GUARD,
    to_simplified=DEFAULT_ASR_TO_SIMPLIFIED,
):
    if not asr_available():
        return False, "faster-whisper 未安装，无法执行离线歌词识别"

    try:
        actual_device = (device or DEFAULT_ASR_DEVICE).strip() or "cpu"
        actual_compute_type = (compute_type or DEFAULT_ASR_COMPUTE_TYPE).strip() or "float32"
        model = _get_model(model_size, actual_device, actual_compute_type)
        try:
            segments, _ = model.transcribe(
                audio_path,
                language=language,
                vad_filter=bool(vad_filter),
                beam_size=max(1, int(beam_size)),
            )
        except Exception as exc:
            if actual_device != "cpu" and _is_cublas_related_error(str(exc)):
                fallback_device = "cpu"
                fallback_compute_type = "float32"
                fallback_model = _get_model(model_size, fallback_device, fallback_compute_type)
                segments, _ = fallback_model.transcribe(
                    audio_path,
                    language=language,
                    vad_filter=bool(vad_filter),
                    beam_size=max(1, int(beam_size)),
                )
            else:
                raise

        lrc_lines = []
        normalized_texts = []
        for segment in segments:
            text = (segment.text or "").strip()
            if not text:
                continue
            normalized_texts.append("".join(ch for ch in text if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff")))
            if to_simplified:
                text = _to_simplified_text(text)
            time_ms = int(max(0.0, segment.start) * 1000)
            lrc_lines.append(f"{format_timestamp(time_ms)}{text}")

        if not lrc_lines:
            if instrumental_guard:
                return False, "疑似纯音乐或无人声，已跳过识别"
            return False, "ASR 未识别到可用歌词文本"

        if instrumental_guard:
            total_visible_chars = sum(len(item) for item in normalized_texts)
            if len(lrc_lines) <= 1 and total_visible_chars <= 3:
                return False, "疑似纯音乐或无人声，已跳过识别"

        with open(lrc_output_path, "w", encoding="utf-8") as handler:
            handler.write("\n".join(lrc_lines) + "\n")

        return True, ""
    except Exception as exc:
        return False, str(exc)


def transcribe_file_to_lrc_safe(
    audio_path,
    lrc_output_path,
    model_size=DEFAULT_ASR_MODEL_SIZE,
    language="zh",
    timeout_seconds=1800,
    device=None,
    compute_type=None,
    beam_size=DEFAULT_ASR_BEAM_SIZE,
    vad_filter=DEFAULT_ASR_VAD_FILTER,
    instrumental_guard=DEFAULT_ASR_INSTRUMENTAL_GUARD,
    to_simplified=DEFAULT_ASR_TO_SIMPLIFIED,
):
    if not audio_path or not os.path.exists(audio_path):
        return False, "音频文件不存在"

    # 打包态下 `sys.executable` 指向主程序 exe，子进程会重复拉起应用窗口。
    # 这里改为进程内直调，避免“识别歌词时新开程序页面”。
    if bool(getattr(sys, "frozen", False)):
        return transcribe_file_to_lrc(
            audio_path=audio_path,
            lrc_output_path=lrc_output_path,
            model_size=model_size,
            language=language,
            device=device,
            compute_type=compute_type,
            beam_size=beam_size,
            vad_filter=vad_filter,
            instrumental_guard=instrumental_guard,
            to_simplified=to_simplified,
        )

    command = [
        sys.executable,
        __file__,
        "--audio",
        audio_path,
        "--output",
        lrc_output_path,
        "--model-size",
        model_size,
        "--language",
        language,
        "--device",
        (device or DEFAULT_ASR_DEVICE),
        "--compute-type",
        (compute_type or DEFAULT_ASR_COMPUTE_TYPE),
        "--beam-size",
        str(max(1, int(beam_size))),
        "--vad-filter",
        "true" if bool(vad_filter) else "false",
        "--instrumental-guard",
        "true" if bool(instrumental_guard) else "false",
        "--to-simplified",
        "true" if bool(to_simplified) else "false",
    ]

    run_kwargs = {
        "capture_output": True,
        "text": True,
        "timeout": timeout_seconds,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if sys.platform.startswith("win"):
        create_no_window = int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)
        if create_no_window:
            run_kwargs["creationflags"] = create_no_window
        startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
        startf_use_show_window = int(getattr(subprocess, "STARTF_USESHOWWINDOW", 0) or 0)
        if startupinfo_cls is not None and startf_use_show_window:
            startupinfo = startupinfo_cls()
            startupinfo.dwFlags |= startf_use_show_window
            startupinfo.wShowWindow = 0
            run_kwargs["startupinfo"] = startupinfo

    try:
        completed = subprocess.run(
            command,
            **run_kwargs,
        )
    except subprocess.TimeoutExpired:
        return False, f"离线识别超时（>{timeout_seconds}秒）"
    except Exception as exc:
        return False, f"无法启动离线识别子进程: {exc}"

    if completed.returncode == 0:
        return True, ""

    error_text = (completed.stderr or completed.stdout or "未知错误").strip()
    return False, error_text


def _main():
    parser = argparse.ArgumentParser(description="RHYME 离线歌词识别子进程")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-size", default=DEFAULT_ASR_MODEL_SIZE)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", default=DEFAULT_ASR_DEVICE)
    parser.add_argument("--compute-type", default=DEFAULT_ASR_COMPUTE_TYPE)
    parser.add_argument("--beam-size", type=int, default=DEFAULT_ASR_BEAM_SIZE)
    parser.add_argument("--vad-filter", default="false")
    parser.add_argument("--instrumental-guard", default="true")
    parser.add_argument("--to-simplified", default="true")
    args = parser.parse_args()

    vad_filter = str(args.vad_filter).strip().lower() in ("1", "true", "yes", "on")
    instrumental_guard = str(args.instrumental_guard).strip().lower() in ("1", "true", "yes", "on")
    to_simplified = str(args.to_simplified).strip().lower() in ("1", "true", "yes", "on")

    ok, message = transcribe_file_to_lrc(
        audio_path=args.audio,
        lrc_output_path=args.output,
        model_size=args.model_size,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        beam_size=args.beam_size,
        vad_filter=vad_filter,
        instrumental_guard=instrumental_guard,
        to_simplified=to_simplified,
    )
    if ok:
        return 0

    print(message or "离线歌词识别失败", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())


