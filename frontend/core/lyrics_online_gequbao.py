import html
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests


BASE_URL = "https://www.gequbao.com"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
    ),
    "Referer": "https://www.gequbao.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


@dataclass
class OnlineLyricsFetchResult:
    success: bool
    lrc_text: str
    song_name: str
    artist: str
    detail_url: str
    error: str
    debug_search_path: str = ""
    debug_detail_path: str = ""


class GequbaoLyricsClient:
    def __init__(self, *, base_url=BASE_URL, timeout_seconds=12, session=None, debug_dir=""):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = int(timeout_seconds)
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.debug_dir = debug_dir or ""

    def fetch(self, song_name, artist=""):
        clean_song = str(song_name or "").strip()
        clean_artist = str(artist or "").strip()
        if not clean_song:
            return OnlineLyricsFetchResult(False, "", "", "", "", "歌曲名称为空")

        keywords = [clean_song]
        if clean_artist and clean_artist != "无":
            keywords = [f"{clean_song} {clean_artist}", clean_song]

        last_error = "在线歌词获取失败"
        for keyword in keywords:
            result = self._fetch_by_keyword(keyword)
            if result.success:
                return result
            last_error = result.error or last_error

        return OnlineLyricsFetchResult(False, "", "", "", "", last_error)

    def _fetch_by_keyword(self, keyword):
        search_page_url = self._search_song(keyword)
        if not search_page_url:
            return OnlineLyricsFetchResult(False, "", "", "", "", f"搜索失败: {keyword}")

        try:
            search_resp = self.session.get(search_page_url, timeout=self.timeout_seconds)
            search_resp.raise_for_status()
            search_html = search_resp.text
        except Exception as exc:
            return OnlineLyricsFetchResult(False, "", "", "", "", f"获取搜索结果失败: {exc}")

        detail_url = self._extract_detail_url_from_search_page(search_html)
        if not detail_url:
            debug_search = self._write_debug_file("debug_search.html", search_html)
            return OnlineLyricsFetchResult(
                False,
                "",
                "",
                "",
                "",
                "未找到歌曲详情页链接",
                debug_search_path=debug_search,
            )

        try:
            detail_resp = self.session.get(detail_url, timeout=self.timeout_seconds)
            detail_resp.raise_for_status()
            detail_html = detail_resp.text
        except Exception as exc:
            return OnlineLyricsFetchResult(False, "", "", "", "", f"获取歌词详情页失败: {exc}")

        lrc_text = self._extract_lrc_from_html(detail_html)
        if not lrc_text:
            debug_search = self._write_debug_file("debug_search.html", search_html)
            debug_detail = self._write_debug_file("debug_detail.html", detail_html)
            return OnlineLyricsFetchResult(
                False,
                "",
                "",
                "",
                detail_url,
                "未在详情页提取到歌词",
                debug_search_path=debug_search,
                debug_detail_path=debug_detail,
            )

        song_name, artist = self._extract_song_info_from_html(detail_html)
        return OnlineLyricsFetchResult(True, lrc_text, song_name, artist, detail_url, "")

    def _search_song(self, keyword):
        url = urljoin(f"{self.base_url}/", "/api/s")
        try:
            resp = self.session.post(url, data={"keyword": keyword}, timeout=self.timeout_seconds)
            resp.raise_for_status()
            result = resp.json()
        except Exception:
            return ""

        if result.get("code") != 1:
            return ""
        search_path = (((result.get("data") or {}).get("u")) or "").strip()
        if not search_path:
            return ""
        return urljoin(f"{self.base_url}/", search_path)

    def _extract_detail_url_from_search_page(self, html_text):
        pattern = r'<a[^>]*href=["\'](/music/\d+)["\']'
        matches = re.findall(pattern, html_text or "")
        if matches:
            return urljoin(f"{self.base_url}/", matches[0])

        pattern2 = r'href=["\'](/(?:song|music)/[^"\']+)["\']'
        matches2 = re.findall(pattern2, html_text or "")
        if matches2:
            return urljoin(f"{self.base_url}/", matches2[0])
        return ""

    def _extract_lrc_from_html(self, html_text):
        patterns = (
            r'<div[^>]*\sid=["\']content-lrc["\'][^>]*>(.*?)</div>',
            r'<div[^>]*class=["\']content-lrc["\'][^>]*>(.*?)</div>',
        )
        for pattern in patterns:
            match = re.search(pattern, html_text or "", re.DOTALL)
            if not match:
                continue
            lrc_html = match.group(1)
            lrc = lrc_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            lrc = re.sub(r"<[^>]+>", "", lrc)
            lrc = html.unescape(lrc)
            lines = [line.strip() for line in lrc.split("\n") if line.strip()]
            cleaned = "\n".join(lines)
            if cleaned:
                return cleaned
        return ""

    def _extract_song_info_from_html(self, html_text):
        app_data_pattern = r'window\.appData\s*=\s*JSON\.parse\([\'\"](.+?)[\'\"]\)'
        app_match = re.search(app_data_pattern, html_text or "")
        if app_match:
            app_data_str = app_match.group(1)
            try:
                app_data_str = app_data_str.encode().decode("unicode_escape")
                app_data = json.loads(app_data_str)
                song_name = str(app_data.get("mp3_title", "") or "").strip()
                artist = str(app_data.get("mp3_author", "") or "").strip()
                if song_name and artist:
                    return song_name, artist
            except Exception:
                pass

        title_pattern = r'<h1[^>]*class="[^"]*badge[^"]*"[^>]*>(.*?)</h1>'
        title_match = re.search(title_pattern, html_text or "", re.DOTALL)
        if title_match:
            full_title = title_match.group(1).strip()
            if "-" in full_title:
                left, right = full_title.split("-", 1)
                return left.strip(), right.strip()

        return "未知歌曲", "未知歌手"

    def _write_debug_file(self, filename, content):
        if not self.debug_dir:
            return ""
        try:
            os.makedirs(self.debug_dir, exist_ok=True)
            path = os.path.join(self.debug_dir, filename)
            with open(path, "w", encoding="utf-8") as handler:
                handler.write(content or "")
            return path
        except Exception:
            return ""



