"""
ArbMaster Pro - Position Sizer

Calculate optimal position sizes based on Kelly Criterion,
risk limits, and liquidity constraints.
"""

from decimal import Decimal
from typing import Optional
from loguru import logger

from ..models.opportunity import ArbitrageOpportunity
from ..config import settings


class PositionSizer:
    """
    Position sizing calculator using Kelly Criterion and risk limits.

    Factors considered:
    - Available capital
    - Maximum position per market
    - Order book liquidity
    - Win rate and profit expectations
    - Risk tolerance
    """

    def __init__(
        self,
        total_capital: Decimal = Decimal("50000"),
        max_position_pct: float = 0.1,  # 10% of capital per position
        max_position_usd: Decimal = Decimal("5000"),
        min_position_usd: Decimal = Decimal("100"),
        kelly_fraction: float = 0.5,  # Use half-Kelly
    ):
        self.total_capital = total_capital
        self.max_position_pct = max_position_pct
        self.max_position_usd = max_position_usd
        self.min_position_usd = min_position_usd
        self.kelly_fraction = kelly_fraction

        # Track allocated capital
        self._allocated: dict[str, Decimal] = {}

    @property
    def available_capital(self) -> Decimal:
        """Calculate available capital."""
        total_allocated = sum(self._allocated.values())
        return max(Decimal("0"), self.total_capital - total_allocated)

    def calculate_size(
        self,
        opportunity: ArbitrageOpportunity,
        win_rate: Optional[float] = None,
        liquidity_depth: Optional[Decimal] = None,
    ) -> Decimal:
        """
        Calculate optimal position size for an opportunity.

        Args:
            opportunity: The arbitrage opportunity
            win_rate: Historical win rate (0-1), default 0.9 for arb
            liquidity_depth: Available liquidity in USD

        Returns:
            Recommended position size in USD
        """
        # Default win rate for arbitrage (very high)
        if win_rate is None:
            win_rate = 0.90

        # Calculate Kelly optimal size
        kelly_size = self._kelly_criterion(
            win_rate=win_rate,
            profit_pct=float(opportunity.net_profit_pct),
            loss_pct=0.02,  # Assume 2% loss on failed arb
        )

        # Apply position limits
        max_by_capital = self.total_capital * Decimal(str(self.max_position_pct))
        max_by_limit = self.max_position_usd
        max_by_available = self.available_capital

        # Apply liquidity constraint
        max_by_liquidity = Decimal("inf")
        if liquidity_depth:
            # Don't take more than 10% of available liquidity
            max_by_liquidity = liquidity_depth * Decimal("0.1")

        # Get opportunity-specific max
        if hasattr(opportunity, "max_size"):
            max_by_opp = opportunity.max_size * opportunity.total_cost
        else:
            max_by_opp = Decimal("inf")

        # Take minimum of all constraints
        max_size = min(
            kelly_size,
            max_by_capital,
            max_by_limit,
            max_by_available,
            max_by_liquidity,
            max_by_opp,
        )

        # Apply minimum threshold
        if max_size < self.min_position_usd:
            return Decimal("0")

        # Round to reasonable precision
        return Decimal(str(round(float(max_size), 2)))

    def _kelly_criterion(
        self,
        win_rate: float,
        profit_pct: float,
        loss_pct: float,
    ) -> Decimal:
        """
        Calculate Kelly Criterion optimal bet size.

        f* = (p * b - q) / b

        where:
        - p = probability of win
        - q = probability of loss (1 - p)
        - b = odds ratio (profit / loss)
        """
        if loss_pct == 0:
            loss_pct = 0.01  # Prevent division by zero

        p = win_rate
        q = 1 - p
        b = profit_pct / loss_pct

        kelly = (p * b - q) / b

        # Apply fractional Kelly
        kelly *= self.kelly_fraction

        # Clamp to reasonable range
        kelly = max(0.0, min(0.25, kelly))  # Max 25% of capital

        return self.total_capital * Decimal(str(kelly))

    def allocate(self, market_id: str, amount: Decimal) -> bool:
        """
        Allocate capital to a position.

        Returns:
            True if allocation successful
        """
        if amount > self.available_capital:
            logger.warning(
                f"Cannot allocate {amount}: only {self.available_capital} available"
            )
            return False

        self._allocated[market_id] = self._allocated.get(market_id, Decimal("0")) + amount
        logger.debug(f"Allocated {amount} to {market_id}")
        return True

    def deallocate(self, market_id: str, amount: Optional[Decimal] = None) -> None:
        """Remove capital allocation."""
        if market_id not in self._allocated:
            return

        if amount is None:
            del self._allocated[market_id]
        else:
            self._allocated[market_id] -= amount
            if self._allocated[market_id] <= 0:
                del self._allocated[market_id]

    def get_allocation(self, market_id: str) -> Decimal:
        """Get current allocation for a market."""
        return self._allocated.get(market_id, Decimal("0"))

    def get_total_allocated(self) -> Decimal:
        """Get total allocated capital."""
        return sum(self._allocated.values())

    def get_utilization(self) -> float:
        """Get capital utilization as percentage."""
        return float(self.get_total_allocated() / self.total_capital)

    def reset(self) -> None:
        """Reset all allocations."""
        self._allocated.clear()


class LiquidityChecker:
    """
    Check liquidity requirements for trade execution.
    """

    def __init__(
        self,
        min_depth_usd: Decimal = Decimal("10000"),
        max_trade_pct: float = 0.1,  # Max 10% of depth
    ):
        self.min_depth_usd = min_depth_usd
        self.max_trade_pct = max_trade_pct

    def check(
        self,
        market_id: str,
        bid_depth: Decimal,
        ask_depth: Decimal,
        required_size: Decimal,
    ) -> dict:
        """
        Check if liquidity is sufficient for a trade.

        Returns:
            Dictionary with check results
        """
        total_depth = bid_depth + ask_depth
        min_side_depth = min(bid_depth, ask_depth)

        passes = total_depth >= self.min_depth_usd
        max_recommended = min_side_depth * Decimal(str(self.max_trade_pct))

        return {
            "market_id": market_id,
            "bid_depth": float(bid_depth),
            "ask_depth": float(ask_depth),
            "total_depth": float(total_depth),
            "min_side_depth": float(min_side_depth),
            "passes_threshold": passes,
            "threshold_usd": float(self.min_depth_usd),
            "required_size": float(required_size),
            "max_recommended_size": float(max_recommended),
            "size_viable": required_size <= max_recommended,
            "utilization_pct": float(required_size / min_side_depth * 100) if min_side_depth > 0 else 100,
        }

    def estimate_slippage(
        self,
        trade_size: Decimal,
        order_book_depth: Decimal,
        spread_pct: float = 0.001,  # 0.1% base spread
    ) -> float:
        """
        Estimate slippage based on trade size and liquidity.

        Simple linear model: slippage increases with size/depth ratio.
        """
        if order_book_depth <= 0:
            return 1.0  # 100% slippage if no liquidity

        size_ratio = float(trade_size / order_book_depth)

        # Base spread + linear increase with size
        estimated_slippage = spread_pct + size_ratio * 0.1

        return min(estimated_slippage, 0.1)  # Cap at 10%
