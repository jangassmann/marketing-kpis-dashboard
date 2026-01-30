"""
Win Rate Tracker V2 - Media Buying Analytics Dashboard
Gamification + Deep Ad Analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

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
    /* Dark theme base */
    .stApp {
        background-color: #0f1117 !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0f1117 !important;
    }
    [data-testid="stHeader"] {
        background-color: #0f1117 !important;
    }

    /* Text colors */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #fafafa !important;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1d29 0%, #252836 100%);
        border: 1px solid #2d3143;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .metric-label {
        font-size: 12px;
        color: #8b8fa3 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff !important;
        font-family: 'SF Mono', 'Monaco', monospace;
        line-height: 1.1;
    }
    .metric-trend {
        font-size: 13px;
        color: #8b8fa3;
        margin-top: 8px;
    }
    .trend-up { color: #22c55e !important; }
    .trend-down { color: #ef4444 !important; }

    /* Podium styling */
    .podium-card {
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .podium-gold {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        box-shadow: 0 0 40px rgba(251, 191, 36, 0.3);
    }
    .podium-silver {
        background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
        box-shadow: 0 0 30px rgba(156, 163, 175, 0.2);
    }
    .podium-bronze {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        box-shadow: 0 0 30px rgba(217, 119, 6, 0.2);
    }
    .podium-rank {
        font-size: 48px;
        font-weight: 900;
        color: rgba(255,255,255,0.3);
        position: absolute;
        top: 10px;
        right: 20px;
    }
    .podium-name {
        font-size: 28px;
        font-weight: 800;
        color: #1a1a2e !important;
        margin-bottom: 8px;
    }
    .podium-stat {
        font-size: 14px;
        color: rgba(26,26,46,0.8) !important;
        margin: 4px 0;
    }
    .podium-value {
        font-size: 20px;
        font-weight: 700;
        color: #1a1a2e !important;
    }

    /* Alert cards */
    .alert-card {
        background: linear-gradient(135deg, #1a1d29 0%, #252836 100%);
        border-left: 4px solid;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .alert-rising {
        border-color: #22c55e;
    }
    .alert-fatigue {
        border-color: #ef4444;
    }
    .alert-title {
        font-size: 14px;
        font-weight: 600;
        color: #fafafa !important;
        margin-bottom: 4px;
    }
    .alert-subtitle {
        font-size: 12px;
        color: #8b8fa3 !important;
    }

    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #fafafa !important;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Data tables */
    .stDataFrame, [data-testid="stDataFrame"] {
        background: #1a1d29 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: #1a1d29 !important;
        border-radius: 8px !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1a1d29 !important;
        border-radius: 8px !important;
        color: #8b8fa3 !important;
        padding: 10px 20px !important;
    }
    .stTabs [aria-selected="true"] {
        background: #3b82f6 !important;
        color: #ffffff !important;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Plotly chart container */
    .js-plotly-plot {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def generate_dummy_data(num_rows: int = 500) -> pd.DataFrame:
    """Generate robust dummy ad data with proper naming convention."""
    np.random.seed(42)

    # Media buyer initials
    buyers = ["JD", "SM", "AK", "MR", "TL", "KW", "CB", "RP", "NJ", "EL"]

    # Creative concepts
    concepts = [
        "UGC-Hook", "Static-Promo", "Carousel-Sale", "Video-Demo",
        "Testimonial", "BTS-Content", "Product-Focus", "Lifestyle",
        "Problem-Solution", "Before-After", "Comparison", "Tutorial",
        "Unboxing", "Review-Mashup", "FOMO-Timer", "Social-Proof"
    ]

    # Formats
    formats = ["Video", "Image", "Carousel", "Story", "Reel"]

    data = []

    for i in range(num_rows):
        # Generate ad name in strict format: DATE_INITIALS_CONCEPT_FORMAT
        date_str = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y%m%d")
        buyer = random.choice(buyers)
        concept = random.choice(concepts)
        fmt = random.choice(formats)
        ad_name = f"{date_str}_{buyer}_{concept}_{fmt}"

        # Generate spend with realistic distribution (more low spend, fewer high spend)
        spend = np.random.exponential(scale=1500)
        spend = min(max(spend, 50), 10000)  # Clamp between $50 and $10,000

        # ROAS varies - correlation with spend (more spend = more stable ROAS)
        base_roas = np.random.lognormal(mean=0.7, sigma=0.5)
        if spend < 500:
            roas_multiplier = np.random.uniform(0.5, 2.0)  # High variance for low spend
        else:
            roas_multiplier = np.random.uniform(0.8, 1.3)  # Lower variance for high spend
        roas = base_roas * roas_multiplier
        roas = min(max(roas, 0.2), 8.0)  # Clamp ROAS

        revenue = spend * roas

        # Calculate other metrics
        impressions = int(spend * np.random.uniform(40, 120))
        clicks = int(impressions * np.random.uniform(0.005, 0.04))  # 0.5-4% CTR

        # Hook rate and hold rate (video metrics)
        hook_rate = np.random.uniform(0.20, 0.60)  # 3-second view rate
        hold_rate = np.random.uniform(0.05, 0.30)  # Video completion rate

        # Status - more active ads than paused
        status = "Active" if random.random() > 0.25 else "Paused"

        # For recent spend (last 7 days) - used for fatigue detection
        recent_roas = roas * np.random.uniform(0.5, 1.2)  # Could be worse or same

        data.append({
            "ad_name": ad_name,
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
            "launch_date": datetime.now() - timedelta(days=random.randint(0, 90)),
            "recent_roas_7d": round(recent_roas, 2),
        })

    return pd.DataFrame(data)


def generate_daily_trend_data(num_days: int = 30) -> pd.DataFrame:
    """Generate daily trend data for sparklines."""
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')

    # Base values with some trend
    base_spend = 5000
    base_roas = 2.2
    base_winners = 8
    base_win_rate = 3.5

    data = []
    for i, date in enumerate(dates):
        # Add some trend and noise
        trend_factor = 1 + (i / num_days) * 0.15  # Slight upward trend
        noise = np.random.uniform(0.85, 1.15)

        spend = base_spend * trend_factor * noise
        roas = base_roas * (1 + np.random.uniform(-0.15, 0.2))
        winners = int(base_winners * trend_factor * np.random.uniform(0.8, 1.3))
        win_rate = base_win_rate * (1 + np.random.uniform(-0.2, 0.25))

        data.append({
            "date": date,
            "spend": round(spend, 2),
            "roas": round(roas, 2),
            "winners": winners,
            "win_rate": round(win_rate, 2),
        })

    return pd.DataFrame(data)


def create_sparkline(data: list, color: str = "#3b82f6", height: int = 40) -> go.Figure:
    """Create a minimal sparkline chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        y=data,
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
        hoverinfo='skip',
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )

    return fig


