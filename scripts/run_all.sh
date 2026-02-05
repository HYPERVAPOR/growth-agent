#!/bin/bash
# Run all workflow stages manually

set -e  # Exit on error

echo "=================================================="
echo "Growth Agent - 完整流程手动执行"
echo "=================================================="

cd "$(dirname "$0")/.."

echo ""
echo "[1/3] 同步内容..."
python scripts/sync_content.py

echo ""
echo "[2/3] 评估内容..."
python scripts/curate_content.py

echo ""
echo "[3/3] 生成博客..."
python scripts/generate_blog.py

echo ""
echo "=================================================="
echo "✓ 所有步骤完成!"
echo "=================================================="
