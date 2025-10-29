"""Person API endpoints"""

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
    db: Client = Depends(get_db)
):
    """List persons with optional filtering"""
    filters = {'org_id': org_id}
    if person_type:
        filters['person_type'] = person_type

    persons = SupabaseQuery.select_active(
        client=db,
        table='persons',
        filters=filters,
        limit=limit,
        offset=skip
    )

    return persons


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(person_id: UUID, db: Client = Depends(get_db)):
    """Get person by ID"""
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

    return person


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(person: PersonCreate, db: Client = Depends(get_db)):
    """Create new person"""
    person_data = person.model_dump()
    # Add required fields
    person_data['person_id'] = uuid4()
    person_data['created_at'] = datetime.utcnow().isoformat()
    person_data['updated_at'] = datetime.utcnow().isoformat()

    created_person = SupabaseQuery.insert(
        client=db,
        table='persons',
        data=person_data
    )

    return created_person


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: UUID,
    person_update: PersonBase,
    db: Client = Depends(get_db)
):
    """Update person"""
    # Check if person exists
    existing_person = SupabaseQuery.get_by_id(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id
    )

    if not existing_person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    # Update person
    update_data = person_update.model_dump(exclude_unset=True)
    updated_person = SupabaseQuery.update(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id,
        data=update_data
    )

    return updated_person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: UUID, db: Client = Depends(get_db)):
    """Soft delete person"""
    deleted = SupabaseQuery.soft_delete(
        client=db,
        table='persons',
        id_column='person_id',
        id_value=person_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    return None