def render_metric_with_sparkline(label: str, value: str, trend_data: list, trend_pct: float, color: str = "#3b82f6"):
    """Render a metric card with sparkline."""
    trend_class = "trend-up" if trend_pct >= 0 else "trend-down"
    trend_icon = "↑" if trend_pct >= 0 else "↓"

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-trend {trend_class}">{trend_icon} {abs(trend_pct):.1f}% vs last period</div>
    </div>
    """, unsafe_allow_html=True)

    # Sparkline
    fig = create_sparkline(trend_data, color)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_podium(df: pd.DataFrame):
    """Render the Top Gun podium for media buyers."""
    st.markdown('<div class="section-header">🏆 Top Gun Leaderboard</div>', unsafe_allow_html=True)

    # Calculate buyer performance - rank by total spend where ROAS > 2.0
    winning_ads = df[df["roas"] > 2.0].copy()

    if winning_ads.empty:
        st.info("No qualifying ads found (ROAS > 2.0)")
        return

    buyer_stats = winning_ads.groupby("buyer_initials").agg({
        "spend": "sum",
        "revenue": "sum",
        "ad_name": "count"
    }).reset_index()

    buyer_stats["roas"] = buyer_stats["revenue"] / buyer_stats["spend"]
    buyer_stats = buyer_stats.sort_values("spend", ascending=False).head(3)

    if len(buyer_stats) < 3:
        st.warning("Need at least 3 buyers with qualifying ads")
        return

    # Podium layout: 2nd | 1st | 3rd
    col1, col2, col3 = st.columns([1, 1.2, 1])

    # 2nd Place (Silver) - Left
    with col1:
        buyer = buyer_stats.iloc[1]
        st.markdown(f"""
        <div class="podium-card podium-silver" style="margin-top: 40px;">
            <div class="podium-rank">2</div>
            <div class="podium-name">{buyer['buyer_initials']}</div>
            <div class="podium-stat">Total Spend</div>
            <div class="podium-value">${buyer['spend']:,.0f}</div>
            <div class="podium-stat">ROAS</div>
            <div class="podium-value">{buyer['roas']:.2f}x</div>
            <div class="podium-stat">Winning Ads</div>
            <div class="podium-value">{buyer['ad_name']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 1st Place (Gold) - Center
    with col2:
        buyer = buyer_stats.iloc[0]
        st.markdown(f"""
        <div class="podium-card podium-gold">
            <div class="podium-rank">1</div>
            <div class="podium-name">{buyer['buyer_initials']}</div>
            <div class="podium-stat">Total Spend</div>
            <div class="podium-value">${buyer['spend']:,.0f}</div>
            <div class="podium-stat">ROAS</div>
            <div class="podium-value">{buyer['roas']:.2f}x</div>
            <div class="podium-stat">Winning Ads</div>
            <div class="podium-value">{buyer['ad_name']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3rd Place (Bronze) - Right
    with col3:
        buyer = buyer_stats.iloc[2]
        st.markdown(f"""
        <div class="podium-card podium-bronze" style="margin-top: 60px;">
            <div class="podium-rank">3</div>
            <div class="podium-name">{buyer['buyer_initials']}</div>
            <div class="podium-stat">Total Spend</div>
            <div class="podium-value">${buyer['spend']:,.0f}</div>
            <div class="podium-stat">ROAS</div>
            <div class="podium-value">{buyer['roas']:.2f}x</div>
            <div class="podium-stat">Winning Ads</div>
            <div class="podium-value">{buyer['ad_name']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_alerts(df: pd.DataFrame):
    """Render Rising Stars (Incubator) and Fatigue Alerts."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">🌟 Rising Stars (Scale Now)</div>', unsafe_allow_html=True)

        # Rising Stars: <$1K spend but >4.0 ROAS
        rising = df[(df["spend"] < 1000) & (df["roas"] > 4.0)].copy()
        rising = rising.sort_values("roas", ascending=False).head(5)

        if rising.empty:
            st.info("No rising stars found (<$1K spend & >4.0 ROAS)")
        else:
            for _, ad in rising.iterrows():
                st.markdown(f"""
                <div class="alert-card alert-rising">
                    <div class="alert-title">{ad['ad_name'][:50]}...</div>
                    <div class="alert-subtitle">
                        Spend: ${ad['spend']:,.0f} | ROAS: {ad['roas']:.2f}x | Status: {ad['status']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">⚠️ Fatigue Alert (Kill These)</div>', unsafe_allow_html=True)

        # Fatigue: >$5K lifetime spend but <1.5 ROAS in last 7 days
        fatigue = df[(df["spend"] > 5000) & (df["recent_roas_7d"] < 1.5)].copy()
        fatigue = fatigue.sort_values("spend", ascending=False).head(5)

        if fatigue.empty:
            st.success("No fatigued ads detected!")
        else:
            for _, ad in fatigue.iterrows():
                st.markdown(f"""
                <div class="alert-card alert-fatigue">
                    <div class="alert-title">{ad['ad_name'][:50]}...</div>
                    <div class="alert-subtitle">
                        Lifetime: ${ad['spend']:,.0f} | 7d ROAS: {ad['recent_roas_7d']:.2f}x | Losing ${(ad['spend'] * (1 - ad['recent_roas_7d'])):.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_scatter_analysis(df: pd.DataFrame):
    """Render scatter plot for hook rate vs hold rate analysis."""
    st.markdown('<div class="section-header">📊 Creative Performance Matrix</div>', unsafe_allow_html=True)

    # Filter for meaningful data
    plot_df = df[df["impressions"] > 1000].copy()

    if plot_df.empty:
        st.warning("Not enough data for scatter analysis")
        return

    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x="hook_rate",
        y="hold_rate",
        color="roas",
        size="spend",
        hover_name="ad_name",
        hover_data={
            "hook_rate": ":.1%",
            "hold_rate": ":.1%",
            "roas": ":.2f",
            "spend": ":$,.0f",
        },
        color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],  # Red to Yellow to Green
        labels={
            "hook_rate": "Hook Rate (3s Views / Impressions)",
            "hold_rate": "Hold Rate (Completions / Views)",
            "roas": "ROAS",
            "spend": "Spend ($)",
        },
    )

    # Add quadrant labels
    fig.add_annotation(x=0.25, y=0.25, text="💤 Boring Intro<br>Low Hook / Low Hold",
                       showarrow=False, font=dict(color="#8b8fa3", size=10))
    fig.add_annotation(x=0.55, y=0.25, text="🎣 Clickbait<br>High Hook / Low Hold",
                       showarrow=False, font=dict(color="#8b8fa3", size=10))
    fig.add_annotation(x=0.25, y=0.25, text="📚 Slow Burn<br>Low Hook / High Hold",
                       showarrow=False, font=dict(color="#8b8fa3", size=10), yshift=80)
    fig.add_annotation(x=0.55, y=0.25, text="🏆 Winner Zone<br>High Hook / High Hold",
                       showarrow=False, font=dict(color="#22c55e", size=10), yshift=80)

    # Add reference lines
    fig.add_hline(y=0.15, line_dash="dash", line_color="#4b5563", opacity=0.5)
    fig.add_vline(x=0.40, line_dash="dash", line_color="#4b5563", opacity=0.5)

    fig.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,41,0.8)',
        font=dict(color="#fafafa"),
        xaxis=dict(
            gridcolor='rgba(75,85,99,0.3)',
            tickformat='.0%',
            range=[0.15, 0.65],
        ),
        yaxis=dict(
            gridcolor='rgba(75,85,99,0.3)',
            tickformat='.0%',
            range=[0, 0.35],
        ),
        coloraxis_colorbar=dict(
            title="ROAS",
            tickformat=".1f",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add legend
    st.markdown("""
    <div style="display: flex; gap: 24px; justify-content: center; margin-top: -20px; margin-bottom: 20px;">
        <span style="color: #8b8fa3; font-size: 12px;">🔴 Low ROAS (<1.5)</span>
        <span style="color: #8b8fa3; font-size: 12px;">🟡 Medium ROAS (1.5-3.0)</span>
        <span style="color: #8b8fa3; font-size: 12px;">🟢 High ROAS (>3.0)</span>
        <span style="color: #8b8fa3; font-size: 12px;">⬤ Bubble Size = Spend</span>
    </div>
    """, unsafe_allow_html=True)


def render_winners_gallery(df: pd.DataFrame):
    """Render the winners gallery with thumbnails."""
    st.markdown('<div class="section-header">🏅 Winners Gallery</div>', unsafe_allow_html=True)

    # Filter for winners (>$1K spend, >2.0 ROAS)
    winners = df[(df["spend"] >= 1000) & (df["roas"] >= 2.0)].copy()
    winners = winners.sort_values("roas", ascending=False)

    if winners.empty:
        st.info("No winners found (≥$1K spend & ≥2.0 ROAS)")
        return

    # Group by options
    group_by = st.radio(
        "Group by:",
        ["None", "Concept", "Format", "Media Buyer"],
        horizontal=True,
        key="winners_group"
    )

    if group_by == "None":
        display_df = winners[["ad_name", "creative_thumbnail", "spend", "roas", "concept", "format"]].head(20)
        display_df.columns = ["Ad Name", "Thumbnail", "Spend", "ROAS", "Concept", "Format"]

        st.dataframe(
            display_df,
            column_config={
                "Thumbnail": st.column_config.ImageColumn("Preview", width="small"),
                "Spend": st.column_config.NumberColumn("Spend", format="$%.2f"),
                "ROAS": st.column_config.NumberColumn("ROAS", format="%.2fx"),
            },
            use_container_width=True,
            hide_index=True,
            height=500,
        )
    else:
        group_col = {
            "Concept": "concept",
            "Format": "format",
            "Media Buyer": "buyer_initials"
        }[group_by]

        # Group summary
        grouped = winners.groupby(group_col).agg({
            "ad_name": "count",
            "spend": "sum",
            "revenue": "sum",
        }).reset_index()
        grouped["roas"] = grouped["revenue"] / grouped["spend"]
        grouped.columns = [group_by, "Winners", "Total Spend", "Total Revenue", "Avg ROAS"]
        grouped = grouped.sort_values("Total Spend", ascending=False)

        st.dataframe(
            grouped,
            column_config={
                "Total Spend": st.column_config.NumberColumn(format="$%.2f"),
                "Total Revenue": st.column_config.NumberColumn(format="$%.2f"),
                "Avg ROAS": st.column_config.NumberColumn(format="%.2fx"),
            },
            use_container_width=True,
            hide_index=True,
        )


def main():
    """Main application."""
    # Header
    st.markdown("# 🎯 Win Rate Tracker V2")
    st.markdown("*Media Buying Analytics Dashboard with Gamification*")

    # Generate data
    df = generate_dummy_data(500)
    trend_df = generate_daily_trend_data(30)

    # Calculate key metrics
    total_spend = df["spend"].sum()
    total_revenue = df["revenue"].sum()
    blended_roas = total_revenue / total_spend if total_spend > 0 else 0

    # Winners = creatives with ≥$1K spend AND ≥2.0 ROAS
    winners = df[(df["spend"] >= 1000) & (df["roas"] >= 2.0)]
    total_winners = len(winners)

    # Win rate = winners / total creatives
    total_creatives = len(df)
    win_rate = (total_winners / total_creatives * 100) if total_creatives > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION A: High-Level Metrics with Sparklines
    st.markdown('<div class="section-header">📈 The Pulse</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_with_sparkline(
            "Total Spend",
            f"${total_spend:,.0f}",
            trend_df["spend"].tolist(),
            12.5,
            "#3b82f6"
        )

    with col2:
        render_metric_with_sparkline(
            "Win Rate",
            f"{win_rate:.1f}%",
            trend_df["win_rate"].tolist(),
            8.3,
            "#22c55e"
        )

    with col3:
        render_metric_with_sparkline(
            "Total Winners",
            f"{total_winners}",
            trend_df["winners"].tolist(),
            15.2,
            "#f59e0b"
        )

    with col4:
        render_metric_with_sparkline(
            "Blended ROAS",
            f"{blended_roas:.2f}x",
            trend_df["roas"].tolist(),
            -2.1,
            "#8b5cf6"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION B: Top Gun Podium
    render_podium(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION C: Alerts (Rising Stars & Fatigue)
    render_alerts(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION D: Scatter Plot Analysis
    render_scatter_analysis(df)

    st.markdown("<br>", unsafe_allow_html=True)

    # SECTION E: Winners Gallery
    render_winners_gallery(df)


if __name__ == "__main__":
    main()
