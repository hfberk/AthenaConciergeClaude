"""Dashboard API endpoints - aggregated data for client profiles"""

from typing import List, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery

router = APIRouter()


# Pydantic schemas
class ConversationSummary(BaseModel):
    conversation_id: UUID
    channel_type: str
    last_message_preview: str
    last_message_at: str
    message_count: int


class UpcomingDateItem(BaseModel):
    date_item_id: UUID
    title: str
    date_value: str
    next_occurrence: str | None
    category_name: str
    category_icon: str | None
    days_until: int
    reminder_count: int


class ActiveProjectSummary(BaseModel):
    project_id: UUID
    title: str
    status: str
    priority: int
    due_date: str | None
    total_tasks: int
    completed_tasks: int
    completion_percentage: int


class RecommendationSummary(BaseModel):
    recommendation_id: UUID
    vendor_name: str | None
    venue_name: str | None
    category: str
    notes: str | None
    created_at: str


class ActivityItem(BaseModel):
    activity_type: str  # conversation, project, date_item, reminder, recommendation
    title: str
    description: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class PersonDashboard(BaseModel):
    person: Dict[str, Any]
    recent_conversations: List[ConversationSummary]
    upcoming_dates: List[UpcomingDateItem]
    active_projects: List[ActiveProjectSummary]
    recent_recommendations: List[RecommendationSummary]
    stats: Dict[str, int]


@router.get("/persons/{person_id}/dashboard")
async def get_person_dashboard(
    person_id: UUID,
    db: Client = Depends(get_db)
) -> PersonDashboard:
    """
    Get comprehensive dashboard data for a person

    Includes:
    - Profile info
    - Recent conversations (last 5)
    - Upcoming dates (next 5)
    - Active projects (current projects with task progress)
    - Recent recommendations (last 5)
    - Stats summary
    """
    # Get person
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Get recent conversations
    conversations = SupabaseQuery.select_active(
        client=db,
        table='conversations',
        filters={'person_id': person_id},
        order_by='updated_at.desc',
        limit=5
    )

    recent_conversations = []
    for conv in conversations:
        # Get message count and last message
        messages = SupabaseQuery.select_active(
            client=db,
            table='messages',
            filters={'conversation_id': conv['conversation_id']},
            order_by='created_at.desc',
            limit=1
        )

        last_message = messages[0] if messages else None

        # Count total messages (approximate)
        all_messages = SupabaseQuery.select_active(
            client=db,
            table='messages',
            filters={'conversation_id': conv['conversation_id']},
            limit=100
        )

        recent_conversations.append({
            'conversation_id': conv['conversation_id'],
            'channel_type': conv['channel_type'],
            'last_message_preview': last_message['content_text'][:100] + '...' if last_message else '',
            'last_message_at': last_message['created_at'] if last_message else conv['updated_at'],
            'message_count': len(all_messages)
        })

    # Get upcoming dates
    date_items = SupabaseQuery.select_active(
        client=db,
        table='date_items',
        filters={'person_id': person_id},
        order_by='next_occurrence',
        limit=20
    )

    # Filter for upcoming only and calculate days_until
    today = date.today()
    upcoming_dates = []

    for item in date_items:
        next_occ = item.get('next_occurrence') or item.get('date_value')
        if not next_occ:
            continue

        next_date = date.fromisoformat(next_occ)
        if next_date >= today:
            days_until = (next_date - today).days

            # Get category
            category = SupabaseQuery.get_by_id(
                client=db,
                table='date_categories',
                id_column='category_id',
                id_value=item['category_id']
            )

            # Count reminders
            reminders = SupabaseQuery.select_active(
                client=db,
                table='reminder_rules',
                filters={'date_item_id': item['date_item_id']}
            )

            upcoming_dates.append({
                'date_item_id': item['date_item_id'],
                'title': item['title'],
                'date_value': item['date_value'],
                'next_occurrence': next_occ,
                'category_name': category.get('category_name') if category else 'General',
                'category_icon': category.get('icon') if category else None,
                'days_until': days_until,
                'reminder_count': len(reminders)
            })

    # Sort by days_until and take top 5
    upcoming_dates.sort(key=lambda x: x['days_until'])
    upcoming_dates = upcoming_dates[:5]

    # Get active projects
    projects = SupabaseQuery.select_active(
        client=db,
        table='projects',
        filters={'person_id': person_id},
        order_by='priority,created_at.desc',
        limit=10
    )

    active_projects = []
    for project in projects:
        # Skip completed projects
        if project['status'] in ['completed', 'cancelled']:
            continue

        # Get tasks
        tasks = SupabaseQuery.select_active(
            client=db,
            table='tasks',
            filters={'project_id': project['project_id']}
        )

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'done'])
        completion_percentage = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        active_projects.append({
            'project_id': project['project_id'],
            'title': project['title'],
            'status': project['status'],
            'priority': project['priority'],
            'due_date': str(project['due_date']) if project.get('due_date') else None,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_percentage': completion_percentage
        })

    # Get recent recommendations (linked through projects)
    recent_recommendations = []
    if projects:
        # Get recommendations for this person's projects
        project_ids = [p['project_id'] for p in projects]

        for project_id in project_ids[:5]:  # Limit to 5 projects
            recs = SupabaseQuery.select_active(
                client=db,
                table='recommendations',
                filters={'project_id': project_id},
                order_by='created_at.desc',
                limit=2
            )

            for rec in recs:
                # Get item name based on item_type
                item_name = None
                if rec.get('item_type') == 'vendor' and rec.get('item_id'):
                    item = SupabaseQuery.get_by_id(
                        client=db,
                        table='vendors',
                        id_column='vendor_id',
                        id_value=rec['item_id']
                    )
                    item_name = item.get('vendor_name') if item else None
                elif rec.get('item_type') == 'venue' and rec.get('item_id'):
                    item = SupabaseQuery.get_by_id(
                        client=db,
                        table='venues',
                        id_column='venue_id',
                        id_value=rec['item_id']
                    )
                    item_name = item.get('venue_name') if item else None
                elif rec.get('item_type') == 'restaurant' and rec.get('item_id'):
                    item = SupabaseQuery.get_by_id(
                        client=db,
                        table='restaurants',
                        id_column='restaurant_id',
                        id_value=rec['item_id']
                    )
                    item_name = item.get('restaurant_name') if item else None

                recent_recommendations.append({
                    'recommendation_id': rec['recommendation_id'],
                    'vendor_name': item_name if rec.get('item_type') == 'vendor' else None,
                    'venue_name': item_name if rec.get('item_type') == 'venue' else None,
                    'category': rec.get('item_type', 'general'),
                    'notes': rec.get('rationale_text'),
                    'created_at': rec['created_at']
                })

        # Sort by created_at and take most recent 5
        recent_recommendations.sort(key=lambda x: x['created_at'], reverse=True)
        recent_recommendations = recent_recommendations[:5]

    # Calculate stats
    stats = {
        'total_conversations': len(conversations),
        'total_upcoming_dates': len(upcoming_dates),
        'total_active_projects': len(active_projects),
        'total_recommendations': len(recent_recommendations)
    }

    return {
        'person': person,
        'recent_conversations': recent_conversations,
        'upcoming_dates': upcoming_dates,
        'active_projects': active_projects,
        'recent_recommendations': recent_recommendations,
        'stats': stats
    }


