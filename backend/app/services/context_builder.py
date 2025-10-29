"""Context builder for assembling comprehensive client context for agents"""

from uuid import UUID
from supabase import Client
from datetime import datetime, timedelta
import structlog
from app.utils.supabase_helpers import SupabaseQuery

logger = structlog.get_logger()


class ContextBuilder:
    """Builds comprehensive context for AI agents"""

    def __init__(self, db: Client):
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
        person = SupabaseQuery.get_by_id(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=person_id
        )

        if not person:
            return {}

        return {
            "person_id": str(person['person_id']),
            "full_name": person.get('full_name'),
            "preferred_name": person.get('preferred_name') or person.get('full_name', '').split()[0] if person.get('full_name') else '',
            "person_type": person.get('person_type'),
            "timezone": person.get('timezone'),
            "metadata": person.get('metadata_jsonb') or {}
        }

    def _get_households(self, person_id: UUID) -> list:
        """Get household memberships and addresses"""
        memberships = SupabaseQuery.select_active(
            client=self.db,
            table='household_members',
            filters={'person_id': str(person_id)}
        )

        households = []
        for membership in memberships:
            # Fetch household for this membership
            household = SupabaseQuery.get_by_id(
                client=self.db,
                table='households',
                id_column='household_id',
                id_value=membership['household_id']
            )

            if household:
                # Fetch addresses for this household
                addresses = SupabaseQuery.select_active(
                    client=self.db,
                    table='addresses',
                    filters={'household_id': membership['household_id']}
                )

                households.append({
                    "household_name": household.get('household_name'),
                    "household_type": household.get('household_type'),
                    "relationship": membership.get('relationship_to_primary'),
                    "addresses": [
                        {
                            "label": addr.get('label'),
                            "address": addr.get('address_jsonb')
                        }
                        for addr in addresses
                    ]
                })

        return households

    def _get_recent_conversations(self, person_id: UUID, current_conversation_id: UUID | None = None) -> list:
        """Get recent conversation history (sliding window)"""
        # Get last 3 conversations (excluding current)
        # Note: Supabase doesn't support != filter, so we'll fetch and filter in Python
        all_conversations = SupabaseQuery.select_active(
            client=self.db,
            table='conversations',
            filters={'person_id': str(person_id)},
            order_by='updated_at.desc',
            limit=10  # Fetch a few extra to account for filtering
        )

        # Filter out current conversation if needed
        if current_conversation_id:
            recent_conversations = [
                conv for conv in all_conversations
                if conv['conversation_id'] != str(current_conversation_id)
            ][:3]
        else:
            recent_conversations = all_conversations[:3]

        conversations = []
        for conv in recent_conversations:
            # Get last 5 messages from each conversation
            # Note: We need to order desc and then reverse
            messages = SupabaseQuery.select_active(
                client=self.db,
                table='messages',
                filters={'conversation_id': conv['conversation_id']},
                order_by='created_at.desc',
                limit=5
            )

            conversations.append({
                "conversation_id": str(conv['conversation_id']),
                "subject": conv.get('subject'),
                "channel_type": conv.get('channel_type'),
                "updated_at": conv.get('updated_at'),
                "messages": [
                    {
                        "direction": msg.get('direction'),
                        "content": msg.get('content_text'),
                        "created_at": msg.get('created_at')
                    }
                    for msg in reversed(messages)
                ]
            })

        # Get messages from current conversation if provided
        if current_conversation_id:
            current_messages = SupabaseQuery.select_active(
                client=self.db,
                table='messages',
                filters={'conversation_id': str(current_conversation_id)},
                order_by='created_at.asc'
            )

            conversations.insert(0, {
                "conversation_id": str(current_conversation_id),
                "subject": "Current conversation",
                "channel_type": "current",
                "is_current": True,
                "messages": [
                    {
                        "direction": msg.get('direction'),
                        "content": msg.get('content_text'),
                        "created_at": msg.get('created_at')
                    }
                    for msg in current_messages
                ]
            })

        return conversations

    def _get_upcoming_dates(self, person_id: UUID, days_ahead: int = 90) -> list:
        """Get upcoming important dates"""
        cutoff_date = (datetime.now().date() + timedelta(days=days_ahead)).isoformat()

        # Note: Complex filtering (<=) needs to be done via Supabase query builder
        # For now, fetch all date items and filter in Python
        date_items = SupabaseQuery.select_active(
            client=self.db,
            table='date_items',
            filters={'person_id': str(person_id)},
            order_by='next_occurrence.asc'
        )

        # Filter by cutoff date and fetch categories
        result = []
        for item in date_items:
            next_occ = item.get('next_occurrence')
            if next_occ and next_occ <= cutoff_date:
                # Fetch category if present
                category_name = None
                if item.get('date_category_id'):
                    category = SupabaseQuery.get_by_id(
                        client=self.db,
                        table='date_categories',
                        id_column='date_category_id',
                        id_value=item['date_category_id']
                    )
                    category_name = category.get('category_name') if category else None

                result.append({
                    "title": item.get('title'),
                    "date": next_occ if next_occ else item.get('date_value'),
                    "category": category_name,
                    "notes": item.get('notes')
                })

        return result

    def _get_active_projects(self, person_id: UUID) -> list:
        """Get active projects"""
        # Note: Supabase .in_() filter needs to be done via query builder or fetch & filter
        # Fetch all projects for person and filter in Python
        projects = SupabaseQuery.select_active(
            client=self.db,
            table='projects',
            filters={'person_id': str(person_id)},
            order_by='priority.asc'
        )

        # Filter by status and format
        active_statuses = ["new", "in_progress", "blocked"]
        return [
            {
                "project_id": str(proj['project_id']),
                "title": proj.get('title'),
                "description": proj.get('description'),
                "status": proj.get('status'),
                "priority": proj.get('priority'),
                "due_date": proj.get('due_date')
            }
            for proj in projects
            if proj.get('status') in active_statuses
        ]

    def _get_preferences(self, person_id: UUID) -> dict:
        """Extract preferences from metadata and past interactions"""
        person = SupabaseQuery.get_by_id(
            client=self.db,
            table='persons',
            id_column='person_id',
            id_value=person_id
        )

        if not person or not person.get('metadata_jsonb'):
            return {}

        # Extract common preference categories
        metadata = person.get('metadata_jsonb', {})
        return {
            "dining": metadata.get("dining_preferences", {}),
            "travel": metadata.get("travel_preferences", {}),
            "communication": metadata.get("communication_preferences", {}),
            "interests": metadata.get("interests", []),
            "dietary_restrictions": metadata.get("dietary_restrictions", []),
        }
