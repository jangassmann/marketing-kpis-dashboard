"""
Marketing KPIs Dashboard
A Streamlit app for tracking ad creative performance and win rates.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Import local modules
from src.meta_api import MetaAdsClient, get_demo_data, get_available_ad_accounts
from src.data_processor import (
    apply_win_rules,
    calculate_overview_metrics,
    enrich_data,
    calculate_breakdown,
    filter_data,
)
from src.ai_analyzer import (
    enrich_dataframe_with_angles,
    get_cache_stats,
    clear_cache,
    init_cache_db,
)
from src.components.metrics_cards import render_metrics_cards
from src.components.breakdown_table import render_breakdown_table, render_detailed_table
import config

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Marketing KPIs Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e9ecef;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0 20px 0;
        border-bottom: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "data" not in st.session_state:
        st.session_state.data = None
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = None
    if "api_connected" not in st.session_state:
        st.session_state.api_connected = False
    if "use_demo" not in st.session_state:
        st.session_state.use_demo = False


def render_sidebar():
    """Render the sidebar with filters and settings."""
    with st.sidebar:
        st.title("Settings")

        # Data source selection
        st.subheader("Data Source")
        use_demo = st.checkbox(
            "Use Demo Data",
            value=st.session_state.use_demo,
            help="Use sample data instead of connecting to Meta API"
        )
        st.session_state.use_demo = use_demo

        if not use_demo:
            # Ad Account Selection
            available_accounts = get_available_ad_accounts()
            if available_accounts and len(available_accounts) > 1:
                st.subheader("Ad Account")
                selected_account = st.selectbox(
                    "Select Account",
                    options=available_accounts,
                    index=0,
                    format_func=lambda x: x.replace("act_", "Account "),
                )
                if "selected_account" not in st.session_state or st.session_state.selected_account != selected_account:
                    st.session_state.selected_account = selected_account
                    st.session_state.data = None  # Reset data when account changes
            elif available_accounts:
                st.session_state.selected_account = available_accounts[0]

            # API Configuration
            st.subheader("Meta API")
            selected_account = st.session_state.get("selected_account")

            if st.session_state.api_connected:
                st.success("Connected")
            else:
                # Try auto-connect with env credentials
                if selected_account and os.getenv("META_ACCESS_TOKEN"):
                    client = MetaAdsClient(ad_account_id=selected_account)
                    if client.connect():
                        st.session_state.api_connected = True
                        st.session_state.client = client

                with st.expander("Configure API Manually"):
                    app_id = st.text_input("App ID", value=os.getenv("META_APP_ID", ""))
                    app_secret = st.text_input("App Secret", type="password", value=os.getenv("META_APP_SECRET", ""))
                    access_token = st.text_input("Access Token", type="password", value=os.getenv("META_ACCESS_TOKEN", ""))
                    ad_account_id = st.text_input("Ad Account ID", value=selected_account or "", placeholder="act_123456789")

                    if st.button("Connect"):
                        client = MetaAdsClient(
                            app_id=app_id,
                            app_secret=app_secret,
                            access_token=access_token,
                            ad_account_id=ad_account_id,
                        )
                        if client.connect():
                            st.session_state.api_connected = True
                            st.session_state.client = client
                            st.success("Connected successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to connect. Check your credentials.")

        st.divider()

        # Win Rules
        st.subheader("Win Rules")
        min_roas = st.number_input(
            "Minimum ROAS",
            min_value=0.0,
            max_value=20.0,
            value=config.WIN_RULES["min_roas"],
            step=0.1,
            help="Creative must have ROAS >= this value to be a winner"
        )
        min_spend = st.number_input(
            "Minimum Spend ($)",
            min_value=0.0,
            max_value=10000.0,
            value=config.WIN_RULES["min_spend"],
            step=10.0,
            help="Creative must have spent >= this amount to qualify"
        )

        st.divider()

        # Date Range
        st.subheader("Date Range")
        date_end = st.date_input("End Date", value=datetime.now())
        date_start = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))

        st.divider()

        # AI Analysis
        st.subheader("AI Analysis")
        cache_stats = get_cache_stats()
        st.text(f"Cached: {cache_stats['cached_creatives']} creatives")

        if st.button("Clear Analysis Cache"):
            if clear_cache():
                st.success("Cache cleared!")
            else:
                st.error("Failed to clear cache")

        return {
            "min_roas": min_roas,
            "min_spend": min_spend,
            "date_start": date_start,
            "date_end": date_end,
            "use_demo": use_demo,
        }


def load_data(settings):
    """Load data from Meta API or demo data."""
    if settings["use_demo"]:
        return get_demo_data()

    if not st.session_state.api_connected:
        return None

    client = st.session_state.get("client")
    if not client:
        return None

    with st.spinner("Fetching data from Meta API..."):
        try:
            df = client.fetch_ads_data(
                date_start=datetime.combine(settings["date_start"], datetime.min.time()),
                date_end=datetime.combine(settings["date_end"], datetime.max.time()),
            )
            return df
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return None


def render_header(settings):
    """Render the main header with refresh button."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("Win Rate Tracker")

    with col2:
        # Last refresh time
        if st.session_state.last_refresh:
            time_ago = datetime.now() - st.session_state.last_refresh
            minutes = int(time_ago.total_seconds() / 60)
            st.caption(f"Last refresh: {minutes}m ago")
        else:
            st.caption("Not refreshed yet")

    with col3:
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.data = None
            st.session_state.last_refresh = datetime.now()
            st.rerun()


