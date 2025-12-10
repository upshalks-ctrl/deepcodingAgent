import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set
import asyncio
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client import grpc
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
    PayloadSchemaType,
    Prefetch, Fusion, FusionQuery, PointIdsList
)

from src.config.loader import get_bool_env, get_int_env, get_str_env
from src.rag.rag import Resource, Retriever

logger = logging.getLogger(__name__)

SCROLL_SIZE = 64


class DashscopeEmbeddings:
    """
    Dashscope 提供的文本向量化封装类。

    该类通过调用 Dashscope 的 OpenAI 兼容接口，将文本转换为向量表示，
    支持 query 和文档级别的批量嵌入，并自动处理模型维度映射。
    """
    def __init__(self, **kwargs: Any) -> None:
        self._client: OpenAI = OpenAI(
            api_key=kwargs.get("api_key", ""), base_url=kwargs.get("base_url", "")
        )
        self._model: str = kwargs.get("model", "")
        self._encoding_format: str = kwargs.get("encoding_format", "float")

    def _embed(self, texts: Sequence[str]) -> List[List[float]]:
        clean_texts = [t if isinstance(t, str) else str(t) for t in texts]
        if not clean_texts:
            return []
        resp = self._client.embeddings.create(
            model=self._model,
            input=clean_texts,
            dimensions=self._get_embedding_dimension(self._model)
        )
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> List[float]:
        embeddings = self._embed([text])
        return embeddings[0] if embeddings else []

    def _get_embedding_dimension(self, model_name: str) -> int:
        embedding_dims = {
            "text-embedding-ada-002": 1536,
            "text-embedding-v4": 2048,
        }

        explicit_dim = get_int_env("QDRANT_EMBEDDING_DIM", 0)
        if explicit_dim > 0:
            return explicit_dim
        return embedding_dims.get(model_name, 1536)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)


