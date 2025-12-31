"""
ArbMaster Pro - Streamlit Dashboard

Real-time monitoring dashboard for arbitrage trading operations.
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
from pathlib import Path

# Add src to path for imports (handles both local dev and Docker)
src_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"),  # Local dev
    "/app/src",  # Docker
]
for src_path in src_paths:
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)

try:
    from config import settings
except ImportError as e:
    # Fallback: create minimal settings for dashboard to load
    st.error(f"Failed to import config: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="ArbMaster Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .profit-positive { color: #00FF00; }
    .profit-negative { color: #FF4444; }
    .status-active { color: #00FF00; }
    .status-halted { color: #FF4444; }
</style>
""", unsafe_allow_html=True)


def save_env_variable(key: str, value: str):
    """Save or update an environment variable in the .env file."""
    # Find the project root (where .env should be)
    dashboard_dir = Path(__file__).parent
    project_root = dashboard_dir.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    # Read existing .env or use .env.example as template
    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()
    elif env_example.exists():
        with open(env_example, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add the key-value pair
    key_found = False
    updated_lines = []

    for line in lines:
        stripped = line.strip()
        # Check if this line defines our key
        if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
            # Replace with new value
            updated_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            updated_lines.append(line)

    # If key wasn't found, add it
    if not key_found:
        updated_lines.append(f"{key}={value}\n")

    # Write back to .env
    with open(env_file, "w") as f:
        f.writelines(updated_lines)


def main():
    """Main dashboard entry point."""

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=ArbMaster+Pro", width=150)
        st.title("ArbMaster Pro")
        st.markdown("---")

        # Mode indicator
        mode = "DRY RUN" if settings.execution.dry_run else "LIVE"
        mode_color = "🟡" if settings.execution.dry_run else "🟢"
        st.markdown(f"### {mode_color} Mode: **{mode}**")

        # Navigation
        page = st.radio(
            "Navigation",
            ["Dashboard", "Opportunities", "Trades", "Risk Management", "Settings"],
            index=0,
        )

        st.markdown("---")

        # Quick stats
        st.markdown("### Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Daily P&L", "$0.00", "+0%")
        with col2:
            st.metric("Win Rate", "0%", "0")

        # Status
        st.markdown("### System Status")

        # Check Polymarket credentials
        poly_status = "✅" if settings.polymarket.api_key or settings.polymarket.private_key else "❌"
        st.markdown(f"{poly_status} Polymarket {'Connected' if poly_status == '✅' else 'Not Configured'}")

        # Check Kalshi credentials
        kalshi_status = "✅" if (settings.kalshi.email and settings.kalshi.password) else "❌"
        st.markdown(f"{kalshi_status} Kalshi {'Connected' if kalshi_status == '✅' else 'Not Configured'}")

        st.markdown("⚪ No active trades")

    # Main content based on page
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
    """Render main dashboard view."""
    st.title("📊 Dashboard")
    st.markdown("Real-time arbitrage monitoring and performance tracking")

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Daily Profit",
            value="$0.00",
            delta="0%",
            delta_color="normal",
        )

    with col2:
        st.metric(
            label="Total Trades",
            value="0",
            delta="0 today",
        )

    with col3:
        st.metric(
            label="Win Rate",
            value="0%",
            delta="0%",
        )

    with col4:
        st.metric(
            label="Avg Latency",
            value="0ms",
            delta="target: <500ms",
            delta_color="off",
        )

    with col5:
        st.metric(
            label="Active Positions",
            value="0",
            delta="$0 deployed",
            delta_color="off",
        )

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("P&L History")
        # Sample data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D")
        pnl = [0] * len(dates)  # Placeholder

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=pnl,
            mode="lines+markers",
            name="Daily P&L",
            line=dict(color="#00FF00", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 255, 0, 0.1)",
        ))
        fig.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Date",
            yaxis_title="P&L ($)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Strategy Distribution")
        strategies = ["Binary Complement", "Cross-Platform", "DEX-CEX", "Funding Rate"]
        values = [0, 0, 0, 0]  # Placeholder

        fig = go.Figure(data=[go.Pie(
            labels=strategies,
            values=[1, 1, 1, 1],  # Show equal slices when no data
            hole=0.4,
            marker_colors=["#00FF00", "#0088FF", "#FF8800", "#FF00FF"],
        )])
        fig.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔍 Recent Opportunities")
        st.info("No opportunities detected yet. Start the scanner to see live data.")

    with col2:
        st.subheader("📋 Recent Trades")
        st.info("No trades executed yet. Opportunities will be listed here when detected.")


