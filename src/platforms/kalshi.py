"""
ArbMaster Pro - Kalshi Integration

Client for interacting with Kalshi's regulated prediction market API.
"""

import asyncio
import hashlib
import hmac
import time
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


class KalshiClient(BasePlatform):
    """
    Kalshi API Client

    Connects to Kalshi's regulated US prediction market.
    Note: Kalshi charges fees calculated as ceil(0.07 * contracts * price * (1-price))
    """

    platform_name = "kalshi"

    # API endpoints
    BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"
    DEMO_URL = "https://demo-api.kalshi.co/trade-api/v2"

    # Fee calculation constant
    FEE_RATE = Decimal("0.07")

    def __init__(self, dry_run: bool = True, use_demo: bool = False):
        super().__init__(dry_run=dry_run)
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = settings.kalshi.api_key
        self._api_secret = settings.kalshi.api_secret
        self._email = settings.kalshi.email
        self._password = settings.kalshi.password
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        self.base_url = self.DEMO_URL if use_demo else self.BASE_URL

        # Cache
        self._markets_cache: dict[str, PredictionMarket] = {}
        self._events_cache: dict[str, dict] = {}

    async def connect(self) -> bool:
        """Establish connection to Kalshi."""
        try:
            self._session = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )

            # Authenticate if credentials provided
            if self._email and self._password:
                await self._authenticate()

            self._connected = True
            logger.info("Connected to Kalshi API")
            return True

        except Exception as e:
            logger.error(f"Error connecting to Kalshi: {e}")
            return False

    async def _authenticate(self) -> None:
        """Authenticate with Kalshi and get access token."""
        if not self._session:
            raise PlatformError("Session not initialized", platform=self.platform_name)

        try:
            async with self._session.post(
                f"{self.base_url}/login",
                json={
                    "email": self._email,
                    "password": self._password,
                },
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise PlatformError(
                        f"Authentication failed: {response.status} - {text}",
                        platform=self.platform_name,
                    )

                data = await response.json()
                self._access_token = data.get("token")

                # Update session headers with auth token
                self._session.headers.update(
                    {"Authorization": f"Bearer {self._access_token}"}
                )

                logger.info("Authenticated with Kalshi")

        except aiohttp.ClientError as e:
            raise PlatformError(f"Network error during auth: {e}", platform=self.platform_name)

    async def disconnect(self) -> None:
        """Close Kalshi connection."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False
        self._access_token = None
        logger.info("Disconnected from Kalshi")

    async def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[PredictionMarket]:
        """Fetch available markets from Kalshi."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        await self._rate_limit_wait()

        params: dict[str, Any] = {
            "limit": limit,
            "status": "open" if status == "active" else status,
        }

        self._log_request("/markets")

        try:
            async with self._session.get(
                f"{self.base_url}/markets",
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
                markets_data = data.get("markets", [])

                markets = []
                for item in markets_data:
                    market = self._parse_market(item)
                    if market:
                        markets.append(market)
                        self._markets_cache[market.market_id] = market

                return markets

        except aiohttp.ClientError as e:
            raise PlatformError(f"Network error: {e}", platform=self.platform_name)

    async def get_market(self, market_id: str) -> Optional[PredictionMarket]:
        """Fetch a specific market by ticker."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        # Check cache
        if market_id in self._markets_cache:
            return self._markets_cache[market_id]

        await self._rate_limit_wait()
        self._log_request(f"/markets/{market_id}")

        try:
            async with self._session.get(
                f"{self.base_url}/markets/{market_id}"
            ) as response:
                if response.status == 404:
                    return None

                if response.status != 200:
                    raise PlatformError(
                        f"API error: {response.status}",
                        platform=self.platform_name,
                    )

                data = await response.json()
                market_data = data.get("market", data)
                market = self._parse_market(market_data)

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
        """Fetch order book for a market."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        await self._rate_limit_wait()
        self._log_request(f"/markets/{market_id}/orderbook")

        try:
            async with self._session.get(
                f"{self.base_url}/markets/{market_id}/orderbook"
            ) as response:
                if response.status != 200:
                    raise PlatformError(
                        f"API error: {response.status}",
                        platform=self.platform_name,
                    )

                data = await response.json()
                orderbook = data.get("orderbook", data)

                # Kalshi returns separate YES and NO books
                # Transform based on requested outcome
                return self._parse_orderbook(orderbook, outcome)

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
        orderbook = await self.get_orderbook(market_id, "YES")

        if not orderbook:
            return None, None

        yes_price = orderbook.best_ask

        # In Kalshi, NO price = 1 - YES price
        # But we need actual NO side best ask
        no_book = await self.get_orderbook(market_id, "NO")
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
        Place an order on Kalshi.

        Note: Kalshi requires authentication for trading.
        Fee = ceil(0.07 * contracts * price * (1 - price))
        """
        # Handle dry run
        if self.dry_run:
            leg = self._handle_dry_run_order(
                market_id=market_id,
                side=side,
                outcome=outcome,
                price=price,
                size=size,
            )
            # Add Kalshi fee estimate
            fee = self._calculate_fee(size, price)
            leg.fee = fee
            return leg

        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        if not self._access_token:
            raise PlatformError(
                "Authentication required for trading",
                platform=self.platform_name,
                recoverable=False,
            )

        await self._rate_limit_wait()
        self._log_request("/portfolio/orders", method="POST")

        # Kalshi uses cents for prices (0-100)
        price_cents = int(price * 100)

        order_payload = {
            "ticker": market_id,
            "client_order_id": f"arb_{int(time.time() * 1000)}",
            "type": "limit" if order_type == "limit" else "market",
            "action": "buy" if side == OrderSide.BUY else "sell",
            "side": "yes" if outcome.upper() == "YES" else "no",
            "count": int(size),
            "yes_price": price_cents if outcome.upper() == "YES" else None,
            "no_price": price_cents if outcome.upper() == "NO" else None,
        }

        try:
            async with self._session.post(
                f"{self.base_url}/portfolio/orders",
                json=order_payload,
            ) as response:
                if response.status == 401:
                    raise PlatformError(
                        "Authentication expired",
                        platform=self.platform_name,
                    )

                if response.status not in (200, 201):
                    text = await response.text()
                    raise OrderExecutionError(
                        platform=self.platform_name,
                        reason=f"Order failed: {response.status} - {text}",
                    )

                data = await response.json()
                order_data = data.get("order", data)

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
                    order_id=order_data.get("order_id"),
                    fee=self._calculate_fee(size, price),
                )

                return leg

        except aiohttp.ClientError as e:
            raise OrderExecutionError(
                platform=self.platform_name,
                reason=str(e),
            )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would cancel Kalshi order {order_id}")
            return True

        if not self._session or not self._access_token:
            raise PlatformError(
                "Not authenticated",
                platform=self.platform_name,
            )

        await self._rate_limit_wait()
        self._log_request(f"/portfolio/orders/{order_id}", method="DELETE")

        try:
            async with self._session.delete(
                f"{self.base_url}/portfolio/orders/{order_id}"
            ) as response:
                if response.status == 200:
                    return True
                else:
                    logger.warning(f"Cancel failed: {response.status}")
                    return False

        except aiohttp.ClientError as e:
            raise OrderExecutionError(
                platform=self.platform_name,
                order_id=order_id,
                reason=str(e),
            )

    async def get_positions(self) -> list[dict[str, Any]]:
        """Fetch current positions."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        if not self._access_token:
            return []

        await self._rate_limit_wait()
        self._log_request("/portfolio/positions")

        try:
            async with self._session.get(
                f"{self.base_url}/portfolio/positions"
            ) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                return data.get("market_positions", [])

        except aiohttp.ClientError:
            return []

    async def get_balance(self) -> Decimal:
        """Fetch available USD balance."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        if not self._access_token:
            return Decimal("0")

        await self._rate_limit_wait()
        self._log_request("/portfolio/balance")

        try:
            async with self._session.get(
                f"{self.base_url}/portfolio/balance"
            ) as response:
                if response.status != 200:
                    return Decimal("0")

                data = await response.json()
                # Kalshi returns balance in cents
                balance_cents = data.get("balance", 0)
                return Decimal(balance_cents) / 100

        except aiohttp.ClientError:
            return Decimal("0")

    def _calculate_fee(self, contracts: Decimal, price: Decimal) -> Decimal:
        """
        Calculate Kalshi trading fee.

        Fee = ceil(0.07 * contracts * price * (1 - price))
        """
        import math

        fee_raw = float(self.FEE_RATE * contracts * price * (1 - price))
        fee_cents = math.ceil(fee_raw * 100)
        return Decimal(fee_cents) / 100

    def _parse_market(self, data: dict) -> Optional[PredictionMarket]:
        """Parse market data from Kalshi API response."""
        try:
            # Kalshi uses ticker as market_id
            market_id = data.get("ticker", "")

            # Parse status
            status_str = data.get("status", "open")
            if status_str == "open":
                status = MarketStatus.ACTIVE
            elif status_str == "closed":
                status = MarketStatus.CLOSED
            elif status_str in ("finalized", "settled"):
                status = MarketStatus.RESOLVED
            else:
                status = MarketStatus.PAUSED

            # Parse category from event
            category = MarketCategory.OTHER
            category_str = data.get("category", "").lower()
            if "politic" in category_str:
                category = MarketCategory.POLITICS
            elif "crypto" in category_str:
                category = MarketCategory.CRYPTO
            elif "sport" in category_str:
                category = MarketCategory.SPORTS
            elif "econ" in category_str:
                category = MarketCategory.ECONOMICS

            # Create YES/NO outcomes
            # Kalshi prices are in cents (0-100)
            yes_price = Decimal(str(data.get("yes_bid", 0))) / 100
            no_price = Decimal(str(data.get("no_bid", 0))) / 100

            outcomes = [
                MarketOutcome(
                    outcome_id=f"{market_id}_YES",
                    name="YES",
                    token_id=f"{market_id}_YES",
                    last_price=yes_price,
                    best_bid=yes_price if yes_price > 0 else None,
                    best_ask=Decimal(str(data.get("yes_ask", 0))) / 100 if data.get("yes_ask") else None,
                ),
                MarketOutcome(
                    outcome_id=f"{market_id}_NO",
                    name="NO",
                    token_id=f"{market_id}_NO",
                    last_price=no_price,
                    best_bid=no_price if no_price > 0 else None,
                    best_ask=Decimal(str(data.get("no_ask", 0))) / 100 if data.get("no_ask") else None,
                ),
            ]

            # Parse dates
            end_date = None
            if data.get("close_time"):
                try:
                    end_date = datetime.fromisoformat(
                        data["close_time"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Volume (Kalshi returns in contracts)
            volume = Decimal(str(data.get("volume", 0)))

            market = PredictionMarket(
                market_id=market_id,
                platform=self.platform_name,
                slug=data.get("ticker_name", market_id),
                title=data.get("title", data.get("subtitle", "")),
                description=data.get("rules_primary", ""),
                category=category,
                status=status,
                end_date=end_date,
                outcomes=outcomes,
                is_binary=True,  # Kalshi markets are binary
                volume_total=volume,
                volume_24h=Decimal(str(data.get("volume_24h", 0))),
                liquidity=Decimal(str(data.get("open_interest", 0))),
            )

            return market

        except Exception as e:
            logger.warning(f"Error parsing Kalshi market: {e}")
            return None

    def _parse_orderbook(self, data: dict, outcome: str) -> OrderBook:
        """Parse order book from Kalshi API response."""
        bids = []
        asks = []

        # Kalshi returns yes and no books separately
        if outcome.upper() == "YES":
            bid_data = data.get("yes", {}).get("bids", [])
            ask_data = data.get("yes", {}).get("asks", [])
        else:
            bid_data = data.get("no", {}).get("bids", [])
            ask_data = data.get("no", {}).get("asks", [])

        for bid in bid_data:
            # Kalshi prices are in cents
            bids.append(
                OrderBookLevel(
                    price=Decimal(str(bid[0])) / 100,  # price
                    size=Decimal(str(bid[1])),  # count
                )
            )

        for ask in ask_data:
            asks.append(
                OrderBookLevel(
                    price=Decimal(str(ask[0])) / 100,
                    size=Decimal(str(ask[1])),
                )
            )

        return OrderBook(
            bids=sorted(bids, key=lambda x: x.price, reverse=True),
            asks=sorted(asks, key=lambda x: x.price),
        )

    async def get_events(self) -> list[dict]:
        """Fetch all events (groups of related markets)."""
        if not self._session:
            raise PlatformError("Not connected", platform=self.platform_name)

        await self._rate_limit_wait()
        self._log_request("/events")

        try:
            async with self._session.get(f"{self.base_url}/events") as response:
                if response.status != 200:
                    return []

                data = await response.json()
                events = data.get("events", [])

                for event in events:
                    self._events_cache[event.get("event_ticker", "")] = event

                return events

        except aiohttp.ClientError:
            return []
