"""
ArbMaster Pro - Risk Management Models

Data structures for risk metrics, circuit breakers, and P&L tracking.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CircuitBreakerStatus(str, Enum):
    """Circuit breaker status."""

    NORMAL = "normal"
    WARNING = "warning"
    TRIGGERED = "triggered"
    COOLDOWN = "cooldown"


class RiskLevel(str, Enum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitBreakerState(BaseModel):
    """State of the circuit breaker system."""

    status: CircuitBreakerStatus = Field(default=CircuitBreakerStatus.NORMAL)
    triggered_at: Optional[datetime] = Field(default=None)
    cooldown_until: Optional[datetime] = Field(default=None)

    # Trigger reasons
    triggered_by_loss: bool = Field(default=False)
    triggered_by_errors: bool = Field(default=False)
    triggered_by_volatility: bool = Field(default=False)
    trigger_reason: Optional[str] = Field(default=None)

    # Counters
    consecutive_errors: int = Field(default=0)
    daily_loss: Decimal = Field(default=Decimal("0"))
    error_messages: list[str] = Field(default_factory=list)

    # Thresholds
    max_daily_loss: Decimal = Field(default=Decimal("500"))
    max_consecutive_errors: int = Field(default=5)
    cooldown_seconds: int = Field(default=60)

    def should_halt(self) -> bool:
        """Check if trading should be halted."""
        return self.status in (
            CircuitBreakerStatus.TRIGGERED,
            CircuitBreakerStatus.COOLDOWN,
        )

    def is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period."""
        if self.cooldown_until is None:
            return False
        return datetime.utcnow() < self.cooldown_until

    def record_error(self, error_msg: str) -> bool:
        """Record an error and check if threshold exceeded."""
        self.consecutive_errors += 1
        self.error_messages.append(error_msg)

        # Keep only recent errors
        if len(self.error_messages) > 100:
            self.error_messages = self.error_messages[-100:]

        if self.consecutive_errors >= self.max_consecutive_errors:
            self.trigger(f"Max consecutive errors ({self.max_consecutive_errors})")
            return True
        return False

    def record_loss(self, loss_amount: Decimal) -> bool:
        """Record a loss and check if threshold exceeded."""
        self.daily_loss += loss_amount

        if self.daily_loss >= self.max_daily_loss:
            self.trigger(f"Max daily loss (${self.max_daily_loss})")
            return True
        return False

    def trigger(self, reason: str):
        """Trigger the circuit breaker."""
        self.status = CircuitBreakerStatus.TRIGGERED
        self.triggered_at = datetime.utcnow()
        self.trigger_reason = reason

    def start_cooldown(self):
        """Start cooldown period."""
        from datetime import timedelta

        self.status = CircuitBreakerStatus.COOLDOWN
        self.cooldown_until = datetime.utcnow() + timedelta(seconds=self.cooldown_seconds)

    def reset(self):
        """Reset circuit breaker to normal state."""
        self.status = CircuitBreakerStatus.NORMAL
        self.triggered_at = None
        self.cooldown_until = None
        self.triggered_by_loss = False
        self.triggered_by_errors = False
        self.triggered_by_volatility = False
        self.trigger_reason = None
        self.consecutive_errors = 0
        # Note: daily_loss should be reset at day boundary, not here

    def reset_daily(self):
        """Reset daily counters."""
        self.daily_loss = Decimal("0")
        self.consecutive_errors = 0
        self.error_messages.clear()


