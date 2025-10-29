"""Agent API endpoints"""

from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery
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
async def chat(request: ChatRequest, db: Client = Depends(get_db)):
    """
    Process a message from a client and return AI response.
    This is the main entry point for agent interactions.
    """
    # Verify person exists
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=request.person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Get or create conversation
    if request.conversation_id:
        conversation = SupabaseQuery.get_by_id(
            client=db,
            table='conversations',
            id_column='conversation_id',
            id_value=request.conversation_id
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        conversation_data = {
            'conversation_id': uuid4(),
            'org_id': person['org_id'],
            'person_id': person['person_id'],
            'channel_type': request.channel_type,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        conversation = SupabaseQuery.insert(
            client=db,
            table='conversations',
            data=conversation_data
        )

    # Save inbound message
    inbound_message_data = {
        'message_id': uuid4(),
        'org_id': person['org_id'],
        'conversation_id': conversation['conversation_id'],
        'direction': 'inbound',
        'sender_person_id': person['person_id'],
        'content_text': request.message,
        'created_at': datetime.utcnow().isoformat()
    }
    SupabaseQuery.insert(
        client=db,
        table='messages',
        data=inbound_message_data
    )

    # Build context for AI
    context_builder = ContextBuilder(db)
    context = context_builder.build_context(person['person_id'], conversation['conversation_id'])

    # Process with Orchestrator Agent
    orchestrator = OrchestratorAgent(db)
    ai_response = orchestrator.process_message(
        user_message=request.message,
        person=person,
        conversation=conversation,
        context=context
    )

    # Save outbound message
    outbound_message_data = {
        'message_id': uuid4(),
        'org_id': person['org_id'],
        'conversation_id': conversation['conversation_id'],
        'direction': 'outbound',
        'agent_name': 'orchestrator',
        'content_text': ai_response,
        'created_at': datetime.utcnow().isoformat()
    }
    outbound_message = SupabaseQuery.insert(
        client=db,
        table='messages',
        data=outbound_message_data
    )

    # Update conversation timestamp
    SupabaseQuery.update(
        client=db,
        table='conversations',
        id_column='conversation_id',
        id_value=UUID(conversation['conversation_id']),
        data={'updated_at': datetime.utcnow().isoformat()}
    )

    return ChatResponse(
        response=ai_response,
        conversation_id=UUID(conversation['conversation_id']),
        message_id=UUID(outbound_message['message_id'])
    )


@router.get("/health")
async def agent_health():
    """Check agent system health"""
    return {
        "status": "healthy",
        "agents": ["orchestrator", "retrieval", "recommendation", "reminder", "project_management", "data_capture"]
    }
