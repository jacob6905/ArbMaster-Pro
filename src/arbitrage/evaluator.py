"""
ArbMaster Pro - Opportunity Evaluator

Evaluates and scores arbitrage opportunities based on multiple factors
including profitability, risk, liquidity, and execution feasibility.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger

from models.opportunity import (
    ArbitrageOpportunity,
    ArbitrageType,
    BinaryComplementArb,
    CrossPlatformArb,
)
from config import settings


class OpportunityEvaluator:
    """
    Evaluates arbitrage opportunities using multiple criteria.

    Scoring factors:
    - Profitability (expected return)
    - Risk (volatility, time sensitivity)
    - Liquidity (order book depth)
    - Execution complexity (number of legs, platforms)
    - Historical success rate
    """

    def __init__(
        self,
        min_score: float = 0.5,
        risk_weight: float = 0.3,
        profit_weight: float = 0.4,
        liquidity_weight: float = 0.2,
        complexity_weight: float = 0.1,
    ):
        self.min_score = min_score
        self.risk_weight = risk_weight
        self.profit_weight = profit_weight
        self.liquidity_weight = liquidity_weight
        self.complexity_weight = complexity_weight

        # Risk thresholds from config
        self.min_profit = settings.risk.min_profit_threshold
        self.max_slippage = settings.risk.max_slippage
        self.min_liquidity = settings.risk.min_liquidity_depth

    def evaluate(self, opportunity: ArbitrageOpportunity) -> dict:
        """
        Evaluate an opportunity and return detailed scoring.

        Returns:
            Dictionary with scores, recommendation, and reasoning
        """
        scores = {
            "profit_score": self._score_profitability(opportunity),
            "risk_score": self._score_risk(opportunity),
            "liquidity_score": self._score_liquidity(opportunity),
            "complexity_score": self._score_complexity(opportunity),
        }

        # Calculate weighted total
        total_score = (
            scores["profit_score"] * self.profit_weight
            + scores["risk_score"] * self.risk_weight
            + scores["liquidity_score"] * self.liquidity_weight
            + scores["complexity_score"] * self.complexity_weight
        )

        # Generate recommendation
        if total_score >= 0.8:
            recommendation = "STRONG_BUY"
            reasoning = "High-quality opportunity with excellent risk/reward"
        elif total_score >= 0.6:
            recommendation = "BUY"
            reasoning = "Good opportunity meeting all criteria"
        elif total_score >= self.min_score:
            recommendation = "CONSIDER"
            reasoning = "Marginal opportunity, proceed with caution"
        else:
            recommendation = "SKIP"
            reasoning = self._get_skip_reason(scores)

        return {
            "opportunity_id": opportunity.id,
            "arb_type": opportunity.arb_type.value,
            "total_score": round(total_score, 3),
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "recommendation": recommendation,
            "reasoning": reasoning,
            "expected_profit_usd": float(opportunity.estimated_profit_usd),
            "expected_profit_pct": float(opportunity.net_profit_pct * 100),
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    def _score_profitability(self, opp: ArbitrageOpportunity) -> float:
        """Score based on expected profit."""
        profit_pct = float(opp.net_profit_pct)

        # Scale: 1% = 0.3, 2% = 0.5, 5% = 0.8, 10%+ = 1.0
        if profit_pct >= 0.10:
            return 1.0
        elif profit_pct >= 0.05:
            return 0.8 + (profit_pct - 0.05) / 0.05 * 0.2
        elif profit_pct >= 0.02:
            return 0.5 + (profit_pct - 0.02) / 0.03 * 0.3
        elif profit_pct >= 0.01:
            return 0.3 + (profit_pct - 0.01) / 0.01 * 0.2
        else:
            return profit_pct / 0.01 * 0.3

    def _score_risk(self, opp: ArbitrageOpportunity) -> float:
        """Score based on risk factors (higher = lower risk)."""
        score = 1.0

        # Deduct for high risk score
        score -= opp.risk_score * 0.5

        # Deduct for time sensitivity
        if opp.time_sensitivity_ms < 1000:
            score -= 0.2  # Very time sensitive
        elif opp.time_sensitivity_ms < 3000:
            score -= 0.1

        # Deduct for low confidence
        score -= (1 - opp.confidence) * 0.3

        # Type-specific risk adjustments
        if opp.arb_type == ArbitrageType.CROSS_PLATFORM:
            score -= 0.1  # Higher execution risk
        elif opp.arb_type == ArbitrageType.DEX_CEX:
            score -= 0.15  # Gas and slippage risk

        return max(0.0, min(1.0, score))

    def _score_liquidity(self, opp: ArbitrageOpportunity) -> float:
        """Score based on liquidity."""
        liq_score = opp.liquidity_score

        # Binary complement specific
        if isinstance(opp, BinaryComplementArb):
            min_depth = min(float(opp.yes_depth), float(opp.no_depth))
            if min_depth >= 10000:
                liq_score = 1.0
            elif min_depth >= 5000:
                liq_score = 0.8
            elif min_depth >= 1000:
                liq_score = 0.5
            else:
                liq_score = min_depth / 1000 * 0.5

        return max(0.0, min(1.0, liq_score))

    def _score_complexity(self, opp: ArbitrageOpportunity) -> float:
        """Score based on execution complexity (higher = simpler)."""
        # Binary complement is simplest (single platform, 2 orders)
        if opp.arb_type == ArbitrageType.BINARY_COMPLEMENT:
            return 1.0

        # Cross-platform is medium (2 platforms, 2 orders)
        if opp.arb_type == ArbitrageType.CROSS_PLATFORM:
            return 0.7

        # Multi-outcome is more complex (single platform, N orders)
        if opp.arb_type == ArbitrageType.MULTI_OUTCOME:
            if isinstance(opp, BinaryComplementArb):
                return 0.8
            return 0.6

        # DEX-CEX has high complexity (different systems, gas)
        if opp.arb_type == ArbitrageType.DEX_CEX:
            return 0.4

        # Funding rate is moderate (single platform, 2 positions)
        if opp.arb_type == ArbitrageType.FUNDING_RATE:
            return 0.6

        return 0.5

    def _get_skip_reason(self, scores: dict) -> str:
        """Generate reason for skipping an opportunity."""
        reasons = []

        if scores["profit_score"] < 0.3:
            reasons.append("profit too low")

        if scores["risk_score"] < 0.4:
            reasons.append("risk too high")

        if scores["liquidity_score"] < 0.3:
            reasons.append("insufficient liquidity")

        if scores["complexity_score"] < 0.3:
            reasons.append("execution too complex")

        if not reasons:
            reasons.append("overall score below threshold")

        return "Skipped: " + ", ".join(reasons)

    def filter_opportunities(
        self,
        opportunities: list[ArbitrageOpportunity],
        min_score: Optional[float] = None,
    ) -> list[tuple[ArbitrageOpportunity, dict]]:
        """
        Filter and sort opportunities by score.

        Returns:
            List of (opportunity, evaluation) tuples, sorted by score
        """
        if min_score is None:
            min_score = self.min_score

        evaluated = []

        for opp in opportunities:
            evaluation = self.evaluate(opp)

            if evaluation["total_score"] >= min_score:
                evaluated.append((opp, evaluation))

        # Sort by score descending
        evaluated.sort(key=lambda x: x[1]["total_score"], reverse=True)

        return evaluated

    def rank_by_profit(
        self,
        opportunities: list[ArbitrageOpportunity],
        top_n: int = 10,
    ) -> list[ArbitrageOpportunity]:
        """
        Rank opportunities by expected profit.

        Returns:
            Top N opportunities by profit
        """
        sorted_opps = sorted(
            opportunities,
            key=lambda x: x.estimated_profit_usd,
            reverse=True,
        )

        return sorted_opps[:top_n]

    def estimate_execution_probability(
        self,
        opp: ArbitrageOpportunity,
    ) -> float:
        """
        Estimate probability of successful execution.

        Considers:
        - Time sensitivity
        - Liquidity depth
        - Historical fill rates
        """
        base_probability = 0.9

        # Adjust for time sensitivity
        if opp.time_sensitivity_ms < 1000:
            base_probability -= 0.2
        elif opp.time_sensitivity_ms < 2000:
            base_probability -= 0.1

        # Adjust for liquidity
        if opp.liquidity_score < 0.5:
            base_probability -= 0.2
        elif opp.liquidity_score < 0.8:
            base_probability -= 0.1

        # Adjust for complexity
        if opp.arb_type in (ArbitrageType.DEX_CEX, ArbitrageType.CROSS_PLATFORM):
            base_probability -= 0.1

        return max(0.1, min(1.0, base_probability))


class RiskAdjustedReturns:
    """
    Calculate risk-adjusted returns for opportunity comparison.
    """

    @staticmethod
    def sharpe_ratio(
        expected_return: Decimal,
        volatility: Decimal,
        risk_free_rate: Decimal = Decimal("0.05"),  # 5% annual
    ) -> float:
        """Calculate Sharpe ratio for an opportunity."""
        if volatility == 0:
            return float("inf") if expected_return > risk_free_rate else 0.0

        return float((expected_return - risk_free_rate) / volatility)

    @staticmethod
    def sortino_ratio(
        expected_return: Decimal,
        downside_volatility: Decimal,
        risk_free_rate: Decimal = Decimal("0.05"),
    ) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        if downside_volatility == 0:
            return float("inf") if expected_return > risk_free_rate else 0.0

        return float((expected_return - risk_free_rate) / downside_volatility)

    @staticmethod
    def kelly_criterion(
        win_probability: float,
        win_amount: Decimal,
        loss_amount: Decimal,
    ) -> Decimal:
        """
        Calculate optimal position size using Kelly Criterion.

        Returns fraction of capital to allocate.
        """
        if win_amount <= 0 or loss_amount <= 0:
            return Decimal("0")

        b = win_amount / loss_amount  # Odds ratio
        p = Decimal(str(win_probability))
        q = 1 - p

        kelly = (b * p - q) / b

        # Use fractional Kelly (half) for safety
        return max(Decimal("0"), kelly / 2)
