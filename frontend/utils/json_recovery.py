import os
from datetime import datetime
from shutil import copy2


def prune_corrupted_backups(directory, filename, keep_latest=10):
    try:
        entries = []
        prefix = f"{filename}.corrupt-"
        suffix = ".bak"
        for name in os.listdir(directory):
            if not (name.startswith(prefix) and name.endswith(suffix)):
                continue
            full_path = os.path.join(directory, name)
            if os.path.isfile(full_path):
                entries.append(full_path)

        entries.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for stale_path in entries[max(0, int(keep_latest)):]:
            try:
                os.remove(stale_path)
            except Exception:
                continue
    except Exception:
        return


def backup_corrupted_file(path, keep_latest=10):
    if not path or not os.path.exists(path):
        return ""

    directory = os.path.dirname(os.path.abspath(path)) or "."
    filename = os.path.basename(path)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for suffix in range(1000):
        backup_name = f"{filename}.corrupt-{timestamp}-{suffix:03d}.bak"
        backup_path = os.path.join(directory, backup_name)
        if os.path.exists(backup_path):
            continue
        try:
            copy2(path, backup_path)
            prune_corrupted_backups(directory, filename, keep_latest=keep_latest)
            return backup_path
        except Exception:
            return ""
    return ""

