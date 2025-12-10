# DeepCodeAgent 快速开始指南

## 5分钟快速上手

### 1️⃣ 安装项目
```bash
# 克隆项目
git clone https://github.com/yourusername/deepcodeagent.git
cd deepcodeagent

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置API密钥
编辑 `conf.yaml` 文件：
```yaml
BASIC_MODEL:
  api_key: "你的 DeepSeek API 密钥"
CODE_MODEL:
  api_key: "你的阿里云 DashScope API 密钥"
```

### 3️⃣ 运行第一个任务
```bash
# 交互式模式
python main.py -i

# 或直接运行任务
python main.py "创建一个计算器应用"
```

### 4️⃣ 查看结果
程序会在 `testdir/` 目录下创建输出文件，包含生成的代码和相关文档。

---

## 常见使用场景

### 🏗️ 创建应用
```bash
python main.py "创建一个带有用户认证的Flask博客系统"
```

### 🔍 研究任务
```bash
python main.py "研究微服务架构的最佳实践"
```

### 💻 编写代码
```bash
python main.py "用Python实现一个二叉搜索树"
```

### 🐛 调试代码
```bash
python main.py "分析这段代码的性能瓶颈并优化 [粘贴代码]"
```

---

## 进阶使用

### 批处理模式
创建 `tasks.txt` 文件：
```
创建一个待办事项应用
研究 React hooks 的使用方法
编写一个数据可视化脚本
```

运行：
```bash
python main.py -f tasks.txt -o batch_output
```

### 自定义配置
```python
from src.deepcodeagent.workflow import workflowfun

result = await workflowfun(
    requirement="你的需求",
    output_dir="custom_output",
    session_id="my_session"
)
```

---

## 需要帮助？

- 📖 [完整文档](docs/PROJECT_OVERVIEW.md)
- 🔧 [API 参考](docs/API_REFERENCE.md)
- 👨‍💻 [开发者指南](docs/DEVELOPER_GUIDE.md)
- 🐛 [报告问题](https://github.com/yourusername/deepcodeagent/issues)

---

## 下一步

1. 查看 [示例代码](examples/) 了解更多用法
2. 阅读 [最佳实践](docs/BEST_PRACTICES.md) 优化使用体验
3. 加入我们的 [社区讨论](https://github.com/yourusername/deepcodeagent/discussions)

开始您的 AI 辅助开发之旅吧！🚀