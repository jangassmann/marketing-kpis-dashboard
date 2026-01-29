"""AI-powered creative analysis using Claude for angle detection."""

import os
import json
import sqlite3
import base64
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import anthropic
from dotenv import load_dotenv
import config

load_dotenv()

# Database path for caching analysis results
DB_PATH = "creative_analysis_cache.db"


def init_cache_db():
    """Initialize the SQLite database for caching analysis results."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS creative_analysis (
            creative_id TEXT PRIMARY KEY,
            angle TEXT,
            hook_type TEXT,
            tone TEXT,
            key_claim TEXT,
            confidence REAL,
            analyzed_at TEXT,
            raw_response TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_cached_analysis(creative_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached analysis for a creative."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT angle, hook_type, tone, key_claim, confidence FROM creative_analysis WHERE creative_id = ?",
            (creative_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "angle": row[0],
                "hook_type": row[1],
                "tone": row[2],
                "key_claim": row[3],
                "confidence": row[4],
            }
    except Exception:
        pass
    return None


def cache_analysis(creative_id: str, analysis: Dict[str, Any], raw_response: str = ""):
    """Cache analysis results for a creative."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO creative_analysis
            (creative_id, angle, hook_type, tone, key_claim, confidence, analyzed_at, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            creative_id,
            analysis.get("angle", "Unknown"),
            analysis.get("hook_type", ""),
            analysis.get("tone", ""),
            analysis.get("key_claim", ""),
            analysis.get("confidence", 0),
            datetime.now().isoformat(),
            raw_response,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching analysis: {e}")


def fetch_image_as_base64(url: str) -> Optional[str]:
    """Fetch an image from URL and convert to base64."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return base64.standard_b64encode(response.content).decode("utf-8")
    except Exception:
        pass
    return None


def get_image_media_type(url: str) -> str:
    """Determine media type from URL."""
    url_lower = url.lower()
    if ".png" in url_lower:
        return "image/png"
    elif ".gif" in url_lower:
        return "image/gif"
    elif ".webp" in url_lower:
        return "image/webp"
    return "image/jpeg"


def analyze_creative(
    creative_id: str,
    primary_text: str = "",
    headline: str = "",
    image_url: str = "",
    thumbnail_url: str = "",
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a creative using Claude to determine its marketing angle.

    Args:
        creative_id: Unique identifier for the creative
        primary_text: The main ad copy text
        headline: The ad headline
        image_url: URL to the creative image
        thumbnail_url: URL to video thumbnail (fallback if no image_url)
        use_cache: Whether to use cached results

    Returns:
        Dictionary with angle, hook_type, tone, key_claim, confidence
    """
    # Check cache first
    if use_cache:
        cached = get_cached_analysis(creative_id)
        if cached:
            return cached

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "angle": "Unknown",
            "hook_type": "API key not configured",
            "tone": "",
            "key_claim": "",
            "confidence": 0,
        }

    # Prepare the image
    image_to_use = image_url or thumbnail_url
    image_base64 = fetch_image_as_base64(image_to_use) if image_to_use else None

    # Build the prompt
    angle_list = ", ".join(config.ANGLE_CATEGORIES)

    prompt = f"""Analyze this ad creative and categorize its marketing angle.

Ad Copy (Primary Text): {primary_text or "Not provided"}
Headline: {headline or "Not provided"}

Based on the ad copy and image (if provided), classify the creative into ONE of these angle categories:
{angle_list}

Also identify:
- Hook type: What technique is used to grab attention in the first line/seconds?
- Tone: What is the emotional tone? (e.g., Empathetic, Urgent, Aspirational, Educational, Humorous)
- Key claim: What is the main promise or benefit being communicated?

Respond with ONLY a JSON object in this exact format:
{{
  "angle": "One of the categories listed above",
  "hook_type": "Brief description of the hook technique",
  "tone": "One word describing the tone",
  "key_claim": "The main promise in one sentence",
  "confidence": 0.85
}}

The confidence should be between 0 and 1, where 1 means very confident in the classification."""

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build message content
        content = []

        # Add image if available
        if image_base64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": get_image_media_type(image_to_use),
                    "data": image_base64,
                }
            })

        content.append({
            "type": "text",
            "text": prompt,
        })

        # Call Claude API
        message = client.messages.create(
            model=config.AI_MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": content}
            ]
        )

        # Parse response
        response_text = message.content[0].text

        # Try to extract JSON from response
        try:
            # Find JSON in response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)

                # Validate and normalize the angle
                if analysis.get("angle") not in config.ANGLE_CATEGORIES:
                    # Find closest match or default to "Other"
                    analysis["angle"] = "Other"

                # Cache the result
                cache_analysis(creative_id, analysis, response_text)

                return analysis
        except json.JSONDecodeError:
            pass

        # Fallback if JSON parsing fails
        return {
            "angle": "Unknown",
            "hook_type": "Analysis failed",
            "tone": "",
            "key_claim": "",
            "confidence": 0,
        }

    except Exception as e:
        return {
            "angle": "Unknown",
            "hook_type": f"Error: {str(e)[:50]}",
            "tone": "",
            "key_claim": "",
            "confidence": 0,
        }


