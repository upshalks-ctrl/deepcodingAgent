"""
Search tools for agents
"""

import os
import re
import json
from typing import Any, Dict, Optional, List
from pathlib import Path

# Import the existing search functionality from parent directory
from ..search import get_web_search_tool


class WebSearchTool:
    """Tool for web searching"""

    name = "web_search"
    description = "Search the web for information"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": WebSearchTool.name,
                "description": WebSearchTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    @staticmethod
    async def execute(query: str, max_results: int = 10) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Use the existing search functionality
            search_tool = get_web_search_tool(max_results)

            # The tool might be sync, so handle both cases
            import inspect
            if inspect.iscoroutinefunction(search_tool.execute):
                results = await search_tool.execute(query)
            else:
                results = search_tool.execute(query)

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results) if isinstance(results, list) else 1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


class CodeSearchTool:
    """Tool for searching code files"""

    name = "code_search"
    description = "Search for patterns in code files"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": CodeSearchTool.name,
                "description": CodeSearchTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to search for (supports regex)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Path to search in (default: current directory)",
                            "default": "."
                        },
                        "extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File extensions to search (default: ['.py'])",
                            "default": [".py"]
                        }
                    },
                    "required": ["pattern"]
                }
            }
        }

    @staticmethod
    async def execute(pattern: str, path: str = ".", extensions: List[str] = None) -> Dict[str, Any]:
        """Execute the tool"""
        if extensions is None:
            extensions = [".py"]

        try:
            results = []
            pattern_regex = re.compile(pattern, re.IGNORECASE)

            for root, dirs, files in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                                # Search for matches
                                matches = []
                                for i, line in enumerate(content.split('\n'), 1):
                                    if pattern_regex.search(line):
                                        matches.append({
                                            "line": i,
                                            "content": line.strip()
                                        })

                                if matches:
                                    results.append({
                                        "file": filepath,
                                        "matches": matches
                                    })
                        except Exception as e:
                            # Skip files that can't be read
                            continue

            return {
                "success": True,
                "pattern": pattern,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pattern": pattern
            }


class DocumentSearchTool:
    """Tool for searching within documents"""

    name = "document_search"
    description = "Search within document files (pdf, docx, etc.)"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": DocumentSearchTool.name,
                "description": DocumentSearchTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "path": {
                            "type": "string",
                            "description": "Path to search in (default: current directory)",
                            "default": "."
                        },
                        "file_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File types to search (default: ['pdf', 'docx', 'txt'])",
                            "default": ["pdf", "docx", "txt"]
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    @staticmethod
    async def execute(query: str, path: str = ".", file_types: List[str] = None) -> Dict[str, Any]:
        """Execute the tool"""
        if file_types is None:
            file_types = ["pdf", "docx", "txt"]

        try:
            results = []
            path_obj = Path(path)

            # Find documents
            for file_type in file_types:
                for filepath in path_obj.rglob(f"*.{file_type}"):
                    try:
                        # For now, just return file path
                        # In real implementation, you would extract and search content
                        results.append({
                            "file": str(filepath),
                            "type": file_type,
                            "status": "Found file"
                        })
                    except Exception as e:
                        continue

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }