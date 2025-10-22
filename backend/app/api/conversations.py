"""Conversation API endpoints"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.communication import Conversation, Message

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
    db: Session = Depends(get_db)
):
    """List conversations"""
    query = db.query(Conversation).filter(
        Conversation.org_id == org_id,
        Conversation.deleted_at.is_(None)
    )

    if person_id:
        query = query.filter(Conversation.person_id == person_id)

    conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    """Get conversation by ID"""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.deleted_at.is_(None)
    ).first()

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
    db: Session = Depends(get_db)
):
    """List messages in a conversation"""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.deleted_at.is_(None)
    ).order_by(Message.created_at).offset(skip).limit(limit).all()

    return messages
