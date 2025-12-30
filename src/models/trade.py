"""
ArbMaster Pro - Trade Models

Data structures for trades, positions, and execution results.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class TradeStatus(str, Enum):
    """Trade execution status."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class TradeLeg(BaseModel):
    """Single leg of a multi-leg arbitrage trade."""

    leg_id: str = Field(..., description="Unique leg identifier")
    leg_order: int = Field(..., description="Execution order (1, 2, 3...)")

    # Platform and market
    platform: str = Field(...)
    market_id: str = Field(...)
    symbol: str = Field(default="")

    # Order details
    side: OrderSide = Field(...)
    order_type: OrderType = Field(default=OrderType.LIMIT)
    price: Decimal = Field(...)
    size: Decimal = Field(...)

    # Execution
    status: TradeStatus = Field(default=TradeStatus.PENDING)
    filled_size: Decimal = Field(default=Decimal("0"))
    filled_price: Optional[Decimal] = Field(default=None)
    order_id: Optional[str] = Field(default=None)
    tx_hash: Optional[str] = Field(default=None)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = Field(default=None)

    # Fees
    fee: Decimal = Field(default=Decimal("0"))
    fee_asset: str = Field(default="USD")

    # Error handling
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)

    @property
    def is_complete(self) -> bool:
        """Check if leg is fully executed."""
        return self.status in (TradeStatus.FILLED, TradeStatus.CANCELLED, TradeStatus.FAILED)

    @property
    def fill_ratio(self) -> Decimal:
        """Calculate fill ratio."""
        if self.size > 0:
            return self.filled_size / self.size
        return Decimal("0")


class Trade(BaseModel):
    """Complete arbitrage trade consisting of multiple legs."""

    trade_id: str = Field(..., description="Unique trade identifier")
    opportunity_id: str = Field(..., description="Source opportunity ID")
    arb_type: str = Field(..., description="Type of arbitrage")

    # Trade legs
    legs: list[TradeLeg] = Field(default_factory=list)

    # Overall status
    status: TradeStatus = Field(default=TradeStatus.PENDING)
    is_dry_run: bool = Field(default=False)

    # Expected vs actual
    expected_profit: Decimal = Field(default=Decimal("0"))
    expected_profit_pct: Decimal = Field(default=Decimal("0"))
    actual_profit: Optional[Decimal] = Field(default=None)
    actual_profit_pct: Optional[Decimal] = Field(default=None)

    # Costs
    total_cost: Decimal = Field(default=Decimal("0"))
    total_fees: Decimal = Field(default=Decimal("0"))
    total_gas: Decimal = Field(default=Decimal("0"))
    slippage: Decimal = Field(default=Decimal("0"))

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    detection_latency_ms: Optional[int] = Field(default=None)
    execution_latency_ms: Optional[int] = Field(default=None)

    # Risk metrics at time of trade
    risk_score: float = Field(default=0.0)
    confidence: float = Field(default=1.0)

    # Error handling
    error_message: Optional[str] = Field(default=None)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if all legs are complete."""
        return all(leg.is_complete for leg in self.legs)

    @property
    def is_profitable(self) -> bool:
        """Check if trade was profitable."""
        if self.actual_profit is not None:
            return self.actual_profit > 0
        return False

    def calculate_actual_profit(self) -> Decimal:
        """Calculate actual profit from filled legs."""
        if not self.is_complete:
            return Decimal("0")

        total_cost = sum(
            leg.filled_size * (leg.filled_price or leg.price) + leg.fee
            for leg in self.legs
            if leg.side == OrderSide.BUY and leg.status == TradeStatus.FILLED
        )

        total_return = sum(
            leg.filled_size * (leg.filled_price or leg.price) - leg.fee
            for leg in self.legs
            if leg.side == OrderSide.SELL and leg.status == TradeStatus.FILLED
        )

        # For prediction market arbs, the return is $1.00 per share at settlement
        if self.arb_type in ("binary_complement", "cross_platform", "multi_outcome"):
            filled_shares = min(
                leg.filled_size for leg in self.legs if leg.status == TradeStatus.FILLED
            )
            total_return = filled_shares  # $1.00 per share at settlement

        return total_return - total_cost


class TradeResult(BaseModel):
    """Result summary of a completed trade."""

    trade_id: str = Field(...)
    success: bool = Field(...)
    profit_usd: Decimal = Field(default=Decimal("0"))
    profit_pct: Decimal = Field(default=Decimal("0"))

    # Execution quality
    expected_profit: Decimal = Field(default=Decimal("0"))
    execution_slippage: Decimal = Field(default=Decimal("0"))
    execution_time_ms: int = Field(default=0)

    # Details
    legs_filled: int = Field(default=0)
    legs_total: int = Field(default=0)
    total_volume: Decimal = Field(default=Decimal("0"))

    # Errors
    error: Optional[str] = Field(default=None)

    @property
    def fill_rate(self) -> float:
        """Calculate fill rate."""
        if self.legs_total > 0:
            return self.legs_filled / self.legs_total
        return 0.0


class Position(BaseModel):
    """Current position in a market."""

    position_id: str = Field(...)
    platform: str = Field(...)
    market_id: str = Field(...)
    symbol: str = Field(default="")

    # Position details
    side: str = Field(...)  # "YES", "NO", "LONG", "SHORT"
    size: Decimal = Field(...)
    avg_entry_price: Decimal = Field(...)
    current_price: Optional[Decimal] = Field(default=None)

    # P&L
    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl: Decimal = Field(default=Decimal("0"))

    # Timing
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Related trades
    trade_ids: list[str] = Field(default_factory=list)

    @property
    def position_value(self) -> Decimal:
        """Calculate current position value."""
        price = self.current_price or self.avg_entry_price
        return self.size * price

    @property
    def cost_basis(self) -> Decimal:
        """Calculate cost basis."""
        return self.size * self.avg_entry_price


class PositionSummary(BaseModel):
    """Summary of all positions."""

    total_positions: int = Field(default=0)
    total_value: Decimal = Field(default=Decimal("0"))
    total_unrealized_pnl: Decimal = Field(default=Decimal("0"))
    total_realized_pnl: Decimal = Field(default=Decimal("0"))

    positions_by_platform: dict[str, list[Position]] = Field(default_factory=dict)
    positions_by_arb_type: dict[str, list[Position]] = Field(default_factory=dict)

    updated_at: datetime = Field(default_factory=datetime.utcnow)
