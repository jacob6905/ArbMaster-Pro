"""
ArbMaster Pro - Main Application Entry Point

Universal Arbitrage Trading Platform for prediction markets,
cryptocurrency exchanges, and DeFi protocols.

Target: $500+ daily profit through risk-neutral strategies
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
import click
from loguru import logger

from config import settings
from arbitrage.detector import ArbitrageDetector
from arbitrage.evaluator import OpportunityEvaluator
from execution.engine import ExecutionEngine
from risk.manager import RiskManager
from models.opportunity import ArbitrageOpportunity


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.execution.debug else "INFO",
)
logger.add(
    "logs/arbmaster_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
)


class ArbMasterPro:
    """
    Main ArbMaster Pro application.

    Orchestrates:
    - Arbitrage detection across multiple platforms
    - Opportunity evaluation and filtering
    - Trade execution with risk management
    - Real-time monitoring and alerts
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

        # Components
        self.detector: Optional[ArbitrageDetector] = None
        self.evaluator: Optional[OpportunityEvaluator] = None
        self.executor: Optional[ExecutionEngine] = None
        self.risk_manager: Optional[RiskManager] = None

        # State
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"ArbMaster Pro initialized "
            f"(mode: {'DRY RUN' if dry_run else 'LIVE'})"
        )

    async def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing ArbMaster Pro...")

        try:
            # Initialize risk manager first
            self.risk_manager = RiskManager()
            logger.info("Risk manager initialized")

            # Initialize detector (connects to platforms)
            self.detector = ArbitrageDetector(
                dry_run=self.dry_run,
                min_profit_threshold=settings.risk.min_profit_threshold,
                min_liquidity=settings.risk.min_liquidity_depth,
            )

            if not await self.detector.initialize():
                logger.error("Failed to initialize detector")
                return False

            # Initialize evaluator
            self.evaluator = OpportunityEvaluator(
                min_score=0.5,
            )
            logger.info("Evaluator initialized")

            # Initialize executor with platform clients
            self.executor = ExecutionEngine(
                platforms={
                    "polymarket": self.detector.polymarket,
                    "kalshi": self.detector.kalshi,
                    **self.detector.cex_clients,
                },
                risk_manager=self.risk_manager,
                dry_run=self.dry_run,
            )
            logger.info("Execution engine initialized")

            # Set up callbacks
            self.detector.set_opportunity_callback(self._on_opportunity)
            self.executor.set_callbacks(
                on_start=self._on_trade_start,
                on_complete=self._on_trade_complete,
            )

            logger.info("ArbMaster Pro fully initialized")
            return True

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    async def run(self) -> None:
        """Main run loop."""
        if not await self.initialize():
            logger.error("Failed to initialize, exiting")
            return

        self._running = True
        logger.info("Starting ArbMaster Pro main loop...")

        # Set up signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(
                sig, lambda: asyncio.create_task(self.shutdown())
            )

        try:
            # Start detection loop
            detection_task = asyncio.create_task(
                self.detector.start_scanning()
            )

            # Wait for shutdown
            await self._shutdown_event.wait()

            # Clean up
            self.detector.stop_scanning()
            await detection_task

        except asyncio.CancelledError:
            logger.info("Main loop cancelled")

        finally:
            await self.cleanup()

    async def shutdown(self) -> None:
        """Initiate graceful shutdown."""
        logger.info("Shutdown requested...")
        self._running = False
        self._shutdown_event.set()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up...")

        if self.detector:
            await self.detector.shutdown()

        logger.info("Cleanup complete")

    async def _on_opportunity(self, opportunity: ArbitrageOpportunity) -> None:
        """Handle detected opportunity."""
        # Evaluate the opportunity
        evaluation = self.evaluator.evaluate(opportunity)

        logger.info(
            f"Opportunity detected: {opportunity.arb_type.value} "
            f"(score: {evaluation['total_score']:.2f}, "
            f"profit: {evaluation['expected_profit_pct']:.2f}%)"
        )

        # Check if we should execute
        if evaluation["recommendation"] in ("STRONG_BUY", "BUY"):
            if not self.risk_manager.can_trade:
                logger.warning("Trading halted by risk manager")
                return

            # Execute the trade
            result = await self.executor.execute(opportunity)

            if result.success:
                logger.info(
                    f"Trade executed successfully! "
                    f"Profit: ${result.profit_usd:.2f}"
                )
            else:
                logger.warning(f"Trade failed: {result.error}")

        elif evaluation["recommendation"] == "CONSIDER":
            logger.debug(f"Opportunity below threshold: {evaluation['reasoning']}")

        else:
            logger.debug(f"Skipping opportunity: {evaluation['reasoning']}")

    async def _on_trade_start(self, trade) -> None:
        """Handle trade start."""
        logger.debug(f"Trade {trade.trade_id} started")

    async def _on_trade_complete(self, trade, result) -> None:
        """Handle trade completion."""
        status = "SUCCESS" if result.success else "FAILED"
        logger.info(
            f"Trade {trade.trade_id} completed: {status} "
            f"(profit: ${result.profit_usd:.2f}, latency: {result.execution_time_ms}ms)"
        )

    def get_stats(self) -> dict:
        """Get current statistics."""
        stats = {
            "running": self._running,
            "mode": "dry_run" if self.dry_run else "live",
            "started_at": datetime.utcnow().isoformat(),
        }

        if self.detector:
            stats["detector"] = self.detector.stats

        if self.executor:
            stats["executor"] = self.executor.stats

        if self.risk_manager:
            metrics = self.risk_manager.get_metrics()
            stats["risk"] = {
                "can_trade": self.risk_manager.can_trade,
                "risk_level": metrics.risk_level.value,
                "daily_pnl": float(metrics.realized_pnl_today),
                "trades_today": metrics.trades_today,
                "win_rate": metrics.win_rate,
            }

        return stats


