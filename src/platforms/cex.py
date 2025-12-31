"""
ArbMaster Pro - Centralized Exchange Integration

Client for interacting with centralized exchanges via CCXT.
Supports Binance, KuCoin, OKX, and other major exchanges.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
import ccxt.async_support as ccxt
from loguru import logger

from .base import BasePlatform, PlatformError, RateLimitError
from models.market import Market, OrderBook, OrderBookLevel
from models.trade import TradeLeg, TradeStatus, OrderSide, OrderType
from config import settings


class CEXClient(BasePlatform):
    """
    Centralized Exchange Client using CCXT

    Provides unified interface for multiple exchanges:
    - Binance
    - KuCoin
    - OKX
    - and more via CCXT
    """

    platform_name = "cex"

    # Supported exchanges and their CCXT IDs
    SUPPORTED_EXCHANGES = {
        "binance": "binance",
        "kucoin": "kucoin",
        "okx": "okx",
        "bybit": "bybit",
        "kraken": "kraken",
    }

    def __init__(
        self,
        exchange_id: str = "binance",
        dry_run: bool = True,
    ):
        super().__init__(dry_run=dry_run)
        self.exchange_id = exchange_id.lower()
        self._exchange: Optional[ccxt.Exchange] = None
        self._markets: dict[str, Market] = {}

        # Get credentials based on exchange
        self._credentials = self._get_credentials()

    def _get_credentials(self) -> dict[str, Optional[str]]:
        """Get credentials for the selected exchange."""
        creds: dict[str, Optional[str]] = {}

        if self.exchange_id == "binance":
            creds["apiKey"] = settings.exchanges.binance_api_key
            creds["secret"] = settings.exchanges.binance_api_secret
        elif self.exchange_id == "kucoin":
            creds["apiKey"] = settings.exchanges.kucoin_api_key
            creds["secret"] = settings.exchanges.kucoin_api_secret
            creds["password"] = settings.exchanges.kucoin_passphrase
        elif self.exchange_id == "okx":
            creds["apiKey"] = settings.exchanges.okx_api_key
            creds["secret"] = settings.exchanges.okx_api_secret
            creds["password"] = settings.exchanges.okx_passphrase

        return creds

    async def connect(self) -> bool:
        """Initialize exchange connection via CCXT."""
        try:
            if self.exchange_id not in self.SUPPORTED_EXCHANGES:
                raise PlatformError(
                    f"Unsupported exchange: {self.exchange_id}",
                    platform=self.platform_name,
                )

            # Get CCXT exchange class
            exchange_class = getattr(ccxt, self.SUPPORTED_EXCHANGES[self.exchange_id])

            # Initialize with credentials
            config = {
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }

            # Add credentials if available
            if self._credentials.get("apiKey"):
                config.update(self._credentials)

            self._exchange = exchange_class(config)

            # Load markets
            await self._exchange.load_markets()
            self._connected = True

            logger.info(f"Connected to {self.exchange_id} via CCXT")
            logger.info(f"Available markets: {len(self._exchange.markets)}")

            return True

        except Exception as e:
            logger.error(f"Error connecting to {self.exchange_id}: {e}")
            return False

    async def disconnect(self) -> None:
        """Close exchange connection."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
        self._connected = False
        logger.info(f"Disconnected from {self.exchange_id}")

    async def get_ticker(self, symbol: str) -> Optional[dict]:
        """
        Fetch ticker data for a trading pair.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")

        Returns:
            Ticker data including last price, bid, ask, volume
        """
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            ticker = await self._exchange.fetch_ticker(symbol)
            return ticker
        except ccxt.BadSymbol:
            logger.warning(f"Invalid symbol: {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error fetching ticker {symbol}: {e}")
            return None

    async def get_tickers(
        self,
        symbols: Optional[list[str]] = None,
    ) -> dict[str, dict]:
        """
        Fetch tickers for multiple symbols.

        Args:
            symbols: List of trading pairs, or None for all

        Returns:
            Dictionary of symbol -> ticker data
        """
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            if symbols:
                tickers = await self._exchange.fetch_tickers(symbols)
            else:
                tickers = await self._exchange.fetch_tickers()
            return tickers
        except Exception as e:
            logger.error(f"Error fetching tickers: {e}")
            return {}

    async def get_markets(
        self,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 100,
    ) -> list[Market]:
        """Fetch available markets."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        markets = []
        count = 0

        for symbol, market_info in self._exchange.markets.items():
            if count >= limit:
                break

            # Filter by status
            if not market_info.get("active", True):
                continue

            # Filter by category/type
            if category and market_info.get("type") != category:
                continue

            market = Market(
                market_id=symbol,
                platform=self.exchange_id,
                symbol=symbol,
                base_asset=market_info.get("base", ""),
                quote_asset=market_info.get("quote", ""),
            )
            markets.append(market)
            count += 1

        return markets

    async def get_market(self, market_id: str) -> Optional[Market]:
        """Fetch a specific market by symbol."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        if market_id not in self._exchange.markets:
            return None

        market_info = self._exchange.markets[market_id]
        ticker = await self.get_ticker(market_id)

        market = Market(
            market_id=market_id,
            platform=self.exchange_id,
            symbol=market_id,
            base_asset=market_info.get("base", ""),
            quote_asset=market_info.get("quote", ""),
            last_price=Decimal(str(ticker["last"])) if ticker else Decimal("0"),
            bid=Decimal(str(ticker["bid"])) if ticker and ticker.get("bid") else None,
            ask=Decimal(str(ticker["ask"])) if ticker and ticker.get("ask") else None,
            volume_24h=Decimal(str(ticker["baseVolume"])) if ticker else Decimal("0"),
        )

        return market

    async def get_orderbook(
        self,
        market_id: str,
        outcome: str = "YES",  # Ignored for CEX
        limit: int = 20,
    ) -> Optional[OrderBook]:
        """Fetch order book for a market."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            book = await self._exchange.fetch_order_book(market_id, limit)

            bids = [
                OrderBookLevel(
                    price=Decimal(str(bid[0])),
                    size=Decimal(str(bid[1])),
                )
                for bid in book.get("bids", [])
            ]

            asks = [
                OrderBookLevel(
                    price=Decimal(str(ask[0])),
                    size=Decimal(str(ask[1])),
                )
                for ask in book.get("asks", [])
            ]

            return OrderBook(
                bids=bids,
                asks=asks,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error fetching orderbook {market_id}: {e}")
            return None

    async def place_order(
        self,
        market_id: str,
        side: OrderSide,
        outcome: str,  # Ignored for CEX
        price: Decimal,
        size: Decimal,
        order_type: str = "limit",
    ) -> Optional[TradeLeg]:
        """Place an order on the exchange."""
        # Handle dry run
        if self.dry_run:
            return self._handle_dry_run_order(
                market_id=market_id,
                side=side,
                outcome=outcome,
                price=price,
                size=size,
            )

        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            order = await self._exchange.create_order(
                symbol=market_id,
                type=order_type,
                side=side.value,
                amount=float(size),
                price=float(price) if order_type == "limit" else None,
            )

            import uuid

            leg = TradeLeg(
                leg_id=uuid.uuid4().hex[:12],
                leg_order=1,
                platform=self.exchange_id,
                market_id=market_id,
                symbol=market_id,
                side=side,
                order_type=OrderType.LIMIT if order_type == "limit" else OrderType.MARKET,
                price=price,
                size=size,
                status=TradeStatus.SUBMITTED,
                order_id=order.get("id"),
                filled_size=Decimal(str(order.get("filled", 0))),
                filled_price=Decimal(str(order.get("average"))) if order.get("average") else None,
                fee=Decimal(str(order.get("fee", {}).get("cost", 0))),
            )

            return leg

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """Cancel an open order."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would cancel order {order_id}")
            return True

        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def get_positions(self) -> list[dict[str, Any]]:
        """Fetch current positions (for futures/margin)."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            positions = await self._exchange.fetch_positions()
            return positions
        except Exception:
            # Not all exchanges support positions
            return []

    async def get_balance(self, asset: str = "USDT") -> Decimal:
        """Fetch available balance for an asset."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            balance = await self._exchange.fetch_balance()
            asset_balance = balance.get(asset, {})
            return Decimal(str(asset_balance.get("free", 0)))
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return Decimal("0")

    async def get_funding_rate(self, symbol: str) -> Optional[Decimal]:
        """
        Fetch current funding rate for perpetual futures.

        Args:
            symbol: Perpetual futures symbol (e.g., "BTC/USDT:USDT")

        Returns:
            Current funding rate or None
        """
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            funding = await self._exchange.fetch_funding_rate(symbol)
            return Decimal(str(funding.get("fundingRate", 0)))
        except Exception as e:
            logger.debug(f"Error fetching funding rate for {symbol}: {e}")
            return None

    async def get_all_funding_rates(self) -> dict[str, Decimal]:
        """Fetch funding rates for all perpetual markets."""
        if not self._exchange:
            raise PlatformError("Not connected", platform=self.platform_name)

        try:
            funding_rates = await self._exchange.fetch_funding_rates()
            return {
                symbol: Decimal(str(data.get("fundingRate", 0)))
                for symbol, data in funding_rates.items()
            }
        except Exception as e:
            logger.debug(f"Error fetching funding rates: {e}")
            return {}


