"""
ArbMaster Pro - Base Platform Interface

Abstract base class for all platform integrations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
import asyncio
from loguru import logger

from models.market import Market, OrderBook, PredictionMarket
from models.trade import Trade, TradeLeg, TradeStatus, OrderSide


class PlatformError(Exception):
    """Base exception for platform errors."""

    def __init__(
        self,
        message: str,
        platform: str = "unknown",
        error_code: Optional[str] = None,
        recoverable: bool = True,
    ):
        self.message = message
        self.platform = platform
        self.error_code = error_code
        self.recoverable = recoverable
        super().__init__(f"[{platform}] {message}")


class RateLimitError(PlatformError):
    """Rate limit exceeded error."""

    def __init__(self, platform: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            platform=platform,
            recoverable=True,
        )


class InsufficientLiquidityError(PlatformError):
    """Insufficient liquidity for trade."""

    def __init__(
        self,
        platform: str,
        market_id: str,
        required: Decimal,
        available: Decimal,
    ):
        self.market_id = market_id
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient liquidity: need {required}, have {available}",
            platform=platform,
            recoverable=False,
        )


class OrderExecutionError(PlatformError):
    """Order execution failed."""

    def __init__(
        self,
        platform: str,
        order_id: Optional[str] = None,
        reason: str = "Unknown error",
    ):
        self.order_id = order_id
        super().__init__(
            f"Order execution failed: {reason}",
            platform=platform,
            recoverable=True,
        )


class BasePlatform(ABC):
    """Abstract base class for platform integrations."""

    platform_name: str = "base"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._connected = False
        self._last_request_time: Optional[datetime] = None
        self._rate_limit_remaining: int = 100
        self._request_count: int = 0

    @property
    def is_connected(self) -> bool:
        """Check if platform is connected."""
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the platform.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the platform."""
        pass

    @abstractmethod
    async def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[PredictionMarket]:
        """
        Fetch available markets.

        Args:
            category: Filter by category
            status: Filter by status (active, closed, resolved)
            limit: Maximum markets to return

        Returns:
            List of markets
        """
        pass

    @abstractmethod
    async def get_market(self, market_id: str) -> Optional[PredictionMarket]:
        """
        Fetch a specific market by ID.

        Args:
            market_id: Market identifier

        Returns:
            Market details or None if not found
        """
        pass

    @abstractmethod
    async def get_orderbook(
        self,
        market_id: str,
        outcome: str = "YES",
    ) -> Optional[OrderBook]:
        """
        Fetch order book for a market.

        Args:
            market_id: Market identifier
            outcome: Which outcome's order book (YES/NO)

        Returns:
            Order book data
        """
        pass

    @abstractmethod
    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        outcome: str,
        price: Decimal,
        size: Decimal,
        order_type: str = "limit",
    ) -> Optional[TradeLeg]:
        """
        Place an order on the platform.

        Args:
            market_id: Market identifier
            side: Buy or sell
            outcome: YES or NO
            price: Limit price
            size: Order size
            order_type: Order type (limit, market)

        Returns:
            Trade leg with order details
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order identifier

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    async def get_positions(self) -> list[dict[str, Any]]:
        """
        Fetch current positions.

        Returns:
            List of position dictionaries
        """
        pass

    @abstractmethod
    async def get_balance(self) -> Decimal:
        """
        Fetch available balance.

        Returns:
            Available balance in USD/USDC
        """
        pass

    async def health_check(self) -> bool:
        """
        Perform a health check on the platform connection.

        Returns:
            True if platform is healthy
        """
        try:
            if not self._connected:
                return False

            # Try to fetch balance as a simple check
            await self.get_balance()
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.platform_name}: {e}")
            return False

    async def _rate_limit_wait(self) -> None:
        """Wait if rate limit is near exhaustion."""
        if self._rate_limit_remaining < 5:
            wait_time = 1.0  # Default wait
            logger.debug(f"Rate limit low, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

    def _log_request(self, endpoint: str, method: str = "GET") -> None:
        """Log an API request."""
        self._request_count += 1
        self._last_request_time = datetime.utcnow()
        logger.debug(
            f"[{self.platform_name}] {method} {endpoint} "
            f"(request #{self._request_count})"
        )

    def _handle_dry_run_order(
        self,
        market_id: str,
        side: OrderSide,
        outcome: str,
        price: Decimal,
        size: Decimal,
    ) -> TradeLeg:
        """Create a simulated trade leg for dry run mode."""
        import uuid

        leg = TradeLeg(
            leg_id=f"dry_run_{uuid.uuid4().hex[:8]}",
            leg_order=1,
            platform=self.platform_name,
            market_id=market_id,
            symbol=f"{market_id}_{outcome}",
            side=side,
            price=price,
            size=size,
            status=TradeStatus.FILLED,
            filled_size=size,
            filled_price=price,
            order_id=f"sim_{uuid.uuid4().hex[:12]}",
            executed_at=datetime.utcnow(),
        )

        logger.info(
            f"[DRY RUN] Simulated {side.value} {size} {outcome} @ {price} "
            f"on {self.platform_name}"
        )

        return leg

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
