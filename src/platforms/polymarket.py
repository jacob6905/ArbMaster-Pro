"""
ArbMaster Pro - Polymarket Integration

Client for interacting with Polymarket's CLOB (Central Limit Order Book).
Uses py-clob-client for official API access.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
import aiohttp
from loguru import logger

from .base import (
    BasePlatform,
    PlatformError,
    RateLimitError,
    InsufficientLiquidityError,
    OrderExecutionError,
)
from ..models.market import (
    PredictionMarket,
    MarketOutcome,
    OrderBook,
    OrderBookLevel,
    MarketStatus,
    MarketCategory,
)
from ..models.trade import TradeLeg, TradeStatus, OrderSide, OrderType
from ..config import settings


class PolymarketClient(BasePlatform):
    """
    Polymarket CLOB Client

    Connects to Polymarket's Central Limit Order Book for trading
    prediction market outcomes on Polygon.
    """

    platform_name = "polymarket"

    # API endpoints
    CLOB_URL = "https://clob.polymarket.com"
    GAMMA_URL = "https://gamma-api.polymarket.com"

    def __init__(self, dry_run: bool = True):
        super().__init__(dry_run=dry_run)
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = settings.polymarket.api_key
        self._api_secret = settings.polymarket.api_secret
        self._private_key = settings.polymarket.private_key

        # Cache for market data
        self._markets_cache: dict[str, PredictionMarket] = {}
        self._cache_ttl = 60  # seconds

    async def connect(self) -> bool:
        """Establish connection to Polymarket."""
        try:
            self._session = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )

            # Test connection with a simple request
            async with self._session.get(f"{self.GAMMA_URL}/markets") as response:
                if response.status == 200:
                    self._connected = True
                    logger.info("Connected to Polymarket CLOB")
                    return True
                else:
                    logger.error(f"Failed to connect to Polymarket: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error connecting to Polymarket: {e}")
            return False

    async def disconnect(self) -> None:
        """Close Polymarket connection."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False
        logger.info("Disconnected from Polymarket")

    async def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[PredictionMarket]:
        """
        Fetch available markets from Polymarket.

        Uses the Gamma API for market discovery.
        """
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        await self._rate_limit_wait()

        params: dict[str, Any] = {
            "limit": limit,
            "active": str(status == "active").lower(),
        }

        if category:
            params["tag"] = category

        self._log_request("/markets")

        try:
            async with self._session.get(
                f"{self.GAMMA_URL}/markets",
                params=params,
            ) as response:
                if response.status == 429:
                    raise RateLimitError(self.platform_name, retry_after=60)

                if response.status != 200:
                    raise PlatformError(
                        f"API error: {response.status}",
                        platform=self.platform_name,
                    )

                data = await response.json()

                markets = []
                for item in data:
                    market = self._parse_market(item)
                    if market:
                        markets.append(market)
                        self._markets_cache[market.market_id] = market

                return markets

        except aiohttp.ClientError as e:
            raise PlatformError(f"Network error: {e}", platform=self.platform_name)

    async def get_market(self, market_id: str) -> Optional[PredictionMarket]:
        """Fetch a specific market by condition ID."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        # Check cache first
        if market_id in self._markets_cache:
            return self._markets_cache[market_id]

        await self._rate_limit_wait()
        self._log_request(f"/markets/{market_id}")

        try:
            async with self._session.get(
                f"{self.GAMMA_URL}/markets/{market_id}"
            ) as response:
                if response.status == 404:
                    return None

                if response.status != 200:
                    raise PlatformError(
                        f"API error: {response.status}",
                        platform=self.platform_name,
                    )

                data = await response.json()
                market = self._parse_market(data)

                if market:
                    self._markets_cache[market_id] = market

                return market

        except aiohttp.ClientError as e:
            raise PlatformError(f"Network error: {e}", platform=self.platform_name)

    async def get_orderbook(
        self,
        market_id: str,
        outcome: str = "YES",
    ) -> Optional[OrderBook]:
        """
        Fetch order book for a market outcome.

        Uses CLOB API for real-time order book data.
        """
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        # Get token ID for the outcome
        market = await self.get_market(market_id)
        if not market:
            return None

        token_id = None
        for o in market.outcomes:
            if o.name.upper() == outcome.upper():
                token_id = o.token_id
                break

        if not token_id:
            logger.warning(f"No token ID found for {outcome} in {market_id}")
            return None

        await self._rate_limit_wait()
        self._log_request(f"/book?token_id={token_id}")

        try:
            async with self._session.get(
                f"{self.CLOB_URL}/book",
                params={"token_id": token_id},
            ) as response:
                if response.status != 200:
                    raise PlatformError(
                        f"API error: {response.status}",
                        platform=self.platform_name,
                    )

                data = await response.json()
                return self._parse_orderbook(data)

        except aiohttp.ClientError as e:
            raise PlatformError(f"Network error: {e}", platform=self.platform_name)

    async def get_best_prices(
        self, market_id: str
    ) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Get best ask prices for YES and NO outcomes.

        Returns:
            Tuple of (yes_price, no_price)
        """
        yes_book = await self.get_orderbook(market_id, "YES")
        no_book = await self.get_orderbook(market_id, "NO")

        yes_price = yes_book.best_ask if yes_book else None
        no_price = no_book.best_ask if no_book else None

        return yes_price, no_price

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
        Place an order on Polymarket.

        In dry run mode, simulates order execution.
        """
        # Handle dry run
        if self.dry_run:
            return self._handle_dry_run_order(
                market_id=market_id,
                side=side,
                outcome=outcome,
                price=price,
                size=size,
            )

        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        if not self._private_key:
            raise PlatformError(
                "Private key required for trading",
                platform=self.platform_name,
                recoverable=False,
            )

        # Get token ID
        market = await self.get_market(market_id)
        if not market:
            raise PlatformError(
                f"Market not found: {market_id}",
                platform=self.platform_name,
            )

        token_id = None
        for o in market.outcomes:
            if o.name.upper() == outcome.upper():
                token_id = o.token_id
                break

        if not token_id:
            raise PlatformError(
                f"Token not found for {outcome}",
                platform=self.platform_name,
            )

        # Check liquidity
        orderbook = await self.get_orderbook(market_id, outcome)
        if orderbook:
            available = orderbook.depth_at_price(price, "ask" if side == OrderSide.BUY else "bid")
            if available < size:
                raise InsufficientLiquidityError(
                    platform=self.platform_name,
                    market_id=market_id,
                    required=size,
                    available=available,
                )

        await self._rate_limit_wait()
        self._log_request("/order", method="POST")

        # Build order payload
        # Note: Actual implementation would use py-clob-client for signing
        order_payload = {
            "token_id": token_id,
            "side": "BUY" if side == OrderSide.BUY else "SELL",
            "price": str(price),
            "size": str(size),
            "type": order_type.upper(),
        }

        try:
            # This would be the actual order placement via py-clob-client
            # For now, we log what would happen
            logger.info(
                f"Would place order: {side.value} {size} {outcome} @ {price} "
                f"on market {market_id}"
            )

            # Create trade leg (in real implementation, parse response)
            import uuid

            leg = TradeLeg(
                leg_id=uuid.uuid4().hex[:12],
                leg_order=1,
                platform=self.platform_name,
                market_id=market_id,
                symbol=f"{market_id}_{outcome}",
                side=side,
                order_type=OrderType.LIMIT if order_type == "limit" else OrderType.MARKET,
                price=price,
                size=size,
                status=TradeStatus.SUBMITTED,
                order_id=f"poly_{uuid.uuid4().hex[:12]}",
            )

            return leg

        except Exception as e:
            raise OrderExecutionError(
                platform=self.platform_name,
                reason=str(e),
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would cancel order {order_id}")
            return True

        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        await self._rate_limit_wait()
        self._log_request(f"/order/{order_id}", method="DELETE")

        try:
            # Actual cancellation via py-clob-client
            logger.info(f"Would cancel order {order_id}")
            return True
        except Exception as e:
            raise OrderExecutionError(
                platform=self.platform_name,
                order_id=order_id,
                reason=str(e),
            )

    async def get_positions(self) -> list[dict[str, Any]]:
        """Fetch current positions."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        # Would require authenticated request
        # For now, return empty list
        return []

    async def get_balance(self) -> Decimal:
        """Fetch available USDC balance."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        # Would require authenticated request
        # For now, return placeholder
        return Decimal("0")

    def _parse_market(self, data: dict) -> Optional[PredictionMarket]:
        """Parse market data from API response."""
        try:
            # Parse outcomes
            outcomes = []
            tokens = data.get("tokens", [])

            for token in tokens:
                outcome = MarketOutcome(
                    outcome_id=token.get("token_id", ""),
                    name=token.get("outcome", ""),
                    token_id=token.get("token_id"),
                    last_price=Decimal(str(token.get("price", 0))),
                )
                outcomes.append(outcome)

            # Determine category
            tags = data.get("tags", [])
            category = MarketCategory.OTHER
            for tag in tags:
                tag_lower = tag.lower()
                if "politic" in tag_lower:
                    category = MarketCategory.POLITICS
                    break
                elif "crypto" in tag_lower or "bitcoin" in tag_lower:
                    category = MarketCategory.CRYPTO
                    break
                elif "sport" in tag_lower:
                    category = MarketCategory.SPORTS
                    break
                elif "esport" in tag_lower:
                    category = MarketCategory.ESPORTS
                    break

            # Parse status
            active = data.get("active", True)
            closed = data.get("closed", False)
            resolved = data.get("resolved", False)

            if resolved:
                status = MarketStatus.RESOLVED
            elif closed:
                status = MarketStatus.CLOSED
            elif active:
                status = MarketStatus.ACTIVE
            else:
                status = MarketStatus.PAUSED

            # Parse dates
            end_date = None
            if data.get("end_date_iso"):
                try:
                    end_date = datetime.fromisoformat(
                        data["end_date_iso"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            market = PredictionMarket(
                market_id=data.get("condition_id", data.get("id", "")),
                platform=self.platform_name,
                slug=data.get("slug", ""),
                condition_id=data.get("condition_id"),
                title=data.get("question", data.get("title", "")),
                description=data.get("description", ""),
                category=category,
                status=status,
                end_date=end_date,
                outcomes=outcomes,
                is_binary=len(outcomes) == 2,
                volume_total=Decimal(str(data.get("volume", 0))),
                volume_24h=Decimal(str(data.get("volume_24hr", 0))),
                liquidity=Decimal(str(data.get("liquidity", 0))),
            )

            return market

        except Exception as e:
            logger.warning(f"Error parsing market: {e}")
            return None

    def _parse_orderbook(self, data: dict) -> OrderBook:
        """Parse order book from API response."""
        bids = []
        asks = []

        for bid in data.get("bids", []):
            bids.append(
                OrderBookLevel(
                    price=Decimal(str(bid.get("price", 0))),
                    size=Decimal(str(bid.get("size", 0))),
                )
            )

        for ask in data.get("asks", []):
            asks.append(
                OrderBookLevel(
                    price=Decimal(str(ask.get("price", 0))),
                    size=Decimal(str(ask.get("size", 0))),
                )
            )

        return OrderBook(
            bids=sorted(bids, key=lambda x: x.price, reverse=True),
            asks=sorted(asks, key=lambda x: x.price),
        )

    async def subscribe_orderbook(
        self,
        market_id: str,
        callback,
    ) -> None:
        """
        Subscribe to real-time order book updates via WebSocket.

        This is a placeholder for WebSocket implementation.
        """
        logger.info(f"Would subscribe to orderbook updates for {market_id}")
        # Actual implementation would use WebSocket connection
        pass
