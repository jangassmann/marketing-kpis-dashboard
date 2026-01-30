"""
Win Rate Tracker V2 - Gamification & Deep Ad Analysis Dashboard
Media Buying Analytics with Team Leaderboards and Creative Intelligence
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import random
import string

# Page configuration
st.set_page_config(
    page_title="Win Rate Tracker V2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for dark mode native design
st.markdown("""
<style>
    /* Dark mode native */
    .stApp {
        background-color: #0f1117 !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0f1117 !important;
    }
    [data-testid="stHeader"] {
        background-color: #0f1117 !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #141824 100%);
        border: 1px solid #2d3548;
        border-radius: 16px;
        padding: 24px;
        height: 100%;
    }
    .metric-label {
        font-size: 12px;
        color: #8b95a5;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'SF Mono', 'Monaco', monospace;
        letter-spacing: -1px;
        margin-bottom: 4px;
    }
    .metric-subtitle {
        font-size: 13px;
        color: #6b7280;
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

    /* Podium styling */
    .podium-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #141824 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        height: 100%;
    }
    .podium-gold {
        border: 2px solid #fbbf24;
        box-shadow: 0 0 30px rgba(251, 191, 36, 0.3);
    }
    .podium-silver {
        border: 2px solid #9ca3af;
        box-shadow: 0 0 20px rgba(156, 163, 175, 0.2);
    }
    .podium-bronze {
        border: 2px solid #cd7f32;
        box-shadow: 0 0 20px rgba(205, 127, 50, 0.2);
    }
    .podium-rank {
        font-size: 48px;
        margin-bottom: 8px;
    }
    .podium-name {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }
    .podium-stat {
        font-size: 14px;
        color: #9ca3af;
        margin-bottom: 4px;
    }
    .podium-value {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
    }

    /* Alert cards */
    .alert-card {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid;
    }
    .alert-rising {
        border-left-color: #10b981;
    }
    .alert-fatigue {
        border-left-color: #ef4444;
    }
    .alert-title {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .alert-subtitle {
        font-size: 12px;
        color: #6b7280;
    }

    /* Section headers */
    .section-header {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #2d3548;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1a1f2e !important;
        color: #ffffff !important;
    }

    /* Data table styling */
    .stDataFrame {
        background-color: #1a1f2e !important;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f2e !important;
        color: #9ca3af !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------
# DATA GENERATION
# -------------------------------------------------------------------
@st.cache_data
def generate_ad_data(num_rows: int = 500) -> pd.DataFrame:
    """Generate robust simulated ad data with proper naming convention."""

    # Media buyer initials
    buyers = ["JD", "MK", "AS", "TR", "LW", "PB", "CR", "NM", "KS", "DF"]

    # Creative concepts
    concepts = [
        "UGC-Hook", "UGC-Testimonial", "Founder-Story", "Problem-Solution",
        "Before-After", "Listicle", "ASMR", "Tutorial", "Unboxing",
        "Review", "Demo", "Comparison", "FAQ", "Lifestyle", "Social-Proof"
    ]

    # Formats
    formats = ["Video", "Image", "Carousel", "Reel", "Story"]

    data = []
    base_date = datetime(2026, 1, 15)  # Mid-January 2026

    for i in range(num_rows):
        # Generate date within last 90 days
        days_ago = random.randint(0, 90)
        ad_date = base_date - timedelta(days=days_ago)
        date_str = ad_date.strftime("%Y%m%d")

        # Pick random components
        buyer = random.choice(buyers)
        concept = random.choice(concepts)
        fmt = random.choice(formats)

        # Create ad name: DATE_INITIALS_CONCEPT_FORMAT
        ad_name = f"{date_str}_{buyer}_{concept}_{fmt}"

        # Generate realistic metrics with correlation
        # Higher hook rate = better ad = higher spend potential
        hook_rate = random.uniform(0.20, 0.60)
        hold_rate = random.uniform(0.05, 0.30)

        # Spend correlates loosely with hook quality (better ads get more budget)
        base_spend = random.uniform(50, 10000)
        spend = base_spend * (0.5 + hook_rate)  # Boost spend for better hooks
        spend = min(max(spend, 50), 10000)

        # ROAS correlates with both hook and hold rate
        base_roas = hook_rate * 2 + hold_rate * 4 + random.uniform(-0.5, 1.5)
        roas = max(0.3, base_roas)

        # Revenue
        revenue = spend * roas

        # Impressions based on spend (assume ~$10 CPM average)
        impressions = int(spend / 10 * 1000 * random.uniform(0.7, 1.3))

        # Clicks based on impressions and hook rate
        ctr = hook_rate * 0.05 + random.uniform(0.005, 0.02)  # 0.5% to ~5% CTR
        clicks = int(impressions * ctr)

        # Status - more likely paused if low ROAS
        if roas < 1.5:
            status = random.choices(["Active", "Paused"], weights=[30, 70])[0]
        elif roas > 3.0:
            status = random.choices(["Active", "Paused"], weights=[90, 10])[0]
        else:
            status = random.choices(["Active", "Paused"], weights=[60, 40])[0]

        data.append({
            "ad_name": ad_name,
            "ad_date": ad_date,
            "buyer_initials": buyer,
            "concept": concept,
            "format": fmt,
            "spend": round(spend, 2),
            "revenue": round(revenue, 2),
            "roas": round(roas, 2),
            "impressions": impressions,
            "clicks": clicks,
            "hook_rate": round(hook_rate, 3),
            "hold_rate": round(hold_rate, 3),
            "status": status,
            "creative_thumbnail": "https://placehold.co/100",
        })

    return pd.DataFrame(data)


def calculate_daily_metrics(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """Calculate daily aggregated metrics for sparklines."""
    df = df.copy()

    # Filter to last N days
    cutoff = datetime(2026, 1, 15) - timedelta(days=days)
    recent = df[df["ad_date"] >= cutoff]

    # Group by date
    daily = recent.groupby(recent["ad_date"].dt.date).agg({
        "spend": "sum",
        "revenue": "sum",
        "ad_name": "count"
    }).reset_index()
    daily.columns = ["date", "spend", "revenue", "creatives"]

    # Calculate daily ROAS
    daily["roas"] = daily.apply(
        lambda r: r["revenue"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )

    # Calculate daily winners (simplified - count ads with ROAS > 2)
    daily["winners"] = 0  # Placeholder, would need per-day calculation

    # Sort by date
    daily = daily.sort_values("date")

    return daily


def get_top_buyers(df: pd.DataFrame, min_roas: float = 2.0, top_n: int = 3) -> pd.DataFrame:
    """Get top media buyers ranked by qualifying spend."""
    # Filter for winning ads
    winners = df[df["roas"] >= min_roas]

    # Group by buyer
    buyer_stats = winners.groupby("buyer_initials").agg({
        "spend": "sum",
        "revenue": "sum",
        "ad_name": "count"
    }).reset_index()
    buyer_stats.columns = ["initials", "spend", "revenue", "winning_ads"]

    # Calculate ROAS
    buyer_stats["roas"] = buyer_stats.apply(
        lambda r: r["revenue"] / r["spend"] if r["spend"] > 0 else 0, axis=1
    )

    # Sort by spend and take top N
    buyer_stats = buyer_stats.sort_values("spend", ascending=False).head(top_n)

    return buyer_stats


def get_rising_stars(df: pd.DataFrame, max_spend: float = 1000, min_roas: float = 4.0) -> pd.DataFrame:
    """Get rising star ads - low spend but high ROAS."""
    stars = df[(df["spend"] < max_spend) & (df["roas"] > min_roas)]
    return stars.sort_values("roas", ascending=False).head(10)


def get_fatigue_alerts(df: pd.DataFrame, min_spend: float = 5000, max_roas: float = 1.5) -> pd.DataFrame:
    """Get fatigued ads - high spend but low recent ROAS."""
    # Simulate "last 7 days" by looking at recent dates
    recent_cutoff = datetime(2026, 1, 8)  # Last 7 days of our data

    # Get ads with high lifetime spend
    high_spend = df[df["spend"] >= min_spend].copy()

    # Flag as fatigue if ROAS is low (simulating recent performance drop)
    fatigued = high_spend[high_spend["roas"] < max_roas]

    return fatigued.sort_values("spend", ascending=False).head(10)


# -------------------------------------------------------------------
# RENDERING FUNCTIONS
# -------------------------------------------------------------------
def render_sparkline(data: list, color: str = "#3b82f6", height: int = 40) -> go.Figure:
    """Create a mini sparkline chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}',
        hoverinfo='skip'
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False
    )

    return fig


def render_metric_card(label: str, value: str, sparkline_data: list = None,
                       change: float = None, color: str = "#3b82f6"):
    """Render a metric card with optional sparkline."""

    change_html = ""
    if change is not None:
        if change > 0:
            change_html = f'<span class="metric-change-positive">+{change:.1f}%</span>'
        elif change < 0:
            change_html = f'<span class="metric-change-negative">{change:.1f}%</span>'

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{change_html}</div>
    </div>
    """, unsafe_allow_html=True)

    if sparkline_data and len(sparkline_data) > 1:
        fig = render_sparkline(sparkline_data, color)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_podium(top_buyers: pd.DataFrame):
    """Render the Top Gun podium with gold, silver, bronze."""

    if len(top_buyers) < 3:
        st.warning("Not enough data for podium")
        return

    col1, col2, col3 = st.columns([1, 1.2, 1])

    # 2nd Place (Silver) - Left
    with col1:
        if len(top_buyers) >= 2:
            buyer = top_buyers.iloc[1]
            st.markdown(f"""
            <div class="podium-card podium-silver">
                <div class="podium-rank">🥈</div>
                <div class="podium-name">{buyer['initials']}</div>
                <div class="podium-stat">Qualifying Spend</div>
                <div class="podium-value">${buyer['spend']:,.0f}</div>
                <div class="podium-stat" style="margin-top: 12px;">ROAS</div>
                <div class="podium-value">{buyer['roas']:.2f}x</div>
                <div class="podium-stat" style="margin-top: 12px;">Winners</div>
                <div class="podium-value">{buyer['winning_ads']}</div>
            </div>
            """, unsafe_allow_html=True)

    # 1st Place (Gold) - Center
    with col2:
        buyer = top_buyers.iloc[0]
        st.markdown(f"""
        <div class="podium-card podium-gold">
            <div class="podium-rank">🥇</div>
            <div class="podium-name" style="font-size: 36px;">{buyer['initials']}</div>
            <div class="podium-stat">Qualifying Spend</div>
            <div class="podium-value" style="font-size: 28px;">${buyer['spend']:,.0f}</div>
            <div class="podium-stat" style="margin-top: 16px;">ROAS</div>
            <div class="podium-value" style="font-size: 24px;">{buyer['roas']:.2f}x</div>
            <div class="podium-stat" style="margin-top: 16px;">Winners</div>
            <div class="podium-value" style="font-size: 24px;">{buyer['winning_ads']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3rd Place (Bronze) - Right
    with col3:
        if len(top_buyers) >= 3:
            buyer = top_buyers.iloc[2]
            st.markdown(f"""
            <div class="podium-card podium-bronze">
                <div class="podium-rank">🥉</div>
                <div class="podium-name">{buyer['initials']}</div>
                <div class="podium-stat">Qualifying Spend</div>
                <div class="podium-value">${buyer['spend']:,.0f}</div>
                <div class="podium-stat" style="margin-top: 12px;">ROAS</div>
                <div class="podium-value">{buyer['roas']:.2f}x</div>
                <div class="podium-stat" style="margin-top: 12px;">Winners</div>
                <div class="podium-value">{buyer['winning_ads']}</div>
            </div>
            """, unsafe_allow_html=True)


def render_scatter_plot(df: pd.DataFrame):
    """Render the Hook Rate vs Hold Rate scatter plot."""

    fig = px.scatter(
        df,
        x="hook_rate",
        y="hold_rate",
        size="spend",
        color="roas",
        color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
        hover_name="ad_name",
        hover_data={
            "hook_rate": ":.2%",
            "hold_rate": ":.2%",
            "spend": ":$,.0f",
            "roas": ":.2f"
        },
        labels={
            "hook_rate": "Hook Rate (3s Views / Impressions)",
            "hold_rate": "Hold Rate (Watch Time Retention)",
            "roas": "ROAS",
            "spend": "Spend"
        }
    )

    # Add quadrant lines
    fig.add_hline(y=0.15, line_dash="dash", line_color="#4b5563", opacity=0.5)
    fig.add_vline(x=0.35, line_dash="dash", line_color="#4b5563", opacity=0.5)

    # Add quadrant annotations
    fig.add_annotation(x=0.55, y=0.28, text="<b>Winners</b><br>Great Hook + Hold",
                      showarrow=False, font=dict(color="#10b981", size=11))
    fig.add_annotation(x=0.55, y=0.08, text="<b>Clickbait</b><br>Hook but No Hold",
                      showarrow=False, font=dict(color="#f59e0b", size=11))
    fig.add_annotation(x=0.25, y=0.28, text="<b>Slow Burn</b><br>Low Hook, High Hold",
                      showarrow=False, font=dict(color="#3b82f6", size=11))
    fig.add_annotation(x=0.25, y=0.08, text="<b>Underperformers</b><br>Needs Work",
                      showarrow=False, font=dict(color="#ef4444", size=11))

    fig.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#1a1f2e',
        font=dict(color='#9ca3af'),
        xaxis=dict(
            gridcolor='#2d3548',
            tickformat='.0%',
            range=[0.15, 0.65]
        ),
        yaxis=dict(
            gridcolor='#2d3548',
            tickformat='.0%',
            range=[0, 0.35]
        ),
        coloraxis_colorbar=dict(
            title="ROAS",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["1x", "2x", "3x", "4x", "5x+"]
        )
    )

    return fig


def render_alerts_section(rising_stars: pd.DataFrame, fatigue_alerts: pd.DataFrame):
    """Render the Rising Stars and Fatigue Alerts section."""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🌟 Rising Stars (Scale These)")
        st.caption("Ads with <$1K spend but >4.0 ROAS")

        if rising_stars.empty:
            st.info("No rising stars found")
        else:
            for _, ad in rising_stars.head(5).iterrows():
                st.markdown(f"""
                <div class="alert-card alert-rising">
                    <div class="alert-title">{ad['ad_name'][:50]}...</div>
                    <div class="alert-subtitle">
                        Spend: ${ad['spend']:,.0f} | ROAS: {ad['roas']:.1f}x |
                        Buyer: {ad['buyer_initials']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🚨 Fatigue Alerts (Consider Pausing)")
        st.caption("Ads with >$5K spend but <1.5 ROAS")

        if fatigue_alerts.empty:
            st.success("No fatigued ads found!")
        else:
            for _, ad in fatigue_alerts.head(5).iterrows():
                st.markdown(f"""
                <div class="alert-card alert-fatigue">
                    <div class="alert-title">{ad['ad_name'][:50]}...</div>
                    <div class="alert-subtitle">
                        Spend: ${ad['spend']:,.0f} | ROAS: {ad['roas']:.1f}x |
                        Status: {ad['status']}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_winners_gallery(df: pd.DataFrame, min_roas: float = 2.0):
    """Render the winners gallery with grouping options."""

    # Filter winners
    winners = df[df["roas"] >= min_roas].copy()
    winners = winners.sort_values("roas", ascending=False)

    # Calculate win rate for each ad
    total_ads = len(df)
    winners["win_rate"] = "Winner"

    # Group by option
    group_by = st.radio(
        "Group by:",
        ["None", "Month", "Concept", "Buyer"],
        horizontal=True,
        key="gallery_group"
    )

    if group_by == "Month":
        winners["month"] = winners["ad_date"].dt.strftime("%B %Y")
        grouped = winners.groupby("month")
        for month, group in grouped:
            st.markdown(f"**{month}** ({len(group)} winners)")
            display_df = group[["ad_name", "spend", "roas", "buyer_initials", "concept"]].head(10)
            display_df.columns = ["Ad Name", "Spend", "ROAS", "Buyer", "Concept"]
            display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.0f}")
            display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}x")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    elif group_by == "Concept":
        grouped = winners.groupby("concept")
        for concept, group in sorted(grouped, key=lambda x: -len(x[1])):
            st.markdown(f"**{concept}** ({len(group)} winners)")
            display_df = group[["ad_name", "spend", "roas", "buyer_initials"]].head(5)
            display_df.columns = ["Ad Name", "Spend", "ROAS", "Buyer"]
            display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.0f}")
            display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}x")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    elif group_by == "Buyer":
        grouped = winners.groupby("buyer_initials")
        for buyer, group in sorted(grouped, key=lambda x: -x[1]["spend"].sum()):
            total_spend = group["spend"].sum()
            avg_roas = group["revenue"].sum() / total_spend if total_spend > 0 else 0
            st.markdown(f"**{buyer}** - {len(group)} winners | ${total_spend:,.0f} spend | {avg_roas:.2f}x ROAS")
            display_df = group[["ad_name", "spend", "roas", "concept"]].head(5)
            display_df.columns = ["Ad Name", "Spend", "ROAS", "Concept"]
            display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.0f}")
            display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}x")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        # No grouping - show all
        display_df = winners[["ad_name", "spend", "roas", "buyer_initials", "concept", "format"]].head(20)
        display_df.columns = ["Ad Name", "Spend", "ROAS", "Buyer", "Concept", "Format"]
        display_df["Spend"] = display_df["Spend"].apply(lambda x: f"${x:,.0f}")
        display_df["ROAS"] = display_df["ROAS"].apply(lambda x: f"{x:.2f}x")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "Ad Name": st.column_config.TextColumn("Ad Name", width="large"),
                "ROAS": st.column_config.TextColumn("ROAS", width="small"),
            }
        )


# -------------------------------------------------------------------
# MAIN APPLICATION
# -------------------------------------------------------------------
def main():
    # Header
    st.markdown("# 🎯 Win Rate Tracker V2")
    st.markdown("Media Buying Analytics Dashboard with Gamification & Deep Analysis")
    st.markdown("---")

    # Generate data
    df = generate_ad_data(500)
    daily_metrics = calculate_daily_metrics(df, 30)

    # Calculate key metrics
    total_spend = df["spend"].sum()
    total_revenue = df["revenue"].sum()
    blended_roas = total_revenue / total_spend if total_spend > 0 else 0

    # Winners: spend >= $1K AND ROAS >= 2.0
    qualified = df[df["spend"] >= 1000]
    winners = qualified[qualified["roas"] >= 2.0]
    total_creatives = len(df["ad_name"].unique())
    win_rate = (len(winners) / total_creatives * 100) if total_creatives > 0 else 0

    # Generate sparkline data
    spend_sparkline = daily_metrics["spend"].tolist() if not daily_metrics.empty else []
    roas_sparkline = daily_metrics["roas"].tolist() if not daily_metrics.empty else []

    # -------------------------------------------------------------------
    # SECTION A: High-Level Metrics (The "Pulse")
    # -------------------------------------------------------------------
    st.markdown('<div class="section-header">📊 The Pulse</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Total Spend",
            f"${total_spend:,.0f}",
            sparkline_data=spend_sparkline,
            change=12.4,
            color="#3b82f6"
        )

    with col2:
        render_metric_card(
            "Win Rate",
            f"{win_rate:.1f}%",
            sparkline_data=None,
            change=2.3,
            color="#10b981"
        )

    with col3:
        render_metric_card(
            "Total Winners",
            f"{len(winners)}",
            sparkline_data=None,
            change=8.1,
            color="#f59e0b"
        )

    with col4:
        render_metric_card(
            "Blended ROAS",
            f"{blended_roas:.2f}x",
            sparkline_data=roas_sparkline,
            change=-1.2,
            color="#8b5cf6"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # SECTION B: The "Top Gun" Podium (Gamification)
    # -------------------------------------------------------------------
    st.markdown('<div class="section-header">🏆 Top Gun Leaderboard</div>', unsafe_allow_html=True)
    st.caption("Ranked by total qualifying spend (ads with ROAS > 2.0)")

    top_buyers = get_top_buyers(df, min_roas=2.0, top_n=3)
    render_podium(top_buyers)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # SECTION C: The "Incubator" & "Fatigue" Alerts
    # -------------------------------------------------------------------
    st.markdown('<div class="section-header">🧠 Creative Intelligence</div>', unsafe_allow_html=True)

    rising_stars = get_rising_stars(df, max_spend=1000, min_roas=4.0)
    fatigue_alerts = get_fatigue_alerts(df, min_spend=5000, max_roas=1.5)

    with st.expander("📈 Rising Stars & 🚨 Fatigue Alerts", expanded=True):
        render_alerts_section(rising_stars, fatigue_alerts)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # SECTION D: Visual Deep Dive (Scatter Plot)
    # -------------------------------------------------------------------
    st.markdown('<div class="section-header">🔬 Creative Deep Dive</div>', unsafe_allow_html=True)
    st.caption("Hook Rate vs Hold Rate Analysis - Identify Clickbait vs Boring Intros")

    fig = render_scatter_plot(df)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------
    # SECTION E: The "Winners Gallery" (Data Table)
    # -------------------------------------------------------------------
    st.markdown('<div class="section-header">🏅 Winners Gallery</div>', unsafe_allow_html=True)
    st.caption(f"Showing {len(winners)} winning ads (≥$1K spend AND ≥2.0 ROAS)")

    render_winners_gallery(df, min_roas=2.0)


if __name__ == "__main__":
    main()