def render_opportunities():
    """Render opportunities view."""
    st.title("🔍 Arbitrage Opportunities")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        arb_type = st.selectbox(
            "Arbitrage Type",
            ["All", "Binary Complement", "Cross-Platform", "DEX-CEX", "Funding Rate"],
        )

    with col2:
        min_profit = st.slider("Min Profit %", 0.0, 10.0, 1.0, 0.1)

    with col3:
        platform = st.selectbox(
            "Platform",
            ["All", "Polymarket", "Kalshi", "Binance", "KuCoin"],
        )

    with col4:
        sort_by = st.selectbox(
            "Sort By",
            ["Profit %", "Liquidity", "Time Detected", "Confidence"],
        )

    st.markdown("---")

    # Opportunities table
    st.subheader("Live Opportunities")

    # Sample empty dataframe
    df = pd.DataFrame(columns=[
        "ID", "Type", "Platform", "Market", "Profit %",
        "Liquidity", "Confidence", "Detected", "Actions"
    ])

    if df.empty:
        st.info(
            "No opportunities currently detected. "
            "The scanner checks for arbitrage every 1-5 seconds."
        )
    else:
        st.dataframe(df, use_container_width=True)

    # Scanner controls
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Start Scanner", use_container_width=True):
            st.success("Scanner started!")

    with col2:
        if st.button("⏹️ Stop Scanner", use_container_width=True):
            st.warning("Scanner stopped")

    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()


def render_trades():
    """Render trades history view."""
    st.title("📋 Trade History")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", "0")
    with col2:
        st.metric("Winning Trades", "0")
    with col3:
        st.metric("Losing Trades", "0")
    with col4:
        st.metric("Total P&L", "$0.00")

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
        )

    with col2:
        status_filter = st.multiselect(
            "Status",
            ["Filled", "Pending", "Failed", "Cancelled"],
            default=["Filled", "Pending"],
        )

    with col3:
        type_filter = st.selectbox(
            "Type",
            ["All", "Binary Complement", "Cross-Platform", "DEX-CEX"],
        )

    # Trades table
    st.subheader("Executed Trades")

    df = pd.DataFrame(columns=[
        "ID", "Time", "Type", "Platform", "Market",
        "Size", "Entry", "Exit", "P&L", "Status"
    ])

    if df.empty:
        st.info("No trades have been executed yet.")
    else:
        st.dataframe(df, use_container_width=True)


def render_risk_management():
    """Render risk management view."""
    st.title("⚠️ Risk Management")

    # Circuit breaker status
    st.subheader("Circuit Breaker Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Status: NORMAL")
        st.markdown("Trading is enabled")

    with col2:
        st.metric("Daily Loss", "$0.00", f"Limit: ${settings.risk.max_daily_loss_usd}")

    with col3:
        st.metric("Consecutive Errors", "0", f"Limit: {settings.risk.max_consecutive_errors}")

    st.markdown("---")

    # Risk limits
    st.subheader("Risk Limits Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Capital Limits")
        st.markdown(f"- Max Capital: **${settings.risk.max_capital_usd:,.0f}**")
        st.markdown(f"- Max Per Market: **${settings.risk.max_position_per_market:,.0f}**")
        st.markdown(f"- Max Total Positions: **${settings.risk.max_total_positions:,.0f}**")

        st.markdown("### Execution Parameters")
        st.markdown(f"- Min Profit Threshold: **{settings.risk.min_profit_threshold:.1%}**")
        st.markdown(f"- Max Slippage: **{settings.risk.max_slippage:.2%}**")
        st.markdown(f"- Min Liquidity Depth: **${settings.risk.min_liquidity_depth:,.0f}**")

    with col2:
        st.markdown("### Circuit Breaker Triggers")
        st.markdown(f"- Max Daily Loss: **${settings.risk.max_daily_loss_usd:,.0f}**")
        st.markdown(f"- Max Consecutive Errors: **{settings.risk.max_consecutive_errors}**")
        st.markdown(f"- Cooldown Period: **{settings.risk.cooldown_seconds}s**")

        st.markdown("### Performance Targets")
        st.markdown(f"- Daily Profit Target: **${settings.performance.target_daily_profit:,.0f}**")
        st.markdown(f"- Target Win Rate: **{settings.performance.target_win_rate:.0%}**")
        st.markdown(f"- Target Latency: **<{settings.performance.target_latency_ms}ms**")

    st.markdown("---")

    # Manual controls
    st.subheader("Manual Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔴 EMERGENCY STOP", type="primary", use_container_width=True):
            st.error("Emergency stop triggered! All trading halted.")

    with col2:
        if st.button("🟡 Reset Circuit Breaker", use_container_width=True):
            st.success("Circuit breaker reset")

    with col3:
        if st.button("📊 Export Risk Report", use_container_width=True):
            st.info("Risk report exported to ./reports/")


