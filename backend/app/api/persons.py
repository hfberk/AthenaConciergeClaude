"""Person API endpoints"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.identity import Person

router = APIRouter()


# Pydantic schemas
class PersonBase(BaseModel):
    full_name: str
    preferred_name: str | None = None
    person_type: str
    birthday: str | None = None
    timezone: str = "America/New_York"
    metadata_jsonb: dict = {}


class PersonCreate(PersonBase):
    org_id: UUID


class PersonResponse(PersonBase):
    person_id: UUID
    org_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PersonResponse])
async def list_persons(
    org_id: UUID,
    person_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List persons with optional filtering"""
    query = db.query(Person).filter(
        Person.org_id == org_id,
        Person.deleted_at.is_(None)
    )

    if person_type:
        query = query.filter(Person.person_type == person_type)

    persons = query.offset(skip).limit(limit).all()
    return persons


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(person_id: UUID, db: Session = Depends(get_db)):
    """Get person by ID"""
    person = db.query(Person).filter(
        Person.person_id == person_id,
        Person.deleted_at.is_(None)
    ).first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    return person


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(person: PersonCreate, db: Session = Depends(get_db)):
    """Create new person"""
    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    person_update: PersonBase,
    db: Session = Depends(get_db)
):
    """Update person"""
    db_person = db.query(Person).filter(
        Person.person_id == person_id,
        Person.deleted_at.is_(None)
    ).first()

    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    for key, value in person_update.model_dump(exclude_unset=True).items():
        setattr(db_person, key, value)

    db.commit()
    db.refresh(db_person)
    return db_person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: UUID, db: Session = Depends(get_db)):
    """Soft delete person"""
    from datetime import datetime

    db_person = db.query(Person).filter(
        Person.person_id == person_id,
        Person.deleted_at.is_(None)
    ).first()

    if not db_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    db_person.deleted_at = datetime.utcnow()
    db.commit()
    return None