def analyze_creatives_batch(
    creatives: List[Dict[str, Any]],
    use_cache: bool = True,
    progress_callback=None,
) -> List[Dict[str, Any]]:
    """
    Analyze multiple creatives and return results.

    Args:
        creatives: List of dicts with creative_id, primary_text, headline, image_url, thumbnail_url
        use_cache: Whether to use cached results
        progress_callback: Optional callback function(current, total) for progress updates

    Returns:
        List of analysis results
    """
    init_cache_db()
    results = []

    for i, creative in enumerate(creatives):
        if progress_callback:
            progress_callback(i + 1, len(creatives))

        analysis = analyze_creative(
            creative_id=creative.get("creative_id", ""),
            primary_text=creative.get("primary_text", ""),
            headline=creative.get("headline", ""),
            image_url=creative.get("image_url", ""),
            thumbnail_url=creative.get("thumbnail_url", ""),
            use_cache=use_cache,
        )

        results.append({
            "creative_id": creative.get("creative_id", ""),
            **analysis,
        })

    return results


def enrich_dataframe_with_angles(df, progress_callback=None) -> None:
    """
    Add angle analysis to a DataFrame in place.

    Adds columns: angle, hook_type, tone, key_claim, confidence
    """
    import pandas as pd

    init_cache_db()

    # Prepare creative data for batch analysis
    creatives = df[[
        "creative_id", "primary_text", "headline", "image_url", "thumbnail_url"
    ]].to_dict("records")

    # Analyze
    results = analyze_creatives_batch(creatives, progress_callback=progress_callback)

    # Create a lookup dict
    analysis_lookup = {r["creative_id"]: r for r in results}

    # Add columns to dataframe
    df["angle"] = df["creative_id"].apply(
        lambda cid: analysis_lookup.get(cid, {}).get("angle", "Unknown")
    )
    df["hook_type"] = df["creative_id"].apply(
        lambda cid: analysis_lookup.get(cid, {}).get("hook_type", "")
    )
    df["tone"] = df["creative_id"].apply(
        lambda cid: analysis_lookup.get(cid, {}).get("tone", "")
    )
    df["key_claim"] = df["creative_id"].apply(
        lambda cid: analysis_lookup.get(cid, {}).get("key_claim", "")
    )
    df["ai_confidence"] = df["creative_id"].apply(
        lambda cid: analysis_lookup.get(cid, {}).get("confidence", 0)
    )


def clear_cache():
    """Clear all cached analysis results."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM creative_analysis")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the analysis cache."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM creative_analysis")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(analyzed_at), MAX(analyzed_at) FROM creative_analysis")
        dates = cursor.fetchone()
        conn.close()

        return {
            "cached_creatives": count,
            "oldest_analysis": dates[0],
            "newest_analysis": dates[1],
        }
    except Exception:
        return {
            "cached_creatives": 0,
            "oldest_analysis": None,
            "newest_analysis": None,
        }
