#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepCodeAgent - 主程序入口文件
支持命令行和交互式两种运行模式
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.deepcodeagent.workflow import workflowfun


async def run_single_task(requirement: str, output_dir: str = None):
    """运行单个任务"""
    print("=" * 60)
    print("DeepCodeAgent - AI驱动的代码生成系统")
    print("=" * 60)
    print(f"\n任务需求: {requirement}")
    print("\n开始处理...\n")

    result = await workflowfun(requirement, output_dir)

    print("\n" + "=" * 60)
    print("执行结果:")
    print("=" * 60)

    if result.get("success", False):
        print(f"[OK] 任务完成")
        print(f"[INFO] 会话ID: {result.get('session_id')}")
        print(f"[INFO] 任务类型: {result.get('task_type')}")

        if result.get("files_created"):
            print(f"\n创建的文件:")
            for file in result["files_created"]:
                print(f"  - {file}")

        if result.get("research_output"):
            print(f"\n研究摘要:")
            print(result["research_output"][:300] + "..." if len(result["research_output"]) > 300 else result["research_output"])
    else:
        print(f"[ERROR] 任务失败")
        print(f"错误信息: {result.get('error', '未知错误')}")

    print("\n" + "=" * 60)
    return result


async def interactive_mode():
    """交互式模式"""
    print("=" * 60)
    print("DeepCodeAgent - 交互式模式")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出程序")
    print("输入 'help' 查看帮助信息\n")

    while True:
        try:
            user_input = input("\n请输入您的需求: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n感谢使用 DeepCodeAgent！")
                break

            if user_input.lower() in ['help', '帮助']:
                print("\n帮助信息:")
                print("- 直接输入您的编程需求，例如:")
                print("  * '创建一个计算器应用'")
                print("  * '编写一个Python函数来排序数组'")
                print("  * '实现一个简单的web服务器'")
                print("  * '分析并优化这段代码的性能'")
                print("\n- 输入 'quit' 或 'exit' 退出程序")
                continue

            if not user_input:
                continue



            await run_single_task(user_input)

        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")


async def test_full_workflow():
    """测试完整工作流程"""
    print("=" * 60)
    print("DeepCodeAgent - 完整工作流程测试")
    print("=" * 60)

    test_cases = [
        {
            "name": "直接回答测试",
            "requirement": "什么是Python？",
            "expected_type": "direct_answer"
        },
        {
            "name": "编码任务测试",
            "requirement": "创建一个简单的todolist应用",
            "expected_type": "coding_only"
        },
        {
            "name": "研究任务测试",
            "requirement": "研究微服务架构的最佳实践",
            "expected_type": "research_only"
        }
    ]

    results = []
    test_output_dir = Path("testdir") / f"workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_output_dir.mkdir(parents=True, exist_ok=True)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['name']}")
        print(f"需求: {test_case['requirement']}")
        print("-" * 40)

        try:
            result = await workflowfun(
                test_case['requirement'],
                str(test_output_dir / f"test_{i}")
            )

            results.append({
                "test_name": test_case['name'],
                "requirement": test_case['requirement'],
                "expected_type": test_case['expected_type'],
                "actual_type": result.get('task_type'),
                "success": result.get('success', False),
                "result": result
            })

            # 验证结果
            if result.get('success', False):
                print(f"[✓] 测试通过")
                print(f"  任务类型: {result.get('task_type')}")
                if result.get('files_created'):
                    print(f"  创建文件: {len(result['files_created'])}个")
            else:
                print(f"[✗] 测试失败")
                print(f"  错误: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"[✗] 测试异常: {str(e)}")
            results.append({
                "test_name": test_case['name'],
                "requirement": test_case['requirement'],
                "expected_type": test_case['expected_type'],
                "actual_type": "error",
                "success": False,
                "error": str(e)
            })

    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for r in results if r.get('success', False))
    total = len(results)

    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")

    print("\n详细结果:")
    for result in results:
        status = "✓" if result.get('success', False) else "✗"
        print(f"  {status} {result['test_name']}")
        print(f"    需求: {result['requirement']}")
        print(f"    预期类型: {result['expected_type']}")
        print(f"    实际类型: {result.get('actual_type', 'N/A')}")
        if not result.get('success', False) and 'error' in result:
            print(f"    错误: {result['error']}")

    # 保存测试报告
    import json
    report_file = test_output_dir / "test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{passed/total*100:.1f}%"
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n测试报告已保存到: {report_file}")
    return results


async def batch_mode(requirements_file: str, output_dir: str = None):
    """批处理模式"""
    print("=" * 60)
    print("DeepCodeAgent - 批处理模式")
    print("=" * 60)

    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip()]

        print(f"从文件加载了 {len(requirements)} 个任务")

        results = []
        for i, req in enumerate(requirements, 1):
            print(f"\n[{i}/{len(requirements)}] 处理任务: {req}")
            result = await workflowfun(req, output_dir)
            results.append(result)

            # 显示简要结果
            status = "[OK]" if result.get("success", False) else "[FAIL]"
            print(f"   {status} {result.get('task_type', 'unknown')}")

        # 保存批处理结果
        output_path = Path(output_dir or "batch_output")
        output_path.mkdir(parents=True, exist_ok=True)

        summary_file = output_path / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_tasks": len(requirements),
                "successful": sum(1 for r in results if r.get("success", False)),
                "failed": sum(1 for r in results if not r.get("success", False)),
                "results": results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n批处理完成！结果已保存到: {summary_file}")

    except FileNotFoundError:
        print(f"错误: 找不到需求文件 '{requirements_file}'")
    except Exception as e:
        print(f"批处理错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="DeepCodeAgent - AI驱动的代码生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py "创建一个简单的Flask应用"
  python main.py -i                    # 交互式模式
  python main.py -f tasks.txt -o output  # 批处理模式
  python main.py -t                    # 运行完整工作流程测试
        """
    )

    parser.add_argument(
        "requirement",
        nargs="?",
        help="任务需求描述"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="启动交互式模式"
    )

    parser.add_argument(
        "-f", "--file",
        help="从文件读取多个任务需求（批处理模式）"
    )

    parser.add_argument(
        "-o", "--output",
        help="输出目录（默认: testdir/TIMESTAMP）"
    )

    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="运行完整工作流程测试"
    )

    args = parser.parse_args()

    # 运行模式判断
    if args.test:
        # 测试模式
        asyncio.run(test_full_workflow())
    elif args.interactive:
        # 交互式模式
        asyncio.run(interactive_mode())
    elif args.file:
        # 批处理模式
        asyncio.run(batch_mode(args.file, args.output))
    elif args.requirement:
        # 单任务模式
        asyncio.run(run_single_task(args.requirement, args.output))
    else:
        # 默认进入交互式模式
        print("未指定任务，进入交互式模式...")
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()