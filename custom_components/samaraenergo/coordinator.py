"""Data update coordinator."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SamaraEnergoApi, SamaraEnergoApiError, SamaraEnergoAuthError, SamaraEnergoData
from .const import CONF_PASSWORD, CONF_USERNAME, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SamaraEnergoCoordinator(DataUpdateCoordinator[SamaraEnergoData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, session: aiohttp.ClientSession) -> None:
        self.entry = entry
        self.api = SamaraEnergoApi(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=session,
        )
        scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> SamaraEnergoData:
        try:
            return await self.api.async_get_data()
        except SamaraEnergoAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except SamaraEnergoApiError as err:
            raise UpdateFailed(str(err)) from err
