"""
ArbMaster Pro - Arbitrage Opportunity Models

Data structures representing different types of arbitrage opportunities.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ArbitrageType(str, Enum):
    """Types of arbitrage strategies supported."""

    BINARY_COMPLEMENT = "binary_complement"  # YES + NO < $1
    CROSS_PLATFORM = "cross_platform"  # Polymarket vs Kalshi
    MULTI_OUTCOME = "multi_outcome"  # Bundle arb
    DEX_CEX = "dex_cex"  # DEX-CEX price gaps
    TRIANGULAR = "triangular"  # Multi-pair loops
    FUNDING_RATE = "funding_rate"  # Spot-futures hedge
    YIELD_GAP = "yield_gap"  # DeFi lending spread
    TAIL_END = "tail_end"  # Near-settlement trading


class Platform(str, Enum):
    """Supported trading platforms."""

    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    BINANCE = "binance"
    KUCOIN = "kucoin"
    OKX = "okx"
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    AAVE = "aave"
    COMPOUND = "compound"


class ArbitrageOpportunity(BaseModel):
    """Base model for all arbitrage opportunities."""

    id: str = Field(description="Unique opportunity identifier")
    arb_type: ArbitrageType = Field(description="Type of arbitrage")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)

    # Profit metrics
    gross_profit_pct: Decimal = Field(description="Gross profit percentage")
    net_profit_pct: Decimal = Field(description="Net profit after fees")
    estimated_profit_usd: Decimal = Field(description="Estimated USD profit")

    # Cost breakdown
    total_cost: Decimal = Field(description="Total cost to execute")
    estimated_fees: Decimal = Field(default=Decimal("0"))
    estimated_slippage: Decimal = Field(default=Decimal("0"))
    estimated_gas: Decimal = Field(default=Decimal("0"))

    # Risk assessment
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    liquidity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Execution window
    time_sensitivity_ms: int = Field(
        default=5000, description="Time sensitivity in milliseconds"
    )

    def is_profitable(self, min_threshold: Decimal = Decimal("0.01")) -> bool:
        """Check if opportunity meets minimum profit threshold."""
        return self.net_profit_pct >= min_threshold

    def is_valid(self) -> bool:
        """Check if opportunity is still valid (not expired)."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at


class BinaryComplementArb(ArbitrageOpportunity):
    """
    Binary Complement Arbitrage: YES + NO < $1

    Buy both YES and NO shares when their combined cost is less than $1.00,
    guaranteeing profit at settlement regardless of outcome.
    """

    arb_type: ArbitrageType = ArbitrageType.BINARY_COMPLEMENT
    platform: Platform = Field(description="Source platform")

    # Market details
    market_id: str = Field(description="Market identifier")
    market_title: str = Field(default="", description="Human-readable market title")
    condition_id: str = Field(default="", description="Condition ID for the market")

    # Pricing
    yes_price: Decimal = Field(description="Best ask price for YES shares")
    no_price: Decimal = Field(description="Best ask price for NO shares")
    combined_price: Decimal = Field(description="YES + NO combined cost")

    # Liquidity
    yes_depth: Decimal = Field(default=Decimal("0"), description="YES side liquidity")
    no_depth: Decimal = Field(default=Decimal("0"), description="NO side liquidity")
    max_size: Decimal = Field(description="Maximum executable size")

    def calculate_profit(self) -> Decimal:
        """Calculate guaranteed profit per share."""
        return Decimal("1.0") - self.combined_price


class CrossPlatformArb(ArbitrageOpportunity):
    """
    Cross-Platform Arbitrage: Polymarket vs Kalshi

    Exploit price gaps between disconnected platforms by buying YES on one
    and NO on the other for a combined cost under $1.00.
    """

    arb_type: ArbitrageType = ArbitrageType.CROSS_PLATFORM

    # Platform A (e.g., Polymarket)
    platform_a: Platform
    market_id_a: str
    side_a: str  # "YES" or "NO"
    price_a: Decimal
    depth_a: Decimal = Field(default=Decimal("0"))

    # Platform B (e.g., Kalshi)
    platform_b: Platform
    market_id_b: str
    side_b: str  # "YES" or "NO"
    price_b: Decimal
    depth_b: Decimal = Field(default=Decimal("0"))

    # Market matching
    event_slug: str = Field(default="", description="Normalized event identifier")
    match_confidence: float = Field(
        default=1.0, description="Confidence in market matching"
    )


