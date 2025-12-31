"""
ArbMaster Pro - Risk Manager

Central risk management orchestrator that coordinates circuit breakers,
position sizing, liquidity checks, and overall risk assessment.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from loguru import logger

from models.risk import (
    RiskMetrics,
    CircuitBreakerState,
    DailyPnL,
    RiskLevel,
    LiquidityCheck,
    SlippageEstimate,
)
from models.opportunity import ArbitrageOpportunity
from models.trade import Trade, TradeResult
from config import settings


class RiskManager:
    """
    Central risk management system.

    Responsibilities:
    - Monitor and enforce risk limits
    - Track daily P&L and drawdowns
    - Manage circuit breakers
    - Validate trades before execution
    - Calculate position sizes
    """

    def __init__(self):
        # Load config
        self.max_capital = Decimal(str(settings.risk.max_capital_usd))
        self.max_position_per_market = Decimal(str(settings.risk.max_position_per_market))
        self.max_total_positions = Decimal(str(settings.risk.max_total_positions))
        self.max_daily_loss = Decimal(str(settings.risk.max_daily_loss_usd))
        self.min_liquidity = Decimal(str(settings.risk.min_liquidity_depth))
        self.max_slippage = Decimal(str(settings.risk.max_slippage))
        self.min_profit = Decimal(str(settings.risk.min_profit_threshold))

        # State
        self._circuit_breaker = CircuitBreakerState(
            max_daily_loss=self.max_daily_loss,
            max_consecutive_errors=settings.risk.max_consecutive_errors,
            cooldown_seconds=settings.risk.cooldown_seconds,
        )
        self._daily_pnl: dict[date, DailyPnL] = {}
        self._metrics = RiskMetrics()
        self._positions: dict[str, Decimal] = {}  # market_id -> size

        # Tracking
        self._total_deployed = Decimal("0")
        self._consecutive_wins = 0
        self._consecutive_losses = 0

    @property
    def can_trade(self) -> bool:
        """Check if trading is allowed."""
        return not self._circuit_breaker.should_halt()

    @property
    def risk_level(self) -> RiskLevel:
        """Get current risk level."""
        return self._metrics.calculate_risk_level()

    def validate_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
    ) -> tuple[bool, str]:
        """
        Validate if an opportunity should be executed.

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check circuit breaker
        if self._circuit_breaker.should_halt():
            return False, "Circuit breaker active"

        # Check cooldown
        if self._circuit_breaker.is_in_cooldown():
            return False, "In cooldown period"

        # Check profit threshold
        if opportunity.net_profit_pct < self.min_profit:
            return False, f"Profit {opportunity.net_profit_pct:.2%} below minimum {self.min_profit:.2%}"

        # Check liquidity
        if opportunity.liquidity_score < 0.3:
            return False, "Insufficient liquidity"

        # Check capital limits
        if self._total_deployed >= self.max_total_positions:
            return False, "Maximum total positions reached"

        # Check market position limit
        market_id = getattr(opportunity, "market_id", None)
        if market_id and market_id in self._positions:
            current_pos = self._positions[market_id]
            if current_pos >= self.max_position_per_market:
                return False, "Maximum position per market reached"

        if daily.net_pnl < -self.max_daily_loss:
            self._circuit_breaker.trigger("Daily loss limit exceeded")
            return False, "Daily loss limit exceeded"

        # Check AI Insider Score (if available in opportunity metadata)
        if hasattr(opportunity, "metadata") and "ai_risk_score" in opportunity.metadata:
            ai_risk = opportunity.metadata["ai_risk_score"]
            if ai_risk > 0.6: # Threshold for "Insider Risk"
                return False, f"High AI-detected insider risk: {ai_risk}"

        return True, "Valid"

    def calculate_position_size(
        self,
        opportunity: ArbitrageOpportunity,
        max_risk_pct: float = 0.02,  # 2% of capital
    ) -> Decimal:
        """
        Calculate optimal position size for an opportunity.

        Uses Kelly Criterion with fractional sizing for safety.
        """
        available_capital = self.max_capital - self._total_deployed

        # Get opportunity-specific constraints
        if hasattr(opportunity, "max_size"):
            liquidity_limit = opportunity.max_size
        else:
            liquidity_limit = Decimal("inf")

        # Market position limit
        market_id = getattr(opportunity, "market_id", None)
        market_limit = self.max_position_per_market
        if market_id and market_id in self._positions:
            market_limit -= self._positions[market_id]

        # Risk-based limit
        risk_limit = available_capital * Decimal(str(max_risk_pct))

        # Take minimum of all limits
        max_size = min(
            available_capital,
            liquidity_limit,
            market_limit,
            risk_limit,
            self.max_position_per_market,
        )

        # Apply Kelly fraction if we have win rate data
        if self._metrics.win_rate > 0:
            kelly_fraction = self._calculate_kelly(
                self._metrics.win_rate,
                opportunity.net_profit_pct,
            )
            max_size *= kelly_fraction

        return max(Decimal("0"), max_size)

    def _calculate_kelly(
        self,
        win_rate: float,
        profit_pct: Decimal,
    ) -> Decimal:
        """Calculate Kelly Criterion fraction."""
        # Simplified Kelly: f* = (p * b - q) / b
        # where p = win probability, q = 1-p, b = odds ratio

        p = Decimal(str(win_rate))
        q = 1 - p
        b = 1 + profit_pct  # Odds ratio for even money

        kelly = (p * b - q) / b

        # Use half-Kelly for safety
        return max(Decimal("0"), min(Decimal("0.5"), kelly / 2))

    def record_trade(self, trade: Trade, result: TradeResult) -> None:
        """Record a completed trade for risk tracking."""
        today = date.today()
        daily = self._get_daily_pnl(today)

        # Update daily P&L
        daily.add_trade(
            pnl=result.profit_usd,
            fees=trade.total_fees,
            gas=trade.total_gas,
            volume=result.total_volume,
            strategy=trade.arb_type,
        )

        # Update circuit breaker
        if result.profit_usd < 0:
            self._circuit_breaker.record_loss(abs(result.profit_usd))
            self._consecutive_losses += 1
            self._consecutive_wins = 0
        else:
            self._circuit_breaker.consecutive_errors = 0
            self._consecutive_wins += 1
            self._consecutive_losses = 0

        # Update metrics
        self._update_metrics(result)

        # Update position tracking
        if hasattr(trade, "market_id"):
            market_id = trade.market_id
            if result.success:
                self._positions[market_id] = self._positions.get(
                    market_id, Decimal("0")
                ) + result.total_volume

        logger.info(
            f"Trade recorded: {'PROFIT' if result.success else 'LOSS'} "
            f"${result.profit_usd:.2f} "
            f"(daily: ${daily.net_pnl:.2f})"
        )

    def record_error(self, error_message: str) -> bool:
        """
        Record an execution error.

        Returns:
            True if circuit breaker was triggered
        """
        return self._circuit_breaker.record_error(error_message)

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker."""
        self._circuit_breaker.reset()
        logger.info("Circuit breaker reset")

    def reset_daily(self) -> None:
        """Reset daily counters (call at day boundary)."""
        self._circuit_breaker.reset_daily()

        # Create new daily record
        today = date.today()
        self._daily_pnl[today] = DailyPnL(date=today)

        logger.info("Daily risk counters reset")

    def _get_daily_pnl(self, day: date) -> DailyPnL:
        """Get or create daily P&L record."""
        if day not in self._daily_pnl:
            self._daily_pnl[day] = DailyPnL(date=day)
        return self._daily_pnl[day]

    def _update_metrics(self, result: TradeResult) -> None:
        """Update running risk metrics."""
        self._metrics.trades_today += 1

        if result.profit_usd > 0:
            self._metrics.winning_trades_today += 1
            self._metrics.realized_pnl_today += result.profit_usd
        else:
            self._metrics.losing_trades_today += 1
            self._metrics.realized_pnl_today += result.profit_usd

        # Update win rate
        if self._metrics.trades_today > 0:
            self._metrics.win_rate = (
                self._metrics.winning_trades_today / self._metrics.trades_today
            )

        # Update latency metrics
        if result.execution_time_ms > 0:
            old_avg = self._metrics.avg_execution_latency_ms
            n = self._metrics.trades_today
            self._metrics.avg_execution_latency_ms = (
                old_avg * (n - 1) + result.execution_time_ms
            ) / n

        # Update risk level
        self._metrics.risk_level = self._metrics.calculate_risk_level()

    def get_metrics(self) -> RiskMetrics:
        """Get current risk metrics."""
        self._metrics.circuit_breaker = self._circuit_breaker
        self._metrics.timestamp = datetime.utcnow()
        return self._metrics

    def get_daily_summary(self, day: Optional[date] = None) -> DailyPnL:
        """Get P&L summary for a day."""
        if day is None:
            day = date.today()
        return self._get_daily_pnl(day)

    def estimate_slippage(
        self,
        market_id: str,
        trade_size: Decimal,
        order_book_depth: Decimal,
    ) -> SlippageEstimate:
        """
        Estimate slippage for a potential trade.
        """
        # Simple model: slippage increases with size/depth ratio
        size_ratio = trade_size / max(order_book_depth, Decimal("1"))

        # Base slippage of 0.05%, increases linearly with size ratio
        base_slippage = Decimal("0.0005")
        estimated_slippage = base_slippage * (1 + size_ratio * 10)

        return SlippageEstimate(
            market_id=market_id,
            platform="estimate",
            trade_size=trade_size,
            side="buy",
            estimated_slippage_pct=float(estimated_slippage),
            estimated_slippage_usd=trade_size * estimated_slippage,
            worst_case_slippage_pct=float(estimated_slippage * 3),
            price_impact_pct=float(size_ratio * Decimal("0.01")),
            recommended_max_size=order_book_depth * Decimal("0.1"),
            execution_viable=estimated_slippage < self.max_slippage,
        )

    def check_liquidity(
        self,
        market_id: str,
        platform: str,
        bid_depth: Decimal,
        ask_depth: Decimal,
    ) -> LiquidityCheck:
        """
        Check if liquidity meets requirements.
        """
        total_depth = bid_depth + ask_depth
        passes = total_depth >= self.min_liquidity

        return LiquidityCheck(
            market_id=market_id,
            platform=platform,
            bid_depth_10k=bid_depth,
            ask_depth_10k=ask_depth,
            total_depth=total_depth,
            passes_threshold=passes,
            threshold_usd=self.min_liquidity,
        )
