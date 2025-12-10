#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Concise workflow implementation for deepcodeagent
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Add parent directory to path (for src)
parent_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, parent_path)

from src.myllms import get_llm_by_type
from src.deepcodeagent.coding_team import CodingTeam
from src.deepcodeagent.core import DeepCodeAgentState, WorkflowStage
from src.deepcodeagent.coordinator import GlobalCoordinator, TaskType
from src.deepcodeagent.architecture_team import ArchitectureTeam


async def workflowfun(requirement: str, output_dir: str = None) -> Dict:
    """
    Three-layer workflow function

    Args:
        requirement: User requirement
        output_dir: Output directory (optional)

    Returns:
        Workflow result dictionary
    """
    logger.info(f"[WORKFLOW] Starting workflow for requirement: {requirement[:100]}...")

    # Setup output directory
    if output_dir is None:
        output_dir = Path("testdir") / datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[WORKFLOW] Output directory: {output_dir}")

    # Initialize global coordinator
    logger.info("[WORKFLOW] Initializing global coordinator")
    global_coordinator = GlobalCoordinator()

    print(f"Workflow session: {output_dir}")
    print(f"Requirement: {requirement}")

    try:
        # Phase 1: Global coordination decision
        logger.info("[WORKFLOW] Phase 1: Analyzing requirement with global coordinator")
        decision = await global_coordinator.analyze(requirement)
        logger.info(f"[WORKFLOW] Global coordinator decision: {decision.task_type.value}")
        logger.debug(f"[WORKFLOW] Decision reasoning: {decision.reasoning[:200]}...")
        print(f"Decision: {decision.task_type.value}")
        print(f"Reasoning: {decision.reasoning}")

        # Phase 2: Route based on decision
        if decision.task_type == TaskType.DIRECT_ANSWER:
            logger.info("[WORKFLOW] Phase 2: Routing to direct answer")
            # Direct answer
            answer = await global_coordinator.direct_answer(requirement)
            return {
                "requirement": requirement,
                "session_id": output_dir.name,
                "task_type": "direct_answer",
                "answer": answer,
                "success": True,
                "created_at": datetime.now().isoformat(),
                "files_created": []
            }

        elif decision.task_type == TaskType.RESEARCH:
            logger.info("[WORKFLOW] Phase 2: Routing to research phase")
            # Research phase
            logger.info("[WORKFLOW] Initializing architecture team")
            architecture_team = ArchitectureTeam(
                planner_model=get_llm_by_type("reasoning"),
                coordinator_model=get_llm_by_type("reasoning"),
                researcher_model=get_llm_by_type("basic"),
                writer_model=get_llm_by_type("reasoning"),
                output_dir=output_dir
            )

            logger.info("[WORKFLOW] Creating initial state for research")
            state = DeepCodeAgentState(
                task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_requirement=requirement,
                current_stage=WorkflowStage.REQUIREMENT_ANALYSIS
            )

            # Run research phase
            logger.info("[WORKFLOW] Starting research phase loop")
            research_iterations = 0
            while state.current_stage in [WorkflowStage.REQUIREMENT_ANALYSIS, WorkflowStage.RESEARCH_PLANNING,
                                         WorkflowStage.RESEARCH_EXECUTION, WorkflowStage.ARCHITECTURE_WRITING]:
                logger.debug(f"[WORKFLOW] Research iteration {research_iterations}, stage: {state.current_stage.value}")
                state = await architecture_team.process(state)
                research_iterations += 1
                if research_iterations > 10:  # Safety check
                    logger.warning("[WORKFLOW] Research phase exceeded 10 iterations, breaking")
                    break

            logger.info("[WORKFLOW] Research phase completed")
            # Research completed, check if coding is needed
            if state.architecture_document:
                logger.info("[WORKFLOW] Architecture document generated, proceeding to coding")
                logger.debug(f"[WORKFLOW] Architecture document length: {len(state.architecture_document)}")
                # Proceed to coding
                coding_team = CodingTeam(
                    coordinator_model=get_llm_by_type("reasoning"),
                    coder_model=get_llm_by_type("code"),
                    test_model=get_llm_by_type("basic"),
                    reflector_model=get_llm_by_type("reasoning"),
                    middleware_chain=None,
                    human_in_the_loop=None
                )

                state.current_stage = WorkflowStage.CODING_COORDINATION
                logger.info("[WORKFLOW] Starting coding phase")
                final_state = await coding_team.process(state)
                logger.info("[WORKFLOW] Coding phase completed")

                # Collect created files
                logger.info("[WORKFLOW] Collecting created files")
                created_files = []
                for file_path in output_dir.rglob("*"):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(output_dir))
                        created_files.append(rel_path)
                logger.info(f"[WORKFLOW] Found {len(created_files)} created files")

                return {
                    "requirement": requirement,
                    "session_id": output_dir.name,
                    "task_type": "research_then_coding",
                    "research_output": state.architecture_document[:500] if state.architecture_document else "",
                    "success": len(created_files) > 0,
                    "created_at": datetime.now().isoformat(),
                    "files_created": created_files
                }
            else:
                # Research only
                return {
                    "requirement": requirement,
                    "session_id": output_dir.name,
                    "task_type": "research_only",
                    "research_output": state.architecture_document[:500] if state.architecture_document else "",
                    "success": True,
                    "created_at": datetime.now().isoformat(),
                    "files_created": ["research_report.md"]
                }

        else:  # CODING
            logger.info("[WORKFLOW] Phase 2: Routing to direct coding")
            # Direct coding
            logger.info("[WORKFLOW] Initializing coding team for direct coding")
            coding_team = CodingTeam(
                coordinator_model=get_llm_by_type("reasoning"),
                coder_model=get_llm_by_type("code"),
                test_model=get_llm_by_type("basic"),
                reflector_model=get_llm_by_type("reasoning"),
                middleware_chain=None,
                human_in_the_loop=None
            )

            logger.info("[WORKFLOW] Creating initial state for direct coding")
            # Create a basic architecture document for direct coding tasks
            basic_architecture = f"""
# Architecture Plan: {requirement}

## Overview
Direct implementation of the requirement without extensive research phase.

## Key Components
- Core functionality based on user requirement
- Basic structure following standard practices
- Minimal external dependencies

## Implementation Notes
- Focus on core functionality first
- Use standard libraries and patterns
- Keep implementation simple and maintainable

## Next Steps
1. Break down into concrete coding tasks
2. Implement core components
3. Test basic functionality
4. Refine and complete
"""

            state = DeepCodeAgentState(
                task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_requirement=requirement,
                current_stage=WorkflowStage.CODING_COORDINATION,
                architecture_document=basic_architecture
            )

            logger.info("[WORKFLOW] Starting direct coding phase")

            # Keep processing until coding is complete
            coding_iterations = 0
            while state.current_stage in [WorkflowStage.CODING_COORDINATION, WorkflowStage.TASK_BREAKDOWN,
                                        WorkflowStage.CODE_WRITING, WorkflowStage.CODE_TESTING,
                                        WorkflowStage.REFLECTION]:
                logger.debug(f"[WORKFLOW] Coding iteration {coding_iterations}, stage: {state.current_stage.value}")
                state = await coding_team.process(state)
                coding_iterations += 1
                if coding_iterations > 20:  # Safety check
                    logger.warning("[WORKFLOW] Coding phase exceeded 20 iterations, breaking")
                    break

            logger.info("[WORKFLOW] Direct coding phase completed")

            # Collect created files
            logger.info("[WORKFLOW] Collecting created files")
            created_files = []
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(output_dir))
                    created_files.append(rel_path)
            logger.info(f"[WORKFLOW] Found {len(created_files)} created files")

            return {
                "requirement": requirement,
                "session_id": output_dir.name,
                "task_type": "coding_only",
                "success": len(created_files) > 0,
                "created_at": datetime.now().isoformat(),
                "files_created": created_files
            }

    except Exception as e:
        logger.error(f"[WORKFLOW] Workflow failed with error: {e}", exc_info=True)
        # Save error summary
        summary_file = output_dir / "workflow_summary.json"
        error_summary = {
            "error": str(e),
            "session_id": output_dir.name,
            "success": False,
            "created_at": datetime.now().isoformat()
        }
        logger.info(f"[WORKFLOW] Saving error summary to {summary_file}")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(error_summary, f, indent=2, ensure_ascii=False)
        logger.error(f"[WORKFLOW] Workflow failed: {str(e)}")
        return error_summary

    finally:
        # Save summary
        logger.info("[WORKFLOW] Saving workflow summary")
        summary = {
            "requirement": requirement,
            "session_id": output_dir.name,
            "created_at": datetime.now().isoformat()
        }
        if 'result' in locals():
            summary.update(result)

        summary_file = output_dir / "workflow_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Example usage
    async def main():
        result = await workflowfun("Create a simple REST API")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())