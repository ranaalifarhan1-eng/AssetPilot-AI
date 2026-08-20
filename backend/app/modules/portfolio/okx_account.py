import httpx
import hmac
import hashlib
import base64
import time
import datetime
import os
import logging
import asyncio
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

from app.modules.portfolio.schemas import RawAccountBalance

logger = logging.getLogger(__name__)

class OKXAccountClient:
    """Secure client for communicating strictly with OKX read-only private endpoints."""
    BASE_URL = "https://www.okx.cab"
    FALLBACK_URL = "https://www.okx.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 2
    ):
        self.api_key = api_key if api_key is not None else os.getenv("OKX_API_KEY", "")
        self.api_secret = api_secret if api_secret is not None else os.getenv("OKX_API_SECRET", "")
        self.passphrase = passphrase if passphrase is not None else os.getenv("OKX_API_PASSPHRASE", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    def is_configured(self) -> bool:
        """Check if read-only credentials are fully provided without printing them."""
        return bool(
            self.api_key
            and len(self.api_key.strip()) > 0
            and self.api_secret
            and len(self.api_secret.strip()) > 0
            and self.passphrase
            and len(self.passphrase.strip()) > 0
        )

    async def fetch_trading_balances(self) -> List[RawAccountBalance]:
        """Fetch balances from Trading account via GET /api/v5/account/balance."""
        if not self.is_configured():
            return []
        
        request_path = "/api/v5/account/balance"
        data = await self._authenticated_get(request_path)
        
        raw_balances: List[RawAccountBalance] = []
        try:
            account_data = data.get("data", [])
            if account_data and len(account_data) > 0:
                details = account_data[0].get("details", [])
                for d in details:
                    ccy = d.get("ccy", "").upper()
                    cash_bal = d.get("cashBal", d.get("eq", "0"))
                    avail_bal = d.get("availBal", d.get("availEq", "0"))
                    frozen_bal = d.get("frozenBal", "0")
                    
                    if float(cash_bal or 0) > 0 or float(avail_bal or 0) > 0 or float(frozen_bal or 0) > 0:
                        raw_balances.append(
                            RawAccountBalance(
                                ccy=ccy,
                                total=str(cash_bal),
                                available=str(avail_bal),
                                frozen=str(frozen_bal),
                                source="Trading"
                            )
                        )
            return raw_balances
        except Exception as e:
            logger.error(f"Error parsing OKX Trading balance response: {e}")
            raise RuntimeError(f"Failed to parse Trading account response: {str(e)}")

    async def fetch_funding_balances(self) -> List[RawAccountBalance]:
        """Fetch balances from Funding account via GET /api/v5/asset/balances."""
        if not self.is_configured():
            return []

        request_path = "/api/v5/asset/balances"
        data = await self._authenticated_get(request_path)
        
        raw_balances: List[RawAccountBalance] = []
        try:
            asset_data = data.get("data", [])
            for d in asset_data:
                ccy = d.get("ccy", "").upper()
                bal = d.get("bal", "0")
                avail_bal = d.get("availBal", "0")
                frozen_bal = d.get("frozenBal", "0")
                
                if float(bal or 0) > 0 or float(avail_bal or 0) > 0 or float(frozen_bal or 0) > 0:
                    raw_balances.append(
                        RawAccountBalance(
                            ccy=ccy,
                            total=str(bal),
                            available=str(avail_bal),
                            frozen=str(frozen_bal),
                            source="Funding"
                        )
                    )
            return raw_balances
        except Exception as e:
            logger.error(f"Error parsing OKX Funding balance response: {e}")
            raise RuntimeError(f"Failed to parse Funding account response: {str(e)}")

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Create HMAC-SHA256 signature for OKX API authentication."""
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        mac = hmac.new(
            bytes(self.api_secret, encoding='utf8'),
            bytes(message, encoding='utf8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')

    async def _authenticated_get(self, request_path: str) -> Dict[str, Any]:
        """Send authenticated GET request to OKX endpoints with multi-domain fallback and retries."""
        endpoints = [self.BASE_URL, self.FALLBACK_URL]
        last_exception = None
        
        for base_url in endpoints:
            url = f"{base_url}{request_path}"
            for attempt in range(1, self.max_retries + 1):
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
                sign = self._generate_signature(timestamp, "GET", request_path)
                
                headers = {
                    **self._default_headers,
                    "OK-ACCESS-KEY": self.api_key,
                    "OK-ACCESS-SIGN": sign,
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": self.passphrase,
                }
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    try:
                        resp = await client.get(url, headers=headers)
                        resp.raise_for_status()
                        res_json = resp.json()
                        if res_json.get("code") != "0":
                            msg = res_json.get("msg", "Unknown OKX API error")
                            logger.error(f"OKX API error on {request_path}: code {res_json.get('code')} - {msg}")
                            raise RuntimeError(f"OKX API Error {res_json.get('code')}: {msg}")
                        return res_json
                    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
                        last_exception = e
                        logger.debug(f"OKX authenticated GET attempt {attempt}/{self.max_retries} failed for {request_path} on {base_url}: {e}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(0.3 * attempt)

        raise RuntimeError(f"Network error connecting to OKX account API after {self.max_retries} attempts: {str(last_exception)}")
