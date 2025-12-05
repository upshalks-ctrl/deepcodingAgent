from src.config.tools import SELECTED_RAG_PROVIDER, RAGProvider
from src.rag.enhanced_qdrant import EnhancedQdrantRetriever
from src.rag.retriever import Retriever


def build_retriever() -> Retriever | None:
    if SELECTED_RAG_PROVIDER == RAGProvider.QDRANT.value:
        return EnhancedQdrantRetriever()
    return None