def main():
    """Main application entry point."""
    init_session_state()
    init_cache_db()

    # Render sidebar and get settings
    settings = render_sidebar()

    # Main content
    render_header(settings)

    # Load data if needed
    if st.session_state.data is None:
        df = load_data(settings)
        if df is not None:
            st.session_state.data = df
            st.session_state.last_refresh = datetime.now()
    else:
        df = st.session_state.data

    # Check if we have data
    if df is None or df.empty:
        st.info("No data available. Please connect to Meta API or enable Demo Data in the sidebar.")

        # Show setup instructions
        with st.expander("How to set up Meta API access"):
            st.markdown("""
            ### Step 1: Create a Meta Developer App
            1. Go to [Meta for Developers](https://developers.facebook.com/)
            2. Click "My Apps" → "Create App"
            3. Select "Business" as the app type
            4. Fill in app details and create

            ### Step 2: Add Marketing API
            1. In your app dashboard, click "Add Products"
            2. Find "Marketing API" and click "Set Up"

            ### Step 3: Get Access Token
            1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
            2. Select your app
            3. Click "Generate Access Token"
            4. Select permissions: `ads_read`, `ads_management`
            5. Copy the access token

            ### Step 4: Find your Ad Account ID
            1. Go to [Meta Business Suite](https://business.facebook.com/)
            2. Navigate to Ad Account Settings
            3. Copy the Account ID (format: `act_123456789`)

            ### Step 5: Configure the Dashboard
            Enter your credentials in the sidebar under "Meta API"
            """)

        return

    # Process data
    with st.spinner("Processing data..."):
        # Enrich with funnel and format
        df = enrich_data(df)

        # Apply win rules
        df = apply_win_rules(df, settings["min_roas"], settings["min_spend"])

        # AI analysis for angles (if not already done)
        if "angle" not in df.columns or df["angle"].isna().all():
            with st.spinner("Analyzing creatives with AI..."):
                progress = st.progress(0)
                def update_progress(current, total):
                    progress.progress(current / total)
                enrich_dataframe_with_angles(df, progress_callback=update_progress)
                progress.empty()

        # Update session state
        st.session_state.data = df

    # Calculate overview metrics
    metrics = calculate_overview_metrics(df)

    # Render overview section
    st.markdown("## Overview")
    render_metrics_cards(metrics)

    st.markdown("---")

    # Breakdown tabs
    tab_funnel, tab_format, tab_angle, tab_creator, tab_monthly = st.tabs([
        "Funnel", "Format", "Angle", "Creator", "Monthly"
    ])

    with tab_funnel:
        funnel_breakdown = calculate_breakdown(df, "funnel_stage")
        render_breakdown_table(funnel_breakdown, "Funnel Breakdown")

    with tab_format:
        format_breakdown = calculate_breakdown(df, "format")
        render_breakdown_table(format_breakdown, "Format Breakdown")

    with tab_angle:
        angle_breakdown = calculate_breakdown(df, "angle")
        render_breakdown_table(angle_breakdown, "Angle Breakdown")

    with tab_creator:
        if "creator" in df.columns:
            creator_breakdown = calculate_breakdown(df, "creator")
            render_breakdown_table(creator_breakdown, "Creator Breakdown")
        else:
            st.info("Creator data not available. Add 'creator' to your ad naming convention to enable this breakdown.")

    with tab_monthly:
        monthly_breakdown = calculate_breakdown(df, "launch_month")
        render_breakdown_table(monthly_breakdown, "Monthly Breakdown")

    # Detailed table
    st.markdown("---")
    with st.expander("View All Creatives"):
        render_detailed_table(df, "All Creatives")


if __name__ == "__main__":
    main()
