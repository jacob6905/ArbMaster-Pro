"""
ArbMaster Pro - Platform Integrations

Connectors for prediction markets, exchanges, and DeFi protocols.
"""

from .base import BasePlatform, PlatformError
from .polymarket import PolymarketClient
from .kalshi import KalshiClient
from .cex import CEXClient
from .dex import DEXClient

__all__ = [
    "BasePlatform",
    "PlatformError",
    "PolymarketClient",
    "KalshiClient",
    "CEXClient",
    "DEXClient",
]
