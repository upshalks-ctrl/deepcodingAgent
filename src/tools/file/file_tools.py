"""
File manipulation tools for agents
"""

import os
import json
from typing import Any, Dict, Optional, List
from pathlib import Path


class WriteFileTool:
    """Tool for writing content to files"""

    name = "write_file"
    description = "Write content to a file"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": WriteFileTool.name,
                "description": WriteFileTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["filepath", "content"]
                }
            }
        }

    @staticmethod
    async def execute(filepath: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(filepath)
            if dir_path:  # Only create if there's a directory path
                os.makedirs(dir_path, exist_ok=True)

            # Write file
            with open(filepath, "w", encoding=encoding) as f:
                f.write(content)

            return {
                "success": True,
                "message": f"Successfully wrote {len(content)} characters to {filepath}",
                "filepath": filepath,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }


class ReadFileTool:
    """Tool for reading content from files"""

    name = "read_file"
    description = "Read content from a file"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": ReadFileTool.name,
                "description": ReadFileTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["filepath"]
                }
            }
        }

    @staticmethod
    async def execute(filepath: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Read file
            with open(filepath, "r", encoding=encoding) as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "filepath": filepath,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }


class EditFileTool:
    """Tool for editing content in files"""

    name = "edit_file"
    description = "Edit content in a file by replacing old content with new content"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": EditFileTool.name,
                "description": EditFileTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the file to edit"
                        },
                        "old_content": {
                            "type": "string",
                            "description": "Content to replace"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "New content to insert"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["filepath", "old_content", "new_content"]
                }
            }
        }

    @staticmethod
    async def execute(filepath: str, old_content: str, new_content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Read existing content
            with open(filepath, "r", encoding=encoding) as f:
                content = f.read()

            # Replace content
            if old_content in content:
                new_file_content = content.replace(old_content, new_content)

                # Write back
                with open(filepath, "w", encoding=encoding) as f:
                    f.write(new_file_content)

                return {
                    "success": True,
                    "message": f"Successfully replaced content in {filepath}",
                    "filepath": filepath,
                    "replacements": content.count(old_content)
                }
            else:
                return {
                    "success": False,
                    "error": f"Old content not found in {filepath}",
                    "filepath": filepath
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }


class ListFilesTool:
    """Tool for listing files in a directory"""

    name = "list_files"
    description = "List files and directories in a path"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": ListFilesTool.name,
                "description": ListFilesTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (default: current directory)",
                            "default": "."
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Pattern to match files (e.g., *.py)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "List files recursively",
                            "default": False
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    async def execute(path: str = ".", pattern: Optional[str] = None, recursive: bool = False) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            path_obj = Path(path)

            if recursive:
                if pattern:
                    files = list(path_obj.rglob(pattern))
                else:
                    files = list(path_obj.rglob("*"))
            else:
                if pattern:
                    files = list(path_obj.glob(pattern))
                else:
                    files = list(path_obj.iterdir())

            # Separate files and directories
            file_list = []
            dir_list = []

            for item in files:
                if item.is_file():
                    file_list.append(str(item))
                elif item.is_dir():
                    dir_list.append(str(item))

            return {
                "success": True,
                "files": file_list,
                "directories": dir_list,
                "path": str(path_obj.absolute())
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }


class AddImportsTool:
    """Tool for adding imports to Python files"""

    name = "add_imports"
    description = "Add import statements to Python files"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": AddImportsTool.name,
                "description": AddImportsTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the Python file"
                        },
                        "imports": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of import statements to add"
                        },
                        "position": {
                            "type": "string",
                            "enum": ["top", "after_existing"],
                            "description": "Where to add imports (default: after_existing)",
                            "default": "after_existing"
                        }
                    },
                    "required": ["filepath", "imports"]
                }
            }
        }

    @staticmethod
    async def execute(filepath: str, imports: List[str], position: str = "after_existing") -> Dict[str, Any]:
        """Execute the tool"""
        try:
            path = Path(filepath)

            # Check if file exists
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {filepath}"
                }

            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Parse existing imports
            import_lines = set()
            import_end_idx = 0

            for i, line in enumerate(lines):
                stripped = line.strip()
                # Check for import statements
                if stripped.startswith(('import ', 'from ')):
                    import_lines.add(stripped)
                    import_end_idx = i + 1
                elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    # Stop at first non-import, non-comment line
                    break

            # Filter out already existing imports
            new_imports = []
            for imp in imports:
                if imp.strip() not in import_lines:
                    new_imports.append(imp.strip())

            if not new_imports:
                return {
                    "success": True,
                    "message": "All imports already exist in file",
                    "added_imports": []
                }

            # Insert imports
            if position == "top" or import_end_idx == 0:
                # Add at the top
                insert_idx = 0
            else:
                # Add after existing imports
                insert_idx = import_end_idx

            # Ensure proper spacing
            for imp in new_imports:
                lines.insert(insert_idx, imp + '\n')
                insert_idx += 1

            # Add a blank line after imports if needed
            if insert_idx < len(lines) and lines[insert_idx].strip() != '':
                lines.insert(insert_idx, '\n')

            # Write back to file
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return {
                "success": True,
                "message": f"Added {len(new_imports)} import(s) to {filepath}",
                "added_imports": new_imports
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }