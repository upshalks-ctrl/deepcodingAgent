# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import abc

from pydantic import BaseModel, Field






class Resource(BaseModel):
    """
    Resource is a class that represents a resource.
    """
    doc_id: str = Field(..., description="The ID of the document associated with this resource")
    uri: str|None = Field(None, description="The URI of the resource")
    title: str | None = Field(None, description="The title of the resource")
    description: str | None = Field("", description="The description of the resource")
    user_id: str | None = Field(None, description="The ID of the user associated with this resource")
    conversation_id: str | None = Field(None, description="The ID of the conversation session")


class Retriever(abc.ABC):
    """
    Define a RAG provider, which can be used to query documents and resources.
    """

    @abc.abstractmethod
    def list_resources(self, query: str | None = None) -> list[Resource]:
        """
        List resources from the rag provider.
        """
        pass

    @abc.abstractmethod
    def query_relevant_documents(
        self, query: str, resources: list[Resource] = []
    ) -> list[str]:
        """
        Query relevant documents from the resources.
        """
        pass