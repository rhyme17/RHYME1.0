from importlib import import_module


def load_attr(module_names, attr_name):
    last_error = None
    for module_name in module_names:
        try:
            module = import_module(module_name)
            return getattr(module, attr_name)
        except ModuleNotFoundError as exc:
            # 仅在候选模块本身不存在时继续尝试；
            # 若是模块内部依赖缺失，应原样抛出便于排障。
            missing_name = str(getattr(exc, "name", "") or "")
            if missing_name and missing_name != module_name and not missing_name.startswith(f"{module_name}."):
                raise
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    raise ImportError(f"Cannot resolve {attr_name} from modules: {module_names}")

