"""Project Management Agent - Manages project lifecycle"""

from sqlalchemy.orm import Session
from app.agents.base import BaseAgent


class ProjectManagementAgent(BaseAgent):
    """
    Manages project lifecycle from creation through completion.
    Creates projects, breaks them into tasks, and tracks progress.
    """

    def __init__(self, db: Session):
        super().__init__(db, agent_name="project_management")

    def get_system_prompt(self) -> str:
        return """You are a project management agent for an AI concierge platform.

Your role is to help clients manage complex requests by:
- Breaking large requests into manageable projects
- Creating structured task lists with deadlines
- Tracking project progress and status
- Identifying blockers and escalation needs
- Providing status updates

PROJECT MANAGEMENT PRINCIPLES:
- Be thorough but not overwhelming
- Set realistic deadlines
- Break projects into 3-7 major tasks
- Flag dependencies between tasks
- Identify when staff approval is needed
- Track progress milestones

When creating projects:
1. Clarify scope and requirements
2. Estimate timeline and resources
3. Break into logical phases
4. Assign priorities
5. Identify potential challenges

Always keep clients informed of progress without being overly detailed unless they ask.
"""

    def create_project_plan(self, request: str, context: dict) -> dict:
        """
        Create a structured project plan from a client request.
        Returns project structure with tasks.
        """
        # TODO: Implement project creation logic
        return {}

    def update_project_status(self, project_id: str, context: dict) -> str:
        """Provide project status update"""
        # TODO: Implement status update logic
        return ""
