"""
ArbMaster Pro - Arbitrage Detector

Main orchestrator for detecting arbitrage opportunities across all platforms.
Coordinates multiple scanners and evaluates opportunities in real-time.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Callable, Awaitable
import uuid
from loguru import logger

from models.opportunity import (
    ArbitrageType,
    ArbitrageOpportunity,
    BinaryComplementArb,
    CrossPlatformArb,
    MultiOutcomeArb,
    DEXCEXArb,
    FundingRateArb,
    Platform,
)
from models.market import PredictionMarket
from platforms.polymarket import PolymarketClient
from platforms.kalshi import KalshiClient
from platforms.cex import CEXClient, MultiCEXClient
from platforms.dex import DEXClient
from config import settings


class ArbitrageDetector:
    """
    Main arbitrage detection orchestrator.

    Coordinates multiple platform clients and scanners to detect
    opportunities in real-time with target latency of <500ms.
    """

    def __init__(
        self,
        dry_run: bool = True,
        min_profit_threshold: Decimal = Decimal("0.01"),  # 1%
        min_liquidity: Decimal = Decimal("10000"),  # $10k
    ):
        self.dry_run = dry_run
        self.min_profit_threshold = min_profit_threshold
        self.min_liquidity = min_liquidity

        # Platform clients
        self.polymarket: Optional[PolymarketClient] = None
        self.kalshi: Optional[KalshiClient] = None
        self.cex_clients: dict[str, CEXClient] = {}
        self.dex_client: Optional[DEXClient] = None

        # State
        self._running = False
        self._opportunities: dict[str, ArbitrageOpportunity] = {}
        self._scan_interval = 1.0  # seconds between scans

        # Callbacks
        self._on_opportunity: Optional[
            Callable[[ArbitrageOpportunity], Awaitable[None]]
        ] = None

        # Metrics
        self._scan_count = 0
        self._opportunities_found = 0
        self._last_scan_time: Optional[datetime] = None
        self._last_scan_duration_ms: int = 0

    async def initialize(self) -> bool:
        """Initialize all platform connections."""
        logger.info("Initializing ArbMaster Pro detector...")

        success = True

        # Initialize Polymarket
        try:
            self.polymarket = PolymarketClient(dry_run=self.dry_run)
            if await self.polymarket.connect():
                logger.info("Polymarket client connected")
            else:
                logger.warning("Failed to connect Polymarket client")
                success = False
        except Exception as e:
            logger.error(f"Error initializing Polymarket: {e}")
            self.polymarket = None

        # Initialize Kalshi
        try:
            self.kalshi = KalshiClient(dry_run=self.dry_run)
            if await self.kalshi.connect():
                logger.info("Kalshi client connected")
            else:
                logger.warning("Failed to connect Kalshi client")
        except Exception as e:
            logger.error(f"Error initializing Kalshi: {e}")
            self.kalshi = None

        # Initialize CEX clients
        for exchange in ["binance", "kucoin"]:
            try:
                client = CEXClient(exchange_id=exchange, dry_run=self.dry_run)
                if await client.connect():
                    self.cex_clients[exchange] = client
                    logger.info(f"{exchange} client connected")
            except Exception as e:
                logger.warning(f"Error initializing {exchange}: {e}")

        # Initialize DEX client
        try:
            self.dex_client = DEXClient(
                network="polygon",
                dex="sushiswap",
                dry_run=self.dry_run,
            )
            if await self.dex_client.connect():
                logger.info("DEX client connected")
        except Exception as e:
            logger.warning(f"Error initializing DEX: {e}")
            self.dex_client = None

        logger.info(f"Initialization complete. Success: {success}")
        return success

    async def shutdown(self) -> None:
        """Shutdown all platform connections."""
        logger.info("Shutting down ArbMaster Pro detector...")

        self._running = False

        if self.polymarket:
            await self.polymarket.disconnect()

        if self.kalshi:
            await self.kalshi.disconnect()

        for client in self.cex_clients.values():
            await client.disconnect()

        if self.dex_client:
            await self.dex_client.disconnect()

        logger.info("Shutdown complete")

    def set_opportunity_callback(
        self,
        callback: Callable[[ArbitrageOpportunity], Awaitable[None]],
    ) -> None:
        """Set callback for when opportunities are detected."""
        self._on_opportunity = callback

    async def scan_once(self) -> list[ArbitrageOpportunity]:
        """
        Perform a single scan across all platforms and strategies.

        Returns:
            List of detected opportunities
        """
        start_time = datetime.utcnow()
        opportunities = []

        # Run all scanners concurrently
        scan_tasks = []

        # Binary complement arbitrage on Polymarket
        if self.polymarket:
            scan_tasks.append(self._scan_binary_complement())

        # Cross-platform arbitrage (Polymarket vs Kalshi)
        if self.polymarket and self.kalshi:
            scan_tasks.append(self._scan_cross_platform())

        # CEX spatial arbitrage
        if len(self.cex_clients) >= 2:
            scan_tasks.append(self._scan_cex_arbitrage())

        # DEX-CEX arbitrage
        if self.dex_client and self.cex_clients:
            scan_tasks.append(self._scan_dex_cex())

        # Funding rate arbitrage
        if self.cex_clients:
            scan_tasks.append(self._scan_funding_rates())

        # Execute all scans concurrently
        if scan_tasks:
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    opportunities.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Scanner error: {result}")

        # Filter by minimum profit
        opportunities = [
            opp for opp in opportunities
            if opp.net_profit_pct >= self.min_profit_threshold
        ]

        # Update metrics
        end_time = datetime.utcnow()
        self._scan_count += 1
        self._last_scan_time = end_time
        self._last_scan_duration_ms = int(
            (end_time - start_time).total_seconds() * 1000
        )
        self._opportunities_found += len(opportunities)

        # Trigger callbacks
        for opp in opportunities:
            self._opportunities[opp.id] = opp
            if self._on_opportunity:
                try:
                    await self._on_opportunity(opp)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        return opportunities

    async def start_scanning(self) -> None:
        """Start continuous scanning loop."""
        logger.info(
            f"Starting continuous scanning (interval: {self._scan_interval}s)"
        )
        self._running = True

        while self._running:
            try:
                opportunities = await self.scan_once()

                if opportunities:
                    logger.info(
                        f"Found {len(opportunities)} opportunities "
                        f"(scan #{self._scan_count}, {self._last_scan_duration_ms}ms)"
                    )

                await asyncio.sleep(self._scan_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan error: {e}")
                await asyncio.sleep(self._scan_interval)

        logger.info("Scanning stopped")

    def stop_scanning(self) -> None:
        """Stop the scanning loop."""
        self._running = False

    async def _scan_binary_complement(self) -> list[BinaryComplementArb]:
        """
        Scan for binary complement arbitrage on Polymarket.

        Finds markets where YES + NO < $1.00
        """
        opportunities = []

        if not self.polymarket:
            return opportunities

        try:
            # Fetch active markets
            markets = await self.polymarket.get_markets(status="active", limit=100)

            for market in markets:
                if not market.is_binary:
                    continue

                # Get best prices for YES and NO
                yes_price, no_price = await self.polymarket.get_best_prices(
                    market.market_id
                )

                if yes_price is None or no_price is None:
                    continue

                combined = yes_price + no_price

                # Check for arbitrage (YES + NO < 1.00)
                if combined < Decimal("1.0"):
                    profit_pct = (Decimal("1.0") - combined) / combined

                    # Estimate liquidity
                    yes_book = await self.polymarket.get_orderbook(
                        market.market_id, "YES"
                    )
                    no_book = await self.polymarket.get_orderbook(
                        market.market_id, "NO"
                    )

                    yes_depth = yes_book.total_ask_depth() if yes_book else Decimal("0")
                    no_depth = no_book.total_ask_depth() if no_book else Decimal("0")
                    max_size = min(yes_depth, no_depth)

                    # Skip if liquidity too low
                    if max_size * combined < self.min_liquidity:
                        continue

                    opp = BinaryComplementArb(
                        id=f"bc_{uuid.uuid4().hex[:8]}",
                        platform=Platform.POLYMARKET,
                        market_id=market.market_id,
                        market_title=market.title,
                        condition_id=market.condition_id or "",
                        yes_price=yes_price,
                        no_price=no_price,
                        combined_price=combined,
                        yes_depth=yes_depth,
                        no_depth=no_depth,
                        max_size=max_size,
                        gross_profit_pct=profit_pct,
                        net_profit_pct=profit_pct,  # Polymarket has no fees
                        estimated_profit_usd=max_size * (Decimal("1.0") - combined),
                        total_cost=max_size * combined,
                        confidence=0.95,
                        liquidity_score=float(min(yes_depth, no_depth) / 1000),
                    )

                    opportunities.append(opp)
                    logger.debug(
                        f"Binary arb found: {market.title[:50]} "
                        f"({yes_price}+{no_price}={combined}) "
                        f"profit: {profit_pct:.2%}"
                    )

        except Exception as e:
            logger.error(f"Binary complement scan error: {e}")

        return opportunities

    async def _scan_cross_platform(self) -> list[CrossPlatformArb]:
        """
        Scan for cross-platform arbitrage between Polymarket and Kalshi.

        Finds matching markets where combined YES(A) + NO(B) < $1.00
        """
        opportunities = []

        if not self.polymarket or not self.kalshi:
            return opportunities

        try:
            # Get markets from both platforms
            poly_markets = await self.polymarket.get_markets(limit=50)
            kalshi_markets = await self.kalshi.get_markets(limit=50)

            # Build slug index for matching
            poly_by_slug = {m.slug.lower(): m for m in poly_markets if m.slug}
            kalshi_by_slug = {m.slug.lower(): m for m in kalshi_markets if m.slug}

            # Find matching markets (simplified matching by slug)
            for poly_slug, poly_market in poly_by_slug.items():
                # Try to find matching Kalshi market
                matching_kalshi = None

                for kalshi_slug, kalshi_market in kalshi_by_slug.items():
                    # Simple similarity check
                    if self._markets_match(poly_market, kalshi_market):
                        matching_kalshi = kalshi_market
                        break

                if not matching_kalshi:
                    continue

                # Get prices from both platforms
                poly_yes, poly_no = await self.polymarket.get_best_prices(
                    poly_market.market_id
                )
                kalshi_yes, kalshi_no = await self.kalshi.get_best_prices(
                    matching_kalshi.market_id
                )

                if not all([poly_yes, poly_no, kalshi_yes, kalshi_no]):
                    continue

                # Check all combinations for arbitrage
                combinations = [
                    ("YES", "NO", poly_yes, kalshi_no),
                    ("NO", "YES", poly_no, kalshi_yes),
                ]

                for side_a, side_b, price_a, price_b in combinations:
                    if price_a is None or price_b is None:
                        continue

                    combined = price_a + price_b

                    if combined < Decimal("0.99"):  # Account for Kalshi fees
                        # Calculate Kalshi fee
                        kalshi_fee = self.kalshi._calculate_fee(
                            Decimal("100"),  # 100 contracts
                            price_b,
                        )

                        net_profit = Decimal("1.0") - combined - kalshi_fee / 100
                        profit_pct = net_profit / combined

                        if profit_pct < self.min_profit_threshold:
                            continue

                        opp = CrossPlatformArb(
                            id=f"cp_{uuid.uuid4().hex[:8]}",
                            platform_a=Platform.POLYMARKET,
                            market_id_a=poly_market.market_id,
                            side_a=side_a,
                            price_a=price_a,
                            platform_b=Platform.KALSHI,
                            market_id_b=matching_kalshi.market_id,
                            side_b=side_b,
                            price_b=price_b,
                            event_slug=poly_slug,
                            match_confidence=0.8,
                            gross_profit_pct=profit_pct + kalshi_fee / 100 / combined,
                            net_profit_pct=profit_pct,
                            estimated_profit_usd=net_profit * 100,
                            total_cost=combined * 100,
                            estimated_fees=kalshi_fee,
                        )

                        opportunities.append(opp)
                        logger.debug(
                            f"Cross-platform arb: {poly_slug} "
                            f"({side_a}@{price_a} + {side_b}@{price_b}) "
                            f"profit: {profit_pct:.2%}"
                        )

        except Exception as e:
            logger.error(f"Cross-platform scan error: {e}")

        return opportunities

    async def _scan_cex_arbitrage(self) -> list[DEXCEXArb]:
        """
        Scan for spatial arbitrage across centralized exchanges.

        Finds price differences for the same asset on different exchanges.
        """
        opportunities = []

        if len(self.cex_clients) < 2:
            return opportunities

        try:
            # Common pairs to check
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

            for symbol in symbols:
                prices: dict[str, Decimal] = {}

                # Get prices from all exchanges
                for exchange_id, client in self.cex_clients.items():
                    try:
                        ticker = await client.get_ticker(symbol)
                        if ticker and ticker.get("last"):
                            prices[exchange_id] = Decimal(str(ticker["last"]))
                    except Exception:
                        continue

                if len(prices) < 2:
                    continue

                # Find max spread
                min_exchange = min(prices, key=lambda x: prices[x])
                max_exchange = max(prices, key=lambda x: prices[x])

                spread = prices[max_exchange] - prices[min_exchange]
                spread_pct = spread / prices[min_exchange]

                # Check if profitable after fees (~0.1% per side)
                fee_pct = Decimal("0.002")  # 0.2% round trip
                net_profit_pct = spread_pct - fee_pct

                if net_profit_pct < self.min_profit_threshold:
                    continue

                opp = DEXCEXArb(
                    id=f"cex_{uuid.uuid4().hex[:8]}",
                    arb_type=ArbitrageType.DEX_CEX,
                    token_symbol=symbol.split("/")[0],
                    dex_platform=Platform.BINANCE,  # Using CEX as "dex" here
                    dex_price=prices[min_exchange],
                    cex_platform=Platform(max_exchange),
                    cex_price=prices[max_exchange],
                    cex_pair=symbol,
                    buy_on=min_exchange,
                    sell_on=max_exchange,
                    max_trade_size=Decimal("10000"),  # $10k max
                    gross_profit_pct=spread_pct,
                    net_profit_pct=net_profit_pct,
                    estimated_profit_usd=Decimal("10000") * net_profit_pct,
                    total_cost=Decimal("10000"),
                    estimated_fees=Decimal("10000") * fee_pct,
                )

                opportunities.append(opp)
                logger.debug(
                    f"CEX arb: {symbol} buy@{min_exchange}({prices[min_exchange]}) "
                    f"sell@{max_exchange}({prices[max_exchange]}) "
                    f"spread: {spread_pct:.3%}"
                )

        except Exception as e:
            logger.error(f"CEX arbitrage scan error: {e}")

        return opportunities

    async def _scan_dex_cex(self) -> list[DEXCEXArb]:
        """
        Scan for DEX-CEX price gaps.

        Finds opportunities where DEX and CEX prices diverge.
        """
        # Simplified implementation - would need more sophisticated
        # routing and liquidity analysis in production
        return []

    async def _scan_funding_rates(self) -> list[FundingRateArb]:
        """
        Scan for funding rate arbitrage opportunities.

        Finds high funding rates suitable for spot-futures hedging.
        """
        opportunities = []

        try:
            for exchange_id, client in self.cex_clients.items():
                funding_rates = await client.get_all_funding_rates()

                for symbol, rate in funding_rates.items():
                    # Skip if rate too low (annualized < 5%)
                    annualized = rate * 3 * 365  # 8h periods
                    if abs(annualized) < Decimal("0.05"):
                        continue

                    opp = FundingRateArb(
                        id=f"fr_{uuid.uuid4().hex[:8]}",
                        arb_type=ArbitrageType.FUNDING_RATE,
                        platform=Platform(exchange_id),
                        symbol=symbol,
                        current_funding_rate=rate,
                        annualized_yield=annualized,
                        spot_size=Decimal("10000"),
                        futures_size=Decimal("10000"),
                        next_funding_time=datetime.utcnow(),  # Would need actual time
                        gross_profit_pct=abs(annualized),
                        net_profit_pct=abs(annualized) - Decimal("0.01"),  # Subtract fees
                        estimated_profit_usd=Decimal("10000") * abs(rate),
                        total_cost=Decimal("10000"),
                    )

                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"Funding rate scan error: {e}")

        return opportunities

    def _markets_match(
        self,
        market_a: PredictionMarket,
        market_b: PredictionMarket,
    ) -> bool:
        """
        Check if two markets from different platforms refer to the same event.

        Uses fuzzy matching on titles and slugs.
        """
        # Simple slug comparison
        if market_a.slug and market_b.slug:
            slug_a = market_a.slug.lower().replace("-", " ").replace("_", " ")
            slug_b = market_b.slug.lower().replace("-", " ").replace("_", " ")

            # Check for common words
            words_a = set(slug_a.split())
            words_b = set(slug_b.split())
            common = words_a & words_b

            if len(common) >= 3:
                return True

        # Title comparison
        title_a = market_a.title.lower()
        title_b = market_b.title.lower()

        words_a = set(title_a.split())
        words_b = set(title_b.split())
        common = words_a & words_b

        # Remove common stop words
        stop_words = {"the", "a", "an", "will", "be", "in", "on", "at", "to", "for"}
        common = common - stop_words

        return len(common) >= 4

    @property
    def stats(self) -> dict:
        """Get detector statistics."""
        return {
            "scan_count": self._scan_count,
            "opportunities_found": self._opportunities_found,
            "last_scan_time": self._last_scan_time.isoformat() if self._last_scan_time else None,
            "last_scan_duration_ms": self._last_scan_duration_ms,
            "active_opportunities": len(self._opportunities),
            "platforms_connected": {
                "polymarket": self.polymarket is not None and self.polymarket.is_connected,
                "kalshi": self.kalshi is not None and self.kalshi.is_connected,
                "cex_count": len(self.cex_clients),
                "dex": self.dex_client is not None and self.dex_client.is_connected,
            },
        }
