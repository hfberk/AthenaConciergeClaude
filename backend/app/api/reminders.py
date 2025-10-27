"""Reminders API endpoints"""

from typing import List
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery

router = APIRouter()


# Pydantic schemas
class ReminderRuleBase(BaseModel):
    reminder_type: str  # lead_time or scheduled
    lead_time_days: int | None = None
    scheduled_datetime: str | None = None
    metadata_jsonb: dict = {}


class ReminderRuleCreate(ReminderRuleBase):
    org_id: UUID
    person_id: UUID  # Will be used to find comm_identity
    date_item_id: UUID | None = None  # Optional - can be standalone reminder
    action: str | None = None  # What to remind about (for standalone reminders)


class ReminderRuleUpdate(BaseModel):
    reminder_type: str | None = None
    lead_time_days: int | None = None
    scheduled_datetime: str | None = None
    metadata_jsonb: dict | None = None


class MessageResponse(BaseModel):
    message_id: UUID
    content_text: str
    direction: str
    agent_name: str | None
    created_at: str

    class Config:
        from_attributes = True


class ReminderRuleResponse(ReminderRuleBase):
    reminder_rule_id: UUID
    org_id: UUID
    date_item_id: UUID | None
    comm_identity_id: UUID
    sent_at: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ReminderHistoryResponse(ReminderRuleResponse):
    """Reminder with delivery history"""
    messages: List[MessageResponse] = []


@router.get("/reminders", response_model=List[ReminderRuleResponse])
async def list_reminders(
    org_id: UUID,
    person_id: UUID | None = None,
    status_filter: str = "all",  # all, pending, sent
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """
    List reminder rules with filtering

    Args:
        org_id: Organization ID
        person_id: Optional person ID to filter by
        status_filter: Filter by status - "all", "pending", or "sent"
        skip: Pagination offset
        limit: Pagination limit
    """
    # Get all reminders for org
    filters = {'org_id': org_id}

    reminders = SupabaseQuery.select_active(
        client=db,
        table='reminder_rules',
        filters=filters,
        order_by='scheduled_datetime',
        limit=1000  # Get more for filtering
    )

    # Filter by person_id if provided
    if person_id:
        # Get person's comm_identities
        comm_identities = SupabaseQuery.select_active(
            client=db,
            table='comm_identities',
            filters={'person_id': person_id}
        )
        comm_identity_ids = [ci['comm_identity_id'] for ci in comm_identities]

        reminders = [
            r for r in reminders
            if r.get('comm_identity_id') in comm_identity_ids
        ]

    # Filter by status
    if status_filter == "pending":
        reminders = [r for r in reminders if r.get('sent_at') is None]
    elif status_filter == "sent":
        reminders = [r for r in reminders if r.get('sent_at') is not None]

    # Apply pagination
    reminders = reminders[skip:skip + limit]

    return reminders


@router.get("/reminders/{reminder_id}", response_model=ReminderRuleResponse)
async def get_reminder(reminder_id: UUID, db: Client = Depends(get_db)):
    """Get reminder rule by ID"""
    reminder = SupabaseQuery.get_by_id(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    return reminder


@router.post("/reminders", response_model=ReminderRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder: ReminderRuleCreate, db: Client = Depends(get_db)):
    """
    Create a new reminder rule

    Can be linked to a date_item or standalone
    """
    # Verify person exists
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=reminder.person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Get person's primary comm_identity
    comm_identities = SupabaseQuery.select_active(
        client=db,
        table='comm_identities',
        filters={'person_id': reminder.person_id},
        limit=1
    )

    if not comm_identities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No communication identity found for person"
        )

    comm_identity = comm_identities[0]

    # If linked to date_item, verify it exists
    if reminder.date_item_id:
        date_item = SupabaseQuery.get_by_id(
            client=db,
            table='date_items',
            id_column='date_item_id',
            id_value=reminder.date_item_id
        )

        if not date_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Date item not found"
            )

        # Calculate scheduled_datetime for lead_time type
        if reminder.reminder_type == 'lead_time' and reminder.lead_time_days:
            from datetime import timedelta
            target_date = datetime.fromisoformat(date_item['next_occurrence'] or date_item['date_value'])
            reminder_date = target_date - timedelta(days=reminder.lead_time_days)
            reminder.scheduled_datetime = reminder_date.isoformat()

    # Validate scheduled_datetime is provided for scheduled type
    if reminder.reminder_type == 'scheduled' and not reminder.scheduled_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_datetime is required for scheduled reminder type"
        )

    # Create reminder_rule
    reminder_data = reminder.model_dump(exclude={'person_id', 'action'})
    reminder_data['reminder_rule_id'] = uuid4()
    reminder_data['comm_identity_id'] = comm_identity['comm_identity_id']
    reminder_data['created_at'] = datetime.utcnow().isoformat()
    reminder_data['updated_at'] = datetime.utcnow().isoformat()

    # Add action to metadata if provided
    if reminder.action:
        reminder_data['metadata_jsonb']['action'] = reminder.action

    reminder_data['metadata_jsonb']['created_by'] = 'reminders_api'

    created_reminder = SupabaseQuery.insert(
        client=db,
        table='reminder_rules',
        data=reminder_data
    )

    return created_reminder


