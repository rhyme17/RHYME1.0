AUDIO_OUTPUT_STRATEGIES = ("follow_system", "fixed_current")
VOLUME_UNIFORMITY_LEVELS = ("off", "light", "medium", "strong")
UI_THEMES = ("light", "dark")
UI_FONT_WEIGHTS = ("light", "regular", "medium")
LYRICS_FONT_SIZE_RANGE = (12, 28)

_AUDIO_OUTPUT_STRATEGY_ALIASES = {
    "fixed": "fixed_current",
}

_VOLUME_UNIFORMITY_ALIASES = {
    "low": "light",
    "high": "strong",
}

_UI_THEME_ALIASES = {
    "default": "light",
}

_UI_FONT_WEIGHT_ALIASES = {
    "normal": "regular",
}


def clamp_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except Exception:
        parsed = int(default)
    return max(int(minimum), min(int(maximum), parsed))


def normalize_audio_output_strategy(value, default="follow_system"):
    candidate = str(value or default).strip().lower()
    candidate = _AUDIO_OUTPUT_STRATEGY_ALIASES.get(candidate, candidate)
    if candidate not in AUDIO_OUTPUT_STRATEGIES:
        return default
    return candidate


def normalize_volume_uniformity_level(value, default="medium"):
    candidate = str(value or default).strip().lower()
    candidate = _VOLUME_UNIFORMITY_ALIASES.get(candidate, candidate)
    if candidate not in VOLUME_UNIFORMITY_LEVELS:
        return default
    return candidate


def normalize_ui_theme(value, default="light"):
    candidate = str(value or default).strip().lower()
    candidate = _UI_THEME_ALIASES.get(candidate, candidate)
    if candidate not in UI_THEMES:
        return default
    return candidate


def normalize_ui_font_weight(value, default="regular"):
    candidate = str(value or default).strip().lower()
    candidate = _UI_FONT_WEIGHT_ALIASES.get(candidate, candidate)
    if candidate not in UI_FONT_WEIGHTS:
        return default
    return candidate


def normalize_lyrics_font_size(value, default=18):
    minimum, maximum = LYRICS_FONT_SIZE_RANGE
    try:
        parsed = int(value)
    except Exception:
        parsed = int(default)
    return max(int(minimum), min(int(maximum), parsed))


