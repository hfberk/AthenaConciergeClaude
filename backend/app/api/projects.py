"""Project API endpoints"""

from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from pydantic import BaseModel
from datetime import date, datetime

from app.database import get_db
from app.utils.supabase_helpers import SupabaseQuery

router = APIRouter()


# Pydantic schemas
class ProjectBase(BaseModel):
    title: str
    description: str | None = None
    priority: int = 3
    status: str = "new"
    due_date: date | None = None


class ProjectCreate(ProjectBase):
    org_id: UUID
    person_id: UUID
    assigned_to_account_id: UUID | None = None
    source_date_item_id: UUID | None = None


class ProjectResponse(ProjectBase):
    project_id: UUID
    org_id: UUID
    person_id: UUID
    assigned_to_account_id: UUID | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"
    due_date: date | None = None


class TaskCreate(TaskBase):
    project_id: UUID
    parent_id: UUID | None = None
    assigned_to_account_id: UUID | None = None


class TaskResponse(TaskBase):
    task_id: UUID
    project_id: UUID
    parent_id: UUID | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    org_id: UUID,
    person_id: UUID | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """List projects with optional filtering"""
    filters = {'org_id': org_id}
    if person_id:
        filters['person_id'] = person_id
    if status:
        filters['status'] = status

    projects = SupabaseQuery.select_active(
        client=db,
        table='projects',
        filters=filters,
        order_by='priority,created_at.desc',
        limit=limit,
        offset=skip
    )

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: Client = Depends(get_db)):
    """Get project by ID"""
    project = SupabaseQuery.get_by_id(
        client=db,
        table='projects',
        id_column='project_id',
        id_value=project_id
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: Client = Depends(get_db)):
    """Create new project"""
    project_data = project.model_dump()
    project_data['project_id'] = uuid4()
    project_data['created_at'] = datetime.utcnow().isoformat()
    project_data['updated_at'] = datetime.utcnow().isoformat()

    created_project = SupabaseQuery.insert(
        client=db,
        table='projects',
        data=project_data
    )

    return created_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectBase,
    db: Client = Depends(get_db)
):
    """Update project"""
    existing_project = SupabaseQuery.get_by_id(
        client=db,
        table='projects',
        id_column='project_id',
        id_value=project_id
    )

    if not existing_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    update_data = project_update.model_dump(exclude_unset=True)
    updated_project = SupabaseQuery.update(
        client=db,
        table='projects',
        id_column='project_id',
        id_value=project_id,
        data=update_data
    )

    return updated_project


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_project_tasks(project_id: UUID, db: Client = Depends(get_db)):
    """List tasks for a project"""
    tasks = SupabaseQuery.select_active(
        client=db,
        table='tasks',
        filters={'project_id': project_id},
        order_by='sort_order'
    )

    return tasks


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: UUID, task: TaskCreate, db: Client = Depends(get_db)):
    """Create new task"""
    # Verify project exists
    project = SupabaseQuery.get_by_id(
        client=db,
        table='projects',
        id_column='project_id',
        id_value=project_id
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    task_data = task.model_dump()
    task_data['task_id'] = uuid4()
    task_data['org_id'] = project['org_id']
    task_data['created_at'] = datetime.utcnow().isoformat()
    task_data['updated_at'] = datetime.utcnow().isoformat()

    created_task = SupabaseQuery.insert(
        client=db,
        table='tasks',
        data=task_data
    )

    return created_task
