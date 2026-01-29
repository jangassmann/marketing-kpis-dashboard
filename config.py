"""Configuration settings for the Marketing KPIs Dashboard."""

# Default win rule thresholds (can be adjusted in sidebar)
WIN_RULES = {
    "min_roas": 2.0,
    "min_spend": 100.0,
}

# Angle categories for AI classification
ANGLE_CATEGORIES = [
    "Problem/Solution",
    "Social Proof",
    "Testimonial",
    "Before/After",
    "UGC Style",
    "Product Demo",
    "Lifestyle",
    "Urgency/Scarcity",
    "Educational",
    "Comparison",
    "Unboxing",
    "Other",
]

# Funnel stage mapping from Meta campaign objectives
OBJECTIVE_TO_FUNNEL = {
    "OUTCOME_AWARENESS": "TOF",
    "OUTCOME_ENGAGEMENT": "TOF",
    "OUTCOME_LEADS": "MOF",
    "OUTCOME_TRAFFIC": "MOF",
    "OUTCOME_APP_PROMOTION": "MOF",
    "OUTCOME_SALES": "BOF",
    "CONVERSIONS": "BOF",
    "LINK_CLICKS": "MOF",
    "REACH": "TOF",
    "BRAND_AWARENESS": "TOF",
    "VIDEO_VIEWS": "TOF",
    "POST_ENGAGEMENT": "TOF",
    "PAGE_LIKES": "TOF",
    "LEAD_GENERATION": "MOF",
    "MESSAGES": "MOF",
    "CATALOG_SALES": "BOF",
    "STORE_TRAFFIC": "BOF",
}

# Format detection based on creative type
FORMAT_MAPPING = {
    "VIDEO": "Video",
    "IMAGE": "Static",
    "CAROUSEL": "Carousel",
    "COLLECTION": "Collection",
    "SLIDESHOW": "Slideshow",
}

# Claude model for AI analysis
AI_MODEL = "claude-sonnet-4-20250514"
