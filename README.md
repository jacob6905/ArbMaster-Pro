# ArbMaster Pro

**Universal Arbitrage Trading Platform for Prediction Markets, Cryptocurrency Exchanges, and DeFi Protocols**

Target: $500+ daily profit through risk-neutral strategies

## Overview

ArbMaster Pro is a sophisticated automated arbitrage system designed to exploit price discrepancies and inefficiencies across prediction markets (Polymarket, Kalshi), cryptocurrency exchanges (Binance, KuCoin, OKX), and DeFi protocols (Uniswap, SushiSwap, Aave).

## Core Features

### Trading Strategies

- **Binary Complement Arbitrage** (YES + NO < $1): Buy both sides when combined cost is under $1.00 for guaranteed profit
- **Cross-Platform Arbitrage**: Exploit pricing gaps between Polymarket and Kalshi
- **Multi-Outcome Bundle Arbitrage**: Buy all outcomes when sum is under $1.00
- **DEX-CEX Price Gaps**: Capitalize on price differences between decentralized and centralized exchanges
- **Funding Rate Arbitrage**: Spot-futures hedging to capture funding rate yield
- **Tail-End Trading**: Near-settlement trading when outcomes are nearly certain

### Key Capabilities

- **High-Frequency Scanning**: Target <500ms detection-to-execution latency
- **Real-Time WebSocket Feeds**: Live order book monitoring
- **AI-Powered Decision Making**: Integration with Claude 3.5 and Gemini for contextual risk assessment
- **Dry-Run Mode**: Paper trading for strategy validation
- **Comprehensive Risk Management**: Circuit breakers, liquidity checks, position sizing
- **Streamlit Dashboard**: Real-time monitoring and control

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Blockchain**: Web3.py for DeFi interactions
- **Exchange Integration**: CCXT for CEX connectivity
- **Prediction Markets**: py-clob-client for Polymarket, custom Kalshi client
- **Dashboard**: Streamlit with Plotly visualizations
- **Database**: SQLAlchemy with async support

## Project Structure

```
ArbMaster-Pro/
├── src/
│   ├── arbitrage/          # Arbitrage detection and scanning
│   │   ├── detector.py     # Main detection orchestrator
│   │   ├── scanner.py      # Individual strategy scanners
│   │   └── evaluator.py    # Opportunity evaluation
│   ├── platforms/          # Platform integrations
│   │   ├── polymarket.py   # Polymarket CLOB client
│   │   ├── kalshi.py       # Kalshi API client
│   │   ├── cex.py          # CEX integration (CCXT)
│   │   └── dex.py          # DEX integration (Web3)
│   ├── execution/          # Trade execution
│   │   ├── engine.py       # Execution orchestrator
│   │   └── executor.py     # Low-level execution
│   ├── risk/               # Risk management
│   │   ├── manager.py      # Central risk manager
│   │   ├── circuit_breaker.py
│   │   └── position_sizer.py
│   ├── models/             # Data models
│   │   ├── opportunity.py  # Arbitrage opportunity models
│   │   ├── market.py       # Market data models
│   │   ├── trade.py        # Trade models
│   │   └── risk.py         # Risk metric models
│   ├── config.py           # Configuration management
│   └── main.py             # Application entry point
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ArbMaster-Pro.git
cd ArbMaster-Pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required for live trading:
# - POLYMARKET_PRIVATE_KEY
# - WALLET_PRIVATE_KEY
# Optional for expanded features:
# - KALSHI_EMAIL / KALSHI_PASSWORD
# - BINANCE_API_KEY / BINANCE_API_SECRET
```

### 3. Run in Dry-Run Mode

```bash
# Start the bot in paper trading mode
python src/main.py run --dry-run

# Or run a single scan
python src/main.py scan

# Launch the monitoring dashboard
python src/main.py dashboard
```

### 4. Live Trading (Caution!)

```bash
# Start live trading (requires confirmation)
python src/main.py run --live
```

## Risk Management

ArbMaster Pro includes comprehensive risk controls:

- **Circuit Breakers**: Auto-halt on daily loss, consecutive errors, or high volatility
- **Position Limits**: Max capital per market, max total positions
- **Liquidity Checks**: Minimum $10k depth requirement
- **Slippage Control**: Maximum slippage thresholds
- **Kelly Criterion**: Optimal position sizing

### Default Risk Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Max Capital | $50,000 | Maximum total trading capital |
| Max Position/Market | $5,000 | Maximum per single market |
| Min Profit Threshold | 1% | Minimum profit to execute |
| Max Daily Loss | $500 | Circuit breaker trigger |
| Min Liquidity | $10,000 | Required order book depth |

## Performance Targets

- **Daily Profit**: $500+
- **Win Rate**: 90%+
- **Detection Latency**: <500ms
- **Monthly ROI**: 3-15%

## Supported Platforms

### Prediction Markets
- Polymarket (CLOB on Polygon)
- Kalshi (Regulated US market)

### Centralized Exchanges
- Binance
- KuCoin
- OKX
- Bybit

### Decentralized Exchanges
- Uniswap V2/V3
- SushiSwap
- QuickSwap (Polygon)

## Disclaimer

**This software is for educational purposes only.** Trading involves substantial risk of loss. Past performance does not guarantee future results. Always:

1. Start with dry-run mode to validate strategies
2. Use only capital you can afford to lose
3. Understand the risks of automated trading
4. Comply with all applicable laws and regulations
5. Never trade with borrowed money

## License

MIT License - See LICENSE file for details
