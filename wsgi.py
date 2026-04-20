import importlib.util
import pathlib

_MODULE_PATH = pathlib.Path(__file__).resolve().parent / "format-calendars.py"
_spec = importlib.util.spec_from_file_location("format_calendars", _MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load WSGI app from {_MODULE_PATH}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

app = _module.app
