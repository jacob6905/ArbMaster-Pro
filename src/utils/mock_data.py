"""
ArbMaster Pro - Mock Data Provider

Generates synthetic data for markets, prices, and trades 
to enable "Simulation Mode" for testing and UI demonstrations.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal

class MockDataProvider:
    """Provides synthetic arbitrage and market data."""

    STRATEGIES = ["Binary Complement", "Cross-Platform", "DEX-CEX", "Funding Rate"]
    PLATFORMS = ["Polymarket", "Kalshi", "Binance", "KuCoin", "Uniswap"]

    @staticmethod
    def get_mock_metrics() -> Dict[str, Any]:
        """Generate synthetic global metrics."""
        return {
            "daily_profit": Decimal(str(round(random.uniform(50, 500), 2))),
            "total_trades": random.randint(10, 50),
            "win_rate": random.randint(65, 92),
            "avg_latency": random.randint(120, 350),
            "active_positions": random.randint(0, 5)
        }

    @staticmethod
    def get_mock_opportunities(count: int = 5) -> List[Dict[str, Any]]:
        """Generate synthetic arbitrage opportunities."""
        opps = []
        for i in range(count):
            strategy = random.choice(MockDataProvider.STRATEGIES)
            profit_pct = round(random.uniform(0.5, 4.5), 2)
            
            opps.append({
                "id": f"mock-opp-{i}",
                "title": f"Simulated {strategy} Opportunity",
                "strategy": strategy,
                "profit_pct": profit_pct,
                "confidence": round(random.uniform(0.7, 0.98), 2),
                "platforms": random.sample(MockDataProvider.PLATFORMS, 2),
                "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 60)),
                "ai_risk_score": round(random.uniform(0.05, 0.3), 2),
                "ai_reasoning": "Market sentiment is stable. Liquidity depth is sufficient for execution."
            })
        return sorted(opps, key=lambda x: x["profit_pct"], reverse=True)

    @staticmethod
    def get_mock_trades(count: int = 10) -> List[Dict[str, Any]]:
        """Generate synthetic trade history."""
        trades = []
        for i in range(count):
            status = random.choice(["Filled", "Filled", "Filled", "Failed"])
            profit = Decimal(str(round(random.uniform(-10, 100), 2))) if status == "Filled" else Decimal("0.00")
            
            trades.append({
                "id": f"mock-trade-{i}",
                "market": f"Market Event {random.randint(100, 999)}",
                "strategy": random.choice(MockDataProvider.STRATEGIES),
                "status": status,
                "profit": profit,
                "timestamp": datetime.now() - timedelta(hours=random.randint(1, 72))
            })
        return sorted(trades, key=lambda x: x["timestamp"], reverse=True)
