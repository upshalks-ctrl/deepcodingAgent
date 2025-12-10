"""
Reporting and documentation tools
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.tools import BaseTool


class ReportGeneratorTool(BaseTool):
    """Generate various types of reports"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "generate_report",
                "description": "Generate a comprehensive report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["progress", "summary", "detailed", "executive"], "description": "Type of report"},
                        "data": {"type": "object", "description": "Report data"},
                        "format": {"type": "string", "enum": ["json", "markdown", "html"], "description": "Output format"},
                        "include_charts": {"type": "boolean", "description": "Include visualizations"}
                    },
                    "required": ["report_type", "data"]
                }
            }
        }

    def execute(self, report_type: str, data: Dict,
                format: str = "markdown",
                include_charts: bool = False) -> Dict[str, Any]:
        """Generate report"""
        report_id = str(uuid.uuid4())

        report = {
            "id": report_id,
            "type": report_type,
            "format": format,
            "generated_at": datetime.now().isoformat(),
            "data": data,
            "include_charts": include_charts,
            "content": self._generate_report_content(report_type, data, format)
        }

        return {
            "success": True,
            "report": report,
            "message": f"Generated {report_type} report in {format} format"
        }

    def _generate_report_content(self, report_type: str, data: Dict, format: str) -> str:
        """Generate report content based on type and format"""
        if format == "markdown":
            return self._generate_markdown_report(report_type, data)
        elif format == "json":
            return json.dumps(data, indent=2)
        else:
            return "Report content (HTML would go here)"

    def _generate_markdown_report(self, report_type: str, data: Dict) -> str:
        """Generate markdown report"""
        content = [f"# {report_type.title()} Report", ""]
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")

        # Add key sections based on report type
        if report_type == "progress":
            content.extend([
                "## Progress Summary",
                "- Total Tasks: " + str(data.get("total_tasks", 0)),
                "- Completed: " + str(data.get("completed", 0)),
                "- In Progress: " + str(data.get("in_progress", 0)),
                ""
            ])
        elif report_type == "summary":
            content.extend([
                "## Executive Summary",
                data.get("summary", "No summary provided"),
                ""
            ])

        return "\n".join(content)


class RetrospectiveTool(BaseTool):
    """Create team retrospectives"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_retrospective",
                "description": "Create a team retrospective",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "what_went_well": {"type": "array", "items": {"type": "string"}, "description": "Things that went well"},
                        "what_could_improve": {"type": "array", "items": {"type": "string"}, "description": "Areas for improvement"},
                        "action_items": {"type": "array", "items": {"type": "object"}, "description": "Action items"},
                        "participants": {"type": "array", "items": {"type": "string"}, "description": "Team members"},
                        "timeframe": {"type": "string", "description": "Retrospective timeframe"}
                    },
                    "required": ["what_went_well", "what_could_improve", "action_items"]
                }
            }
        }

    def execute(self, what_went_well: List[str], what_could_improve: List[str],
                action_items: List[Dict], participants: Optional[List[str]] = None,
                timeframe: Optional[str] = None) -> Dict[str, Any]:
        """Create retrospective"""
        retrospective_id = str(uuid.uuid4())

        retrospective = {
            "id": retrospective_id,
            "what_went_well": what_went_well,
            "what_could_improve": what_could_improve,
            "action_items": action_items,
            "participants": participants or [],
            "timeframe": timeframe or "Current Sprint",
            "created_at": datetime.now().isoformat(),
            "summary": {
                "positives_count": len(what_went_well),
                "improvements_count": len(what_could_improve),
                "action_items_count": len(action_items)
            }
        }

        return {
            "success": True,
            "retrospective": retrospective,
            "message": f"Created retrospective with {len(action_items)} action items"
        }


class ReflectionTool(BaseTool):
    """Record and process reflections"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "record_reflection",
                "description": "Record a reflection on work done",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reflection": {"type": "string", "description": "Reflection content"},
                        "aspects": {"type": "array", "items": {"type": "string"}, "description": "Aspects reflected on"},
                        "insights": {"type": "array", "items": {"type": "string"}, "description": "Key insights"},
                        "context": {"type": "string", "description": "Reflection context"}
                    },
                    "required": ["reflection", "aspects"]
                }
            }
        }

    def execute(self, reflection: str, aspects: List[str],
                insights: Optional[List[str]] = None,
                context: Optional[str] = None) -> Dict[str, Any]:
        """Record reflection"""
        reflection_id = str(uuid.uuid4())

        reflection_data = {
            "id": reflection_id,
            "reflection": reflection,
            "aspects": aspects,
            "insights": insights or [],
            "context": context or "General",
            "created_at": datetime.now().isoformat(),
            "sentiment": self._analyze_sentiment(reflection)
        }

        return {
            "success": True,
            "reflection": reflection_data,
            "message": "Reflection recorded successfully"
        }

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ["good", "great", "excellent", "success", "achieved", "completed"]
        negative_words = ["bad", "failed", "issue", "problem", "challenge", "difficult"]

        words = text.lower().split()
        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


