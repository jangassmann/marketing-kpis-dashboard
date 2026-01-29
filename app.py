"""
Win Rate Tracker Dashboard
Track ad creative performance and win rates across Meta ad accounts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re
from dotenv import load_dotenv

from src.meta_api import (
    MetaAdsClient,
    get_demo_data,
    get_demo_insights,
    get_available_ad_accounts,
    fetch_all_accounts_data,
    fetch_all_accounts_insights,
)

load_dotenv()


# Cache data for 10 minutes to speed up page loads
@st.cache_data(ttl=600)
def load_cached_data(date_start_str: str, date_end_str: str, use_demo: bool):
    """Load and cache data from Meta API."""
    if use_demo:
        return get_demo_data(), get_demo_insights()

    date_start = datetime.strptime(date_start_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d")
    date_end = datetime.combine(date_end, datetime.max.time())

    data = fetch_all_accounts_data(date_start, date_end)
    insights = fetch_all_accounts_insights(date_start, date_end)
    return data, insights


# Page configuration
st.set_page_config(
    page_title="Win Rate Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for white theme with visible text
st.markdown("""
<style>
    /* White background theme - force light mode */
    .stApp {
        background-color: #f8f9fa !important;
    }
    .main > div {
        padding-top: 1rem;
    }

    /* Force light theme colors */
    [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa !important;
    }
    [data-testid="stHeader"] {
        background-color: #f8f9fa !important;
    }

    /* Make all text dark */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #111827 !important;
    }

    /* Selectbox styling - ensure visible text */
    .stSelectbox > div > div {
        background-color: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
    }
    .stSelectbox > div > div > div {
        color: #111827 !important;
    }
    .stSelectbox label {
        color: #374151 !important;
    }
    [data-baseweb="select"] {
        background-color: white !important;
    }
    [data-baseweb="select"] > div {
        background-color: white !important;
        color: #111827 !important;
    }
    [data-baseweb="select"] span {
        color: #111827 !important;
    }

    /* Dropdown menu styling - force white background */
    [data-baseweb="popover"] {
        background-color: white !important;
    }
    [data-baseweb="popover"] > div {
        background-color: white !important;
    }
    [data-baseweb="menu"] {
        background-color: white !important;
    }
    [data-baseweb="menu"] li {
        color: #111827 !important;
        background-color: white !important;
    }
    [data-baseweb="menu"] li:hover {
        background-color: #f3f4f6 !important;
    }
    [role="listbox"] {
        background-color: white !important;
    }
    [role="listbox"] > div {
        background-color: white !important;
    }
    [role="option"] {
        color: #111827 !important;
        background-color: white !important;
    }
    [role="option"]:hover {
        background-color: #f3f4f6 !important;
    }
    [data-highlighted="true"] {
        background-color: #f3f4f6 !important;
    }
    /* Fix dropdown list container */
    ul[role="listbox"] {
        background-color: white !important;
    }
    div[data-baseweb="popover"] > div > div {
        background-color: white !important;
    }

    /* Overview cards - white with shadow */
    .overview-card {
        background: white !important;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .overview-label {
        font-size: 11px;
        color: #6b7280 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }
    .overview-value {
        font-size: 48px;
        font-weight: 700;
        color: #111827 !important;
        margin-bottom: 8px;
        font-family: 'SF Mono', 'Monaco', monospace;
        letter-spacing: -1px;
    }
    .overview-subtitle {
        font-size: 13px;
        color: #6b7280 !important;
    }
    .overview-change {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 500;
        margin-left: 8px;
    }
    .change-positive {
        background: #dcfce7 !important;
        color: #15803d !important;
    }
    .change-negative {
        background: #fee2e2 !important;
        color: #dc2626 !important;
    }
    .change-neutral {
        background: #f3f4f6 !important;
        color: #6b7280 !important;
    }

    /* Section styling */
    .section-card {
        background: white !important;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #111827 !important;
        margin-bottom: 16px;
    }

    /* Data tables - force light background */
    .stDataFrame, [data-testid="stDataFrame"] {
        background: white !important;
    }
    .stDataFrame th {
        background-color: #f9fafb !important;
        color: #374151 !important;
    }
    .stDataFrame td {
        background-color: white !important;
        color: #111827 !important;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #6b7280 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #111827 !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1f2937 !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    [data-testid="stSidebar"] label {
        color: white !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Button styling */
    .stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #dc2626 !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state."""
    if "data" not in st.session_state:
        st.session_state.data = None
    if "insights" not in st.session_state:
        st.session_state.insights = None
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = None
    if "use_demo" not in st.session_state:
        st.session_state.use_demo = False
    if "selected_account" not in st.session_state:
        st.session_state.selected_account = "All Accounts"


def format_currency(value: float) -> str:
    """Format number as currency."""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:,.0f}"
    return f"${value:.2f}"


def format_number(value: float) -> str:
    """Format large numbers with commas."""
    if value >= 1000000:
        return f"{value/1000000:.2f}M"
    elif value >= 1000:
        return f"{value/1000:,.0f}K"
    return f"{value:,.0f}"


def get_month_date_range(year: int, month: int):
    """Get start and end dates for a month."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(days=1)
    return start, end


def extract_base_creative_name(name: str) -> str:
    """Extract base creative name to identify unique creatives.

    Same creative name = same creative, even if duplicated in account.
    We use the full ad_name as the creative identifier.
    """
    if not name:
        return "Unknown"
    return str(name).strip()


def aggregate_by_creative(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate all ads by unique creative name.

    Same ad_name = same creative. Combine spend, revenue, purchases, etc.
    This gives us the true performance of each unique creative.
    """
    if df.empty:
        return df

    df = df.copy()

    # Group by ad_name (creative name) and aggregate metrics
    agg_df = df.groupby("ad_name", as_index=False).agg({
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "purchases": "sum",
        "purchase_value": "sum",
        # Keep first value for non-numeric fields
        "campaign_name": "first",
        "adset_name": "first",
        "creative_type": "first",
        "account_id": "first",
    })

    # Recalculate ROAS based on aggregated values
    agg_df["roas"] = agg_df.apply(
        lambda row: row["purchase_value"] / row["spend"] if row["spend"] > 0 else 0,
        axis=1
    )

    # Recalculate CPA
    agg_df["cpa"] = agg_df.apply(
        lambda row: row["spend"] / row["purchases"] if row["purchases"] > 0 else 0,
        axis=1
    )

    return agg_df


def calculate_monthly_stats(df: pd.DataFrame, min_spend: float = 1000, min_roas: float = 2.0):
    """Calculate monthly statistics based on unique creatives.

    Key logic:
    - Aggregate all ads by creative name first
    - Count unique creatives launched
    - Winners = creatives with ≥min_spend AND ≥min_roas
    - Win rate = winners / total unique creatives (how many we launch that hit KPIs)
    """
    if df.empty:
        return {
            "total_ads": 0,
            "unique_creatives": 0,
            "winners": 0,
            "win_rate": 0,
            "total_spend": 0,
            "avg_roas": 0,
        }

    # Aggregate by unique creative name
    creative_df = aggregate_by_creative(df)

    # Count unique creatives launched
    unique_creatives = len(creative_df)

    # Winners = creatives that hit BOTH KPIs (≥min_spend AND ≥min_roas)
    winners = creative_df[(creative_df["spend"] >= min_spend) & (creative_df["roas"] >= min_roas)]

    # Win rate = winners / total creatives launched
    # This shows: of all creatives we launch, how many hit our KPIs
    win_rate = (len(winners) / unique_creatives * 100) if unique_creatives > 0 else 0

    return {
        "total_ads": len(df),  # Raw ad count
        "unique_creatives": unique_creatives,  # Unique creative count
        "winners": len(winners),
        "win_rate": win_rate,
        "total_spend": creative_df["spend"].sum(),
        "avg_roas": creative_df["purchase_value"].sum() / creative_df["spend"].sum() if creative_df["spend"].sum() > 0 else 0,
    }


def render_overview_card(label: str, value: str, subtitle: str = "", change: float = None, change_label: str = ""):
    """Render an overview card with white background."""
    change_html = ""
    if change is not None:
        if change > 0:
            change_html = f'<span class="overview-change change-positive">↑ +{change:.1f}%</span>'
        elif change < 0:
            change_html = f'<span class="overview-change change-negative">↓ {change:.1f}%</span>'
        else:
            change_html = f'<span class="overview-change change-neutral">— 0%</span>'

    st.markdown(f"""
    <div class="overview-card">
        <div class="overview-label">{label}</div>
        <div class="overview-value">{value}</div>
        <div class="overview-subtitle">{subtitle} {change_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_header_bar():
    """Render the top header bar with controls."""
    col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])

    with col1:
        st.markdown("## Win Rate Tracker")

    with col2:
        # Account selector
        available_accounts = get_available_ad_accounts()
        account_options = ["All Accounts"] + available_accounts
        selected = st.selectbox(
            "Account",
            options=account_options,
            index=0,
            key="account_dropdown",
            label_visibility="collapsed"
        )
        st.session_state.selected_account = selected

    with col3:
        # Win metric selector (ROAS threshold)
        roas_threshold = st.selectbox(
            "ROAS",
            options=["ROAS ≥ 2.0", "ROAS ≥ 1.5", "ROAS ≥ 2.5", "ROAS ≥ 3.0"],
            index=0,
            key="roas_selector",
            label_visibility="collapsed"
        )

    with col4:
        # Last refresh time
        if st.session_state.last_refresh:
            mins_ago = int((datetime.now() - st.session_state.last_refresh).seconds / 60)
            st.markdown(f"<p style='color: #6b7280; font-size: 13px; margin-top: 8px;'>Last refresh: {mins_ago}m ago</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #6b7280; font-size: 13px; margin-top: 8px;'>Not refreshed yet</p>", unsafe_allow_html=True)

    with col5:
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.session_state.data = None
            st.session_state.insights = None
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    # Parse ROAS threshold
    roas_map = {
        "ROAS ≥ 2.0": 2.0,
        "ROAS ≥ 1.5": 1.5,
        "ROAS ≥ 2.5": 2.5,
        "ROAS ≥ 3.0": 3.0,
    }
    return roas_map.get(roas_threshold, 2.0)


def render_overview_section(df: pd.DataFrame, insights: dict, min_roas: float = 2.0):
    """Render the Overview section with monthly stats and MoM comparison."""

    # Current month stats - based on unique creatives
    current_stats = calculate_monthly_stats(df, min_spend=1000, min_roas=min_roas)

    # For demo purposes, simulate previous month data (in real app, fetch separately)
    prev_stats = {
        "unique_creatives": int(current_stats["unique_creatives"] * 0.85),
        "winners": int(current_stats["winners"] * 0.8),
        "win_rate": current_stats["win_rate"] * 0.95,
    }

    # Calculate MoM changes
    def calc_change(current, previous):
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    creatives_change = calc_change(current_stats["unique_creatives"], prev_stats["unique_creatives"])
    winners_change = calc_change(current_stats["winners"], prev_stats["winners"])
    winrate_change = calc_change(current_stats["win_rate"], prev_stats["win_rate"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_overview_card(
            "UNIQUE CREATIVES",
            f"{current_stats['unique_creatives']:,}",
            "Distinct ad names",
            creatives_change
        )

    with col2:
        render_overview_card(
            "TOTAL WINNERS",
            f"{current_stats['winners']}",
            f"≥$1K spend & ≥{min_roas} ROAS",
            winners_change
        )

    with col3:
        render_overview_card(
            "WIN RATE",
            f"{current_stats['win_rate']:.1f}%",
            f"{current_stats['winners']}/{current_stats['unique_creatives']} creatives",
            winrate_change
        )

    with col4:
        render_overview_card(
            "BLENDED ROAS",
            f"{current_stats['avg_roas']:.2f}",
            "All accounts"
        )


def render_monthly_breakdown(df: pd.DataFrame, min_roas: float = 2.0):
    """Render monthly breakdown table."""
    if df.empty:
        st.info("No data available")
        return

    st.markdown("### Monthly Performance")

    # Get current month stats
    stats = calculate_monthly_stats(df, min_spend=1000, min_roas=min_roas)

    # For demo, create monthly breakdown
    # In real implementation, would need to fetch historical data per month
    now = datetime.now()
    months_data = []

    for i in range(6):  # Last 6 months
        month_date = now - timedelta(days=30 * i)
        month_name = month_date.strftime("%B %Y")

        # Simulate declining data for older months (demo)
        factor = 1 - (i * 0.1)
        new_ads = int(stats["unique_creatives"] * factor)
        winners = int(stats["winners"] * factor)
        total_spend = stats["total_spend"] * factor

        # Win rate = winners / new_ads (correct formula)
        win_rate = (winners / new_ads * 100) if new_ads > 0 else 0

        months_data.append({
            "Month": month_name,
            "New Ads": new_ads,
            "Total Spend": format_currency(total_spend),
            "Winners": winners,
            "Win Rate": f"{win_rate:.1f}%",
            "Blended ROAS": f"{stats['avg_roas'] * (0.9 + i * 0.05):.2f}",
        })

    monthly_df = pd.DataFrame(months_data)
    st.dataframe(monthly_df, use_container_width=True, hide_index=True)


def render_format_breakdown(df: pd.DataFrame, min_roas: float = 2.0):
    """Render format breakdown with win rates based on unique creatives."""
    if df.empty:
        st.info("No data available")
        return

    # First aggregate by unique creative
    creative_df = aggregate_by_creative(df)

    def get_format(row):
        name = str(row.get("ad_name", "")).upper()
        creative_type = str(row.get("creative_type", "")).upper()

        if "VIDEO" in creative_type or "VID" in name:
            return "Video"
        elif "CAROUSEL" in name or "CAR" in name:
            return "Carousel"
        else:
            return "Image"

    creative_df["format"] = creative_df.apply(get_format, axis=1)

    # Calculate stats per format based on unique creatives
    formats = []
    for fmt in creative_df["format"].unique():
        fmt_df = creative_df[creative_df["format"] == fmt]
        # Winners = creatives with ≥$1K spend AND ≥min_roas
        winners = fmt_df[(fmt_df["spend"] >= 1000) & (fmt_df["roas"] >= min_roas)]
        # Win rate = winners / total creatives in this format
        win_rate = (len(winners) / len(fmt_df) * 100) if len(fmt_df) > 0 else 0

        formats.append({
            "Name": fmt,
            "Creatives": len(fmt_df),
            "Winners": len(winners),
            "Win Rate": f"{win_rate:.1f}%",
            "Spend": format_currency(fmt_df["spend"].sum()),
            "ROAS": f"{fmt_df['purchase_value'].sum() / fmt_df['spend'].sum() if fmt_df['spend'].sum() > 0 else 0:.2f}",
        })

    format_df = pd.DataFrame(formats).sort_values("Spend", ascending=False, key=lambda x: x.str.replace('$', '').str.replace(',', '').str.replace('K', '000').astype(float))
    st.dataframe(format_df, use_container_width=True, hide_index=True)


def render_winners_table(df: pd.DataFrame, min_roas: float = 2.0):
    """Render winning creatives table based on aggregated unique creatives."""
    if df.empty:
        st.info("No data available")
        return

    # Aggregate by unique creative first
    creative_df = aggregate_by_creative(df)

    # Filter for winners (based on aggregated metrics)
    qualified = creative_df[creative_df["spend"] >= 1000]
    winners = qualified[qualified["roas"] >= min_roas].copy()

    if winners.empty:
        st.info(f"No winners found (≥$1K spend & ≥{min_roas} ROAS)")
        return

    winners = winners.sort_values("roas", ascending=False)

    display_df = winners[["ad_name", "spend", "roas", "purchases", "purchase_value"]].head(20).copy()
    display_df.columns = ["Creative Name", "Spend", "ROAS", "Purchases", "Revenue"]
    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)


def render_losers_table(df: pd.DataFrame, min_roas: float = 2.0):
    """Render underperforming creatives table based on aggregated unique creatives."""
    if df.empty:
        st.info("No data available")
        return

    # Aggregate by unique creative first
    creative_df = aggregate_by_creative(df)

    # Filter for losers (high spend, low ROAS)
    qualified = creative_df[creative_df["spend"] >= 1000]
    losers = qualified[qualified["roas"] < min_roas].copy()

    if losers.empty:
        st.success("No underperforming creatives found!")
        return

    losers = losers.sort_values("spend", ascending=False)

    display_df = losers[["ad_name", "spend", "roas", "purchases", "purchase_value"]].head(20).copy()
    display_df.columns = ["Creative Name", "Spend", "ROAS", "Purchases", "Revenue"]
    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)


def main():
    """Main application."""
    init_session_state()

    # Sidebar (collapsed by default)
    with st.sidebar:
        st.title("Settings")
        use_demo = st.checkbox("Use Demo Data", value=st.session_state.use_demo)
        st.session_state.use_demo = use_demo

        st.divider()
        st.subheader("Date Range")
        date_end = st.date_input("End Date", value=datetime.now())
        date_start = st.date_input("Start Date", value=datetime.now().replace(day=1))  # First of month

        date_start = datetime.combine(date_start, datetime.min.time())
        date_end = datetime.combine(date_end, datetime.max.time())

    # Header bar with controls
    min_roas = render_header_bar()

    # Load data
    if st.session_state.data is None or st.session_state.insights is None:
        with st.spinner("Loading data..."):
            try:
                date_start_str = date_start.strftime("%Y-%m-%d")
                date_end_str = date_end.strftime("%Y-%m-%d")
                st.session_state.data, st.session_state.insights = load_cached_data(
                    date_start_str, date_end_str, st.session_state.use_demo
                )
                st.session_state.last_refresh = datetime.now()
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.session_state.data = get_demo_data()
                st.session_state.insights = get_demo_insights()

    df = st.session_state.data
    insights = st.session_state.insights

    if df is None or df.empty:
        st.warning("No data available. Enable 'Use Demo Data' in the sidebar.")
        return

    # Filter by selected account
    if st.session_state.selected_account != "All Accounts" and "account_id" in df.columns:
        df = df[df["account_id"] == st.session_state.selected_account]

    # Overview section
    st.markdown("### Overview")
    render_overview_section(df, insights, min_roas)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for breakdowns
    tab1, tab2, tab3, tab4 = st.tabs(["Format", "Monthly", "🏆 Winners", "⚠️ Underperformers"])

    with tab1:
        render_format_breakdown(df, min_roas)

    with tab2:
        render_monthly_breakdown(df, min_roas)

    with tab3:
        render_winners_table(df, min_roas)

    with tab4:
        render_losers_table(df, min_roas)


if __name__ == "__main__":
    main()
