from types import SimpleNamespace

import pytest

from utils import import_compat


def test_load_attr_falls_back_to_next_module_when_candidate_is_missing(monkeypatch):
    def _fake_import(name):
        if name == "missing.module":
            raise ModuleNotFoundError("No module named 'missing.module'", name="missing.module")
        if name == "ok.module":
            return SimpleNamespace(target=123)
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr(import_compat, "import_module", _fake_import)

    resolved = import_compat.load_attr(["missing.module", "ok.module"], "target")
    assert resolved == 123


def test_load_attr_propagates_nested_missing_dependency(monkeypatch):
    def _fake_import(name):
        if name == "candidate.module":
            raise ModuleNotFoundError("No module named 'inner.dependency'", name="inner.dependency")
        raise AssertionError(f"should not continue to next module: {name}")

    monkeypatch.setattr(import_compat, "import_module", _fake_import)

    with pytest.raises(ModuleNotFoundError) as exc:
        import_compat.load_attr(["candidate.module", "fallback.module"], "target")

    assert exc.value.name == "inner.dependency"

