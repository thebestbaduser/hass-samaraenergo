"""Async client for lk.samaraenergo.ru SAP OData API."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
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

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "Accept": "application/json",
            "X-REQUESTED-WITH": "XMLHttpRequest",
        }

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
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            text = await response.text()
            _LOGGER.debug("GET %s status=%s body=%s", path, response.status, text[:300])
            if response.status == 401:
                raise SamaraEnergoAuthError("Invalid username or password")
            if response.status >= 400:
                raise SamaraEnergoApiError(f"HTTP {response.status} for {path}: {text[:300]}")
            if not text.strip():
                return {}
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

    async def _preauth_session(self) -> None:
        """Mirror browser login: warm SAP session before OData calls."""
        url = f"{BASE_URL}{AUTH_CHECK_PATH}"
        params = {
            "sap-language": "RU",
            "sap-user": self.username,
            "sap-password": self.password,
        }
        async with self._session.get(
            url,
            params=params,
            headers=self._headers(),
            allow_redirects=False,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            text = await response.text()
            _LOGGER.debug("Pre-auth status=%s body=%s", response.status, text[:300])
            if "Авторизация не удалась" in text:
                raise SamaraEnergoAuthError("Invalid username or password")
            if text and "Пароль начальный" not in text and response.status >= 400:
                raise SamaraEnergoAuthError("Invalid username or password")

    async def _get_password_stat(self) -> int | None:
        payload = await self._request(f"{SERVICE_PATH}/PasswordStatSet('{self.username}')")
        entity = self._entity(payload)
        for key in ("PassStat", "passStat", "PASS_STAT"):
            if key in entity:
                try:
                    return int(entity[key])
                except (TypeError, ValueError):
                    return None
        return None

    async def validate_credentials(self) -> None:
        if len(self.username) != ACCOUNT_NUMBER_LENGTH or not self.username.isdigit():
            raise SamaraEnergoAuthError("Account number must contain exactly 12 digits")

        await self._preauth_session()

        accounts = self._results(
            await self._request(
                f"{SERVICE_PATH}/Accounts",
                {
                    "$expand": (
                        "ContractAccounts,"
                        "ContractAccounts/Contracts/Premise,"
                        "ContractAccounts/Contracts/Devices"
                    )
                },
            )
        )
        if not accounts:
            raise SamaraEnergoAuthError("Invalid username or password")

        pass_stat = await self._get_password_stat()
        if pass_stat is None:
            raise SamaraEnergoApiError("Password status is unavailable")
        if pass_stat not in {1, 2}:
            raise SamaraEnergoAuthError("Account is blocked or unavailable")

    async def _get_account(self) -> dict[str, Any]:
        await self._preauth_session()
        payload = await self._request(
            f"{SERVICE_PATH}/Accounts",
            {
                "$expand": (
                    "ContractAccounts,"
                    "ContractAccounts/Contracts/Premise,"
                    "ContractAccounts/Contracts/Devices"
                )
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
        elif isinstance(premise, dict) and premise.get("AddressInfo"):
            info = premise["AddressInfo"]
            if isinstance(info, dict) and info.get("ShortForm"):
                return info["ShortForm"]

        parts = [
            premise.get("City") if isinstance(premise, dict) else None,
            premise.get("Street") if isinstance(premise, dict) else None,
            premise.get("HouseNumber") if isinstance(premise, dict) else None,
        ]
        address = ", ".join(part for part in parts if part)
        if address:
            return address
        return account.get("Description") or account.get("AccountID") or ""

    async def _get_amount_due(self, contract_account_id: str) -> tuple[float, datetime | None]:
        safe_id = contract_account_id.replace("'", "''")
        payload = await self._request(
            f"{SERVICE_PATH}/ContractAccounts('{safe_id}')/Invoices",
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

    async def _fetch_payment_documents(
        self,
        contract_account_id: str,
    ) -> list[dict[str, Any]]:
        """PaymentDocuments is a top-level entity set, not a ContractAccounts nav property."""
        safe_id = contract_account_id.replace("'", "''")
        attempts: list[tuple[str, dict[str, Any] | None]] = [
            (
                f"{SERVICE_PATH}/PaymentDocuments",
                {"$filter": f"ContractAccountID eq '{safe_id}'"},
            ),
            (f"{SERVICE_PATH}/PaymentDocuments", None),
        ]
        for path, params in attempts:
            try:
                payload = await self._request(path, params)
            except SamaraEnergoApiError as err:
                _LOGGER.debug("PaymentDocuments request failed for %s: %s", path, err)
                continue
            results = self._results(payload)
            if results:
                return results
        return []

    async def _get_last_payment(self, contract_account_id: str) -> tuple[float | None, datetime | None]:
        try:
            payments = [
                item
                for item in await self._fetch_payment_documents(contract_account_id)
                if str(item.get("PaymentStatusID")) == "9"
            ]
        except SamaraEnergoApiError as err:
            _LOGGER.warning("Unable to load payment documents: %s", err)
            return None, None

        if not payments:
            return None, None

        completed = max(
            payments,
            key=lambda item: _parse_sap_date(item.get("ExecutionDate"))
            or datetime.min.replace(tzinfo=UTC),
        )
        return _to_float(completed.get("Amount")), _parse_sap_date(completed.get("ExecutionDate"))

    async def _get_last_reading(self, device_id: str) -> tuple[float | None, datetime | None]:
        safe_id = device_id.replace("'", "''")
        payload = await self._request(
            f"{SERVICE_PATH}/Devices('{safe_id}')",
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
        safe_id = contract_id.replace("'", "''")
        period_payload = await self._request(
            f"{SERVICE_PATH}/GetCurrentBillingPeriod",
            {"ContractID": f"'{safe_id}'"},
        )
        period = self._entity(period_payload)
        start_date = _parse_sap_date(period.get("StartDate"))
        if not start_date:
            start_date = datetime.now(tz=UTC)

        history_start = start_date - timedelta(days=730)
        start_iso = history_start.strftime("%Y-%m-%dT00:00:00")

        payload = await self._request(
            f"{SERVICE_PATH}/Contracts('{safe_id}')/ContractConsumptionValues",
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
        last_payment_amount, last_payment_date = await self._get_last_payment(contract_account_id)
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
