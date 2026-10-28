"""Aktuelle Niederschlagsart aus DWD HymecNG; keine Artenvorhersage."""

from datetime import UTC, datetime, timedelta
from io import BytesIO
import re

import h5py
import numpy as np
import requests

from .radar_grid import RadarGrid, text

HYMEC_URL = "https://opendata.dwd.de/weather/radar/composite/hymecng/"
MAX_AGE = timedelta(minutes=20)
PRECIPITATION_TYPES = {
    0: "Kein Niederschlag",
    1: "Nicht klassifizierbar",
    2: "Sprühregen",
    3: "Regen",
    4: "Gefrierender Sprühregen",
    5: "Gefrierender Regen",
    6: "Schneeregen",
    7: "Schnee",
    8: "Graupel",
    9: "Hagel",
    10: "Großer Hagel",
}
EXPECTED_LEGEND = {
    0: "NO_PRECIPITATION", 1: "NOT_CLASSIFIED", 2: "DRIZZLE", 3: "RAIN",
    4: "FREEZING_DRIZZLE", 5: "FREEZING_RAIN", 6: "SNOW_RAIN", 7: "SNOW",
    8: "GRAUPEL", 9: "HAIL", 10: "LARGE_HAIL",
}


class HymecData:
    def __init__(self):
        self.data = None
        self.grid = None
        self.timestamp = None
        self.filename = None
        self.nodata = 255
        self.undetect = 254

    def update(self):
        now = datetime.now(UTC)
        response = requests.get(HYMEC_URL, timeout=(5, 15))
        response.raise_for_status()
        candidates = []
        for filename in set(re.findall(r"composite_HymecNG_\d{8}_\d{4}_000-hd5", response.text)):
            stamp = datetime.strptime(filename[18:31], "%Y%m%d_%H%M").replace(tzinfo=UTC)
            if stamp <= now + timedelta(minutes=2):
                candidates.append((stamp, filename))
        if not candidates:
            raise ValueError("Keine HymecNG-Datei im DWD-Verzeichnis")
        stamp, filename = max(candidates)
        if now - stamp > MAX_AGE:
            raise ValueError("HymecNG-Daten sind älter als 20 Minuten")
        if filename == self.filename:
            return
        response = requests.get(HYMEC_URL + filename, timeout=(5, 15))
        response.raise_for_status()
        self.load(response.content, filename)

    def load(self, content, filename=None):
        # Erst nach vollständiger Prüfung den bisherigen Datenstand ersetzen.
        with h5py.File(BytesIO(content), "r") as hdf:
            what = hdf["dataset1/data1/what"].attrs
            if text(what["quantity"]) != "CLASS" or float(what["gain"]) != 1 or float(what["offset"]) != 0:
                raise ValueError("Unerwartetes HymecNG-Datenformat")
            legend = {int(text(row[1])): text(row[0]) for row in hdf["dataset1/data1/legend"][:]}
            if legend != EXPECTED_LEGEND:
                raise ValueError("Unbekannte HymecNG-Klassenzuordnung")
            grid = RadarGrid.from_hdf(hdf)
            data = np.asarray(hdf["dataset1/data1/data"][:])
            if data.shape != (grid.ysize, grid.xsize):
                raise ValueError("HymecNG-Rastergröße stimmt nicht")
            root = hdf["what"].attrs
            stamp = datetime.strptime(text(root["date"]) + text(root["time"]), "%Y%m%d%H%M%S").replace(tzinfo=UTC)
            nodata, undetect = int(what["nodata"]), int(what["undetect"])
        self.data, self.grid, self.timestamp = data, grid, stamp
        self.nodata, self.undetect, self.filename = nodata, undetect, filename

    def code_at(self, latitude, longitude):
        if self.data is None:
            return None
        column, row = self.grid.index(latitude, longitude)
        code = int(self.data[row, column])
        if code == self.nodata:
            return None
        if code == self.undetect:
            return 0
        return code if code in PRECIPITATION_TYPES else None

    def fresh(self):
        return self.timestamp is not None and -timedelta(minutes=2) <= datetime.now(UTC) - self.timestamp <= MAX_AGE
