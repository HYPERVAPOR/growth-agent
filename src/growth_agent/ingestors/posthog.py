"""
PostHog API client for fetching product analytics data.

This module uses PostHog API for events, insights, and feature flags.
"""

import logging
from datetime import datetime, UTC, timedelta
from typing import Any, Optional

import httpx

from growth_agent.config import Settings
from growth_agent.core.schema import PostHogMetricStat

logger = logging.getLogger(__name__)


class PostHogIngestor:
    """
    PostHog API client for fetching analytics data.

    Uses Personal API Key or Project API Key for authentication.
    """

    def __init__(self, settings: Settings):
        """
        Initialize PostHog ingestor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_base_url = f"https://{settings.posthog_host}/api"

        # HTTP client with longer timeout for PostHog API
        self.client = httpx.Client(timeout=60.0)

        # Set up headers for API requests
        self.headers = settings.get_posthog_headers()

        logger.info("PostHog Ingestor initialized (placeholder - API methods not yet implemented)")

    def fetch_events(
        self,
        event_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[PostHogMetricStat]:
        """
        Fetch event data from PostHog.

        Args:
            event_name: Optional specific event name
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum events to return

        Returns:
            List of PostHogMetricStat objects
        """
        logger.info(f"Fetching PostHog events")

        if not start_date:
            start_date = datetime.now(UTC) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(UTC)

        metrics_list = []

        try:
            # PostHog API endpoint for events
            # Note: The actual API may vary based on PostHog version
            project_id = self.settings.posthog_project_id
            if not project_id:
                logger.error("PostHog project_id not configured")
                return []

            url = f"{self.api_base_url}/projects/{project_id}/events/"

            params = {
                "limit": limit,
            }

            # Add date filters if provided
            if start_date:
                params["after"] = start_date.isoformat()
            if end_date:
                params["before"] = end_date.isoformat()
            if event_name:
                params["event"] = event_name

            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse response and convert to PostHogMetricStat
            if "results" in data:
                for event_data in data["results"]:
                    try:
                        metric = PostHogMetricStat(
                            data_type="events",
                            date=datetime.fromisoformat(event_data.get("timestamp", datetime.now(UTC).isoformat())),
                            event_name=event_data.get("event"),
                            event_count=event_data.get("count", 0),
                            properties=event_data.get("properties", {}),
                        )
                        metrics_list.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse event data: {e}")
                        continue

            logger.info(f"Fetched {len(metrics_list)} PostHog events")
            return metrics_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching PostHog events: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching PostHog events: {e}")
            return []

    def fetch_funnels(
        self,
        funnel_id: str | None = None,
        days: int = 7,
    ) -> list[PostHogMetricStat]:
        """
        Fetch funnel analysis data.

        Args:
            funnel_id: Optional specific funnel ID
            days: Number of days to look back

        Returns:
            List of PostHogMetricStat objects
        """
        logger.info(f"Fetching PostHog funnels")

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        metrics_list = []

        try:
            # PostHog API endpoint for insights (funnels are a type of insight)
            project_id = self.settings.posthog_project_id
            if not project_id:
                logger.error("PostHog project_id not configured")
                return []

            url = f"{self.api_base_url}/projects/{project_id}/insights/"

            params = {
                "date_from": start_date.isoformat(),
                "date_to": end_date.isoformat(),
            }

            if funnel_id:
                url = f"{url}{funnel_id}/"

            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Debug: log the response structure
            logger.debug(f"PostHog funnels response type: {type(data)}")
            if isinstance(data, list):
                logger.debug(f"Found {len(data)} items in response (list)")
            elif isinstance(data, dict) and "results" in data:
                logger.debug(f"Found {len(data['results'])} items in response (dict with results)")
                data = data["results"]

            # Parse response - handle both single insight and list
            insights = data if isinstance(data, list) else [data]

            for insight_data in insights:
                try:
                    # Check if this is a funnel insight
                    query_kind = insight_data.get("query", {}).get("kind")
                    if query_kind != "FunnelQuery":
                        continue

                    # Extract funnel steps
                    results = insight_data.get("result", [])
                    for step_data in results:
                        try:
                            metric = PostHogMetricStat(
                                data_type="funnels",
                                date=end_date,
                                funnel_name=insight_data.get("name", insight_data.get("derived_name")),
                                funnel_step=step_data.get("order"),
                                conversion_rate=step_data.get("conversion_rate", 0) * 100,  # Convert to percentage
                                dropped_users=step_data.get("dropped_from_previous_step", 0),
                                properties={
                                    "funnel_id": insight_data.get("id"),
                                    "step_name": step_data.get("name"),
                                    "step_action": step_data.get("action"),
                                    "count": step_data.get("count"),
                                },
                            )
                            metrics_list.append(metric)
                        except Exception as e:
                            logger.warning(f"Failed to parse funnel step data: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Failed to parse funnel data: {e}")
                    continue

            logger.info(f"Fetched {len(metrics_list)} PostHog funnel steps")
            return metrics_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching PostHog funnels: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching PostHog funnels: {e}")
            return []

    def fetch_insights(
        self,
        insight_id: str | None = None,
        days: int = 7,
    ) -> list[PostHogMetricStat]:
        """
        Fetch insight/trend data.

        Args:
            insight_id: Optional specific insight ID
            days: Number of days to look back

        Returns:
            List of PostHogMetricStat objects
        """
        logger.info(f"Fetching PostHog insights")

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        metrics_list = []

        try:
            # PostHog API endpoint for insights
            project_id = self.settings.posthog_project_id
            if not project_id:
                logger.error("PostHog project_id not configured")
                return []

            url = f"{self.api_base_url}/projects/{project_id}/insights/"

            params = {
                "date_from": start_date.isoformat(),
                "date_to": end_date.isoformat(),
            }

            if insight_id:
                url = f"{url}{insight_id}/"

            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Debug: log the response structure
            logger.debug(f"PostHog insights response type: {type(data)}")
            if isinstance(data, list):
                logger.debug(f"Found {len(data)} insights in response (list)")
            elif isinstance(data, dict) and "results" in data:
                logger.debug(f"Found {len(data['results'])} insights in response (dict with results)")
                data = data["results"]

            # Parse response - handle both single insight and list
            insights = data if isinstance(data, list) else [data]

            for insight_data in insights:
                try:
                    # Extract trend data if available
                    result = insight_data.get("result", [{}])[0] if insight_data.get("result") else {}

                    metric = PostHogMetricStat(
                        data_type="insights",
                        date=end_date,
                        insight_type=insight_data.get("query", {}).get("kind"),
                        insight_value=result.get("count", result.get("value")),
                        insight_label=insight_data.get("name", insight_data.get("derived_name")),
                        properties={
                            "insight_id": insight_data.get("id"),
                            "query": insight_data.get("query"),
                            "tags": insight_data.get("tags"),
                            "insight_name": insight_data.get("name", insight_data.get("derived_name")),
                        },
                    )
                    metrics_list.append(metric)
                except Exception as e:
                    logger.warning(f"Failed to parse insight data: {e}")
                    continue

            logger.info(f"Fetched {len(metrics_list)} PostHog insights")
            return metrics_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching PostHog insights: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching PostHog insights: {e}")
            return []

    def fetch_feature_flags(
        self,
        active_only: bool = True,
    ) -> list[PostHogMetricStat]:
        """
        Fetch feature flag data.

        Args:
            active_only: Only return active flags

        Returns:
            List of PostHogMetricStat objects
        """
        logger.info(f"Fetching PostHog feature flags")

        metrics_list = []

        try:
            # PostHog API endpoint for feature flags
            project_id = self.settings.posthog_project_id
            if not project_id:
                logger.error("PostHog project_id not configured")
                return []

            url = f"{self.api_base_url}/projects/{project_id}/feature_flags/"

            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            # Debug: log the response structure
            logger.debug(f"PostHog feature_flags response keys: {data.keys()}")
            if "results" in data:
                logger.debug(f"Found {len(data['results'])} feature flags in response")

            # Parse response and convert to PostHogMetricStat
            if "results" in data:
                for flag_data in data["results"]:
                    try:
                        # Filter if active_only is set (only return active flags)
                        is_active = flag_data.get("active", False)
                        if active_only and not is_active:
                            continue

                        # Get rollout percentage
                        filters = flag_data.get("filters", {})
                        multivariate = filters.get("multivariate", [])
                        rollout_percentage = 0
                        if multivariate and len(multivariate) > 0:
                            rollout_percentage = multivariate[0].get("rollout_percentage", 0)

                        metric = PostHogMetricStat(
                            data_type="feature_flags",
                            date=datetime.now(UTC),
                            flag_name=flag_data.get("key"),
                            flag_enabled=is_active,
                            flag_rollout_percentage=int(rollout_percentage),
                            properties={
                                "flag_id": flag_data.get("id"),
                                "description": flag_data.get("description"),
                                "filters": flag_data.get("filters"),
                            },
                        )
                        metrics_list.append(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse feature flag data: {e}")
                        continue

            logger.info(f"Fetched {len(metrics_list)} PostHog feature flags")
            return metrics_list

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching PostHog feature flags: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching PostHog feature flags: {e}")
            return []

    def _execute_hogql_query(
        self,
        query: str,
        name: str = "hogql_query",
    ) -> list[dict]:
        """
        Execute a HogQL query against PostHog.

        Args:
            query: HogQL query string
            name: Query name for logging and debugging

        Returns:
            List of result rows as dictionaries
        """
        try:
            project_id = self.settings.posthog_project_id
            if not project_id:
                logger.error("PostHog project_id not configured")
                return []

            url = f"{self.api_base_url}/projects/{project_id}/query/"

            payload = {
                "query": {
                    "kind": "HogQLQuery",
                    "query": query,
                },
                "name": name,
            }

            response = self.client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()

            # Extract results from response
            if "results" in data:
                results = data["results"]
                # Handle different result formats
                if isinstance(results, list):
                    # If results is a list of lists (rows with columns), convert to dicts
                    if results and isinstance(results[0], list):
                        # Get column names from the response if available
                        columns = data.get("columns", [])
                        if columns:
                            return [dict(zip(columns, row)) for row in results]
                        # Fallback: return as-is
                        return results
                    return results
                return []

            logger.warning(f"No results found in HogQL query response")
            return []

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing HogQL query: {e}")
            logger.error(f"Query was: {query[:200]}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error executing HogQL query: {e}")
            logger.error(f"Query was: {query[:200]}")
            return []

    def fetch_event_properties(
        self,
        days: int = 7,
        sample_size: int = 1000,
    ) -> list[PostHogMetricStat]:
        """
        Fetch event property definitions from PostHog.

        Analyzes recent events to extract all unique property names and their types.

        Args:
            days: Number of days to look back for events
            sample_size: Number of events to sample for property discovery

        Returns:
            List of PostHogMetricStat objects with event property metadata
        """
        logger.info("Fetching PostHog event properties")

        metrics_list = []

        try:
            # Query recent events and extract properties
            # Use INTERVAL syntax for date filtering in HogQL
            query = f"""
                SELECT
                    event,
                    properties
                FROM events
                WHERE timestamp >= now() - INTERVAL {days} DAY
                LIMIT {sample_size}
            """

            results = self._execute_hogql_query(
                query=query,
                name="fetch_event_properties_sample",
            )

            if not results:
                logger.warning("No events found for property extraction")
                return []

            # Extract all unique property names and types
            import json

            property_stats = {}  # {property_name: {"count": int, "types": set}}

            for row in results:
                props_raw = row.get("properties", {})

                # Properties might be a JSON string or dict
                if isinstance(props_raw, str):
                    try:
                        properties = json.loads(props_raw)
                    except json.JSONDecodeError:
                        continue
                elif isinstance(props_raw, dict):
                    properties = props_raw
                else:
                    continue

                if isinstance(properties, dict):
                    for prop_name, prop_value in properties.items():
                        if prop_name not in property_stats:
                            property_stats[prop_name] = {"count": 0, "types": set()}
                        property_stats[prop_name]["count"] += 1
                        property_stats[prop_name]["types"].add(type(prop_value).__name__)

            # Convert to PostHogMetricStat objects
            total_properties = len(property_stats)

            for prop_name, stats in sorted(property_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                try:
                    # Determine the most common type
                    type_list = list(stats["types"])
                    primary_type = type_list[0] if type_list else "unknown"
                    if len(type_list) > 1:
                        primary_type = f"mixed ({', '.join(type_list[:3])})"

                    metric = PostHogMetricStat(
                        data_type="event_properties",
                        date=datetime.now(UTC),
                        event_property_name=prop_name,
                        event_property_type=primary_type,
                        event_property_usage_count=stats["count"],
                        event_properties_total=total_properties,
                        properties={
                            "property_name": prop_name,
                            "value_types": type_list,
                        },
                    )
                    metrics_list.append(metric)
                except Exception as e:
                    logger.warning(f"Failed to parse event property data: {e}")
                    continue

            logger.info(f"Fetched {len(metrics_list)} PostHog event properties from {len(results)} sampled events")
            return metrics_list

        except Exception as e:
            logger.error(f"Error fetching PostHog event properties: {e}")
            return []

    def fetch_person_properties(
        self,
        days: int = 7,
        sample_size: int = 1000,
    ) -> list[PostHogMetricStat]:
        """
        Fetch person property definitions from PostHog.

        Analyzes recent person data to extract all unique property names and their types.

        Args:
            days: Number of days to look back for data
            sample_size: Number of persons to sample for property discovery

        Returns:
            List of PostHogMetricStat objects with person property metadata
        """
        logger.info("Fetching PostHog person properties")

        metrics_list = []

        try:
            # Query persons and extract their properties
            # Using the persons table with properties
            # Note: persons table may be empty or limited in some projects
            query = f"""
                SELECT
                    id,
                    properties
                FROM persons
                LIMIT {sample_size}
            """

            results = self._execute_hogql_query(
                query=query,
                name="fetch_person_properties_sample",
            )

            if not results:
                logger.warning("No persons found for property extraction")
                return []

            # Extract all unique property names and types
            import json

            property_stats = {}  # {property_name: {"count": int, "types": set}}

            for row in results:
                props_raw = row.get("properties", {})

                # Properties might be a JSON string or dict
                if isinstance(props_raw, str):
                    try:
                        properties = json.loads(props_raw)
                    except json.JSONDecodeError:
                        continue
                elif isinstance(props_raw, dict):
                    properties = props_raw
                else:
                    continue

                if isinstance(properties, dict):
                    for prop_name, prop_value in properties.items():
                        if prop_name not in property_stats:
                            property_stats[prop_name] = {"count": 0, "types": set()}
                        property_stats[prop_name]["count"] += 1
                        property_stats[prop_name]["types"].add(type(prop_value).__name__)

            # Convert to PostHogMetricStat objects
            total_properties = len(property_stats)

            for prop_name, stats in sorted(property_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                try:
                    # Determine the most common type
                    type_list = list(stats["types"])
                    primary_type = type_list[0] if type_list else "unknown"
                    if len(type_list) > 1:
                        primary_type = f"mixed ({', '.join(type_list[:3])})"

                    metric = PostHogMetricStat(
                        data_type="person_properties",
                        date=datetime.now(UTC),
                        person_property_name=prop_name,
                        person_property_type=primary_type,
                        person_property_usage_count=stats["count"],
                        person_properties_total=total_properties,
                        properties={
                            "property_name": prop_name,
                            "value_types": type_list,
                        },
                    )
                    metrics_list.append(metric)
                except Exception as e:
                    logger.warning(f"Failed to parse person property data: {e}")
                    continue

            logger.info(f"Fetched {len(metrics_list)} PostHog person properties from {len(results)} sampled persons")
            return metrics_list

        except Exception as e:
            logger.error(f"Error fetching PostHog person properties: {e}")
            return []

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
