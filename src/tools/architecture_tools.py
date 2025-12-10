"""
Architecture design and documentation tools
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.tools import BaseTool


class CreateArchitectureDiagramTool(BaseTool):
    """Create architecture diagram"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_architecture_diagram",
                "description": "Create an architecture diagram",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "components": {"type": "array", "items": {"type": "string"}, "description": "List of components"},
                        "relationships": {"type": "array", "items": {"type": "string"}, "description": "Component relationships"},
                        "diagram_type": {"type": "string", "description": "Type of diagram"},
                        "style": {"type": "string", "description": "Diagram style"}
                    },
                    "required": ["components"]
                }
            }
        }

    def execute(self, components: List[str],
                relationships: Optional[List[str]] = None,
                diagram_type: Optional[str] = None,
                style: Optional[str] = None) -> Dict[str, Any]:
        """Execute diagram creation"""
        diagram = {
            "id": str(uuid.uuid4()),
            "components": components,
            "relationships": relationships or [],
            "diagram_type": diagram_type or "component",
            "style": style or "modern",
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "diagram": diagram,
            "message": f"Created architecture diagram with {len(components)} components"
        }


class DocumentComponentTool(BaseTool):
    """Document component specifications"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "document_component",
                "description": "Document component specifications",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Component name"},
                        "description": {"type": "string", "description": "Component description"},
                        "responsibilities": {"type": "array", "items": {"type": "string"}, "description": "Component responsibilities"},
                        "interfaces": {"type": "array", "items": {"type": "object"}, "description": "Component interfaces"},
                        "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Component dependencies"}
                    },
                    "required": ["name", "description"]
                }
            }
        }

    def execute(self, name: str, description: str,
                responsibilities: Optional[List[str]] = None,
                interfaces: Optional[List[Dict]] = None,
                dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute component documentation"""
        documentation = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "responsibilities": responsibilities or [],
            "interfaces": interfaces or [],
            "dependencies": dependencies or [],
            "documented_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "documentation": documentation,
            "message": f"Documented component: {name}"
        }


class CreateImplementationRoadmapTool(BaseTool):
    """Create implementation roadmap"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "create_implementation_roadmap",
                "description": "Create an implementation roadmap",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phases": {"type": "array", "items": {"type": "object"}, "description": "Implementation phases"},
                        "timeline": {"type": "string", "description": "Timeline description"},
                        "milestones": {"type": "array", "items": {"type": "object"}, "description": "Key milestones"}
                    },
                    "required": ["phases"]
                }
            }
        }

    def execute(self, phases: List[Dict],
                timeline: Optional[str] = None,
                milestones: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Execute roadmap creation"""
        roadmap = {
            "id": str(uuid.uuid4()),
            "phases": phases,
            "timeline": timeline or "TBD",
            "milestones": milestones or [],
            "total_phases": len(phases),
            "created_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "roadmap": roadmap,
            "message": f"Created implementation roadmap with {len(phases)} phases"
        }


class AssessRisksTool(BaseTool):
    """Assess project risks"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "assess_risks",
                "description": "Assess project risks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "risks": {"type": "array", "items": {"type": "object"}, "description": "List of risks"},
                        "mitigation_strategies": {"type": "array", "items": {"type": "object"}, "description": "Mitigation strategies"}
                    },
                    "required": ["risks"]
                }
            }
        }

    def execute(self, risks: List[Dict],
                mitigation_strategies: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Execute risk assessment"""
        assessment = {
            "id": str(uuid.uuid4()),
            "risks": risks,
            "mitigation_strategies": mitigation_strategies or [],
            "risk_matrix": self._create_risk_matrix(risks),
            "assessed_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "assessment": assessment,
            "message": f"Assessed {len(risks)} risks"
        }

    def _create_risk_matrix(self, risks: List[Dict]) -> Dict:
        """Create risk matrix from risks"""
        high_risks = [r for r in risks if r.get("impact", "medium") == "high" or r.get("probability", "medium") == "high"]
        return {
            "high_risk_count": len(high_risks),
            "total_risks": len(risks),
            "categories": list(set(r.get("category", "general") for r in risks))
        }


class DecideArchitectureWritingTool(BaseTool):
    """Decide to start architecture writing"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "decide_architecture_writing",
                "description": "Decide to start architecture writing phase",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string", "description": "Reason for decision"},
                        "findings_summary": {"type": "string", "description": "Summary of research findings"},
                        "readiness_score": {"type": "number", "description": "Readiness score (0-10)"}
                    },
                    "required": ["reason", "findings_summary"]
                }
            }
        }

    def execute(self, reason: str, findings_summary: str,
                readiness_score: Optional[float] = None) -> Dict[str, Any]:
        """Execute architecture writing decision"""
        decision = {
            "id": str(uuid.uuid4()),
            "decision": "start_architecture_writing",
            "reason": reason,
            "findings_summary": findings_summary,
            "readiness_score": readiness_score or 7.0,
            "decided_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "decision": decision,
            "message": "Decided to start architecture writing phase"
        }


class AnalyzeRequirementsTool(BaseTool):
    """Analyze requirements for completeness"""

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "analyze_requirements",
                "description": "Analyze requirements for completeness and clarity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requirements": {"type": "array", "items": {"type": "string"}, "description": "List of requirements"},
                        "analysis_type": {"type": "string", "description": "Type of analysis"},
                        "context": {"type": "string", "description": "Analysis context"}
                    },
                    "required": ["requirements"]
                }
            }
        }

    def execute(self, requirements: List[str],
                analysis_type: Optional[str] = None,
                context: Optional[str] = None) -> Dict[str, Any]:
        """Execute requirements analysis"""
        analysis = {
            "id": str(uuid.uuid4()),
            "requirements": requirements,
            "analysis_type": analysis_type or "completeness",
            "context": context or "general",
            "total_requirements": len(requirements),
            "analysis_results": self._perform_analysis(requirements),
            "analyzed_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "analysis": analysis,
            "message": f"Analyzed {len(requirements)} requirements"
        }

    def _perform_analysis(self, requirements: List[str]) -> Dict:
        """Perform basic analysis on requirements"""
        complete_reqs = sum(1 for r in requirements if len(r.split()) > 5)
        return {
            "complete_requirements": complete_reqs,
            "incomplete_requirements": len(requirements) - complete_reqs,
            "completeness_score": complete_reqs / len(requirements) if requirements else 0,
            "identified_gaps": self._identify_gaps(requirements)
        }

    def _identify_gaps(self, requirements: List[str]) -> List[str]:
        """Identify potential gaps in requirements"""
        gaps = []
        req_text = " ".join(requirements).lower()

        common_aspects = ["security", "performance", "scalability", "testing", "documentation"]
        for aspect in common_aspects:
            if aspect not in req_text:
                gaps.append(f"Consider {aspect} requirements")

        return gaps