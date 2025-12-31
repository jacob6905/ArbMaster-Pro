"""
ArbMaster Pro - Command Center Dashboard

Single-page trading dashboard with master-detail layout.
Built with Streamlit + Vercel Dark Mode styling.
"""

import streamlit as st
import asyncio
import random
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger

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
    initial_sidebar_state="collapsed"  # No sidebar in new design
)

# =============================================================================
# VERCEL DARK MODE CSS
# =============================================================================

VERCEL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        /* Vercel Colors */
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-card: #111111;
        --bg-hover: #1a1a1a;
        --border-default: #262626;
        --border-hover: #404040;
        --text-primary: #ededed;
        --text-secondary: #888888;
        --text-muted: #666666;
        --accent-blue: #0070f3;
        --accent-cyan: #79ffe1;
        --success: #00d26a;
        --danger: #ff4444;
        --warning: #f5a623;
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
    
    /* Remove default padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* ==================== HEADER ==================== */
    .header-bar {
        background: var(--bg-primary);
        border-bottom: 1px solid var(--border-default);
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    
    .header-left {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    
    .logo {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .scanner-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .scanner-on {
        background: rgba(0, 210, 106, 0.15);
        border: 1px solid var(--success);
        color: var(--success);
    }
    
    .scanner-off {
        background: rgba(255, 68, 68, 0.15);
        border: 1px solid var(--danger);
        color: var(--danger);
    }
    
    .header-center {
        display: flex;
        align-items: center;
        gap: 32px;
    }
    
    .pnl-display {
        text-align: center;
    }
    
    .pnl-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .pnl-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .pnl-positive { color: var(--success); }
    .pnl-negative { color: var(--danger); }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stat-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    /* ==================== MAIN LAYOUT ==================== */
    .main-container {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 0;
        height: calc(100vh - 120px);
        overflow: hidden;
    }
    
    .opportunities-panel {
        border-right: 1px solid var(--border-default);
        overflow-y: auto;
        padding: 16px;
    }
    
    .detail-panel {
        padding: 24px;
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }

    /* ==================== OPPORTUNITY CARDS ==================== */
    .opp-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .opp-card:hover {
        border-color: var(--accent-blue);
        background: var(--bg-hover);
    }
    
    .opp-card.selected {
        border-color: var(--accent-blue);
        background: rgba(0, 112, 243, 0.1);
    }
    
    .opp-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }
    
    .opp-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.3;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .opp-spread {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1rem;
        font-weight: 600;
        color: var(--success);
    }
    
    .opp-meta {
        display: flex;
        gap: 12px;
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    
    .platform-badge {
        background: var(--bg-hover);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--text-secondary);
    }

    /* ==================== DETAIL PANEL ==================== */
    .detail-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 16px;
        line-height: 1.4;
    }
    
    .price-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
    }
    
    .price-box {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    
    .price-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .price-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .price-yes { color: var(--success); }
    .price-no { color: var(--danger); }
    
    .spread-box {
        background: rgba(0, 210, 106, 0.1);
        border: 1px solid var(--success);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        margin-bottom: 24px;
    }
    
    .spread-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }
    
    .spread-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 2rem;
        font-weight: 700;
        color: var(--success);
    }
    
    .ai-reasoning {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 24px;
    }
    
    .ai-label {
        font-size: 0.75rem;
        color: var(--accent-cyan);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .ai-text {
        font-size: 0.875rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }
    
    .action-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: auto;
    }
    
    .btn-execute {
        background: var(--success) !important;
        color: #000 !important;
        font-weight: 600 !important;
        padding: 14px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .btn-execute:hover {
        filter: brightness(1.1) !important;
    }
    
    .btn-skip {
        background: transparent !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        padding: 14px 24px !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-default) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    .btn-skip:hover {
        border-color: var(--text-secondary) !important;
        color: var(--text-primary) !important;
    }

    /* ==================== FOOTER ==================== */
    .footer-bar {
        background: var(--bg-secondary);
        border-top: 1px solid var(--border-default);
        padding: 8px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
    }
    
    .connection-status {
        display: flex;
        gap: 16px;
    }
    
    .status-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }
    
    .status-connected { background: var(--success); }
    .status-disconnected { background: var(--danger); }
    
    .last-update {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* ==================== TRADES TABLE ==================== */
    .trades-section {
        background: var(--bg-secondary);
        border-top: 1px solid var(--border-default);
        padding: 16px 24px;
    }
    
    .trades-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    
    .trades-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .trades-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .trades-table th {
        text-align: left;
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 8px 12px;
        border-bottom: 1px solid var(--border-default);
    }
    
    .trades-table td {
        font-size: 0.8rem;
        padding: 10px 12px;
        color: var(--text-secondary);
        border-bottom: 1px solid var(--border-default);
    }
    
    .trades-table td:first-child {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ==================== EMPTY STATE ==================== */
    .empty-state {
        text-align: center;
        padding: 60px 24px;
        color: var(--text-muted);
    }
    
    .empty-icon {
        font-size: 3rem;
        margin-bottom: 16px;
        opacity: 0.5;
    }
    
    .empty-text {
        font-size: 1rem;
        margin-bottom: 8px;
    }
    
    .empty-hint {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    /* ==================== SETTINGS MODAL ==================== */
    .settings-overlay {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        width: 400px;
        background: var(--bg-card);
        border-left: 1px solid var(--border-default);
        z-index: 200;
        padding: 24px;
        overflow-y: auto;
    }
    
    .settings-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    
    .settings-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    /* ==================== STREAMLIT OVERRIDES ==================== */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
    }
    
    div[data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    
    div[data-testid="stMetric"] label {
        color: var(--text-muted) !important;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--text-primary) !important;
    }
    
    /* Toast styling */
    .stToast {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 8px !important;
    }
</style>
"""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "scanner_running": False,
        "selected_opportunity": None,
        "opportunities": [],
        "trades": [],
        "last_update": None,
        "show_settings": False,
        "paper_trading": True,
        "daily_pnl": Decimal("0.00"),
        "total_trades": 0,
        "win_rate": 0,
        "api_status": {
            "polymarket": True,
            "kalshi": True,
            "binance": True
        }
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
            opportunities = await PublicDataProvider.get_live_opportunities()
            return opportunities
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
    return []

def get_opportunities():
    """Sync wrapper for fetching opportunities."""
    try:
        return asyncio.run(fetch_live_data())
    except Exception as e:
        logger.error(f"Error in get_opportunities: {e}")
        return []

# =============================================================================
# HEADER COMPONENT
# =============================================================================

def render_header():
    """Render the top header bar."""
    pnl = float(st.session_state.daily_pnl)
    pnl_class = "pnl-positive" if pnl >= 0 else "pnl-negative"
    pnl_display = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
    
    scanner_class = "scanner-on" if st.session_state.scanner_running else "scanner-off"
    scanner_text = "● SCANNING" if st.session_state.scanner_running else "○ STOPPED"
    
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1.5, 1.5, 1])
    
    with col1:
        st.markdown("### 📈 ArbMaster Pro")
    
    with col2:
        if st.session_state.scanner_running:
            if st.button("⏹ Stop Scanner", use_container_width=True):
                st.session_state.scanner_running = False
                st.toast("Scanner stopped", icon="🛑")
                st.rerun()
        else:
            if st.button("▶ Start Scanner", use_container_width=True):
                st.session_state.scanner_running = True
                # Fetch fresh data
                st.session_state.opportunities = get_opportunities()
                st.session_state.last_update = datetime.now()
                st.toast("Scanner started!", icon="🚀")
                st.rerun()
    
    with col3:
        st.metric("Today's P&L", pnl_display)
    
    with col4:
        st.metric("Trades", st.session_state.total_trades)
    
    with col5:
        st.metric("Win Rate", f"{st.session_state.win_rate}%")
    
    with col6:
        if st.button("⚙️", use_container_width=True):
            st.session_state.show_settings = not st.session_state.show_settings
            st.rerun()
    
    st.markdown("<hr style='margin: 8px 0; border-color: #262626;'>", unsafe_allow_html=True)

# =============================================================================
# OPPORTUNITY LIST COMPONENT
# =============================================================================

def render_opportunity_card(opp: Dict[str, Any], index: int):
    """Render a single opportunity card."""
    is_selected = st.session_state.selected_opportunity == index
    
    platform = opp.get('platforms', ['Unknown'])[0]
    spread = opp.get('profit_pct', 0)
    title = opp.get('title', 'Untitled')[:50]
    
    # Card container
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(
                f"**{title}**\n\n`{platform}`",
                key=f"opp_{index}",
                use_container_width=True
            ):
                st.session_state.selected_opportunity = index
                st.rerun()
        
        with col2:
            spread_color = "🟢" if spread > 0 else "⚪"
            st.markdown(f"### {spread_color} {spread:.2f}%")

def render_opportunity_list():
    """Render the scrollable list of opportunities."""
    st.markdown("#### Live Opportunities")
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.opportunities = get_opportunities()
            st.session_state.last_update = datetime.now()
            st.toast("Data refreshed!", icon="✅")
            st.rerun()
    
    st.markdown("<hr style='margin: 8px 0; border-color: #262626;'>", unsafe_allow_html=True)
    
    opportunities = st.session_state.opportunities
    
    if not opportunities:
        st.markdown("""
        <div style='text-align: center; padding: 40px; color: #666;'>
            <div style='font-size: 2rem; margin-bottom: 12px;'>📭</div>
            <div>No opportunities found</div>
            <div style='font-size: 0.875rem; margin-top: 8px;'>Start the scanner to find arbitrage opportunities</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sort by spread
    sorted_opps = sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)
    
    for i, opp in enumerate(sorted_opps[:15]):
        platform = opp.get('platforms', ['Unknown'])[0]
        spread = opp.get('profit_pct', 0)
        title = opp.get('title', 'Untitled')
        
        is_selected = st.session_state.selected_opportunity == i
        
        # Create a card-like button
        with st.container():
            if st.button(
                f"{'→ ' if is_selected else ''}{title[:40]}{'...' if len(title) > 40 else ''}",
                key=f"opp_btn_{i}",
                use_container_width=True
            ):
                st.session_state.selected_opportunity = i
                st.rerun()
            
            cols = st.columns([2, 1])
            with cols[0]:
                st.caption(f"📍 {platform}")
            with cols[1]:
                color = "green" if spread > 0 else "gray"
                st.markdown(f"<span style='color: {color}; font-weight: 600;'>{spread:.2f}%</span>", unsafe_allow_html=True)
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# =============================================================================
# OPPORTUNITY DETAIL COMPONENT
# =============================================================================

def render_opportunity_detail():
    """Render the detail panel for selected opportunity."""
    st.markdown("#### Opportunity Details")
    st.markdown("<hr style='margin: 8px 0; border-color: #262626;'>", unsafe_allow_html=True)
    
    if st.session_state.selected_opportunity is None:
        st.markdown("""
        <div style='text-align: center; padding: 60px; color: #666;'>
            <div style='font-size: 2rem; margin-bottom: 12px;'>👈</div>
            <div>Select an opportunity to view details</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    opportunities = st.session_state.opportunities
    if not opportunities:
        return
    
    # Sort same as list
    sorted_opps = sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)
    
    idx = st.session_state.selected_opportunity
    if idx >= len(sorted_opps):
        st.session_state.selected_opportunity = None
        return
    
    opp = sorted_opps[idx]
    
    # Title
    st.markdown(f"### {opp.get('title', 'Untitled')}")
    
    # Platform and strategy
    platform = opp.get('platforms', ['Unknown'])[0]
    strategy = opp.get('strategy', 'Unknown')
    st.caption(f"📍 {platform} • 🎯 {strategy}")
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Price Grid
    col1, col2 = st.columns(2)
    
    yes_price = opp.get('yes_price')
    no_price = opp.get('no_price')
    
    with col1:
        st.markdown("**YES Price**")
        if yes_price:
            st.markdown(f"<h2 style='color: #00d26a; margin: 0;'>${yes_price:.2f}</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color: #666; margin: 0;'>—</h2>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("**NO Price**")
        if no_price:
            st.markdown(f"<h2 style='color: #ff4444; margin: 0;'>${no_price:.2f}</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color: #666; margin: 0;'>—</h2>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Spread Display
    spread = opp.get('profit_pct', 0)
    st.markdown(f"""
    <div style='background: rgba(0, 210, 106, 0.1); border: 1px solid #00d26a; border-radius: 8px; padding: 16px; text-align: center;'>
        <div style='font-size: 0.875rem; color: #888;'>Arbitrage Spread</div>
        <div style='font-size: 2rem; font-weight: 700; color: #00d26a; font-family: "JetBrains Mono", monospace;'>{spread:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # AI Reasoning
    reasoning = opp.get('ai_reasoning', 'No analysis available')
    confidence = opp.get('confidence', 0) * 100
    
    st.markdown(f"""
    <div style='background: #111; border: 1px solid #262626; border-radius: 8px; padding: 16px;'>
        <div style='font-size: 0.75rem; color: #79ffe1; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;'>
            🤖 AI Analysis • {confidence:.0f}% Confidence
        </div>
        <div style='font-size: 0.875rem; color: #888; line-height: 1.5;'>{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Action Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ EXECUTE", use_container_width=True, type="primary"):
            # Simulate trade execution
            st.session_state.trades.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "market": opp.get('title', 'Unknown')[:30],
                "side": "BUY YES",
                "pnl": f"+${spread:.2f}"
            })
            st.session_state.total_trades += 1
            st.session_state.daily_pnl += Decimal(str(spread))
            st.session_state.win_rate = 85  # Simulated
            st.toast(f"Paper trade executed! Profit: {spread:.2f}%", icon="💰")
            st.session_state.selected_opportunity = None
            st.rerun()
    
    with col2:
        if st.button("⏭ SKIP", use_container_width=True):
            # Move to next opportunity
            if st.session_state.selected_opportunity < len(sorted_opps) - 1:
                st.session_state.selected_opportunity += 1
            else:
                st.session_state.selected_opportunity = 0
            st.rerun()
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # View on Platform Link
    slug = opp.get('slug', '')
    ticker = opp.get('ticker', '')
    
    if 'polymarket' in platform.lower() and slug:
        url = f"https://polymarket.com/event/{slug}"
        st.markdown(f"[🔗 View on Polymarket]({url})")
    elif 'kalshi' in platform.lower() and ticker:
        url = f"https://kalshi.com/markets/{ticker}"
        st.markdown(f"[🔗 View on Kalshi]({url})")

# =============================================================================
# RECENT TRADES COMPONENT
# =============================================================================

def render_recent_trades():
    """Render the recent trades section."""
    st.markdown("#### Recent Trades")
    
    trades = st.session_state.trades[:5]
    
    if not trades:
        st.caption("No trades yet. Execute an opportunity to see trades here.")
        return
    
    for trade in trades:
        cols = st.columns([1, 3, 2, 1])
        with cols[0]:
            st.caption(trade['time'])
        with cols[1]:
            st.caption(trade['market'])
        with cols[2]:
            st.caption(trade['side'])
        with cols[3]:
            st.markdown(f"<span style='color: #00d26a;'>{trade['pnl']}</span>", unsafe_allow_html=True)

# =============================================================================
# FOOTER COMPONENT
# =============================================================================

def render_footer():
    """Render the status footer."""
    st.markdown("<hr style='margin: 16px 0; border-color: #262626;'>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "🟢" if st.session_state.api_status.get('polymarket') else "🔴"
        st.caption(f"{status} Polymarket")
    
    with col2:
        status = "🟢" if st.session_state.api_status.get('kalshi') else "🔴"
        st.caption(f"{status} Kalshi")
    
    with col3:
        status = "🟢" if st.session_state.api_status.get('binance') else "🔴"
        st.caption(f"{status} Binance")
    
    with col4:
        if st.session_state.last_update:
            st.caption(f"Updated: {st.session_state.last_update.strftime('%H:%M:%S')}")
        else:
            st.caption("Not updated yet")

# =============================================================================
# SETTINGS PANEL
# =============================================================================

def render_settings():
    """Render settings panel if open."""
    if not st.session_state.show_settings:
        return
    
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        st.markdown("### Trading Mode")
        st.session_state.paper_trading = st.toggle(
            "Paper Trading",
            value=st.session_state.paper_trading,
            help="When enabled, trades are simulated without real execution"
        )
        
        st.markdown("### API Status")
        st.info("Using public API endpoints (no auth required)")
        
        st.markdown("### Actions")
        if st.button("Reset Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        if st.button("Close Settings", use_container_width=True):
            st.session_state.show_settings = False
            st.rerun()

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    # Inject CSS
    st.markdown(VERCEL_CSS, unsafe_allow_html=True)
    
    # Initialize state
    init_session_state()
    
    # Auto-fetch on first load
    if st.session_state.scanner_running and not st.session_state.opportunities:
        st.session_state.opportunities = get_opportunities()
        st.session_state.last_update = datetime.now()
    
    # Render components
    render_header()
    
    # Main layout: Two columns
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        render_opportunity_list()
    
    with right_col:
        render_opportunity_detail()
    
    # Recent trades
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    render_recent_trades()
    
    # Footer
    render_footer()
    
    # Settings (renders in sidebar when open)
    render_settings()
    
    # Auto-refresh when scanner is running
    if st.session_state.scanner_running:
        import time
        now = datetime.now()
        if st.session_state.last_update:
            elapsed = (now - st.session_state.last_update).total_seconds()
            if elapsed > 60:  # Refresh every 60s
                st.session_state.opportunities = get_opportunities()
                st.session_state.last_update = now
                st.rerun()


if __name__ == "__main__":
    main()
