"""Meta Ads API client for fetching ad creative data and metrics."""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
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
    multi_accounts = os.getenv("META_AD_ACCOUNT_IDS", "")
    if multi_accounts:
        return [acc.strip() for acc in multi_accounts.split(",") if acc.strip()]
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
        self.app_id = app_id or os.getenv("META_APP_ID")
        self.app_secret = app_secret or os.getenv("META_APP_SECRET")
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")

        if ad_account_id:
            self.ad_account_id = ad_account_id
        else:
            accounts = get_available_ad_accounts()
            self.ad_account_id = accounts[0] if accounts else None

        self._api = None
        self._account = None
        self._initialized = False

    def is_configured(self) -> bool:
        return all([self.app_id, self.app_secret, self.access_token, self.ad_account_id])

    def _ensure_initialized(self):
        """Ensure API is initialized."""
        if not self._initialized and self.access_token:
            try:
                FacebookAdsApi.init(
                    app_id=self.app_id,
                    app_secret=self.app_secret,
                    access_token=self.access_token,
                )
                self._initialized = True
            except Exception:
                pass

    def connect(self) -> bool:
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
            self._account.api_get(fields=["name"])
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to connect to Meta API: {e}")
            return False

    def get_account_name(self) -> str:
        if not self._account:
            return "Not connected"
        try:
            account_data = self._account.api_get(fields=["name"])
            return account_data.get("name", "Unknown")
        except Exception:
            return "Unknown"

    def fetch_account_insights(
        self,
        date_start: datetime,
        date_end: datetime,
    ) -> Dict[str, Any]:
        """Fetch account-level insights for the date range."""
        if not self._account:
            raise ConnectionError("Not connected to Meta API")

        time_range = {
            "since": date_start.strftime("%Y-%m-%d"),
            "until": date_end.strftime("%Y-%m-%d"),
        }

        try:
            insights = self._account.get_insights(
                fields=[
                    "spend",
                    "impressions",
                    "clicks",
                    "cpc",
                    "cpm",
                    "ctr",
                    "actions",
                    "action_values",
                    "purchase_roas",
                    "cost_per_action_type",
                ],
                params={"time_range": time_range}
            )

            if not insights:
                return {}

            data = insights[0]
            spend = float(data.get("spend", 0))
            impressions = int(data.get("impressions", 0))
            clicks = int(data.get("clicks", 0))
            cpc = float(data.get("cpc", 0))
            cpm = float(data.get("cpm", 0))

            # Extract purchases and value
            purchases = 0
            purchase_value = 0
            actions = data.get("actions", [])
            for action in actions:
                if action.get("action_type") == "purchase":
                    purchases = int(action.get("value", 0))
                    break

            action_values = data.get("action_values", [])
            for av in action_values:
                if av.get("action_type") == "purchase":
                    purchase_value = float(av.get("value", 0))
                    break

            # ROAS
            roas = 0
            purchase_roas = data.get("purchase_roas", [])
            if purchase_roas:
                roas = float(purchase_roas[0].get("value", 0))
            elif spend > 0:
                roas = purchase_value / spend

            # CPA
            cpa = 0
            cost_per_action = data.get("cost_per_action_type", [])
            for cpa_data in cost_per_action:
                if cpa_data.get("action_type") == "purchase":
                    cpa = float(cpa_data.get("value", 0))
                    break

            # AOV
            aov = purchase_value / purchases if purchases > 0 else 0

            return {
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "purchases": purchases,
                "purchase_value": purchase_value,
                "roas": roas,
                "cpa": cpa,
                "aov": aov,
                "cpc": cpc,
                "cpm": cpm,
            }

        except Exception as e:
            print(f"Error fetching account insights: {e}")
            return {}

    def fetch_daily_insights(
        self,
        date_start: datetime,
        date_end: datetime,
    ) -> pd.DataFrame:
        """Fetch daily account insights for sparklines."""
        if not self._account:
            raise ConnectionError("Not connected to Meta API")

        time_range = {
            "since": date_start.strftime("%Y-%m-%d"),
            "until": date_end.strftime("%Y-%m-%d"),
        }

        try:
            insights = self._account.get_insights(
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
                    "time_increment": 1,  # Daily breakdown
                }
            )

            daily_data = []
            for day in insights:
                spend = float(day.get("spend", 0))

                purchases = 0
                purchase_value = 0
                for action in day.get("actions", []):
                    if action.get("action_type") == "purchase":
                        purchases = int(action.get("value", 0))
                        break
                for av in day.get("action_values", []):
                    if av.get("action_type") == "purchase":
                        purchase_value = float(av.get("value", 0))
                        break

                roas = 0
                purchase_roas = day.get("purchase_roas", [])
                if purchase_roas:
                    roas = float(purchase_roas[0].get("value", 0))
                elif spend > 0:
                    roas = purchase_value / spend

                daily_data.append({
                    "date": day.get("date_start"),
                    "spend": spend,
                    "roas": roas,
                    "purchases": purchases,
                    "purchase_value": purchase_value,
                })

            return pd.DataFrame(daily_data)

        except Exception as e:
            print(f"Error fetching daily insights: {e}")
            return pd.DataFrame()

    def fetch_ads_data(
        self,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch all ads with their performance metrics."""
        if not self._account:
            raise ConnectionError("Not connected to Meta API")

        if not date_end:
            date_end = datetime.now()
        if not date_start:
            date_start = date_end - timedelta(days=30)

        time_range = {
            "since": date_start.strftime("%Y-%m-%d"),
            "until": date_end.strftime("%Y-%m-%d"),
        }

        ads_data = []

        try:
            # Get ads with insights in one call for efficiency
            ads = self._account.get_insights(
                fields=[
                    "ad_id",
                    "ad_name",
                    "campaign_id",
                    "campaign_name",
                    "adset_id",
                    "adset_name",
                    "spend",
                    "impressions",
                    "clicks",
                    "cpc",
                    "cpm",
                    "actions",
                    "action_values",
                    "purchase_roas",
                    "cost_per_action_type",
                    # Video metrics
                    "video_play_actions",
                    "video_p25_watched_actions",
                    "video_p50_watched_actions",
                    "video_p75_watched_actions",
                    "video_p100_watched_actions",
                    "video_avg_time_watched_actions",
                    "video_thruplay_watched_actions",
                ],
                params={
                    "time_range": time_range,
                    "level": "ad",
                    "limit": limit,
                }
            )

            # Collect ad IDs to fetch creative info
            ad_ids = []
            ads_list = list(ads)

            for ad_data in ads_list:
                ad_id = ad_data.get("ad_id")
                spend = float(ad_data.get("spend", 0))
                impressions = int(ad_data.get("impressions", 0))
                clicks = int(ad_data.get("clicks", 0))
                cpc = float(ad_data.get("cpc", 0)) if ad_data.get("cpc") else 0
                cpm = float(ad_data.get("cpm", 0)) if ad_data.get("cpm") else 0

                # Extract purchases
                purchases = 0
                purchase_value = 0
                for action in ad_data.get("actions", []):
                    if action.get("action_type") == "purchase":
                        purchases = int(action.get("value", 0))
                        break
                for av in ad_data.get("action_values", []):
                    if av.get("action_type") == "purchase":
                        purchase_value = float(av.get("value", 0))
                        break

                # ROAS
                roas = 0
                purchase_roas = ad_data.get("purchase_roas", [])
                if purchase_roas:
                    roas = float(purchase_roas[0].get("value", 0))
                elif spend > 0:
                    roas = purchase_value / spend

                # CPA
                cpa = 0
                for cpa_data in ad_data.get("cost_per_action_type", []):
                    if cpa_data.get("action_type") == "purchase":
                        cpa = float(cpa_data.get("value", 0))
                        break

                # Video metrics
                video_plays = 0
                video_play_actions = ad_data.get("video_play_actions", [])
                if video_play_actions:
                    video_plays = int(video_play_actions[0].get("value", 0))

                # 3-second views (Thumbstop) - can be "video_view" or in video_play_actions
                video_3s_views = 0
                for action in ad_data.get("actions", []):
                    action_type = action.get("action_type", "")
                    # Try multiple possible action types for 3-second views
                    if action_type in ["video_view", "video_play", "video_avg_time_watched"]:
                        video_3s_views = int(action.get("value", 0))
                        break

                # If no 3s views found, try using video_plays as fallback
                if video_3s_views == 0 and video_plays > 0:
                    video_3s_views = video_plays

                # Video completion percentages
                video_p25 = 0
                video_p50 = 0
                video_p75 = 0
                video_p100 = 0
                video_thruplay = 0
                video_avg_time = 0

                p25_actions = ad_data.get("video_p25_watched_actions", [])
                if p25_actions:
                    video_p25 = int(p25_actions[0].get("value", 0))

                p50_actions = ad_data.get("video_p50_watched_actions", [])
                if p50_actions:
                    video_p50 = int(p50_actions[0].get("value", 0))

                p75_actions = ad_data.get("video_p75_watched_actions", [])
                if p75_actions:
                    video_p75 = int(p75_actions[0].get("value", 0))

                p100_actions = ad_data.get("video_p100_watched_actions", [])
                if p100_actions:
                    video_p100 = int(p100_actions[0].get("value", 0))

                thruplay_actions = ad_data.get("video_thruplay_watched_actions", [])
                if thruplay_actions:
                    video_thruplay = int(thruplay_actions[0].get("value", 0))

                avg_time_actions = ad_data.get("video_avg_time_watched_actions", [])
                if avg_time_actions:
                    video_avg_time = float(avg_time_actions[0].get("value", 0))

                ads_data.append({
                    "ad_id": ad_id,
                    "ad_name": ad_data.get("ad_name", ""),
                    "campaign_id": ad_data.get("campaign_id", ""),
                    "campaign_name": ad_data.get("campaign_name", ""),
                    "adset_id": ad_data.get("adset_id", ""),
                    "adset_name": ad_data.get("adset_name", ""),
                    "spend": spend,
                    "impressions": impressions,
                    "clicks": clicks,
                    "purchases": purchases,
                    "purchase_value": purchase_value,
                    "roas": roas,
                    "cpa": cpa,
                    "cpc": cpc,
                    "cpm": cpm,
                    "account_id": self.ad_account_id,
                    # Video metrics
                    "video_plays": video_plays,
                    "video_3s_views": video_3s_views,
                    "video_p25": video_p25,
                    "video_p50": video_p50,
                    "video_p75": video_p75,
                    "video_p100": video_p100,
                    "video_thruplay": video_thruplay,
                    "video_avg_time": video_avg_time,
                })
                ad_ids.append(ad_id)

            # Skip fetching creative details to speed up loading
            # Creative info (thumbnails, body, etc.) is optional and slow
            # Just set defaults for now
            for ad in ads_data:
                ad["thumbnail_url"] = ""
                ad["creative_type"] = "VIDEO" if "VID" in str(ad.get("ad_name", "")).upper() else "IMAGE"
                ad["body"] = ""
                ad["headline"] = ""
                ad["link_url"] = ""
                ad["video_id"] = ""

        except Exception as e:
            print(f"Error fetching ads: {e}")
            raise

        return pd.DataFrame(ads_data)

    def _fetch_creative_info(self, ad_ids: List[str]) -> Dict[str, Dict]:
        """Fetch creative info (thumbnails, body, headline, URL) for ads."""
        creative_info = {}
        import time

        # Process all ads, but add small delays to avoid rate limits
        for idx, ad_id in enumerate(ad_ids):
            try:
                # Add delay every 25 requests to avoid rate limits
                if idx > 0 and idx % 25 == 0:
                    time.sleep(1)

                ad = Ad(ad_id)
                ad_data = ad.api_get(fields=["creative"])
                creative_data = ad_data.get("creative", {})
                creative_id = creative_data.get("id")

                if creative_id:
                    creative = AdCreative(creative_id)
                    info = creative.api_get(fields=[
                        "thumbnail_url",
                        "object_type",
                        "image_url",
                        "body",
                        "title",
                        "link_url",
                        "object_story_spec",
                        "video_id",
                        "asset_feed_spec",
                        "effective_object_story_id",
                    ])

                    # Extract body and headline from various locations
                    body = info.get("body", "")
                    headline = info.get("title", "")
                    link_url = info.get("link_url", "")
                    video_id = info.get("video_id", "")
                    object_type = info.get("object_type", "")

                    # Try to get from object_story_spec if not found
                    story_spec = info.get("object_story_spec", {})
                    if story_spec:
                        link_data = story_spec.get("link_data", {})
                        if not body:
                            body = link_data.get("message", "")
                        if not headline:
                            headline = link_data.get("name", "") or link_data.get("title", "")
                        if not link_url:
                            link_url = link_data.get("link", "")

                        video_data = story_spec.get("video_data", {})
                        if video_data:
                            if not body:
                                body = video_data.get("message", "")
                            if not headline:
                                headline = video_data.get("title", "")
                            if not link_url:
                                call_to_action = video_data.get("call_to_action", {})
                                link_url = call_to_action.get("value", {}).get("link", "") if call_to_action else ""
                            if not video_id:
                                video_id = video_data.get("video_id", "")

                    # Try asset_feed_spec for dynamic creative ads
                    asset_feed = info.get("asset_feed_spec", {})
                    if asset_feed and not body:
                        bodies = asset_feed.get("bodies", [])
                        if bodies:
                            body = bodies[0].get("text", "")
                    if asset_feed and not headline:
                        titles = asset_feed.get("titles", [])
                        if titles:
                            headline = titles[0].get("text", "")
                    if asset_feed and not link_url:
                        link_urls = asset_feed.get("link_urls", [])
                        if link_urls:
                            link_url = link_urls[0].get("website_url", "")

                    # Determine creative type from object_type
                    creative_type = object_type
                    if not creative_type:
                        if video_id:
                            creative_type = "VIDEO"
                        else:
                            creative_type = "IMAGE"

                    creative_info[ad_id] = {
                        "thumbnail_url": info.get("thumbnail_url") or info.get("image_url", ""),
                        "creative_type": creative_type,
                        "body": body,
                        "headline": headline,
                        "link_url": link_url,
                        "video_id": video_id,
                    }
            except Exception as e:
                print(f"Error fetching creative for ad {ad_id}: {e}")
                pass

        return creative_info


def fetch_all_accounts_data(
    date_start: datetime,
    date_end: datetime,
) -> pd.DataFrame:
    """Fetch and combine data from all configured ad accounts."""
    accounts = get_available_ad_accounts()
    all_data = []

    for account_id in accounts:
        try:
            client = MetaAdsClient(ad_account_id=account_id)
            if client.connect():
                df = client.fetch_ads_data(date_start, date_end)
                if not df.empty:
                    all_data.append(df)
        except Exception as e:
            print(f"Error fetching from {account_id}: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def fetch_all_accounts_insights(
    date_start: datetime,
    date_end: datetime,
) -> Dict[str, Any]:
    """Fetch and combine account-level insights from all accounts."""
    accounts = get_available_ad_accounts()
    combined = {
        "spend": 0,
        "impressions": 0,
        "clicks": 0,
        "purchases": 0,
        "purchase_value": 0,
        "cpc": 0,
        "cpm": 0,
    }

    valid_accounts = 0
    for account_id in accounts:
        try:
            client = MetaAdsClient(ad_account_id=account_id)
            if client.connect():
                insights = client.fetch_account_insights(date_start, date_end)
                if insights:
                    combined["spend"] += insights.get("spend", 0)
                    combined["impressions"] += insights.get("impressions", 0)
                    combined["clicks"] += insights.get("clicks", 0)
                    combined["purchases"] += insights.get("purchases", 0)
                    combined["purchase_value"] += insights.get("purchase_value", 0)
                    valid_accounts += 1
        except Exception as e:
            print(f"Error fetching insights from {account_id}: {e}")

    # Calculate derived metrics
    if combined["spend"] > 0:
        combined["roas"] = combined["purchase_value"] / combined["spend"]
        combined["cpm"] = (combined["spend"] / combined["impressions"] * 1000) if combined["impressions"] > 0 else 0
    else:
        combined["roas"] = 0
        combined["cpm"] = 0

    if combined["clicks"] > 0:
        combined["cpc"] = combined["spend"] / combined["clicks"]
    else:
        combined["cpc"] = 0

    if combined["purchases"] > 0:
        combined["cpa"] = combined["spend"] / combined["purchases"]
        combined["aov"] = combined["purchase_value"] / combined["purchases"]
    else:
        combined["cpa"] = 0
        combined["aov"] = 0

    return combined


def fetch_monthly_data(num_months: int = 6) -> Dict[str, pd.DataFrame]:
    """Fetch data for multiple months for historical comparison.

    Returns a dict with month keys (e.g., "January 2026") and DataFrame values.
    """
    from calendar import monthrange

    monthly_data = {}
    now = datetime.now()

    for i in range(num_months):
        # Calculate month start/end
        if i == 0:
            # Current month: 1st to today
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = now
        else:
            # Previous months: full month
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1

            month_start = datetime(year, month, 1)
            last_day = monthrange(year, month)[1]
            month_end = datetime(year, month, last_day, 23, 59, 59)

        month_key = month_start.strftime("%B %Y")

        try:
            df = fetch_all_accounts_data(month_start, month_end)
            monthly_data[month_key] = df
        except Exception as e:
            print(f"Error fetching data for {month_key}: {e}")
            monthly_data[month_key] = pd.DataFrame()

    return monthly_data


def get_demo_data() -> pd.DataFrame:
    """Generate demo data for testing."""
    import random

    creative_names = [
        "3554_PK_IMG_B1G1", "3951_PK_IMG_B1G1", "5444_PK_VID_KASDAVA",
        "3302_PK_IMG_B1G1", "5160_PK_B1G1_h1", "3532_PK_IMG_B1G1",
        "Flex", "Flex - Copy", "Winter Freedom", "Senior Sale",
    ]

    bodies = [
        "Transform your health with our premium supplements. Order now and get 50% off!",
        "Join thousands of satisfied customers. Limited time offer - Buy 1 Get 1 Free!",
        "Experience the difference with our all-natural formula. Shop now!",
        "Don't miss out on our biggest sale of the year. Free shipping on all orders!",
        "The secret to better wellness is here. Try it risk-free today!",
    ]

    headlines = [
        "Limited Time Offer",
        "Buy 1 Get 1 Free",
        "Free Shipping Today",
        "50% Off Sale",
        "Shop Now & Save",
        "Best Seller",
        "New Arrival",
    ]

    landing_pages = [
        "https://example.com/shop",
        "https://example.com/offer",
        "https://example.com/sale",
        "https://example.com/products",
        "https://example.com/special",
    ]

    data = []
    for i in range(50):
        # Use same creative name for some ads (duplicates)
        creative_name = random.choice(creative_names)
        spend = random.uniform(100, 2000)
        roas = random.uniform(1.5, 6.0)
        purchases = int(spend * roas / random.uniform(50, 120))
        creative_type = random.choice(["IMAGE", "VIDEO"])
        impressions = int(spend * random.uniform(50, 150))

        data.append({
            "ad_id": f"ad_{i+1}",
            "ad_name": f"{creative_name}_{random.randint(1,5)}",
            "campaign_id": f"camp_{(i % 5) + 1}",
            "campaign_name": f"Campaign {(i % 5) + 1}",
            "adset_id": f"adset_{(i % 10) + 1}",
            "adset_name": f"Adset {(i % 10) + 1}",
            "spend": round(spend, 2),
            "impressions": impressions,
            "clicks": int(spend * random.uniform(1, 5)),
            "purchases": purchases,
            "purchase_value": round(spend * roas, 2),
            "roas": round(roas, 2),
            "cpa": round(spend / purchases, 2) if purchases > 0 else 0,
            "cpc": round(random.uniform(0.5, 2.0), 2),
            "cpm": round(random.uniform(20, 60), 2),
            "thumbnail_url": "",
            "creative_type": creative_type,
            "account_id": random.choice(["act_830553234595972", "act_1079916799996214"]),
            "body": random.choice(bodies),
            "headline": random.choice(headlines),
            "link_url": random.choice(landing_pages),
            "video_id": f"video_{i+1}" if creative_type == "VIDEO" else "",
            # Video metrics
            "video_plays": int(impressions * random.uniform(0.3, 0.6)) if creative_type == "VIDEO" else 0,
            "video_3s_views": int(impressions * random.uniform(0.15, 0.45)) if creative_type == "VIDEO" else 0,
            "video_p25": int(impressions * random.uniform(0.10, 0.35)) if creative_type == "VIDEO" else 0,
            "video_p50": int(impressions * random.uniform(0.05, 0.25)) if creative_type == "VIDEO" else 0,
            "video_p75": int(impressions * random.uniform(0.03, 0.15)) if creative_type == "VIDEO" else 0,
            "video_p100": int(impressions * random.uniform(0.01, 0.10)) if creative_type == "VIDEO" else 0,
            "video_thruplay": int(impressions * random.uniform(0.05, 0.20)) if creative_type == "VIDEO" else 0,
            "video_avg_time": round(random.uniform(3.0, 25.0), 1) if creative_type == "VIDEO" else 0,
        })

    return pd.DataFrame(data)


def get_demo_insights() -> Dict[str, Any]:
    """Generate demo insights."""
    return {
        "spend": 75830,
        "impressions": 2150000,
        "clicks": 87200,
        "purchases": 1536,
        "purchase_value": 134730,
        "roas": 1.78,
        "cpa": 49.43,
        "aov": 87.83,
        "cpc": 0.87,
        "cpm": 35.44,
    }
