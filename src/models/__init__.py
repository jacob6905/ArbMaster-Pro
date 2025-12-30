"""
ArbMaster Pro - Data Models

Core data structures for arbitrage opportunities, trades, and market data.
"""

from .opportunity import (
    ArbitrageType,
    ArbitrageOpportunity,
    BinaryComplementArb,
    CrossPlatformArb,
    MultiOutcomeArb,
    DEXCEXArb,
    FundingRateArb,
)
from .market import (
    Market,
    OrderBook,
    OrderBookLevel,
    MarketOutcome,
    PredictionMarket,
)
from .trade import (
    Trade,
    TradeStatus,
    TradeLeg,
    TradeResult,
    Position,
)
from .risk import (
    RiskMetrics,
    CircuitBreakerState,
    DailyPnL,
)

__all__ = [
    # Opportunities
    "ArbitrageType",
    "ArbitrageOpportunity",
    "BinaryComplementArb",
    "CrossPlatformArb",
    "MultiOutcomeArb",
    "DEXCEXArb",
    "FundingRateArb",
    # Markets
    "Market",
    "OrderBook",
    "OrderBookLevel",
    "MarketOutcome",
    "PredictionMarket",
    # Trades
    "Trade",
    "TradeStatus",
    "TradeLeg",
    "TradeResult",
    "Position",
    # Risk
    "RiskMetrics",
    "CircuitBreakerState",
    "DailyPnL",
]
