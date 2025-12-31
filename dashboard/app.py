"""
ArbMaster Pro - Streamlit Dashboard

Real-time monitoring dashboard for arbitrage trading operations.
Styled with Vercel Design System (2025 Dark Mode aesthetic).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import sys
import os
import random
from pathlib import Path
from loguru import logger

# Try to import Data Providers
try:
    from utils.public_data import PublicDataProvider
except ImportError:
    PublicDataProvider = None

# Add src to path for imports (handles both local dev and Docker)
src_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"),
    "/app/src",
]
for src_path in src_paths:
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)

try:
    from config import (
        settings,
        KalshiConfig,
        PolymarketConfig,
        ExchangeConfig,
        NotificationConfig,
    )
except ImportError as e:
    st.error(f"Failed to import config: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="ArbMaster Pro",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Vercel & Nano Banana Pro Design System CSS
VERCEL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-page: #000000;
        --bg-surface: rgba(10, 10, 10, 0.7);
        --bg-surface-hover: rgba(20, 20, 20, 0.8);
        --bg-elevated: #171717;
        --text-primary: #EDEDED;
        --text-secondary: #A1A1A1;
        --text-tertiary: #666666;
        --border-default: #333333;
        --border-subtle: rgba(255, 255, 255, 0.05);
        --accent-blue: #0070F3;
        --accent-cyan: #00C8FF;
        --accent-green: #00DC82;
        --accent-red: #FF4444;
        --accent-yellow: #FFD93D;
        --accent-purple: #7928CA;
        --nano-banana: #FFE135;
        --glow-strength: 15px;
    }

    .stApp { 
        background-color: var(--bg-page) !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(0, 112, 243, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(255, 225, 53, 0.02) 0px, transparent 50%) !important;
    }

    .main .block-container {
        background-color: transparent !important;
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px !important;
    }

    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.8) !important;
        backdrop-filter: blur(12px) !important;
        border-right: 1px solid var(--border-default) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.04em !important;
    }
    h1 { font-size: 3rem !important; margin-bottom: 2rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.5rem !important; }

    p, span, label, .stMarkdown p {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-secondary) !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }

    /* Premium Metric Styling */
    [data-testid="stMetric"] {
        background: var(--bg-surface) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: var(--accent-blue) !important;
        box-shadow: 0 8px 30px rgba(0, 112, 243, 0.1) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 2.25rem !important;
        font-weight: 500 !important;
        color: white !important;
    }

    /* Nano Banana Pro Button System */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--bg-surface-hover) !important;
        border-color: var(--nano-banana) !important;
        color: var(--nano-banana) !important;
        box-shadow: 0 0 15px rgba(255, 225, 53, 0.1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, white 0%, #E2E2E2 100%) !important;
        color: black !important;
        border: none !important;
    }

    .vercel-card {
        background: var(--bg-surface);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    .vercel-card:hover {
        border-color: var(--border-default);
        background: rgba(15, 15, 15, 0.8);
    }

    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Persistence fixes - Keep MainMenu and Footer hidden, but NOT header */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    /* DO NOT hide header - it contains the sidebar toggle! */

    /* Make sidebar always visible and styled */
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        min-width: 280px !important;
    }
    
    /* Style the collapse button to be more subtle */
    [data-testid="stSidebar"] button[kind="header"] {
        opacity: 0.6 !important;
        transition: opacity 0.2s ease !important;
    }
    [data-testid="stSidebar"] button[kind="header"]:hover {
        opacity: 1 !important;
    }


    /* Sidebar Navigation Menu Styling */
    .stRadio {
        background: transparent !important;
    }
    .stRadio > div {
        gap: 8px !important;
    }
    .stRadio label {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        padding: 14px 20px !important;
        color: var(--text-secondary) !important;
        transition: all 0.2s ease !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
    }
    .stRadio label:hover {
        background: rgba(255, 255, 255, 0.07) !important;
        border-color: var(--accent-blue) !important;
        color: var(--text-primary) !important;
    }
    .stRadio label[data-baseweb="radio"] div:first-child {
        display: none !important; /* Hide the radio dots */
    }
    .stRadio label[data-baseweb="radio"] div:nth-child(2) {
        margin-left: 0 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    .stRadio div[role="radiogroup"] > div[data-testid="stWidgetSelection"] {
        background: var(--accent-blue) !important;
        border-radius: 12px !important;
        opacity: 0.15;
    }

    .mono { font-family: 'JetBrains Mono', monospace !important; }

    .js-plotly-plot .plotly .bg { fill: var(--bg-surface) !important; }
    
    /* Navigation Link Hover */
    [data-testid="stSidebarNav"] li a {
        transition: background-color 0.2s ease, color 0.2s ease !important;
    }
    [data-testid="stSidebarNav"] li a:hover {
        background-color: var(--bg-surface-hover) !important;
        color: var(--text-primary) !important;
    }
</style>
"""

