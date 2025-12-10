import abc
import json
import asyncio
import os
from typing import Any, Dict, List, Set, Optional

from src.config.loader import get_str_env
from src.rag.rag import BaseKVStorage


# --- 2. 简单的 JSON 实现 ---
class JsonKVStorage(BaseKVStorage):
    def __init__(self, file_path: str| None = None):
        """
        初始化 JSON KV 存储。
        
        Args:
            file_path: JSON 文件的存储路径
        """
        self.file_path = get_str_env("JSON_KV_FILE_PATH", "jsonstroge")
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()  # 确保异步环境下的并发安全
        
        # 初始化时加载数据
        self._load_from_disk()

    def _load_from_disk(self):
        """从磁盘加载数据到内存"""
        if not os.path.exists(self.file_path):
            self._data = {}
            # 创建空文件确保路径存在
            self._save_to_disk()
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    self._data = {}
                else:
                    self._data = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load KV file {self.file_path}: {e}")
            self._data = {}

    def _save_to_disk(self):
        """将内存数据持久化到磁盘"""
        # 确保存储目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        async with self._lock:
            return self._data.get(id)

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        async with self._lock:
            return [self._data.get(id) for id in ids]

    async def filter_keys(self, keys: set[str]) -> set[str]:
        async with self._lock:
            # 返回 keys 中不在 self._data 里的那些 key
            existing_keys = set(self._data.keys())
            return keys - existing_keys

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        async with self._lock:
            # 更新内存
            self._data.update(data)
            # 立即持久化 (简单实现模式)
            # 如果需要高性能，可以改为像 LightRAG 那样异步批量写入
            self._save_to_disk()

    async def delete(self, ids: list[str]) -> None:
        async with self._lock:
            changed = False
            for id in ids:
                if id in self._data:
                    del self._data[id]
                    changed = True
            
            if changed:
                self._save_to_disk()

    async def is_empty(self) -> bool:
        async with self._lock:
            return len(self._data) == 0
        
    async def has_id(self, id: str) -> bool:
        """
        检查指定 ID 是否存在。
        
        Args:
            id: 要检查的 ID
            
        Returns:
            bool: 存在返回 True，否则返回 False
        """
        async with self._lock:
            return id in self._data
