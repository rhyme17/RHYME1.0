import os
import re
import shutil
import hashlib
from dataclasses import dataclass
from importlib import import_module

try:
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    get_logger = import_module("utils.logging_utils").get_logger

from .asr_offline import (
    DEFAULT_ASR_BEAM_SIZE,
    DEFAULT_ASR_MODEL_SIZE,
    DEFAULT_ASR_VAD_FILTER,
    asr_available,
    transcribe_file_to_lrc_safe,
)
from .lyrics_online_gequbao import GequbaoLyricsClient
from .lrc_parser import parse_lrc_file


_SAFE_NAME_PATTERN = re.compile(r"[^\w\-\u4e00-\u9fff ]+")
_HEX_NAME_PATTERN = re.compile(r"^[a-fA-F0-9]{32,64}$")
_MANAGED_LRC_MARK = "[re:RHYME-ASR]"
logger = get_logger(__name__)


@dataclass
class LyricsResolveResult:
    lines: list
    source: str
    file_path: str
    pending_asr: bool


class LyricsService:
    def __init__(
        self,
        cache_dir,
        asr_model_size=DEFAULT_ASR_MODEL_SIZE,
        asr_language="zh",
        asr_device="cpu",
        asr_compute_type="float32",
        asr_beam_size=DEFAULT_ASR_BEAM_SIZE,
        asr_vad_filter=DEFAULT_ASR_VAD_FILTER,
        online_lyrics_enabled=True,
        online_lyrics_timeout_seconds=12,
    ):
        self.cache_dir = cache_dir
        self.asr_model_size = asr_model_size
        self.asr_language = asr_language
        self.asr_device = asr_device
        self.asr_compute_type = asr_compute_type
        self.asr_beam_size = asr_beam_size
        self.asr_vad_filter = asr_vad_filter
        self.online_lyrics_enabled = bool(online_lyrics_enabled)
        self._asr_available_cache = None
        os.makedirs(self.cache_dir, exist_ok=True)
        self.online_lyrics_debug_dir = os.path.join(self.cache_dir, "debug_online")
        self.online_lyrics_client = GequbaoLyricsClient(
            timeout_seconds=online_lyrics_timeout_seconds,
            debug_dir=self.online_lyrics_debug_dir,
        )
        self._instrumental_guard_song_ids = set()

    def resolve_for_song(self, song):
        song_id = song.get("id", "")
        local_path = self._find_local_lrc(song)
        if local_path:
            lines, _ = self._safe_parse_lrc(local_path)
            if lines:
                logger.debug("命中本地歌词: song_id=%s path=%s", song_id, local_path)
                return LyricsResolveResult(lines=lines, source="local", file_path=local_path, pending_asr=False)

        cache_path = self.get_cache_lrc_path(song)
        if os.path.exists(cache_path):
            lines, _ = self._safe_parse_lrc(cache_path)
            if lines:
                self.export_cache_lyrics_to_song_dir(song, cache_path)
                logger.debug("命中缓存歌词: song_id=%s path=%s", song_id, cache_path)
                return LyricsResolveResult(
                    lines=lines,
                    source="asr-cache",
                    file_path=cache_path,
                    pending_asr=self._asr_available(),
                )

        logger.debug("未找到歌词: song_id=%s", song_id)
        return LyricsResolveResult(lines=[], source="none", file_path="", pending_asr=self._asr_available())

    def get_cache_lrc_path(self, song):
        song_id = song.get("id") or self._fallback_song_id(song)
        return os.path.join(self.cache_dir, f"{song_id}.lrc")

    def generate_lrc_with_asr(self, song):
        try:
            audio_path = song.get("path", "")
            song_id = song.get("id", "")
            if not audio_path or not os.path.exists(audio_path):
                return False, "", "音频文件不存在"

            if song_id and song_id in self._instrumental_guard_song_ids:
                return False, "", "疑似纯音乐，已跳过重复识别（本次运行）"

            output_path = self.get_cache_lrc_path(song)
            success, error_message = transcribe_file_to_lrc_safe(
                audio_path=audio_path,
                lrc_output_path=output_path,
                model_size=self.asr_model_size,
                language=self.asr_language,
                device=self.asr_device,
                compute_type=self.asr_compute_type,
                beam_size=self.asr_beam_size,
                vad_filter=self.asr_vad_filter,
            )
            if not success:
                logger.warning("ASR生成歌词失败: song_id=%s error=%s", song_id, error_message)
                if song_id and "疑似纯音乐" in str(error_message or ""):
                    self._instrumental_guard_song_ids.add(song_id)
                return False, "", error_message
            self.export_cache_lyrics_to_song_dir(song, output_path)
            logger.info("ASR生成歌词成功: song_id=%s output=%s", song_id, output_path)
            return True, output_path, ""
        except Exception as exc:
            logger.exception("ASR生成歌词异常")
            return False, "", f"离线歌词识别异常: {exc}"

    def try_fetch_online_lrc(self, song):
        if not self.online_lyrics_enabled:
            return False, "", "在线歌词获取已关闭"

        audio_path = str(song.get("path", "") or "")
        if not audio_path:
            return False, "", "音频文件路径无效"

        query_title = str(song.get("title", "") or "").strip()
        if not query_title:
            query_title = os.path.splitext(os.path.basename(audio_path))[0].strip()
        query_artist = str(song.get("artist", "") or "").strip()

        result = self.online_lyrics_client.fetch(query_title, query_artist)
        if not result.success:
            error = str(result.error or "在线歌词获取失败")
            if result.debug_search_path or result.debug_detail_path:
                debug_files = [path for path in (result.debug_search_path, result.debug_detail_path) if path]
                error = f"{error}（debug: {'; '.join(debug_files)}）"
            return False, "", error

        cache_path = self.get_cache_lrc_path(song)
        with open(cache_path, "w", encoding="utf-8") as handler:
            handler.write((result.lrc_text or "").strip() + "\n")

        # 统一通过托管导出路径落盘，避免同一首歌生成多份命名不同的歌词文件。
        target_path = self.export_cache_lyrics_to_song_dir(song, cache_path)
        if not target_path:
            return False, "", "在线歌词获取成功，但写入本地歌词失败"

        return True, target_path, ""

    def find_local_lrc(self, song):
        """公开本地歌词查找接口，供 UI 层安全调用。"""
        return self._find_local_lrc(song)

    def parse_lrc_safe(self, file_path):
        """公开安全解析接口，统一异常处理策略。"""
        return self._safe_parse_lrc(file_path)

    def export_cache_lyrics_to_song_dir(self, song, cache_lrc_path):
        audio_path = song.get("path", "")
        if not audio_path or not os.path.exists(cache_lrc_path):
            return ""

        song_dir = os.path.dirname(audio_path)
        lyrics_dir = os.path.join(song_dir, "lyrics")
        os.makedirs(lyrics_dir, exist_ok=True)

        title = self._resolve_export_title(song, audio_path)
        target_path = os.path.join(lyrics_dir, f"{title}.lrc")

        # 仅覆盖由程序托管导出的歌词，保留用户手动修订的同名文件。
        if os.path.exists(target_path):
            if self._is_managed_lrc(target_path):
                self._write_managed_lrc(cache_lrc_path, target_path)
                logger.debug("覆盖托管歌词文件: %s", target_path)
            return target_path

        self._write_managed_lrc(cache_lrc_path, target_path)
        logger.debug("导出歌词到歌曲目录: %s", target_path)
        return target_path

    def _is_managed_lrc(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as handler:
                head = handler.readline().strip()
            return head == _MANAGED_LRC_MARK
        except Exception:
            return False

    def _write_managed_lrc(self, source_path, target_path):
        try:
            with open(source_path, "r", encoding="utf-8", errors="replace") as src:
                content = src.read()
        except Exception:
            shutil.copyfile(source_path, target_path)
            return

        normalized = content.lstrip("\ufeff")
        if normalized.startswith(_MANAGED_LRC_MARK):
            payload = normalized
        else:
            payload = f"{_MANAGED_LRC_MARK}\n{normalized}"

        with open(target_path, "w", encoding="utf-8") as dst:
            dst.write(payload)

    def _resolve_export_title(self, song, audio_path):
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        title = self._safe_filename(song.get("title", ""))
        if not title:
            return audio_name
        if self._looks_like_hash_name(title):
            return audio_name
        if self._looks_like_mojibake(title):
            return audio_name
        return title

    def current_line_index(self, lines, position_ms):
        if not lines:
            return -1

        left = 0
        right = len(lines) - 1
        answer = -1
        while left <= right:
            mid = (left + right) // 2
            if lines[mid].time_ms <= position_ms:
                answer = mid
                left = mid + 1
            else:
                right = mid - 1
        return answer

    def _find_local_lrc(self, song):
        audio_path = song.get("path", "")
        if not audio_path:
            return ""

        song_dir = os.path.dirname(audio_path)
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        title_filename = self._safe_filename(song.get("title", ""))

        candidates = [
            os.path.join(song_dir, f"{audio_name}.lrc"),
            os.path.join(song_dir, "lyrics", f"{audio_name}.lrc"),
        ]

        if title_filename:
            candidates.extend(
                [
                    os.path.join(song_dir, f"{title_filename}.lrc"),
                    os.path.join(song_dir, "lyrics", f"{title_filename}.lrc"),
                ]
            )

        title = self._safe_text(song.get("title", ""))
        artist = self._safe_text(song.get("artist", ""))
        if title and artist:
            candidates.extend(
                [
                    os.path.join(song_dir, f"{title} - {artist}.lrc"),
                    os.path.join(song_dir, f"{artist} - {title}.lrc"),
                    os.path.join(song_dir, "lyrics", f"{title} - {artist}.lrc"),
                    os.path.join(song_dir, "lyrics", f"{artist} - {title}.lrc"),
                ]
            )

        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return ""

    def _safe_text(self, value):
        text = str(value or "").strip()
        if not text:
            return ""
        return _SAFE_NAME_PATTERN.sub("", text).strip()

    def _safe_filename(self, value):
        text = str(value or "").strip()
        if not text:
            return ""
        # Windows 不允许的文件名字符。
        text = re.sub(r'[<>:"/\\|?*]', "_", text)
        return text.strip(" .")

    def _looks_like_hash_name(self, text):
        return bool(_HEX_NAME_PATTERN.fullmatch((text or "").strip()))

    def _looks_like_mojibake(self, text):
        markers = "ÃÂÐÑÄÅÆÇÈÉÊËÌÍÎÏÒÓÔÕÖØÙÚÛÜÝÞßæåçèéêëìíîïðñòóôõöøùúûüÿ"
        value = text or ""
        return any(ch in markers for ch in value) or "�" in value

    def _fallback_song_id(self, song):
        path = os.path.abspath(song.get("path", "") or "")
        title = str(song.get("title", "") or "")
        raw = f"{path.lower()}|{title}".encode("utf-8", errors="ignore")
        return hashlib.md5(raw).hexdigest()

    def _safe_parse_lrc(self, file_path):
        try:
            return parse_lrc_file(file_path)
        except Exception:
            return [], {}

    def _asr_available(self):
        if self._asr_available_cache is None:
            self._asr_available_cache = asr_available()
        return self._asr_available_cache

    def is_asr_available(self):
        """向界面层暴露离线歌词识别能力检查，保持与现有调用一致。"""
        return bool(self._asr_available())


