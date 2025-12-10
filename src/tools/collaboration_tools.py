"""
Team collaboration and coordination tools
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.tools import BaseTool


class TaskAssignmentTool(BaseTool):
    """Assign tasks to team members with proper coordination"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "coordinate_task_assignment",
                "description": "Coordinate task assignment to team members",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task identifier"},
                        "assignee": {"type": "string", "description": "Team member to assign to"},
                        "assignment_reason": {"type": "string", "description": "Reason for assignment"},
                        "deadline": {"type": "string", "description": "Task deadline"},
                        "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Task dependencies"}
                    },
                    "required": ["task_id", "assignee"]
                }
            }
        }

    def execute(self, task_id: str, assignee: str,
                assignment_reason: Optional[str] = None,
                deadline: Optional[str] = None,
                dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute task assignment coordination"""
        assignment_id = str(uuid.uuid4())

        assignment = {
            "id": assignment_id,
            "task_id": task_id,
            "assignee": assignee,
            "assignment_reason": assignment_reason or "Skill-based assignment",
            "deadline": deadline,
            "dependencies": dependencies or [],
            "status": "assigned",
            "assigned_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "assignment": assignment,
            "message": f"Task {task_id} assigned to {assignee}"
        }


class TeamCoordinationTool(BaseTool):
    """Coordinate team activities and workflows"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "coordinate_team_activities",
                "description": "Coordinate team activities and workflows",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activity_type": {"type": "string", "description": "Type of activity"},
                        "participants": {"type": "array", "items": {"type": "string"}, "description": "Team participants"},
                        "schedule": {"type": "string", "description": "Activity schedule"},
                        "objectives": {"type": "array", "items": {"type": "string"}, "description": "Activity objectives"}
                    },
                    "required": ["activity_type", "participants"]
                }
            }
        }

    def execute(self, activity_type: str, participants: List[str],
                schedule: Optional[str] = None,
                objectives: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute team coordination"""
        coordination_id = str(uuid.uuid4())

        coordination = {
            "id": coordination_id,
            "activity_type": activity_type,
            "participants": participants,
            "schedule": schedule or "Immediate",
            "objectives": objectives or [],
            "status": "coordinated",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "coordination": coordination,
            "message": f"Coordinated {activity_type} for {len(participants)} participants"
        }


class ApprovalRequestTool(BaseTool):
    """Request approvals for various items"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "request_approval",
                "description": "Request approval for an item",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "Item to approve"},
                        "item_type": {"type": "string", "description": "Type of item"},
                        "approver": {"type": "string", "description": "Approver"},
                        "justification": {"type": "string", "description": "Approval justification"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Approval urgency"}
                    },
                    "required": ["item_id", "item_type", "approver"]
                }
            }
        }

    def execute(self, item_id: str, item_type: str, approver: str,
                justification: Optional[str] = None,
                urgency: str = "medium") -> Dict[str, Any]:
        """Execute approval request"""
        request_id = str(uuid.uuid4())

        approval_request = {
            "id": request_id,
            "item_id": item_id,
            "item_type": item_type,
            "approver": approver,
            "justification": justification or "Standard approval required",
            "urgency": urgency,
            "status": "pending",
            "requested_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "approval_request": approval_request,
            "message": f"Approval requested for {item_type} {item_id}"
        }


class ReviewRequestTool(BaseTool):
    """Request code or document reviews"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "request_review",
                "description": "Request a review for code or documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_path": {"type": "string", "description": "Path to item to review"},
                        "review_type": {"type": "string", "description": "Type of review required"},
                        "reviewers": {"type": "array", "items": {"type": "string"}, "description": "List of reviewers"},
                        "checklist": {"type": "array", "items": {"type": "string"}, "description": "Review checklist"},
                        "deadline": {"type": "string", "description": "Review deadline"}
                    },
                    "required": ["item_path", "review_type", "reviewers"]
                }
            }
        }

    def execute(self, item_path: str, review_type: str, reviewers: List[str],
                checklist: Optional[List[str]] = None,
                deadline: Optional[str] = None) -> Dict[str, Any]:
        """Execute review request"""
        review_id = str(uuid.uuid4())

        review_request = {
            "id": review_id,
            "item_path": item_path,
            "review_type": review_type,
            "reviewers": reviewers,
            "checklist": checklist or [],
            "deadline": deadline,
            "status": "requested",
            "requested_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "review_request": review_request,
            "message": f"Review requested for {item_path}"
        }


class CoordinateTestingTool(BaseTool):
    """Coordinate testing activities across the team"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "coordinate_testing",
                "description": "Coordinate testing activities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_scope": {"type": "string", "description": "Scope of testing"},
                        "test_type": {"type": "string", "description": "Type of testing"},
                        "testers": {"type": "array", "items": {"type": "string"}, "description": "Assigned testers"},
                        "test_plan": {"type": "string", "description": "Test plan reference"},
                        "environment": {"type": "string", "description": "Test environment"}
                    },
                    "required": ["test_scope", "test_type", "testers"]
                }
            }
        }

    def execute(self, test_scope: str, test_type: str, testers: List[str],
                test_plan: Optional[str] = None,
                environment: Optional[str] = None) -> Dict[str, Any]:
        """Execute testing coordination"""
        coordination_id = str(uuid.uuid4())

        testing_coordination = {
            "id": coordination_id,
            "test_scope": test_scope,
            "test_type": test_type,
            "testers": testers,
            "test_plan": test_plan,
            "environment": environment or "staging",
            "status": "coordinated",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "testing_coordination": testing_coordination,
            "message": f"Coordinated {test_type} testing for {test_scope}"
        }


class MakeDecisionTool(BaseTool):
    """Make and document decisions"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "make_decision",
                "description": "Make and document a decision",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string", "description": "Type of task decision"},
                        "reasoning": {"type": "string", "description": "Decision reasoning"},
                        "next_phase_input": {"type": "object", "description": "Input for next phase"},
                        "complexity": {"type": "string", "description": "Task complexity"}
                    },
                    "required": ["task_type", "reasoning", "complexity"]
                }
            }
        }

    def execute(self, task_type: str, reasoning: str,
                next_phase_input: Optional[Dict] = None,
                complexity: str = "medium") -> Dict[str, Any]:
        """Execute decision making"""
        decision_id = str(uuid.uuid4())

        decision = {
            "id": decision_id,
            "task_type": task_type,
            "reasoning": reasoning,
            "next_phase_input": next_phase_input or {},
            "complexity": complexity,
            "made_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "decision": decision,
            "message": f"Decision made: {task_type} (complexity: {complexity})"
        }


class SynthesizeResultsTool(BaseTool):
    """Synthesize results from multiple sources"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "synthesize_results",
                "description": "Synthesize results from multiple sources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sources": {"type": "array", "items": {"type": "object"}, "description": "Source data"},
                        "synthesis_type": {"type": "string", "description": "Type of synthesis"},
                        "key_findings": {"type": "array", "items": {"type": "string"}, "description": "Key findings"},
                        "conclusions": {"type": "array", "items": {"type": "string"}, "description": "Conclusions"}
                    },
                    "required": ["sources", "synthesis_type"]
                }
            }
        }

    def execute(self, sources: List[Dict], synthesis_type: str,
                key_findings: Optional[List[str]] = None,
                conclusions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute results synthesis"""
        synthesis_id = str(uuid.uuid4())

        synthesis = {
            "id": synthesis_id,
            "sources": sources,
            "synthesis_type": synthesis_type,
            "key_findings": key_findings or [],
            "conclusions": conclusions or [],
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "synthesis": synthesis,
            "message": f"Synthesized {len(sources)} sources"
        }