class QdrantRetriever(Retriever):
    def __init__(self) -> None:
        self.location: str = get_str_env("QDRANT_LOCATION", ":memory:")
        self.api_key: str = get_str_env("QDRANT_API_KEY", "")
        self.collection_name: str = get_str_env("QDRANT_COLLECTION", "documents")

        top_k_raw = get_str_env("QDRANT_TOP_K", "10")
        self.top_k: int = int(top_k_raw) if top_k_raw.isdigit() else 10

        self.embedding_model_name = get_str_env("QDRANT_EMBEDDING_MODEL")
        self.embedding_api_key = get_str_env("QDRANT_EMBEDDING_API_KEY")
        self.embedding_base_url = get_str_env("QDRANT_EMBEDDING_BASE_URL")
        self.embedding_dim: int = self._get_embedding_dimension(
            self.embedding_model_name
        )
        self.embedding_provider = get_str_env("QDRANT_EMBEDDING_PROVIDER", "openai")

        self.auto_load_examples: bool = get_bool_env("QDRANT_AUTO_LOAD_EXAMPLES", True)
        self.examples_dir: str = get_str_env("QDRANT_EXAMPLES_DIR", "examples")
        self.chunk_size: int = get_int_env("QDRANT_CHUNK_SIZE", 4000)
        self.chunk_overlap: int = get_int_env("QDRANT_CHUNK_OVERLAP", 400)


        self._init_embedding_model()
        self._connect()


    def _init_embedding_model(self) -> None:
        kwargs = {
            "api_key": self.embedding_api_key,
            "model": self.embedding_model_name,
            "base_url": self.embedding_base_url,
            "encoding_format": "float",
            "dimensions": self.embedding_dim,
        }
        if self.embedding_provider.lower() == "dashscope":
            self.embedding_model = DashscopeEmbeddings(**kwargs)
        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.embedding_provider}. "
                "Supported providers: openai, dashscope"
            )

    def _get_embedding_dimension(self, model_name: str) -> int:
        embedding_dims = {
            "text-embedding-ada-002": 1536,
            "text-embedding-v4": 2048,
        }

        explicit_dim = get_int_env("QDRANT_EMBEDDING_DIM", 0)
        if explicit_dim > 0:
            return explicit_dim
        return embedding_dims.get(model_name, 1536)

    def _ensure_collection_exists(self) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    # 1. 为“原始内容”定义的向量配置（名字必须与 insert 函数里的 key 一致）
                    "content_vec": VectorParams(
                        size=self.embedding_dim, 
                        distance=Distance.COSINE
                    ),
                    
                    # 2. 为“生成的问题”定义的向量配置（这就是你要的单独索引）
                    "problem_vec": VectorParams(
                        size=self.embedding_dim, 
                        distance=Distance.COSINE
                    ),
                }
            )


    def insert(self,content:str,file_paths:str,doc_id:str,type:str,generate_problem:str) -> None:
        try:
            # 1. 生成 content 的向量
            content_embedding = self._get_embedding(content)
            


            # 2. 构建多向量结构 (Named Vectors)
            # 使用字典将不同的向量分配给不同的名字
            vectors = {
                "content_vec": content_embedding,    # 对应内容的向量空间
            }
            # 3. 动态判断：只有当问题不为空时，才计算并添加 problem_vec
            if generate_problem is not None:
                problem_embedding = self._get_embedding(generate_problem)
                vectors["problem_vec"] = problem_embedding

            payload = {
                "doc_id": doc_id,
                "content": content,
                "title": file_paths,
                "generate_problem": generate_problem,
                "type": type,
            }

            point_id = self._string_to_uuid(doc_id)

            # 4. 传入字典类型的 vectors
            point = PointStruct(id=point_id, vector=vectors, payload=payload)

            self.client.upsert(
                collection_name=self.collection_name, points=[point], wait=True
            )
        except Exception as e:
            logger.error(f"Error insert document: {e}")


    async def ainsert(self,content:str,file_paths:str,doc_id:str,type:str,generate_problem:str) -> None:
        """
        Asynchronous version of insert method to insert documents into Qdrant.
        
        Args:
            content: The content to insert
            file_paths: The file path for the document
            doc_id: The document ID
            type: The document type
            generate_problem: Generated problem for the document
        """

        
        # Use run_in_executor to run synchronous operations asynchronously
        await asyncio.get_event_loop().run_in_executor(
            None,  # Use default executor
            self.insert,  # Call the existing sync method
            content, file_paths, doc_id, type, generate_problem  # Pass all arguments
        )
    def _string_to_uuid(self, text: str) -> str:
        namespace = uuid.NAMESPACE_DNS
        return str(uuid.uuid5(namespace, text))

    def _scroll_all_points(
        self,
        scroll_filter: Optional[Filter] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[Any]:
        results = []
        next_offset = None
        stop_scrolling = False

        while not stop_scrolling:
            points, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=SCROLL_SIZE,
                offset=next_offset,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )
            stop_scrolling = next_offset is None or (
                isinstance(next_offset, grpc.PointId)
                and getattr(next_offset, "num", 0) == 0
                and getattr(next_offset, "uuid", "") == ""
            )
            results.extend(points)

        return results

    def _get_existing_document_ids(self) -> Set[str]:
        try:
            points = self._scroll_all_points(with_payload=True, with_vectors=False)
            return {
                point.payload.get("doc_id", str(point.id))
                for point in points
                if point.payload
            }
        except Exception:
            return set()



    def _connect(self) -> None:
        client_kwargs = {"location": self.location}
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        self.client = QdrantClient(**client_kwargs)

        self._ensure_collection_exists()


    def _get_embedding(self, text: str) -> List[float]:
        return self.embedding_model.embed_query(text=text.strip())



    def query_relevant_documents(
            self, query: str, resources: Optional[List[Resource]] = None
        ) -> List[Dict[str, Any]]:
            resources = resources or []
            if not self.client:
                self._connect()

            # 1. 生成查询向量
            query_embedding = self._get_embedding(query)

            # 2. 构建过滤条件 (Pre-filtering)
            # 如果传入了 resources，则构建 doc_id 的过滤逻辑
            qdrant_filter = None
            if resources:
                should_conditions = []
                for resource in resources:
                    if resource.doc_id:
                        should_conditions.append(
                            FieldCondition(
                                key="doc_id", 
                                match=MatchValue(value=resource.doc_id)
                            )
                        )
                # 使用 should (OR 逻辑)：只要匹配其中一个 doc_id 即可
                if should_conditions:
                    qdrant_filter = Filter(should=should_conditions)

            # 3. 执行融合搜索 (Fusion Search)
            # 同时在 content_vec 和 problem_vec 中搜索，并应用过滤条件
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                # 定义预搜索 (Prefetch)：分别在两个向量空间并行搜索
                prefetch=[
                    Prefetch(
                        query=query_embedding,
                        using="content_vec",  # 搜内容
                        filter=qdrant_filter, # 应用 doc_id 过滤
                        limit=self.top_k,
                    ),
                    Prefetch(
                        query=query_embedding,
                        using="problem_vec",  # 搜生成的问题
                        filter=qdrant_filter, # 应用 doc_id 过滤
                        limit=self.top_k,
                    ),
                ],
                # 使用 RRF (Reciprocal Rank Fusion) 算法融合两边的排名
                query=FusionQuery(fusion=Fusion.RRF),
                limit=self.top_k,
                with_payload=True,
                query_filter=qdrant_filter,
            ).points

            # 4. 处理结果格式
            results_list = []

            for hit in search_results:
                payload = hit.payload or {}
                
                # 移除不需要的 'generate_problem' (即你说的 question)
                # 使用 pop 安全删除，如果不存在也不会报错
                payload.pop("generate_problem", None)
                
                # 也可以顺便把内部的 vector 结构移除（虽然 query_points 默认不返回 vector 数据）
                # 如果需要保留 score 供参考，也可以加进去，例如 payload['_score'] = hit.score

                results_list.append(payload)

            return results_list

    def create_collection(self) -> None:
        if not self.client:
            self._connect()
        else:
            self._ensure_collection_exists()




    def create_index(self, field_name: Optional[str] = None, field_schema=None) -> None:
        if not self.client:
            self._connect()
        try:
            if not field_schema:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="doc_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )

            else:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_schema,
                )
        except Exception as e:
            logger.warning("Error creating index: %s", e)

    # 1. 删除整个集合 (慎用)
    def drop_collection(self) -> None:
        """
        彻底删除当前集合及其所有数据。
        """
        try:
            self.client.delete_collection(self.collection_name)
            # logger.info(f"Collection {self.collection_name} successfully deleted.")
            print(f"Collection {self.collection_name} successfully deleted.")
        except Exception as e:
            # logger.error(f"Error deleting collection: {e}")
            print(f"Error deleting collection: {e}")

    # 2. 删除特定文档 Payload 中的特定字段
    def delete_payload_keys(self, doc_ids: List[str], keys: List[str]) -> None:
        """
        仅删除指定文档中的特定字段 (例如：只删除 'generate_problem' 字段，但保留 content 和向量)。
        
        Args:
            doc_ids: 文档 ID 列表
            keys: 要删除的字段名列表，例如 ["generate_problem", "title"]
        """
        try:
            # 将 doc_id 转换为实际存储的 point_id (UUID)
            points = [self._string_to_uuid(did) for did in doc_ids]
            
            self.client.delete_payload(
                collection_name=self.collection_name,
                keys=keys,
                points=points
            )
            print(f"Deleted keys {keys} from {len(points)} documents.")
        except Exception as e:
            print(f"Error deleting payload keys: {e}")

    # 3. 删除特定的文档 (整行删除)
    def delete_documents(self, doc_ids: List[str]) -> None:
        """
        根据 ID 删除整条记录（包含向量、Payload 所有内容）。
        """
        try:
            # 将 doc_id 转换为实际存储的 point_id (UUID)
            points = [self._string_to_uuid(did) for did in doc_ids]
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=points)
            )
            print(f"Successfully deleted {len(points)} documents.")
        except Exception as e:
            print(f"Error deleting documents: {e}")


    def close(self) -> None:
        if hasattr(self, "client") and self.client:
            try:
                if hasattr(self.client, "close"):
                    self.client.close()
                self.client = None
                self.vector_store = None
            except Exception as e:
                logger.warning("发生异常 while closing QdrantProvider: %s", e)

    def __del__(self) -> None:
        self.close()