class RiskMetrics(BaseModel):
    """Current risk metrics snapshot."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Portfolio metrics
    total_capital: Decimal = Field(default=Decimal("0"))
    deployed_capital: Decimal = Field(default=Decimal("0"))
    available_capital: Decimal = Field(default=Decimal("0"))
    capital_utilization: float = Field(default=0.0)

    # P&L
    unrealized_pnl: Decimal = Field(default=Decimal("0"))
    realized_pnl_today: Decimal = Field(default=Decimal("0"))
    realized_pnl_total: Decimal = Field(default=Decimal("0"))

    # Position metrics
    total_positions: int = Field(default=0)
    largest_position_pct: float = Field(default=0.0)
    position_concentration: float = Field(default=0.0)

    # Performance metrics
    win_rate: float = Field(default=0.0)
    avg_win: Decimal = Field(default=Decimal("0"))
    avg_loss: Decimal = Field(default=Decimal("0"))
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)

    # Trade metrics
    trades_today: int = Field(default=0)
    winning_trades_today: int = Field(default=0)
    losing_trades_today: int = Field(default=0)

    # Latency metrics
    avg_detection_latency_ms: float = Field(default=0.0)
    avg_execution_latency_ms: float = Field(default=0.0)
    p95_latency_ms: float = Field(default=0.0)

    # Risk indicators
    current_drawdown_pct: float = Field(default=0.0)
    max_drawdown_pct: float = Field(default=0.0)
    var_95: Decimal = Field(default=Decimal("0"))  # Value at Risk
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)

    # Circuit breaker
    circuit_breaker: CircuitBreakerState = Field(default_factory=CircuitBreakerState)

    def calculate_risk_level(self) -> RiskLevel:
        """Calculate overall risk level."""
        if self.circuit_breaker.should_halt():
            return RiskLevel.CRITICAL

        # Check drawdown
        if self.current_drawdown_pct > 10:
            return RiskLevel.HIGH
        elif self.current_drawdown_pct > 5:
            return RiskLevel.MEDIUM

        # Check win rate
        if self.trades_today >= 10 and self.win_rate < 0.5:
            return RiskLevel.HIGH

        # Check position concentration
        if self.largest_position_pct > 30:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW


class DailyPnL(BaseModel):
    """Daily profit and loss record."""

    pnl_date: date  # Required field (renamed to avoid conflict with 'date' type)
    platform: str = Field(default="all")

    # P&L breakdown
    gross_profit: Decimal = Field(default=Decimal("0"))
    gross_loss: Decimal = Field(default=Decimal("0"))
    net_pnl: Decimal = Field(default=Decimal("0"))

    # Fees
    total_fees: Decimal = Field(default=Decimal("0"))
    gas_costs: Decimal = Field(default=Decimal("0"))

    # Trade counts
    total_trades: int = Field(default=0)
    winning_trades: int = Field(default=0)
    losing_trades: int = Field(default=0)

    # Volume
    total_volume: Decimal = Field(default=Decimal("0"))

    # By strategy
    pnl_by_strategy: dict[str, Decimal] = Field(default_factory=dict)
    trades_by_strategy: dict[str, int] = Field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.total_trades > 0:
            return self.winning_trades / self.total_trades
        return 0.0

    @property
    def profit_factor(self) -> float:
        """Calculate profit factor."""
        if self.gross_loss != 0:
            return float(abs(self.gross_profit / self.gross_loss))
        return float("inf") if self.gross_profit > 0 else 0.0

    def add_trade(
        self,
        pnl: Decimal,
        fees: Decimal = Decimal("0"),
        gas: Decimal = Decimal("0"),
        volume: Decimal = Decimal("0"),
        strategy: str = "unknown",
    ):
        """Add a trade to the daily record."""
        self.total_trades += 1
        self.total_fees += fees
        self.gas_costs += gas
        self.total_volume += volume

        if pnl > 0:
            self.gross_profit += pnl
            self.winning_trades += 1
        else:
            self.gross_loss += abs(pnl)
            self.losing_trades += 1

        self.net_pnl = self.gross_profit - self.gross_loss - self.total_fees - self.gas_costs

        # Track by strategy
        if strategy not in self.pnl_by_strategy:
            self.pnl_by_strategy[strategy] = Decimal("0")
            self.trades_by_strategy[strategy] = 0

        self.pnl_by_strategy[strategy] += pnl
        self.trades_by_strategy[strategy] += 1


class LiquidityCheck(BaseModel):
    """Liquidity check result."""

    market_id: str
    platform: str

    # Depth at price levels
    bid_depth_10k: Decimal = Field(default=Decimal("0"))
    ask_depth_10k: Decimal = Field(default=Decimal("0"))
    total_depth: Decimal = Field(default=Decimal("0"))

    # Assessment
    passes_threshold: bool = Field(default=False)
    threshold_usd: Decimal = Field(default=Decimal("10000"))

    # Spread
    bid_ask_spread_pct: float = Field(default=0.0)

    checked_at: datetime = Field(default_factory=datetime.utcnow)


class SlippageEstimate(BaseModel):
    """Slippage estimation for a potential trade."""

    market_id: str
    platform: str
    trade_size: Decimal
    side: str

    # Estimates
    estimated_slippage_pct: float
    estimated_slippage_usd: Decimal
    worst_case_slippage_pct: float

    # Price impact
    price_impact_pct: float = Field(default=0.0)
    fills_at_levels: int = Field(default=1)

    # Recommendation
    recommended_max_size: Decimal
    execution_viable: bool = Field(default=True)

    calculated_at: datetime = Field(default_factory=datetime.utcnow)
