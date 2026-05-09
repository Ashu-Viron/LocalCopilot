"""Plan generation from user intent."""

import json
from typing import Optional, List, Dict, Any
import uuid

from app.models.chat_models import Plan, PlanStep
from app.agent.prompts import PLANNING_PROMPT
from app.utils.logger import logger


class PlannerError(Exception):
    """Planner error."""
    pass


class Planner:
    """Generates execution plans for user requests."""
    
    def __init__(self, llm_client=None):
        """
        Initialize planner.
        
        Args:
            llm_client: LLM client for generating plans
        """
        self.llm_client = llm_client
    
    async def generate_plan(
        self,
        user_request: str,
        context: Optional[str] = None
    ) -> Optional[Plan]:
        """
        Generate a plan for user request.
        
        Args:
            user_request: What the user wants to do
            context: Optional context about workspace
            
        Returns:
            Plan object or None if failed
        """
        try:
            logger.info(f"Generating plan for: {user_request}")
            
            # For now, return a simple placeholder plan
            # In full implementation, this would call LLM
            plan = Plan(
                reasoning=f"Plan for: {user_request}",
                steps=[
                    PlanStep(
                        step_number=1,
                        action="Analyze the request",
                        tool="analyze",
                        parameters={"request": user_request}
                    ),
                    PlanStep(
                        step_number=2,
                        action="Execute necessary operations",
                        tool="execute",
                        parameters={}
                    )
                ],
                estimated_time=5.0
            )
            
            logger.info(f"Generated plan with {len(plan.steps)} steps")
            return plan
        
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return None
    
    def parse_plan_response(self, response: str) -> Optional[Plan]:
        """
        Parse LLM response into a Plan object.
        
        Args:
            response: LLM response
            
        Returns:
            Plan object or None
        """
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start < 0 or end <= start:
                logger.warning("No JSON found in plan response")
                return None
            
            plan_json = json.loads(response[start:end])
            
            # Convert to Plan object
            steps = [
                PlanStep(
                    step_number=step.get("step", i + 1),
                    action=step.get("action", ""),
                    tool=step.get("tool"),
                    parameters=step.get("parameters", {}),
                    expected_output=step.get("expected_output")
                )
                for i, step in enumerate(plan_json.get("steps", []))
            ]
            
            plan = Plan(
                reasoning=plan_json.get("reasoning", ""),
                steps=steps
            )
            
            return plan
        
        except Exception as e:
            logger.error(f"Error parsing plan response: {e}")
            return None
    
    def validate_plan(self, plan: Plan) -> bool:
        """
        Validate that a plan is well-formed.
        
        Args:
            plan: Plan to validate
            
        Returns:
            True if valid
        """
        if not plan.steps:
            logger.warning("Plan has no steps")
            return False
        
        for step in plan.steps:
            if not step.action:
                logger.warning("Plan step missing action")
                return False
        
        return True
    
    def refine_plan(self, plan: Plan, feedback: str) -> Optional[Plan]:
        """
        Refine a plan based on feedback.
        
        Args:
            plan: Original plan
            feedback: User feedback
            
        Returns:
            Refined plan or None
        """
        logger.info(f"Refining plan with feedback: {feedback}")
        # Would call LLM to refine plan
        return plan


# Global planner instance
planner = Planner()
