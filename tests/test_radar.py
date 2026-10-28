from datetime import UTC, datetime, timedelta
from io import BytesIO
import json
from pathlib import Path
import tarfile
from unittest.mock import Mock, patch

import h5py
import numpy as np
from pyproj import Proj
import pytest

from custom_components.dwd_forecast_german import dwdradar, hymec
from custom_components.dwd_forecast_german.radar_grid import NotInAreaError, RadarGrid

PROJECTION = "+proj=eqc +R=6371000 +units=m"
STAMP = datetime(2026, 10, 28, 18, 45, tzinfo=UTC)


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return STAMP + timedelta(minutes=4)


def hdf_bytes(kind="CLASS", value=7, bad_legend=False):
    buffer = BytesIO()
    with h5py.File(buffer, "w") as f:
        f.create_group("where").attrs.update(
            projdef=PROJECTION, UL_lat=50., UL_lon=10., xscale=1000., yscale=1000., xsize=3, ysize=3,
        )
        f.create_group("what").attrs.update(date="20261028", time="184500")
        f.create_dataset("dataset1/data1/data", data=np.full((3, 3), value, dtype="uint32"))
        f.create_group("dataset1/data1/what").attrs.update(
            quantity=kind, gain=1. if kind == "CLASS" else .001,
            offset=0. if kind == "CLASS" else -.001,
            nodata=255 if kind == "CLASS" else 4294967295,
            undetect=254 if kind == "CLASS" else 0,
        )
        if kind == "CLASS":
            entries = [(v.encode(), str(k).encode()) for k, v in hymec.EXPECTED_LEGEND.items()]
            if bad_legend:
                entries[7] = (b"CHANGED", b"7")
            f.create_dataset("dataset1/data1/legend", data=np.array(entries, dtype=[("label", "S32"), ("value", "S4")]))
    return buffer.getvalue()


def point(column=1, row=1):
    p = Proj(PROJECTION)
    left, top = p(10, 50)
    lon, lat = p(left + (column + .5) * 1000, top - (row + .5) * 1000, inverse=True)
    return lat, lon


def rv_archive(value=101, count=25):
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as t:
        for step in reversed(range(count)):
            content = hdf_bytes("ACRR", value)
            member = tarfile.TarInfo(f"composite_rv_20261028_1845_{step * 5:03d}-hd5")
            member.size = len(content)
            t.addfile(member, BytesIO(content))
    return buffer.getvalue()


@pytest.mark.parametrize("code,label", hymec.PRECIPITATION_TYPES.items())
def test_hymec_all_classes(code, label):
    data = hymec.HymecData()
    data.load(hdf_bytes(value=code))
    assert hymec.PRECIPITATION_TYPES[data.code_at(*point())] == label
    assert data.timestamp == STAMP


@pytest.mark.parametrize("raw,expected", [(254, 0), (255, None), (123, None)])
def test_hymec_missing_is_not_dry(raw, expected):
    data = hymec.HymecData()
    data.load(hdf_bytes(value=raw))
    assert data.code_at(*point()) == expected


def test_bad_legend_does_not_overwrite_valid_data():
    data = hymec.HymecData()
    data.load(hdf_bytes(value=7))
    with pytest.raises(ValueError):
        data.load(hdf_bytes(value=3, bad_legend=True))
    assert data.code_at(*point()) == 7


def test_grid_every_cell_and_outside():
    with h5py.File(BytesIO(hdf_bytes()), "r") as f:
        grid = RadarGrid.from_hdf(f)
    for col in range(3):
        for row in range(3):
            assert grid.index(*point(col, row)) == (col, row)
    for lat, lon in [point(-1, 0), point(3, 0), point(0, -1), point(0, 3), (100, 10), (float("nan"), 10)]:
        with pytest.raises(NotInAreaError):
            grid.index(lat, lon)


def test_hymec_freshness():
    data = hymec.HymecData()
    with patch.object(hymec, "datetime", Clock):
        assert not data.fresh()
        data.timestamp = STAMP
        assert data.fresh()
        data.timestamp = STAMP - timedelta(minutes=21)
        assert not data.fresh()


def test_hymec_update_latest_and_cache():
    data = hymec.HymecData()
    index = Mock(text='<a href="composite_HymecNG_20261028_1845_000-hd5">file</a>')
    content = Mock(content=hdf_bytes(value=6))
    with patch.object(hymec, "datetime", Clock), patch.object(hymec.requests, "get", side_effect=[index, content, index]) as get:
        data.update()
        data.update()
        assert data.code_at(*point()) == 6
        assert get.call_count == 3  # zweite Runde lädt nur das Verzeichnis


def test_hymec_rejects_stale_listing():
    response = Mock(text="composite_HymecNG_20261028_1700_000-hd5")
    with patch.object(hymec, "datetime", Clock), patch.object(hymec.requests, "get", return_value=response):
        with pytest.raises(ValueError, match="älter"):
            hymec.HymecData().update()


@pytest.mark.parametrize("raw,expected", [(0, 0), (1, 0), (101, 1.2)])
def test_rv_calibration_sorting_and_timing(raw, expected):
    radar = dwdradar.DWDRadar()
    with patch.object(dwdradar, "datetime", Clock), patch.object(dwdradar.requests, "get", return_value=Mock(content=rv_archive(raw))):
        radar.get_radars()
    values = radar.get_precipitation_values(*point())
    assert len(values) == 25
    assert list(values) == sorted(values)
    assert list(values.values()) == pytest.approx([expected] * 25)
    assert radar.get_value(*point(), STAMP + timedelta(minutes=7)) == pytest.approx(expected)


def test_rv_nodata_is_not_rain_or_dry():
    radar = dwdradar.DWDRadar()
    with patch.object(dwdradar, "datetime", Clock), patch.object(dwdradar.requests, "get", return_value=Mock(content=rv_archive(4294967295))):
        radar.get_radars()
    with pytest.raises(dwdradar.RadarNotAvailableError):
        radar.get_precipitation_values(*point())


def test_rv_incomplete_archive_preserves_previous_data():
    radar = dwdradar.DWDRadar()
    sentinel = {"previous": True}
    radar.radars = sentinel
    with patch.object(dwdradar, "datetime", Clock), patch.object(dwdradar.requests, "get", return_value=Mock(content=rv_archive(count=24))):
        with pytest.raises(ValueError, match="Unvollständige"):
            radar.get_radars()
    assert radar.radars is sentinel


def test_legacy_event_attributes_remain():
    radar = dwdradar.DWDRadar()
    values = {STAMP + timedelta(minutes=i * 5): v for i, v in enumerate([0, 1.2, 1.2, 0, 0])}
    radar.get_precipitation_values = lambda *args: values
    event = radar.get_next_precipitation(0, 0)
    assert event["start"] == STAMP + timedelta(minutes=5)
    assert event["end"] == STAMP + timedelta(minutes=15)
    assert event["length"] == timedelta(minutes=10)
    assert event["max"] == 1.2
    assert event["sum"] == pytest.approx(.2)


def test_metadata_and_german_fallback():
    root = Path(__file__).parents[1]
    component = root / "custom_components/dwd_forecast_german"
    manifest = json.loads((component / "manifest.json").read_text())
    assert manifest["domain"] == "dwd_forecast_german"
    assert manifest["version"] == "1.0.1"
    assert json.loads((component / "strings.json").read_text()) == json.loads((component / "translations/de.json").read_text())
