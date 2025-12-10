"""
Todo list management tools for code coordination
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TodoItem:
    """Todo item structure"""
    id: str
    title: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    priority: str = "normal"  # low, normal, high, critical
    assignee: Optional[str] = None
    files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TodoList:
    """Todo list structure"""
    id: str
    title: str
    description: str
    items: List[TodoItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CreateTodoListTool:
    """Tool for creating a todo list"""

    name = "create_todo_list"
    description = "Create a structured todo list for code implementation"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": CreateTodoListTool.name,
                "description": CreateTodoListTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the todo list"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the todo list"
                        },
                        "items": {
                            "type": "array",
                            "description": "List of todo items",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
                                    "files": {"type": "array", "items": {"type": "string"}},
                                    "dependencies": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["title", "description"]
                            }
                        }
                    },
                    "required": ["title", "description", "items"]
                }
            }
        }

    @staticmethod
    async def execute(
        title: str,
        description: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Create todo list
            todo_list = TodoList(
                id=f"todo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=title,
                description=description
            )

            # Add items
            for i, item_data in enumerate(items):
                todo_item = TodoItem(
                    id=f"item_{i+1}",
                    title=item_data.get("title", ""),
                    description=item_data.get("description", ""),
                    priority=item_data.get("priority", "normal"),
                    files=item_data.get("files", []),
                    dependencies=item_data.get("dependencies", [])
                )
                todo_list.items.append(todo_item)

            # Save to file
            os.makedirs("todo_lists", exist_ok=True)
            filename = f"todo_lists/{todo_list.id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "id": todo_list.id,
                    "title": todo_list.title,
                    "description": todo_list.description,
                    "items": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "description": item.description,
                            "status": item.status,
                            "priority": item.priority,
                            "files": item.files,
                            "dependencies": item.dependencies,
                            "created_at": item.created_at,
                            "updated_at": item.updated_at
                        }
                        for item in todo_list.items
                    ],
                    "created_at": todo_list.created_at,
                    "updated_at": todo_list.updated_at
                }, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "todo_list_id": todo_list.id,
                "title": title,
                "items_count": len(items),
                "file": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class UpdateTodoTool:
    """Tool for updating todo items"""

    name = "update_todo"
    description = "Update status of a todo item"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": UpdateTodoTool.name,
                "description": UpdateTodoTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "todo_list_id": {
                            "type": "string",
                            "description": "ID of the todo list"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "ID of the todo item"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "blocked"],
                            "description": "New status for the item"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional notes about the update"
                        }
                    },
                    "required": ["todo_list_id", "item_id", "status"]
                }
            }
        }

    @staticmethod
    async def execute(
        todo_list_id: str,
        item_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Load todo list
            filename = f"todo_lists/{todo_list_id}.json"
            with open(filename, 'r', encoding='utf-8') as f:
                todo_data = json.load(f)

            # Find and update item
            updated = False
            for item in todo_data["items"]:
                if item["id"] == item_id:
                    item["status"] = status
                    item["updated_at"] = datetime.now().isoformat()
                    if notes:
                        item["notes"] = notes
                    updated = True
                    break

            if not updated:
                return {
                    "success": False,
                    "error": f"Item {item_id} not found in todo list {todo_list_id}"
                }

            # Save updated list
            todo_data["updated_at"] = datetime.now().isoformat()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(todo_data, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "item_id": item_id,
                "new_status": status,
                "message": f"Updated item {item_id} to {status}"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Todo list {todo_list_id} not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetTodoListTool:
    """Tool for retrieving todo list status"""

    name = "get_todo_list"
    description = "Get current status of a todo list"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the tool schema"""
        return {
            "type": "function",
            "function": {
                "name": GetTodoListTool.name,
                "description": GetTodoListTool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "todo_list_id": {
                            "type": "string",
                            "description": "ID of the todo list"
                        },
                        "filter": {
                            "type": "string",
                            "enum": ["all", "pending", "in_progress", "completed", "blocked"],
                            "description": "Filter items by status (default: all)",
                            "default": "all"
                        }
                    },
                    "required": ["todo_list_id"]
                }
            }
        }

    @staticmethod
    async def execute(
        todo_list_id: str,
        filter: str = "all"
    ) -> Dict[str, Any]:
        """Execute the tool"""
        try:
            # Load todo list
            filename = f"todo_lists/{todo_list_id}.json"
            with open(filename, 'r', encoding='utf-8') as f:
                todo_data = json.load(f)

            # Filter items if needed
            items = todo_data["items"]
            if filter != "all":
                items = [item for item in items if item["status"] == filter]

            # Count statuses
            status_counts = {}
            for item in todo_data["items"]:
                status = item["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            # Generate summary
            summary = f"""
Todo List: {todo_data['title']}
Total items: {len(todo_data['items'])}
Status: {status_counts}
"""

            if items:
                summary += "\n\nItems:\n"
                for item in items:
                    priority_symbol = {"low": "↓", "normal": "○", "high": "↑", "critical": "!"}[item.get("priority", "normal")]
                    summary += f"\n{priority_symbol} [{item['status'].upper()}] {item['title']}"
                    if item.get("files"):
                        summary += f" (Files: {', '.join(item['files'])})"

            return {
                "success": True,
                "todo_list": {
                    "id": todo_data["id"],
                    "title": todo_data["title"],
                    "summary": summary.strip(),
                    "items": items,
                    "status_counts": status_counts,
                    "total_items": len(todo_data["items"])
                }
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Todo list {todo_list_id} not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }