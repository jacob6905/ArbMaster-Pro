"""
ArbMaster Pro - Arbitrage Detection Engine

Core module for detecting and evaluating arbitrage opportunities.
"""

from .detector import ArbitrageDetector
from .scanner import (
    BinaryComplementScanner,
    CrossPlatformScanner,
    MultiOutcomeScanner,
    DEXCEXScanner,
    FundingRateScanner,
)
from .evaluator import OpportunityEvaluator

__all__ = [
    "ArbitrageDetector",
    "BinaryComplementScanner",
    "CrossPlatformScanner",
    "MultiOutcomeScanner",
    "DEXCEXScanner",
    "FundingRateScanner",
    "OpportunityEvaluator",
]
