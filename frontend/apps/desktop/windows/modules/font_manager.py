import os
from PyQt5.QtGui import QFontDatabase


class FontManager:
    FONT_WEIGHT_TO_SUFFIX = {
        "light": "Light",
        "regular": "Regular",
        "medium": "Medium",
    }

    FONT_WEIGHT_TO_CSS = {
        "light": 300,
        "regular": 400,
        "medium": 500,
    }

    def __init__(self):
        self._font_registry = {}
        self._current_font_weight = "regular"
        self._current_css_rule = ""

    def resolve_font_dir_candidates(self):
        current_file = os.path.abspath(__file__)
        module_dir = os.path.dirname(current_file)
        frontend_dir = os.path.abspath(os.path.join(module_dir, "..", "..", "..", ".."))
        project_root = os.path.abspath(os.path.join(frontend_dir, ".."))
        return [
            os.path.join(frontend_dir, "assets", "fonts", "TTF"),
            os.path.join(project_root, "frontend", "assets", "fonts", "TTF"),
            os.path.join(project_root, "assets", "fonts", "TTF"),
        ]

    def resolve_font_file_pair(self, weight):
        suffix = self.FONT_WEIGHT_TO_SUFFIX.get(weight, "Regular")
        filenames = [
            f"JetBrainsMono-{suffix}.ttf",
            f"LXGWWenKaiGB-{suffix}.ttf",
        ]
        for base_dir in self.resolve_font_dir_candidates():
            if not os.path.isdir(base_dir):
                continue
            jet_path = os.path.join(base_dir, filenames[0])
            kai_path = os.path.join(base_dir, filenames[1])
            if os.path.isfile(jet_path) and os.path.isfile(kai_path):
                return jet_path, kai_path
        return "", ""

    def register_font(self, font_file_path):
        if not font_file_path or not os.path.isfile(font_file_path):
            return ""
        cached = self._font_registry.get(font_file_path)
        if cached:
            return cached
        font_id = QFontDatabase.addApplicationFont(font_file_path)
        if font_id < 0:
            return ""
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            return ""
        family = str(families[0] or "").strip()
        if family:
            self._font_registry[font_file_path] = family
        return family

    def apply_font(self, font_weight="regular"):
        normalized_weight = self._normalize_font_weight(font_weight)
        self._current_font_weight = normalized_weight
        jet_file, kai_file = self.resolve_font_file_pair(normalized_weight)
        jet_family = self.register_font(jet_file)
        kai_family = self.register_font(kai_file)
        if jet_family and kai_family:
            css_weight = int(self.FONT_WEIGHT_TO_CSS.get(normalized_weight, 400))
            self._current_css_rule = (
                "QWidget {"
                f" font-family: '{jet_family}', '{kai_family}';"
                f" font-weight: {css_weight};"
                " }"
            )
        else:
            self._current_css_rule = ""
        return self._current_css_rule

    def get_current_css_rule(self):
        return self._current_css_rule

    def _normalize_font_weight(self, value):
        candidate = str(value or "regular").strip().lower()
        if candidate not in ("light", "regular", "medium"):
            return "regular"
        return candidate