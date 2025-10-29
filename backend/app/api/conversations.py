"""Conversation API endpoints"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery

router = APIRouter()


# Pydantic schemas
class MessageBase(BaseModel):
    content_text: str
    direction: str


class MessageResponse(MessageBase):
    message_id: UUID
    conversation_id: UUID
    sender_person_id: UUID | None
    agent_name: str | None
    created_at: str

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    conversation_id: UUID
    person_id: UUID
    channel_type: str
    subject: str | None
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    org_id: UUID,
    person_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """List conversations"""
    filters = {'org_id': org_id}
    if person_id:
        filters['person_id'] = person_id

    conversations = SupabaseQuery.select_active(
        client=db,
        table='conversations',
        filters=filters,
        order_by='updated_at.desc',
        limit=limit,
        offset=skip
    )

    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID, db: Client = Depends(get_db)):
    """Get conversation by ID"""
    conversation = SupabaseQuery.get_by_id(
        client=db,
        table='conversations',
        id_column='conversation_id',
        id_value=conversation_id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_conversation_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """List messages in a conversation"""
    messages = SupabaseQuery.select_active(
        client=db,
        table='messages',
        filters={'conversation_id': conversation_id},
        order_by='created_at',
        limit=limit,
        offset=skip
    )

    return messages
