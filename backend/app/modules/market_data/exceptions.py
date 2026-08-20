class MarketDataException(Exception):
    """Base exception for market data errors"""
    pass

class InvalidAssetError(MarketDataException):
    """Raised when an unsupported or invalid asset symbol is requested"""
    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Unsupported or invalid asset symbol: {symbol}")

class InvalidTimeframeError(MarketDataException):
    """Raised when an invalid timeframe is requested"""
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        super().__init__(f"Invalid timeframe: {timeframe}. Supported: 1m, 5m, 15m, 1H, 4H, 1D")

class ProviderUnavailableError(MarketDataException):
    """Raised when the external data provider is unreachable or returns an error"""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"Data provider '{provider}' error: {message}")

class ProviderTimeoutError(ProviderUnavailableError):
    """Raised when external HTTP requests time out"""
    def __init__(self, provider: str):
        super().__init__(provider, "Request timed out")