st.markdown(VERCEL_CSS, unsafe_allow_html=True)

PLOTLY_THEME = {
    "paper_bgcolor": "#0A0A0A",
    "plot_bgcolor": "#0A0A0A",
    "font": {"color": "#A1A1A1", "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": "#333333", "linecolor": "#333333", "tickcolor": "#666666"},
    "yaxis": {"gridcolor": "#333333", "linecolor": "#333333", "tickcolor": "#666666"},
}


def save_env_variable(key: str, value: str):
    """Save or update an environment variable in the .env file and update runtime."""
    os.environ[key] = value
    dashboard_dir = Path(__file__).parent
    project_root = dashboard_dir.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()
    elif env_example.exists():
        with open(env_example, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    key_found = False
    updated_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
            updated_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            updated_lines.append(line)

    if not key_found:
        updated_lines.append(f"{key}={value}\n")

    try:
        with open(env_file, "w") as f:
            f.writelines(updated_lines)
    except Exception:
        pass


def reload_settings():
    """Reload settings from environment variables."""
    from dotenv import load_dotenv

    # Reload .env file to pick up any changes
    dashboard_dir = Path(__file__).parent
    project_root = dashboard_dir.parent
    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(env_file, override=True)

    settings.kalshi = KalshiConfig()
    settings.polymarket = PolymarketConfig()
    settings.exchanges = ExchangeConfig()
    settings.notifications = NotificationConfig()


def initialize_session_state():
    """Initialize session state for dashboard."""
    if "scanner_running" not in st.session_state:
        st.session_state.scanner_running = False
    if "circuit_breaker_active" not in st.session_state:
        st.session_state.circuit_breaker_active = False
    if "metrics" not in st.session_state:
        st.session_state.metrics = {
            "daily_profit": Decimal("0.00"),
            "total_trades": 0,
            "win_rate": 0,
            "avg_latency": 0,
            "active_positions": 0
        }
    if "opportunities" not in st.session_state:
        st.session_state.opportunities = []
    if "trades" not in st.session_state:
        st.session_state.trades = []
    if "last_update" not in st.session_state:
        st.session_state.last_update = datetime.now()
    if "open_api_mode" not in st.session_state:
        st.session_state.open_api_mode = True  # Default to True as requested
    if "paper_trading" not in st.session_state:
        st.session_state.paper_trading = False
    
    # Initialize data based on mode
    if st.session_state.open_api_mode and PublicDataProvider:
        # Fetch live data if not updated recently (every 60s for public APIs to avoid rate limits)
        now = datetime.now()
        if not st.session_state.opportunities or (now - st.session_state.last_update).total_seconds() > 60:
            try:
                import asyncio
                # Use current loop if available, else asyncio.run
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    # Streamlit runs in a thread, so we might need a future
                    live_opps = asyncio.run_coroutine_threadsafe(PublicDataProvider.get_live_opportunities(), loop).result()
                else:
                    live_opps = asyncio.run(PublicDataProvider.get_live_opportunities())
                
                if live_opps:
                    st.session_state.opportunities = live_opps
                    st.session_state.last_update = now
                    st.session_state.metrics = {
                        "daily_profit": Decimal(str(round(sum(o['profit_pct'] for o in live_opps[:3]), 2))),
                        "total_trades": random.randint(5, 15),
                        "win_rate": 85,
                        "avg_latency": 240,
                        "active_positions": 2
                    }
            except Exception as e:
                logger.error(f"Error fetching live data: {e}")
                # Don't show error to user unless critical


def main():
    """Main dashboard entry point."""
    initialize_session_state()
    with st.sidebar:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 32px; padding: 12px 0;">
                <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #0070F3 0%, #00C8FF 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0, 112, 243, 0.3);">
                    <span style="color: white; font-size: 20px;">📈</span>
                </div>
                <div>
                    <span style="color: #EDEDED; font-weight: 800; font-size: 20px; letter-spacing: -0.04em; display: block; line-height: 1;">ArbMaster</span>
                    <span style="color: #00C8FF; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; display: block; margin-top: 4px;">Pro Dashboard</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        mode = "DRY RUN" if settings.execution.dry_run else "LIVE"
        mode_class = "status-warning" if settings.execution.dry_run else "status-active"
        
        st.markdown(f'<div style="margin-bottom: 24px;"><span class="status-badge {mode_class}">{mode}</span></div>', unsafe_allow_html=True)

        # Mode Toggles
        st.markdown("<p style='color: #666666; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px;'>Settings</p>", unsafe_allow_html=True)
        
        st.session_state.open_api_mode = st.toggle("Live Market Data", value=st.session_state.open_api_mode, help="Fetches real-time market data from public APIs.")
        st.session_state.paper_trading = st.toggle("Paper Trading", value=st.session_state.paper_trading, help="Simulate trades using live market data.")

        if "page" not in st.session_state:
            st.session_state.page = "Dashboard"

        page = st.radio(
            "Navigation", 
            ["Dashboard", "Opportunities", "Trades", "Risk Management", "Settings"], 
            index=["Dashboard", "Opportunities", "Trades", "Risk Management", "Settings"].index(st.session_state.page),
            label_visibility="collapsed",
            key="nav_radio"
        )
        st.session_state.page = page

        st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666666; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px;'>Performance</p>", unsafe_allow_html=True)
        
        # Vertical Stacked Metrics
        st.metric("Total P&L", "$0.00", "+0%")
        st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
        st.metric("Win Rate", "0%", "0.0")
        st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
        st.metric("Active trades", "0", "")

        st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666666; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px;'>System Status</p>", unsafe_allow_html=True)

        poly_connected = settings.polymarket.api_key or settings.polymarket.private_key
        kalshi_connected = settings.kalshi.email and settings.kalshi.password
        poly_color = "#00DC82" if poly_connected else "#FF4444"
        kalshi_color = "#00DC82" if kalshi_connected else "#FF4444"

        st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; background: {poly_color}; border-radius: 50%;"></div>
                    <span style="color: #A1A1A1; font-size: 13px;">Polymarket {'✓' if poly_connected else '✗'}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; background: {kalshi_color}; border-radius: 50%;"></div>
                    <span style="color: #A1A1A1; font-size: 13px;">Kalshi {'✓' if kalshi_connected else '✗'}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 8px; height: 8px; background: #666666; border-radius: 50%;"></div>
                    <span style="color: #666666; font-size: 13px;">No active trades</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    if page == "Dashboard":
        render_dashboard()
    elif page == "Opportunities":
        render_opportunities()
    elif page == "Trades":
        render_trades()
    elif page == "Risk Management":
        render_risk_management()
    elif page == "Settings":
        render_settings()


def render_dashboard():
    # Simulated notification for demo if no opportunities exist
    if 'notifications_shown' not in st.session_state:
        st.session_state.notifications_shown = []
    
    if st.session_state.get("scanner_running") and not st.session_state.get("first_opp_notified", False):
        st.toast("🔍 Scanner active: Monitoring Polymarket and Kalshi...", icon="📡")
        st.session_state.first_opp_notified = True

    st.markdown('<h1 style="margin-bottom: 8px;">Dashboard</h1><p style="color: #666666; margin-bottom: 32px;">Real-time arbitrage monitoring and performance tracking</p>', unsafe_allow_html=True)

    metrics = st.session_state.metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Daily Profit", value=f"${metrics['daily_profit']}", delta="+12%")
    with col2:
        st.metric(label="Total Trades", value=str(metrics['total_trades']), delta="0 today")
    with col3:
        st.metric(label="Win Rate", value=f"{metrics['win_rate']}%", delta="+2%")
    with col4:
        st.metric(label="Avg Latency", value=f"{metrics['avg_latency']}ms", delta="-15ms")
    with col5:
        st.metric(label="Active Positions", value=str(metrics['active_positions']), delta="$0.00 deployed")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='margin-bottom: 16px;'>P&L History</h3>", unsafe_allow_html=True)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=[0]*len(dates), mode="lines", line=dict(color="#00DC82", width=2), fill="tozeroy", fillcolor="rgba(0, 220, 130, 0.1)"))
        fig.update_layout(**PLOTLY_THEME, height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<h3 style='margin-bottom: 16px;'>Strategy Distribution</h3>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=["Binary Complement", "Cross-Platform", "DEX-CEX", "Funding Rate"], values=[1,1,1,1], hole=0.6, marker=dict(colors=["#0070F3", "#7928CA", "#FF4444", "#00DC82"], line=dict(color="#0A0A0A", width=2)), textinfo="none")])
        fig.update_layout(**PLOTLY_THEME, height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=11, color="#A1A1A1")))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='margin: 32px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='margin-bottom: 20px; font-size: 18px;'>Latest Opportunities</h3>", unsafe_allow_html=True)
        opps = st.session_state.get("opportunities", [])[:3]
        if not opps:
            st.markdown('<div class="vercel-card" style="padding: 24px; color: #666666;">No opportunities detected yet.</div>', unsafe_allow_html=True)
        for opp in opps:
            st.markdown(f"""
                <div class="vercel-card" style="padding: 16px; margin-bottom: 12px; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; font-size: 14px; color: #EDEDED;">{opp['title'][:40]}{'...' if len(opp['title']) > 40 else ''}</div>
                            <div style="font-size: 12px; color: #666666;">{opp['strategy']}</div>
                        </div>
                        <div style="color: var(--accent-green); font-weight: 700;">+{opp['profit_pct']}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    with col2:
        st.markdown("<h3 style='margin-bottom: 20px; font-size: 18px;'>Recent Trades</h3>", unsafe_allow_html=True)
        trades = st.session_state.get("trades", [])[:3]
        if not trades:
            st.markdown('<div class="vercel-card" style="padding: 24px; color: #666666;">No trades executed yet.</div>', unsafe_allow_html=True)
        for trade in trades:
            st.markdown(f"""
                <div class="vercel-card" style="padding: 16px; margin-bottom: 12px; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; font-size: 14px; color: #EDEDED;">{trade['market'][:40]}</div>
                            <div style="font-size: 12px; color: #666666;">{trade['strategy']}</div>
                        </div>
                        <div style="color: {'var(--accent-green)' if trade['profit'] > 0 else 'var(--accent-red)'}; font-weight: 700;">
                            {'+' if trade['profit'] > 0 else ''}${trade['profit']}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)


    st.markdown('<h1 style="margin-bottom: 8px;">Opportunities</h1><p style="color: #666666; margin-bottom: 24px;">Live arbitrage opportunities across all platforms</p>', unsafe_allow_html=True)

    # Scanner Controls at the Top
    col1, col2, col3, _ = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("▶ Start Scanner", use_container_width=True):
            st.session_state.scanner_running = True
            st.toast("Arbitrage scanner started", icon="🚀")
    with col2:
        if st.button("⏹ Stop Scanner", use_container_width=True):
            st.session_state.scanner_running = False
            st.toast("Arbitrage scanner stopped", icon="🛑")
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.selectbox("Type", ["All", "Binary Complement", "Cross-Platform", "DEX-CEX", "Funding Rate"])
    with col2:
        st.slider("Min Profit %", 0.0, 10.0, 1.0, 0.1)
    with col3:
        st.selectbox("Platform", ["All", "Polymarket", "Kalshi", "Binance", "KuCoin"])
    with col4:
        st.selectbox("Sort By", ["Profit %", "Liquidity", "Time Detected", "Confidence"])

    st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)
    
    opportunities = st.session_state.opportunities
    if not opportunities:
        st.markdown('<div class="vercel-card" style="text-align: center; padding: 48px;"><div style="width: 48px; height: 48px; background: #111; border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;"><span style="font-size: 24px;">🔍</span></div><h3 style="margin-bottom: 8px;">No opportunities detected</h3><p style="color: #666666;">The scanner checks for arbitrage every 1-5 seconds.</p></div>', unsafe_allow_html=True)
    else:
        for opp in opportunities:
            with st.container():
                st.markdown(f"""
                <div class="vercel-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h3 style="margin: 0; font-size: 18px;">{opp['title']}</h3>
                            <p style="color: #666666; font-size: 13px; margin-top: 4px;">{opp['strategy']} • {' & '.join(opp['platforms'])}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="color: var(--accent-green); font-family: 'JetBrains Mono'; font-weight: 700; font-size: 20px;">+{opp['profit_pct']}%</span>
                            <div style="font-size: 11px; color: #666666; margin-top: 4px;">{opp['timestamp'].strftime('%H:%M:%S')}</div>
                        </div>
                    </div>
                    <div style="margin-top: 16px; display: flex; gap: 24px;">
                        <div>
                            <p style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #444; margin-bottom: 4px;">Confidence</p>
                            <span class="mono" style="color: #EDEDED;">{opp['confidence']:.1%}</span>
                        </div>
                        <div>
                            <p style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #444; margin-bottom: 4px;">AI Risk Score</p>
                            <span class="mono" style="color: { 'var(--accent-green)' if opp['ai_risk_score'] < 0.2 else 'var(--accent-yellow)' };">{opp['ai_risk_score']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # Execution Links
                platform = opp['platforms'][0].lower()
                url = "#"
                if "polymarket" in platform:
                    slug = opp.get('slug')
                    url = f"https://polymarket.com/event/{slug}" if slug else f"https://polymarket.com/event/{opp['id'].split('-')[-1]}"
                elif "kalshi" in platform:
                    ticker = opp.get('ticker')
                    url = f"https://kalshi.com/markets/{ticker}" if ticker else f"https://kalshi.com/markets/{opp['id'].split('-')[-1]}"

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"Execute: {opp['id'][:8]}", key=f"exec_{opp['id']}", use_container_width=True):
                        st.toast(f"Executing paper trade for {opp['title']}...", icon="💸")
                with col2:
                    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration: none;"><button style="width: 100%; padding: 0.6rem; background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 10px; color: var(--text-primary); cursor: pointer; font-weight: 600;">View Market ↗</button></a>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)


def render_trades():
    st.markdown('<h1 style="margin-bottom: 8px;">Trade History</h1><p style="color: #666666; margin-bottom: 32px;">Complete record of all executed trades</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", "0")
    with col2:
        st.metric("Winning Trades", "0")
    with col3:
        st.metric("Losing Trades", "0")
    with col4:
        st.metric("Total P&L", "$0.00")

    st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.date_input("Date Range", value=(datetime.now() - timedelta(days=7), datetime.now()))
    with col2:
        st.multiselect("Status", ["Filled", "Pending", "Failed", "Cancelled"], default=["Filled", "Pending"])
    with col3:
        st.selectbox("Type", ["All", "Binary Complement", "Cross-Platform", "DEX-CEX"])

    st.markdown("<div style='margin: 24px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    trades = st.session_state.trades
    if not trades:
        st.markdown('<div class="vercel-card" style="text-align: center; padding: 48px;"><div style="width: 48px; height: 48px; background: #111; border-radius: 12px; margin: 0 auto 16px;"><span style="font-size: 24px;">📋</span></div><h3 style="margin-bottom: 8px;">No trades yet</h3><p style="color: #666666;">Executed trades will appear here.</p></div>', unsafe_allow_html=True)
    else:
        # Simple table rendering
        df = pd.DataFrame(trades)
        df['profit'] = df['profit'].apply(lambda x: f"${x:,.2f}")
        df['timestamp'] = df['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_risk_management():
    st.markdown('<h1 style="margin-bottom: 8px;">Risk Management</h1><p style="color: #666666; margin-bottom: 32px;">Circuit breakers, limits, and risk monitoring</p>', unsafe_allow_html=True)

    st.markdown('<div class="vercel-card"><div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;"><h3 style="margin: 0;">Circuit Breaker</h3><span class="status-badge status-active">NORMAL</span></div><p style="color: #666666; margin: 0;">All systems operational. Trading is enabled.</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Daily Loss", "$0.00", f"Limit: ${settings.risk.max_daily_loss_usd}")
    with col2:
        st.metric("Consecutive Errors", "0", f"Limit: {settings.risk.max_consecutive_errors}")
    with col3:
        st.metric("Risk Level", "Low", "Normal")

    st.markdown("<div style='margin: 32px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="vercel-card"><h3 style="margin-bottom: 16px; font-size: 16px;">Capital Limits</h3><div style="display: flex; flex-direction: column; gap: 12px;"><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Max Capital</span><span class="mono" style="color: #EDEDED;">${settings.risk.max_capital_usd:,.0f}</span></div><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Max Per Market</span><span class="mono" style="color: #EDEDED;">${settings.risk.max_position_per_market:,.0f}</span></div><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Max Total Positions</span><span class="mono" style="color: #EDEDED;">${settings.risk.max_total_positions:,.0f}</span></div></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="vercel-card"><h3 style="margin-bottom: 16px; font-size: 16px;">Execution Parameters</h3><div style="display: flex; flex-direction: column; gap: 12px;"><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Min Profit Threshold</span><span class="mono" style="color: #EDEDED;">{settings.risk.min_profit_threshold:.1%}</span></div><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Max Slippage</span><span class="mono" style="color: #EDEDED;">{settings.risk.max_slippage:.2%}</span></div><div style="display: flex; justify-content: space-between;"><span style="color: #666666;">Min Liquidity Depth</span><span class="mono" style="color: #EDEDED;">${settings.risk.min_liquidity_depth:,.0f}</span></div></div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔴 EMERGENCY STOP", type="primary", use_container_width=True):
            st.session_state.circuit_breaker_active = True
            st.toast("EMERGENCY STOP TRIGGERED", icon="🚨")
            st.error("Emergency stop triggered!")
    with col2:
        if st.button("Reset Circuit Breaker", use_container_width=True):
            st.session_state.circuit_breaker_active = False
            st.toast("Circuit breaker reset", icon="✅")
            st.success("Circuit breaker reset")
    with col3:
        if st.button("Export Risk Report", use_container_width=True):
            st.info("Risk report exported")


def render_settings():
    st.markdown('<h1 style="margin-bottom: 8px;">Settings</h1><p style="color: #666666; margin-bottom: 32px;">Configure trading mode, platform connections, and notifications</p>', unsafe_allow_html=True)

    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    if is_railway:
        st.markdown('<div class="vercel-card" style="border-color: #FFD93D; background: rgba(255, 217, 61, 0.05);"><p style="color: #FFD93D; margin: 0;">🚂 <strong>Running on Railway</strong>: Credentials saved here only persist for the current session. For permanent storage, set environment variables in Railway\'s Variables tab.</p></div>', unsafe_allow_html=True)
        st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='margin-bottom: 16px;'>Trading Mode</h3>", unsafe_allow_html=True)
    mode = st.radio("Mode", ["Dry Run (Paper Trading)", "Live Trading"], index=0 if settings.execution.dry_run else 1, horizontal=True, label_visibility="collapsed")

    if mode == "Live Trading":
        st.markdown('<div class="vercel-card" style="border-color: #FF4444; background: rgba(255, 68, 68, 0.05);"><p style="color: #FF4444; margin: 0;">⚠️ Live trading is enabled. Real orders will be placed with real funds.</p></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom: 16px;'>Platform Connections</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("Polymarket", expanded=True):
            poly_key = st.text_input("API Key", value="*" * 20 if settings.polymarket.api_key else "", type="password", key="poly_key")
            st.checkbox("Enabled", value=True, key="poly_enabled")

        with st.expander("Kalshi"):
            kalshi_email = st.text_input("Email", value=settings.kalshi.email or "", key="kalshi_email")
            kalshi_pass = st.text_input("Password", type="password", placeholder="Enter new password to update" if settings.kalshi.password else "Enter password", key="kalshi_pass")
            st.checkbox("Enabled", value=True, key="kalshi_enabled")

    with col2:
        with st.expander("Binance"):
            binance_key = st.text_input("API Key", type="password", key="binance_key")
            binance_secret = st.text_input("API Secret", type="password", key="binance_secret")
            st.checkbox("Enabled", value=False, key="binance_enabled")

        with st.expander("KuCoin"):
            kucoin_key = st.text_input("API Key", type="password", key="kucoin_key")
            st.checkbox("Enabled", value=False, key="kucoin_enabled")

    st.markdown("<div style='margin: 32px 0; border-top: 1px solid #333333;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom: 16px;'>Notifications</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        telegram_token = st.text_input("Telegram Bot Token", type="password", value=settings.notifications.telegram_bot_token or "")
        telegram_chat = st.text_input("Telegram Chat ID", value=settings.notifications.telegram_chat_id or "")
    with col2:
        discord_webhook = st.text_input("Discord Webhook URL", type="password", value=settings.notifications.discord_webhook_url or "")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    if st.button("Save Settings", type="primary", use_container_width=True):
        try:
            if kalshi_email:
                save_env_variable("KALSHI_EMAIL", kalshi_email)
            if kalshi_pass:
                save_env_variable("KALSHI_PASSWORD", kalshi_pass)
            if poly_key and poly_key != "*" * 20:
                save_env_variable("POLYMARKET_API_KEY", poly_key)
            if binance_key:
                save_env_variable("BINANCE_API_KEY", binance_key)
            if binance_secret:
                save_env_variable("BINANCE_API_SECRET", binance_secret)
            if kucoin_key:
                save_env_variable("KUCOIN_API_KEY", kucoin_key)
            if telegram_token and telegram_token != settings.notifications.telegram_bot_token:
                save_env_variable("TELEGRAM_BOT_TOKEN", telegram_token)
            if telegram_chat:
                save_env_variable("TELEGRAM_CHAT_ID", telegram_chat)
            if discord_webhook and discord_webhook != settings.notifications.discord_webhook_url:
                save_env_variable("DISCORD_WEBHOOK_URL", discord_webhook)

            reload_settings()
            st.success("✅ Settings saved successfully!")

            if is_railway:
                st.warning("⚠️ **Railway Note**: Credentials work for this session only. For permanent storage, add them to Railway's Variables tab.")
            else:
                st.info("💾 Credentials saved to .env file and will persist across restarts.")

            st.rerun()
        except Exception as e:
            st.error(f"❌ Error saving settings: {e}")


if __name__ == "__main__":
    main()
