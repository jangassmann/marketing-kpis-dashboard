"""Breakdown table component for displaying metrics by dimension."""

import streamlit as st
import pandas as pd
from typing import Optional


def render_breakdown_table(
    df: pd.DataFrame,
    title: str = "Breakdown",
    show_drill_down: bool = True,
):
    """
    Render a breakdown table with metrics.

    Args:
        df: DataFrame with columns: name, total_ads, winners, win_rate, spend, roas
        title: Title for the table section
        show_drill_down: Whether to show drill-down arrows
    """
    if df.empty:
        st.info("No data available for this breakdown.")
        return

    st.markdown(f"### {title}")

    # Style the dataframe
    def style_win_rate(val):
        """Style win rate with colored badges."""
        if val >= 35:
            return "background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 12px; font-weight: 500;"
        elif val >= 25:
            return "background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 12px; font-weight: 500;"
        else:
            return "background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 12px; font-weight: 500;"

    # Create a display copy
    display_df = df.copy()

    # Format columns
    display_df["spend"] = display_df["spend"].apply(lambda x: f"${x:,.0f}")
    display_df["win_rate"] = display_df["win_rate"].apply(lambda x: f"{x}%")

    # Rename columns for display
    display_df = display_df.rename(columns={
        "name": "Name",
        "total_ads": "Total Ads",
        "winners": "Winners",
        "win_rate": "Win Rate",
        "spend": "Spend",
        "roas": "ROAS",
    })

    # Use Streamlit's native dataframe with column config
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Total Ads": st.column_config.NumberColumn("Total Ads", format="%d"),
            "Winners": st.column_config.NumberColumn("Winners", format="%d"),
            "Win Rate": st.column_config.TextColumn("Win Rate", width="small"),
            "Spend": st.column_config.TextColumn("Spend", width="small"),
            "ROAS": st.column_config.NumberColumn("ROAS", format="%.2f"),
        }
    )


def render_detailed_table(
    df: pd.DataFrame,
    title: str = "All Creatives",
):
    """
    Render a detailed table with all creative data.

    Args:
        df: Full DataFrame with ad data
        title: Title for the section
    """
    if df.empty:
        st.info("No creatives to display.")
        return

    st.markdown(f"### {title}")

    # Select columns to display
    display_cols = [
        "ad_name",
        "format",
        "funnel_stage",
        "angle",
        "spend",
        "roas",
        "is_winner",
    ]

    # Filter to existing columns
    display_cols = [c for c in display_cols if c in df.columns]

    display_df = df[display_cols].copy()

    # Format columns
    if "spend" in display_df.columns:
        display_df["spend"] = display_df["spend"].apply(lambda x: f"${x:,.0f}")
    if "roas" in display_df.columns:
        display_df["roas"] = display_df["roas"].apply(lambda x: f"{x:.2f}")
    if "is_winner" in display_df.columns:
        display_df["is_winner"] = display_df["is_winner"].apply(lambda x: "Winner" if x else "-")

    # Rename columns
    rename_map = {
        "ad_name": "Creative Name",
        "format": "Format",
        "funnel_stage": "Funnel",
        "angle": "Angle",
        "spend": "Spend",
        "roas": "ROAS",
        "is_winner": "Status",
    }
    display_df = display_df.rename(columns=rename_map)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_win_rate_badge(win_rate: float) -> str:
    """Return HTML for a win rate badge."""
    if win_rate >= 35:
        bg_color = "#d4edda"
        text_color = "#155724"
    elif win_rate >= 25:
        bg_color = "#fff3cd"
        text_color = "#856404"
    else:
        bg_color = "#f8d7da"
        text_color = "#721c24"

    return f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 500;
        font-size: 13px;
    ">{win_rate}%</span>
    """
