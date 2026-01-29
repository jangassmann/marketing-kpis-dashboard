"""
Creative Analytics Dashboard
Track ad creative performance across multiple Meta ad accounts.
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
    initial_sidebar_state="expanded",
)

# Custom CSS for the new design
st.markdown("""
<style>
    /* Main layout */
    .main > div {
        padding-top: 1rem;
    }

    /* Overview cards */
    .overview-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 24px;
        height: 100%;
    }
    .overview-label {
        font-size: 12px;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .overview-value {
        font-size: 42px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
        font-family: monospace;
    }
    .overview-subtitle {
        font-size: 13px;
        color: #6b7280;
    }
    .overview-change-positive {
        color: #10b981;
        font-size: 13px;
        font-weight: 500;
    }
    .overview-change-negative {
        color: #ef4444;
        font-size: 13px;
        font-weight: 500;
    }

    /* Win rate badge */
    .win-rate-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }
    .win-rate-high {
        background: #dcfce7;
        color: #15803d;
    }
    .win-rate-medium {
        background: #fef3c7;
        color: #b45309;
    }
    .win-rate-low {
        background: #fee2e2;
        color: #dc2626;
    }

    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #111827;
        margin: 24px 0 16px 0;
    }

    /* Refresh button */
    .refresh-btn {
        background: #6366f1;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
    }

    /* Filter pills */
    .filter-pill {
        display: inline-block;
        padding: 8px 16px;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-right: 8px;
        font-size: 14px;
        cursor: pointer;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
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
    if "selected_accounts" not in st.session_state:
        st.session_state.selected_accounts = []


def format_currency(value: float) -> str:
    """Format number as currency."""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.1f}K"
    return f"${value:.2f}"


def format_number(value: float) -> str:
    """Format large numbers."""
    if value >= 1000000:
        return f"{value/1000000:.2f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"
    return f"{value:,.0f}"


