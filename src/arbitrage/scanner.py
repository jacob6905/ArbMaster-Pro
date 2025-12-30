"""
ArbMaster Pro - Arbitrage Scanners

Individual scanner implementations for each arbitrage type.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from loguru import logger

from ..models.opportunity import (
    ArbitrageOpportunity,
    BinaryComplementArb,
    CrossPlatformArb,
    MultiOutcomeArb,
    DEXCEXArb,
    FundingRateArb,
    Platform,
    ArbitrageType,
)
from ..models.market import PredictionMarket


class BaseScanner(ABC):
    """Base class for all arbitrage scanners."""

    scanner_type: str = "base"

    def __init__(
        self,
        min_profit_threshold: Decimal = Decimal("0.01"),
        min_liquidity: Decimal = Decimal("10000"),
    ):
        self.min_profit_threshold = min_profit_threshold
        self.min_liquidity = min_liquidity
        self._scan_count = 0
        self._opportunities_found = 0

    @abstractmethod
    async def scan(self) -> list[ArbitrageOpportunity]:
        """Execute scan and return opportunities."""
        pass

    def _generate_id(self, prefix: str = "arb") -> str:
        """Generate unique opportunity ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


class BinaryComplementScanner(BaseScanner):
    """
    Scanner for Binary Complement Arbitrage.

    Detects when YES + NO < $1.00 on a single prediction market platform.
    """

    scanner_type = "binary_complement"

    def __init__(
        self,
        client,  # PolymarketClient or KalshiClient
        platform: Platform,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.client = client
        self.platform = platform

    async def scan(self) -> list[BinaryComplementArb]:
        """Scan for binary complement opportunities."""
        opportunities = []

        try:
            markets = await self.client.get_markets(status="active", limit=100)

            for market in markets:
                if not market.is_binary:
                    continue

                opp = await self._check_market(market)
                if opp:
                    opportunities.append(opp)
                    self._opportunities_found += 1

            self._scan_count += 1

        except Exception as e:
            logger.error(f"Binary complement scan error: {e}")

        return opportunities

    async def _check_market(
        self, market: PredictionMarket
    ) -> Optional[BinaryComplementArb]:
        """Check a single market for arbitrage opportunity."""
        try:
            yes_price, no_price = await self.client.get_best_prices(market.market_id)

            if yes_price is None or no_price is None:
                return None

            combined = yes_price + no_price

            if combined >= Decimal("1.0"):
                return None

            profit_pct = (Decimal("1.0") - combined) / combined

            if profit_pct < self.min_profit_threshold:
                return None

            # Get liquidity
            yes_book = await self.client.get_orderbook(market.market_id, "YES")
            no_book = await self.client.get_orderbook(market.market_id, "NO")

            yes_depth = yes_book.total_ask_depth() if yes_book else Decimal("0")
            no_depth = no_book.total_ask_depth() if no_book else Decimal("0")
            max_size = min(yes_depth, no_depth)

            if max_size * combined < self.min_liquidity:
                return None

            # Calculate fees (Polymarket: 0, Kalshi: complex formula)
            fee = Decimal("0")
            if self.platform == Platform.KALSHI:
                fee = self.client._calculate_fee(max_size, yes_price)
                fee += self.client._calculate_fee(max_size, no_price)

            net_profit_pct = profit_pct - fee / (max_size * combined) if max_size > 0 else profit_pct

            return BinaryComplementArb(
                id=self._generate_id("bc"),
                platform=self.platform,
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
                net_profit_pct=net_profit_pct,
                estimated_profit_usd=max_size * (Decimal("1.0") - combined) - fee,
                total_cost=max_size * combined,
                estimated_fees=fee,
                confidence=0.95,
                liquidity_score=min(1.0, float(max_size / 1000)),
            )

        except Exception as e:
            logger.debug(f"Error checking market {market.market_id}: {e}")
            return None


class CrossPlatformScanner(BaseScanner):
    """
    Scanner for Cross-Platform Arbitrage.

    Detects when the same event is priced differently on Polymarket vs Kalshi.
    """

    scanner_type = "cross_platform"

    def __init__(
        self,
        polymarket_client,
        kalshi_client,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.polymarket = polymarket_client
        self.kalshi = kalshi_client
        self._market_mappings: dict[str, str] = {}  # poly_id -> kalshi_id

    async def scan(self) -> list[CrossPlatformArb]:
        """Scan for cross-platform opportunities."""
        opportunities = []

        try:
            # Get markets from both platforms
            poly_markets = await self.polymarket.get_markets(limit=50)
            kalshi_markets = await self.kalshi.get_markets(limit=50)

            # Build index for matching
            kalshi_index = self._build_market_index(kalshi_markets)

            for poly_market in poly_markets:
                if not poly_market.is_binary:
                    continue

                # Find matching Kalshi market
                kalshi_market = self._find_matching_market(poly_market, kalshi_index)

                if not kalshi_market:
                    continue

                opps = await self._check_pair(poly_market, kalshi_market)
                opportunities.extend(opps)

            self._scan_count += 1
            self._opportunities_found += len(opportunities)

        except Exception as e:
            logger.error(f"Cross-platform scan error: {e}")

        return opportunities

    def _build_market_index(
        self, markets: list[PredictionMarket]
    ) -> dict[str, PredictionMarket]:
        """Build searchable index of markets."""
        index = {}
        for market in markets:
            # Index by various keys for matching
            if market.slug:
                index[market.slug.lower()] = market
            # Also index key words from title
            words = market.title.lower().split()
            key = "_".join(sorted(words[:5]))
            index[key] = market
        return index

    def _find_matching_market(
        self,
        poly_market: PredictionMarket,
        kalshi_index: dict[str, PredictionMarket],
    ) -> Optional[PredictionMarket]:
        """Find matching Kalshi market for a Polymarket market."""
        # Try slug match
        if poly_market.slug:
            slug_key = poly_market.slug.lower()
            if slug_key in kalshi_index:
                return kalshi_index[slug_key]

        # Try title match
        words = poly_market.title.lower().split()
        key = "_".join(sorted(words[:5]))
        if key in kalshi_index:
            return kalshi_index[key]

        return None

    async def _check_pair(
        self,
        poly_market: PredictionMarket,
        kalshi_market: PredictionMarket,
    ) -> list[CrossPlatformArb]:
        """Check a market pair for arbitrage opportunities."""
        opportunities = []

        try:
            poly_yes, poly_no = await self.polymarket.get_best_prices(
                poly_market.market_id
            )
            kalshi_yes, kalshi_no = await self.kalshi.get_best_prices(
                kalshi_market.market_id
            )

            if not all([poly_yes, poly_no, kalshi_yes, kalshi_no]):
                return opportunities

            # Check both cross combinations
            # Poly YES + Kalshi NO
            combined1 = poly_yes + kalshi_no
            if combined1 < Decimal("0.98"):
                opp = self._create_opportunity(
                    poly_market, kalshi_market,
                    "YES", poly_yes, "NO", kalshi_no
                )
                if opp:
                    opportunities.append(opp)

            # Poly NO + Kalshi YES
            combined2 = poly_no + kalshi_yes
            if combined2 < Decimal("0.98"):
                opp = self._create_opportunity(
                    poly_market, kalshi_market,
                    "NO", poly_no, "YES", kalshi_yes
                )
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.debug(f"Error checking pair: {e}")

        return opportunities

    def _create_opportunity(
        self,
        poly_market: PredictionMarket,
        kalshi_market: PredictionMarket,
        poly_side: str,
        poly_price: Decimal,
        kalshi_side: str,
        kalshi_price: Decimal,
    ) -> Optional[CrossPlatformArb]:
        """Create a cross-platform arbitrage opportunity."""
        combined = poly_price + kalshi_price

        # Calculate Kalshi fee
        kalshi_fee = self.kalshi._calculate_fee(Decimal("100"), kalshi_price)

        net_profit = Decimal("1.0") - combined - kalshi_fee / 100
        profit_pct = net_profit / combined

        if profit_pct < self.min_profit_threshold:
            return None

        return CrossPlatformArb(
            id=self._generate_id("cp"),
            platform_a=Platform.POLYMARKET,
            market_id_a=poly_market.market_id,
            side_a=poly_side,
            price_a=poly_price,
            platform_b=Platform.KALSHI,
            market_id_b=kalshi_market.market_id,
            side_b=kalshi_side,
            price_b=kalshi_price,
            event_slug=poly_market.slug or kalshi_market.slug or "",
            match_confidence=0.8,
            gross_profit_pct=profit_pct + kalshi_fee / 100 / combined,
            net_profit_pct=profit_pct,
            estimated_profit_usd=net_profit * 100,
            total_cost=combined * 100,
            estimated_fees=kalshi_fee,
        )


class MultiOutcomeScanner(BaseScanner):
    """
    Scanner for Multi-Outcome Bundle Arbitrage.

    Detects when sum of all outcome prices < $1.00 in multi-choice markets.
    """

    scanner_type = "multi_outcome"

    def __init__(self, client, platform: Platform, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.platform = platform

    async def scan(self) -> list[MultiOutcomeArb]:
        """Scan for multi-outcome bundle opportunities."""
        opportunities = []

        try:
            markets = await self.client.get_markets(status="active", limit=100)

            for market in markets:
                if market.is_binary or len(market.outcomes) < 3:
                    continue

                opp = await self._check_market(market)
                if opp:
                    opportunities.append(opp)

            self._scan_count += 1
            self._opportunities_found += len(opportunities)

        except Exception as e:
            logger.error(f"Multi-outcome scan error: {e}")

        return opportunities

    async def _check_market(
        self, market: PredictionMarket
    ) -> Optional[MultiOutcomeArb]:
        """Check a multi-outcome market for bundle arbitrage."""
        try:
            # Get prices for all outcomes
            outcome_prices = {}
            outcome_depths = {}
            total_cost = Decimal("0")
            min_depth = Decimal("inf")
            weakest_leg = ""

            for outcome in market.outcomes:
                book = await self.client.get_orderbook(
                    market.market_id, outcome.name
                )

                if not book or book.best_ask is None:
                    return None

                price = book.best_ask
                depth = book.total_ask_depth()

                outcome_prices[outcome.name] = price
                outcome_depths[outcome.name] = depth
                total_cost += price

                if depth < min_depth:
                    min_depth = depth
                    weakest_leg = outcome.name

            # Check for arbitrage
            if total_cost >= Decimal("1.0"):
                return None

            profit_pct = (Decimal("1.0") - total_cost) / total_cost

            if profit_pct < self.min_profit_threshold:
                return None

            # Check minimum liquidity on weakest leg
            if min_depth * total_cost < self.min_liquidity:
                return None

            return MultiOutcomeArb(
                id=self._generate_id("mo"),
                platform=self.platform,
                market_id=market.market_id,
                market_title=market.title,
                outcome_count=len(market.outcomes),
                outcome_prices=outcome_prices,
                outcome_depths=outcome_depths,
                bundle_cost=total_cost,
                weakest_leg=weakest_leg,
                weakest_depth=min_depth,
                gross_profit_pct=profit_pct,
                net_profit_pct=profit_pct,
                estimated_profit_usd=min_depth * (Decimal("1.0") - total_cost),
                total_cost=min_depth * total_cost,
            )

        except Exception as e:
            logger.debug(f"Error checking multi-outcome market: {e}")
            return None


class DEXCEXScanner(BaseScanner):
    """
    Scanner for DEX-CEX Price Gap Arbitrage.

    Detects price differences between decentralized and centralized exchanges.
    """

    scanner_type = "dex_cex"

    def __init__(
        self,
        dex_client,
        cex_clients: dict,
        tokens: list[str],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dex_client = dex_client
        self.cex_clients = cex_clients
        self.tokens = tokens

    async def scan(self) -> list[DEXCEXArb]:
        """Scan for DEX-CEX price gaps."""
        opportunities = []

        for token in self.tokens:
            try:
                opp = await self._check_token(token)
                if opp:
                    opportunities.append(opp)
            except Exception as e:
                logger.debug(f"Error checking token {token}: {e}")

        self._scan_count += 1
        self._opportunities_found += len(opportunities)

        return opportunities

    async def _check_token(self, token: str) -> Optional[DEXCEXArb]:
        """Check a single token for DEX-CEX arbitrage."""
        # Get DEX price
        dex_price = await self.dex_client.get_token_price(token, "USDC")

        if not dex_price:
            return None

        # Get CEX prices
        best_cex_price = None
        best_cex = None

        for exchange_id, client in self.cex_clients.items():
            try:
                ticker = await client.get_ticker(f"{token}/USDT")
                if ticker and ticker.get("last"):
                    price = Decimal(str(ticker["last"]))
                    if best_cex_price is None or price > best_cex_price:
                        best_cex_price = price
                        best_cex = exchange_id
            except Exception:
                continue

        if not best_cex_price or not best_cex:
            return None

        # Calculate spread
        spread = abs(dex_price - best_cex_price)
        spread_pct = spread / min(dex_price, best_cex_price)

        # Account for fees (~0.3% DEX, ~0.1% CEX)
        fee_pct = Decimal("0.004")
        net_profit_pct = spread_pct - fee_pct

        if net_profit_pct < self.min_profit_threshold:
            return None

        # Determine direction
        if dex_price < best_cex_price:
            buy_on, sell_on = "dex", "cex"
        else:
            buy_on, sell_on = "cex", "dex"

        return DEXCEXArb(
            id=self._generate_id("dc"),
            arb_type=ArbitrageType.DEX_CEX,
            token_symbol=token,
            dex_platform=Platform.UNISWAP,
            dex_price=dex_price,
            cex_platform=Platform(best_cex),
            cex_price=best_cex_price,
            cex_pair=f"{token}/USDT",
            buy_on=buy_on,
            sell_on=sell_on,
            max_trade_size=Decimal("5000"),
            gross_profit_pct=spread_pct,
            net_profit_pct=net_profit_pct,
            estimated_profit_usd=Decimal("5000") * net_profit_pct,
            total_cost=Decimal("5000"),
            estimated_fees=Decimal("5000") * fee_pct,
        )


class FundingRateScanner(BaseScanner):
    """
    Scanner for Funding Rate Arbitrage.

    Detects high funding rates suitable for spot-futures hedging.
    """

    scanner_type = "funding_rate"

    def __init__(
        self,
        cex_client,
        min_annualized_yield: Decimal = Decimal("0.08"),  # 8%
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cex_client = cex_client
        self.min_annualized_yield = min_annualized_yield

    async def scan(self) -> list[FundingRateArb]:
        """Scan for funding rate arbitrage opportunities."""
        opportunities = []

        try:
            funding_rates = await self.cex_client.get_all_funding_rates()

            for symbol, rate in funding_rates.items():
                opp = self._evaluate_funding_rate(symbol, rate)
                if opp:
                    opportunities.append(opp)

            self._scan_count += 1
            self._opportunities_found += len(opportunities)

        except Exception as e:
            logger.error(f"Funding rate scan error: {e}")

        return opportunities

    def _evaluate_funding_rate(
        self, symbol: str, rate: Decimal
    ) -> Optional[FundingRateArb]:
        """Evaluate a funding rate for arbitrage opportunity."""
        # Annualize the rate (8h periods, 3 per day)
        annualized = rate * 3 * 365

        if abs(annualized) < self.min_annualized_yield:
            return None

        # Estimate fees for hedge (~0.1% entry + exit)
        fee_pct = Decimal("0.002")
        net_yield = abs(annualized) - fee_pct * 365

        if net_yield < self.min_profit_threshold:
            return None

        return FundingRateArb(
            id=self._generate_id("fr"),
            arb_type=ArbitrageType.FUNDING_RATE,
            platform=Platform.BINANCE,
            symbol=symbol,
            current_funding_rate=rate,
            annualized_yield=annualized,
            spot_size=Decimal("10000"),
            futures_size=Decimal("10000"),
            next_funding_time=datetime.utcnow(),
            gross_profit_pct=abs(annualized),
            net_profit_pct=net_yield,
            estimated_profit_usd=Decimal("10000") * abs(rate),
            total_cost=Decimal("10000"),
            estimated_fees=Decimal("10000") * fee_pct,
        )
