"""
ArbMaster Pro - FastAPI Backend Server

Comprehensive REST API and WebSocket server for the Next.js frontend.
Provides real-time data, trading controls, and system monitoring.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import settings


# ============================================================================
# Enums
# ============================================================================

class StrategyType(str, Enum):
    BINARY_COMPLEMENT = "binary_complement"
    CROSS_PLATFORM = "cross_platform"
    MULTI_OUTCOME = "multi_outcome"
    DEX_CEX = "dex_cex"
    FUNDING_RATE = "funding_rate"
    YIELD_FARMING = "yield_farming"


class PlatformType(str, Enum):
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    BINANCE = "binance"
    UNISWAP = "uniswap"
    AAVE = "aave"
    SUSHISWAP = "sushiswap"


class TradeStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


# ============================================================================
# Pydantic Models
# ============================================================================

class PerformanceMetrics(BaseModel):
    total_pnl: float = Field(default=0.0, description="Total profit/loss")
    daily_pnl: float = Field(default=0.0, description="Today's profit/loss")
    weekly_pnl: float = Field(default=0.0, description="This week's profit/loss")
    monthly_pnl: float = Field(default=0.0, description="This month's profit/loss")
    win_rate: float = Field(default=0.0, description="Win rate percentage")
    total_trades: int = Field(default=0, description="Total trades executed")
    active_positions: int = Field(default=0, description="Number of active positions")
    active_capital: float = Field(default=0.0, description="Capital in active positions")
    daily_roi: float = Field(default=0.0, description="Daily return on investment %")


class ArbitrageOpportunity(BaseModel):
    id: str
    type: StrategyType
    markets: List[Dict[str, Any]]
    profit_pct: float
    net_profit_pct: float
    required_capital: float
    liquidity: float
    expires_at: Optional[datetime]
    detected_at: datetime
    confidence: float
    title: str
    platforms: List[str]


class Trade(BaseModel):
    id: str
    market_id: str
    strategy_id: str
    type: str  # buy/sell
    side: str  # YES/NO
    size: float
    price: float
    fees: float
    status: TradeStatus
    executed_at: datetime
    profit_usd: Optional[float] = 0.0


class Position(BaseModel):
    id: str
    market_id: str
    outcome_id: str
    side: str
    size: float
    avg_entry_price: float
    current_value: float
    unrealized_pnl: float
    created_at: datetime


class Strategy(BaseModel):
    id: str
    type: StrategyType
    name: str
    description: str
    enabled: bool
    allocation: float
    roi: float
    trades: int
    win_rate: float
    parameters: Dict[str, Any]


class PlatformStatus(BaseModel):
    name: str
    platform: PlatformType
    status: str  # online/offline/error
    last_update: datetime
    latency_ms: Optional[float]


class CircuitBreakerStatus(BaseModel):
    is_triggered: bool
    daily_loss: float
    max_daily_loss: float
    consecutive_errors: int
    max_consecutive_errors: int
    trades_today: int
    max_trades_per_day: int
    reason: Optional[str] = None


# ============================================================================
# Global State
# ============================================================================

class AppState:
    def __init__(self):
        self.running: bool = False
        self.started_at: Optional[datetime] = None
        self.last_scan: Optional[datetime] = None

        # Mock data (replace with real data sources)
        self.metrics = PerformanceMetrics(
            total_pnl=2847.32,
            daily_pnl=127.50,
            weekly_pnl=634.80,
            monthly_pnl=2847.32,
            win_rate=87.3,
            total_trades=147,
            active_positions=12,
            active_capital=15000.0,
            daily_roi=3.2
        )

        self.opportunities: List[ArbitrageOpportunity] = []
        self.trades: List[Trade] = []
        self.positions: List[Position] = []
        self.strategies: List[Strategy] = self._init_strategies()
        self.platform_status: List[PlatformStatus] = self._init_platforms()
        self.circuit_breaker = CircuitBreakerStatus(
            is_triggered=False,
            daily_loss=127.50,
            max_daily_loss=500.0,
            consecutive_errors=0,
            max_consecutive_errors=5,
            trades_today=12,
            max_trades_per_day=200
        )

        # WebSocket connections
        self.active_connections: List[WebSocket] = []

    def _init_strategies(self) -> List[Strategy]:
        return [
            Strategy(
                id="binary_complement",
                type=StrategyType.BINARY_COMPLEMENT,
                name="Binary Complement Arbitrage",
                description="YES + NO < $1.00 risk-free opportunities",
                enabled=True,
                allocation=40.0,
                roi=12.4,
                trades=47,
                win_rate=96.1,
                parameters={
                    "min_profit_threshold": 0.02,
                    "max_position_size": 5000,
                    "min_liquidity": 10000
                }
            ),
            Strategy(
                id="cross_platform",
                type=StrategyType.CROSS_PLATFORM,
                name="Cross-Platform Arbitrage",
                description="Polymarket vs Kalshi price gaps",
                enabled=True,
                allocation=30.0,
                roi=8.2,
                trades=23,
                win_rate=91.3,
                parameters={
                    "min_spread": 0.03,
                    "kalshi_fee_buffer": 0.07
                }
            ),
            Strategy(
                id="multi_outcome",
                type=StrategyType.MULTI_OUTCOME,
                name="Multi-Outcome Bundle",
                description="All outcomes < $1.00 in multi-choice markets",
                enabled=False,
                allocation=0.0,
                roi=0.0,
                trades=0,
                win_rate=0.0,
                parameters={
                    "min_outcomes": 3,
                    "max_outcomes": 20
                }
            )
        ]

    def _init_platforms(self) -> List[PlatformStatus]:
        return [
            PlatformStatus(
                name="Polymarket",
                platform=PlatformType.POLYMARKET,
                status="online",
                last_update=datetime.utcnow(),
                latency_ms=127.5
            ),
            PlatformStatus(
                name="Kalshi",
                platform=PlatformType.KALSHI,
                status="online",
                last_update=datetime.utcnow(),
                latency_ms=234.2
            ),
            PlatformStatus(
                name="Binance",
                platform=PlatformType.BINANCE,
                status="offline",
                last_update=datetime.utcnow(),
                latency_ms=None
            ),
            PlatformStatus(
                name="Uniswap",
                platform=PlatformType.UNISWAP,
                status="online",
                last_update=datetime.utcnow(),
                latency_ms=89.3
            ),
            PlatformStatus(
                name="Aave",
                platform=PlatformType.AAVE,
                status="online",
                last_update=datetime.utcnow(),
                latency_ms=156.7
            ),
            PlatformStatus(
                name="SushiSwap",
                platform=PlatformType.SUSHISWAP,
                status="offline",
                last_update=datetime.utcnow(),
                latency_ms=None
            )
        ]


state = AppState()


# ============================================================================
# Mock Data Generators
# ============================================================================

def generate_mock_opportunity() -> ArbitrageOpportunity:
    """Generate a mock arbitrage opportunity for testing."""
    strategy_types = list(StrategyType)
    strategy = random.choice(strategy_types)

    markets_data = [
        "Bitcoin > $100k by January",
        "Trump 2028 Win",
        "ETH above $5000",
        "Oscar Best Picture Winner",
        "S&P 500 ATH before March"
    ]

    return ArbitrageOpportunity(
        id=f"opp_{datetime.utcnow().timestamp()}",
        type=strategy,
        markets=[{"platform": "polymarket", "market_id": "0x123", "price": 0.48}],
        profit_pct=round(random.uniform(1.5, 8.0), 2),
        net_profit_pct=round(random.uniform(1.0, 6.0), 2),
        required_capital=round(random.uniform(1000, 10000), 2),
        liquidity=round(random.uniform(10000, 50000), 2),
        expires_at=datetime.utcnow() + timedelta(hours=random.randint(1, 72)),
        detected_at=datetime.utcnow(),
        confidence=round(random.uniform(0.7, 0.98), 2),
        title=random.choice(markets_data),
        platforms=["polymarket", "kalshi"]
    )


def generate_mock_trade() -> Trade:
    """Generate a mock trade for testing."""
    return Trade(
        id=f"trade_{datetime.utcnow().timestamp()}",
        market_id="market_123",
        strategy_id=random.choice(["binary_complement", "cross_platform"]),
        type=random.choice(["buy", "sell"]),
        side=random.choice(["YES", "NO"]),
        size=round(random.uniform(100, 1000), 2),
        price=round(random.uniform(0.3, 0.7), 4),
        fees=round(random.uniform(0.5, 5.0), 2),
        status=random.choice([TradeStatus.FILLED, TradeStatus.PENDING]),
        executed_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
        profit_usd=round(random.uniform(5, 50), 2)
    )


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    state.started_at = datetime.utcnow()
    state.running = True

    # Start background tasks
    asyncio.create_task(background_opportunity_generator())

    yield

    # Cleanup
    state.running = False


app = FastAPI(
    title="ArbMaster Pro API",
    description="Universal Arbitrage Trading Platform - REST API & WebSocket Server",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://*.railway.app",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Background Tasks
# ============================================================================

async def background_opportunity_generator():
    """Generate mock opportunities in the background."""
    while state.running:
        await asyncio.sleep(random.uniform(5, 15))

        # Generate new opportunity
        if random.random() > 0.3:  # 70% chance
            opp = generate_mock_opportunity()
            state.opportunities.append(opp)

            # Keep only last 20 opportunities
            state.opportunities = state.opportunities[-20:]

            # Broadcast to WebSocket clients
            await broadcast_message({
                "type": "new_opportunity",
                "data": opp.dict()
            })

        # Update metrics randomly
        state.metrics.daily_pnl += round(random.uniform(-5, 15), 2)
        state.metrics.total_pnl = state.metrics.daily_pnl * 22.3  # Simulate monthly growth

        await broadcast_message({
            "type": "metrics_update",
            "data": state.metrics.dict()
        })


async def broadcast_message(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    for connection in state.active_connections:
        try:
            await connection.send_json(message)
        except:
            pass


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ArbMaster Pro API",
        "description": "Universal Arbitrage Trading Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "metrics": "/api/metrics",
            "opportunities": "/api/opportunities",
            "trades": "/api/trades",
            "positions": "/api/positions",
            "strategies": "/api/strategies",
            "platforms": "/api/platforms",
            "circuit_breaker": "/api/circuit-breaker"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    uptime = 0.0
    if state.started_at:
        uptime = (datetime.utcnow() - state.started_at).total_seconds()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime,
        "mode": "dry_run" if settings.execution.dry_run else "live",
        "version": "1.0.0"
    }


@app.get("/api/metrics", response_model=PerformanceMetrics)
async def get_metrics():
    """Get current performance metrics."""
    return state.metrics


@app.get("/api/opportunities", response_model=List[ArbitrageOpportunity])
async def get_opportunities(limit: int = 20):
    """Get current arbitrage opportunities."""
    return state.opportunities[-limit:]


@app.get("/api/trades", response_model=List[Trade])
async def get_trades(limit: int = 50):
    """Get recent trades."""
    # Generate some mock trades if empty
    if not state.trades:
        state.trades = [generate_mock_trade() for _ in range(10)]

    return state.trades[-limit:]


@app.get("/api/positions", response_model=List[Position])
async def get_positions():
    """Get active positions."""
    return state.positions


@app.get("/api/strategies", response_model=List[Strategy])
async def get_strategies():
    """Get all trading strategies."""
    return state.strategies


@app.post("/api/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str):
    """Enable or disable a trading strategy."""
    for strategy in state.strategies:
        if strategy.id == strategy_id:
            strategy.enabled = not strategy.enabled
            return {
                "success": True,
                "strategy_id": strategy_id,
                "enabled": strategy.enabled
            }

    raise HTTPException(status_code=404, detail="Strategy not found")


@app.get("/api/platforms", response_model=List[PlatformStatus])
async def get_platform_status():
    """Get status of all connected platforms."""
    # Update timestamps
    for platform in state.platform_status:
        platform.last_update = datetime.utcnow()

    return state.platform_status


@app.get("/api/circuit-breaker", response_model=CircuitBreakerStatus)
async def get_circuit_breaker():
    """Get circuit breaker status."""
    return state.circuit_breaker


@app.get("/api/config")
async def get_config():
    """Get current configuration (non-sensitive)."""
    return {
        "execution": {
            "dry_run": settings.execution.dry_run,
            "debug": settings.execution.debug,
        },
        "risk": {
            "max_capital_usd": settings.risk.max_capital_usd,
            "max_position_per_market": settings.risk.max_position_per_market,
            "max_daily_loss_usd": settings.risk.max_daily_loss_usd,
            "min_profit_threshold": settings.risk.min_profit_threshold,
            "min_liquidity_depth": settings.risk.min_liquidity_depth,
        },
        "performance": {
            "target_daily_profit": settings.performance.target_daily_profit,
            "target_win_rate": settings.performance.target_win_rate,
            "target_latency_ms": settings.performance.target_latency_ms,
        },
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    state.active_connections.append(websocket)

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to ArbMaster Pro WebSocket"
            }
        })

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()

            # Echo back for now (can add more handlers)
            await websocket.send_json({
                "type": "echo",
                "data": data
            })

    except WebSocketDisconnect:
        state.active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)


# ============================================================================
# Server Runner
# ============================================================================

def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    run_api_server(port=port)
