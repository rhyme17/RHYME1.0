from collections import OrderedDict
from contextlib import contextmanager
import math
import os
import sys
import threading
import time

from mutagen import File as MutagenFile
import numpy as np
from pydub import AudioSegment
from pydub import audio_segment as pydub_audio_segment
from pydub import utils as pydub_utils
import sounddevice as sd

try:
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.logging_utils import get_logger


logger = get_logger(__name__)

_FFMPEG_POPEN_PATCH_LOCK = threading.RLock()
_FFMPEG_POPEN_PATCH_DEPTH = 0
_FFMPEG_POPEN_PATCH_TARGETS = []


class AudioPlayer:
    DEFAULT_FILE_SIZE_WARNING_MB = 80
    DEFAULT_PCM_MEMORY_WARNING_MB = 220

    def __init__(self):
        self.volume = 1.0
        self.is_playing = False
        self.is_paused = False
        self.current_file = None

        self._lock = threading.RLock()
        self._stream = None
        self._audio_data = None
        self._sample_rate = 0
        self._total_frames = 0
        self._position_frames = 0
        self._duration_seconds = 0.0

        self.prefer_high_quality_output = False
        self.audio_output_strategy = "follow_system"
        self.fixed_output_device_signature = None

        self.loudness_normalization_level = "medium"
        self._current_track_normalize_gain = 1.0

        self._decoded_cache = OrderedDict()
        self._decoded_cache_max_items = 6

        self._active_output_device_signature = None
        self._last_recover_attempt_monotonic = 0.0
        self._suppress_recover_until_monotonic = 0.0
        self._recover_min_interval_seconds = 1.0
        self._is_recovering_output_device = False

        self._visual_intensity = 0.0
        self._visual_accent = 0.0

    def set_high_quality_output_mode(self, enabled):
        self.prefer_high_quality_output = bool(enabled)

    def get_high_quality_output_mode(self):
        return bool(self.prefer_high_quality_output)

    def set_output_device_strategy(self, strategy, fixed_signature=None):
        normalized = str(strategy or "follow_system").strip().lower()
        if normalized == "fixed":
            normalized = "fixed_current"
        if normalized not in {"follow_system", "fixed_current"}:
            normalized = "follow_system"

        self.audio_output_strategy = normalized
        if normalized == "fixed_current":
            signature = fixed_signature if fixed_signature is not None else self.get_default_output_device_signature()
            self.fixed_output_device_signature = signature
            return

        self.fixed_output_device_signature = None

    def set_loudness_normalization_level(self, level):
        level = str(level or "medium").strip().lower()
        if level == "low":
            level = "light"
        elif level == "high":
            level = "strong"
        if level not in {"off", "light", "medium", "strong"}:
            level = "medium"
        self.loudness_normalization_level = level

    def should_warn_heavy_decode(
        self,
        file_size_bytes,
        duration_seconds,
        file_size_threshold_mb=None,
        pcm_threshold_mb=None,
    ):
        file_size_threshold_mb = float(
            self.DEFAULT_FILE_SIZE_WARNING_MB if file_size_threshold_mb is None else file_size_threshold_mb
        )
        pcm_threshold_mb = float(
            self.DEFAULT_PCM_MEMORY_WARNING_MB if pcm_threshold_mb is None else pcm_threshold_mb
        )
        file_size_mb = max(0.0, float(file_size_bytes or 0.0) / (1024.0 * 1024.0))
        duration_seconds = max(0.0, float(duration_seconds or 0.0))
        estimated_pcm_mb = duration_seconds * 44100.0 * 2.0 * 4.0 / (1024.0 * 1024.0)
        should_warn = file_size_mb >= file_size_threshold_mb or estimated_pcm_mb >= pcm_threshold_mb
        return bool(should_warn), file_size_mb, estimated_pcm_mb

    def _get_file_signature(self, file_path):
        try:
            stat = os.stat(file_path)
            return (int(stat.st_size), int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))))
        except OSError:
            return None

    def _get_cached_decoded(self, file_path):
        cached = self._decoded_cache.get(file_path)
        if not cached:
            return None
        signature = self._get_file_signature(file_path)
        if signature is None or cached.get("signature") != signature:
            self._decoded_cache.pop(file_path, None)
            return None
        self._decoded_cache.move_to_end(file_path)
        return cached

    def has_decoded_cache(self, file_path):
        return self._get_cached_decoded(file_path) is not None

    def _put_decoded_cache(self, file_path, audio_data, sample_rate, duration_seconds, normalization_gain=None):
        signature = self._get_file_signature(file_path)
        if signature is None:
            return
        if normalization_gain is None:
            normalization_gain = 1.0
        self._decoded_cache[file_path] = {
            "signature": signature,
            "audio_data": audio_data,
            "sample_rate": int(sample_rate),
            "duration_seconds": float(duration_seconds),
            "normalization_gain": float(normalization_gain),
        }
        self._decoded_cache.move_to_end(file_path)
        while len(self._decoded_cache) > int(self._decoded_cache_max_items):
            self._decoded_cache.popitem(last=False)

    def prepare_predecoded_audio(self, file_path):
        cached = self._get_cached_decoded(file_path)
        if cached is not None:
            return {
                "audio_data": cached["audio_data"],
                "sample_rate": int(cached["sample_rate"]),
                "duration_seconds": float(cached["duration_seconds"]),
                "normalization_gain": float(cached.get("normalization_gain", 1.0) or 1.0),
            }

        segment = self._decode_audio_segment(file_path)
        audio_data = self._segment_to_float_array(segment)
        sample_rate = int(segment.frame_rate)
        duration_seconds = float(len(audio_data) / sample_rate) if sample_rate > 0 else 0.0
        normalization_gain = self._compute_normalization_gain(audio_data)

        self._put_decoded_cache(
            file_path,
            audio_data,
            sample_rate,
            duration_seconds,
            normalization_gain=normalization_gain,
        )
        return {
            "audio_data": audio_data,
            "sample_rate": sample_rate,
            "duration_seconds": duration_seconds,
            "normalization_gain": normalization_gain,
        }

    def play_predecoded(self, file_path, payload, start_position=0):
        try:
            audio_data = np.asarray(payload["audio_data"], dtype=np.float32)
            if audio_data.ndim == 1:
                audio_data = audio_data[:, np.newaxis]
            if audio_data.size <= 0:
                return False

            sample_rate = int(payload.get("sample_rate") or 0)
            if sample_rate <= 0:
                return False

            duration_seconds = float(payload.get("duration_seconds") or (len(audio_data) / sample_rate))
            normalization_gain = float(payload.get("normalization_gain", 1.0) or 1.0)

            safe_start_ms = max(0.0, float(start_position or 0.0))
            if not math.isfinite(safe_start_ms):
                safe_start_ms = 0.0

            with self._lock:
                self.stop()
                self.current_file = file_path
                self._audio_data = audio_data
                self._sample_rate = sample_rate
                self._total_frames = int(len(audio_data))
                self._duration_seconds = duration_seconds
                self._current_track_normalize_gain = normalization_gain
                self._position_frames = min(int(safe_start_ms * sample_rate / 1000.0), self._total_frames)
                self.is_playing = True
                self.is_paused = False
                self._reset_visual_metrics()

            self._build_stream()
            self._active_output_device_signature = self.get_default_output_device_signature()
            now = time.monotonic()
            self._last_recover_attempt_monotonic = now
            self._suppress_recover_until_monotonic = now + 5.0 if safe_start_ms > 0 else 0.0
            return True
        except Exception:
            logger.exception("预解码播放失败")
            self.is_playing = False
            self.is_paused = False
            self._audio_data = None
            self._current_track_normalize_gain = 1.0
            return False

    def _compute_normalization_gain(self, audio_data):
        level = getattr(self, "loudness_normalization_level", "medium")
        if level == "off":
            return 1.0

        target_map = {
            "light": 0.11,
            "medium": 0.16,
            "strong": 0.21,
        }
        target_rms = float(target_map.get(level, 0.16))

        if audio_data is None:
            return 1.0
        if getattr(audio_data, "ndim", 1) > 1:
            mono = np.mean(audio_data, axis=1)
        else:
            mono = audio_data
        mono = np.asarray(mono, dtype=np.float32)
        if mono.size <= 0:
            return 1.0

        rms = float(np.sqrt(np.mean(np.square(mono))))
        if rms <= 1e-6:
            return 1.0

        gain = target_rms / rms
        return float(max(0.35, min(2.2, gain)))

    def _segment_to_float_array(self, segment):
        samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
        channels = int(segment.channels or 1)
        if channels > 1:
            samples = samples.reshape((-1, channels))
        else:
            samples = samples.reshape((-1, 1))
        scale = float(1 << (8 * int(segment.sample_width) - 1))
        if scale <= 0:
            scale = 32768.0
        samples /= scale
        return np.clip(samples, -1.0, 1.0).astype(np.float32, copy=False)

    @contextmanager
    def _suppress_ffmpeg_console_window(self):
        global _FFMPEG_POPEN_PATCH_DEPTH
        global _FFMPEG_POPEN_PATCH_TARGETS

        if not sys.platform.startswith("win"):
            yield
            return

        subprocess_module = getattr(pydub_audio_segment, "subprocess", None)
        popen_targets = []

        audio_segment_popen = getattr(subprocess_module, "Popen", None) if subprocess_module is not None else None
        if audio_segment_popen is not None:
            popen_targets.append((subprocess_module, "Popen", audio_segment_popen))

        utils_popen = getattr(pydub_utils, "Popen", None)
        if utils_popen is not None:
            popen_targets.append((pydub_utils, "Popen", utils_popen))

        if not popen_targets:
            yield
            return

        create_no_window = int(getattr(subprocess_module, "CREATE_NO_WINDOW", 0) or 0)
        startupinfo_cls = getattr(subprocess_module, "STARTUPINFO", None)
        startf_use_show_window = int(getattr(subprocess_module, "STARTF_USESHOWWINDOW", 0) or 0)

        def _wrapped_popen(*args, **kwargs):
            if create_no_window:
                kwargs["creationflags"] = int(kwargs.get("creationflags", 0) or 0) | create_no_window
            if startupinfo_cls is not None and startf_use_show_window:
                startupinfo = kwargs.get("startupinfo")
                if startupinfo is None:
                    startupinfo = startupinfo_cls()
                    kwargs["startupinfo"] = startupinfo
                startupinfo.dwFlags |= startf_use_show_window
                startupinfo.wShowWindow = 0
            target_original = kwargs.pop("_rhyme_target_original_popen")
            return target_original(*args, **kwargs)

        with _FFMPEG_POPEN_PATCH_LOCK:
            if _FFMPEG_POPEN_PATCH_DEPTH == 0:
                _FFMPEG_POPEN_PATCH_TARGETS = []
                for target_module, attr_name, target_original in popen_targets:
                    def _build_wrapped(original_ref):
                        def _wrapped(*args, **kwargs):
                            kwargs["_rhyme_target_original_popen"] = original_ref
                            return _wrapped_popen(*args, **kwargs)
                        return _wrapped

                    setattr(target_module, attr_name, _build_wrapped(target_original))
                    _FFMPEG_POPEN_PATCH_TARGETS.append((target_module, attr_name, target_original))
            _FFMPEG_POPEN_PATCH_DEPTH += 1

        try:
            yield
        finally:
            with _FFMPEG_POPEN_PATCH_LOCK:
                if _FFMPEG_POPEN_PATCH_DEPTH > 0:
                    _FFMPEG_POPEN_PATCH_DEPTH -= 1
                if _FFMPEG_POPEN_PATCH_DEPTH == 0 and _FFMPEG_POPEN_PATCH_TARGETS:
                    for target_module, attr_name, target_original in _FFMPEG_POPEN_PATCH_TARGETS:
                        setattr(target_module, attr_name, target_original)
                    _FFMPEG_POPEN_PATCH_TARGETS = []

    def _decode_audio_segment(self, file_path):
        with self._suppress_ffmpeg_console_window():
            return AudioSegment.from_file(file_path)

    def _reset_visual_metrics(self):
        self._visual_intensity = 0.0
        self._visual_accent = 0.0

    def _update_visual_metrics_from_chunk(self, chunk):
        if chunk is None:
            self._reset_visual_metrics()
            return

        data = np.asarray(chunk, dtype=np.float32)
        if data.size <= 0:
            self._visual_intensity *= 0.75
            self._visual_accent *= 0.62
            return

        if data.ndim > 1:
            mono = np.mean(data, axis=1)
        else:
            mono = data

        rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size > 0 else 0.0
        intensity = max(0.0, min(1.0, rms / 0.28))

        gradient = np.abs(np.diff(mono)) if mono.size > 1 else np.array([0.0], dtype=np.float32)
        transient = float(np.max(gradient)) if gradient.size > 0 else 0.0
        transient_norm = max(0.0, min(1.0, transient / 0.25))
        # Keep accent responsive even for sustained high-energy chunks.
        transient_norm = max(transient_norm, intensity * 0.45)

        self._visual_intensity = max(intensity, self._visual_intensity * 0.82)
        self._visual_accent = max(transient_norm, self._visual_accent * 0.62)

    def _build_stream(self):
        def callback(outdata, frames, _time_info, _status):
            with self._lock:
                if (not self.is_playing) or self._audio_data is None:
                    self._reset_visual_metrics()
                    outdata.fill(0)
                    raise sd.CallbackStop

                if self.is_paused:
                    self._reset_visual_metrics()
                    outdata.fill(0)
                    return

                start = self._position_frames
                end = min(start + frames, self._total_frames)
                chunk = self._audio_data[start:end]
                gain = float(getattr(self, "_current_track_normalize_gain", 1.0) or 1.0)
                chunk = chunk * float(self.volume) * gain
                self._update_visual_metrics_from_chunk(chunk)

                chunk_len = len(chunk)
                outdata[:chunk_len] = chunk
                if chunk_len < frames:
                    outdata[chunk_len:].fill(0)

                self._position_frames = end
                if end >= self._total_frames:
                    self.is_playing = False
                    self.is_paused = False
                    raise sd.CallbackStop

        stream_kwargs = {
            "samplerate": self._sample_rate,
            "channels": int(self._audio_data.shape[1]),
            "dtype": "float32",
            "callback": callback,
        }

        prefer_exclusive = bool(self.prefer_high_quality_output) and sys.platform.startswith("win")
        if prefer_exclusive:
            hostapi_name = self._default_output_hostapi_name()
            if "wasapi" not in hostapi_name:
                prefer_exclusive = False

        if prefer_exclusive:
            wasapi_settings_cls = getattr(sd, "WasapiSettings", None)
            if wasapi_settings_cls is not None:
                try:
                    self._stream = sd.OutputStream(
                        **stream_kwargs,
                        extra_settings=wasapi_settings_cls(exclusive=True),
                    )
                    self._stream.start()
                    return
                except Exception:
                    logger.warning("高音质独占输出不可用，已回退共享模式")

        self._stream = sd.OutputStream(**stream_kwargs)
        self._stream.start()

    def _default_output_hostapi_name(self):
        try:
            default_output_index = None
            default_device = sd.default.device
            if isinstance(default_device, (list, tuple)) and len(default_device) > 1:
                default_output_index = default_device[1]

            if default_output_index is not None and int(default_output_index) >= 0:
                device_info = sd.query_devices(int(default_output_index))
            else:
                device_info = sd.query_devices(kind="output")

            hostapi_index = device_info.get("hostapi") if device_info else None
            if hostapi_index is None:
                return ""

            hostapis = sd.query_hostapis()
            hostapi = hostapis[int(hostapi_index)]
            return str(hostapi.get("name", "") or "").lower()
        except Exception:
            return ""

    def _close_stream_only(self):
        with self._lock:
            stream = self._stream
            self._stream = None
        if stream is None:
            return True
        try:
            stream.stop()
            stream.close()
            return True
        except Exception:
            logger.exception("关闭音频流失败")
            return False

    def reopen_stream_from_current_buffer(self, keep_pause_state=True):
        if self._audio_data is None or self._total_frames <= 0 or self._sample_rate <= 0:
            return False

        was_paused = bool(self.is_paused)
        self._close_stream_only()
        try:
            self.is_playing = True
            self.is_paused = False
            self._build_stream()
            if keep_pause_state and was_paused:
                self.pause()
            return True
        except Exception:
            logger.exception("重建音频输出流失败")
            self.is_playing = False
            self.is_paused = False
            return False

    def play(self, file_path, start_position=0):
        try:
            decoded_payload = self.prepare_predecoded_audio(file_path)
            return self.play_predecoded(file_path, decoded_payload, start_position=start_position)
        except Exception:
            logger.exception("播放失败")
            self.is_playing = False
            self.is_paused = False
            self._audio_data = None
            return False

    def _normalize_output_device_signature(self, signature):
        if not signature:
            return None
        if isinstance(signature, (list, tuple)) and len(signature) >= 2:
            idx = int(signature[0]) if signature[0] is not None else -1
            name = str(signature[1] or "")
            return idx, name
        return None

    def get_default_output_device_signature(self):
        if self.audio_output_strategy in {"fixed", "fixed_current"} and self.fixed_output_device_signature is not None:
            return self.fixed_output_device_signature

        default_output_index = -1
        try:
            default_device = sd.default.device
            if isinstance(default_device, (list, tuple)) and len(default_device) > 1:
                default_output_index = default_device[1]

            if default_output_index is None or int(default_output_index) < 0:
                device_info = sd.query_devices(kind="output")
                if not device_info:
                    return None
                return (
                    -1,
                    device_info.get("name", ""),
                    device_info.get("hostapi", ""),
                    int(device_info.get("max_output_channels", 0)),
                )

            device_info = sd.query_devices(int(default_output_index))
        except Exception:
            return None

        if not device_info:
            return None

        return (
            int(default_output_index),
            device_info.get("name", ""),
            device_info.get("hostapi", ""),
            int(device_info.get("max_output_channels", 0)),
        )

    def recover_on_device_change(self):
        if not self.is_playing or not self.current_file:
            return False

        now = time.monotonic()
        if now < float(self._suppress_recover_until_monotonic):
            return False
        if now - self._last_recover_attempt_monotonic < self._recover_min_interval_seconds:
            return False
        if self._is_recovering_output_device:
            return False

        latest_signature = self.get_default_output_device_signature()
        if latest_signature is None:
            return False

        latest_normalized = self._normalize_output_device_signature(latest_signature)
        active_normalized = self._normalize_output_device_signature(self._active_output_device_signature)
        if latest_normalized is not None and latest_normalized == active_normalized:
            return False

        self._active_output_device_signature = latest_signature
        resume_ms = int(max(0.0, self.get_position()) * 1000)
        should_restore_pause = self.is_paused
        self._is_recovering_output_device = True
        try:
            self._last_recover_attempt_monotonic = now
            if not self.reopen_stream_from_current_buffer(keep_pause_state=should_restore_pause):
                if not self.play(self.current_file, start_position=resume_ms):
                    return False

            if should_restore_pause:
                self.pause()
            return True
        finally:
            self._is_recovering_output_device = False

    def pause(self):
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self._reset_visual_metrics()
            return True
        return False

    def resume(self):
        if self.is_playing and self.is_paused:
            self.is_paused = False
            return True
        return False

    def stop(self):
        with self._lock:
            self.is_playing = False
            self.is_paused = False
            self._position_frames = 0
            stream = self._stream
            self._stream = None
            self._audio_data = None
            self._current_track_normalize_gain = 1.0
            self._reset_visual_metrics()

        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                logger.exception("关闭音频流失败")
        return True

    def set_volume(self, volume):
        if 0.0 <= volume <= 1.0:
            self.volume = float(volume)
            return True
        return False

    def get_duration(self, file_path):
        if self.current_file == file_path and self._duration_seconds > 0:
            return self._duration_seconds
        try:
            audio = self._decode_audio_segment(file_path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0

    def get_duration_hint(self, file_path):
        if self.current_file == file_path and self._duration_seconds > 0:
            return self._duration_seconds
        try:
            audio = MutagenFile(file_path)
            duration = float(getattr(getattr(audio, "info", None), "length", 0.0) or 0.0)
            if duration > 0:
                return duration
        except Exception:
            pass
        return 0.0

    def get_position(self):
        if self._sample_rate <= 0:
            return 0.0
        return self._position_frames / self._sample_rate

    def seek(self, position_seconds):
        if self._sample_rate <= 0 or self._total_frames <= 0:
            return False
        position_seconds = max(0.0, min(float(position_seconds), self._duration_seconds))
        with self._lock:
            self._position_frames = int(position_seconds * self._sample_rate)
        return True

    def get_visual_intensity(self):
        with self._lock:
            return max(0.0, min(1.0, float(self._visual_intensity)))

    def get_visual_accent(self):
        with self._lock:
            return max(0.0, min(1.0, float(self._visual_accent)))

