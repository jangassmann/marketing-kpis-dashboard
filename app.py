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

# Page configuration
st.set_page_config(
    page_title="Creative Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for the new design
st.markdown("""
<style>
    /* Main layout */
    .main > div {
        padding-top: 1rem;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 12px;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 2px;
    }
    .metric-change-positive {
        color: #10b981;
        font-size: 13px;
        font-weight: 500;
    }
    .metric-change-negative {
        color: #ef4444;
        font-size: 13px;
        font-weight: 500;
    }

    /* Creative cards */
    .creative-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 16px;
    }
    .creative-thumbnail {
        width: 100%;
        height: 180px;
        object-fit: cover;
        background: #f3f4f6;
    }
    .creative-info {
        padding: 12px;
    }
    .creative-name {
        font-size: 14px;
        font-weight: 500;
        color: #111827;
        margin-bottom: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .creative-metric {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        margin-bottom: 4px;
    }
    .creative-metric-label {
        color: #6b7280;
    }
    .creative-metric-value {
        font-weight: 600;
        color: #111827;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
    }
    .badge-image {
        background: #dbeafe;
        color: #1d4ed8;
    }
    .badge-video {
        background: #dcfce7;
        color: #15803d;
    }

    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: #111827;
        margin: 24px 0 16px 0;
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


def format_currency(value: float) -> str:
    """Format number as currency."""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.2f}K"
    return f"${value:.2f}"


def format_number(value: float) -> str:
    """Format large numbers."""
    if value >= 1000000:
        return f"{value/1000000:.2f}M"
    elif value >= 1000:
        return f"{value/1000:.2f}K"
    return f"{value:.0f}"


def render_metric_card(label: str, value: str, change: float = None, prefix: str = ""):
    """Render a metric card with optional change indicator."""
    change_html = ""
    if change is not None:
        change_class = "metric-change-positive" if change >= 0 else "metric-change-negative"
        change_sign = "+" if change >= 0 else ""
        change_html = f'<span class="{change_class}">{change_sign}{change:.2f}%</span>'

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value} {change_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_key_metrics(insights: dict, prev_insights: dict = None):
    """Render the key metrics section."""
    col1, col2, col3, col4 = st.columns(4)

    # Calculate changes if previous period data available
    def calc_change(current, previous, key):
        if previous and previous.get(key, 0) > 0:
            return ((current.get(key, 0) - previous.get(key, 0)) / previous.get(key, 0)) * 100
        return None

    with col1:
        render_metric_card(
            "Spend",
            format_currency(insights.get("spend", 0)),
            calc_change(insights, prev_insights, "spend")
        )

    with col2:
        render_metric_card(
            "ROAS",
            f"{insights.get('roas', 0):.2f}",
            calc_change(insights, prev_insights, "roas")
        )

    with col3:
        render_metric_card(
            "CPA",
            format_currency(insights.get("cpa", 0)),
            calc_change(insights, prev_insights, "cpa")
        )

    with col4:
        render_metric_card(
            "Purchase Value",
            format_currency(insights.get("purchase_value", 0)),
            calc_change(insights, prev_insights, "purchase_value")
        )

    # Second row
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        render_metric_card(
            "AOV",
            format_currency(insights.get("aov", 0)),
            calc_change(insights, prev_insights, "aov")
        )

    with col6:
        render_metric_card(
            "CPC (all)",
            format_currency(insights.get("cpc", 0)),
            calc_change(insights, prev_insights, "cpc")
        )

    with col7:
        render_metric_card(
            "CPC (link click)",
            format_currency(insights.get("cpc", 0) * 1.25),  # Approximation
            None
        )

    with col8:
        render_metric_card(
            "CPM",
            format_currency(insights.get("cpm", 0)),
            calc_change(insights, prev_insights, "cpm")
        )


def group_by_creative_name(df: pd.DataFrame) -> pd.DataFrame:
    """Group ads by creative name to handle duplicates."""
    if df.empty:
        return df

    # Extract base creative name (remove suffix numbers, copies, etc.)
    def extract_base_name(name):
        if not name:
            return "Unknown"
        # Remove common suffixes like _1, _2, - Copy, etc.
        import re
        base = re.sub(r'(_\d+|_copy|\s*-\s*copy\s*\d*|\s+\d+)$', '', name, flags=re.IGNORECASE)
        return base.strip()

    df = df.copy()
    df["creative_base_name"] = df["ad_name"].apply(extract_base_name)

    # Group by base name
    grouped = df.groupby("creative_base_name").agg({
        "ad_id": "first",
        "ad_name": "first",
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "purchases": "sum",
        "purchase_value": "sum",
        "thumbnail_url": "first",
        "creative_type": "first",
    }).reset_index()

    # Recalculate derived metrics
    grouped["roas"] = grouped.apply(
        lambda r: r["purchase_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )
    grouped["cpa"] = grouped.apply(
        lambda r: r["spend"] / r["purchases"] if r["purchases"] > 0 else 0, axis=1
    )

    return grouped


def render_top_spend_chart(df: pd.DataFrame):
    """Render the Top Spend bar chart with thumbnails."""
    st.markdown('<div class="section-header">Top Spend</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No data available")
        return

    # Group by creative and sort by spend
    grouped = group_by_creative_name(df)
    top_spend = grouped.nlargest(10, "spend")

    # Create dual-axis bar chart
    fig = go.Figure()

    # Spend bars
    fig.add_trace(go.Bar(
        name="Spend",
        x=top_spend["creative_base_name"],
        y=top_spend["spend"],
        marker_color="#818cf8",
        text=[f"${v/1000:.1f}K" for v in top_spend["spend"]],
        textposition="outside",
    ))

    # ROAS line
    fig.add_trace(go.Scatter(
        name="ROAS",
        x=top_spend["creative_base_name"],
        y=top_spend["roas"],
        mode="lines+markers+text",
        marker=dict(color="#5eead4", size=10),
        line=dict(color="#5eead4", width=2),
        text=[f"{v:.2f}" for v in top_spend["roas"]],
        textposition="top center",
        yaxis="y2",
    ))

    fig.update_layout(
        height=400,
        margin=dict(t=40, b=100, l=60, r=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickangle=45),
        yaxis=dict(title="Spend", side="left"),
        yaxis2=dict(title="ROAS", side="right", overlaying="y", range=[0, max(top_spend["roas"]) * 1.3]),
        plot_bgcolor="white",
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_performing_grid(df: pd.DataFrame):
    """Render the Top Performing creatives grid."""
    st.markdown('<div class="section-header">Top Performing</div>', unsafe_allow_html=True)

    # Tabs for different views
    tab1, tab2 = st.tabs(["By ROAS", "By Spend"])

    if df.empty:
        st.info("No data available")
        return

    grouped = group_by_creative_name(df)

    with tab1:
        # Filter for meaningful spend and sort by ROAS
        qualified = grouped[grouped["spend"] >= 100].nlargest(8, "roas")
        render_creative_grid(qualified)

    with tab2:
        # Sort by spend
        top_by_spend = grouped.nlargest(8, "spend")
        render_creative_grid(top_by_spend)


def render_creative_grid(df: pd.DataFrame):
    """Render a grid of creative cards."""
    if df.empty:
        st.info("No creatives match the criteria")
        return

    cols = st.columns(4)

    for idx, (_, row) in enumerate(df.iterrows()):
        with cols[idx % 4]:
            creative_type = row.get("creative_type", "IMAGE")
            badge_class = "badge-video" if "VIDEO" in str(creative_type).upper() else "badge-image"
            badge_text = "Video" if "VIDEO" in str(creative_type).upper() else "Image"

            thumbnail = row.get("thumbnail_url", "")
            if not thumbnail:
                thumbnail = "https://via.placeholder.com/300x200/f3f4f6/9ca3af?text=No+Preview"

            st.markdown(f"""
            <div class="creative-card">
                <img src="{thumbnail}" class="creative-thumbnail" onerror="this.src='https://via.placeholder.com/300x200/f3f4f6/9ca3af?text=No+Preview'">
                <div style="position: relative; margin-top: -30px; margin-left: 8px;">
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>
                <div class="creative-info">
                    <div class="creative-name">{row.get('creative_base_name', row.get('ad_name', 'Unknown'))}</div>
                    <div class="creative-metric">
                        <span class="creative-metric-label">ROAS</span>
                        <span class="creative-metric-value" style="color: #10b981;">{row.get('roas', 0):.2f}</span>
                    </div>
                    <div class="creative-metric">
                        <span class="creative-metric-label">Spend</span>
                        <span class="creative-metric-value">{format_currency(row.get('spend', 0))}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_header(date_start, date_end):
    """Render the page header."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("Creative Analytics")

    with col2:
        st.caption(f"📅 {date_start.strftime('%b %d')} - {date_end.strftime('%b %d, %Y')}")

    with col3:
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.data = None
            st.session_state.insights = None
            st.rerun()


def main():
    """Main application."""
    init_session_state()

    # Sidebar for settings
    with st.sidebar:
        st.title("Settings")

        # Demo mode toggle
        use_demo = st.checkbox("Use Demo Data", value=st.session_state.use_demo)
        st.session_state.use_demo = use_demo

        st.divider()

        # Date range picker
        st.subheader("Date Range")
        date_end = st.date_input("End Date", value=datetime.now())
        date_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=14))

        # Convert to datetime
        date_start = datetime.combine(date_start, datetime.min.time())
        date_end = datetime.combine(date_end, datetime.max.time())

        st.divider()

        # Minimum spend filter
        st.subheader("Filters")
        min_spend = st.number_input("Min Spend for Top Performing", value=100, step=50)

    # Header
    render_header(date_start, date_end)

    # Load data
    if st.session_state.data is None or st.session_state.insights is None:
        with st.spinner("Loading data from all accounts..."):
            if st.session_state.use_demo:
                st.session_state.data = get_demo_data()
                st.session_state.insights = get_demo_insights()
            else:
                try:
                    st.session_state.data = fetch_all_accounts_data(date_start, date_end)
                    st.session_state.insights = fetch_all_accounts_insights(date_start, date_end)
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

    # Key Metrics Section
    st.markdown("### Key Metrics")
    render_key_metrics(insights)

    st.divider()

    # Top Spend Chart
    render_top_spend_chart(df)

    st.divider()

    # Top Performing Grid
    render_top_performing_grid(df)

    st.divider()

    # Data Table
    with st.expander("View All Creatives Data"):
        grouped = group_by_creative_name(df)
        display_df = grouped[[
            "creative_base_name", "spend", "roas", "purchases", "purchase_value", "cpa"
        ]].copy()
        display_df.columns = ["Creative", "Spend", "ROAS", "Purchases", "Revenue", "CPA"]
        display_df = display_df.sort_values("Spend", ascending=False)

        # Format columns
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
        display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
