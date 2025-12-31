"""
ArbMaster Pro - Premium Trading Dashboard

Matches the Replit reference design with:
- Persistent sidebar with icon navigation
- Global header with search, live status, notifications
- Key metrics row with sparklines
- Performance chart with gradient
- Live activity feed
- Active strategies cards
"""

import streamlit as st
import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import json

# Configure path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from utils.public_data import PublicDataProvider
except ImportError:
    PublicDataProvider = None
    logger.warning("PublicDataProvider not available")

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="ArbMaster Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# PREMIUM DARK MODE CSS (Matching Replit Reference)
# =============================================================================

PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-card: #111111;
        --bg-card-hover: #161616;
        --border-default: #1a1a1a;
        --border-hover: #2a2a2a;
        --text-primary: #ffffff;
        --text-secondary: #a1a1a1;
        --text-muted: #666666;
        --accent-green: #00ff88;
        --accent-green-dim: rgba(0, 255, 136, 0.1);
        --accent-red: #ff4757;
        --accent-red-dim: rgba(255, 71, 87, 0.1);
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
    }

    /* Global Reset */
    .stApp {
        background: var(--bg-primary) !important;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* ==================== SIDEBAR ==================== */
    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 72px;
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-default);
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px 0;
        z-index: 100;
    }
    
    .sidebar-logo {
        font-size: 1.5rem;
        margin-bottom: 32px;
    }
    
    .nav-item {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 1.25rem;
        color: var(--text-muted);
    }
    
    .nav-item:hover {
        background: var(--bg-card);
        color: var(--text-primary);
    }
    
    .nav-item.active {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    
    .sidebar-bottom {
        margin-top: auto;
    }
    
    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
        font-weight: 600;
        color: white;
    }

    /* ==================== MAIN WRAPPER ==================== */
    .main-wrapper {
        margin-left: 72px;
        min-height: 100vh;
    }

    /* ==================== HEADER ==================== */
    .top-header {
        background: var(--bg-primary);
        border-bottom: 1px solid var(--border-default);
        padding: 16px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .search-box {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 12px;
        padding: 12px 20px;
        width: 360px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .search-icon {
        color: var(--text-muted);
    }
    
    .search-input {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        font-size: 0.875rem;
        flex: 1;
    }
    
    .header-status {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    
    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 8px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-green);
        box-shadow: 0 0 8px var(--accent-green);
    }
    
    .status-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-value {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .notification-btn {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        position: relative;
    }
    
    .notification-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 8px;
        height: 8px;
        background: var(--accent-red);
        border-radius: 50%;
    }

    /* ==================== CONTENT ==================== */
    .content-wrapper {
        padding: 32px;
    }
    
    .page-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    
    .page-subtitle {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin-bottom: 32px;
    }

    /* ==================== METRICS GRID ==================== */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;
        margin-bottom: 32px;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: var(--border-hover);
        background: var(--bg-card-hover);
    }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }
    
    .metric-icon.green {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    
    .metric-icon.red {
        background: var(--accent-red-dim);
        color: var(--accent-red);
    }
    
    .metric-icon.blue {
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-blue);
    }
    
    .metric-icon.purple {
        background: rgba(139, 92, 246, 0.1);
        color: var(--accent-purple);
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    
    .metric-value.positive {
        color: var(--accent-green);
    }
    
    .metric-value.negative {
        color: var(--accent-red);
    }
    
    .metric-change {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
    }
    
    .metric-change.positive {
        color: var(--accent-green);
    }
    
    .metric-change.negative {
        color: var(--accent-red);
    }
    
    .sparkline {
        margin-top: 16px;
        height: 40px;
        background: linear-gradient(180deg, var(--accent-green-dim) 0%, transparent 100%);
        border-radius: 8px;
    }

    /* ==================== MAIN GRID ==================== */
    .main-grid {
        display: grid;
        grid-template-columns: 1fr 380px;
        gap: 24px;
        margin-bottom: 32px;
    }
    
    .chart-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 24px;
    }
    
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    
    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .chart-tabs {
        display: flex;
        gap: 8px;
    }
    
    .chart-tab {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        color: var(--text-muted);
    }
    
    .chart-tab.active {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    
    .chart-area {
        height: 280px;
        background: linear-gradient(180deg, var(--accent-green-dim) 0%, transparent 100%);
        border-radius: 12px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .chart-svg {
        width: 100%;
        height: 100%;
    }

    /* ==================== ACTIVITY FEED ==================== */
    .activity-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 24px;
        max-height: 360px;
        overflow-y: auto;
    }
    
    .activity-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .activity-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .live-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: var(--accent-red-dim);
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--accent-red);
        text-transform: uppercase;
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        background: var(--accent-red);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .activity-item {
        display: flex;
        gap: 16px;
        padding: 16px 0;
        border-bottom: 1px solid var(--border-default);
    }
    
    .activity-item:last-child {
        border-bottom: none;
    }
    
    .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .activity-icon.buy {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    
    .activity-icon.sell {
        background: var(--accent-red-dim);
        color: var(--accent-red);
    }
    
    .activity-content {
        flex: 1;
    }
    
    .activity-text {
        font-size: 0.875rem;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    
    .activity-meta {
        display: flex;
        gap: 12px;
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    
    .activity-profit {
        color: var(--accent-green);
        font-weight: 600;
    }

    /* ==================== STRATEGIES GRID ==================== */
    .strategies-section {
        margin-top: 32px;
    }
    
    .strategies-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .strategies-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .strategies-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
    }
    
    .strategy-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.2s ease;
    }
    
    .strategy-card:hover {
        border-color: var(--accent-green);
        box-shadow: 0 0 24px var(--accent-green-dim);
    }
    
    .strategy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    
    .strategy-name {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .strategy-toggle {
        width: 44px;
        height: 24px;
        background: var(--accent-green);
        border-radius: 12px;
        position: relative;
        cursor: pointer;
    }
    
    .strategy-toggle::after {
        content: '';
        position: absolute;
        top: 2px;
        right: 2px;
        width: 20px;
        height: 20px;
        background: white;
        border-radius: 50%;
    }
    
    .strategy-toggle.off {
        background: var(--border-hover);
    }
    
    .strategy-toggle.off::after {
        right: auto;
        left: 2px;
    }
    
    .strategy-market {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 16px;
    }
    
    .strategy-stats {
        display: flex;
        gap: 16px;
    }
    
    .strategy-stat {
        flex: 1;
    }
    
    .strategy-stat-label {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .strategy-stat-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .strategy-stat-value.positive {
        color: var(--accent-green);
    }

    /* ==================== STREAMLIT OVERRIDES ==================== */
    div[data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }
    
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        color: var(--text-primary) !important;
    }
    
    .stButton > button:hover {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 16px var(--accent-green-dim) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 10px !important;
    }
</style>
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    """Initialize session state."""
    defaults = {
        "current_page": "dashboard",
        "scanner_running": True,
        "opportunities": [],
        "trades": [],
        "last_update": None,
        "metrics": {
            "total_profit": 2847.32,
            "active_capital": 15000.00,
            "daily_roi": 3.2,
            "win_rate": 87
        },
        "strategies": [
            {"name": "Cross-Exchange Arb", "market": "Polymarket ↔ Kalshi", "active": True, "roi": 2.4, "risk": "Low", "freq": "12/hr"},
            {"name": "Binary Complement", "market": "Single Market Spreads", "active": True, "roi": 1.8, "risk": "Med", "freq": "8/hr"},
            {"name": "Contextual Arb", "market": "News-Driven Markets", "active": False, "roi": 4.1, "risk": "High", "freq": "3/hr"},
        ],
        "activities": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# =============================================================================
# DATA FETCHING
# =============================================================================

async def fetch_live_data():
    """Fetch live opportunities from APIs."""
    if PublicDataProvider:
        try:
            return await PublicDataProvider.get_live_opportunities()
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
    return []

def get_opportunities():
    """Sync wrapper for fetching opportunities."""
    try:
        return asyncio.run(fetch_live_data())
    except:
        return []

def generate_activities():
    """Generate sample activity feed."""
    activities = [
        {"type": "buy", "text": "Bought YES on 'Bitcoin above $100k'", "profit": "+$12.40", "time": "2s ago"},
        {"type": "sell", "text": "Closed Kalshi position", "profit": "+$8.20", "time": "15s ago"},
        {"type": "buy", "text": "Arbitrage on ETH markets", "profit": "+$24.80", "time": "32s ago"},
        {"type": "buy", "text": "Cross-platform spread capture", "profit": "+$6.50", "time": "1m ago"},
        {"type": "sell", "text": "Exited low-confidence trade", "profit": "-$2.10", "time": "2m ago"},
    ]
    return activities

# =============================================================================
# COMPONENTS
# =============================================================================

def render_sidebar():
    """Render the sidebar navigation."""
    st.markdown("""
    <div class="sidebar">
        <div class="sidebar-logo">📈</div>
        <div class="nav-item active" title="Dashboard">🏠</div>
        <div class="nav-item" title="Strategies">🎯</div>
        <div class="nav-item" title="Analytics">📊</div>
        <div class="nav-item" title="Wallet">💰</div>
        <div class="nav-item" title="Risk">⚠️</div>
        <div class="nav-item" title="Settings">⚙️</div>
        <div class="sidebar-bottom">
            <div class="user-avatar">J</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """Render the top header."""
    st.markdown("""
    <div class="top-header">
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <span style="color: #666; font-size: 0.875rem;">Search markets, strategies...</span>
        </div>
        <div class="header-status">
            <div class="status-item">
                <div class="status-dot"></div>
                <div>
                    <div class="status-label">System</div>
                    <div class="status-value">Online</div>
                </div>
            </div>
            <div class="status-item">
                <div>
                    <div class="status-label">ETH</div>
                    <div class="status-value">$3,420</div>
                </div>
            </div>
            <div class="status-item">
                <div>
                    <div class="status-label">Gas</div>
                    <div class="status-value">12 gwei</div>
                </div>
            </div>
            <div class="notification-btn">
                🔔
                <div class="notification-badge"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metrics():
    """Render the metrics grid."""
    m = st.session_state.metrics
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Net Profit",
            f"${m['total_profit']:,.2f}",
            "+12.5% from yesterday"
        )
    
    with col2:
        st.metric(
            "Active Capital",
            f"${m['active_capital']:,.2f}",
            "+$2,500 deployed"
        )
    
    with col3:
        st.metric(
            "Daily ROI",
            f"{m['daily_roi']}%",
            "+0.8% vs 7d avg"
        )
    
    with col4:
        st.metric(
            "Win Rate",
            f"{m['win_rate']}%",
            "Last 24 trades"
        )

def render_chart():
    """Render the performance chart."""
    st.markdown("""
    <div class="chart-card">
        <div class="chart-header">
            <div class="chart-title">Performance Overview</div>
            <div class="chart-tabs">
                <div class="chart-tab active">24H</div>
                <div class="chart-tab">7D</div>
                <div class="chart-tab">30D</div>
                <div class="chart-tab">ALL</div>
            </div>
        </div>
        <div class="chart-area">
            <svg class="chart-svg" viewBox="0 0 400 150" preserveAspectRatio="none">
                <defs>
                    <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#00ff88;stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:#00ff88;stop-opacity:0" />
                    </linearGradient>
                </defs>
                <path d="M0,120 L50,100 L100,110 L150,70 L200,80 L250,50 L300,60 L350,30 L400,40 L400,150 L0,150 Z" fill="url(#chartGradient)" />
                <path d="M0,120 L50,100 L100,110 L150,70 L200,80 L250,50 L300,60 L350,30 L400,40" stroke="#00ff88" stroke-width="2" fill="none" />
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_activity_feed():
    """Render the live activity feed."""
    activities = generate_activities()
    
    activity_html = ""
    for act in activities:
        icon_class = "buy" if act["type"] == "buy" else "sell"
        icon = "📈" if act["type"] == "buy" else "📉"
        profit_class = "" if act["profit"].startswith("+") else "style='color: #ff4757;'"
        
        activity_html += f"""
        <div class="activity-item">
            <div class="activity-icon {icon_class}">{icon}</div>
            <div class="activity-content">
                <div class="activity-text">{act["text"]}</div>
                <div class="activity-meta">
                    <span class="activity-profit" {profit_class}>{act["profit"]}</span>
                    <span>{act["time"]}</span>
                </div>
            </div>
        </div>
        """
    
    st.markdown(f"""
    <div class="activity-card">
        <div class="activity-header">
            <div class="activity-title">Live Activity</div>
            <div class="live-badge">
                <div class="live-dot"></div>
                LIVE
            </div>
        </div>
        {activity_html}
    </div>
    """, unsafe_allow_html=True)

def render_strategies():
    """Render the strategies section."""
    strategies = st.session_state.strategies
    
    st.markdown("### Active Strategies")
    
    cols = st.columns(3)
    for i, strategy in enumerate(strategies):
        with cols[i]:
            toggle_class = "" if strategy["active"] else "off"
            roi_class = "positive" if strategy["roi"] > 0 else ""
            status = "Running" if strategy["active"] else "Paused"
            
            st.markdown(f"""
            <div class="strategy-card">
                <div class="strategy-header">
                    <div class="strategy-name">{strategy["name"]}</div>
                    <div class="strategy-toggle {toggle_class}"></div>
                </div>
                <div class="strategy-market">{strategy["market"]}</div>
                <div class="strategy-stats">
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">EXP. ROI</div>
                        <div class="strategy-stat-value {roi_class}">{strategy["roi"]}%</div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">Risk</div>
                        <div class="strategy-stat-value">{strategy["risk"]}</div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">Freq</div>
                        <div class="strategy-stat-value">{strategy["freq"]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_opportunities_section():
    """Render opportunities section with live data."""
    st.markdown("### 🎯 Live Opportunities")
    
    # Fetch data if needed
    if not st.session_state.opportunities:
        with st.spinner("Fetching live market data..."):
            st.session_state.opportunities = get_opportunities()
            st.session_state.last_update = datetime.now()
    
    opportunities = st.session_state.opportunities
    
    if not opportunities:
        st.info("No opportunities found. Scanner is searching...")
        return
    
    # Sort by profit
    sorted_opps = sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)[:6]
    
    cols = st.columns(3)
    for i, opp in enumerate(sorted_opps):
        with cols[i % 3]:
            platform = opp.get('platforms', ['Unknown'])[0]
            spread = opp.get('profit_pct', 0)
            title = opp.get('title', 'Untitled')[:35]
            confidence = opp.get('confidence', 0.5) * 100
            
            spread_class = "positive" if spread > 0 else ""
            
            st.markdown(f"""
            <div class="strategy-card">
                <div class="strategy-header">
                    <div class="strategy-name">{title}...</div>
                </div>
                <div class="strategy-market">📍 {platform}</div>
                <div class="strategy-stats">
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">Spread</div>
                        <div class="strategy-stat-value {spread_class}">{spread:.2f}%</div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat-label">Confidence</div>
                        <div class="strategy-stat-value">{confidence:.0f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application."""
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
    init_session_state()
    
    # Sidebar (HTML)
    render_sidebar()
    
    # Main content wrapper
    st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)
    
    # Header
    render_header()
    
    # Content
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Page title
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Real-time arbitrage monitoring and execution</div>', unsafe_allow_html=True)
    
    # Metrics row
    render_metrics()
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Main grid: Chart + Activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_chart()
    
    with col2:
        render_activity_feed()
    
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    
    # Strategies section
    render_strategies()
    
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    
    # Opportunities section
    render_opportunities_section()
    
    # Refresh button
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Live Data", use_container_width=True):
            st.session_state.opportunities = get_opportunities()
            st.session_state.last_update = datetime.now()
            st.toast("Data refreshed!", icon="✅")
            st.rerun()
    
    # Close wrappers
    st.markdown('</div></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
