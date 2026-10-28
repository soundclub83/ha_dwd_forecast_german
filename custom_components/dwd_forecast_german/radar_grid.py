"""DWD-Raster anhand der Projektion im HDF5-Header auswerten."""

from dataclasses import dataclass
from math import floor, isfinite

from pyproj import Proj


class NotInAreaError(ValueError):
    """Der Standort liegt außerhalb des Rasters."""


def text(value):
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


@dataclass
class RadarGrid:
    projection: Proj
    left: float
    top: float
    xscale: float
    yscale: float
    xsize: int
    ysize: int

    @classmethod
    def from_hdf(cls, hdf):
        where = hdf["where"].attrs
        projection = Proj(text(where["projdef"]))
        left, top = projection(float(where["UL_lon"]), float(where["UL_lat"]))
        return cls(projection, left, top, float(where["xscale"]),
                   float(where["yscale"]), int(where["xsize"]), int(where["ysize"]))

    def index(self, latitude, longitude):
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise NotInAreaError("Ungültige Koordinaten")
        x, y = self.projection(longitude, latitude)
        if not (isfinite(x) and isfinite(y)):
            raise NotInAreaError("Standort ist nicht projizierbar")
        # Pixel beziehen sich auf Flächen, nicht auf den nächsten Pixelmittelpunkt.
        column = floor(round((x - self.left) / self.xscale, 8))
        row = floor(round((self.top - y) / self.yscale, 8))
        if not (0 <= column < self.xsize and 0 <= row < self.ysize):
            raise NotInAreaError("Standort liegt außerhalb des DWD-Rasters")
        return column, row
