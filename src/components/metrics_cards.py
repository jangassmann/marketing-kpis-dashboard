"""Metrics cards component for the dashboard overview."""

import streamlit as st
from typing import Dict, Any


def render_metrics_cards(metrics: Dict[str, Any]):
    """
    Render the overview metrics cards.

    Args:
        metrics: Dictionary with total_ads, total_winners, win_rate, blended_roas
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">
            <p style="color: #6c757d; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Total Ads</p>
            <p style="font-size: 32px; font-weight: 600; margin: 8px 0 4px 0; color: #212529;">{:,}</p>
            <p style="color: #6c757d; font-size: 13px; margin: 0;">Active campaigns</p>
        </div>
        """.format(metrics["total_ads"]), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">
            <p style="color: #6c757d; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Total Winners</p>
            <p style="font-size: 32px; font-weight: 600; margin: 8px 0 4px 0; color: #212529;">{:,}</p>
            <p style="color: #6c757d; font-size: 13px; margin: 0;">All tiers</p>
        </div>
        """.format(metrics["total_winners"]), unsafe_allow_html=True)

    with col3:
        win_rate = metrics["win_rate"]
        color = "#28a745" if win_rate >= 30 else "#ffc107" if win_rate >= 20 else "#dc3545"
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">
            <p style="color: #6c757d; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Win Rate</p>
            <p style="font-size: 32px; font-weight: 600; margin: 8px 0 4px 0; color: {color};">{rate}%</p>
            <p style="color: #6c757d; font-size: 13px; margin: 0;">Last 30 days</p>
        </div>
        """.format(color=color, rate=win_rate), unsafe_allow_html=True)

    with col4:
        roas = metrics["blended_roas"]
        roas_color = "#28a745" if roas >= 3 else "#ffc107" if roas >= 2 else "#dc3545"
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">
            <p style="color: #6c757d; font-size: 12px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Blended ROAS</p>
            <p style="font-size: 32px; font-weight: 600; margin: 8px 0 4px 0; color: {color};">{roas}</p>
            <p style="color: #6c757d; font-size: 13px; margin: 0;">${spend:,.0f} spend</p>
        </div>
        """.format(color=roas_color, roas=roas, spend=metrics.get("total_spend", 0)), unsafe_allow_html=True)


def render_mini_stat(label: str, value: str, sublabel: str = "", delta: str = ""):
    """Render a small stat card."""
    delta_html = ""
    if delta:
        delta_color = "#28a745" if delta.startswith("+") else "#dc3545"
        delta_html = f'<span style="color: {delta_color}; font-size: 12px; margin-left: 8px;">{delta}</span>'

    st.markdown(f"""
    <div style="padding: 12px 0;">
        <p style="color: #6c757d; font-size: 11px; margin: 0; text-transform: uppercase;">{label}</p>
        <p style="font-size: 20px; font-weight: 600; margin: 4px 0; color: #212529;">{value}{delta_html}</p>
        {f'<p style="color: #868e96; font-size: 12px; margin: 0;">{sublabel}</p>' if sublabel else ''}
    </div>
    """, unsafe_allow_html=True)
