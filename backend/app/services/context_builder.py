"""Context builder for assembling comprehensive client context for agents"""

from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class ContextBuilder:
    """Builds comprehensive context for AI agents"""

    def __init__(self, db: Session):
        self.db = db

    def build_context(self, person_id: UUID, conversation_id: UUID | None = None) -> dict:
        """
        Build comprehensive context for a person and conversation.

        Returns structured context including:
        - Person profile and preferences
        - Household information
        - Recent conversations
        - Upcoming important dates
        - Active projects
        - Past recommendations and feedback
        """
        context = {
            "person": self._get_person_profile(person_id),
            "households": self._get_households(person_id),
            "recent_conversations": self._get_recent_conversations(person_id, conversation_id),
            "upcoming_dates": self._get_upcoming_dates(person_id),
            "active_projects": self._get_active_projects(person_id),
            "preferences": self._get_preferences(person_id),
        }

        return context

    def _get_person_profile(self, person_id: UUID) -> dict:
        """Get person profile with basic information"""
        from app.models.identity import Person

        person = self.db.query(Person).filter(
            Person.person_id == person_id,
            Person.deleted_at.is_(None)
        ).first()

        if not person:
            return {}

        return {
            "person_id": str(person.person_id),
            "full_name": person.full_name,
            "preferred_name": person.preferred_name or person.full_name.split()[0],
            "person_type": person.person_type,
            "timezone": person.timezone,
            "metadata": person.metadata_jsonb or {}
        }

    def _get_households(self, person_id: UUID) -> list:
        """Get household memberships and addresses"""
        from app.models.household import HouseholdMember, Household, Address

        memberships = self.db.query(HouseholdMember).filter(
            HouseholdMember.person_id == person_id,
            HouseholdMember.deleted_at.is_(None)
        ).all()

        households = []
        for membership in memberships:
            household = membership.household
            if household and not household.deleted_at:
                addresses = self.db.query(Address).filter(
                    Address.household_id == household.household_id,
                    Address.deleted_at.is_(None)
                ).all()

                households.append({
                    "household_name": household.household_name,
                    "household_type": household.household_type,
                    "relationship": membership.relationship_to_primary,
                    "addresses": [
                        {
                            "label": addr.label,
                            "address": addr.address_jsonb
                        }
                        for addr in addresses
                    ]
                })

        return households

    def _get_recent_conversations(self, person_id: UUID, current_conversation_id: UUID | None = None) -> list:
        """Get recent conversation history (sliding window)"""
        from app.models.communication import Conversation, Message

        # Get last 3 conversations (excluding current)
        query = self.db.query(Conversation).filter(
            Conversation.person_id == person_id,
            Conversation.deleted_at.is_(None)
        )

        if current_conversation_id:
            query = query.filter(Conversation.conversation_id != current_conversation_id)

        recent_conversations = query.order_by(
            Conversation.updated_at.desc()
        ).limit(3).all()

        conversations = []
        for conv in recent_conversations:
            # Get last 5 messages from each conversation
            messages = self.db.query(Message).filter(
                Message.conversation_id == conv.conversation_id,
                Message.deleted_at.is_(None)
            ).order_by(Message.created_at.desc()).limit(5).all()

            conversations.append({
                "conversation_id": str(conv.conversation_id),
                "subject": conv.subject,
                "channel_type": conv.channel_type,
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    {
                        "direction": msg.direction,
                        "content": msg.content_text,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in reversed(messages)
                ]
            })

        # Get messages from current conversation if provided
        if current_conversation_id:
            current_messages = self.db.query(Message).filter(
                Message.conversation_id == current_conversation_id,
                Message.deleted_at.is_(None)
            ).order_by(Message.created_at).all()

            conversations.insert(0, {
                "conversation_id": str(current_conversation_id),
                "subject": "Current conversation",
                "channel_type": "current",
                "is_current": True,
                "messages": [
                    {
                        "direction": msg.direction,
                        "content": msg.content_text,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in current_messages
                ]
            })

        return conversations

    def _get_upcoming_dates(self, person_id: UUID, days_ahead: int = 90) -> list:
        """Get upcoming important dates"""
        from app.models.dates import DateItem, DateCategory

        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)

        date_items = self.db.query(DateItem).join(DateCategory).filter(
            DateItem.person_id == person_id,
            DateItem.deleted_at.is_(None),
            DateItem.next_occurrence <= cutoff_date
        ).order_by(DateItem.next_occurrence).all()

        return [
            {
                "title": item.title,
                "date": item.next_occurrence.isoformat() if item.next_occurrence else item.date_value.isoformat(),
                "category": item.category.category_name if item.category else None,
                "notes": item.notes
            }
            for item in date_items
        ]

    def _get_active_projects(self, person_id: UUID) -> list:
        """Get active projects"""
        from app.models.projects import Project

        projects = self.db.query(Project).filter(
            Project.person_id == person_id,
            Project.status.in_(["new", "in_progress", "blocked"]),
            Project.deleted_at.is_(None)
        ).order_by(Project.priority, Project.created_at.desc()).all()

        return [
            {
                "project_id": str(proj.project_id),
                "title": proj.title,
                "description": proj.description,
                "status": proj.status,
                "priority": proj.priority,
                "due_date": proj.due_date.isoformat() if proj.due_date else None
            }
            for proj in projects
        ]

    def _get_preferences(self, person_id: UUID) -> dict:
        """Extract preferences from metadata and past interactions"""
        from app.models.identity import Person

        person = self.db.query(Person).filter(
            Person.person_id == person_id
        ).first()

        if not person or not person.metadata_jsonb:
            return {}

        # Extract common preference categories
        metadata = person.metadata_jsonb
        return {
            "dining": metadata.get("dining_preferences", {}),
            "travel": metadata.get("travel_preferences", {}),
            "communication": metadata.get("communication_preferences", {}),
            "interests": metadata.get("interests", []),
            "dietary_restrictions": metadata.get("dietary_restrictions", []),
        }
