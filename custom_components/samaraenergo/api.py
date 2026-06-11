"""Async client for lk.samaraenergo.ru SAP OData API."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import aiohttp

from .const import (
    ACCOUNT_NUMBER_LENGTH,
    AUTH_CHECK_PATH,
    BASE_URL,
    SERVICE_PATH,
)

_LOGGER = logging.getLogger(__name__)


class SamaraEnergoAuthError(Exception):
    """Authentication failed."""


class SamaraEnergoApiError(Exception):
    """API request failed."""


@dataclass
class ConsumptionPoint:
    month: str
    kwh: float
    cost: float | None = None


@dataclass
class SamaraEnergoData:
    account_number: str
    address: str
    contract_account_id: str
    amount_due: float
    due_date: datetime | None
    last_payment_amount: float | None
    last_payment_date: datetime | None
    last_reading_kwh: float | None
    last_reading_date: datetime | None
    avg_monthly_consumption_kwh: float | None
    avg_monthly_cost_rub: float | None
    consumption_history: list[ConsumptionPoint] = field(default_factory=list)


def _parse_sap_date(value: Any) -> datetime | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        match = re.search(r"/Date\((-?\d+)\)/", value)
        if match:
            return datetime.fromtimestamp(int(match.group(1)) / 1000, tz=UTC)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class SamaraEnergoApi:
    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        self.username = username
        self.password = password
        self._session = session

    def _auth_params(self) -> dict[str, str]:
        return {
            "sap-language": "RU",
            "sap-user": self.username,
            "sap-password": self.password,
            "$format": "json",
        }

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{BASE_URL}{path}"
        query = {**self._auth_params(), **(params or {})}
        async with self._session.get(
            url,
            params=query,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            text = await response.text()
            if response.status == 401:
                raise SamaraEnergoAuthError("Invalid username or password")
            if response.status >= 400:
                raise SamaraEnergoApiError(f"HTTP {response.status} for {path}: {text[:300]}")
            try:
                return await response.json(content_type=None)
            except aiohttp.ContentTypeError as err:
                raise SamaraEnergoApiError(f"Invalid JSON from {path}") from err

    @staticmethod
    def _results(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        data = payload.get("d", payload)
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    @staticmethod
    def _entity(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        data = payload.get("d", payload)
        return data if isinstance(data, dict) else {}

    async def validate_credentials(self) -> None:
        if len(self.username) != ACCOUNT_NUMBER_LENGTH or not self.username.isdigit():
            raise SamaraEnergoAuthError("Account number must contain exactly 12 digits")

        url = f"{BASE_URL}{AUTH_CHECK_PATH}"
        params = {
            "sap-language": "RU",
            "sap-user": self.username,
            "sap-password": self.password,
        }
        async with self._session.get(
            url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            text = await response.text()
            if text and "Пароль начальный" not in text:
                raise SamaraEnergoAuthError("Authorization failed")

        payload = await self._request(
            f"{SERVICE_PATH}/PasswordStatSet('{self.username}')",
        )
        pass_stat = self._entity(payload).get("PassStat")
        if str(pass_stat) not in {"2", "1"}:
            raise SamaraEnergoAuthError("Account is blocked or unavailable")

    async def _get_account(self) -> dict[str, Any]:
        payload = await self._request(
            f"{SERVICE_PATH}/Accounts",
            {
                "$expand": "ContractAccounts,ContractAccounts/Contracts/Premise",
            },
        )
        accounts = self._results(payload)
        if not accounts:
            raise SamaraEnergoApiError("No accounts returned")
        return accounts[0]

    @staticmethod
    def _pick_primary_contract(account: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        contract_accounts = account.get("ContractAccounts", {})
        if isinstance(contract_accounts, dict):
            contract_accounts = contract_accounts.get("results", [])

        if not contract_accounts:
            raise SamaraEnergoApiError("No contract accounts found")

        contract_account = contract_accounts[0]
        contracts = contract_account.get("Contracts", {})
        if isinstance(contracts, dict):
            contracts = contracts.get("results", [])
        if not contracts:
            raise SamaraEnergoApiError("No contracts found")

        contract = contracts[0]
        return contract_account, contract, account

    @staticmethod
    def _format_address(account: dict[str, Any], contract: dict[str, Any]) -> str:
        premise = contract.get("Premise", {})
        if isinstance(premise, dict) and premise.get("results"):
            premise = premise["results"][0]
        parts = [
            premise.get("City"),
            premise.get("Street"),
            premise.get("HouseNumber"),
        ]
        address = ", ".join(part for part in parts if part)
        if address:
            return address
        return account.get("Description") or account.get("AccountID") or ""

    async def _get_amount_due(self, contract_account_id: str) -> tuple[float, datetime | None]:
        payload = await self._request(
            f"{SERVICE_PATH}/Invoices/ContractAccounts('{contract_account_id}')",
        )
        invoices = [
            item
            for item in self._results(payload)
            if str(item.get("InvoiceStatusID", "")) != "9"
        ]
        if not invoices:
            return 0.0, None

        amount_due = round(
            sum(_to_float(item.get("AmountRemaining")) or 0.0 for item in invoices),
            2,
        )
        due_date = _parse_sap_date(invoices[0].get("DueDate"))
        return amount_due, due_date

    async def _get_last_payment(self) -> tuple[float | None, datetime | None]:
        payload = await self._request(f"{SERVICE_PATH}/PaymentDocuments")
        payments = self._results(payload)
        completed = next(
            (item for item in payments if str(item.get("PaymentStatusID")) == "9"),
            None,
        )
        if not completed:
            return None, None
        return _to_float(completed.get("Amount")), _parse_sap_date(completed.get("ExecutionDate"))

    async def _get_last_reading(self, device_id: str) -> tuple[float | None, datetime | None]:
        payload = await self._request(
            f"{SERVICE_PATH}/Devices('{quote(device_id, safe='')}')",
            {"$expand": "MeterReadingResults"},
        )
        entity = self._entity(payload)
        readings = entity.get("MeterReadingResults", {})
        if isinstance(readings, dict):
            readings = readings.get("results", [])
        if not readings:
            return None, None

        last = readings[-1]
        return _to_float(last.get("ReadingResult")), _parse_sap_date(last.get("ReadingDateTime"))

    async def _get_consumption_history(self, contract_id: str) -> list[ConsumptionPoint]:
        period_payload = await self._request(
            f"{SERVICE_PATH}/GetCurrentBillingPeriod",
            {"ContractID": f"'{contract_id}'"},
        )
        period = self._entity(period_payload)
        start_date = _parse_sap_date(period.get("StartDate"))
        if not start_date:
            start_date = datetime.now(tz=UTC)

        from datetime import timedelta

        history_start = start_date - timedelta(days=730)
        start_iso = history_start.strftime("%Y-%m-%dT00:00:00")

        payload = await self._request(
            f"{SERVICE_PATH}/ContractConsumptionValues/Contracts('{contract_id}')",
            {
                "$filter": (
                    f"ConsumptionPeriodTypeID eq 'BC' and "
                    f"StartDate ge datetime'{start_iso}'"
                ),
                "$expand": "MeterReadingCategory",
            },
        )
        rows = sorted(
            self._results(payload),
            key=lambda item: _parse_sap_date(item.get("StartDate")) or datetime.min.replace(tzinfo=UTC),
        )
        history: list[ConsumptionPoint] = []
        for row in rows:
            start = _parse_sap_date(row.get("StartDate"))
            if not start:
                continue
            history.append(
                ConsumptionPoint(
                    month=start.strftime("%Y-%m"),
                    kwh=_to_float(row.get("ConsumptionValue")) or 0.0,
                    cost=_to_float(row.get("BilledAmount")),
                )
            )
        return history

    async def async_get_data(self) -> SamaraEnergoData:
        account = await self._get_account()
        contract_account, contract, account = self._pick_primary_contract(account)

        contract_account_id = contract_account.get("ContractAccountID", "")
        contract_id = contract.get("ContractID", "")

        devices = contract.get("Devices", {})
        if isinstance(devices, dict):
            devices = devices.get("results", [])
        device_id = devices[0].get("DeviceID") if devices else ""

        amount_due, due_date = await self._get_amount_due(contract_account_id)
        last_payment_amount, last_payment_date = await self._get_last_payment()
        last_reading_kwh, last_reading_date = (
            await self._get_last_reading(device_id) if device_id else (None, None)
        )
        history = await self._get_consumption_history(contract_id) if contract_id else []

        avg_consumption = None
        avg_cost = None
        if len(history) > 1:
            avg_consumption = round(sum(point.kwh for point in history) / len(history))
            costs = [point.cost for point in history if point.cost is not None]
            if costs:
                avg_cost = round(sum(costs) / len(costs))

        return SamaraEnergoData(
            account_number=self.username,
            address=self._format_address(account, contract),
            contract_account_id=contract_account_id,
            amount_due=amount_due,
            due_date=due_date,
            last_payment_amount=last_payment_amount,
            last_payment_date=last_payment_date,
            last_reading_kwh=last_reading_kwh,
            last_reading_date=last_reading_date,
            avg_monthly_consumption_kwh=avg_consumption,
            avg_monthly_cost_rub=avg_cost,
            consumption_history=history,
        )
