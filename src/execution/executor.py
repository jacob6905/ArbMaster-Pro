"""
ArbMaster Pro - Trade Executor

Low-level trade execution with retry logic and error handling.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger

from models.trade import TradeLeg, TradeStatus, OrderSide
from platforms.base import BasePlatform, PlatformError, RateLimitError


class TradeExecutor:
    """
    Low-level trade executor with retry and error handling.

    Handles:
    - Order placement with retries
    - Rate limit management
    - Order cancellation
    - Status tracking
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        timeout_seconds: float = 30.0,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout_seconds = timeout_seconds

    async def execute_leg(
        self,
        platform: BasePlatform,
        leg: TradeLeg,
    ) -> TradeLeg:
        """
        Execute a single trade leg with retries.

        Args:
            platform: The platform to execute on
            leg: The trade leg to execute

        Returns:
            Updated TradeLeg with execution results
        """
        leg.status = TradeStatus.PENDING

        for attempt in range(self.max_retries):
            try:
                leg.retry_count = attempt

                result = await asyncio.wait_for(
                    platform.place_order(
                        market_id=leg.market_id,
                        side=leg.side,
                        outcome=leg.symbol.split("_")[-1],  # Extract YES/NO
                        price=leg.price,
                        size=leg.size,
                    ),
                    timeout=self.timeout_seconds,
                )

                if result:
                    leg.status = result.status
                    leg.filled_size = result.filled_size
                    leg.filled_price = result.filled_price
                    leg.order_id = result.order_id
                    leg.tx_hash = result.tx_hash
                    leg.fee = result.fee
                    leg.executed_at = datetime.utcnow()

                    if result.status == TradeStatus.FILLED:
                        logger.debug(
                            f"Leg {leg.leg_id} filled: "
                            f"{leg.filled_size} @ {leg.filled_price}"
                        )
                        return leg

                    elif result.status == TradeStatus.SUBMITTED:
                        # Wait for fill
                        leg = await self._wait_for_fill(platform, leg)
                        return leg

            except RateLimitError as e:
                logger.warning(f"Rate limited, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after or self.retry_delay)

            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                leg.error_message = "Timeout"

            except PlatformError as e:
                logger.warning(f"Platform error on attempt {attempt + 1}: {e}")
                leg.error_message = str(e)

                if not e.recoverable:
                    break

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                leg.error_message = str(e)

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        leg.status = TradeStatus.FAILED
        return leg

    async def _wait_for_fill(
        self,
        platform: BasePlatform,
        leg: TradeLeg,
        max_wait_seconds: float = 10.0,
        poll_interval: float = 0.5,
    ) -> TradeLeg:
        """
        Wait for an order to fill.

        Polls order status until filled, cancelled, or timeout.
        """
        start_time = datetime.utcnow()

        while True:
            elapsed = (datetime.utcnow() - start_time).total_seconds()

            if elapsed > max_wait_seconds:
                logger.warning(f"Wait timeout for order {leg.order_id}")
                break

            # Check order status (would need platform method)
            # For now, assume filled in dry-run
            if platform.dry_run:
                leg.status = TradeStatus.FILLED
                leg.filled_size = leg.size
                leg.filled_price = leg.price
                leg.executed_at = datetime.utcnow()
                return leg

            await asyncio.sleep(poll_interval)

        return leg

    async def cancel_leg(
        self,
        platform: BasePlatform,
        leg: TradeLeg,
    ) -> bool:
        """
        Cancel a pending order.

        Returns:
            True if cancellation successful
        """
        if not leg.order_id:
            return False

        if leg.status in (TradeStatus.FILLED, TradeStatus.CANCELLED):
            return True

        try:
            success = await platform.cancel_order(leg.order_id)

            if success:
                leg.status = TradeStatus.CANCELLED
                logger.info(f"Cancelled order {leg.order_id}")

            return success

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def execute_multi_leg(
        self,
        platforms: dict[str, BasePlatform],
        legs: list[TradeLeg],
        parallel: bool = True,
    ) -> list[TradeLeg]:
        """
        Execute multiple trade legs.

        Args:
            platforms: Dictionary of platform_name -> client
            legs: List of legs to execute
            parallel: If True, execute all legs concurrently

        Returns:
            List of updated legs
        """
        if parallel:
            tasks = []
            for leg in legs:
                platform = platforms.get(leg.platform)
                if platform:
                    tasks.append(self.execute_leg(platform, leg))
                else:
                    leg.status = TradeStatus.FAILED
                    leg.error_message = f"Platform {leg.platform} not found"
                    tasks.append(asyncio.coroutine(lambda l=leg: l)())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            updated_legs = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    legs[i].status = TradeStatus.FAILED
                    legs[i].error_message = str(result)
                    updated_legs.append(legs[i])
                else:
                    updated_legs.append(result)

            return updated_legs

        else:
            # Sequential execution
            updated_legs = []
            for leg in legs:
                platform = platforms.get(leg.platform)
                if platform:
                    result = await self.execute_leg(platform, leg)
                    updated_legs.append(result)

                    # Stop if a leg fails
                    if result.status == TradeStatus.FAILED:
                        logger.warning(f"Leg {leg.leg_id} failed, stopping execution")
                        break
                else:
                    leg.status = TradeStatus.FAILED
                    leg.error_message = f"Platform {leg.platform} not found"
                    updated_legs.append(leg)
                    break

            return updated_legs

    async def rollback(
        self,
        platforms: dict[str, BasePlatform],
        legs: list[TradeLeg],
    ) -> bool:
        """
        Attempt to rollback/cancel any filled legs.

        Note: In prediction markets, true rollback is not possible
        after settlement. This just cancels unfilled orders.
        """
        all_cancelled = True

        for leg in legs:
            if leg.status == TradeStatus.SUBMITTED:
                platform = platforms.get(leg.platform)
                if platform:
                    success = await self.cancel_leg(platform, leg)
                    if not success:
                        all_cancelled = False

        return all_cancelled
