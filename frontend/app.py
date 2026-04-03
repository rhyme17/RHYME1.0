import sys
from importlib import import_module
from pathlib import Path


def _ensure_project_root_on_sys_path():
    frontend_dir = Path(__file__).resolve().parent
    project_root = str(frontend_dir.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_root_on_sys_path()


def _get_windows_main():
    try:
        module = import_module("frontend.apps.desktop.windows.app")
    except ModuleNotFoundError:
        module = import_module("apps.desktop.windows.app")
    return module.main


def main(argv=None):
    args = argv if argv is not None else sys.argv
    return _get_windows_main()(argv=args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
