# 文档处理器测试套件

本目录包含所有文档处理器的测试文件，用于验证各处理器的功能正确性。

## 📁 测试文件列表

| 测试文件 | 处理器类型 | 测试用例数 | 说明 |
|----------|------------|------------|------|
| `test_pdf_processor.py` | PDF处理器 | 12个 | 测试v1临时文件模式和v2内存buffer模式 |
| `test_ppt_processor.py` | PPT处理器 | 12个 | 测试python-pptx后端和文本提取 |
| `test_text_processor.py` | 文本处理器 | 14个 | 测试多编码和多格式支持 |
| `test_docx_processor.py` | DOCX处理器 | 14个 | 测试python-docx和docx2txt后端 |
| `test_image_processor.py` | 图片处理器 | 13个 | 测试多格式图片和视觉模型 |
| `test_unified_processor.py` | 统一处理器 | 12个 | 测试所有文档类型的统一接口 |

## 🚀 运行测试

### 运行所有测试
```bash
# 从项目根目录运行
python test/run_all_tests.py

# 或从test目录运行
cd test && python run_all_tests.py
```

### 运行单个测试
```bash
# PDF处理器测试
python test/test_pdf_processor.py

# PPT处理器测试
python test/test_ppt_processor.py

# 文本处理器测试
python test/test_text_processor.py

# DOCX处理器测试
python test/test_docx_processor.py

# 图片处理器测试
python test/test_image_processor.py

# 统一处理器测试
python test/test_unified_processor.py
```

## 📊 测试覆盖率

### PDF处理器 (test_pdf_processor.py)
- ✅ v1模式：临时文件模式，逐页处理
- ✅ v2模式：内存buffer + base64编码，批量处理
- ✅ 多种处理方法：视觉模型、PyMuPDF、pdfplumber
- ✅ 图片提取功能
- ✅ 元数据完整性
- ✅ 自动分块

### PPT处理器 (test_ppt_processor.py)
- ✅ python-pptx后端
- ✅ 幻灯片文本提取
- ✅ 幻灯片分割
- ✅ 元数据完整性
- ✅ 文本质量验证
- ⚠️ v2模式暂未整合到主类（需要PowerPoint COM）

### 文本处理器 (test_text_processor.py)
- ✅ 多编码支持：UTF-8、GBK等
- ✅ 多格式支持：TXT、MD、RST、RTF
- ✅ 自动编码检测
- ✅ 内容完整性保持
- ✅ 分块功能

### DOCX处理器 (test_docx_processor.py)
- ✅ python-docx后端
- ✅ docx2txt后端
- ✅ 段落提取
- ✅ 表格提取
- ✅ 后端自动选择
- ✅ 性能测试

### 图片处理器 (test_image_processor.py)
- ✅ 多格式支持：PNG、JPG、GIF、BMP、TIFF
- ✅ 视觉模型集成
- ✅ 格式检测
- ✅ 元数据提取
- ✅ 内容质量验证
- ✅ 批量处理

### 统一处理器 (test_unified_processor.py)
- ✅ 多文档类型处理
- ✅ 批量处理
- ✅ 处理器自动选择
- ✅ 分块选项
- ✅ 错误处理
- ✅ use_vision参数

## 🔧 依赖要求

### 基础依赖
```bash
pip install pathlib typing
```

### 测试生成依赖
```bash
# 自动创建测试文件
pip install PyMuPDF python-pptx python-docx pillow
```

### 处理器依赖
```bash
# PDF处理器
pip install PyMuPDF pdfplumber

# PPT处理器
pip install python-pptx

# DOCX处理器
pip install python-docx docx2txt

# 图片处理器
pip install pillow

# 视觉模型（可选）
pip install vision-llm  # 根据实际视觉模型而定
```

## ⚡ 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 或单独安装
pip install PyMuPDF python-pptx python-docx pillow pdfplumber
```

### 2. 运行测试
```bash
# 运行所有测试
python test/run_all_tests.py

# 运行单个测试
python test/test_pdf_processor.py
```

### 3. 查看结果
测试会显示：
- ✅ PASS - 测试通过
- ✗ FAIL - 测试失败
- ℹ INFO - 信息提示
- ⚠ WARN - 警告

## 📝 测试输出示例

```
========================================
PDF PROCESSOR TEST SUITE
========================================

TEST 1: PDFProcessor v1 - mineru method
  ✓ mineru method processed 3 pages

  Page 1:
    Title: 第1页
    Content length: 152 chars
    Preview: 第1页 内容...

TEST SUMMARY
  Total: 7/7 tests passed
```

## 🎯 关键特性测试

### PDF处理器 v2 内存优化
测试PDF处理器的v2模式：
- 内存buffer存储图片（无临时文件）
- Base64编码传输
- 批量视觉模型分析
- 自动按标题切分

### 使用示例
```python
from src.document_processors.pdf_processor import PDFProcessor

processor = PDFProcessor()

# v2模式（推荐）
documents = await processor.process(
    "document.pdf",
    mode='v2_memory_buffer',
    dpi=200,
    chunk_after=True
)
```

## 🐛 问题排查

### 常见错误

#### 1. ModuleNotFoundError: No module named 'src'
**解决方案**: 确保从项目根目录运行测试，或确保路径设置正确
```bash
# 正确方式
python test/test_pdf_processor.py

# 错误方式（从test目录运行）
cd test && python test_pdf_processor.py
```

#### 2. ImportError: No module named 'xxx'
**解决方案**: 安装缺失的依赖
```bash
pip install PyMuPDF  # PDF处理
pip install python-pptx  # PPT处理
pip install python-docx  # DOCX处理
pip install pillow  # 图片处理
```

#### 3. 视觉模型测试失败
**原因**: 视觉模型未配置或不可用
**解决方案**: 配置视觉模型或跳过视觉模型测试

### 调试技巧

1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **查看临时文件**
```python
# 临时文件存储在 temp_pdf_images/ 目录
ls -la temp_pdf_images/
```

3. **检查测试数据**
```bash
ls -la test/test_data/
```

## 📈 性能基准

### 预期性能
- 小文档 (< 1MB): < 1秒
- 中等文档 (1-10MB): 1-5秒
- 大文档 (> 10MB): 5-30秒

### 性能影响因素
- 图片DPI设置（影响处理速度）
- 文档复杂度（影响视觉模型速度）
- 系统资源（CPU、内存）

## 🤝 贡献指南

添加新测试用例：
1. 在相应的测试文件中添加新方法
2. 方法名以 `test_` 开头
3. 在 `run_all_tests()` 中注册新测试
4. 运行测试确保通过

## 📄 许可证

本测试套件与DeepCodeAgent项目使用相同许可证。

---

**注意**: 测试文件会自动生成测试数据，运行完成后会清理临时文件。
