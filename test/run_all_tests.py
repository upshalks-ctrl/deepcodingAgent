#!/usr/bin/env python3
"""
运行所有文档处理器测试
"""

import asyncio
import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_header(title):
    """打印测试标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_section(title):
    """打印部分标题"""
    print("\n" + "-"*70)
    print(f"  {title}")
    print("-"*70)


async def run_test(test_file):
    """运行单个测试文件"""
    print_section(f"运行测试: {test_file}")

    try:
        # 导入测试模块
        spec = __import__(f"test.{test_file}", fromlist=['main'])

        # 运行测试
        if hasattr(spec, 'main'):
            success = await spec.main()
            if success:
                print(f"\n✓ {test_file} - 所有测试通过")
            else:
                print(f"\n✗ {test_file} - 部分测试失败")
            return success
        else:
            print(f"\n✗ {test_file} - 未找到main函数")
            return False
    except Exception as e:
        print(f"\n✗ {test_file} - 运行错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数 - 运行所有测试"""
    print_header("文档处理器测试套件")
    print("这是一个综合测试套件，测试所有文档处理器的功能")
    print("\n测试包括:")
    print("  • PDF处理器 (v1临时文件 + v2内存buffer)")
    print("  • PPT处理器 (python-pptx)")
    print("  • 文本处理器 (多编码支持)")
    print("  • DOCX处理器 (python-docx + docx2txt)")
    print("  • 图片处理器 (多格式支持)")
    print("  • 统一处理器 (所有类型)")

    # 测试文件列表
    test_files = [
        "test_pdf_processor",
        "test_ppt_processor",
        "test_text_processor",
        "test_docx_processor",
        "test_image_processor",
        "test_unified_processor",
    ]

    results = []
    total_tests = len(test_files)

    # 运行每个测试
    for i, test_file in enumerate(test_files, 1):
        print_header(f"进度: {i}/{total_tests}")
        success = await run_test(test_file)
        results.append((test_file, success))

    # 总结
    print_header("测试总结")
    passed = sum(1 for _, success in results if success)
    failed = total_tests - passed

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/total_tests*100:.1f}%")

    print("\n详细结果:")
    for test_file, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status} - {test_file}")

    # 提供使用说明
    print("\n" + "="*70)
    print("使用说明")
    print("="*70)
    print("\n运行单个测试:")
    print("  python test/test_pdf_processor.py")
    print("  python test/test_text_processor.py")
    print("\n从项目根目录运行:")
    print("  python test/run_all_tests.py")
    print("\n从test目录运行:")
    print("  cd test && python run_all_tests.py")

    # 返回结果
    return failed == 0


if __name__ == "__main__":
    print("DeepCodeAgent - 文档处理器测试套件")
    print("="*70)
    print(f"项目目录: {project_root}")
    print(f"Python版本: {sys.version}")
    print("="*70)

    result = asyncio.run(main())

    # 退出码
    sys.exit(0 if result else 1)
