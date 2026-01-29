"""Data processing and win rate calculations."""

import pandas as pd
from typing import Tuple, Dict, Any
from datetime import datetime
import config


def apply_win_rules(
    df: pd.DataFrame,
    min_roas: float = None,
    min_spend: float = None,
) -> pd.DataFrame:
    """
    Apply win rules to determine which creatives are winners.

    A creative is a winner if:
    - ROAS >= min_roas threshold
    - Spend >= min_spend (to have statistical significance)
    """
    if min_roas is None:
        min_roas = config.WIN_RULES["min_roas"]
    if min_spend is None:
        min_spend = config.WIN_RULES["min_spend"]

    df = df.copy()

    # Mark qualified ads (those with enough spend)
    df["is_qualified"] = df["spend"] >= min_spend

    # Mark winners (qualified AND meets ROAS threshold)
    df["is_winner"] = df["is_qualified"] & (df["roas"] >= min_roas)

    return df


def calculate_overview_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate overview metrics for the dashboard.

    Returns:
        Dictionary with total_ads, total_winners, win_rate, blended_roas
    """
    total_ads = len(df)
    qualified_ads = len(df[df["is_qualified"]])
    total_winners = df["is_winner"].sum()

    # Win rate is winners / qualified ads
    win_rate = (total_winners / qualified_ads * 100) if qualified_ads > 0 else 0

    # Blended ROAS is total revenue / total spend
    total_spend = df["spend"].sum()
    total_revenue = df["purchase_value"].sum()
    blended_roas = total_revenue / total_spend if total_spend > 0 else 0

    return {
        "total_ads": total_ads,
        "total_winners": int(total_winners),
        "win_rate": round(win_rate, 1),
        "blended_roas": round(blended_roas, 2),
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "qualified_ads": qualified_ads,
    }


def get_funnel_stage(objective: str) -> str:
    """Map campaign objective to funnel stage."""
    return config.OBJECTIVE_TO_FUNNEL.get(objective, "Unknown")


def get_format_name(creative_type: str) -> str:
    """Map creative type to readable format name."""
    return config.FORMAT_MAPPING.get(creative_type, creative_type or "Unknown")


def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich the data with derived columns.

    Adds: funnel_stage, format
    """
    df = df.copy()

    # Add funnel stage based on campaign objective
    df["funnel_stage"] = df["objective"].apply(get_funnel_stage)

    # Add format name
    df["format"] = df["creative_type"].apply(get_format_name)

    # Parse launch month from created_time
    def parse_month(created_time):
        if not created_time:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(created_time.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m")
        except Exception:
            return "Unknown"

    df["launch_month"] = df["created_time"].apply(parse_month)

    return df


def calculate_breakdown(
    df: pd.DataFrame,
    group_by: str,
) -> pd.DataFrame:
    """
    Calculate metrics breakdown by a specific dimension.

    Args:
        df: DataFrame with ad data (must have is_winner, is_qualified columns)
        group_by: Column to group by (format, funnel_stage, angle, creator, launch_month)

    Returns:
        DataFrame with columns: name, total_ads, winners, win_rate, spend, roas
    """
    if group_by not in df.columns:
        return pd.DataFrame()

    # Group and aggregate
    grouped = df.groupby(group_by).agg({
        "ad_id": "count",
        "is_winner": "sum",
        "is_qualified": "sum",
        "spend": "sum",
        "purchase_value": "sum",
    }).reset_index()

    grouped.columns = [group_by, "total_ads", "winners", "qualified", "spend", "revenue"]

    # Calculate win rate and ROAS
    grouped["win_rate"] = grouped.apply(
        lambda r: round(r["winners"] / r["qualified"] * 100, 1) if r["qualified"] > 0 else 0,
        axis=1
    )
    grouped["roas"] = grouped.apply(
        lambda r: round(r["revenue"] / r["spend"], 2) if r["spend"] > 0 else 0,
        axis=1
    )

    # Rename the group column to 'name' for consistency
    grouped = grouped.rename(columns={group_by: "name"})

    # Select and order final columns
    result = grouped[["name", "total_ads", "winners", "win_rate", "spend", "roas"]]

    # Sort by win rate descending
    result = result.sort_values("win_rate", ascending=False)

    return result


def filter_data(
    df: pd.DataFrame,
    funnel: str = None,
    format_type: str = None,
    angle: str = None,
    creator: str = None,
    min_spend: float = None,
    max_spend: float = None,
) -> pd.DataFrame:
    """Apply filters to the data."""
    filtered = df.copy()

    if funnel and funnel != "All":
        filtered = filtered[filtered["funnel_stage"] == funnel]

    if format_type and format_type != "All":
        filtered = filtered[filtered["format"] == format_type]

    if angle and angle != "All":
        filtered = filtered[filtered["angle"] == angle]

    if creator and creator != "All":
        filtered = filtered[filtered["creator"] == creator]

    if min_spend is not None:
        filtered = filtered[filtered["spend"] >= min_spend]

    if max_spend is not None:
        filtered = filtered[filtered["spend"] <= max_spend]

    return filtered
