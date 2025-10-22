"""Project API endpoints"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models.projects import Project, Task

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
    db: Session = Depends(get_db)
):
    """List projects with optional filtering"""
    query = db.query(Project).filter(
        Project.org_id == org_id,
        Project.deleted_at.is_(None)
    )

    if person_id:
        query = query.filter(Project.person_id == person_id)

    if status:
        query = query.filter(Project.status == status)

    projects = query.order_by(Project.priority, Project.created_at.desc()).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get project by ID"""
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create new project"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectBase,
    db: Session = Depends(get_db)
):
    """Update project"""
    db_project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()

    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    for key, value in project_update.model_dump(exclude_unset=True).items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_project_tasks(project_id: UUID, db: Session = Depends(get_db)):
    """List tasks for a project"""
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.deleted_at.is_(None)
    ).order_by(Task.sort_order).all()

    return tasks


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: UUID, task: TaskCreate, db: Session = Depends(get_db)):
    """Create new task"""
    # Verify project exists
    project = db.query(Project).filter(
        Project.project_id == project_id,
        Project.deleted_at.is_(None)
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    db_task = Task(org_id=project.org_id, **task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
