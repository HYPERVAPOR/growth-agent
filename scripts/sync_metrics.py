#!/usr/bin/env python
"""
Manual trigger for social media metrics synchronization.

This script fetches engagement metrics from X/Twitter and saves them for tracking.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.storage import StorageManager
from growth_agent.workflows.workflow_c import WorkflowC


def main():
    """Manually trigger social media metrics synchronization."""
    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("社交媒体指标同步")
    print("=" * 60)

    # Get account info
    username = "puppyone_ai"  # Default account
    user_id = "1689650211810123776"  # @puppyone_ai user ID

    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        user_id = sys.argv[2]

    print(f"账号: @{username}")
    if user_id:
        print(f"用户ID: {user_id}")
    print(f"数量: 20 条推文")

    # Initialize storage
    storage = StorageManager(settings.data_root)
    workflow = WorkflowC(settings, storage)

    # Validate prerequisites
    print("\n检查前置条件...")
    if not workflow.validate_prerequisites():
        print("\n✗ 前置条件检查失败")
        print("  请确保：")
        print("  1. 已配置 X_RAPIDAPI_KEY")
        return 1

    print("✓ 前置条件检查通过")

    # Run sync
    print(f"\n开始同步 @{username} 的指标...")
    result = workflow.execute(username=username, user_id=user_id, count=20)

    if result.success:
        print("\n" + "=" * 60)
        print(f"✓ 同步完成!")
        print("=" * 60)

        metadata = result.metadata
        print(f"\n账号: @{metadata.get('username')}")
        print(f"获取: {metadata.get('fetched_count', 0)} 条推文")
        print(f"\n总指标:")
        print(f"  - 浏览量: {metadata.get('total_impressions', 0):,}")
        print(f"  - 互动数: {metadata.get('total_engagements', 0):,}")
        print(f"  - 点赞数: {metadata.get('total_likes', 0):,}")
        print(f"  - 转发数: {metadata.get('total_retweets', 0):,}")

        if result.errors:
            print(f"\n遇到 {len(result.errors)} 个警告:")
            for error in result.errors:
                print(f"  - {error}")

        print("\n数据已保存到: data/metrics/stats.jsonl")

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
