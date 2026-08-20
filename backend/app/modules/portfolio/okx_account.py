import hmac
import hashlib
import base64
import httpx
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class OKXAccountClient:
    BASE_URL = "https://www.okx.com"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, passphrase: Optional[str] = None, timeout: float = 6.0):
        self.api_key = api_key or os.getenv("OKX_API_KEY", "")
        self.api_secret = api_secret or os.getenv("OKX_API_SECRET", "")
        self.passphrase = passphrase or os.getenv("OKX_API_PASSPHRASE", "")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret and self.passphrase)

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            bytes(self.api_secret, encoding="utf-8"),
            bytes(message, encoding="utf-8"),
            digestmod=hashlib.sha256
        )
        d = mac.digest()
        return base64.b64encode(d).decode("utf-8")

    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        sign = self._generate_signature(timestamp, method, request_path, body)
        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def fetch_trading_balances(self) -> List[Dict[str, Any]]:
        """Fetch read-only trading account balances (GET /api/v5/account/balance)"""
        if not self.is_configured():
            return []

        request_path = "/api/v5/account/balance"
        data = await self._authenticated_get(request_path)
        
        balances = []
        try:
            raw_data = data.get("data", [])
            if raw_data and "details" in raw_data[0]:
                for item in raw_data[0]["details"]:
                    ccy = item.get("ccy")
                    eq = item.get("eq", "0")
                    avail = item.get("availEq", item.get("availBal", "0"))
                    frozen = item.get("frozenBal", "0")
                    if float(eq) > 0 or float(avail) > 0:
                        balances.append({
                            "currency": ccy,
                            "balance": str(eq if float(eq) > 0 else avail),
                            "available": str(avail),
                            "frozen": str(frozen),
                            "source": "Trading"
                        })
        except Exception as e:
            logger.error(f"Error parsing OKX trading balances: {e}")
        return balances

    async def fetch_funding_balances(self) -> List[Dict[str, Any]]:
        """Fetch read-only funding account balances (GET /api/v5/asset/balances)"""
        if not self.is_configured():
            return []

        request_path = "/api/v5/asset/balances"
        data = await self._authenticated_get(request_path)
        
        balances = []
        try:
            raw_data = data.get("data", [])
            for item in raw_data:
                ccy = item.get("ccy")
                bal = item.get("bal", "0")
                avail = item.get("availBal", bal)
                frozen = item.get("frozenBal", "0")
                if float(bal) > 0:
                    balances.append({
                        "currency": ccy,
                        "balance": str(bal),
                        "available": str(avail),
                        "frozen": str(frozen),
                        "source": "Funding"
                    })
        except Exception as e:
            logger.error(f"Error parsing OKX funding balances: {e}")
        return balances

    async def _authenticated_get(self, request_path: str) -> Dict[str, Any]:
        headers = self._get_headers("GET", request_path)
        url = f"{self.BASE_URL}{request_path}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                res_json = response.json()
                if res_json.get("code") != "0":
                    msg = res_json.get("msg", "OKX account API error")
                    logger.warning(f"OKX account API error for {request_path}: code {res_json.get('code')}")
                    raise RuntimeError(f"OKX API error code {res_json.get('code')}: {msg}")
                return res_json
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching OKX account path {request_path}: status {e.response.status_code}")
                raise RuntimeError(f"OKX API HTTP error status {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Network error fetching OKX account path {request_path}")
                raise RuntimeError("Network error connecting to OKX account API")