class MultiOutcomeArb(ArbitrageOpportunity):
    """
    Multi-Outcome Bundle Arbitrage

    Buy one share of every outcome when the sum is under $1.00,
    guaranteeing profit since exactly one outcome will resolve to $1.00.
    """

    arb_type: ArbitrageType = ArbitrageType.MULTI_OUTCOME
    platform: Platform

    # Market details
    market_id: str
    market_title: str = Field(default="")
    outcome_count: int = Field(description="Number of possible outcomes")

    # Outcome pricing
    outcome_prices: dict[str, Decimal] = Field(
        ..., description="Price for each outcome"
    )
    outcome_depths: dict[str, Decimal] = Field(
        default_factory=dict, description="Liquidity for each outcome"
    )

    # Bundle metrics
    bundle_cost: Decimal = Field(description="Total cost to buy all outcomes")
    weakest_leg: str = Field(default="", description="Outcome with lowest liquidity")
    weakest_depth: Decimal = Field(
        default=Decimal("0"), description="Depth of weakest leg"
    )


class DEXCEXArb(ArbitrageOpportunity):
    """
    DEX-CEX Price Gap Arbitrage

    Exploit price differences between decentralized and centralized exchanges.
    """

    arb_type: ArbitrageType = ArbitrageType.DEX_CEX

    # Asset
    token_symbol: str = Field(description="Token being arbitraged")
    token_address: Optional[str] = Field(default=None)

    # DEX side
    dex_platform: Platform
    dex_price: Decimal
    dex_pool_address: Optional[str] = Field(default=None)

    # CEX side
    cex_platform: Platform
    cex_price: Decimal
    cex_pair: str

    # Direction
    buy_on: str = Field(description="Platform to buy on (dex/cex)")
    sell_on: str = Field(description="Platform to sell on (dex/cex)")

    # Size constraints
    max_trade_size: Decimal


class FundingRateArb(ArbitrageOpportunity):
    """
    Funding Rate Arbitrage

    Hedge spot positions with perpetual futures to capture funding rate yield
    without directional market exposure.
    """

    arb_type: ArbitrageType = ArbitrageType.FUNDING_RATE
    platform: Platform

    # Asset
    symbol: str

    # Funding rate
    current_funding_rate: Decimal
    predicted_funding_rate: Decimal = Field(default=Decimal("0"))
    annualized_yield: Decimal

    # Position sizing
    spot_size: Decimal
    futures_size: Decimal

    # Timing
    next_funding_time: datetime
    funding_interval_hours: int = Field(default=8)


class YieldGapArb(ArbitrageOpportunity):
    """
    Yield Gap Arbitrage (DeFi Lending)

    Exploit APY differences between lending protocols.
    """

    arb_type: ArbitrageType = ArbitrageType.YIELD_GAP

    # Asset
    token_symbol: str
    token_address: str

    # Borrow side
    borrow_platform: Platform
    borrow_apy: Decimal

    # Lend side
    lend_platform: Platform
    lend_apy: Decimal

    # Spread
    net_yield_spread: Decimal
    use_flash_loan: bool = Field(default=False)


class TailEndArb(ArbitrageOpportunity):
    """
    Tail-End Trading (Near Settlement)

    Buy shares at 0.997-0.999 from panic-selling retail traders
    when outcome is nearly certain.
    """

    arb_type: ArbitrageType = ArbitrageType.TAIL_END
    platform: Platform

    # Market details
    market_id: str
    market_title: str = Field(default="")

    # Timing
    settlement_time: datetime
    hours_to_settlement: float

    # Position
    side: str  # The side we're buying
    current_price: Decimal
    target_exit_price: Decimal = Field(default=Decimal("1.0"))

    # Confidence
    outcome_probability: float = Field(ge=0.0, le=1.0)
