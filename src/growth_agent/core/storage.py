"""
File-system database implementation with atomic operations.

This module provides JSONL and Markdown storage with atomic writes for data integrity.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class JSONLStore:
    """
    Generic JSONL file handler with atomic writes.

    JSONL format: One JSON object per line, append-only for efficient operations.
    """

    def __init__(self, data_root: Path):
        """
        Initialize JSONL store.

        Args:
            data_root: Root directory for data storage
        """
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

    def _ensure_dir(self, relative_path: Path) -> Path:
        """Ensure directory exists for the given path."""
        full_path = self.data_root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

    def atomic_write(self, path: Path, content: str) -> None:
        """
        Write content to file atomically.

        Uses a temporary file and atomic rename to prevent corruption.

        Args:
            path: Target file path (can be relative or absolute)
            content: Content to write
        """
        if not path.is_absolute():
            path = self.data_root / path

        # Create temporary file
        temp_path = path.with_suffix(".tmp")

        try:
            temp_path.write_text(content, encoding="utf-8")
            # Atomic rename (POSIX)
            temp_path.replace(path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def append(self, relative_path: Path, items: list[dict[str, Any]]) -> None:
        """
        Append items to a JSONL file.

        Args:
            relative_path: Relative path from data_root
            items: List of dictionaries to append
        """
        # Handle both relative and absolute paths
        if relative_path.is_absolute():
            path = relative_path
        else:
            path = self._ensure_dir(relative_path)

        # Read existing content if file exists
        existing_lines = []
        if path.exists():
            existing_lines = path.read_text(encoding="utf-8").strip().split("\n")
            # Filter out empty lines
            existing_lines = [line for line in existing_lines if line.strip()]

        # Convert new items to JSON lines
        new_lines = [json.dumps(item, ensure_ascii=False, default=str) for item in items]

        # Write all content atomically
        all_lines = existing_lines + new_lines
        content = "\n".join(all_lines) + ("\n" if all_lines else "")
        self.atomic_write(path, content)

    def write(self, relative_path: Path, items: list[dict[str, Any]]) -> None:
        """
        Write items to a JSONL file (overwrite).

        Args:
            relative_path: Relative path from data_root
            items: List of dictionaries to write
        """
        # Handle both relative and absolute paths
        if relative_path.is_absolute():
            path = relative_path
        else:
            path = self._ensure_dir(relative_path)

        # Convert items to JSON lines
        lines = [json.dumps(item, ensure_ascii=False, default=str) for item in items]
        content = "\n".join(lines) + ("\n" if lines else "")
        self.atomic_write(path, content)

    def read_all(self, relative_path: Optional[Path] = None) -> list[dict[str, Any]]:
        """
        Read all items from a JSONL file.

        Args:
            relative_path: Relative path from data_root (if None, uses path as absolute)

        Returns:
            List of dictionaries (one per line)
        """
        if relative_path is None:
            raise ValueError("Path must be provided")

        # Ensure relative_path is a Path object
        relative_path = Path(relative_path)
        path = self.data_root / relative_path if not relative_path.is_absolute() else relative_path

        if not path.exists():
            return []

        items = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        # Skip malformed lines but log warning
                        print(f"Warning: Skipping malformed JSON line: {e}")

        return items

    def remove_by_id(self, relative_path: Path, id_field: str, id_value: str) -> bool:
        """
        Remove an item by its ID field.

        Args:
            relative_path: Relative path from data_root
            id_field: Name of the ID field
            id_value: Value of the ID to remove

        Returns:
            True if item was found and removed, False otherwise
        """
        # Ensure relative_path is a Path object
        relative_path = Path(relative_path)
        items = self.read_all(relative_path)

        # Filter out the item
        filtered_items = [item for item in items if item.get(id_field) != id_value]

        if len(filtered_items) == len(items):
            # Item not found
            return False

        # Rewrite file without the item
        path = self.data_root / relative_path if not relative_path.is_absolute() else relative_path
        content = "\n".join(json.dumps(item, ensure_ascii=False, default=str) for item in filtered_items)
        if content:
            content += "\n"
        self.atomic_write(path, content)

        return True

    def update_field(
        self, relative_path: Path, id_field: str, id_value: str, field_name: str, field_value: Any
    ) -> bool:
        """
        Update a specific field in an item by ID.

        Args:
            relative_path: Relative path from data_root
            id_field: Name of the ID field
            id_value: Value of the ID to update
            field_name: Name of the field to update
            field_value: New value for the field

        Returns:
            True if item was found and updated, False otherwise
        """
        # Ensure relative_path is a Path object
        relative_path = Path(relative_path)
        items = self.read_all(relative_path)

        # Find and update the item
        updated = False
        for item in items:
            if item.get(id_field) == id_value:
                item[field_name] = field_value
                updated = True
                break

        if not updated:
            return False

        # Rewrite file with updated item
        path = self.data_root / relative_path if not relative_path.is_absolute() else relative_path
        content = "\n".join(json.dumps(item, ensure_ascii=False, default=str) for item in items)
        if content:
            content += "\n"
        self.atomic_write(path, content)

        return True


class MarkdownStore:
    """
    Markdown file manager with YAML frontmatter support.
    """

    def __init__(self, data_root: Path):
        """
        Initialize Markdown store.

        Args:
            data_root: Root directory for data storage
        """
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

    def write_blog_post(self, path: Path, blog_post: BaseModel) -> None:
        """
        Write a blog post with YAML frontmatter.

        Args:
            path: Path to save the blog post (relative or absolute)
            blog_post: BlogPost model instance
        """
        if not path.is_absolute():
            path = self.data_root / path

        path.parent.mkdir(parents=True, exist_ok=True)

        # Extract frontmatter data
        if hasattr(blog_post, "frontmatter"):
            frontmatter_dict = blog_post.frontmatter.model_dump()
            content = blog_post.content
        else:
            frontmatter_dict = blog_post.model_dump(exclude={"content"})
            content = blog_post.content

        # Build YAML frontmatter
        import yaml

        frontmatter_yaml = yaml.dump(frontmatter_dict, default_flow_style=False, allow_unicode=True)

        # Combine frontmatter and content
        full_content = f"---\n{frontmatter_yaml}---\n{content}"

        # Write atomically
        temp_path = path.with_suffix(".tmp")
        try:
            temp_path.write_text(full_content, encoding="utf-8")
            temp_path.replace(path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def read_blog_post(self, path: Path) -> dict[str, Any]:
        """
        Read a blog post and parse YAML frontmatter.

        Args:
            path: Path to the blog post (relative or absolute)

        Returns:
            Dictionary with frontmatter and content
        """
        if not path.is_absolute():
            path = self.data_root / path

        if not path.exists():
            raise FileNotFoundError(f"Blog post not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Parse frontmatter
        import re
        import yaml

        match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)

        if match:
            frontmatter_str = match.group(1)
            body = match.group(2)
            frontmatter = yaml.safe_load(frontmatter_str)
            return {**frontmatter, "content": body}
        else:
            # No frontmatter found
            return {"content": content}


class StorageManager:
    """
    Central storage coordinator for all data types.

    Provides convenience methods for accessing different data collections.
    Uses LanceDB for fast queries when available, JSONL as persistent storage.
    """

    def __init__(self, data_root: Path, vector_store=None):
        """
        Initialize storage manager.

        Args:
            data_root: Root directory for data storage
            vector_store: Optional VectorStore for fast queries
        """
        self.data_root = Path(data_root)
        self.jsonl = JSONLStore(data_root)
        self.markdown = MarkdownStore(data_root)
        self.vector_store = vector_store  # Optional LanceDB vector store

        # Ensure all directories exist
        self._init_directories()

    def _init_directories(self) -> None:
        """Create all required directories."""
        dirs = [
            "subscriptions",
            "inbox",
            "curated/archives",
            "blogs",
            "github",
            "metrics",
            "logs",
            "index",
            "schemas",
        ]

        for dir_path in dirs:
            (self.data_root / dir_path).mkdir(parents=True, exist_ok=True)

    # Subscription management
    def read_x_creators(self) -> list[dict]:
        """Read all X creator subscriptions."""
        return self.jsonl.read_all(Path("subscriptions/x_creators.jsonl"))

    def write_x_creators(self, creators: list[dict]) -> None:
        """Write X creator subscriptions."""
        self.jsonl.append(Path("subscriptions/x_creators.jsonl"), creators)

    def read_rss_feeds(self) -> list[dict]:
        """Read all RSS feed subscriptions."""
        return self.jsonl.read_all(Path("subscriptions/rss_feeds.jsonl"))

    def write_rss_feeds(self, feeds: list[dict]) -> None:
        """Write RSS feed subscriptions."""
        self.jsonl.append(Path("subscriptions/rss_feeds.jsonl"), feeds)

    # Inbox management
    def read_inbox(self) -> list[dict]:
        """
        Read all inbox items.

        Uses LanceDB for fast queries if available, otherwise falls back to JSONL.
        """
        if self.vector_store:
            try:
                # Try to get from LanceDB first (much faster for large datasets)
                stats = self.vector_store.get_stats()
                if stats.get("num_rows", 0) > 0:
                    logger.debug("Reading inbox from LanceDB (fast path)")
                    return self.vector_store.get_all()
                else:
                    logger.debug("LanceDB empty, falling back to JSONL")
            except Exception as e:
                logger.warning(f"LanceDB read failed, falling back to JSONL: {e}")

        # Fallback to JSONL
        return self.jsonl.read_all(Path("inbox/items.jsonl"))

    def write_inbox(self, items: list[dict]) -> None:
        """Write inbox items."""
        self.jsonl.append(Path("inbox/items.jsonl"), items)

    def clear_inbox(self) -> None:
        """Clear all inbox items."""
        path = self.data_root / "inbox/items.jsonl"
        if path.exists():
            path.unlink()

    def remove_inbox_items(self, items_to_remove: list[dict]) -> int:
        """
        Remove specific items from inbox by their IDs.

        Uses the same deduplication key as ingestion: (source, original_id, author_id)

        Args:
            items_to_remove: List of items to remove (must have source, original_id, author_id)

        Returns:
            Number of items removed
        """
        # Build set of IDs to remove
        ids_to_remove = {
            (item.get("source"), item.get("original_id"), item.get("author_id"))
            for item in items_to_remove
        }

        removed_count = 0

        # If vector store is available, use it for fast deletion
        if self.vector_store:
            try:
                logger.debug("Removing items from LanceDB (fast path)")
                removed_count = self.vector_store.delete_by_ids(ids_to_remove)

                # Also update JSONL (for backup)
                all_items = self.jsonl.read_all(Path("inbox/items.jsonl"))
                remaining_items = [
                    item for item in all_items
                    if (item.get("source"), item.get("original_id"), item.get("author_id")) not in ids_to_remove
                ]

                path = self.data_root / "inbox/items.jsonl"
                if remaining_items:
                    content = "\n".join(
                        json.dumps(item, ensure_ascii=False, default=str) for item in remaining_items
                    )
                    content += "\n"
                    self.jsonl.atomic_write(path, content)
                else:
                    if path.exists():
                        path.unlink()

                return removed_count

            except Exception as e:
                logger.warning(f"LanceDB delete failed, falling back to JSONL: {e}")

        # Fallback to JSONL-only approach
        all_items = self.read_inbox()

        if not all_items:
            return 0

        # Filter out items to remove
        remaining_items = [
            item for item in all_items
            if (item.get("source"), item.get("original_id"), item.get("author_id")) not in ids_to_remove
        ]

        removed_count = len(all_items) - len(remaining_items)

        if removed_count == 0:
            return 0

        # Rewrite inbox with remaining items
        path = self.data_root / "inbox/items.jsonl"

        if remaining_items:
            content = "\n".join(
                json.dumps(item, ensure_ascii=False, default=str) for item in remaining_items
            )
            content += "\n"
            self.jsonl.atomic_write(path, content)
        else:
            # If no items left, delete the file
            if path.exists():
                path.unlink()

        return removed_count

    # Curated content management
    def read_curated(self, date: str) -> list[dict]:
        """Read curated items for a specific date."""
        path = Path(f"curated/{date}_ranked.jsonl")
        return self.jsonl.read_all(path)

    def write_curated(self, date: str, items: list[dict]) -> None:
        """Write curated items for a specific date."""
        path = Path(f"curated/{date}_ranked.jsonl")
        self.jsonl.append(path, items)

    def archive_curated(self, date: str) -> None:
        """Archive curated file to archives directory."""
        src = self.data_root / f"curated/{date}_ranked.jsonl"
        dst = self.data_root / f"curated/archives/{date}_ranked.jsonl"
        if src.exists():
            shutil.move(str(src), str(dst))

    # Blog management
    def write_blog(self, filename: str, blog_post: BaseModel) -> None:
        """Write a blog post."""
        path = Path(f"blogs/{filename}")
        self.markdown.write_blog_post(path, blog_post)

    # GitHub issues (Workflow A)
    def read_github_issues(self) -> list[dict]:
        """Read all GitHub issues."""
        return self.jsonl.read_all(Path("github/issues.jsonl"))

    def write_github_issues(self, issues: list[dict]) -> None:
        """Write GitHub issues (overwrite)."""
        self.jsonl.write(Path("github/issues.jsonl"), issues)

    # Metrics (Workflow C)
    def read_metrics(self) -> list[dict]:
        """Read all metrics."""
        return self.jsonl.read_all(Path("metrics/stats.jsonl"))

    def write_metrics(self, metrics: list[dict]) -> None:
        """Write metrics (overwrite mode)."""
        self.jsonl.write(Path("metrics/stats.jsonl"), metrics)
