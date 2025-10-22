"""Agent API endpoints"""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.agents.orchestrator import OrchestratorAgent
from app.services.context_builder import ContextBuilder

router = APIRouter()


# Pydantic schemas
class ChatRequest(BaseModel):
    person_id: UUID
    message: str
    conversation_id: UUID | None = None
    channel_type: str = "web"


class ChatResponse(BaseModel):
    response: str
    conversation_id: UUID
    message_id: UUID


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Process a message from a client and return AI response.
    This is the main entry point for agent interactions.
    """
    from app.models.identity import Person
    from app.models.communication import Conversation, Message
    from datetime import datetime

    # Verify person exists
    person = db.query(Person).filter(
        Person.person_id == request.person_id,
        Person.deleted_at.is_(None)
    ).first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == request.conversation_id,
            Conversation.deleted_at.is_(None)
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        conversation = Conversation(
            org_id=person.org_id,
            person_id=person.person_id,
            channel_type=request.channel_type,
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save inbound message
    inbound_message = Message(
        org_id=person.org_id,
        conversation_id=conversation.conversation_id,
        direction="inbound",
        sender_person_id=person.person_id,
        content_text=request.message
    )
    db.add(inbound_message)
    db.commit()

    # Build context for AI
    context_builder = ContextBuilder(db)
    context = context_builder.build_context(person.person_id, conversation.conversation_id)

    # Process with Orchestrator Agent
    orchestrator = OrchestratorAgent(db)
    ai_response = orchestrator.process_message(
        user_message=request.message,
        person=person,
        conversation=conversation,
        context=context
    )

    # Save outbound message
    outbound_message = Message(
        org_id=person.org_id,
        conversation_id=conversation.conversation_id,
        direction="outbound",
        agent_name="orchestrator",
        content_text=ai_response
    )
    db.add(outbound_message)
    db.commit()
    db.refresh(outbound_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        response=ai_response,
        conversation_id=conversation.conversation_id,
        message_id=outbound_message.message_id
    )


@router.get("/health")
async def agent_health():
    """Check agent system health"""
    return {
        "status": "healthy",
        "agents": ["orchestrator", "retrieval", "recommendation", "reminder", "project_management", "data_capture"]
    }
