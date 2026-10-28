"""Datenleser ohne laufenden Home-Assistant-Server testen."""

from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.dwd_forecast_german"
for name, path in [("custom_components", ROOT / "custom_components"),
                   (PACKAGE, ROOT / "custom_components/dwd_forecast_german")]:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module
