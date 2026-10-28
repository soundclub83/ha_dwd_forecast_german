"""Datenleser ohne laufenden Home-Assistant-Server testen."""

from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.dwd_precipitation_forecast"
for name, path in [("custom_components", ROOT / "custom_components"),
                   (PACKAGE, ROOT / "custom_components/dwd_precipitation_forecast")]:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module
