"""
ArbMaster Pro - Circuit Breaker

Automatic trading halt mechanism to protect capital from excessive losses,
technical failures, or unusual market conditions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, Callable
from loguru import logger


class CircuitBreakerTrigger(str, Enum):
    """Reasons for circuit breaker activation."""

    DAILY_LOSS = "daily_loss"
    CONSECUTIVE_ERRORS = "consecutive_errors"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    MANUAL = "manual"
    VOLATILITY = "volatility"
    API_ERROR = "api_error"


class CircuitBreaker:
    """
    Circuit breaker for automated trading halt.

    Triggers:
    - Daily loss exceeds threshold
    - Too many consecutive errors
    - Too many consecutive losses
    - Manual trigger
    - Unusual volatility detection
    """

    def __init__(
        self,
        max_daily_loss: Decimal = Decimal("500"),
        max_consecutive_errors: int = 5,
        max_consecutive_losses: int = 10,
        cooldown_seconds: int = 60,
        volatility_threshold: float = 0.1,  # 10% price swing
    ):
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_errors = max_consecutive_errors
        self.max_consecutive_losses = max_consecutive_losses
        self.cooldown_seconds = cooldown_seconds
        self.volatility_threshold = volatility_threshold

        # State
        self._triggered = False
        self._trigger_reason: Optional[CircuitBreakerTrigger] = None
        self._triggered_at: Optional[datetime] = None
        self._cooldown_until: Optional[datetime] = None

        # Counters
        self._daily_loss = Decimal("0")
        self._consecutive_errors = 0
        self._consecutive_losses = 0
        self._error_messages: list[str] = []

        # Callbacks
        self._on_trigger: Optional[Callable[[CircuitBreakerTrigger, str], None]] = None
        self._on_reset: Optional[Callable[[], None]] = None

    @property
    def is_triggered(self) -> bool:
        """Check if circuit breaker is currently triggered."""
        return self._triggered

    @property
    def is_in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if self._cooldown_until is None:
            return False
        return datetime.utcnow() < self._cooldown_until

    @property
    def should_halt(self) -> bool:
        """Check if trading should be halted."""
        return self._triggered or self.is_in_cooldown

    @property
    def status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "triggered": self._triggered,
            "trigger_reason": self._trigger_reason.value if self._trigger_reason else None,
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None,
            "in_cooldown": self.is_in_cooldown,
            "cooldown_until": self._cooldown_until.isoformat() if self._cooldown_until else None,
            "daily_loss": float(self._daily_loss),
            "consecutive_errors": self._consecutive_errors,
            "consecutive_losses": self._consecutive_losses,
            "can_trade": not self.should_halt,
        }

    def set_callbacks(
        self,
        on_trigger: Optional[Callable[[CircuitBreakerTrigger, str], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set callback functions for state changes."""
        self._on_trigger = on_trigger
        self._on_reset = on_reset

    def check_and_trigger(self) -> bool:
        """
        Check all conditions and trigger if necessary.

        Returns:
            True if circuit breaker was triggered
        """
        # Check daily loss
        if self._daily_loss >= self.max_daily_loss:
            self.trigger(
                CircuitBreakerTrigger.DAILY_LOSS,
                f"Daily loss ${self._daily_loss} exceeded limit ${self.max_daily_loss}",
            )
            return True

        # Check consecutive errors
        if self._consecutive_errors >= self.max_consecutive_errors:
            self.trigger(
                CircuitBreakerTrigger.CONSECUTIVE_ERRORS,
                f"Consecutive errors ({self._consecutive_errors}) exceeded limit",
            )
            return True

        # Check consecutive losses
        if self._consecutive_losses >= self.max_consecutive_losses:
            self.trigger(
                CircuitBreakerTrigger.CONSECUTIVE_LOSSES,
                f"Consecutive losses ({self._consecutive_losses}) exceeded limit",
            )
            return True

        return False

    def trigger(
        self,
        reason: CircuitBreakerTrigger,
        message: str = "",
    ) -> None:
        """Manually trigger the circuit breaker."""
        if self._triggered:
            return

        self._triggered = True
        self._trigger_reason = reason
        self._triggered_at = datetime.utcnow()

        logger.warning(f"CIRCUIT BREAKER TRIGGERED: {reason.value} - {message}")

        if self._on_trigger:
            self._on_trigger(reason, message)

    def record_loss(self, amount: Decimal) -> bool:
        """
        Record a trading loss.

        Returns:
            True if circuit breaker was triggered
        """
        self._daily_loss += abs(amount)
        self._consecutive_losses += 1

        return self.check_and_trigger()

    def record_win(self, amount: Decimal) -> None:
        """Record a trading win (resets consecutive losses)."""
        self._consecutive_losses = 0
        self._consecutive_errors = 0

    def record_error(self, error_message: str) -> bool:
        """
        Record an execution error.

        Returns:
            True if circuit breaker was triggered
        """
        self._consecutive_errors += 1
        self._error_messages.append(f"{datetime.utcnow().isoformat()}: {error_message}")

        # Keep only recent errors
        if len(self._error_messages) > 100:
            self._error_messages = self._error_messages[-100:]

        return self.check_and_trigger()

    def record_success(self) -> None:
        """Record successful execution (resets error counter)."""
        self._consecutive_errors = 0

    def start_cooldown(self) -> None:
        """Start the cooldown period."""
        self._cooldown_until = datetime.utcnow() + timedelta(seconds=self.cooldown_seconds)
        logger.info(f"Starting cooldown until {self._cooldown_until.isoformat()}")

    def reset(self) -> None:
        """Reset the circuit breaker to normal state."""
        was_triggered = self._triggered

        self._triggered = False
        self._trigger_reason = None
        self._triggered_at = None
        self._cooldown_until = None
        self._consecutive_errors = 0

        if was_triggered:
            logger.info("Circuit breaker reset to normal state")

            if self._on_reset:
                self._on_reset()

    def reset_daily(self) -> None:
        """Reset daily counters (call at day boundary)."""
        self._daily_loss = Decimal("0")
        self._consecutive_losses = 0
        self._consecutive_errors = 0
        self._error_messages.clear()

        logger.info("Circuit breaker daily counters reset")

    def check_volatility(
        self,
        price_change_pct: float,
        timeframe_minutes: int = 5,
    ) -> bool:
        """
        Check if price volatility exceeds threshold.

        Returns:
            True if circuit breaker was triggered
        """
        if abs(price_change_pct) >= self.volatility_threshold:
            self.trigger(
                CircuitBreakerTrigger.VOLATILITY,
                f"Price changed {price_change_pct:.1%} in {timeframe_minutes} minutes",
            )
            return True

        return False

    def get_recovery_actions(self) -> list[str]:
        """Get recommended recovery actions based on trigger reason."""
        if not self._triggered:
            return []

        actions = ["Wait for cooldown period to expire"]

        if self._trigger_reason == CircuitBreakerTrigger.DAILY_LOSS:
            actions.extend([
                "Review losing trades for patterns",
                "Consider reducing position sizes",
                "Check for unusual market conditions",
            ])

        elif self._trigger_reason == CircuitBreakerTrigger.CONSECUTIVE_ERRORS:
            actions.extend([
                "Check API connectivity",
                "Verify credentials are valid",
                "Review error logs for patterns",
                "Check exchange status pages",
            ])

        elif self._trigger_reason == CircuitBreakerTrigger.VOLATILITY:
            actions.extend([
                "Wait for market to stabilize",
                "Review news for major events",
                "Consider manual override only if conditions are understood",
            ])

        elif self._trigger_reason == CircuitBreakerTrigger.CONSECUTIVE_LOSSES:
            actions.extend([
                "Review strategy parameters",
                "Check for market regime change",
                "Analyze recent trades for systematic issues",
            ])

        return actions
