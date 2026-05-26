"""Compatibility facade for `build_from_collection/__init__.py`.

v1.5.30.1 queue-wide facade split recovery

The active implementation lives in `build_from_collection.public_api`. This facade preserves the
original import path while the internals are split out of the large queue target.
"""

from __future__ import annotations

from importlib import import_module as _import_module

_impl = _import_module("build_from_collection.public_api")

for _name in dir(_impl):
    if not (_name.startswith("__") and _name.endswith("__")):
        globals()[_name] = getattr(_impl, _name)

try:
    __all__ = list(getattr(_impl, "__all__"))
except Exception:
    __all__ = [_name for _name in dir(_impl) if not _name.startswith("_")]

if __name__ == "__main__":
    _entry = globals().get("main")
    if callable(_entry):
        raise SystemExit(_entry())
    raise SystemExit("No main() entrypoint is available from build_from_collection.public_api.")
