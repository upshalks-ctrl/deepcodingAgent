from src.config.tools import SELECTED_RAG_PROVIDER, RAGProvider
from src.rag.rag import Retriever
from src.rag.qdrant import QdrantRetriever


def build_retriever() -> Retriever | None:
    if SELECTED_RAG_PROVIDER == RAGProvider.QDRANT.value:
        return QdrantRetriever()
    return None