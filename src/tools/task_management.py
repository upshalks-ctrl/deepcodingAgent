"""
Task management tools for coordinating and tracking tasks
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.tools import BaseTool


class CreateTaskTool(BaseTool):
    """Create a new task"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_task",
                "description": "Create a new task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "assignee": {"type": "string", "description": "Task assignee"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Task priority"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Task tags"}
                    },
                    "required": ["title", "description"]
                }
            }
        }

    def execute(self, title: str, description: str, assignee: Optional[str] = None,
                priority: str = "medium", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute task creation"""
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "assignee": assignee,
            "priority": priority,
            "status": "pending",
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created with ID: {task_id}"
        }


class AssignTaskTool(BaseTool):
    """Assign a task to a team member"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "assign_task",
                "description": "Assign a task to a team member",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "assignee": {"type": "string", "description": "Assignee name"},
                        "notes": {"type": "string", "description": "Assignment notes"}
                    },
                    "required": ["task_id", "assignee"]
                }
            }
        }

    def execute(self, task_id: str, assignee: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Execute task assignment"""
        return {
            "success": True,
            "task_id": task_id,
            "assignee": assignee,
            "notes": notes,
            "message": f"Task {task_id} assigned to {assignee}"
        }


class UpdateTaskStatusTool(BaseTool):
    """Update task status"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "update_task_status",
                "description": "Update the status of a task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"], "description": "New status"},
                        "notes": {"type": "string", "description": "Status update notes"}
                    },
                    "required": ["task_id", "status"]
                }
            }
        }

    def execute(self, task_id: str, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Execute status update"""
        return {
            "success": True,
            "task_id": task_id,
            "status": status,
            "notes": notes,
            "updated_at": datetime.now().isoformat(),
            "message": f"Task {task_id} status updated to {status}"
        }


class CreateCodingPlanTool(BaseTool):
    """Create a coding plan with multiple tasks"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_coding_plan",
                "description": "Create a coding plan with tasks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan_title": {"type": "string", "description": "Plan title"},
                        "architecture_summary": {"type": "string", "description": "Architecture summary"},
                        "tasks": {"type": "array", "items": {"type": "object"}, "description": "List of tasks"}
                    },
                    "required": ["plan_title", "architecture_summary", "tasks"]
                }
            }
        }

    def execute(self, plan_title: str, architecture_summary: str,
                tasks: List[Dict]) -> Dict[str, Any]:
        """Execute coding plan creation"""
        plan_id = str(uuid.uuid4())

        plan = {
            "id": plan_id,
            "title": plan_title,
            "architecture_summary": architecture_summary,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "plan": plan,
            "message": f"Coding plan created with {len(tasks)} tasks"
        }


class GenerateProgressReportTool(BaseTool):
    """Generate a progress report for tasks"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "generate_progress_report",
                "description": "Generate a progress report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_ids": {"type": "array", "items": {"type": "string"}, "description": "List of task IDs"},
                        "include_details": {"type": "boolean", "description": "Include detailed task information"}
                    }
                }
            }
        }

    def execute(self, task_ids: Optional[List[str]] = None,
                include_details: bool = True) -> Dict[str, Any]:
        """Execute progress report generation"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0
            },
            "tasks": []
        }

        return {
            "success": True,
            "report": report,
            "message": "Progress report generated"
        }


class CreateTaskListTool(BaseTool):
    """Create a todo list"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_task_list",
                "description": "Create a task list or todo list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "List title"},
                        "tasks": {"type": "array", "items": {"type": "object"}, "description": "List of tasks"},
                        "category": {"type": "string", "description": "Task category"}
                    },
                    "required": ["title", "tasks"]
                }
            }
        }

    def execute(self, title: str, tasks: List[Dict],
                category: Optional[str] = None) -> Dict[str, Any]:
        """Execute task list creation"""
        task_list = {
            "id": str(uuid.uuid4()),
            "title": title,
            "category": category,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "task_list": task_list,
            "message": f"Task list '{title}' created with {len(tasks)} tasks"
        }