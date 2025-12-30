"""
ArbMaster Pro - Configuration Module

Centralized configuration management using pydantic-settings.
Loads from environment variables with sensible defaults.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class ExecutionConfig(BaseSettings):
    """Execution mode configuration."""

    dry_run: bool = Field(default=True, description="Paper trading mode")
    debug: bool = Field(default=False, description="Enable debug logging")

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
