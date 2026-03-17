#!/usr/bin/env python
"""
Generate human-readable report from PostHog metrics data.

This script analyzes the posthog_stats.jsonl file and creates
a comprehensive report with statistics and insights.
"""
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_metrics(file_path: str) -> list:
    """Load metrics from JSONL file."""
    metrics = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                metrics.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return metrics


def analyze_event_properties(metrics: list) -> dict:
    """Analyze event properties."""
    event_props = [m for m in metrics if m.get('data_type') == 'event_properties']

    analysis = {
        'total': len(event_props),
        'by_type': defaultdict(int),
        'by_usage': [],
        'high_usage': [],  # > 500 uses
        'medium_usage': [],  # 100-500 uses
        'low_usage': [],  # < 100 uses
        'categories': {
            'device': [],
            'browser': [],
            'session': [],
            'page': [],
            'user': [],
            'technical': [],
            'other': []
        }
    }

    for prop in event_props:
        name = prop.get('event_property_name', '')
        prop_type = prop.get('event_property_type', '')
        usage = prop.get('event_property_usage_count', 0)

        analysis['by_type'][prop_type] += 1
        analysis['by_usage'].append((name, usage, prop_type))

        # Categorize by usage
        if usage > 500:
            analysis['high_usage'].append((name, usage, prop_type))
        elif usage >= 100:
            analysis['medium_usage'].append((name, usage, prop_type))
        else:
            analysis['low_usage'].append((name, usage, prop_type))

        # Categorize by function
        if any(x in name for x in ['viewport', 'screen', 'device', '$os', '$browser']):
            analysis['categories']['device'].append((name, usage))
        elif any(x in name for x in ['session', 'window']):
            analysis['categories']['session'].append((name, usage))
        elif any(x in name for x in ['path', 'url', 'host', 'referrer', 'title']):
            analysis['categories']['page'].append((name, usage))
        elif any(x in name for x in ['user', 'person', 'email', 'id']):
            analysis['categories']['user'].append((name, usage))
        elif name.startswith('$'):
            analysis['categories']['technical'].append((name, usage))
        else:
            analysis['categories']['other'].append((name, usage))

    # Sort by usage
    analysis['by_usage'] = sorted(analysis['by_usage'], key=lambda x: x[1], reverse=True)

    return analysis


def analyze_person_properties(metrics: list) -> dict:
    """Analyze person properties."""
    person_props = [m for m in metrics if m.get('data_type') == 'person_properties']

    analysis = {
        'total': len(person_props),
        'by_type': defaultdict(int),
        'all_props': [],
        'has_value': [],  # Properties with non-None values
        'marketing': [],  # UTM params, click IDs
        'geo': [],  # Geographic info
        'device': [],  # Device/browser info
        'initial': [],  # Initial_* properties
    }

    for prop in person_props:
        name = prop.get('person_property_name', '')
        prop_type = prop.get('person_property_type', '')
        usage = prop.get('person_property_usage_count', 0)

        analysis['by_type'][prop_type] += 1
        analysis['all_props'].append((name, prop_type))

        if prop_type != 'NoneType':
            analysis['has_value'].append((name, prop_type, usage))

        # Categorize
        if any(x in name for x in ['utm_', 'gclid', 'fbclid', 'msclkid', 'ttclid']):
            analysis['marketing'].append((name, prop_type))
        elif 'geoip' in name:
            analysis['geo'].append((name, prop_type))
        elif any(x in name for x in ['device', 'browser', 'os', 'screen']):
            analysis['device'].append((name, prop_type))
        elif name.startswith('$initial_'):
            analysis['initial'].append((name, prop_type))

    return analysis


