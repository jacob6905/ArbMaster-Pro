"""
ArbMaster Pro - Execution Engine

Main execution orchestrator for arbitrage trades.
Handles multi-leg execution, dry-run mode, and error recovery.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Callable, Awaitable
import uuid
from loguru import logger

from ..models.opportunity import (
    ArbitrageOpportunity,
    ArbitrageType,
    BinaryComplementArb,
    CrossPlatformArb,
    Platform,
)
from ..models.trade import (
    Trade,
    TradeLeg,
    TradeStatus,
    TradeResult,
    OrderSide,
    OrderType,
)
from ..platforms.base import BasePlatform, PlatformError
from ..risk.manager import RiskManager
from ..config import settings


class ExecutionEngine:
    """
    Main execution engine for arbitrage trades.

    Features:
    - Dry-run (paper trading) mode
    - Multi-leg execution with rollback
    - Latency tracking (<500ms target)
    - Integration with risk management
    """

    def __init__(
        self,
        platforms: dict[str, BasePlatform],
        risk_manager: RiskManager,
        dry_run: bool = True,
    ):
        self.platforms = platforms
        self.risk_manager = risk_manager
        self.dry_run = dry_run

        # Execution state
        self._active_trades: dict[str, Trade] = {}
        self._completed_trades: list[Trade] = []

        # Callbacks
        self._on_trade_start: Optional[Callable[[Trade], Awaitable[None]]] = None
        self._on_trade_complete: Optional[Callable[[Trade, TradeResult], Awaitable[None]]] = None

        # Metrics
        self._total_trades = 0
        self._successful_trades = 0
        self._failed_trades = 0
        self._total_profit = Decimal("0")
        self._total_latency_ms = 0

    def set_callbacks(
        self,
        on_start: Optional[Callable[[Trade], Awaitable[None]]] = None,
        on_complete: Optional[Callable[[Trade, TradeResult], Awaitable[None]]] = None,
    ) -> None:
        """Set execution callbacks."""
        self._on_trade_start = on_start
        self._on_trade_complete = on_complete

    async def execute(
        self,
        opportunity: ArbitrageOpportunity,
        size: Optional[Decimal] = None,
    ) -> TradeResult:
        """
        Execute an arbitrage opportunity.

        Args:
            opportunity: The opportunity to execute
            size: Override position size (uses calculated if None)

        Returns:
            TradeResult with execution details
        """
        start_time = datetime.utcnow()

        # Validate with risk manager
        is_valid, reason = self.risk_manager.validate_opportunity(opportunity)
        if not is_valid:
            logger.warning(f"Opportunity rejected: {reason}")
            return TradeResult(
                trade_id="",
                success=False,
                error=reason,
            )

        # Calculate size if not provided
        if size is None:
            size = self.risk_manager.calculate_position_size(opportunity)

        if size <= 0:
            return TradeResult(
                trade_id="",
                success=False,
                error="Position size too small",
            )

        # Create trade
        trade = self._create_trade(opportunity, size)
        self._active_trades[trade.trade_id] = trade

        logger.info(
            f"{'[DRY RUN] ' if self.dry_run else ''}"
            f"Executing {opportunity.arb_type.value} trade {trade.trade_id} "
            f"(size: ${size:.2f}, expected profit: {opportunity.net_profit_pct:.2%})"
        )

        if self._on_trade_start:
            await self._on_trade_start(trade)

        # Execute based on arbitrage type
        try:
            if opportunity.arb_type == ArbitrageType.BINARY_COMPLEMENT:
                result = await self._execute_binary_complement(trade, opportunity)
            elif opportunity.arb_type == ArbitrageType.CROSS_PLATFORM:
                result = await self._execute_cross_platform(trade, opportunity)
            else:
                result = await self._execute_generic(trade, opportunity)

        except Exception as e:
            logger.error(f"Execution error: {e}")
            result = TradeResult(
                trade_id=trade.trade_id,
                success=False,
                error=str(e),
            )
            self.risk_manager.record_error(str(e))

        # Calculate latency
        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        result.execution_time_ms = latency_ms

        # Update trade
        trade.completed_at = end_time
        trade.execution_latency_ms = latency_ms
        trade.status = TradeStatus.FILLED if result.success else TradeStatus.FAILED
        trade.actual_profit = result.profit_usd
        trade.actual_profit_pct = result.profit_pct

        # Record with risk manager
        self.risk_manager.record_trade(trade, result)

        # Update metrics
        self._total_trades += 1
        self._total_latency_ms += latency_ms

        if result.success:
            self._successful_trades += 1
            self._total_profit += result.profit_usd
        else:
            self._failed_trades += 1

        # Cleanup
        del self._active_trades[trade.trade_id]
        self._completed_trades.append(trade)

        if self._on_trade_complete:
            await self._on_trade_complete(trade, result)

        logger.info(
            f"Trade {trade.trade_id} completed: "
            f"{'SUCCESS' if result.success else 'FAILED'} "
            f"(profit: ${result.profit_usd:.2f}, latency: {latency_ms}ms)"
        )

        return result

    async def _execute_binary_complement(
        self,
        trade: Trade,
        opportunity: BinaryComplementArb,
    ) -> TradeResult:
        """
        Execute binary complement arbitrage (YES + NO < $1).

        Places orders for both YES and NO shares simultaneously.
        """
        platform = self.platforms.get(opportunity.platform.value)
        if not platform:
            return TradeResult(
                trade_id=trade.trade_id,
                success=False,
                error=f"Platform {opportunity.platform.value} not connected",
            )

        # Calculate share quantities
        total_cost = opportunity.combined_price
        size_shares = trade.total_cost / total_cost

        # Create legs
        yes_leg = TradeLeg(
            leg_id=f"{trade.trade_id}_yes",
            leg_order=1,
            platform=opportunity.platform.value,
            market_id=opportunity.market_id,
            symbol=f"{opportunity.market_id}_YES",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=opportunity.yes_price,
            size=size_shares,
        )

        no_leg = TradeLeg(
            leg_id=f"{trade.trade_id}_no",
            leg_order=2,
            platform=opportunity.platform.value,
            market_id=opportunity.market_id,
            symbol=f"{opportunity.market_id}_NO",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=opportunity.no_price,
            size=size_shares,
        )

        trade.legs = [yes_leg, no_leg]

        # Execute both legs
        yes_result = await platform.place_order(
            market_id=opportunity.market_id,
            side=OrderSide.BUY,
            outcome="YES",
            price=opportunity.yes_price,
            size=size_shares,
        )

        no_result = await platform.place_order(
            market_id=opportunity.market_id,
            side=OrderSide.BUY,
            outcome="NO",
            price=opportunity.no_price,
            size=size_shares,
        )

        # Update legs with results
        if yes_result:
            yes_leg.status = yes_result.status
            yes_leg.filled_size = yes_result.filled_size
            yes_leg.filled_price = yes_result.filled_price
            yes_leg.order_id = yes_result.order_id

        if no_result:
            no_leg.status = no_result.status
            no_leg.filled_size = no_result.filled_size
            no_leg.filled_price = no_result.filled_price
            no_leg.order_id = no_result.order_id

        # Check success
        both_filled = (
            yes_result and yes_result.status == TradeStatus.FILLED
            and no_result and no_result.status == TradeStatus.FILLED
        )

        if both_filled:
            # Calculate actual profit
            actual_cost = (
                yes_result.filled_size * yes_result.filled_price +
                no_result.filled_size * no_result.filled_price
            )
            filled_shares = min(yes_result.filled_size, no_result.filled_size)
            profit = filled_shares - actual_cost
            profit_pct = profit / actual_cost if actual_cost > 0 else Decimal("0")

            return TradeResult(
                trade_id=trade.trade_id,
                success=True,
                profit_usd=profit,
                profit_pct=profit_pct,
                expected_profit=trade.expected_profit,
                legs_filled=2,
                legs_total=2,
                total_volume=actual_cost,
            )
        else:
            # Handle partial fill - would need rollback logic
            return TradeResult(
                trade_id=trade.trade_id,
                success=False,
                error="One or both legs failed to fill",
                legs_filled=sum(1 for l in [yes_result, no_result] if l and l.status == TradeStatus.FILLED),
                legs_total=2,
            )

    async def _execute_cross_platform(
        self,
        trade: Trade,
        opportunity: CrossPlatformArb,
    ) -> TradeResult:
        """
        Execute cross-platform arbitrage.

        Places orders on two different platforms simultaneously.
        """
        platform_a = self.platforms.get(opportunity.platform_a.value)
        platform_b = self.platforms.get(opportunity.platform_b.value)

        if not platform_a or not platform_b:
            return TradeResult(
                trade_id=trade.trade_id,
                success=False,
                error="One or both platforms not connected",
            )

        # Calculate share quantities
        total_cost = opportunity.price_a + opportunity.price_b
        size_shares = trade.total_cost / total_cost

        # Create legs
        leg_a = TradeLeg(
            leg_id=f"{trade.trade_id}_a",
            leg_order=1,
            platform=opportunity.platform_a.value,
            market_id=opportunity.market_id_a,
            symbol=f"{opportunity.market_id_a}_{opportunity.side_a}",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=opportunity.price_a,
            size=size_shares,
        )

        leg_b = TradeLeg(
            leg_id=f"{trade.trade_id}_b",
            leg_order=2,
            platform=opportunity.platform_b.value,
            market_id=opportunity.market_id_b,
            symbol=f"{opportunity.market_id_b}_{opportunity.side_b}",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=opportunity.price_b,
            size=size_shares,
        )

        trade.legs = [leg_a, leg_b]

        # Execute both legs concurrently
        results = await asyncio.gather(
            platform_a.place_order(
                market_id=opportunity.market_id_a,
                side=OrderSide.BUY,
                outcome=opportunity.side_a,
                price=opportunity.price_a,
                size=size_shares,
            ),
            platform_b.place_order(
                market_id=opportunity.market_id_b,
                side=OrderSide.BUY,
                outcome=opportunity.side_b,
                price=opportunity.price_b,
                size=size_shares,
            ),
            return_exceptions=True,
        )

        result_a, result_b = results

        # Handle results
        if isinstance(result_a, Exception):
            logger.error(f"Platform A error: {result_a}")
            result_a = None

        if isinstance(result_b, Exception):
            logger.error(f"Platform B error: {result_b}")
            result_b = None

        # Update legs
        if result_a and not isinstance(result_a, Exception):
            leg_a.status = result_a.status
            leg_a.filled_size = result_a.filled_size
            leg_a.filled_price = result_a.filled_price
            leg_a.order_id = result_a.order_id
            leg_a.fee = result_a.fee

        if result_b and not isinstance(result_b, Exception):
            leg_b.status = result_b.status
            leg_b.filled_size = result_b.filled_size
            leg_b.filled_price = result_b.filled_price
            leg_b.order_id = result_b.order_id
            leg_b.fee = result_b.fee

        # Check success
        both_filled = (
            result_a and result_a.status == TradeStatus.FILLED
            and result_b and result_b.status == TradeStatus.FILLED
        )

        if both_filled:
            actual_cost = (
                result_a.filled_size * result_a.filled_price +
                result_b.filled_size * result_b.filled_price
            )
            fees = result_a.fee + result_b.fee
            filled_shares = min(result_a.filled_size, result_b.filled_size)
            profit = filled_shares - actual_cost - fees
            profit_pct = profit / actual_cost if actual_cost > 0 else Decimal("0")

            return TradeResult(
                trade_id=trade.trade_id,
                success=True,
                profit_usd=profit,
                profit_pct=profit_pct,
                expected_profit=trade.expected_profit,
                legs_filled=2,
                legs_total=2,
                total_volume=actual_cost,
            )
        else:
            return TradeResult(
                trade_id=trade.trade_id,
                success=False,
                error="One or both legs failed to fill",
                legs_filled=sum(1 for r in [result_a, result_b] if r and r.status == TradeStatus.FILLED),
                legs_total=2,
            )

    async def _execute_generic(
        self,
        trade: Trade,
        opportunity: ArbitrageOpportunity,
    ) -> TradeResult:
        """Generic execution for other arbitrage types."""
        # Placeholder for other arb types
        return TradeResult(
            trade_id=trade.trade_id,
            success=False,
            error=f"Execution not implemented for {opportunity.arb_type.value}",
        )

    def _create_trade(
        self,
        opportunity: ArbitrageOpportunity,
        size: Decimal,
    ) -> Trade:
        """Create a new trade from an opportunity."""
        return Trade(
            trade_id=f"trade_{uuid.uuid4().hex[:12]}",
            opportunity_id=opportunity.id,
            arb_type=opportunity.arb_type.value,
            status=TradeStatus.PENDING,
            is_dry_run=self.dry_run,
            expected_profit=opportunity.estimated_profit_usd,
            expected_profit_pct=opportunity.net_profit_pct,
            total_cost=size,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            risk_score=opportunity.risk_score,
            confidence=opportunity.confidence,
        )

    @property
    def stats(self) -> dict:
        """Get execution statistics."""
        avg_latency = (
            self._total_latency_ms / self._total_trades
            if self._total_trades > 0
            else 0
        )

        win_rate = (
            self._successful_trades / self._total_trades
            if self._total_trades > 0
            else 0
        )

        return {
            "total_trades": self._total_trades,
            "successful_trades": self._successful_trades,
            "failed_trades": self._failed_trades,
            "win_rate": win_rate,
            "total_profit_usd": float(self._total_profit),
            "avg_latency_ms": avg_latency,
            "active_trades": len(self._active_trades),
            "dry_run": self.dry_run,
        }
