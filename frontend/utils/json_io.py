import json
import os
import tempfile


def atomic_write_json(file_path, data):
    directory = os.path.dirname(os.path.abspath(file_path)) or "."
    os.makedirs(directory, exist_ok=True)

    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=f"{os.path.basename(file_path)}.",
            suffix=".tmp",
            delete=False,
        ) as handler:
            temp_path = handler.name
            json.dump(data, handler, ensure_ascii=False, indent=2)
            handler.flush()
            os.fsync(handler.fileno())

        os.replace(temp_path, file_path)
        temp_path = ""
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

