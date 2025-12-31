"""
ArbMaster Pro - Premium Trading Dashboard

Clone of the Replit reference design with FUNCTIONAL navigation.
- Uses st.sidebar for real navigation state control
- Multi-page layout (Dashboard, Strategies, Analytics, Wallet)
- Premium dark mode styling
"""

import streamlit as st
import asyncio
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
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS STYLING
# =============================================================================

PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-card: #111111;
        --border-default: #1a1a1a;
        --text-primary: #ffffff;
        --text-secondary: #a1a1a1;
        --accent-green: #00ff88;
        --accent-green-dim: rgba(0, 255, 136, 0.1);
        --accent-red: #ff4757;
    }

    /* Global */
    .stApp { background: var(--bg-primary); }
    * { font-family: 'Inter', sans-serif !important; }

    /* Hide Streamlit Chrome */
    #MainMenu, footer, header { visibility: hidden !important; }
    .stDeployButton { display: none !important; }

    /* Custom Sidebar Styling */
    section[data-testid="stSidebar"] {
        width: 80px !important;
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-default) !important;
    }
    
    /* Hide top padding in sidebar */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }

    /* Navigation Buttons */
    .nav-btn {
        width: 100%;
        border-radius: 12px;
        background: transparent;
        color: var(--text-secondary);
        border: none;
        font-size: 1.5rem;
        padding: 12px 0;
        cursor: pointer;
        text-align: center;
        margin-bottom: 8px;
    }
    
    .nav-btn:hover {
        background: var(--bg-card);
        color: var(--text-primary);
    }
    
    .nav-btn.active {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    
    /* Cards */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Sparklines */
    .sparkline-green {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, transparent, var(--accent-green));
        border-radius: 2px;
        margin-top: 12px;
    }

    /* Streamlit Overrides */
    div[data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 16px !important;
        padding: 16px !important;
    }
    div[data-testid="stMetric"] label { font-size: 0.75rem !important; color: var(--text-secondary) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.5rem !important; color: white !important; font-family: 'JetBrains Mono' !important; }
    
    /* Hide the default sidebar resize handle */
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }
</style>
"""

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "metrics" not in st.session_state:
        st.session_state.metrics = {
            "total_profit": 2847.32,
            "active_capital": 15000.00,
            "daily_roi": 3.2,
            "win_rate": 87
        }
    if "opportunities" not in st.session_state:
        st.session_state.opportunities = []

# =============================================================================
# DATA
# =============================================================================

async def fetch_live_data():
    if PublicDataProvider:
        try:
            st.session_state.opportunities = await PublicDataProvider.get_live_opportunities()
        except:
            pass

def get_data_sync():
    """Sync data fetcher."""
    asyncio.run(fetch_live_data())

# =============================================================================
# COMPONENTS
# =============================================================================

def render_sidebar():
    """Render the functional sidebar."""
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>📈</h2>", unsafe_allow_html=True)
        
        pages = [
            ("dashboard", "🏠", "Dashboard"),
            ("strategies", "🎯", "Strategies"),
            ("analytics", "📊", "Analytics"),
            ("wallet", "💰", "Wallet"),
            ("settings", "⚙️", "Settings")
        ]
        
        for pg_id, icon, label in pages:
            # Use full width buttons
            if st.button(f"{icon}", key=f"nav_{pg_id}", help=label, use_container_width=True):
                st.session_state.page = pg_id
                st.rerun()

def render_header():
    """Global header."""
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"## {st.session_state.page.title()}")
    with col2:
        st.text_input("Search...", placeholder="Search markets...", label_visibility="collapsed")
    with col3:
        st.markdown("""
        <div style='display: flex; gap: 12px; justify-content: flex-end; align-items: center;'>
            <span style='color: #00ff88; font-size: 0.8rem;'>● ONLINE</span>
            <span style='background: #111; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;'>ETH $3,420</span>
            <span style='font-size: 1.2rem;'>🔔</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1a1a1a; margin-top: 0;'>", unsafe_allow_html=True)

# =============================================================================
# PAGES
# =============================================================================