class MultiCEXClient:
    """
    Multi-Exchange Client

    Manages connections to multiple exchanges for arbitrage scanning.
    """

    def __init__(self, exchanges: list[str], dry_run: bool = True):
        self.exchanges = exchanges
        self.dry_run = dry_run
        self.clients: dict[str, CEXClient] = {}

    async def connect_all(self) -> dict[str, bool]:
        """Connect to all configured exchanges."""
        results = {}

        for exchange_id in self.exchanges:
            client = CEXClient(exchange_id=exchange_id, dry_run=self.dry_run)
            success = await client.connect()
            results[exchange_id] = success

            if success:
                self.clients[exchange_id] = client

        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all exchanges."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()

    async def get_prices(self, symbol: str) -> dict[str, Optional[Decimal]]:
        """
        Get prices for a symbol across all connected exchanges.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")

        Returns:
            Dictionary of exchange -> price
        """
        prices = {}

        tasks = []
        for exchange_id, client in self.clients.items():
            tasks.append(self._get_price_task(exchange_id, client, symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for exchange_id, price in results:
            if not isinstance(price, Exception):
                prices[exchange_id] = price

        return prices

    async def _get_price_task(
        self,
        exchange_id: str,
        client: CEXClient,
        symbol: str,
    ) -> tuple[str, Optional[Decimal]]:
        """Task to get price from a single exchange."""
        try:
            ticker = await client.get_ticker(symbol)
            if ticker and ticker.get("last"):
                return exchange_id, Decimal(str(ticker["last"]))
            return exchange_id, None
        except Exception as e:
            logger.debug(f"Error getting price from {exchange_id}: {e}")
            return exchange_id, None

    def find_spread(
        self,
        prices: dict[str, Optional[Decimal]],
    ) -> Optional[tuple[str, str, Decimal]]:
        """
        Find the maximum spread between exchanges.

        Returns:
            Tuple of (buy_exchange, sell_exchange, spread_pct) or None
        """
        valid_prices = {k: v for k, v in prices.items() if v is not None}

        if len(valid_prices) < 2:
            return None

        min_exchange = min(valid_prices, key=lambda x: valid_prices[x])  # type: ignore
        max_exchange = max(valid_prices, key=lambda x: valid_prices[x])  # type: ignore

        min_price = valid_prices[min_exchange]
        max_price = valid_prices[max_exchange]

        if min_price and max_price and min_price > 0:
            spread_pct = (max_price - min_price) / min_price
            return min_exchange, max_exchange, spread_pct

        return None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect_all()
