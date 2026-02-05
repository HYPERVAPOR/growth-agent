#!/usr/bin/env python
"""
Manual trigger for content curation using LLM.

This script evaluates inbox items and filters high-quality content.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, UTC

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.llm import LLMClient
from growth_agent.core.schema import CuratedItem
from growth_agent.core.storage import StorageManager
from growth_agent.core.vector_store import VectorStore
from growth_agent.processors.curator import ContentCurator
from growth_agent.processors.ranker import ContentRanker


def main():
    """Manually trigger content curation."""
    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("手动触发内容评估")
    print("=" * 60)
    print(f"LanceDB: {'启用' if settings.use_lancedb else '禁用'}")

    # Initialize with optional vector store
    vector_store = None
    llm_client = LLMClient(settings)

    if settings.use_lancedb:
        vector_store = VectorStore(settings, llm_client)
        print("✓ LanceDB已启用 (快速查询)")
    else:
        print("✓ LanceDB已禁用 (仅使用JSONL)")

    storage = StorageManager(settings.data_root, vector_store=vector_store)
    curator = ContentCurator(llm_client)
    ranker = ContentRanker()

    # Read inbox items
    print("\n读取inbox内容...")
    inbox_items = storage.read_inbox()

    if not inbox_items:
        print("❌ inbox为空，请先运行: python scripts/sync_content.py")
        return

    print(f"找到 {len(inbox_items)} 条待评估内容")

    # Limit items to evaluate (for cost control)
    items_to_evaluate = inbox_items
    if len(inbox_items) > settings.max_curate_items:
        print(f"限制评估数量为 {settings.max_curate_items} 条 (从 {len(inbox_items)} 条中)")
        items_to_evaluate = inbox_items[:settings.max_curate_items]

    print(f"将评估 {len(items_to_evaluate)} 条内容\n")

    # Evaluate with LLM
    print("开始LLM评估...")
    print("(这可能需要几分钟，请耐心等待...)\n")

    curated_items = curator.evaluate_items(items_to_evaluate)

    if not curated_items:
        print("❌ 评估失败或没有内容通过评估")
        return

    print(f"✓ 成功评估 {len(curated_items)} 条内容")

    # Filter and rank
    print(f"\n过滤和排序 (分数 >= {settings.curation_min_score}, 前{settings.curation_top_k}名)...")
    top_items = ranker.filter_and_rank(
        curated_items,
        min_score=settings.curation_min_score,
        top_k=settings.curation_top_k,
    )

    if not top_items:
        print("❌ 没有内容达到评分标准")
        return

    print(f"✓ 筛选出 {len(top_items)} 条高质量内容")

    # Show statistics
    stats = ranker.get_statistics(curated_items)
    print(f"\n评分统计:")
    print(f"  平均分: {stats['avg_score']:.1f}")
    print(f"  最高分: {stats['max_score']}")
    print(f"  最低分: {stats['min_score']}")

    # Save curated items
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    curated_data = [item.model_dump() for item in top_items]

    storage.write_curated(date_str, curated_data)
    print(f"\n✓ 已保存到: data/curated/{date_str}_ranked.jsonl")

    # Remove only the evaluated items from inbox
    removed_count = storage.remove_inbox_items(items_to_evaluate)
    remaining_count = len(inbox_items) - removed_count
    print(f"✓ 已删除 {removed_count} 条已评估内容 (剩余 {remaining_count} 条未评估内容)")

    # Show top items
    print(f"\n🏆 前{len(top_items)}名:")
    for idx, item in enumerate(top_items, 1):
        print(f"  {idx}. [{item.score}分] {item.summary[:60]}...")

    print("\n" + "=" * 60)
    print("评估完成")
    print("=" * 60)

    print("\n下一步:")
    print("  生成博客: python scripts/generate_blog.py")
    print("  或运行完整workflow: python -m growth_agent.main run workflow-b")


if __name__ == "__main__":
    main()
