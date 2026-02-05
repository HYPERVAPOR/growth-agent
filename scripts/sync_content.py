#!/usr/bin/env python
"""
Manual trigger for content ingestion from X and RSS sources.

This script reuses Workflow B's ingestion logic with all business logic from src/.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.llm import LLMClient
from growth_agent.core.storage import StorageManager
from growth_agent.core.vector_store import VectorStore
from growth_agent.workflows.workflow_b import WorkflowB


def main():
    """Manually trigger content ingestion only (no curation or generation)."""
    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("手动触发内容同步")
    print("=" * 60)
    print(f"配置: 每个源最多获取 {settings.max_items_per_source} 条内容")
    print(f"LanceDB: {'启用' if settings.use_lancedb else '禁用'}")

    # Initialize storage with optional vector store
    vector_store = None
    if settings.use_lancedb:
        llm_client = LLMClient(settings)
        vector_store = VectorStore(settings, llm_client)
        print("✓ LanceDB已启用 (快速查询)")
    else:
        print("✓ LanceDB已禁用 (仅使用JSONL)")

    storage = StorageManager(settings.data_root, vector_store=vector_store)

    workflow = WorkflowB(settings, storage)

    # Validate prerequisites
    if not workflow.validate_prerequisites():
        print("\n✗ 前置条件检查失败")
        print("  请检查配置文件 .env")
        return 1

    # Run ingestion stage only
    print("\n开始同步内容...")
    result = workflow._run_ingestion()

    if result.success:
        print("\n" + "=" * 60)
        print(f"✓ 同步完成!")
        print("=" * 60)
        print(f"\n获取内容:")
        print(f"  - X创作者: {result.metadata.get('x_creators_processed', 0)} 个")
        print(f"  - RSS源: {result.metadata.get('rss_feeds_processed', 0)} 个")
        print(f"  - 总条数: {result.items_processed} 条")

        if result.errors:
            print(f"\n遇到 {len(result.errors)} 个错误:")
            for error in result.errors:
                print(f"  - {error}")

        print("\n下一步:")
        print("  运行评估: uv run python scripts/curate_content.py")
        print("  或完整workflow: uv run python -m growth_agent.main run workflow-b")

        return 0
    else:
        print("\n✗ 同步失败")
        if result.errors:
            print("\n错误信息:")
            for error in result.errors:
                print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
