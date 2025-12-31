"""
ArbMaster Pro - Public Data Provider

Fetches REAL live market data from open, unauthenticated APIs 
(Polymarket, Kalshi, Binance).
"""

import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal
from loguru import logger


class PublicDataProvider:
    """Provides real-time data from public API endpoints."""

    # Updated API endpoints
    GAMMA_API = "https://gamma-api.polymarket.com"
    KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"
    BINANCE_API = "https://api.binance.com/api/v3"

    @staticmethod
    async def fetch_polymarket_data() -> List[Dict[str, Any]]:
        """Fetch active markets from Polymarket Gamma API with real pricing."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Fetch active markets
                response = await client.get(
                    f"{PublicDataProvider.GAMMA_API}/markets",
                    params={"limit": 20, "active": "true", "closed": "false"}
                )
                if response.status_code == 200:
                    markets = response.json()
                    results = []
                    for m in markets:
                        # Extract real pricing data
                        slug = m.get("slug", "")
                        question = m.get("question", "Polymarket Event")
                        
                        # Get actual outcome prices from tokens
                        tokens = m.get("tokens", [])
                        yes_price = None
                        no_price = None
                        
                        for token in tokens:
                            outcome = token.get("outcome", "").lower()
                            price = token.get("price")
                            if price:
                                if outcome == "yes":
                                    yes_price = float(price)
                                elif outcome == "no":
                                    no_price = float(price)
                        
                        # Calculate REAL arbitrage spread (Binary Complement)
                        # If YES + NO < 1.00, there's an arb opportunity
                        profit_pct = 0.0
                        if yes_price is not None and no_price is not None:
                            total_cost = yes_price + no_price
                            if total_cost < 1.0:
                                # Real arbitrage exists!
                                profit_pct = round((1.0 - total_cost) * 100, 2)
                            else:
                                # No arb, but show the "spread" as negative or 0
                                profit_pct = round((1.0 - total_cost) * 100, 2)
                        else:
                            # Fallback: use outcomePrices if available
                            outcome_prices = m.get("outcomePrices", "")
                            if outcome_prices:
                                try:
                                    prices = [float(p) for p in outcome_prices.split(",")]
                                    if len(prices) >= 2:
                                        total_cost = sum(prices[:2])
                                        profit_pct = round((1.0 - total_cost) * 100, 2)
                                except:
                                    pass
                        
                        # Get volume and liquidity
                        volume = float(m.get("volume", 0) or 0)
                        liquidity = float(m.get("liquidity", 0) or 0)
                        
                        results.append({
                            "id": f"poly-{m.get('id', slug)}",
                            "slug": slug,
                            "title": question,
                            "strategy": "Binary Complement" if profit_pct > 0 else "Contextual Monitor",
                            "profit_pct": max(profit_pct, 0),  # Show 0 if negative
                            "spread_pct": profit_pct,  # Keep raw spread for analysis
                            "confidence": 0.85 if profit_pct > 0 else 0.5,
                            "platforms": ["Polymarket"],
                            "timestamp": datetime.now(),
                            "ai_risk_score": 0.15,
                            "ai_reasoning": f"Live data: YES={yes_price}, NO={no_price}",
                            "volume_24h": volume,
                            "liquidity": liquidity,
                            "yes_price": yes_price,
                            "no_price": no_price,
                        })
                    return results
                else:
                    logger.warning(f"Polymarket API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Polymarket data: {e}")
        return []

    @staticmethod
    async def fetch_kalshi_data() -> List[Dict[str, Any]]:
        """Fetch active markets from Kalshi Public API with real pricing."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{PublicDataProvider.KALSHI_API}/markets",
                    params={"limit": 20, "status": "open"}
                )
                if response.status_code == 200:
                    data = response.json()
                    markets = data.get("markets", [])
                    results = []
                    for m in markets:
                        ticker = m.get("ticker", "")
                        title = m.get("title", "Kalshi Event")
                        
                        # Extract REAL pricing from Kalshi response
                        # Kalshi uses yes_bid, yes_ask, last_price etc.
                        yes_bid = m.get("yes_bid")
                        yes_ask = m.get("yes_ask") 
                        no_bid = m.get("no_bid")
                        no_ask = m.get("no_ask")
                        last_price = m.get("last_price")
                        
                        # Calculate spread/arb potential
                        profit_pct = 0.0
                        yes_price = None
                        no_price = None
                        
                        if yes_ask is not None and no_ask is not None:
                            # Best case: buy at ask prices
                            yes_price = yes_ask / 100.0  # Kalshi uses cents
                            no_price = no_ask / 100.0
                            total_cost = yes_price + no_price
                            if total_cost < 1.0:
                                profit_pct = round((1.0 - total_cost) * 100, 2)
                        elif last_price is not None:
                            # Fallback to last traded price
                            yes_price = last_price / 100.0
                            no_price = 1.0 - yes_price
                        
                        # Volume data
                        volume = m.get("volume", 0) or 0
                        open_interest = m.get("open_interest", 0) or 0
                        
                        results.append({
                            "id": f"kalshi-{m.get('id') or ticker}",
                            "ticker": ticker,
                            "title": title,
                            "strategy": "Binary Complement" if profit_pct > 0 else "Cross-Platform",
                            "profit_pct": max(profit_pct, 0),
                            "spread_pct": profit_pct,
                            "confidence": 0.9 if profit_pct > 0 else 0.6,
                            "platforms": ["Kalshi"],
                            "timestamp": datetime.now(),
                            "ai_risk_score": 0.1,
                            "ai_reasoning": f"Live: YES ask={yes_ask}¢, NO ask={no_ask}¢",
                            "volume": volume,
                            "open_interest": open_interest,
                            "yes_price": yes_price,
                            "no_price": no_price,
                        })
                    return results
                else:
                    logger.warning(f"Kalshi API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Kalshi data: {e}")
        return []

    @staticmethod
    async def fetch_binance_prices() -> Dict[str, Any]:
        """Fetch real crypto prices from Binance."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get multiple tickers
                response = await client.get(
                    f"{PublicDataProvider.BINANCE_API}/ticker/24hr",
                    params={"symbols": '["BTCUSDT","ETHUSDT","SOLUSDT"]'}
                )
                if response.status_code == 200:
                    tickers = response.json()
                    return {
                        t['symbol']: {
                            'price': float(t['lastPrice']),
                            'change_24h': float(t['priceChangePercent']),
                            'volume_24h': float(t['volume']),
                            'high_24h': float(t['highPrice']),
                            'low_24h': float(t['lowPrice']),
                        }
                        for t in tickers
                    }
        except Exception as e:
            logger.error(f"Error fetching Binance data: {e}")
        return {}

    @staticmethod
    async def get_live_opportunities() -> List[Dict[str, Any]]:
        """Aggregate live data from multiple public sources."""
        poly_task = PublicDataProvider.fetch_polymarket_data()
        kalshi_task = PublicDataProvider.fetch_kalshi_data()
        
        results = await asyncio.gather(poly_task, kalshi_task, return_exceptions=True)
        
        combined = []
        for result in results:
            if isinstance(result, list):
                combined.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"API fetch error: {result}")
        
        # Sort by profit potential (highest first)
        combined.sort(key=lambda x: x.get('profit_pct', 0), reverse=True)
        
        return combined[:20]

    @staticmethod
    async def get_crypto_dashboard_data() -> Dict[str, Any]:
        """Get crypto prices for dashboard display."""
        prices = await PublicDataProvider.fetch_binance_prices()
        return {
            "btc": prices.get("BTCUSDT", {}),
            "eth": prices.get("ETHUSDT", {}),
            "sol": prices.get("SOLUSDT", {}),
        }