class SuggestImprovementsTool(BaseTool):
    """Suggest improvements based on analysis"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "suggest_improvements",
                "description": "Suggest improvements based on analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "suggestions": {"type": "array", "items": {"type": "object"}, "description": "Improvement suggestions"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"},
                        "category": {"type": "string", "description": "Improvement category"}
                    },
                    "required": ["suggestions"]
                }
            }
        }

    def execute(self, suggestions: List[Dict],
                priority: str = "medium",
                category: Optional[str] = None) -> Dict[str, Any]:
        """Suggest improvements"""
        suggestion_id = str(uuid.uuid4())

        improvement_plan = {
            "id": suggestion_id,
            "suggestions": suggestions,
            "priority": priority,
            "category": category or "general",
            "total_suggestions": len(suggestions),
            "created_at": datetime.now().isoformat(),
            "implementation_plan": self._create_implementation_plan(suggestions)
        }

        return {
            "success": True,
            "improvement_plan": improvement_plan,
            "message": f"Generated {len(suggestions)} improvement suggestions"
        }

    def _create_implementation_plan(self, suggestions: List[Dict]) -> Dict:
        """Create implementation plan from suggestions"""
        return {
            "immediate_actions": [s for s in suggestions if s.get("effort", "medium") == "low"],
            "short_term_goals": [s for s in suggestions if s.get("effort", "medium") == "medium"],
            "long_term_initiatives": [s for s in suggestions if s.get("effort", "medium") == "high"]
        }


class CompleteTaskTool(BaseTool):
    """Complete a task with summary and lessons learned"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "complete_task",
                "description": "Mark a task as completed with summary",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "task_summary": {"type": "string", "description": "Task completion summary"},
                        "lessons_learned": {"type": "array", "items": {"type": "string"}, "description": "Lessons learned"},
                        "outcomes": {"type": "array", "items": {"type": "string"}, "description": "Task outcomes"},
                        "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Recommended next steps"}
                    },
                    "required": ["task_id", "task_summary"]
                }
            }
        }

    def execute(self, task_id: str, task_summary: str,
                lessons_learned: Optional[List[str]] = None,
                outcomes: Optional[List[str]] = None,
                next_steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Complete task"""
        completion_id = str(uuid.uuid4())

        completion = {
            "id": completion_id,
            "task_id": task_id,
            "summary": task_summary,
            "lessons_learned": lessons_learned or [],
            "outcomes": outcomes or [],
            "next_steps": next_steps or [],
            "completed_at": datetime.now().isoformat(),
            "status": "completed"
        }

        return {
            "success": True,
            "completion": completion,
            "message": f"Task {task_id} marked as completed"
        }


class GenerateTodosTool(BaseTool):
    """Generate actionable todo items"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "generate_todos",
                "description": "Generate actionable todo items",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "todos": {"type": "array", "items": {"type": "object"}, "description": "Todo items"},
                        "category": {"type": "string", "description": "Todo category"},
                        "assignee": {"type": "string", "description": "Todo assignee"},
                        "due_date": {"type": "string", "description": "Due date for todos"}
                    },
                    "required": ["todos"]
                }
            }
        }

    def execute(self, todos: List[Dict],
                category: Optional[str] = None,
                assignee: Optional[str] = None,
                due_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate todos"""
        todo_list_id = str(uuid.uuid4())

        todo_list = {
            "id": todo_list_id,
            "todos": todos,
            "category": category or "general",
            "assignee": assignee,
            "due_date": due_date,
            "total_todos": len(todos),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

        # Add metadata to each todo
        for todo in todos:
            todo["list_id"] = todo_list_id
            todo["status"] = todo.get("status", "pending")
            if "priority" not in todo:
                todo["priority"] = "medium"

        return {
            "success": True,
            "todo_list": todo_list,
            "message": f"Generated todo list with {len(todos)} items"
        }