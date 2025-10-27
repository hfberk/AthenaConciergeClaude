"""Date Items API endpoints"""

from typing import List
from uuid import UUID, uuid4
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery

router = APIRouter()


# Pydantic schemas
class ReminderRuleCreate(BaseModel):
    """Embedded reminder rule for creating with date item"""
    reminder_type: str  # lead_time or scheduled
    lead_time_days: int | None = None
    scheduled_datetime: str | None = None
    channel_type: str = "slack"


class DateItemBase(BaseModel):
    title: str
    date_value: str  # Date as ISO string (YYYY-MM-DD)
    category_id: UUID
    recurrence_rule: str | None = None  # iCal RRULE format
    notes: str | None = None
    metadata_jsonb: dict = {}


class DateItemCreate(DateItemBase):
    person_id: UUID
    org_id: UUID
    reminder_rules: List[ReminderRuleCreate] = []  # Create reminders with date


class DateItemUpdate(BaseModel):
    title: str | None = None
    date_value: str | None = None
    category_id: UUID | None = None
    recurrence_rule: str | None = None
    notes: str | None = None
    metadata_jsonb: dict | None = None


class ReminderRuleResponse(BaseModel):
    reminder_rule_id: UUID
    reminder_type: str
    lead_time_days: int | None
    scheduled_datetime: str | None
    sent_at: str | None
    created_at: str

    class Config:
        from_attributes = True


class DateItemResponse(DateItemBase):
    date_item_id: UUID
    person_id: UUID
    org_id: UUID
    next_occurrence: str | None
    created_at: str
    updated_at: str
    reminder_rules: List[ReminderRuleResponse] = []

    class Config:
        from_attributes = True


@router.get("/persons/{person_id}/date-items", response_model=List[DateItemResponse])
async def list_person_date_items(
    person_id: UUID,
    category_id: UUID | None = None,
    upcoming_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """List date items for a person"""
    filters = {'person_id': person_id}
    if category_id:
        filters['category_id'] = category_id

    date_items = SupabaseQuery.select_active(
        client=db,
        table='date_items',
        filters=filters,
        order_by='next_occurrence',
        limit=limit,
        offset=skip
    )

    # Filter upcoming if requested
    if upcoming_only:
        today = date.today().isoformat()
        date_items = [
            item for item in date_items
            if item.get('next_occurrence') and item.get('next_occurrence') >= today
        ]

    # Fetch reminder_rules for each date_item
    for item in date_items:
        reminder_rules = SupabaseQuery.select_active(
            client=db,
            table='reminder_rules',
            filters={'date_item_id': item['date_item_id']}
        )
        item['reminder_rules'] = reminder_rules

    return date_items


@router.get("/date-items/{date_item_id}", response_model=DateItemResponse)
async def get_date_item(date_item_id: UUID, db: Client = Depends(get_db)):
    """Get date item by ID"""
    date_item = SupabaseQuery.get_by_id(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id
    )

    if not date_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date item not found"
        )

    # Fetch reminder_rules
    reminder_rules = SupabaseQuery.select_active(
        client=db,
        table='reminder_rules',
        filters={'date_item_id': date_item_id}
    )
    date_item['reminder_rules'] = reminder_rules

    return date_item