def page_dashboard():
    # METRICS
    m = st.session_state.metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Profit", f"${m['total_profit']:,.2f}", "+12%")
    c2.metric("Active Capital", f"${m['active_capital']:,.2f}", "+$2k")
    c3.metric("Daily ROI", f"{m['daily_roi']}%", "+0.4%")
    c4.metric("Win Rate", f"{m['win_rate']}%", "-2%")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # MAIN GRID
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.markdown("### Performance Overview")
        st.markdown("""
        <div class="card" style="height: 300px; display: flex; align-items: center; justify-content: center; background: linear-gradient(180deg, rgba(0,255,136,0.05) 0%, transparent 100%);">
            <h3 style="color: #00ff88;">[ Area Chart Placeholder ]</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Live Opportunities")
        if not st.session_state.opportunities:
             get_data_sync()
        
        for opp in st.session_state.opportunities[:5]:
            with st.container():
                cols = st.columns([3, 1, 1])
                cols[0].markdown(f"**{opp.get('title', '')}**")
                cols[1].caption(opp.get('platforms', [''])[0])
                profit = opp.get('profit_pct', 0)
                cols[2].markdown(f"<span style='color: #00ff88; font-family: JetBrains Mono;'>{profit:.2f}%</span>", unsafe_allow_html=True)
                st.markdown("<hr style='border-color: #1a1a1a; margin: 4px 0;'>", unsafe_allow_html=True)

    with c_right:
        st.markdown("### Live Activity")
        st.markdown("""
        <div class="card">
            <div style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center;">
                <div style="background: rgba(0,255,136,0.1); color: #00ff88; padding: 4px; border-radius: 4px;">BUY</div>
                <div style="flex: 1; font-size: 0.9rem;">Bitcoin > $100k</div>
                <div style="font-family: JetBrains Mono; color: #00ff88;">+$12.50</div>
            </div>
            <div style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center;">
                <div style="background: rgba(255,71,87,0.1); color: #ff4757; padding: 4px; border-radius: 4px;">SELL</div>
                <div style="flex: 1; font-size: 0.9rem;">ETH Volatility</div>
                <div style="font-family: JetBrains Mono; color: #ff4757;">+$8.20</div>
            </div>
             <div style="display: flex; gap: 10px; margin-bottom: 12px; align-items: center;">
                <div style="background: rgba(0,255,136,0.1); color: #00ff88; padding: 4px; border-radius: 4px;">ARB</div>
                <div style="flex: 1; font-size: 0.9rem;">Poly/Kalshi Spread</div>
                <div style="font-family: JetBrains Mono; color: #00ff88;">+$42.00</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def page_strategies():
    st.markdown("### Active Bots")
    
    strategies = [
        {"name": "Cross-Exchange Arb", "roi": 12.4, "active": True},
        {"name": "Binary Complement", "roi": 8.2, "active": True},
        {"name": "News Event Fade", "roi": -1.2, "active": False},
    ]
    
    cols = st.columns(3)
    for i, s in enumerate(strategies):
        with cols[i]:
            status = "🟢 Running" if s["active"] else "🔴 Paused"
            st.markdown(f"""
            <div class="card">
                <h4>{s['name']}</h4>
                <div style="color: #666; font-size: 0.8rem; margin-bottom: 12px;">{status}</div>
                <div style="font-size: 1.5rem; font-family: JetBrains Mono;">{s['roi']}% ROI</div>
            </div>
            """, unsafe_allow_html=True)
            if s["active"]:
                st.button(f"Pause {s['name']}", key=f"pause_{i}")
            else:
                st.button(f"Start {s['name']}", key=f"start_{i}")

def page_analytics():
    st.info("Analytics module loading...")
    st.markdown("### Profit History")
    st.bar_chart([10, 12, 15, 14, 18, 22, 25, 24, 28, 32, 30, 35])

def page_settings():
    st.markdown("### Configuration")
    st.toggle("Paper Trading Mode", value=True)
    st.toggle("Dark Mode", value=True, disabled=True)
    st.text_input("Polymarket API Key", type="password")
    st.text_input("Kalshi API Key", type="password")
    st.button("Save Changes", type="primary")

# =============================================================================
# MAIN
# =============================================================================

def main():
    init_session_state()
    render_sidebar()
    render_header()
    
    pg = st.session_state.page
    
    if pg == "dashboard":
        page_dashboard()
    elif pg == "strategies":
        page_strategies()
    elif pg == "analytics":
        page_analytics()
    elif pg == "settings":
        page_settings()
    else:
        st.warning("Page not found")

if __name__ == "__main__":
    main()