def extract_creative_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Extract format, funnel, angle from creative names."""
    if df.empty:
        return df

    df = df.copy()

    # Extract format (IMG, VID, etc.)
    def get_format(name):
        name_upper = str(name).upper()
        if "VID" in name_upper or "VIDEO" in name_upper:
            return "Video"
        elif "IMG" in name_upper or "IMAGE" in name_upper:
            return "Image"
        elif "CAR" in name_upper or "CAROUSEL" in name_upper:
            return "Carousel"
        else:
            # Check creative_type column
            return "Other"

    # Extract funnel stage (TOF, MOF, BOF)
    def get_funnel(name):
        name_upper = str(name).upper()
        if "TOF" in name_upper or "PROSPECTING" in name_upper:
            return "TOF"
        elif "MOF" in name_upper:
            return "MOF"
        elif "BOF" in name_upper or "RETARGET" in name_upper:
            return "BOF"
        return "Unknown"

    # Extract angle/hook
    def get_angle(name):
        name_upper = str(name).upper()
        patterns = {
            "B1G1": "BOGO",
            "BOGO": "BOGO",
            "DISCOUNT": "Discount",
            "FREE": "Free Shipping",
            "SALE": "Sale",
            "UGC": "UGC",
            "TESTIMONIAL": "Testimonial",
            "PROBLEM": "Problem/Solution",
            "LIFESTYLE": "Lifestyle",
        }
        for pattern, angle in patterns.items():
            if pattern in name_upper:
                return angle
        return "Other"

    df["format"] = df["ad_name"].apply(get_format)
    # Override with creative_type if available
    if "creative_type" in df.columns:
        df["format"] = df.apply(
            lambda r: "Video" if "VIDEO" in str(r.get("creative_type", "")).upper()
            else ("Image" if "IMAGE" in str(r.get("creative_type", "")).upper() else r["format"]),
            axis=1
        )

    df["funnel"] = df["ad_name"].apply(get_funnel)
    df["angle"] = df["ad_name"].apply(get_angle)

    # Extract launch month from campaign name or use current
    df["launch_month"] = datetime.now().strftime("%Y-%m")

    return df


def calculate_winners(df: pd.DataFrame, min_spend: float = 1000, min_roas: float = 2.0) -> pd.DataFrame:
    """Mark winners based on spend and ROAS criteria."""
    if df.empty:
        return df

    df = df.copy()
    df["is_winner"] = (df["spend"] >= min_spend) & (df["roas"] >= min_roas)
    return df


def render_overview_card(label: str, value: str, subtitle: str = "", change: float = None):
    """Render an overview card."""
    change_html = ""
    if change is not None:
        if change >= 0:
            change_html = f'<span class="overview-change-positive">↑ +{change:.1f}%</span>'
        else:
            change_html = f'<span class="overview-change-negative">↓ {change:.1f}%</span>'

    st.markdown(f"""
    <div class="overview-card">
        <div class="overview-label">{label}</div>
        <div class="overview-value">{value}</div>
        <div class="overview-subtitle">{subtitle} {change_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_overview_section(df: pd.DataFrame, insights: dict):
    """Render the Overview section with key metrics."""
    # Calculate metrics
    df_with_winners = calculate_winners(df)
    total_ads = len(df_with_winners)
    total_winners = df_with_winners["is_winner"].sum()
    win_rate = (total_winners / total_ads * 100) if total_ads > 0 else 0
    blended_roas = insights.get("roas", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_overview_card(
            "TOTAL ADS",
            format_number(total_ads),
            "Active campaigns"
        )

    with col2:
        render_overview_card(
            "TOTAL WINNERS",
            format_number(total_winners),
            "≥$1K spend & ≥2.0 ROAS"
        )

    with col3:
        render_overview_card(
            "WIN RATE",
            f"{win_rate:.1f}%",
            "Last 30 days"
        )

    with col4:
        render_overview_card(
            "BLENDED ROAS",
            f"{blended_roas:.2f}",
            "All accounts"
        )


def render_key_metrics_bar(insights: dict):
    """Render a simple metrics bar: Total Spend, Avg CPA, Avg ROAS."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Spend", format_currency(insights.get("spend", 0)))

    with col2:
        st.metric("Avg CPA", format_currency(insights.get("cpa", 0)))

    with col3:
        st.metric("Avg ROAS", f"{insights.get('roas', 0):.2f}")

    with col4:
        st.metric("Purchases", format_number(insights.get("purchases", 0)))


def render_breakdown_table(df: pd.DataFrame, group_by: str, title: str):
    """Render a breakdown table grouped by a specific attribute."""
    if df.empty:
        st.info("No data available")
        return

    df_with_winners = calculate_winners(df)

    # Group by the specified column
    grouped = df_with_winners.groupby(group_by).agg({
        "ad_id": "count",
        "is_winner": "sum",
        "spend": "sum",
        "roas": "mean",
        "purchases": "sum",
        "purchase_value": "sum",
    }).reset_index()

    grouped.columns = [group_by, "total_ads", "winners", "spend", "roas", "purchases", "revenue"]

    # Calculate win rate
    grouped["win_rate"] = grouped.apply(
        lambda r: (r["winners"] / r["total_ads"] * 100) if r["total_ads"] > 0 else 0, axis=1
    )

    # Recalculate ROAS from aggregated values
    grouped["roas"] = grouped.apply(
        lambda r: r["revenue"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )

    # Sort by spend
    grouped = grouped.sort_values("spend", ascending=False)

    # Create display dataframe
    display_df = grouped[[group_by, "total_ads", "winners", "win_rate", "spend", "roas"]].copy()
    display_df.columns = ["Name", "Total Ads", "Winners", "Win Rate", "Spend", "ROAS"]

    # Format columns
    display_df["Win Rate"] = display_df["Win Rate"].apply(lambda x: f"{x:.1f}%")
    display_df["Spend"] = display_df["Spend"].apply(lambda x: format_currency(x))
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")

    st.markdown(f"### {title}")
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)


def render_format_breakdown(df: pd.DataFrame):
    """Render Format breakdown (Video, Image, Carousel)."""
    render_breakdown_table(df, "format", "Format Breakdown")


def render_funnel_breakdown(df: pd.DataFrame):
    """Render Funnel breakdown (TOF, MOF, BOF)."""
    render_breakdown_table(df, "funnel", "Funnel Breakdown")


def render_angle_breakdown(df: pd.DataFrame):
    """Render Angle breakdown."""
    render_breakdown_table(df, "angle", "Angle Breakdown")


def render_monthly_breakdown(df: pd.DataFrame):
    """Render Monthly breakdown."""
    render_breakdown_table(df, "launch_month", "Monthly Breakdown")


def render_creative_analysis_tab(df: pd.DataFrame):
    """Render the Creative Analysis tab with hit rate details."""
    if df.empty:
        st.info("No data available")
        return

    df_with_winners = calculate_winners(df)

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    total_ads = len(df_with_winners)
    total_winners = df_with_winners["is_winner"].sum()
    win_rate = (total_winners / total_ads * 100) if total_ads > 0 else 0

    # Ads with significant spend
    qualified_ads = df_with_winners[df_with_winners["spend"] >= 1000]
    qualified_count = len(qualified_ads)
    qualified_winners = qualified_ads["is_winner"].sum()

    with col1:
        st.metric("Total Ads Launched", total_ads)

    with col2:
        st.metric("Ads with ≥$1K Spend", qualified_count)

    with col3:
        st.metric("Winners (≥$1K & ≥2.0 ROAS)", int(total_winners))

    with col4:
        st.metric("Hit Rate", f"{win_rate:.1f}%")

    st.divider()

    # Winners table
    st.markdown("### 🏆 Winning Creatives")

    if total_winners > 0:
        winners_df = df_with_winners[df_with_winners["is_winner"]].sort_values("roas", ascending=False)
        display_cols = ["ad_name", "spend", "roas", "purchases", "purchase_value", "cpa"]
        available_cols = [c for c in display_cols if c in winners_df.columns]
        display_df = winners_df[available_cols].copy()

        display_df.columns = ["Ad Name", "Spend", "ROAS", "Purchases", "Revenue", "CPA"]
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
        display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No winners found with current criteria (≥$1K spend & ≥2.0 ROAS)")

    st.divider()

    # Losers / underperformers
    st.markdown("### ⚠️ Underperforming Creatives (≥$1K spend, <2.0 ROAS)")

    losers = df_with_winners[(df_with_winners["spend"] >= 1000) & (df_with_winners["roas"] < 2.0)]
    if len(losers) > 0:
        losers_sorted = losers.sort_values("spend", ascending=False)
        display_cols = ["ad_name", "spend", "roas", "purchases", "purchase_value", "cpa"]
        available_cols = [c for c in display_cols if c in losers_sorted.columns]
        display_df = losers_sorted[available_cols].copy()

        display_df.columns = ["Ad Name", "Spend", "ROAS", "Purchases", "Revenue", "CPA"]
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
        display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.success("No underperforming ads found!")


def render_data_tab(df: pd.DataFrame):
    """Render the Data tab with all ads."""
    if df.empty:
        st.info("No data available")
        return

    # Sort by spend
    sorted_df = df.sort_values("spend", ascending=False)

    # Display columns
    display_cols = ["ad_name", "campaign_name", "format", "funnel", "spend", "roas", "purchases", "cpa"]
    available_cols = [c for c in display_cols if c in sorted_df.columns]
    display_df = sorted_df[available_cols].copy()

    col_names = {
        "ad_name": "Ad Name",
        "campaign_name": "Campaign",
        "format": "Format",
        "funnel": "Funnel",
        "spend": "Spend",
        "roas": "ROAS",
        "purchases": "Purchases",
        "cpa": "CPA",
    }
    display_df.rename(columns={k: v for k, v in col_names.items() if k in display_df.columns}, inplace=True)

    if "Spend" in display_df.columns:
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    if "ROAS" in display_df.columns:
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    if "CPA" in display_df.columns:
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)


def main():
    """Main application."""
    init_session_state()

    # Header
    col_title, col_refresh = st.columns([3, 1])
    with col_title:
        st.title("Win Rate Tracker")
    with col_refresh:
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.data = None
            st.session_state.insights = None
            st.rerun()

    # Sidebar filters
    with st.sidebar:
        st.title("Filters")

        # Demo mode toggle
        use_demo = st.checkbox("Use Demo Data", value=st.session_state.use_demo)
        st.session_state.use_demo = use_demo

        st.divider()

        # Account selector
        st.subheader("Ad Accounts")
        available_accounts = get_available_ad_accounts()
        if available_accounts:
            selected_accounts = st.multiselect(
                "Select Accounts",
                options=available_accounts,
                default=available_accounts,
                key="account_select"
            )
            st.session_state.selected_accounts = selected_accounts
        else:
            st.info("No accounts configured")
            st.session_state.selected_accounts = []

        st.divider()

        # Date range picker
        st.subheader("Date Range")
        date_end = st.date_input("End Date", value=datetime.now())
        date_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))

        # Convert to datetime
        date_start = datetime.combine(date_start, datetime.min.time())
        date_end = datetime.combine(date_end, datetime.max.time())

        st.divider()

        # Win criteria (display only)
        st.subheader("Win Criteria")
        st.info("**Winner** = ≥$1,000 spend AND ≥2.0 ROAS")

    # Load data (cached for 10 minutes)
    if st.session_state.data is None or st.session_state.insights is None:
        with st.spinner("Loading data..."):
            try:
                date_start_str = date_start.strftime("%Y-%m-%d")
                date_end_str = date_end.strftime("%Y-%m-%d")
                st.session_state.data, st.session_state.insights = load_cached_data(
                    date_start_str, date_end_str, st.session_state.use_demo
                )
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.info("Switching to demo data...")
                st.session_state.data = get_demo_data()
                st.session_state.insights = get_demo_insights()

    df = st.session_state.data
    insights = st.session_state.insights

    if df is None or df.empty:
        st.warning("No data available. Enable 'Use Demo Data' in the sidebar to see a preview.")
        return

    # Extract creative attributes
    df = extract_creative_attributes(df)

    # Filter by selected accounts
    if st.session_state.selected_accounts and "account_id" in df.columns:
        df = df[df["account_id"].isin(st.session_state.selected_accounts)]

    # Key metrics bar
    render_key_metrics_bar(insights)

    st.divider()

    # Main tabs: Data and Creative Analysis
    main_tab1, main_tab2 = st.tabs(["📊 Data & Breakdowns", "🎯 Creative Analysis"])

    with main_tab1:
        # Overview section
        st.markdown("## Overview")
        render_overview_section(df, insights)

        st.divider()

        # Breakdown tabs
        st.markdown("## Breakdowns")
        breakdown_tabs = st.tabs(["Format", "Funnel", "Angle", "Monthly"])

        with breakdown_tabs[0]:
            render_format_breakdown(df)

        with breakdown_tabs[1]:
            render_funnel_breakdown(df)

        with breakdown_tabs[2]:
            render_angle_breakdown(df)

        with breakdown_tabs[3]:
            render_monthly_breakdown(df)

        st.divider()

        # All ads table
        st.markdown("## All Ads")
        render_data_tab(df)

    with main_tab2:
        render_creative_analysis_tab(df)


if __name__ == "__main__":
    main()
