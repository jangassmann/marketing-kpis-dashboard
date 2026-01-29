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

    /* Hit rate card */
    .hit-rate-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin-bottom: 16px;
    }
    .hit-rate-title {
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .hit-rate-value {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .hit-rate-subtitle {
        font-size: 12px;
        opacity: 0.8;
    }

    /* Data table styling */
    .data-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #e5e7eb;
    }
    .data-row:hover {
        background: #f9fafb;
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


def render_ads_tab(df: pd.DataFrame):
    """Render the Ads tab with all individual ads."""
    if df.empty:
        st.info("No ads data available")
        return

    # Sort by spend
    sorted_df = df.sort_values("spend", ascending=False)

    # Display as table
    display_cols = ["ad_name", "campaign_name", "spend", "roas", "purchases", "cpa", "impressions", "clicks"]
    available_cols = [c for c in display_cols if c in sorted_df.columns]
    display_df = sorted_df[available_cols].copy()

    # Rename columns
    col_names = {
        "ad_name": "Ad Name",
        "campaign_name": "Campaign",
        "spend": "Spend",
        "roas": "ROAS",
        "purchases": "Purchases",
        "cpa": "CPA",
        "impressions": "Impressions",
        "clicks": "Clicks",
    }
    display_df.rename(columns=col_names, inplace=True)

    # Format
    if "Spend" in display_df.columns:
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    if "ROAS" in display_df.columns:
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    if "CPA" in display_df.columns:
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")
    if "Impressions" in display_df.columns:
        display_df["Impressions"] = display_df["Impressions"].apply(lambda x: f"{x:,}")
    if "Clicks" in display_df.columns:
        display_df["Clicks"] = display_df["Clicks"].apply(lambda x: f"{x:,}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def render_creatives_tab(df: pd.DataFrame):
    """Render the Creatives tab - grouped by creative name."""
    if df.empty:
        st.info("No creatives data available")
        return

    grouped = group_by_creative_name(df)
    sorted_df = grouped.sort_values("spend", ascending=False)

    display_cols = ["creative_base_name", "spend", "roas", "purchases", "purchase_value", "cpa"]
    available_cols = [c for c in display_cols if c in sorted_df.columns]
    display_df = sorted_df[available_cols].copy()

    col_names = {
        "creative_base_name": "Creative",
        "spend": "Spend",
        "roas": "ROAS",
        "purchases": "Purchases",
        "purchase_value": "Revenue",
        "cpa": "CPA",
    }
    display_df.rename(columns=col_names, inplace=True)

    if "Spend" in display_df.columns:
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    if "Revenue" in display_df.columns:
        display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.2f}")
    if "ROAS" in display_df.columns:
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    if "CPA" in display_df.columns:
        display_df["CPA"] = display_df["CPA"].apply(lambda x: f"${x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def render_images_tab(df: pd.DataFrame):
    """Render the Images tab - only image creatives."""
    if df.empty:
        st.info("No data available")
        return

    # Filter for images only
    images_df = df[df["creative_type"].str.upper().str.contains("IMAGE", na=False)]

    if images_df.empty:
        st.info("No image creatives found")
        return

    grouped = group_by_creative_name(images_df)
    sorted_df = grouped.sort_values("spend", ascending=False).head(20)

    render_creative_grid(sorted_df)


def render_videos_tab(df: pd.DataFrame):
    """Render the Videos tab - only video creatives."""
    if df.empty:
        st.info("No data available")
        return

    # Filter for videos only
    videos_df = df[df["creative_type"].str.upper().str.contains("VIDEO", na=False)]

    if videos_df.empty:
        st.info("No video creatives found")
        return

    grouped = group_by_creative_name(videos_df)
    sorted_df = grouped.sort_values("spend", ascending=False).head(20)

    render_creative_grid(sorted_df)


def render_video_hooks_tab(df: pd.DataFrame):
    """Render the Video Hooks tab with video performance metrics."""
    if df.empty:
        st.info("No data available")
        return

    # Filter for videos only
    videos_df = df[df["creative_type"].str.upper().str.contains("VIDEO", na=False)].copy()

    if videos_df.empty:
        st.info("No video creatives found")
        return

    # Ensure video metric columns exist - NO fallbacks, show real data only
    for col in ["video_3s_views", "video_plays", "video_p25", "video_p50",
                "video_p75", "video_p100", "video_thruplay", "video_avg_time"]:
        if col not in videos_df.columns:
            videos_df[col] = 0

    # Calculate video metrics
    # Hook Rate = video plays / impressions (how many started watching)
    videos_df["hook_rate"] = videos_df.apply(
        lambda r: (r["video_plays"] / r["impressions"] * 100) if r["impressions"] > 0 else 0, axis=1
    )

    # Thumbstop % = 3-second views / impressions
    videos_df["thumbstop_pct"] = videos_df.apply(
        lambda r: (r["video_3s_views"] / r["impressions"] * 100) if r["impressions"] > 0 else 0, axis=1
    )

    # Hold Rate = 50% watched / 3-second views (retention after hook)
    videos_df["hold_rate"] = videos_df.apply(
        lambda r: (r["video_p50"] / r["video_3s_views"] * 100) if r["video_3s_views"] > 0 else 0, axis=1
    )

    # View Through Rate = ThruPlay / impressions
    videos_df["view_through_rate"] = videos_df.apply(
        lambda r: (r["video_thruplay"] / r["impressions"] * 100) if r["impressions"] > 0 else 0, axis=1
    )

    # Completion Rate = 100% watched / video plays
    videos_df["completion_rate"] = videos_df.apply(
        lambda r: (r["video_p100"] / r["video_plays"] * 100) if r["video_plays"] > 0 else 0, axis=1
    )

    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Thumbstop %", "Hook Rate", "Hold Rate", "View Through", "Avg Watch Time", "Spend"],
        key="video_sort"
    )

    sort_map = {
        "Thumbstop %": "thumbstop_pct",
        "Hook Rate": "hook_rate",
        "Hold Rate": "hold_rate",
        "View Through": "view_through_rate",
        "Avg Watch Time": "video_avg_time",
        "Spend": "spend",
    }
    sorted_df = videos_df.sort_values(sort_map[sort_by], ascending=False)

    # Build display dataframe
    display_df = sorted_df[[
        "ad_name", "hook_rate", "thumbstop_pct", "hold_rate",
        "view_through_rate", "video_avg_time", "spend", "roas"
    ]].copy()

    display_df.columns = [
        "Video", "Hook Rate", "Thumbstop %", "Hold Rate",
        "View Through", "Avg Watch (sec)", "Spend", "ROAS"
    ]

    # Format percentages
    display_df["Hook Rate"] = display_df["Hook Rate"].apply(lambda x: f"{x:.1f}%")
    display_df["Thumbstop %"] = display_df["Thumbstop %"].apply(lambda x: f"{x:.1f}%")
    display_df["Hold Rate"] = display_df["Hold Rate"].apply(lambda x: f"{x:.1f}%")
    display_df["View Through"] = display_df["View Through"].apply(lambda x: f"{x:.1f}%")
    display_df["Avg Watch (sec)"] = display_df["Avg Watch (sec)"].apply(lambda x: f"{x:.1f}s")
    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

    # Show data availability info
    has_video_data = videos_df["video_plays"].sum() > 0 or videos_df["video_3s_views"].sum() > 0
    if not has_video_data:
        st.warning("Video engagement metrics (plays, 3s views, etc.) are not available from Meta API for these ads. This can happen if the ads don't have video content or if the metrics aren't tracked.")

    # Add metric explanations
    with st.expander("Metric Definitions"):
        st.markdown("""
        - **Hook Rate**: % of impressions that started playing the video
        - **Thumbstop %**: % of impressions that watched at least 3 seconds
        - **Hold Rate**: % of 3-second viewers that watched to 50% (retention)
        - **View Through**: % of impressions that completed ThruPlay (15 sec or full video)
        - **Avg Watch (sec)**: Average time users watched the video
        - **Completion Rate**: % of video plays that watched 100%
        """)


def render_copies_tab(df: pd.DataFrame):
    """Render the Copies (ad body text) tab."""
    if df.empty:
        st.info("No data available")
        return

    if "body" not in df.columns:
        st.info("Ad copy data not available")
        return

    # Group by body text
    copies_df = df[df["body"].notna() & (df["body"] != "")].copy()

    if copies_df.empty:
        st.info("No ad copy data found")
        return

    grouped = copies_df.groupby("body").agg({
        "ad_id": "count",
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "purchases": "sum",
        "purchase_value": "sum",
    }).reset_index()

    grouped["roas"] = grouped.apply(
        lambda r: r["purchase_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )
    grouped["pct_of_spend"] = (grouped["spend"] / grouped["spend"].sum() * 100)

    sorted_df = grouped.sort_values("spend", ascending=False)

    display_df = sorted_df[["body", "ad_id", "spend", "roas", "pct_of_spend"]].copy()
    display_df.columns = ["Copy", "# Ads", "Spend", "ROAS", "% of Spend"]

    display_df["Copy"] = display_df["Copy"].apply(lambda x: x[:100] + "..." if len(str(x)) > 100 else x)
    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    display_df["% of Spend"] = display_df["% of Spend"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def render_headlines_tab(df: pd.DataFrame):
    """Render the Headlines tab."""
    if df.empty:
        st.info("No data available")
        return

    if "headline" not in df.columns:
        st.info("Headline data not available")
        return

    headlines_df = df[df["headline"].notna() & (df["headline"] != "")].copy()

    if headlines_df.empty:
        st.info("No headline data found")
        return

    grouped = headlines_df.groupby("headline").agg({
        "ad_id": "count",
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "purchases": "sum",
        "purchase_value": "sum",
    }).reset_index()

    grouped["roas"] = grouped.apply(
        lambda r: r["purchase_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )
    grouped["pct_of_spend"] = (grouped["spend"] / grouped["spend"].sum() * 100)

    sorted_df = grouped.sort_values("spend", ascending=False)

    display_df = sorted_df[["headline", "ad_id", "spend", "roas", "pct_of_spend"]].copy()
    display_df.columns = ["Headline", "# Ads", "Spend", "ROAS", "% of Spend"]

    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    display_df["% of Spend"] = display_df["% of Spend"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def render_landing_pages_tab(df: pd.DataFrame):
    """Render the Landing Pages tab."""
    if df.empty:
        st.info("No data available")
        return

    if "link_url" not in df.columns:
        st.info("Landing page data not available")
        return

    urls_df = df[df["link_url"].notna() & (df["link_url"] != "")].copy()

    if urls_df.empty:
        st.info("No landing page data found")
        return

    # Extract domain for cleaner display
    import re
    def extract_path(url):
        match = re.search(r'https?://[^/]+(/[^?]*)?', str(url))
        if match:
            return match.group(0)
        return url

    urls_df["clean_url"] = urls_df["link_url"].apply(extract_path)

    grouped = urls_df.groupby("clean_url").agg({
        "ad_id": "count",
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "purchases": "sum",
        "purchase_value": "sum",
    }).reset_index()

    grouped["roas"] = grouped.apply(
        lambda r: r["purchase_value"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )
    grouped["pct_of_spend"] = (grouped["spend"] / grouped["spend"].sum() * 100)

    sorted_df = grouped.sort_values("spend", ascending=False)

    display_df = sorted_df[["clean_url", "ad_id", "spend", "roas", "pct_of_spend"]].copy()
    display_df.columns = ["Landing Page", "# Ads", "Spend", "ROAS", "% of Spend"]

    display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.2f}")
    display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}")
    display_df["% of Spend"] = display_df["% of Spend"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)


def calculate_hit_rate(df: pd.DataFrame, min_spend: float = 1000, min_roas: float = 2.0) -> dict:
    """Calculate hit rate - creatives with spend >= min_spend and ROAS >= min_roas."""
    if df.empty:
        return {"rate": 0, "hits": 0, "total": 0}

    grouped = group_by_creative_name(df)
    qualified = grouped[grouped["spend"] >= min_spend]

    if qualified.empty:
        return {"rate": 0, "hits": 0, "total": 0}

    hits = qualified[qualified["roas"] >= min_roas]

    return {
        "rate": (len(hits) / len(qualified)) * 100 if len(qualified) > 0 else 0,
        "hits": len(hits),
        "total": len(qualified),
    }


def render_hit_rate_card(df: pd.DataFrame):
    """Render the Hit Rate tracker card."""
    hit_rate = calculate_hit_rate(df)

    st.markdown(f"""
    <div class="hit-rate-card">
        <div class="hit-rate-title">Hit Rate (≥$1K spend, ≥2.0 ROAS)</div>
        <div class="hit-rate-value">{hit_rate['rate']:.1f}%</div>
        <div class="hit-rate-subtitle">{hit_rate['hits']} of {hit_rate['total']} creatives</div>
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

    # Key Metrics Section with Hit Rate
    col_metrics, col_hitrate = st.columns([3, 1])

    with col_metrics:
        st.markdown("### Key Metrics")
        render_key_metrics(insights)

    with col_hitrate:
        st.markdown("### Hit Rate")
        render_hit_rate_card(df)

    st.divider()

    # Top Spend Chart
    render_top_spend_chart(df)

    st.divider()

    # Top Performing Grid
    render_top_performing_grid(df)

    st.divider()

    # Tabs for different views
    st.markdown("### Breakdown Analysis")
    tab_ads, tab_creatives, tab_images, tab_videos, tab_hooks, tab_copies, tab_headlines, tab_landing = st.tabs([
        "Ads", "Creatives", "Images", "Videos", "Video Hooks", "Copies", "Headlines", "Landing Pages"
    ])

    with tab_ads:
        render_ads_tab(df)

    with tab_creatives:
        render_creatives_tab(df)

    with tab_images:
        render_images_tab(df)

    with tab_videos:
        render_videos_tab(df)

    with tab_hooks:
        render_video_hooks_tab(df)

    with tab_copies:
        render_copies_tab(df)

    with tab_headlines:
        render_headlines_tab(df)

    with tab_landing:
        render_landing_pages_tab(df)


if __name__ == "__main__":
    main()
