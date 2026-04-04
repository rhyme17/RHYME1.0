import os
import hashlib
import re
from mutagen import File

try:
    from frontend.utils.logging_utils import get_logger
except ModuleNotFoundError:
    from utils.logging_utils import get_logger


logger = get_logger(__name__)

class MusicLibrary:
    def __init__(self):
        self.songs = []
        self.supported_formats = {'.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a'}
        self.last_scan_cancelled = False
        self.last_scan_error = ""
    
    def scan_music(self, directory, should_stop=None, on_progress=None):
        """扫描指定目录下的音乐文件"""
        self.songs = []
        self.last_scan_cancelled = False
        self.last_scan_error = ""

        def _is_cancelled():
            if not callable(should_stop):
                return False
            try:
                return bool(should_stop())
            except Exception:
                return False

        def _report_progress(scanned_count, total_count):
            if not callable(on_progress):
                return
            try:
                on_progress(int(scanned_count), int(total_count))
            except Exception:
                return

        def _walk_error(error):
            logger.warning("跳过不可访问目录: %s", error)

        try:
            discovered_total = 0
            scanned_count = 0
            for root, dirs, files in os.walk(directory, onerror=_walk_error):
                if _is_cancelled():
                    self.last_scan_cancelled = True
                    return False
                dirs.sort(key=lambda value: str(value).lower())
                files.sort(key=lambda value: str(value).lower())
                for file in files:
                    if _is_cancelled():
                        self.last_scan_cancelled = True
                        return False
                    extension = os.path.splitext(file)[1].lower()
                    if extension not in self.supported_formats:
                        continue
                    discovered_total += 1
                    file_path = os.path.join(root, file)
                    file_path = os.path.abspath(file_path)
                    song_info = self._extract_song_info(file_path)
                    self.songs.append(song_info)
                    scanned_count += 1
                    _report_progress(scanned_count, discovered_total)
            return True
        except Exception as e:
            self.last_scan_error = str(e)
            logger.exception("扫描音乐失败")
            return False
    
    def _extract_song_info(self, file_path):
        """从音频文件中提取元数据"""
        raw_filename_title = os.path.splitext(os.path.basename(file_path))[0]
        cleaned_filename_title = self._strip_track_number_prefix(raw_filename_title)
        cleaned_filename_title = self._strip_bracketed_chunks(cleaned_filename_title)
        default_title = self._normalize_text(cleaned_filename_title, '未知歌曲')
        default_artist = '未知艺术家'
        default_album = self._normalize_text(os.path.basename(os.path.dirname(file_path)), '未知专辑')

        title = default_title
        artist = default_artist
        album = default_album
        duration = 0.0

        try:
            # easy=True 优先读取常见标签，兼容性更好。
            audio = File(file_path, easy=True)
            if audio:
                artist = self._normalize_text(audio.get('artist', [default_artist])[0], default_artist)
                album = self._normalize_text(audio.get('album', [default_album])[0], default_album)
                artist = self._prefer_fallback_text(artist, default_artist)
                album = self._prefer_fallback_text(album, default_album)
                duration = float(getattr(getattr(audio, 'info', None), 'length', 0.0) or 0.0)
        except Exception:
            # 标签读取失败时保留默认值，不中断后续时长回退。
            pass

        title = self._strip_artist_from_title(title, artist)

        if duration <= 0:
            try:
                # easy=False 对部分文件的时长识别更稳定。
                full_audio = File(file_path)
                duration = float(getattr(getattr(full_audio, 'info', None), 'length', 0.0) or 0.0)
            except Exception:
                duration = 0.0

        return {
            'id': hashlib.md5(file_path.lower().encode('utf-8')).hexdigest(),
            'title': title,
            'artist': artist,
            'album': album,
            'path': file_path,
            'duration': max(0.0, duration)
        }

    def _strip_artist_from_title(self, title, artist):
        raw_title = str(title or '').strip()
        if not raw_title:
            return raw_title

        artist_tokens = self._artist_tokens(artist)
        if not artist_tokens:
            return raw_title

        parts = [p.strip() for p in re.split(r"\s*[-_–—|]+\s*", raw_title) if p.strip()]
        if len(parts) <= 1:
            return raw_title

        remaining = [p for p in parts if not self._is_artist_text(p, artist_tokens)]
        if not remaining:
            return raw_title
        if len(remaining) == len(parts):
            return raw_title
        return " - ".join(remaining).strip() or raw_title

    @staticmethod
    def _strip_track_number_prefix(title):
        text = str(title or '').strip()
        if not text:
            return text

        # 常见文件名前缀：01.、01-、01_、01、等
        text = re.sub(r"^\s*(?:track\s*)?\d{1,3}\s*[\-._、:：)\]]+\s*", "", text, flags=re.IGNORECASE)
        # 仅当是前导 0 的编号时再移除纯空格分隔，避免误伤如“7 rings”
        text = re.sub(r"^\s*0\d{1,2}\s+", "", text)
        return text.strip()

    @staticmethod
    def _strip_bracketed_chunks(title):
        text = str(title or '').strip()
        if not text:
            return text

        # 连续清理一轮，覆盖常见中英文括号内容。
        patterns = [
            r"\([^()]*\)",
            r"\[[^\[\]]*\]",
            r"\{[^{}]*\}",
            r"（[^（）]*）",
            r"【[^【】]*】",
            r"〔[^〔〕]*〕",
            r"《[^《》]*》",
            r"〈[^〈〉]*〉",
        ]
        for pattern in patterns:
            text = re.sub(pattern, " ", text)

        text = re.sub(r"\s{2,}", " ", text)
        return text.strip(" -_")

    def _artist_tokens(self, artist):
        raw = str(artist or '').strip()
        if not raw:
            return []
        chunks = [c.strip() for c in re.split(r"[/,，;&、]", raw) if c.strip()]
        tokens = []
        for item in chunks:
            normalized = self._normalize_for_compare(item)
            if normalized:
                tokens.append(normalized)
        return tokens

    @staticmethod
    def _normalize_for_compare(text):
        return ''.join(ch.lower() for ch in str(text or '') if ch.isalnum() or ('\u4e00' <= ch <= '\u9fff'))

    def _is_artist_text(self, text, artist_tokens):
        normalized = self._normalize_for_compare(text)
        if not normalized:
            return False
        for token in artist_tokens:
            if not token:
                continue
            if normalized == token:
                return True
            if token in normalized or normalized in token:
                return True
        return False
    
    def search(self, query):
        """根据查询词搜索音乐"""
        if not query:
            return self.songs
        
        query = query.lower()
        results = []
        for song in self.songs:
            if (query in song['title'].lower() or 
                query in song['artist'].lower() or 
                query in song['album'].lower()):
                results.append(song)
        return results
    
    def get_artists(self):
        """获取所有艺术家列表"""
        artists = {}
        for song in self.songs:
            artist = song['artist']
            if artist not in artists:
                artists[artist] = []
            artists[artist].append(song)
        return artists
    
    def get_albums(self):
        """获取所有专辑列表"""
        albums = {}
        for song in self.songs:
            album = song['album']
            if album not in albums:
                albums[album] = []
            albums[album].append(song)
        return albums
    
    def get_songs_by_artist(self, artist):
        """获取指定艺术家的歌曲"""
        return [song for song in self.songs if song['artist'] == artist]
    
    def get_songs_by_album(self, album):
        """获取指定专辑的歌曲"""
        return [song for song in self.songs if song['album'] == album]

    def _normalize_text(self, value, fallback):
        if value is None:
            return fallback

        if isinstance(value, bytes):
            value = self._decode_bytes_best_effort(value)

        text = str(value).replace('\x00', '').strip()
        if not text:
            text = fallback

        repaired = self._repair_mojibake(text)
        return repaired if repaired else fallback

    def _decode_bytes_best_effort(self, value):
        if not isinstance(value, bytes):
            return value

        candidates = []
        for enc in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'gb18030', 'gbk', 'big5', 'cp1252', 'latin1'):
            try:
                decoded = value.decode(enc)
            except Exception:
                continue
            decoded = decoded.replace('\x00', '').strip()
            if decoded:
                candidates.append(decoded)

        if not candidates:
            return value.decode('utf-8', errors='ignore').replace('\x00', '').strip()

        return max(candidates, key=self._text_quality)

    def _prefer_fallback_text(self, text, fallback):
        source = str(text or '').strip()
        target = str(fallback or '').strip()
        if not source:
            return target or source
        if not target:
            return source
        if not self._looks_like_mojibake(source):
            return source
        return target if self._text_quality(target) > self._text_quality(source) else source

    def _looks_like_mojibake(self, text):
        markers = "ÃÂÐÑÄÅÆÇÈÉÊËÌÍÎÏÒÓÔÕÖØÙÚÛÜÝÞßæåçèéêëìíîïðñòóôõöøùúûüÿ"
        has_marker = any(ch in markers for ch in text)
        has_replacement = '�' in text
        has_c1_control = any(0x80 <= ord(ch) <= 0x9F for ch in text)
        return has_marker or has_replacement or has_c1_control

    def _repair_mojibake(self, text):
        if not text or not self._looks_like_mojibake(text):
            return text

        candidates = [text]
        utf8_pairs = (
            ('latin1', 'utf-8'),
            ('cp1252', 'utf-8'),
        )
        legacy_pairs = (
            ('latin1', 'gb18030'),
            ('cp1252', 'gb18030'),
            ('latin1', 'gbk'),
            ('cp1252', 'gbk'),
        )

        utf8_candidates = []
        for src, target in utf8_pairs:
            try:
                candidate = text.encode(src).decode(target)
            except Exception:
                continue
            candidate = candidate.replace('\x00', '').strip()
            if candidate:
                candidates.append(candidate)
                utf8_candidates.append(candidate)

        if utf8_candidates:
            best_utf8 = max(utf8_candidates, key=self._text_quality)
            if self._text_quality(best_utf8) > self._text_quality(text):
                return best_utf8

        for src, target in legacy_pairs:
            try:
                candidate = text.encode(src).decode(target)
            except Exception:
                continue
            candidate = candidate.replace('\x00', '').strip()
            if not candidate:
                continue
            if self._is_suspicious_transcode_result(text, candidate):
                continue
            candidates.append(candidate)

        best = max(candidates, key=self._text_quality)
        return best if self._text_quality(best) > self._text_quality(text) else text

    def _is_suspicious_transcode_result(self, source_text, candidate_text):
        source = str(source_text or '').strip()
        candidate = str(candidate_text or '').strip()
        if not candidate:
            return True
        if len(source) >= 4 and len(set(source)) == 1 and len(candidate) <= 2:
            return True
        if len(source) >= 4 and len(candidate) >= 2 and len(set(candidate)) == 1:
            return True
        return False

    def _text_quality(self, text):
        cjk = sum('\u4e00' <= ch <= '\u9fff' for ch in text)
        replacement = text.count('�')
        weird = sum(ch in "ÃÂÐÑÄÅÆÇÈÉÊËÌÍÎÏÒÓÔÕÖØÙÚÛÜÝÞß" for ch in text)
        c1_control = sum(0x80 <= ord(ch) <= 0x9F for ch in text)
        printable = sum(ch.isprintable() for ch in text)
        alpha_num = sum(ch.isalnum() for ch in text)
        return cjk, alpha_num, printable, -replacement, -weird, -c1_control
