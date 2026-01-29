"""Meta Ads API client for fetching ad creative data and metrics."""

import os
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.campaign import Campaign
from dotenv import load_dotenv

load_dotenv()


def get_available_ad_accounts() -> list:
    """Get list of available ad account IDs from environment."""
    # Check for multiple accounts first
    multi_accounts = os.getenv("META_AD_ACCOUNT_IDS", "")
    if multi_accounts:
        return [acc.strip() for acc in multi_accounts.split(",") if acc.strip()]

    # Fall back to single account
    single_account = os.getenv("META_AD_ACCOUNT_ID", "")
    if single_account:
        return [single_account]

    return []


class MetaAdsClient:
    """Client for interacting with Meta Ads API."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ):
        """Initialize the Meta Ads API client."""
        self.app_id = app_id or os.getenv("META_APP_ID")
        self.app_secret = app_secret or os.getenv("META_APP_SECRET")
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")

        # Get ad account - use provided one or first from list
        if ad_account_id:
            self.ad_account_id = ad_account_id
        else:
            accounts = get_available_ad_accounts()
            self.ad_account_id = accounts[0] if accounts else None

        self._api = None
        self._account = None

    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return all([
            self.app_id,
            self.app_secret,
            self.access_token,
            self.ad_account_id,
        ])

    def connect(self) -> bool:
        """Initialize the API connection."""
        if not self.is_configured():
            return False

        try:
            FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
            )
            self._api = FacebookAdsApi.get_default_api()
            self._account = AdAccount(self.ad_account_id)
            # Test the connection
            self._account.api_get(fields=["name"])
            return True
        except Exception as e:
            print(f"Failed to connect to Meta API: {e}")
            return False

    def get_account_name(self) -> str:
        """Get the ad account name."""
        if not self._account:
            return "Not connected"
        try:
            account_data = self._account.api_get(fields=["name"])
            return account_data.get("name", "Unknown")
        except Exception:
            return "Unknown"

    def fetch_ads_data(
        self,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """
        Fetch all ads with their performance metrics.

        Returns a DataFrame with columns:
        - ad_id, ad_name, campaign_id, campaign_name, adset_id, adset_name
        - creative_id, creative_type, thumbnail_url, primary_text, headline
        - objective, spend, impressions, clicks, conversions, roas
        - date_start, date_end
        """
        if not self._account:
            raise ConnectionError("Not connected to Meta API")

        # Default to last 30 days
        if not date_end:
            date_end = datetime.now()
        if not date_start:
            date_start = date_end - timedelta(days=30)

        date_preset = None
        time_range = {
            "since": date_start.strftime("%Y-%m-%d"),
            "until": date_end.strftime("%Y-%m-%d"),
        }

        # Fetch ads with insights
        ads_data = []

        try:
            # Get all ads
            ads = self._account.get_ads(
                fields=[
                    Ad.Field.id,
                    Ad.Field.name,
                    Ad.Field.campaign_id,
                    Ad.Field.adset_id,
                    Ad.Field.creative,
                    Ad.Field.status,
                    Ad.Field.created_time,
                ],
                params={
                    "limit": limit,
                    "date_preset": "last_30d",
                }
            )

            # Build campaign and adset lookup
            campaigns = {}
            adsets = {}

            for ad in ads:
                ad_id = ad.get("id")
                campaign_id = ad.get("campaign_id")
                adset_id = ad.get("adset_id")
                creative_data = ad.get("creative", {})
                creative_id = creative_data.get("id") if creative_data else None

                # Fetch campaign details if not cached
                if campaign_id and campaign_id not in campaigns:
                    try:
                        campaign = Campaign(campaign_id)
                        campaign_info = campaign.api_get(fields=["name", "objective"])
                        campaigns[campaign_id] = {
                            "name": campaign_info.get("name", ""),
                            "objective": campaign_info.get("objective", ""),
                        }
                    except Exception:
                        campaigns[campaign_id] = {"name": "", "objective": ""}

                # Fetch adset name if not cached
                if adset_id and adset_id not in adsets:
                    try:
                        from facebook_business.adobjects.adset import AdSet
                        adset = AdSet(adset_id)
                        adset_info = adset.api_get(fields=["name"])
                        adsets[adset_id] = adset_info.get("name", "")
                    except Exception:
                        adsets[adset_id] = ""

                # Fetch creative details
                creative_type = ""
                thumbnail_url = ""
                primary_text = ""
                headline = ""
                image_url = ""
                video_id = ""

                if creative_id:
                    try:
                        creative = AdCreative(creative_id)
                        creative_info = creative.api_get(fields=[
                            "object_type",
                            "thumbnail_url",
                            "body",
                            "title",
                            "image_url",
                            "video_id",
                            "asset_feed_spec",
                        ])
                        creative_type = creative_info.get("object_type", "")
                        thumbnail_url = creative_info.get("thumbnail_url", "")
                        primary_text = creative_info.get("body", "")
                        headline = creative_info.get("title", "")
                        image_url = creative_info.get("image_url", "")
                        video_id = creative_info.get("video_id", "")
                    except Exception:
                        pass

                # Fetch insights for this ad
                spend = 0
                impressions = 0
                clicks = 0
                conversions = 0
                purchase_value = 0
                roas = 0

                try:
                    insights = Ad(ad_id).get_insights(
                        fields=[
                            "spend",
                            "impressions",
                            "clicks",
                            "actions",
                            "action_values",
                            "purchase_roas",
                        ],
                        params={
                            "time_range": time_range,
                        }
                    )
                    if insights:
                        insight = insights[0]
                        spend = float(insight.get("spend", 0))
                        impressions = int(insight.get("impressions", 0))
                        clicks = int(insight.get("clicks", 0))

                        # Extract conversions from actions
                        actions = insight.get("actions", [])
                        for action in actions:
                            if action.get("action_type") == "purchase":
                                conversions = int(action.get("value", 0))
                                break

                        # Extract purchase value
                        action_values = insight.get("action_values", [])
                        for av in action_values:
                            if av.get("action_type") == "purchase":
                                purchase_value = float(av.get("value", 0))
                                break

                        # Get ROAS
                        purchase_roas = insight.get("purchase_roas", [])
                        if purchase_roas:
                            roas = float(purchase_roas[0].get("value", 0))
                        elif spend > 0:
                            roas = purchase_value / spend
                except Exception:
                    pass

                campaign_info = campaigns.get(campaign_id, {})

                ads_data.append({
                    "ad_id": ad_id,
                    "ad_name": ad.get("name", ""),
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_info.get("name", ""),
                    "objective": campaign_info.get("objective", ""),
                    "adset_id": adset_id,
                    "adset_name": adsets.get(adset_id, ""),
                    "creative_id": creative_id,
                    "creative_type": creative_type,
                    "thumbnail_url": thumbnail_url,
                    "image_url": image_url,
                    "video_id": video_id,
                    "primary_text": primary_text,
                    "headline": headline,
                    "status": ad.get("status", ""),
                    "created_time": ad.get("created_time", ""),
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "purchase_value": purchase_value,
                    "roas": roas,
                    "date_start": date_start.strftime("%Y-%m-%d"),
                    "date_end": date_end.strftime("%Y-%m-%d"),
                })

        except Exception as e:
            print(f"Error fetching ads: {e}")
            raise

        return pd.DataFrame(ads_data)


def get_demo_data() -> pd.DataFrame:
    """Generate demo data for testing without API credentials."""
    import random

    formats = ["VIDEO", "IMAGE", "CAROUSEL"]
    objectives = ["OUTCOME_SALES", "OUTCOME_TRAFFIC", "OUTCOME_AWARENESS"]
    angles = ["Problem/Solution", "UGC Style", "Product Demo", "Social Proof", "Before/After"]
    creators = ["Sarah", "Mike", "Team", "Agency", "Influencer"]

    data = []
    for i in range(50):
        spend = random.uniform(50, 5000)
        roas = random.uniform(0.5, 6.0)
        format_type = random.choice(formats)
        objective = random.choice(objectives)

        data.append({
            "ad_id": f"ad_{i+1}",
            "ad_name": f"Ad Creative {i+1}",
            "campaign_id": f"camp_{(i % 5) + 1}",
            "campaign_name": f"Campaign {(i % 5) + 1}",
            "objective": objective,
            "adset_id": f"adset_{(i % 10) + 1}",
            "adset_name": f"Adset {(i % 10) + 1}",
            "creative_id": f"creative_{i+1}",
            "creative_type": format_type,
            "thumbnail_url": "",
            "image_url": "",
            "video_id": "",
            "primary_text": f"Check out our amazing product! Limited time offer.",
            "headline": f"Get 50% Off Today",
            "status": "ACTIVE",
            "created_time": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            "spend": round(spend, 2),
            "impressions": int(spend * random.uniform(50, 150)),
            "clicks": int(spend * random.uniform(1, 5)),
            "conversions": int(spend * roas / random.uniform(30, 100)),
            "purchase_value": round(spend * roas, 2),
            "roas": round(roas, 2),
            "date_start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "date_end": datetime.now().strftime("%Y-%m-%d"),
            "angle": random.choice(angles),
            "creator": random.choice(creators),
        })

    return pd.DataFrame(data)
