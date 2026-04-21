import os


def set_immersive_dark_title_bar(window, enabled):
    """Best-effort Windows title bar dark mode; no-op on unsupported platforms."""
    if window is None:
        return False
    if os.name != "nt":
        return False

    # Offscreen/headless tests should skip platform title bar calls.
    if str(os.environ.get("QT_QPA_PLATFORM", "")).strip().lower() == "offscreen":
        return False

    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return False

    try:
        hwnd = int(window.winId())
    except Exception:
        return False

    if hwnd <= 0:
        return False

    try:
        dwmapi = ctypes.windll.dwmapi
    except Exception:
        return False

    value = ctypes.c_int(1 if enabled else 0)
    size = ctypes.sizeof(value)

    # 20 is preferred on modern Windows; 19 is legacy fallback.
    attributes = (20, 19)
    for attr in attributes:
        try:
            result = dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                wintypes.DWORD(attr),
                ctypes.byref(value),
                wintypes.DWORD(size),
            )
            if int(result) == 0:
                return True
        except Exception:
            continue
    return False

