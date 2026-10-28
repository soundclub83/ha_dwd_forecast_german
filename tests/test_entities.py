"""HA-Anbindung mit kleinen Schnittstellen-Doubles prüfen (kein HA-Systemtest)."""

import asyncio
from dataclasses import dataclass
import importlib
import sys
import types
from unittest.mock import Mock

import pytest


@pytest.fixture
def modules(monkeypatch):
    def module(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, m)
        return m

    class Generic:
        @classmethod
        def __class_getitem__(cls, item):
            return cls

    class CoordinatorEntity(Generic):
        def __init__(self, coordinator):
            self.coordinator = coordinator

        @property
        def available(self):
            return self.coordinator.last_update_success

    class DataUpdateCoordinator(Generic):
        def __init__(self, hass, *args, **kwargs):
            self.hass = hass

    @dataclass(kw_only=True)
    class Description:
        key: str
        name: str | None = None
        native_unit_of_measurement: str | None = None
        device_class: str | None = None
        state_class: str | None = None

    module("homeassistant")
    module("homeassistant.components")
    module("homeassistant.components.sensor", SensorEntity=type("SensorEntity", (), {}),
           SensorEntityDescription=Description,
           SensorDeviceClass=types.SimpleNamespace(PRECIPITATION_INTENSITY="precipitation_intensity", TIMESTAMP="timestamp", ENUM="enum"),
           SensorStateClass=types.SimpleNamespace(MEASUREMENT="measurement"))
    module("homeassistant.core", HomeAssistant=object)
    module("homeassistant.helpers")
    module("homeassistant.helpers.device_registry", DeviceInfo=dict, DeviceEntryType=types.SimpleNamespace(SERVICE="service"))
    module("homeassistant.helpers.entity_platform", AddEntitiesCallback=object)
    module("homeassistant.helpers.update_coordinator", CoordinatorEntity=CoordinatorEntity,
           DataUpdateCoordinator=DataUpdateCoordinator, UpdateFailed=type("UpdateFailed", (Exception,), {}))
    module("homeassistant.const", CONF_LATITUDE="latitude", CONF_LONGITUDE="longitude")
    module("homeassistant.config_entries", ConfigEntry=Generic)
    module("async_timeout", timeout=asyncio.timeout)
    for name in ["coordinator", "sensor"]:
        monkeypatch.delitem(sys.modules, "custom_components.dwd_precipitation_forecast." + name, raising=False)
    return (importlib.import_module("custom_components.dwd_precipitation_forecast.sensor"),
            importlib.import_module("custom_components.dwd_precipitation_forecast.coordinator"))


def test_existing_unique_ids_and_attributes(modules):
    sensor, _ = modules
    entry = types.SimpleNamespace(data={"latitude": 52.4, "longitude": 13.3}, title="Home")
    api = Mock()
    api.get_next_precipitation.return_value = {"start": None, "end": None, "length": None, "max": 0, "sum": 0}
    api.get_precipitation_values.return_value = {}
    coordinator = types.SimpleNamespace(api=api, last_update_success=True)
    for description in sensor.SENSORS:
        entity = sensor.DwdPrecipitationForecastEntity(coordinator, entry, description)
        assert entity._attr_unique_id == f"52.4-13.3--{description.key}"
        if description.key == "next":
            assert entity.native_value is None
            assert set(entity.extra_state_attributes) == {"end", "length", "max", "sum"}
        else:
            assert set(entity.extra_state_attributes) == {"forecast", "next_start", "next_end", "next_length"}
        if description.key in ("15min", "30min", "60min"):
            assert entity.native_value is False


def test_snow_sensor_freshness_failure_and_icon(modules):
    sensor, _ = modules
    api = Mock()
    api.code_at.return_value = 7
    api.fresh.return_value = True
    api.timestamp = None
    coordinator = types.SimpleNamespace(api=api, last_update_success=True)
    entry = types.SimpleNamespace(data={"latitude": 52.4, "longitude": 13.3}, title="Home")
    entity = sensor.DwdPrecipitationTypeSensor(coordinator, entry)
    assert entity.native_value == "Schnee"
    assert entity.icon == "mdi:weather-snowy"
    assert entity.extra_state_attributes["ist_vorhersage"] is False
    api.code_at.return_value = None
    assert not entity.available
    api.code_at.return_value = 3
    api.fresh.return_value = False
    assert entity.native_value is None
    api.fresh.return_value = True
    coordinator.last_update_success = False
    assert entity.native_value is None


def test_hymec_failure_does_not_change_rv_coordinator(modules):
    _, coordinators = modules

    class Hass:
        async def async_add_executor_job(self, func):
            return func()

    main = coordinators.DwdPrecipitationForecastCoordinator(Hass())
    main.api = Mock()
    extra = coordinators.DwdPrecipitationTypeCoordinator(Hass())
    extra.api.update = Mock(side_effect=ValueError("Testausfall"))
    with pytest.raises(Exception, match="Niederschlagsart"):
        asyncio.run(extra._async_update_data())
    main.api.get_radars.assert_not_called()
    asyncio.run(main._async_update_data())
    main.api.get_radars.assert_called_once()
