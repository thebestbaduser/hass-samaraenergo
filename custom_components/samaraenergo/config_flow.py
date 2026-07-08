"""Config flow for Samara Energo."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SamaraEnergoApi, SamaraEnergoAuthError, SamaraEnergoApiError
from .const import ACCOUNT_NUMBER_LENGTH, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_input(hass: HomeAssistant, username: str, password: str) -> dict[str, str]:
    session = async_get_clientsession(hass)
    api = SamaraEnergoApi(username=username.strip(), password=password, session=session)
    await api.validate_credentials()
    data = await api.async_get_data()
    return {
        "title": f"Самараэнерго {data.account_number}",
        "address": data.address,
    }


class SamaraEnergoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            if len(username) != ACCOUNT_NUMBER_LENGTH or not username.isdigit():
                errors["base"] = "invalid_account"
            else:
                try:
                    info = await _validate_input(self.hass, username, password)
                except SamaraEnergoAuthError:
                    errors["base"] = "invalid_auth"
                except SamaraEnergoApiError:
                    errors["base"] = "cannot_connect"
                except aiohttp.ClientError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(username)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=info["title"],
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return SamaraEnergoOptionsFlow()


class SamaraEnergoOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        from .const import DEFAULT_SCAN_INTERVAL

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "scan_interval",
                        default=self.config_entry.options.get(
                            "scan_interval", DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=900, max=86400)),
                }
            ),
        )


class InvalidAuth(HomeAssistantError):
    """Invalid authentication."""


class CannotConnect(HomeAssistantError):
    """Cannot connect to API."""
