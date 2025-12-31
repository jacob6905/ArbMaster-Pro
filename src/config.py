"""
ArbMaster Pro - Configuration Module

Centralized configuration management using pydantic-settings.
Loads from environment variables with sensible defaults.
"""

from typing import Optional, Any
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from project root
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # If .env doesn't exist, try to load from .env.example as a template
    env_example = Path(__file__).parent.parent / ".env.example"
    if env_example.exists():
        load_dotenv(env_example)


def parse_bool(value: Any) -> bool:
    """Parse boolean from various input formats, handling typos."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        # Normalize: lowercase, strip whitespace and trailing numbers (typo fix)
        cleaned = value.lower().strip().rstrip('0123456789')
        if cleaned in ('true', 't', 'yes', 'y', '1', 'on'):
            return True
        if cleaned in ('false', 'f', 'no', 'n', '0', 'off', ''):
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


class ExecutionConfig(BaseSettings):
    """Execution mode configuration."""

    dry_run: bool = Field(default=True, description="Paper trading mode")
    debug: bool = Field(default=False, description="Enable debug logging")

    @field_validator('dry_run', 'debug', mode='before')
    @classmethod
    def validate_bool(cls, v: Any) -> bool:
        """Handle boolean parsing with typo tolerance."""
        return parse_bool(v)

    class Config:
        env_prefix = ""


class PolymarketConfig(BaseSettings):
    """Polymarket API configuration."""

    api_key: Optional[str] = Field(default=None)
    api_secret: Optional[str] = Field(default=None)
    private_key: Optional[str] = Field(default=None)
    chain_id: int = Field(default=137)  # Polygon Mainnet
    clob_url: str = Field(default="https://clob.polymarket.com")
    gamma_url: str = Field(default="https://gamma-api.polymarket.com")

    class Config:
        env_prefix = "POLYMARKET_"


class KalshiConfig(BaseSettings):
    """Kalshi API configuration."""

    api_key: Optional[str] = Field(default=None)
    api_secret: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    base_url: str = Field(default="https://trading-api.kalshi.com/trade-api/v2")

    class Config:
        env_prefix = "KALSHI_"


class ExchangeConfig(BaseSettings):
    """Centralized exchange configuration."""

    binance_api_key: Optional[str] = Field(default=None)
    binance_api_secret: Optional[str] = Field(default=None)
    kucoin_api_key: Optional[str] = Field(default=None)
    kucoin_api_secret: Optional[str] = Field(default=None)
    kucoin_passphrase: Optional[str] = Field(default=None)
    okx_api_key: Optional[str] = Field(default=None)
    okx_api_secret: Optional[str] = Field(default=None)
    okx_passphrase: Optional[str] = Field(default=None)

    class Config:
        env_prefix = ""


class BlockchainConfig(BaseSettings):
    """Blockchain and DeFi configuration."""

    polygon_rpc_url: str = Field(default="https://polygon-rpc.com")
    ethereum_rpc_url: str = Field(default="https://eth.llamarpc.com")
    arbitrum_rpc_url: str = Field(default="https://arb1.arbitrum.io/rpc")
    wallet_address: Optional[str] = Field(default=None)
    wallet_private_key: Optional[str] = Field(default=None)

    class Config:
        env_prefix = ""


class AIConfig(BaseSettings):
    """AI/LLM integration configuration."""

    anthropic_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    google_ai_api_key: Optional[str] = Field(default=None)

    # Model preferences
    primary_model: str = Field(default="claude-3-5-sonnet-20241022")
    fast_model: str = Field(default="claude-3-5-haiku-20241022")

    class Config:
        env_prefix = ""


class RiskConfig(BaseSettings):
    """Risk management configuration."""

    # Capital limits
    max_capital_usd: float = Field(default=50000.0)
    max_position_per_market: float = Field(default=5000.0)
    max_total_positions: float = Field(default=25000.0)

    # Circuit breakers
    max_daily_loss_usd: float = Field(default=500.0)
    max_consecutive_errors: int = Field(default=5)
    cooldown_seconds: int = Field(default=60)

    # Execution parameters
    min_profit_threshold: float = Field(default=0.01)  # 1%
    max_slippage: float = Field(default=0.002)  # 0.2%
    min_liquidity_depth: float = Field(default=10000.0)  # $10k
    max_gas_price_gwei: int = Field(default=100)

    class Config:
        env_prefix = ""


class PerformanceConfig(BaseSettings):
    """Performance targets configuration."""

    target_daily_profit: float = Field(default=500.0)
    target_win_rate: float = Field(default=0.90)
    target_latency_ms: int = Field(default=500)

    class Config:
        env_prefix = "TARGET_"


class NotificationConfig(BaseSettings):
    """Notification services configuration."""

    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)
    discord_webhook_url: Optional[str] = Field(default=None)

    class Config:
        env_prefix = ""


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    database_url: str = Field(default="sqlite+aiosqlite:///./arbmaster.db")
    redis_url: str = Field(default="redis://localhost:6379/0")

    class Config:
        env_prefix = ""


class ServerConfig(BaseSettings):
    """Server configuration."""

    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    dashboard_port: int = Field(default=8501)

    class Config:
        env_prefix = ""


class Settings:
    """Master settings container."""

    def __init__(self):
        self.execution = ExecutionConfig()
        self.polymarket = PolymarketConfig()
        self.kalshi = KalshiConfig()
        self.exchanges = ExchangeConfig()
        self.blockchain = BlockchainConfig()
        self.ai = AIConfig()
        self.risk = RiskConfig()
        self.performance = PerformanceConfig()
        self.notifications = NotificationConfig()
        self.database = DatabaseConfig()
        self.server = ServerConfig()

    @property
    def is_dry_run(self) -> bool:
        """Check if running in dry-run mode."""
        return self.execution.dry_run

    def validate_trading_ready(self) -> tuple[bool, list[str]]:
        """Validate all required credentials for live trading."""
        errors = []

        # Check Polymarket credentials
        if not self.polymarket.private_key:
            errors.append("Missing POLYMARKET_PRIVATE_KEY")

        # Check wallet
        if not self.blockchain.wallet_private_key:
            errors.append("Missing WALLET_PRIVATE_KEY")

        return len(errors) == 0, errors


# Global settings instance
settings = Settings()
