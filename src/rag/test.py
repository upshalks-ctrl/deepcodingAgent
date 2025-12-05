import os
from pathlib import Path

from src.rag import QdrantProvider

if __name__ == '__main__':
  qdrant_client = QdrantProvider()
  qdrant_client.create_index("source","keyword")
