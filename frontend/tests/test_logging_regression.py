import logging
from importlib import import_module

logging_utils = import_module("utils.logging_utils")


def test_configure_basic_logging_can_enable_file_output(monkeypatch, tmp_path):
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level

    for handler in list(root.handlers):
        root.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    monkeypatch.setenv("RHYME_LOG_TO_FILE", "true")
    monkeypatch.setenv("RHYME_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("RHYME_LOG_LEVEL", "INFO")

    try:
        logging_utils.configure_basic_logging()
        logger = logging_utils.get_logger("test.logging")
        logger.info("hello logging")

        for handler in root.handlers:
            try:
                handler.flush()
            except Exception:
                pass

        log_file = tmp_path / "rhyme.log"
        assert log_file.exists() is True
        content = log_file.read_text(encoding="utf-8")
        assert "hello logging" in content
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass

        for handler in old_handlers:
            root.addHandler(handler)
        root.setLevel(old_level)


