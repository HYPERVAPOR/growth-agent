#!/usr/bin/env python
"""
Manual trigger for GitHub issues synchronization.

This script fetches issues from GitHub and syncs them to data/github/issues.jsonl.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from growth_agent.config import Settings, reload_settings
from growth_agent.core.logging import setup_logging
from growth_agent.core.storage import StorageManager
from growth_agent.workflows.workflow_a import WorkflowA


def main():
    """Manually trigger GitHub issues synchronization."""
    # Load settings
    settings = reload_settings()
    setup_logging(settings)

    print("=" * 60)
    print("GitHub Issues 同步")
    print("=" * 60)
    print(f"仓库: {settings.repo_path}")
    print(f"状态: open")
    print(f"限制: 100 条")

    # Initialize storage
    storage = StorageManager(settings.data_root)
    workflow = WorkflowA(settings, storage)

    # Validate prerequisites
    print("\n检查前置条件...")
    if not workflow.validate_prerequisites():
        print("\n✗ 前置条件检查失败")
        print("  请确保：")
        print("  1. 已安装 GitHub CLI (gh): https://cli.github.com/")
        print("  2. 已配置 GITHUB_TOKEN (可选但推荐)")
        print("  3. 已配置 REPO_PATH (例如: owner/repo)")
        return 1

    print("✓ 前置条件检查通过")

    # Run sync
    print("\n开始同步 issues...")
    result = workflow.execute(state="open", limit=100)

    if result.success:
        print("\n" + "=" * 60)
        print(f"✓ 同步完成!")
        print("=" * 60)

        metadata = result.metadata
        print(f"\n仓库: {metadata.get('repo')}")
        print(f"获取: {metadata.get('fetched_count', 0)} 条")
        print(f"新增: {metadata.get('new_count', 0)} 条")
        print(f"更新: {metadata.get('updated_count', 0)} 条")
        print(f"未变: {metadata.get('unchanged_count', 0)} 条")
        print(f"总计: {result.items_processed} 条")

        if result.errors:
            print(f"\n遇到 {len(result.errors)} 个错误:")
            for error in result.errors:
                print(f"  - {error}")

        print("\n数据已保存到: data/github/issues.jsonl")

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
