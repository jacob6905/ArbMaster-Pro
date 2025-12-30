"""
ArbMaster Pro - FastAPI Health Check and API Server

Provides health check endpoints and API access for monitoring.
"""

import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import settings


# Global state for tracking bot status
class BotState:
    running: bool = False
    started_at: Optional[datetime] = None
    last_scan: Optional[datetime] = None
    opportunities_found: int = 0
    trades_executed: int = 0
    total_profit: float = 0.0
    errors: list = []


bot_state = BotState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    bot_state.started_at = datetime.utcnow()
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="ArbMaster Pro API",
    description="Universal Arbitrage Trading Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    mode: str
    version: str = "0.1.0"


class StatsResponse(BaseModel):
    running: bool
    mode: str
    started_at: Optional[str]
    last_scan: Optional[str]
    opportunities_found: int
    trades_executed: int
    total_profit: float
    config: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway."""
    uptime = 0.0
    if bot_state.started_at:
        uptime = (datetime.utcnow() - bot_state.started_at).total_seconds()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=uptime,
        mode="dry_run" if settings.execution.dry_run else "live",
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ArbMaster Pro",
        "description": "Universal Arbitrage Trading Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get current bot statistics."""
    return StatsResponse(
        running=bot_state.running,
        mode="dry_run" if settings.execution.dry_run else "live",
        started_at=bot_state.started_at.isoformat() if bot_state.started_at else None,
        last_scan=bot_state.last_scan.isoformat() if bot_state.last_scan else None,
        opportunities_found=bot_state.opportunities_found,
        trades_executed=bot_state.trades_executed,
        total_profit=bot_state.total_profit,
        config={
            "max_capital": settings.risk.max_capital_usd,
            "min_profit_threshold": settings.risk.min_profit_threshold,
            "max_daily_loss": settings.risk.max_daily_loss_usd,
            "target_daily_profit": settings.performance.target_daily_profit,
        },
    )


@app.get("/config")
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


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    run_api_server(port=port)
