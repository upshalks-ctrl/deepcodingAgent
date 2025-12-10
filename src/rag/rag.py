import abc
from typing import Any, List, Optional, Dict

from pydantic import BaseModel, Field






class Resource(BaseModel):
    """
    Resource is a class that represents a resource.
    """
    doc_id: str = Field(..., description="The ID of the document associated with this resource")
    uri: str|None = Field(None, description="The URI of the resource")
    title: str | None = Field(None, description="The title of the resource")
    description: str | None = Field("", description="The description of the resource")


class BaseKVStorage(abc.ABC):

    @abc.abstractmethod
    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get value by id"""

    @abc.abstractmethod
    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get values by ids"""

    @abc.abstractmethod
    async def filter_keys(self, keys: set[str]) -> set[str]:
        """Return un-exist keys"""

    @abc.abstractmethod
    async def upsert(self, data: dict[str|Any, dict[str, Any]]) -> None:
        """Upsert data

        Importance notes for in-memory storage:
        1. Changes will be persisted to disk during the next index_done_callback
        2. update flags to notify other processes that data persistence is needed
        """

    @abc.abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete specific records from storage by their IDs

        Importance notes for in-memory storage:
        1. Changes will be persisted to disk during the next index_done_callback
        2. update flags to notify other processes that data persistence is needed

        Args:
            ids (list[str]): List of document IDs to be deleted from storage

        Returns:
            None
        """

    @abc.abstractmethod
    async def is_empty(self) -> bool:
        """Check if the storage is empty

        Returns:
            bool: True if storage contains no data, False otherwise
        """

class Retriever(abc.ABC):
    """
    Define a RAG provider, which can be used to query documents and resources.
    """

    @abc.abstractmethod
    def query_relevant_documents(
        self, query: str, resources: list[Resource] = []
    ) -> list[str]:
        """
        Query relevant documents from the resources.
        """
        pass
    @abc.abstractmethod
    def insert(self,documents: list[tuple[str,str]]) -> None:
        """
        Insert documents into the retriever.
        Each document is a tuple of (doc_id, content).
        """
        pass
    @abc.abstractmethod
    async def ainsert(self,documents: list[tuple[str,str]]) -> None:
        """
        Insert documents into the retriever asynchronously.
        Each document is a tuple of (doc_id, content).
        """
        pass

class Rag():
    @abc.abstractmethod
    def parse_document(self,
        file_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        cache_key: str|None = None,
        **kwargs,)->tuple[List[Dict[str, Any]], str]:
        """
        Parse a document and return a list of chunks and the title.
        Each chunk is a dict with keys: 'id', 'content', 'metadata'.
        """
        pass
    @abc.abstractmethod
    async def ainsert(self,
        folder_path: str,
        output_dir: str|None = None,
        parse_method: str|None = None,
        display_stats: bool|None = None,
        file_extensions: Optional[List[str]] = None,
        recursive: bool|None = None,
        max_workers: int|None = None,
        **kwargs,):
        """
        Insert all documents in to db asynchronously.
        """
        pass
    @abc.abstractmethod
    async def aquery(self, query: str, resources: list[Resource] = []) -> list[str]:
        """
        Query relevant documents from the resources asynchronously.
        """
        pass