@click.group()
def cli():
    """ArbMaster Pro - Universal Arbitrage Trading Platform"""
    pass


@cli.command()
@click.option("--dry-run/--live", default=True, help="Run in dry-run or live mode")
def run(dry_run: bool):
    """Start the ArbMaster Pro trading bot."""
    click.echo(f"Starting ArbMaster Pro in {'DRY RUN' if dry_run else 'LIVE'} mode...")

    if not dry_run:
        click.confirm(
            "⚠️  LIVE mode will execute real trades. Are you sure?",
            abort=True,
        )

    app = ArbMasterPro(dry_run=dry_run)
    asyncio.run(app.run())


@cli.command()
def scan():
    """Run a single scan for arbitrage opportunities."""
    click.echo("Running single scan...")

    async def single_scan():
        detector = ArbitrageDetector(dry_run=True)
        await detector.initialize()

        opportunities = await detector.scan_once()

        if opportunities:
            click.echo(f"\nFound {len(opportunities)} opportunities:\n")
            for opp in opportunities:
                click.echo(
                    f"  - {opp.arb_type.value}: "
                    f"{opp.net_profit_pct:.2%} profit, "
                    f"${opp.estimated_profit_usd:.2f}"
                )
        else:
            click.echo("No opportunities found")

        await detector.shutdown()

    asyncio.run(single_scan())


@cli.command()
def status():
    """Show current system status."""
    click.echo("\n=== ArbMaster Pro Status ===\n")

    # Check configuration
    click.echo("Configuration:")
    click.echo(f"  Mode: {'DRY RUN' if settings.execution.dry_run else 'LIVE'}")
    click.echo(f"  Max Capital: ${settings.risk.max_capital_usd:,.0f}")
    click.echo(f"  Min Profit: {settings.risk.min_profit_threshold:.1%}")
    click.echo(f"  Daily Loss Limit: ${settings.risk.max_daily_loss_usd:,.0f}")

    click.echo("\nPlatform Credentials:")
    click.echo(f"  Polymarket: {'✓' if settings.polymarket.api_key else '✗'}")
    click.echo(f"  Kalshi: {'✓' if settings.kalshi.email else '✗'}")
    click.echo(f"  Binance: {'✓' if settings.exchanges.binance_api_key else '✗'}")

    click.echo("\nPerformance Targets:")
    click.echo(f"  Daily Profit: ${settings.performance.target_daily_profit:,.0f}")
    click.echo(f"  Win Rate: {settings.performance.target_win_rate:.0%}")
    click.echo(f"  Max Latency: {settings.performance.target_latency_ms}ms")


@cli.command()
def dashboard():
    """Launch the Streamlit monitoring dashboard."""
    import subprocess
    import os

    dashboard_path = os.path.join(
        os.path.dirname(__file__), "..", "dashboard", "app.py"
    )

    click.echo("Starting dashboard...")
    subprocess.run(
        ["streamlit", "run", dashboard_path, "--server.port", str(settings.server.dashboard_port)],
        check=True,
    )


@cli.command()
@click.option("--port", default=8000, help="Port to run API server on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def api(port: int, host: str):
    """Start the API server for health checks and monitoring."""
    import os

    # Allow PORT env var to override (for Railway)
    port = int(os.environ.get("PORT", port))

    click.echo(f"Starting API server on {host}:{port}...")

    from api import run_api_server
    run_api_server(host=host, port=port)


@cli.command()
@click.option("--dry-run/--live", default=True, help="Run in dry-run or live mode")
@click.option("--with-api", is_flag=True, help="Also start the API server")
@click.option("--api-port", default=8000, help="API server port")
def start(dry_run: bool, with_api: bool, api_port: int):
    """Start the bot with optional API server (recommended for Railway)."""
    import os
    import threading

    # Allow PORT env var to override
    api_port = int(os.environ.get("PORT", api_port))

    click.echo(f"Starting ArbMaster Pro in {'DRY RUN' if dry_run else 'LIVE'} mode...")

    if not dry_run:
        click.confirm(
            "⚠️  LIVE mode will execute real trades. Are you sure?",
            abort=True,
        )

    # Start API server in background thread if requested
    if with_api:
        click.echo(f"Starting API server on port {api_port}...")
        from api import run_api_server
        api_thread = threading.Thread(
            target=run_api_server,
            kwargs={"host": "0.0.0.0", "port": api_port},
            daemon=True
        )
        api_thread.start()

    # Start the main bot
    app = ArbMasterPro(dry_run=dry_run)
    asyncio.run(app.run())


if __name__ == "__main__":
    cli()
