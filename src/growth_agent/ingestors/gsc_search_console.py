"""
Google Search Console API client for fetching search analytics data.

This module uses Google Search Console API with OAuth 2.0 authentication.
Requires google-auth and google-api-python-client packages.
"""

import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Optional

import httpx

from growth_agent.config import Settings
from growth_agent.core.schema import GSCMetricStat

logger = logging.getLogger(__name__)


class GoogleSearchConsoleIngestor:
    """
    Google Search Console API client for fetching search performance data.

    Uses OAuth 2.0 service account authentication for API access.
    """

    def __init__(self, settings: Settings):
        """
        Initialize GSC ingestor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_base_url = "https://www.googleapis.com/webmasters/v3"

        # HTTP client with timeout
        self.client = httpx.Client(timeout=30.0)

        # OAuth token cache
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        logger.info("GSC Ingestor initialized (placeholder - OAuth not yet implemented)")

    def _get_access_token(self) -> str:
        """
        Get OAuth 2.0 access token using service account credentials.

        Returns:
            Access token string

        Raises:
            RuntimeError: If authentication fails
        """
        # Check if cached token is still valid
        if self._access_token and self._token_expiry:
            if datetime.now(UTC) < self._token_expiry:
                logger.debug("Using cached GSC access token")
                return self._access_token

        # Get new access token using OAuth 2.0 JWT flow
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            # Scope for Search Console API
            SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

            # Load service account credentials
            # Option 1: From environment variables (GSC_CLIENT_EMAIL + GSC_PRIVATE_KEY)
            if self.settings.gsc_client_email and self.settings.gsc_private_key:
                logger.info("Using GSC credentials from environment variables")
                credentials = service_account.Credentials.from_service_account_info(
                    info={
                        "type": "service_account",
                        "client_email": self.settings.gsc_client_email,
                        "private_key": self.settings.gsc_private_key,
                        "token_uri": "https://oauth2.googleapis.com/token",
                    },
                    scopes=SCOPES,
                )
            # Option 2: From JSON file (GSC_SERVICE_ACCOUNT_PATH)
            elif self.settings.gsc_service_account_path:
                logger.info(f"Using GSC credentials from file: {self.settings.gsc_service_account_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.settings.gsc_service_account_path,
                    scopes=SCOPES,
                )
            else:
                raise RuntimeError(
                    "GSC credentials not configured. "
                    "Please set either (GSC_CLIENT_EMAIL + GSC_PRIVATE_KEY) or GSC_SERVICE_ACCOUNT_PATH"
                )

            # Refresh the credentials to obtain access token
            credentials.refresh(Request())

            # Cache the token and expiry
            self._access_token = credentials.token
            # credentials.expiry might be a datetime or timestamp
            self._token_expiry = credentials.expiry if isinstance(credentials.expiry, datetime) else datetime.fromtimestamp(credentials.expiry, tz=UTC)

            logger.info("Successfully obtained GSC access token")
            return self._access_token

        except FileNotFoundError:
            raise RuntimeError(
                f"Service account file not found: {self.settings.gsc_service_account_path}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to obtain GSC access token: {e}")

    def fetch_search_analytics(
        self,
        site_url: str,
        start_date: datetime,
        end_date: datetime,
        dimensions: list[str] | None = None,
        search_type: str = "web",
        row_limit: int = 100,
    ) -> list[GSCMetricStat]:
        """
        Fetch search analytics data from GSC.

        Args:
            site_url: Site URL (e.g., "https://example.com")
            start_date: Start date for data
            end_date: End date for data
            dimensions: Dimensions to group by (e.g., ["page", "query", "country", "device"])
            search_type: Search type (web, image, video, news, discover)
            row_limit: Maximum rows to return

        Returns:
            List of GSCMetricStat objects
        """
        logger.info(f"Fetching GSC search analytics for {site_url}")

        if not dimensions:
            dimensions = ["page"]

        metrics_list = []

        try:
            # Get access token
            access_token = self._get_access_token()

            # Prepare API request
            # URL encode the site URL for the API path
            from urllib.parse import quote
            encoded_site_url = quote(site_url, safe='')

            url = f"{self.api_base_url}/sites/{encoded_site_url}/searchAnalytics/query"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            # Build request body
            request_body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": dimensions,
                "searchType": search_type,
                "rowLimit": row_limit,
            }

            response = self.client.post(url, headers=headers, json=request_body)
            response.raise_for_status()

            data = response.json()

            # Parse response and convert to GSCMetricStat
            if "rows" in data:
                for row in data["rows"]:
                    try:
                        # Extract dimension values (keys)
                        dimension_values = row.get("keys", [])

                        # Extract metric values
                        impressions = row.get("impressions", 0)
                        clicks = row.get("clicks", 0)
                        ctr = row.get("ctr", 0.0)
                        position = row.get("position", 0.0)

                        # Build metric object
                        metric = GSCMetricStat(
                            data_type="search_analytics",
                            url=dimension_values[0] if len(dimension_values) > 0 else site_url,
                            date=start_date,
                            queries=[dimension_values[1]] if len(dimension_values) > 1 and dimensions[1] == "query" else None,
                            impressions=impressions,
                            clicks=clicks,
                            ctr=ctr * 100 if ctr > 0 else None,  # Convert to percentage
                            position=position,
                            device=dimension_values[2] if len(dimension_values) > 2 and dimensions[2] == "device" else None,
                            country=dimension_values[2] if len(dimension_values) > 2 and dimensions[2] == "country" else None,
                            search_type=search_type,
                        )
                        metrics_list.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse GSC row data: {e}")
                        continue

            logger.info(f"Fetched {len(metrics_list)} GSC search analytics records")
            return metrics_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching GSC search analytics: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching GSC search analytics: {e}")
            return []

    def fetch_page_performance(
        self,
        site_url: str,
        page_url: str,
        days: int = 7,
    ) -> list[GSCMetricStat]:
        """
        Fetch performance data for a specific page.

        Args:
            site_url: Site URL
            page_url: Specific page URL
            days: Number of days to look back

        Returns:
            List of GSCMetricStat objects
        """
        logger.info(f"Fetching GSC page performance for {page_url}")

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        # Use search analytics with page dimension
        return self.fetch_search_analytics(
            site_url=site_url,
            start_date=start_date,
            end_date=end_date,
            dimensions=["page", "query", "device", "country"],
            row_limit=10,
        )

    def fetch_index_status(
        self,
        site_url: str,
        page_url: str | None = None,
    ) -> list[GSCMetricStat]:
        """
        Fetch index coverage status.

        Args:
            site_url: Site URL
            page_url: Optional specific page URL

        Returns:
            List of GSCMetricStat objects
        """
        logger.info(f"Fetching GSC index status for {site_url}")

        # TODO: Implement URL inspection API call
        logger.warning("GSC index status fetching not yet implemented")
        return []

    def fetch_core_web_vitals(
        self,
        site_url: str,
        mobile: bool = True,
    ) -> list[GSCMetricStat]:
        """
        Fetch Core Web Vitals data.

        Args:
            site_url: Site URL
            mobile: Whether to fetch mobile data (vs desktop)

        Returns:
            List of GSCMetricStat objects
        """
        logger.info(f"Fetching GSC Core Web Vitals for {site_url} ({'mobile' if mobile else 'desktop'})")

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=28)  # CWV data uses 28-day window

        try:
            # Get access token
            access_token = self._get_access_token()

            # Prepare API request
            from urllib.parse import quote
            encoded_site_url = quote(site_url, safe='')

            url = f"{self.api_base_url}/sites/{encoded_site_url}/searchAnalytics/query"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            # Build request body for CWV data
            request_body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimensions": ["page"],
                "searchType": "web",
                "rowLimit": 100,
                "dataState": "all",  # Use all data (including unindexed)
            }

            response = self.client.post(url, headers=headers, json=request_body)
            response.raise_for_status()

            data = response.json()

            metrics_list = []

            # Parse response
            if "rows" in data:
                for row in data["rows"]:
                    try:
                        page_url = row.get("keys", [""])[0]

                        # Note: GSC API doesn't provide individual LCP, FID, CLS values directly
                        # These are typically aggregated. We'll create placeholder metric objects
                        # In a production system, you might need to use PageSpeed Insights API alongside

                        metric = GSCMetricStat(
                            data_type="core_web_vitals",
                            url=page_url,
                            date=start_date,
                            impressions=row.get("impressions", 0),
                            clicks=row.get("clicks", 0),
                            ctr=row.get("ctr", 0.0) * 100,
                            position=row.get("position", 0.0),
                            # CWV specific fields would need to come from PageSpeed Insights API
                            # For now, we create placeholders
                            lcp=None,
                            fid=None,
                            cls=None,
                            status=None,
                            properties={
                                "device": "mobile" if mobile else "desktop",
                                "note": "CWV detailed metrics require PageSpeed Insights API",
                            },
                        )
                        metrics_list.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse CWV row data: {e}")
                        continue

            logger.info(f"Fetched {len(metrics_list)} GSC Core Web Vitals records")
            return metrics_list

        except Exception as e:
            logger.error(f"Error fetching GSC Core Web Vitals: {e}")
            return []

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
