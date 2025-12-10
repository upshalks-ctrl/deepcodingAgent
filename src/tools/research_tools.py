"""
Research coordination and execution tools
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.tools import BaseTool


class RequestResearchTool(BaseTool):
    """Request research on a specific topic"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "request_research",
                "description": "Request research on a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Research topic"},
                        "research_focus": {"type": "string", "description": "Specific focus areas"},
                        "requirements": {"type": "array", "items": {"type": "string"}, "description": "Research requirements"},
                        "round": {"type": "integer", "description": "Research round number"}
                    },
                    "required": ["topic", "research_focus", "requirements"]
                }
            }
        }

    def execute(self, topic: str, research_focus: str,
                requirements: List[str], round: int = 1) -> Dict[str, Any]:
        """Execute research request"""
        request_id = str(uuid.uuid4())

        request = {
            "id": request_id,
            "topic": topic,
            "research_focus": research_focus,
            "requirements": requirements,
            "round": round,
            "status": "requested",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "request": request,
            "message": f"Research request created for topic: {topic}"
        }


class AssignSearchTaskTool(BaseTool):
    """Assign search task to searcher"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "assign_search_task",
                "description": "Assign a search task to the searcher",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "Focus areas"},
                        "search_depth": {"type": "string", "enum": ["basic", "comprehensive"], "description": "Search depth"}
                    },
                    "required": ["query", "focus_areas"]
                }
            }
        }

    def execute(self, query: str, focus_areas: List[str],
                search_depth: str = "comprehensive") -> Dict[str, Any]:
        """Execute search task assignment"""
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "type": "search",
            "query": query,
            "focus_areas": focus_areas,
            "search_depth": search_depth,
            "assignee": "searcher",
            "status": "assigned",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "task": task,
            "message": f"Search task assigned with query: {query}"
        }


class AssignAnalysisTaskTool(BaseTool):
    """Assign analysis task to analyzer"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "assign_analysis_task",
                "description": "Assign an analysis task to the analyzer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "solutions": {"type": "array", "items": {"type": "string"}, "description": "Solutions to analyze"},
                        "criteria": {"type": "array", "items": {"type": "string"}, "description": "Analysis criteria"},
                        "analysis_type": {"type": "string", "description": "Type of analysis"}
                    },
                    "required": ["solutions", "criteria"]
                }
            }
        }

    def execute(self, solutions: List[str], criteria: List[str],
                analysis_type: Optional[str] = None) -> Dict[str, Any]:
        """Execute analysis task assignment"""
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "type": "analysis",
            "solutions": solutions,
            "criteria": criteria,
            "analysis_type": analysis_type or "technical",
            "assignee": "analyzer",
            "status": "assigned",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "task": task,
            "message": f"Analysis task assigned for {len(solutions)} solutions"
        }


class AssignResearchTaskTool(BaseTool):
    """Assign deep research task to researcher"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "assign_research_task",
                "description": "Assign a deep research task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Research topic"},
                        "depth": {"type": "string", "enum": ["shallow", "medium", "deep"], "description": "Research depth"},
                        "aspects": {"type": "array", "items": {"type": "string"}, "description": "Research aspects"}
                    },
                    "required": ["topic", "depth", "aspects"]
                }
            }
        }

    def execute(self, topic: str, depth: str, aspects: List[str]) -> Dict[str, Any]:
        """Execute research task assignment"""
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "type": "research",
            "topic": topic,
            "depth": depth,
            "aspects": aspects,
            "assignee": "researcher",
            "status": "assigned",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "task": task,
            "message": f"Deep research task assigned for topic: {topic}"
        }


class SynthesizeFindingsTool(BaseTool):
    """Synthesize research findings"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "synthesize_findings",
                "description": "Synthesize research findings from multiple sources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "findings": {"type": "array", "items": {"type": "string"}, "description": "Research findings"},
                        "key_insights": {"type": "array", "items": {"type": "string"}, "description": "Key insights"},
                        "synthesis_type": {"type": "string", "description": "Type of synthesis"}
                    },
                    "required": ["findings", "key_insights"]
                }
            }
        }

    def execute(self, findings: List[str], key_insights: List[str],
                synthesis_type: Optional[str] = None) -> Dict[str, Any]:
        """Execute findings synthesis"""
        synthesis = {
            "id": str(uuid.uuid4()),
            "findings": findings,
            "key_insights": key_insights,
            "synthesis_type": synthesis_type or "comprehensive",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "synthesis": synthesis,
            "message": f"Synthesized {len(findings)} findings"
        }


class ReportCompletionTool(BaseTool):
    """Report research completion"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "report_completion",
                "description": "Report research completion with summary",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "research_summary": {"type": "string", "description": "Research summary"},
                        "recommendations": {"type": "array", "items": {"type": "string"}, "description": "Recommendations"},
                        "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Suggested next steps"}
                    },
                    "required": ["research_summary", "recommendations"]
                }
            }
        }

    def execute(self, research_summary: str, recommendations: List[str],
                next_steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute completion report"""
        report = {
            "id": str(uuid.uuid4()),
            "research_summary": research_summary,
            "recommendations": recommendations,
            "next_steps": next_steps or [],
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "report": report,
            "message": "Research completion report generated"
        }


class PlanNextRoundTool(BaseTool):
    """Plan next research round"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "plan_next_round",
                "description": "Plan the next round of research",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "next_steps": {"type": "string", "description": "Next steps description"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "Focus areas for next round"}
                    },
                    "required": ["next_steps", "focus_areas"]
                }
            }
        }

    def execute(self, next_steps: str, focus_areas: List[str]) -> Dict[str, Any]:
        """Execute next round planning"""
        plan = {
            "id": str(uuid.uuid4()),
            "next_steps": next_steps,
            "focus_areas": focus_areas,
            "status": "planned",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "plan": plan,
            "message": f"Next round planned with {len(focus_areas)} focus areas"
        }