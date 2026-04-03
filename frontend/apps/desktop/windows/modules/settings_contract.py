AUDIO_OUTPUT_STRATEGIES = ("follow_system", "fixed_current")
VOLUME_UNIFORMITY_LEVELS = ("off", "light", "medium", "strong")

_AUDIO_OUTPUT_STRATEGY_ALIASES = {
    "fixed": "fixed_current",
}

_VOLUME_UNIFORMITY_ALIASES = {
    "low": "light",
    "high": "strong",
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

