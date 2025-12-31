"""
ArbMaster Pro - Liquidity Checker

Verify market liquidity meets minimum thresholds before execution.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional
from loguru import logger

from models.market import OrderBook
from models.risk import LiquidityCheck, SlippageEstimate


class LiquidityChecker:
    """
    Comprehensive liquidity checking for trade execution.

    Ensures:
    - Minimum depth threshold ($10k default)
    - Trade size won't move market excessively
    - Slippage is within acceptable bounds
    """

    def __init__(
        self,
        min_depth_usd: Decimal = Decimal("10000"),
        max_trade_depth_pct: float = 0.1,  # Max 10% of depth per trade
        max_slippage_pct: float = 0.002,  # 0.2% max slippage
    ):
        self.min_depth_usd = min_depth_usd
        self.max_trade_depth_pct = max_trade_depth_pct
        self.max_slippage_pct = max_slippage_pct

    def check_depth(
        self,
        market_id: str,
        platform: str,
        order_book: OrderBook,
    ) -> LiquidityCheck:
        """
        Check if market has sufficient liquidity.

        Args:
            market_id: Market identifier
            platform: Trading platform
            order_book: Current order book

        Returns:
            LiquidityCheck result
        """
        bid_depth = order_book.total_bid_depth()
        ask_depth = order_book.total_ask_depth()
        total_depth = bid_depth + ask_depth

        # Calculate spread
        spread_pct = 0.0
        if order_book.best_bid and order_book.best_ask and order_book.best_bid > 0:
            spread_pct = float(
                (order_book.best_ask - order_book.best_bid) / order_book.best_bid
            )

        passes = total_depth >= self.min_depth_usd

        return LiquidityCheck(
            market_id=market_id,
            platform=platform,
            bid_depth_10k=bid_depth,
            ask_depth_10k=ask_depth,
            total_depth=total_depth,
            passes_threshold=passes,
            threshold_usd=self.min_depth_usd,
            bid_ask_spread_pct=spread_pct,
        )

    def estimate_slippage(
        self,
        market_id: str,
        platform: str,
        order_book: OrderBook,
        trade_size: Decimal,
        side: str = "buy",
    ) -> SlippageEstimate:
        """
        Estimate slippage for a potential trade.

        Uses order book depth to model price impact.
        """
        if side.lower() == "buy":
            levels = order_book.asks
            total_depth = order_book.total_ask_depth()
        else:
            levels = order_book.bids
            total_depth = order_book.total_bid_depth()

        if not levels or total_depth == 0:
            return SlippageEstimate(
                market_id=market_id,
                platform=platform,
                trade_size=trade_size,
                side=side,
                estimated_slippage_pct=1.0,
                estimated_slippage_usd=trade_size,
                worst_case_slippage_pct=1.0,
                recommended_max_size=Decimal("0"),
                execution_viable=False,
            )

        # Calculate weighted average price for the trade
        remaining = trade_size
        total_cost = Decimal("0")
        fills_at_levels = 0

        for level in levels:
            if remaining <= 0:
                break

            fill_size = min(remaining, level.size)
            total_cost += fill_size * level.price
            remaining -= fill_size
            fills_at_levels += 1

        if remaining > 0:
            # Not enough liquidity
            return SlippageEstimate(
                market_id=market_id,
                platform=platform,
                trade_size=trade_size,
                side=side,
                estimated_slippage_pct=1.0,
                estimated_slippage_usd=trade_size,
                worst_case_slippage_pct=1.0,
                fills_at_levels=fills_at_levels,
                recommended_max_size=total_depth * Decimal(str(self.max_trade_depth_pct)),
                execution_viable=False,
            )

        # Calculate slippage
        best_price = levels[0].price
        avg_price = total_cost / trade_size

        if side.lower() == "buy":
            slippage_pct = float((avg_price - best_price) / best_price)
        else:
            slippage_pct = float((best_price - avg_price) / best_price)

        slippage_usd = trade_size * Decimal(str(abs(slippage_pct)))

        # Price impact (how much we move the market)
        price_impact = float(trade_size / total_depth)

        # Worst case: assume 3x normal slippage
        worst_case = slippage_pct * 3

        # Recommended max size (10% of depth)
        recommended_max = total_depth * Decimal(str(self.max_trade_depth_pct))

        # Check viability
        viable = (
            slippage_pct <= self.max_slippage_pct
            and trade_size <= recommended_max
        )

        return SlippageEstimate(
            market_id=market_id,
            platform=platform,
            trade_size=trade_size,
            side=side,
            estimated_slippage_pct=slippage_pct,
            estimated_slippage_usd=slippage_usd,
            worst_case_slippage_pct=worst_case,
            price_impact_pct=price_impact,
            fills_at_levels=fills_at_levels,
            recommended_max_size=recommended_max,
            execution_viable=viable,
        )

    def calculate_max_size(
        self,
        order_book: OrderBook,
        max_slippage: Optional[float] = None,
    ) -> Decimal:
        """
        Calculate maximum trade size for acceptable slippage.

        Binary search to find the size that hits slippage threshold.
        """
        if max_slippage is None:
            max_slippage = self.max_slippage_pct

        total_depth = order_book.total_ask_depth()

        if total_depth == 0:
            return Decimal("0")

        # Start with 10% of depth
        test_size = total_depth * Decimal("0.1")
        low = Decimal("0")
        high = total_depth

        for _ in range(10):  # Binary search iterations
            estimate = self.estimate_slippage(
                market_id="",
                platform="",
                order_book=order_book,
                trade_size=test_size,
            )

            if estimate.estimated_slippage_pct <= max_slippage:
                low = test_size
                test_size = (test_size + high) / 2
            else:
                high = test_size
                test_size = (low + test_size) / 2

        return low

    def is_liquid_enough(
        self,
        order_book: OrderBook,
        required_size: Decimal,
    ) -> bool:
        """
        Quick check if order book can support the required size.
        """
        ask_depth = order_book.total_ask_depth()
        bid_depth = order_book.total_bid_depth()
        min_depth = min(ask_depth, bid_depth)

        # Need at least 10x the trade size in liquidity
        return min_depth >= required_size * 10