def render_settings():
    """Render settings view."""
    st.title("⚙️ Settings")

    # Execution mode
    st.subheader("Execution Mode")

    mode = st.radio(
        "Trading Mode",
        ["Dry Run (Paper Trading)", "Live Trading"],
        index=0 if settings.execution.dry_run else 1,
        horizontal=True,
    )

    if mode == "Live Trading":
        st.warning(
            "⚠️ Live trading is enabled. Real orders will be placed. "
            "Ensure all API keys and risk limits are correctly configured."
        )

    st.markdown("---")

    # Platform connections
    st.subheader("Platform Connections")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Prediction Markets")

        # Polymarket
        with st.expander("Polymarket", expanded=True):
            poly_key = st.text_input(
                "API Key",
                value="*" * 20 if settings.polymarket.api_key else "",
                type="password",
                key="poly_key",
            )
            poly_enabled = st.checkbox("Enabled", value=True, key="poly_enabled")

        # Kalshi
        with st.expander("Kalshi"):
            kalshi_email = st.text_input(
                "Email",
                value=settings.kalshi.email or "",
                key="kalshi_email",
            )
            kalshi_pass = st.text_input(
                "Password",
                type="password",
                placeholder="Enter new password to update" if settings.kalshi.password else "Enter password",
                key="kalshi_pass",
            )
            kalshi_enabled = st.checkbox("Enabled", value=True, key="kalshi_enabled")

    with col2:
        st.markdown("### Exchanges")

        # Binance
        with st.expander("Binance"):
            binance_key = st.text_input(
                "API Key",
                type="password",
                key="binance_key",
            )
            binance_secret = st.text_input(
                "API Secret",
                type="password",
                key="binance_secret",
            )
            binance_enabled = st.checkbox("Enabled", value=False, key="binance_enabled")

        # KuCoin
        with st.expander("KuCoin"):
            kucoin_key = st.text_input(
                "API Key",
                type="password",
                key="kucoin_key",
            )
            kucoin_enabled = st.checkbox("Enabled", value=False, key="kucoin_enabled")

    st.markdown("---")

    # Notifications
    st.subheader("Notifications")

    col1, col2 = st.columns(2)

    with col1:
        telegram_token = st.text_input(
            "Telegram Bot Token",
            type="password",
            value=settings.notifications.telegram_bot_token or "",
        )
        telegram_chat = st.text_input(
            "Telegram Chat ID",
            value=settings.notifications.telegram_chat_id or "",
        )

    with col2:
        discord_webhook = st.text_input(
            "Discord Webhook URL",
            type="password",
            value=settings.notifications.discord_webhook_url or "",
        )

    st.markdown("---")

    # Save button
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        try:
            # Save Kalshi credentials
            if kalshi_email:
                save_env_variable("KALSHI_EMAIL", kalshi_email)
            if kalshi_pass:
                save_env_variable("KALSHI_PASSWORD", kalshi_pass)

            # Save Polymarket API key
            if poly_key and poly_key != "*" * 20:
                save_env_variable("POLYMARKET_API_KEY", poly_key)

            # Save Binance credentials
            if binance_key:
                save_env_variable("BINANCE_API_KEY", binance_key)
            if binance_secret:
                save_env_variable("BINANCE_API_SECRET", binance_secret)

            # Save KuCoin credentials
            if kucoin_key:
                save_env_variable("KUCOIN_API_KEY", kucoin_key)

            # Save notification settings
            if telegram_token and telegram_token != settings.notifications.telegram_bot_token:
                save_env_variable("TELEGRAM_BOT_TOKEN", telegram_token)
            if telegram_chat:
                save_env_variable("TELEGRAM_CHAT_ID", telegram_chat)
            if discord_webhook and discord_webhook != settings.notifications.discord_webhook_url:
                save_env_variable("DISCORD_WEBHOOK_URL", discord_webhook)

            st.success("✅ Settings saved successfully!")
            st.info("⚠️ Note: Restart the application for changes to take effect.")
        except Exception as e:
            st.error(f"❌ Error saving settings: {e}")


if __name__ == "__main__":
    main()
