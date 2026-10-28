from datetime import UTC, datetime, timedelta
from io import BytesIO
import tarfile
import re

import numpy as np
import requests
import logging
import h5py

API_URL = "https://opendata.dwd.de/weather/radar/composite/rv/composite_rv_LATEST.tar"

from .radar_grid import NotInAreaError, RadarGrid, text

_LOGGER = logging.getLogger(__name__)


class RadarNotAvailableError(Exception):
    pass


class DWDRadar:
    def __init__(self):
        self.radars = None
        self.grid = None
        self.xsize = 1100
        self.ysize = 1200

    def get_radars(self):
        response = requests.get(API_URL, timeout=(5, 30))
        response.raise_for_status()
        radars = {}
        grid = None
        calibration = {}
        with tarfile.open(fileobj=BytesIO(response.content)) as archive:
            for member in archive.getmembers():
                match = re.fullmatch(r"composite_rv_(\d{8}_\d{4})_(\d{3})-hd5", member.name)
                if not member.isfile() or match is None:
                    continue
                base = datetime.strptime(match[1], "%Y%m%d_%H%M").replace(tzinfo=UTC)
                radar_time = base + timedelta(minutes=int(match[2]))
                with archive.extractfile(member) as stream:
                    with h5py.File(BytesIO(stream.read()), "r") as hdf:
                        current_grid = RadarGrid.from_hdf(hdf)
                        if grid is not None and current_grid != grid:
                            raise ValueError("RV-Raster sind uneinheitlich")
                        grid = current_grid
                        meta = hdf["dataset1/data1/what"].attrs
                        if text(meta["quantity"]) != "ACRR":
                            raise ValueError("Unerwartetes RV-Datenformat")
                        raw = hdf["dataset1/data1/data"][:]
                        if raw.shape != (grid.ysize, grid.xsize):
                            raise ValueError("RV-Rastergröße stimmt nicht")
                        calibration[radar_time] = {
                            key: float(meta[key]) for key in ("gain", "offset", "nodata", "undetect")
                        }
                        radars[radar_time] = raw
        times = sorted(radars)
        if len(times) != 25 or any(b - a != timedelta(minutes=5) for a, b in zip(times, times[1:])):
            raise ValueError("Unvollständige RV-Vorhersage")
        age = datetime.now(UTC) - times[0]
        if not -timedelta(minutes=2) <= age <= timedelta(minutes=20):
            raise ValueError("RV-Datenstand ist veraltet oder liegt in der Zukunft")
        self.radars = dict(sorted(radars.items()))
        self.grid = grid
        self.calibration = calibration
        self.xsize, self.ysize = grid.xsize, grid.ysize

    def get_location_index(self, latitude, longitude):
        if self.radars is None or self.grid is None:
            raise RadarNotAvailableError
        return self.grid.index(latitude, longitude)

    def get_precipitation_values(self, latitude, longitude):
        column, row = self.get_location_index(latitude, longitude)
        values = {}
        for stamp, radar in self.radars.items():
            raw = float(radar[row, column])
            meta = self.calibration[stamp]
            if raw == meta["nodata"] or not np.isfinite(raw):
                raise RadarNotAvailableError("Am Standort fehlen RV-Daten")
            values[stamp] = 0.0 if raw == meta["undetect"] else max(
                0.0, raw * meta["gain"] + meta["offset"]
            ) * 12
        return values

    def get_value(self, x, y, search_time: datetime):
        precipitation_values = self.get_precipitation_values(x, y)
        return np.interp(
            search_time.timestamp(),
            [x.timestamp() for x in precipitation_values],
            list(precipitation_values.values()),
        )
    def get_next_precipitation(self, x, y):
        rain_start = None
        rain_end = None
        rain_max = 0
        rain_sum = 0
        for rain_time, precipitation in self.get_precipitation_values(x, y).items():
            if rain_start is None and precipitation > 0:
                rain_start = rain_time
                rain_max = precipitation
                rain_sum = precipitation
                continue
            if rain_start is not None:
                rain_max = max(rain_max, precipitation)
                rain_sum += precipitation
            if rain_start is not None and rain_end is None and precipitation == 0:
                rain_end = rain_time
                continue
            if rain_start is not None and rain_end is not None and precipitation != 0:
                rain_end = None
                continue
            if rain_start is not None and rain_end is not None and precipitation == 0:
                break

        if rain_start is not None:
            if rain_end is not None:
                rain_length = rain_end - rain_start
            else:
                rain_length = None
            rain_sum = rain_sum / 12
        else:
            rain_length = None

        return {
            "start": rain_start,
            "end": rain_end,
            "length": rain_length,
            "max": rain_max,
            "sum": rain_sum,
        }