@router.put("/reminders/{reminder_id}", response_model=ReminderRuleResponse)
async def update_reminder(
    reminder_id: UUID,
    reminder_update: ReminderRuleUpdate,
    db: Client = Depends(get_db)
):
    """Update reminder rule"""
    existing_reminder = SupabaseQuery.get_by_id(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id
    )

    if not existing_reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Don't allow updating already-sent reminders
    if existing_reminder.get('sent_at'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update reminder that has already been sent"
        )

    update_data = reminder_update.model_dump(exclude_unset=True)
    updated_reminder = SupabaseQuery.update(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id,
        data=update_data
    )

    return updated_reminder


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(reminder_id: UUID, db: Client = Depends(get_db)):
    """Soft delete reminder rule"""
    deleted = SupabaseQuery.soft_delete(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    return None


@router.get("/reminders/{reminder_id}/history", response_model=ReminderHistoryResponse)
async def get_reminder_history(reminder_id: UUID, db: Client = Depends(get_db)):
    """
    Get reminder delivery history

    Returns reminder rule with associated messages sent
    """
    reminder = SupabaseQuery.get_by_id(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Find messages associated with this reminder
    # Look for messages from 'reminder' agent sent to this person around the scheduled time
    messages = []

    if reminder.get('sent_at'):
        # Get comm_identity to find person
        comm_identity = SupabaseQuery.get_by_id(
            client=db,
            table='comm_identities',
            id_column='comm_identity_id',
            id_value=reminder['comm_identity_id']
        )

        if comm_identity:
            # Get conversations for this person
            conversations = SupabaseQuery.select_active(
                client=db,
                table='conversations',
                filters={'person_id': comm_identity['person_id']},
                limit=10
            )

            # Look through messages in these conversations
            for conv in conversations:
                conv_messages = SupabaseQuery.select_active(
                    client=db,
                    table='messages',
                    filters={
                        'conversation_id': conv['conversation_id'],
                        'agent_name': 'reminder',
                        'direction': 'outbound'
                    },
                    limit=20
                )
                messages.extend(conv_messages)

    reminder['messages'] = messages
    return reminder


@router.post("/reminders/{reminder_id}/retry", response_model=ReminderRuleResponse)
async def retry_reminder(reminder_id: UUID, db: Client = Depends(get_db)):
    """
    Manually retry sending a failed reminder

    Resets sent_at to None and updates scheduled_datetime to now
    """
    reminder = SupabaseQuery.get_by_id(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id
    )

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

    # Reset sent_at and update scheduled_datetime to now
    update_data = {
        'sent_at': None,
        'scheduled_datetime': datetime.utcnow().isoformat(),
        'metadata_jsonb': {
            **reminder.get('metadata_jsonb', {}),
            'manually_retried': True,
            'retry_at': datetime.utcnow().isoformat()
        }
    }

    updated_reminder = SupabaseQuery.update(
        client=db,
        table='reminder_rules',
        id_column='reminder_rule_id',
        id_value=reminder_id,
        data=update_data
    )

    return updated_reminder
