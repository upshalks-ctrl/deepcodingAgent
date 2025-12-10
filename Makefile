# DeepCodeAgent Makefile

.PHONY: help install install-dev test test-coverage lint format clean docs run docker-build docker-run

# 默认目标
help:
	@echo "DeepCodeAgent 开发工具"
	@echo ""
	@echo "可用命令："
	@echo "  install      安装项目依赖"
	@echo "  install-dev  安装开发依赖"
	@echo "  test         运行测试"
	@echo "  test-cov     运行测试并生成覆盖率报告"
	@echo "  lint         代码检查"
	@echo "  format       格式化代码"
	@echo "  clean        清理临时文件"
	@echo "  docs         生成文档"
	@echo "  run          运行主程序"
	@echo "  docker-build 构建Docker镜像"
	@echo "  docker-run   运行Docker容器"

# 安装依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install -r requirements.txt
	pip install -e .[dev,docs]

# 运行测试
test:
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# 代码检查
lint:
	flake8 src/ tests/
	mypy src/

# 格式化代码
format:
	black src/ tests/
	isort src/ tests/

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# 生成文档
docs:
	@if [ -d "docs" ]; then \
		mkdocs build; \
	else \
		echo "文档目录不存在，跳过文档生成"; \
	fi

# 运行主程序
run:
	python main.py -i

# 运行示例
example:
	python main.py "创建一个简单的Flask TODO应用"

# 运行测试模式
test-run:
	python main.py -t

# Docker相关命令
docker-build:
	docker build -t deepcodeagent .

docker-run:
	docker run -it --rm \
		-v $(PWD)/conf.yaml:/app/conf.yaml \
		-v $(PWD)/testdir:/app/testdir \
		deepcodeagent

# 初始化项目
init:
	cp conf.yaml.example conf.yaml
	@echo "请编辑 conf.yaml 文件，添加您的API密钥"

# 发布到PyPI
publish:
	python setup.py sdist bdist_wheel
	twine upload dist/*

# 检查包
check:
	twine check dist/*

# 安装pre-commit钩子
pre-commit:
	pre-commit install

# 全部检查（在提交前运行）
check-all: format lint test-cov
	@echo "所有检查完成！"