def generate_report(event_analysis: dict, person_analysis: dict) -> str:
    """Generate human-readable report."""
    report = []
    report.append("=" * 100)
    report.append("PostHog 属性分析报告")
    report.append("=" * 100)
    report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"数据来源: data/metrics/posthog_stats.jsonl\n")

    # Event Properties Summary
    report.append("-" * 100)
    report.append("📊 事件属性 (Event Properties)")
    report.append("-" * 100)
    report.append(f"\n总计: {event_analysis['total']} 个唯一属性\n")

    # Type distribution
    report.append("📈 属性类型分布:")
    for prop_type, count in sorted(event_analysis['by_type'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / event_analysis['total']) * 100
        report.append(f"  {prop_type:30s}: {count:4d} 个 ({percentage:5.1f}%)")

    # Usage tiers
    report.append(f"\n📊 使用频率分层:")
    report.append(f"  高频使用 (>500次):  {len(event_analysis['high_usage']):3d} 个属性")
    report.append(f"  中频使用 (100-500): {len(event_analysis['medium_usage']):3d} 个属性")
    report.append(f"  低频使用 (<100次):  {len(event_analysis['low_usage']):3d} 个属性")

    # Top properties
    report.append(f"\n🔥 使用最多的 20 个属性:")
    for i, (name, usage, prop_type) in enumerate(event_analysis['by_usage'][:20], 1):
        bar = "█" * min(50, int(usage / 20))
        report.append(f"  {i:2d}. {name:35s} [{prop_type:15s}] {usage:4d} {bar}")

    # Category breakdown
    report.append(f"\n📂 功能分类:")
    for category, props in event_analysis['categories'].items():
        if props:
            props_sorted = sorted(props, key=lambda x: x[1], reverse=True)
            report.append(f"\n  {category.upper()} ({len(props)} 个属性):")
            for name, usage in props_sorted[:5]:
                report.append(f"    - {name:35s}: {usage:4d} 次")
            if len(props_sorted) > 5:
                report.append(f"    ... 还有 {len(props_sorted) - 5} 个")

    # Person Properties Summary
    report.append("\n" + "-" * 100)
    report.append("👤 用户属性 (Person Properties)")
    report.append("-" * 100)
    report.append(f"\n总计: {person_analysis['total']} 个唯一属性\n")

    # Type distribution
    report.append("📈 属性类型分布:")
    for prop_type, count in sorted(person_analysis['by_type'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / person_analysis['total']) * 100
        report.append(f"  {prop_type:30s}: {count:4d} 个 ({percentage:5.1f}%)")

    # Properties with values
    report.append(f"\n✅ 有值的属性: {len(person_analysis['has_value'])} 个")
    if person_analysis['has_value']:
        report.append("  列表:")
        for name, prop_type, usage in sorted(person_analysis['has_value'], key=lambda x: x[0]):
            report.append(f"    - {name:35s} [{prop_type:15s}]")

    # Marketing attributes
    if person_analysis['marketing']:
        report.append(f"\n📢 营销追踪属性: {len(person_analysis['marketing'])} 个")
        for name, prop_type in person_analysis['marketing']:
            status = "✓ 有值" if prop_type != 'NoneType' else "✗ 未设置"
            report.append(f"    - {name:35s} [{status}]")

    # Geographic attributes
    if person_analysis['geo']:
        report.append(f"\n🌍 地理位置属性: {len(person_analysis['geo'])} 个")
        for name, prop_type in sorted(person_analysis['geo']):
            status = "✓ 有值" if prop_type != 'NoneType' else "✗ 未设置"
            report.append(f"    - {name:35s} [{status}]")

    # Device attributes
    if person_analysis['device']:
        report.append(f"\n💻 设备信息属性: {len(person_analysis['device'])} 个")
        for name, prop_type in sorted(person_analysis['device']):
            status = "✓ 有值" if prop_type != 'NoneType' else "✗ 未设置"
            report.append(f"    - {name:35s} [{status}]")

    # Insights
    report.append("\n" + "-" * 100)
    report.append("💡 关键洞察")
    report.append("-" * 100)

    insights = []

    # Event insights
    if event_analysis['total'] > 0:
        most_used = event_analysis['by_usage'][0]
        insights.append(f"• 最常用的事件属性是 '{most_used[0]}'，在 {most_used[1]} 个事件中使用")

        high_usage_count = len(event_analysis['high_usage'])
        if high_usage_count > 0:
            insights.append(f"• 有 {high_usage_count} 个核心属性在超过 80% 的事件中使用")

        str_count = event_analysis['by_type'].get('str', 0)
        insights.append(f"• {str_count} 个属性 ({str_count/event_analysis['total']*100:.1f}%) 是字符串类型，主要包含 URL、路径等文本数据")

    # Person insights
    if person_analysis['total'] > 0:
        none_count = person_analysis['by_type'].get('NoneType', 0)
        if none_count > 0:
            insights.append(f"• {none_count} 个用户属性 ({none_count/person_analysis['total']*100:.1f}%) 当前未设置值，主要是营销追踪参数")

        has_geo = any(prop_type != 'NoneType' for _, prop_type in person_analysis['geo'])
        if has_geo:
            insights.append("• 地理位置追踪已启用，可以分析用户地域分布")

        has_marketing = any(prop_type != 'NoneType' for _, prop_type in person_analysis['marketing'])
        if has_marketing:
            insights.append("• 部分营销追踪参数已设置，可以进行渠道归因分析")

    report.append("\n")
    for insight in insights:
        report.append(insight)

    # Recommendations
    report.append("\n" + "-" * 100)
    report.append("🎯 优化建议")
    report.append("-" * 100)

    recommendations = []

    if person_analysis['by_type'].get('NoneType', 0) > 50:
        recommendations.append("• 考虑启用更多营销追踪参数 (UTM, Click IDs) 以改善渠道分析")

    if len(event_analysis['categories']['device']) < 5:
        recommendations.append("• 建议增加更多设备相关的自定义事件属性以更好地了解用户行为")

    if len(person_analysis['has_value']) < len(person_analysis['all_props']) * 0.5:
        recommendations.append("• 用户属性填充率较低，建议在关键触点收集更多用户信息")

    recommendations.append("• 定期监控高频使用的属性，确保数据质量")
    recommendations.append("• 考虑设置属性命名规范，便于团队协作")

    for rec in recommendations:
        report.append(f"\n{rec}")

    report.append("\n" + "=" * 100)
    report.append("报告结束")
    report.append("=" * 100)

    return "\n".join(report)


def main():
    """Main execution."""
    metrics_file = "data/metrics/posthog_stats.jsonl"

    # Check if file exists
    if not Path(metrics_file).exists():
        print(f"❌ 错误: 文件不存在 - {metrics_file}")
        print("   请先运行数据获取脚本: bash scripts/workflow_c.sh --source posthog")
        sys.exit(1)

    print("📊 正在分析 PostHog 数据...")
    print(f"   来源: {metrics_file}")

    # Load metrics
    metrics = load_metrics(metrics_file)
    print(f"   加载: {len(metrics)} 条记录")

    # Analyze
    event_analysis = analyze_event_properties(metrics)
    person_analysis = analyze_person_properties(metrics)

    # Generate report
    report = generate_report(event_analysis, person_analysis)

    # Output to console and file
    print("\n" + report)

    # Save to file
    report_file = "docs/posthog-analysis-report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
