"""
LanceDB vector store for semantic search.

This module provides vector indexing and similarity search for inbox items.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import lancedb
import pydantic
from pydantic import BaseModel

from growth_agent.config import Settings
from growth_agent.core.llm import LLMClient

logger = logging.getLogger(__name__)


class VectorDocument(BaseModel):
    """Document for vector storage."""

    id: str
    source_id: str
    content: str
    author: str
    source: str
    published_at: str
    url: str
    # Vector will be added by LanceDB


class VectorStore:
    """
    Vector store using LanceDB for semantic search.

    Provides indexing and similarity search for content items.
    """

    def __init__(self, settings: Settings, llm_client: LLMClient):
        """
        Initialize vector store.

        Args:
            settings: Application settings
            llm_client: LLM client for embedding generation
        """
        self.settings = settings
        self.llm_client = llm_client
        self.uri = settings.lancedb_uri

        # Ensure directory exists
        Path(self.uri).parent.mkdir(parents=True, exist_ok=True)

        # Connect to LanceDB
        self.db = lancedb.connect(self.uri)
        self.table_name = "inbox_items"

        logger.info(f"Vector store initialized at {self.uri}")

    def _get_table(self):
        """Get or create the vector table."""
        try:
            # Try to open existing table
            table = self.db.open_table(self.table_name)
            return table
        except Exception:
            # Table doesn't exist, create it (will auto-infer schema from first data)
            logger.info(f"Creating new vector table: {self.table_name}")
            # Create table without schema - LanceDB will infer it
            table = self.db.create_table(self.table_name, schema=None)
            return table

    def index_item(self, item: dict[str, Any]) -> None:
        """
        Index a single item in the vector store.

        Args:
            item: Inbox item dictionary
        """
        try:
            # Prepare text for embedding
            text = item.get("content", "")
            if not text:
                logger.warning(f"Skipping item {item.get('id')} with no content")
                return

            # Generate embedding (with fallback)
            vector = None
            try:
                embeddings = self.llm_client.generate_embeddings([text])
                vector = embeddings[0]
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {item.get('id')}: {e}, indexing without vector")

            # Prepare record
            record = {
                "id": item.get("id"),
                "source_id": item.get("original_id"),
                "original_id": item.get("original_id"),
                "author_id": item.get("author_id"),
                "content": text[:1000],  # Limit content length
                "author": item.get("author_name"),
                "source": item.get("source"),
                "published_at": str(item.get("published_at", "")),
                "url": item.get("url"),
            }

            # Add vector if available
            if vector:
                record["vector"] = vector

            # Get or create table, then add
            try:
                table = self.db.open_table(self.table_name)
                table.add([record])
            except Exception:
                # Table doesn't exist, create with first record
                logger.info(f"Creating table {self.table_name} with first record")
                self.db.create_table(self.table_name, data=[record])

            logger.debug(f"Indexed item: {item.get('id')}")

        except Exception as e:
            logger.error(f"Failed to index item {item.get('id')}: {e}")

    def index_items(self, items: list[dict[str, Any]]) -> int:
        """
        Index multiple items in batch.

        Args:
            items: List of inbox items

        Returns:
            Number of successfully indexed items
        """
        indexed_count = 0

        for item in items:
            try:
                self.index_item(item)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index item {item.get('id')}: {e}")
                continue

        logger.info(f"Indexed {indexed_count}/{len(items)} items")
        return indexed_count

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar items using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters (e.g., {"source": "x"})

        Returns:
            List of similar items with scores
        """
        try:
            # Generate query embedding
            embeddings = self.llm_client.generate_embeddings([query])
            query_vector = embeddings[0]

            # Search
            table = self._get_table()
            results = table.search(query_vector).limit(top_k).to_pandas()

            # Convert to list of dicts
            items = []
            for _, row in results.iterrows():
                item = {
                    "id": row.get("id"),
                    "source_id": row.get("source_id"),
                    "content": row.get("content"),
                    "author": row.get("author"),
                    "source": row.get("source"),
                    "published_at": row.get("published_at"),
                    "url": row.get("url"),
                    "score": row.get("_distance", 0.0),  # Distance = lower is better
                }

                # Apply filters if provided
                if filters:
                    match = True
                    for key, value in filters.items():
                        if item.get(key) != value:
                            match = False
                            break
                    if match:
                        items.append(item)
                else:
                    items.append(item)

            logger.info(f"Found {len(items)} similar items for query")
            return items

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def get_all(self) -> list[dict[str, Any]]:
        """
        Get all items from the vector store.

        Returns:
            List of all inbox items
        """
        try:
            table = self._get_table()

            # Use LanceDB's to_pandas() to get all rows
            df = table.to_pandas()

            # Convert to list of dicts
            items = []
            for _, row in df.iterrows():
                # Skip vector column when converting
                item = {
                    "id": row.get("id"),
                    "source_id": row.get("source_id"),
                    "original_id": row.get("original_id"),
                    "author_id": row.get("author_id"),
                    "content": row.get("content"),
                    "author_name": row.get("author"),
                    "title": None,  # Not stored in vector DB
                    "url": row.get("url"),
                    "published_at": row.get("published_at"),
                    "source": row.get("source"),
                    "fetched_at": None,  # Not stored in vector DB
                    "metadata": None,    # Not stored in vector DB
                }
                items.append(item)

            logger.info(f"Retrieved {len(items)} items from vector store")
            return items

        except Exception as e:
            logger.error(f"Failed to get all items: {e}")
            return []

    def delete_by_ids(self, ids_to_remove: set[tuple[str, str, str]]) -> int:
        """
        Delete items by their (source, original_id, author_id) tuples.

        Args:
            ids_to_remove: Set of (source, original_id, author_id) tuples to remove

        Returns:
            Number of items deleted
        """
        try:
            table = self._get_table()

            # LanceDB doesn't have efficient batch delete
            # We need to rebuild the table without the deleted items
            all_items = self.get_all()

            # Filter out items to delete
            remaining_items = [
                item for item in all_items
                if (item.get("source"), item.get("original_id"), item.get("author_id")) not in ids_to_remove
            ]

            deleted_count = len(all_items) - len(remaining_items)

            if deleted_count == 0:
                return 0

            # Rebuild table
            return self.rebuild_index(remaining_items)

        except Exception as e:
            logger.error(f"Failed to delete items: {e}")
            return 0

    def delete_by_id(self, item_id: str) -> bool:
        """
        Delete an item from the vector store.

        Args:
            item_id: ID of the item to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            table = self._get_table()
            # LanceDB doesn't have direct delete by ID, need to use filter
            # This is a limitation - for production, consider full re-index
            logger.warning(f"Delete operation not fully supported: {item_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Dictionary with stats
        """
        try:
            table = self._get_table()
            stats = {
                "table_name": self.table_name,
                "num_rows": table.count_rows(),
                "uri": self.uri,
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    def rebuild_index(self, items: list[dict[str, Any]]) -> int:
        """
        Rebuild the entire index from scratch.

        Args:
            items: List of all inbox items

        Returns:
            Number of indexed items
        """
        try:
            # Drop existing table
            try:
                self.db.drop_table(self.table_name)
                logger.info(f"Dropped existing table: {self.table_name}")
            except Exception:
                pass  # Table doesn't exist

            # Re-create and index
            return self.index_items(items)

        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return 0
