"""
ArbMaster Pro - Market Data Models

Data structures for market data, order books, and prediction markets.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MarketStatus(str, Enum):
    """Market trading status."""

    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    DISPUTED = "disputed"
    PAUSED = "paused"


class MarketCategory(str, Enum):
    """Market category classification."""

    POLITICS = "politics"
    CRYPTO = "crypto"
    SPORTS = "sports"
    ESPORTS = "esports"
    ENTERTAINMENT = "entertainment"
    ECONOMICS = "economics"
    SCIENCE = "science"
    OTHER = "other"


class OrderBookLevel(BaseModel):
    """Single level in an order book."""

    price: Decimal = Field(..., description="Price level")
    size: Decimal = Field(..., description="Size available at this price")


class OrderBook(BaseModel):
    """Order book representation."""

    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> Optional[Decimal]:
        """Get best bid price."""
        if self.bids:
            return max(level.price for level in self.bids)
        return None

    @property
    def best_ask(self) -> Optional[Decimal]:
        """Get best ask price."""
        if self.asks:
            return min(level.price for level in self.asks)
        return None

    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price."""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None

    def total_bid_depth(self) -> Decimal:
        """Calculate total bid-side liquidity."""
        return sum(level.size for level in self.bids)

    def total_ask_depth(self) -> Decimal:
        """Calculate total ask-side liquidity."""
        return sum(level.size for level in self.asks)

    def depth_at_price(self, price: Decimal, side: str = "ask") -> Decimal:
        """Get depth available at or better than a price."""
        if side == "ask":
            return sum(
                level.size for level in self.asks if level.price <= price
            )
        else:
            return sum(
                level.size for level in self.bids if level.price >= price
            )


class MarketOutcome(BaseModel):
    """Single outcome in a prediction market."""

    outcome_id: str = Field(..., description="Unique outcome identifier")
    name: str = Field(..., description="Outcome name (e.g., 'YES', 'NO', 'Trump')")
    token_id: Optional[str] = Field(default=None, description="Token ID if applicable")

    # Pricing
    last_price: Decimal = Field(default=Decimal("0"))
    best_bid: Optional[Decimal] = Field(default=None)
    best_ask: Optional[Decimal] = Field(default=None)

    # Volume
    volume_24h: Decimal = Field(default=Decimal("0"))

    # Order book
    order_book: Optional[OrderBook] = Field(default=None)


class Market(BaseModel):
    """Generic market representation."""

    market_id: str = Field(..., description="Unique market identifier")
    platform: str = Field(..., description="Source platform")
    symbol: str = Field(default="", description="Trading symbol")
    base_asset: str = Field(default="", description="Base asset")
    quote_asset: str = Field(default="", description="Quote asset")

    # Pricing
    last_price: Decimal = Field(default=Decimal("0"))
    bid: Optional[Decimal] = Field(default=None)
    ask: Optional[Decimal] = Field(default=None)
    volume_24h: Decimal = Field(default=Decimal("0"))

    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PredictionMarket(BaseModel):
    """Prediction market representation."""

    market_id: str = Field(..., description="Unique market identifier")
    platform: str = Field(..., description="Source platform (polymarket, kalshi)")
    slug: str = Field(default="", description="URL-friendly identifier")
    condition_id: Optional[str] = Field(default=None, description="Polymarket condition ID")

    # Market info
    title: str = Field(..., description="Market question/title")
    description: str = Field(default="", description="Detailed description")
    category: MarketCategory = Field(default=MarketCategory.OTHER)
    status: MarketStatus = Field(default=MarketStatus.ACTIVE)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = Field(default=None)
    resolution_date: Optional[datetime] = Field(default=None)

    # Outcomes
    outcomes: list[MarketOutcome] = Field(default_factory=list)
    is_binary: bool = Field(default=True, description="True if YES/NO market")

    # Volume and liquidity
    volume_total: Decimal = Field(default=Decimal("0"))
    volume_24h: Decimal = Field(default=Decimal("0"))
    liquidity: Decimal = Field(default=Decimal("0"))

    # Resolution
    resolution: Optional[str] = Field(default=None, description="Resolved outcome")
    resolution_source: Optional[str] = Field(default=None)

    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def yes_outcome(self) -> Optional[MarketOutcome]:
        """Get YES outcome for binary markets."""
        if not self.is_binary:
            return None
        for outcome in self.outcomes:
            if outcome.name.upper() in ("YES", "Y", "TRUE"):
                return outcome
        return self.outcomes[0] if self.outcomes else None

    @property
    def no_outcome(self) -> Optional[MarketOutcome]:
        """Get NO outcome for binary markets."""
        if not self.is_binary:
            return None
        for outcome in self.outcomes:
            if outcome.name.upper() in ("NO", "N", "FALSE"):
                return outcome
        return self.outcomes[1] if len(self.outcomes) > 1 else None

    def hours_to_settlement(self) -> Optional[float]:
        """Calculate hours until settlement."""
        if self.end_date:
            delta = self.end_date - datetime.utcnow()
            return delta.total_seconds() / 3600
        return None

    def is_near_settlement(self, hours_threshold: float = 24.0) -> bool:
        """Check if market is within settlement threshold."""
        hours = self.hours_to_settlement()
        return hours is not None and hours <= hours_threshold


class MarketPair(BaseModel):
    """Matched markets across platforms for cross-platform arbitrage."""

    pair_id: str = Field(...)
    event_slug: str = Field(..., description="Normalized event identifier")

    polymarket: Optional[PredictionMarket] = Field(default=None)
    kalshi: Optional[PredictionMarket] = Field(default=None)

    match_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    last_checked: datetime = Field(default_factory=datetime.utcnow)

    def has_both_platforms(self) -> bool:
        """Check if market exists on both platforms."""
        return self.polymarket is not None and self.kalshi is not None


class TokenPrice(BaseModel):
    """Token price data for DEX/CEX arbitrage."""

    symbol: str = Field(...)
    address: Optional[str] = Field(default=None)

    # Prices by platform
    prices: dict[str, Decimal] = Field(default_factory=dict)

    # Liquidity by platform
    liquidity: dict[str, Decimal] = Field(default_factory=dict)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_spread(self, platform_a: str, platform_b: str) -> Optional[Decimal]:
        """Calculate price spread between two platforms."""
        if platform_a in self.prices and platform_b in self.prices:
            return abs(self.prices[platform_a] - self.prices[platform_b])
        return None

    def get_spread_pct(self, platform_a: str, platform_b: str) -> Optional[Decimal]:
        """Calculate percentage spread between platforms."""
        if platform_a in self.prices and platform_b in self.prices:
            min_price = min(self.prices[platform_a], self.prices[platform_b])
            if min_price > 0:
                spread = abs(self.prices[platform_a] - self.prices[platform_b])
                return spread / min_price
        return None
