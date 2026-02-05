#!/usr/bin/env python
"""
Manual trigger for blog generation from curated content.

This script generates blog posts from previously curated content.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime, UTC

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.llm import LLMClient
from growth_agent.core.storage import StorageManager
from growth_agent.processors.blog_generator import BlogGenerator


def main():
    """Manually trigger blog generation."""
    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("手动触发博客生成")
    print("=" * 60)

    # Initialize
    storage = StorageManager(settings.data_root)
    llm_client = LLMClient(settings)
    blog_generator = BlogGenerator(llm_client)

    # Read today's curated items
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    print(f"\n读取今天的精选内容 ({date_str})...")

    curated_items_data = storage.read_curated(date_str)

    if not curated_items_data:
        print(f"❌ 没有找到 {date_str} 的精选内容")
        print("  请先运行: python scripts/curate_content.py")
        return

    print(f"找到 {len(curated_items_data)} 条精选内容")

    # Convert to CuratedItem objects
    from growth_agent.core.schema import CuratedItem

    curated_items = [CuratedItem(**item) for item in curated_items_data]

    # Generate blog
    print("\n开始生成博客...")
    print("(这可能需要几分钟，请耐心等待...)\n")

    try:
        blog_post = blog_generator.generate_blog(
            curated_items=curated_items,
            context="AI and technology insights for business growth",
        )

        # Save blog
        filename = f"{blog_post.id}_{blog_post.slug}.md"
        storage.write_blog(filename, blog_post)

        print(f"✓ 博客生成成功!")
        print(f"\n文件: data/blogs/{filename}")
        print(f"标题: {blog_post.frontmatter.title}")
        print(f"长度: {len(blog_post.content)} 字符")

        # Show preview
        print(f"\n内容预览:")
        print(f"  {blog_post.frontmatter.summary}")
        print(f"  标签: {', '.join(blog_post.frontmatter.tags)}")

        # Archive curated file
        storage.archive_curated(date_str)
        print(f"\n✓ 已归档精选内容到: data/curated/archives/{date_str}_ranked.jsonl")

    except Exception as e:
        print(f"❌ 博客生成失败: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("生成完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
