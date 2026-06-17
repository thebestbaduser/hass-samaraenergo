"""Sensors for Samara Energo."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_AMOUNT_DUE,
    SENSOR_AVG_MONTHLY_CONSUMPTION,
    SENSOR_AVG_MONTHLY_COST,
    SENSOR_CONSUMPTION_HISTORY,
    SENSOR_DUE_DATE,
    SENSOR_LAST_PAYMENT,
    SENSOR_LAST_PAYMENT_DATE,
    SENSOR_LAST_READING,
    SENSOR_LAST_READING_DATE,
    SENSOR_TARIFF_DAY,
    SENSOR_TARIFF_NIGHT,
    SENSOR_TARIFF_SEMI_PEAK,
    SENSOR_TARIFF_TYPE,
)
from .coordinator import SamaraEnergoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: SamaraEnergoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SamaraEnergoAmountDueSensor(coordinator, entry),
            SamaraEnergoDueDateSensor(coordinator, entry),
            SamaraEnergoLastPaymentSensor(coordinator, entry),
            SamaraEnergoLastPaymentDateSensor(coordinator, entry),
            SamaraEnergoLastReadingSensor(coordinator, entry),
            SamaraEnergoLastReadingDateSensor(coordinator, entry),
            SamaraEnergoAvgMonthlyConsumptionSensor(coordinator, entry),
            SamaraEnergoAvgMonthlyCostSensor(coordinator, entry),
            SamaraEnergoConsumptionHistorySensor(coordinator, entry),
            SamaraEnergoTariffTypeSensor(coordinator, entry),
            SamaraEnergoTariffDaySensor(coordinator, entry),
            SamaraEnergoTariffSemiPeakSensor(coordinator, entry),
            SamaraEnergoTariffNightSensor(coordinator, entry),
        ]
    )


class SamaraEnergoBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        data = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["username"])},
            name=f"Самараэнерго {entry.data['username']}",
            manufacturer="ПАО Самараэнерго",
            model="Личный кабинет",
        )
        if data:
            self._attr_device_info["configuration_url"] = "https://lk.samaraenergo.ru/"
            if data.address:
                self._attr_device_info["suggested_area"] = data.address


class SamaraEnergoAmountDueSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_AMOUNT_DUE
    _attr_native_unit_of_measurement = "RUB"
    _attr_icon = "mdi:cash-clock"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_AMOUNT_DUE}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.amount_due


class SamaraEnergoDueDateSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_DUE_DATE
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_DUE_DATE}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.due_date


class SamaraEnergoLastPaymentSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_LAST_PAYMENT
    _attr_native_unit_of_measurement = "RUB"
    _attr_icon = "mdi:cash-check"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_LAST_PAYMENT}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.last_payment_amount


class SamaraEnergoLastPaymentDateSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_LAST_PAYMENT_DATE
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_LAST_PAYMENT_DATE}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.last_payment_date


class SamaraEnergoLastReadingSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_LAST_READING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_LAST_READING}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.last_reading_kwh


class SamaraEnergoLastReadingDateSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_LAST_READING_DATE
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:calendar-sync"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_LAST_READING_DATE}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.last_reading_date


class SamaraEnergoAvgMonthlyConsumptionSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_AVG_MONTHLY_CONSUMPTION
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_icon = "mdi:chart-bar"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_AVG_MONTHLY_CONSUMPTION}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.avg_monthly_consumption_kwh


class SamaraEnergoAvgMonthlyCostSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_AVG_MONTHLY_COST
    _attr_native_unit_of_measurement = "RUB"
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_AVG_MONTHLY_COST}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.avg_monthly_cost_rub


class SamaraEnergoConsumptionHistorySensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_CONSUMPTION_HISTORY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:chart-timeline-variant"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_CONSUMPTION_HISTORY}"

    @property
    def native_value(self):
        if not self.coordinator.data or not self.coordinator.data.consumption_history:
            return None
        return self.coordinator.data.consumption_history[-1].kwh

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        history = self.coordinator.data.consumption_history
        return {
            "address": self.coordinator.data.address,
            "account_number": self.coordinator.data.account_number,
            "history": [
                {
                    "month": point.month,
                    "kwh": point.kwh,
                    "cost": point.cost,
                }
                for point in history
            ],
            "history_kwh": [point.kwh for point in history],
            "history_months": [point.month for point in history],
            "history_costs": [point.cost for point in history if point.cost is not None],
        }


class SamaraEnergoTariffTypeSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_TARIFF_TYPE
    _attr_icon = "mdi:tag-text"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_TARIFF_TYPE}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.tariff.tariff_type

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        tariff = self.coordinator.data.tariff
        return {
            "zones": tariff.zone_count,
            "zone_1": tariff.day_zone_label,
            "zone_2": tariff.semi_peak_zone_label if tariff.zone_count == 3 else tariff.night_zone_label,
            "zone_3": tariff.night_zone_label if tariff.zone_count == 3 else None,
        }


class SamaraEnergoTariffDaySensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_TARIFF_DAY
    _attr_native_unit_of_measurement = "RUB/kWh"
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_TARIFF_DAY}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.tariff.day_rate_rub

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        return {"zone": self.coordinator.data.tariff.day_zone_label}


class SamaraEnergoTariffSemiPeakSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_TARIFF_SEMI_PEAK
    _attr_native_unit_of_measurement = "RUB/kWh"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_TARIFF_SEMI_PEAK}"

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.tariff.zone_count == 3
        )

    @property
    def native_value(self):
        if not self.coordinator.data or self.coordinator.data.tariff.zone_count != 3:
            return None
        return self.coordinator.data.tariff.semi_peak_rate_rub

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        return {"zone": self.coordinator.data.tariff.semi_peak_zone_label}


class SamaraEnergoTariffNightSensor(SamaraEnergoBaseSensor):
    _attr_translation_key = SENSOR_TARIFF_NIGHT
    _attr_native_unit_of_measurement = "RUB/kWh"
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator: SamaraEnergoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.data['username']}_{SENSOR_TARIFF_NIGHT}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.tariff.night_rate_rub

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        return {"zone": self.coordinator.data.tariff.night_zone_label}
