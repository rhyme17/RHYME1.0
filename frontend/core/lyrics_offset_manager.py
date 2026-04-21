import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

try:
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.logging_utils import get_logger


logger = get_logger(__name__)


@dataclass
class LyricsOffset:
    song_id: str
    offset_ms: int


class LyricsOffsetManager:
    DEFAULT_OFFSET_FILE = "lyrics_offsets.json"

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.offset_file = os.path.join(cache_dir, self.DEFAULT_OFFSET_FILE)
        self._offsets: Dict[str, int] = {}
        self._load_offsets()

    def _load_offsets(self):
        if not os.path.exists(self.offset_file):
            self._offsets = {}
            return

        try:
            with open(self.offset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._offsets = {str(k): int(v) for k, v in data.items() if isinstance(v, (int, float))}
            logger.info("已加载 %d 个歌词偏移量", len(self._offsets))
        except Exception as exc:
            logger.warning("加载歌词偏移量失败: %s", exc)
            self._offsets = {}

    def _save_offsets(self):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.offset_file, "w", encoding="utf-8") as f:
                json.dump(self._offsets, f, ensure_ascii=False, indent=2)
            logger.debug("已保存 %d 个歌词偏移量", len(self._offsets))
        except Exception as exc:
            logger.warning("保存歌词偏移量失败: %s", exc)

    def get_offset(self, song_id: str) -> int:
        return self._offsets.get(str(song_id), 0)

    def set_offset(self, song_id: str, offset_ms: int):
        song_id = str(song_id)
        offset_ms = int(offset_ms)
        if offset_ms == 0:
            self._offsets.pop(song_id, None)
        else:
            self._offsets[song_id] = offset_ms
        self._save_offsets()

    def adjust_offset(self, song_id: str, delta_ms: int) -> int:
        current = self.get_offset(song_id)
        new_offset = current + delta_ms
        max_offset = 30000
        new_offset = max(-max_offset, min(max_offset, new_offset))
        self.set_offset(song_id, new_offset)
        return new_offset

    def reset_offset(self, song_id: str):
        song_id = str(song_id)
        self._offsets.pop(song_id, None)
        self._save_offsets()

    def clear_all_offsets(self):
        self._offsets = {}
        self._save_offsets()
