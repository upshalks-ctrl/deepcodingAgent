# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT


import logging

from pathlib import Path
from typing import Dict, List, Optional
from qdrant_client import models
from src.models.document import Document as DocModel
from src.rag.qdrant import QdrantRetriever
from src.llms.llm import get_llm_by_type
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


class EnhancedQdrantRetriever(QdrantRetriever):
    """
    增强版Qdrant检索器
    继承QdrantRetriever，实现文档块的智能合并和嵌入功能

    主要功能：
    1. 合并过小的块（只有source_path和title相同的块才可以合并）
    2. 设定最小chunk_size，所有嵌入块的大小都大于chunk_size
    3. 如果同一个文件剩下最后一个chunk块不满足大小，也可以嵌入
    4. 生成假设性问题并作为元数据传入
    5. 支持会话ID管理
    """

    def __init__(self):
        """
        初始化增强版Qdrant检索器
        """
        super().__init__()
        self._llm: Optional[BaseChatModel] = None
        self._session_id_map: Dict[str, str] = {}  # 存储用户名到会话ID的映射
        self._connect()

    def _get_llm(self) -> BaseChatModel:
        """获取LLM实例"""
        if self._llm is None:
            self._llm = get_llm_by_type("basic")
        return self._llm



    def _generate_questions_for_chunk(self, content: str, title: str) -> List[str]:
        """
        为文档块生成假设性问题

        Args:
            content: 文档内容
            title: 文档标题

        Returns:
            生成的假设性问题列表
        """
        try:
            llm = self._get_llm()
            prompt = f"""
请根据以下文档内容，生成3-5个可能的问题，这些问题应该是该文档能够回答的。

文档标题：{title}

文档内容：
{content[:2000]}  # 限制内容长度避免超出token限制

要求：
1. 问题应该覆盖文档的主要知识点
2. 问题应该具有代表性，能够测试文档的理解程度
3. 问题应该用中文表述
4. 返回格式为JSON数组，每个元素是一个问题字符串

请直接返回JSON数组，不要包含任何解释或前缀。
"""

            response = llm.invoke([{"role": "user", "content": prompt}])
            response_content = response.content if hasattr(response, 'content') else str(response)

            # 尝试解析JSON响应
            import json
            try:
                questions = json.loads(response_content)
                if isinstance(questions, list):
                    return [str(q) for q in questions if isinstance(q, str)]
            except:
                pass

            # 如果解析失败，使用简单的启发式方法
            return [
                f"关于{title}的主要内容是什么？",
                f"{title}中有哪些关键信息？",
                f"如何理解{title}中的核心概念？"
            ]

        except Exception as e:
            logger.warning(f"生成假设性问题失败: {e}")
            # 返回默认问题
            return [
                f"关于{title}的主要内容是什么？",
                f"{title}中有哪些关键信息？"
            ]

    def embed_documents(
        self,
        documents: List[DocModel],
        user_id: str,
        conversation_id: str
    ) -> List[str]:
        """
        将文档块嵌入到向量数据库中

        Args:
            documents: 文档对象列表
            user_id: 用户ID
            conversation_id: 会话ID（可选，如果不提供则自动生成）

        Returns:
            嵌入的文档ID列表
        """
        if not documents:
            logger.warning("没有文档需要嵌入")
            return []



        logger.info(f"开始嵌入 {len(documents)} 个文档块，用户ID: {user_id}, 会话ID: {conversation_id}")


        # 2. 为每个块生成假设性问题
        embedded_doc_ids = []
        for i, doc in enumerate(documents):
            try:
                # 生成假设性问题
                questions = self._generate_questions_for_chunk(doc.content, doc.title)

                # 创建文档ID（使用文件路径和索引）
                source_path = doc.source_path

                doc_id = f"{source_path}_{user_id}_{conversation_id}"
                if doc_id in self.get_doc_id_documents(doc_id):
                    continue
                # 3. 嵌入到向量数据库
                self._insert_document_chunk(
                    doc_id=doc_id,
                    content=doc.content,
                    title=doc.title,
                    url=f"qdrant://{self.collection_name}/{Path(source_path).name}",
                    user_id=user_id,
                    conversation_id=conversation_id,
                    metadata=doc.metadata,
                    generated_questions=questions
                )

                embedded_doc_ids.append(doc_id)
                logger.debug(f"成功嵌入块 {i+1}/{len(documents)}: {doc_id}")

            except Exception as e:
                logger.error(f"嵌入文档块失败 (索引 {i}): {e}")
                continue

        logger.info(f"成功嵌入 {len(embedded_doc_ids)} 个文档块")
        return embedded_doc_ids


    def get_doc_id_documents(
        self,
        doc_id: str,
    ) -> List[str]:
        """
        获取指定会话的文档

        Args:
            doc_id: 文档ID

        Returns:
            文档列表
        """
        if not self.client:
            self._connect()

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # 构建过滤器
            filter_conditions = [
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            ]


            qdrant_filter = Filter(must=filter_conditions)

            points = self.client.query_points(
                collection_name=self.collection_name,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=False,
                limit=1000  # 足够大的限制
            ).points

            documents = []
            for point in points:
                payload = point.payload or {}
                documents.append(payload.get("doc_id", str(point.id)))

            return documents

        except Exception as e:
            logger.error(f"获取会话文档失败: {e}")
            return []

    def delete_conversation_documents(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> int:
        """
        删除指定会话的文档

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（可选）

        Returns:
            删除的文档数量
        """
        if not self.client:
            self._connect()

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # 构建过滤器
            filter_conditions = [
                FieldCondition(key="conversation_id", match=MatchValue(value=conversation_id))
            ]
            if user_id:
                filter_conditions.append(
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                )

            qdrant_filter = Filter(must=filter_conditions)

            # 先查询要删除的文档
            points = self.client.query_points(
                collection_name=self.collection_name,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=False,
                limit=1000
            ).points

            if not points:
                return 0

            # 删除文档
            point_ids = [str(point.id) for point in points]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )

            logger.info(f"删除了 {len(point_ids)} 个会话文档")
            return len(point_ids)

        except Exception as e:
            logger.error(f"删除会话文档失败: {e}")
            return 0

    def create_index(self, field_name: Optional[str] = None, field_schema=None) -> None:
        if not self.client:
            self._connect()
        try:
            if not field_schema:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="doc_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

            else:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_schema,
                )
        except Exception as e:
            logger.warning("Error creating index: %s", e)