@router.post("/date-items", response_model=DateItemResponse, status_code=status.HTTP_201_CREATED)
async def create_date_item(date_item: DateItemCreate, db: Client = Depends(get_db)):
    """Create new date item with optional reminder rules"""

    # Verify person exists
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=date_item.person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Verify category exists
    category = SupabaseQuery.get_by_id(
        client=db,
        table='date_categories',
        id_column='category_id',
        id_value=date_item.category_id
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date category not found"
        )

    # Create date_item
    date_item_data = date_item.model_dump(exclude={'reminder_rules'})
    date_item_data['date_item_id'] = uuid4()
    date_item_data['next_occurrence'] = date_item.date_value  # Initial next occurrence
    date_item_data['created_at'] = datetime.utcnow().isoformat()
    date_item_data['updated_at'] = datetime.utcnow().isoformat()

    created_date_item = SupabaseQuery.insert(
        client=db,
        table='date_items',
        data=date_item_data
    )

    # Create reminder_rules if provided
    created_reminders = []
    if date_item.reminder_rules:
        # Get person's primary comm_identity
        comm_identities = SupabaseQuery.select_active(
            client=db,
            table='comm_identities',
            filters={'person_id': date_item.person_id},
            limit=1
        )

        if not comm_identities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No communication identity found for person"
            )

        comm_identity = comm_identities[0]

        for reminder_rule in date_item.reminder_rules:
            reminder_data = {
                'reminder_rule_id': str(uuid4()),
                'org_id': date_item.org_id,
                'date_item_id': created_date_item['date_item_id'],
                'comm_identity_id': comm_identity['comm_identity_id'],
                'reminder_type': reminder_rule.reminder_type,
                'lead_time_days': reminder_rule.lead_time_days,
                'scheduled_datetime': reminder_rule.scheduled_datetime,
                'metadata_jsonb': {
                    'created_by': 'date_items_api',
                    'channel_type': reminder_rule.channel_type
                },
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Calculate scheduled_datetime for lead_time type
            if reminder_rule.reminder_type == 'lead_time' and reminder_rule.lead_time_days:
                from datetime import timedelta
                target_date = datetime.fromisoformat(date_item.date_value)
                reminder_date = target_date - timedelta(days=reminder_rule.lead_time_days)
                reminder_data['scheduled_datetime'] = reminder_date.isoformat()

            created_reminder = SupabaseQuery.insert(
                client=db,
                table='reminder_rules',
                data=reminder_data
            )
            created_reminders.append(created_reminder)

    created_date_item['reminder_rules'] = created_reminders
    return created_date_item


@router.put("/date-items/{date_item_id}", response_model=DateItemResponse)
async def update_date_item(
    date_item_id: UUID,
    date_item_update: DateItemUpdate,
    db: Client = Depends(get_db)
):
    """Update date item"""
    existing_date_item = SupabaseQuery.get_by_id(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id
    )

    if not existing_date_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date item not found"
        )

    # Update date_item
    update_data = date_item_update.model_dump(exclude_unset=True)

    # Update next_occurrence if date_value changed
    if 'date_value' in update_data:
        update_data['next_occurrence'] = update_data['date_value']

    updated_date_item = SupabaseQuery.update(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id,
        data=update_data
    )

    # Fetch reminder_rules
    reminder_rules = SupabaseQuery.select_active(
        client=db,
        table='reminder_rules',
        filters={'date_item_id': date_item_id}
    )
    updated_date_item['reminder_rules'] = reminder_rules

    return updated_date_item


@router.delete("/date-items/{date_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_date_item(date_item_id: UUID, db: Client = Depends(get_db)):
    """Soft delete date item and associated reminder rules"""

    # Verify date item exists
    existing_date_item = SupabaseQuery.get_by_id(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id
    )

    if not existing_date_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date item not found"
        )

    # Soft delete the date item
    deleted = SupabaseQuery.soft_delete(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id
    )

    # Soft delete associated reminder_rules
    reminder_rules = SupabaseQuery.select_active(
        client=db,
        table='reminder_rules',
        filters={'date_item_id': date_item_id}
    )

    for reminder in reminder_rules:
        SupabaseQuery.soft_delete(
            client=db,
            table='reminder_rules',
            id_column='reminder_rule_id',
            id_value=reminder['reminder_rule_id']
        )

    return None


@router.get("/date-items/{date_item_id}/reminders", response_model=List[ReminderRuleResponse])
async def list_date_item_reminders(date_item_id: UUID, db: Client = Depends(get_db)):
    """Get all reminder rules for a date item"""

    # Verify date item exists
    date_item = SupabaseQuery.get_by_id(
        client=db,
        table='date_items',
        id_column='date_item_id',
        id_value=date_item_id
    )

    if not date_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date item not found"
        )

    reminder_rules = SupabaseQuery.select_active(
        client=db,
        table='reminder_rules',
        filters={'date_item_id': date_item_id}
    )

    return reminder_rules
