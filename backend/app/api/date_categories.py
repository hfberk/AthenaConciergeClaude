"""Date Categories API endpoints"""

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
class DateCategoryBase(BaseModel):
    category_name: str
    icon: str | None = None
    color: str | None = None
    schema_jsonb: dict = {}


class DateCategoryCreate(DateCategoryBase):
    org_id: UUID


class DateCategoryResponse(DateCategoryBase):
    category_id: UUID
    org_id: UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/date-categories", response_model=List[DateCategoryResponse])
async def list_date_categories(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Client = Depends(get_db)
):
    """List date categories for an organization"""
    categories = SupabaseQuery.select_active(
        client=db,
        table='date_categories',
        filters={'org_id': org_id},
        order_by='category_name',
        limit=limit,
        offset=skip
    )

    return categories


@router.get("/date-categories/{category_id}", response_model=DateCategoryResponse)
async def get_date_category(category_id: UUID, db: Client = Depends(get_db)):
    """Get date category by ID"""
    category = SupabaseQuery.get_by_id(
        client=db,
        table='date_categories',
        id_column='category_id',
        id_value=category_id
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date category not found"
        )

    return category


@router.post("/date-categories", response_model=DateCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_date_category(category: DateCategoryCreate, db: Client = Depends(get_db)):
    """Create new date category"""
    category_data = category.model_dump()
    category_data['category_id'] = uuid4()
    category_data['created_at'] = datetime.utcnow().isoformat()
    category_data['updated_at'] = datetime.utcnow().isoformat()

    created_category = SupabaseQuery.insert(
        client=db,
        table='date_categories',
        data=category_data
    )

    return created_category


@router.put("/date-categories/{category_id}", response_model=DateCategoryResponse)
async def update_date_category(
    category_id: UUID,
    category_update: DateCategoryBase,
    db: Client = Depends(get_db)
):
    """Update date category"""
    existing_category = SupabaseQuery.get_by_id(
        client=db,
        table='date_categories',
        id_column='category_id',
        id_value=category_id
    )

    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date category not found"
        )

    update_data = category_update.model_dump(exclude_unset=True)
    updated_category = SupabaseQuery.update(
        client=db,
        table='date_categories',
        id_column='category_id',
        id_value=category_id,
        data=update_data
    )

    return updated_category


@router.delete("/date-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_date_category(category_id: UUID, db: Client = Depends(get_db)):
    """Soft delete date category"""
    # Check if any date_items use this category
    date_items = SupabaseQuery.select_active(
        client=db,
        table='date_items',
        filters={'category_id': category_id},
        limit=1
    )

    if date_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that is in use by date items"
        )

    deleted = SupabaseQuery.soft_delete(
        client=db,
        table='date_categories',
        id_column='category_id',
        id_value=category_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Date category not found"
        )

    return None