@router.get("/persons/{person_id}/upcoming", response_model=List[UpcomingDateItem])
async def get_upcoming_dates(
    person_id: UUID,
    days_ahead: int = 30,
    db: Client = Depends(get_db)
):
    """Get upcoming date items for a person within specified days"""
    # Verify person exists
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Get all date items
    date_items = SupabaseQuery.select_active(
        client=db,
        table='date_items',
        filters={'person_id': person_id}
    )

    # Filter for upcoming within days_ahead
    today = date.today()
    cutoff_date = today + timedelta(days=days_ahead)
    upcoming_dates = []

    for item in date_items:
        next_occ = item.get('next_occurrence') or item.get('date_value')
        if not next_occ:
            continue

        next_date = date.fromisoformat(next_occ)
        if today <= next_date <= cutoff_date:
            days_until = (next_date - today).days

            # Get category
            category = SupabaseQuery.get_by_id(
                client=db,
                table='date_categories',
                id_column='category_id',
                id_value=item['category_id']
            )

            # Count reminders
            reminders = SupabaseQuery.select_active(
                client=db,
                table='reminder_rules',
                filters={'date_item_id': item['date_item_id']}
            )

            upcoming_dates.append({
                'date_item_id': item['date_item_id'],
                'title': item['title'],
                'date_value': item['date_value'],
                'next_occurrence': next_occ,
                'category_name': category.get('category_name') if category else 'General',
                'category_icon': category.get('icon') if category else None,
                'days_until': days_until,
                'reminder_count': len(reminders)
            })

    # Sort by days_until
    upcoming_dates.sort(key=lambda x: x['days_until'])

    return upcoming_dates


@router.get("/persons/{person_id}/activity", response_model=List[ActivityItem])
async def get_person_activity(
    person_id: UUID,
    limit: int = 50,
    db: Client = Depends(get_db)
):
    """
    Get unified activity feed for a person

    Combines conversations, projects, date items, reminders into chronological feed
    """
    # Verify person exists
    person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id
    )

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    activities = []

    # Get conversations
    conversations = SupabaseQuery.select_active(
        client=db,
        table='conversations',
        filters={'person_id': person_id},
        order_by='created_at.desc',
        limit=20
    )

    for conv in conversations:
        activities.append({
            'activity_type': 'conversation',
            'title': f"Conversation via {conv['channel_type']}",
            'description': conv.get('subject', 'New conversation started'),
            'timestamp': conv['created_at'],
            'metadata': {'conversation_id': conv['conversation_id']}
        })

    # Get projects
    projects = SupabaseQuery.select_active(
        client=db,
        table='projects',
        filters={'person_id': person_id},
        order_by='created_at.desc',
        limit=20
    )

    for project in projects:
        activities.append({
            'activity_type': 'project',
            'title': f"Project: {project['title']}",
            'description': f"Status: {project['status']}",
            'timestamp': project['created_at'],
            'metadata': {'project_id': project['project_id']}
        })

    # Get date items
    date_items = SupabaseQuery.select_active(
        client=db,
        table='date_items',
        filters={'person_id': person_id},
        order_by='created_at.desc',
        limit=20
    )

    for item in date_items:
        activities.append({
            'activity_type': 'date_item',
            'title': f"Important Date: {item['title']}",
            'description': f"Date: {item['date_value']}",
            'timestamp': item['created_at'],
            'metadata': {'date_item_id': item['date_item_id']}
        })

    # Sort all activities by timestamp (desc)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return activities[:limit]
