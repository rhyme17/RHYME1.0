import re
from dataclasses import dataclass


TIMESTAMP_PATTERN = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?]")
META_PATTERN = re.compile(r"^\[([a-zA-Z]+):(.*)]$")


@dataclass
class LyricLine:
    time_ms: int
    text: str


def _to_milliseconds(minutes_text, seconds_text, fraction_text):
    minutes = int(minutes_text)
    seconds = int(seconds_text)
    fraction = fraction_text or "0"
    if len(fraction) == 1:
        millis = int(fraction) * 100
    elif len(fraction) == 2:
        millis = int(fraction) * 10
    else:
        millis = int(fraction[:3])
    return minutes * 60 * 1000 + seconds * 1000 + millis


def parse_lrc_text(content):
    lines = []
    metadata = {}

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        meta_match = META_PATTERN.match(line)
        if meta_match and not TIMESTAMP_PATTERN.search(line):
            metadata[meta_match.group(1).lower()] = meta_match.group(2).strip()
            continue

        matches = list(TIMESTAMP_PATTERN.finditer(line))
        if not matches:
            continue

        lyric_text = TIMESTAMP_PATTERN.sub("", line).strip()
        for match in matches:
            time_ms = _to_milliseconds(match.group(1), match.group(2), match.group(3))
            lines.append(LyricLine(time_ms=time_ms, text=lyric_text))

    lines.sort(key=lambda item: item.time_ms)
    return lines, metadata


def parse_lrc_file(file_path):
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            with open(file_path, "r", encoding=encoding) as handler:
                content = handler.read()
            parsed_lines, metadata = parse_lrc_text(content)
            if parsed_lines:
                return parsed_lines, metadata
        except Exception as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    return [], {}


def format_timestamp(time_ms):
    total_ms = max(0, int(time_ms))
    minutes = total_ms // 60000
    seconds = (total_ms % 60000) // 1000
    centiseconds = (total_ms % 1000) // 10
    return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"


