"""Supabase query helper functions"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from supabase import Client


def to_dict(data: Any) -> Dict:
    """Convert Supabase response data to dict"""
    if hasattr(data, 'data'):
        return data.data
    return data


def handle_supabase_error(func):
    """Decorator to handle Supabase API errors"""
    from functools import wraps
    from fastapi import HTTPException, status

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Parse Supabase error
            error_msg = str(e)
            if 'PGRST116' in error_msg or 'not found' in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resource not found"
                )
            elif 'PGRST' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database error: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {error_msg}"
                )
    return wrapper


class SupabaseQuery:
    """Helper class for building Supabase queries with soft delete support"""

    @staticmethod
    def select_active(
        client: Client,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict]:
        """
        Select records excluding soft-deleted items

        Args:
            client: Supabase client
            table: Table name
            columns: Columns to select (default: *)
            filters: Dict of column: value filters
            order_by: Column to order by
            limit: Max records to return
            offset: Number of records to skip

        Returns:
            List of records
        """
        query = client.table(table).select(columns).is_('deleted_at', 'null')

        if filters:
            for key, value in filters.items():
                if isinstance(value, UUID):
                    value = str(value)
                query = query.eq(key, value)

        if order_by:
            # Parse order_by string (e.g., "column.desc" or "column.asc")
            parts = order_by.split('.')
            column = parts[0]
            desc = len(parts) > 1 and parts[1] == 'desc'
            query = query.order(column, desc=desc)

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.range(offset, offset + limit - 1) if limit else query.offset(offset)

        response = query.execute()
        return response.data if response.data else []

    @staticmethod
    def get_by_id(
        client: Client,
        table: str,
        id_value: UUID,
        id_column: str = 'id',
        columns: str = "*"
    ) -> Optional[Dict]:
        """
        Get single record by ID (excluding soft-deleted)

        Args:
            client: Supabase client
            table: Table name
            id_value: ID value (required)
            id_column: Primary key column name (default: 'id')
            columns: Columns to select

        Returns:
            Record dict or None
        """
        response = client.table(table).select(columns).eq(
            id_column, str(id_value)
        ).is_('deleted_at', 'null').execute()

        return response.data[0] if response.data else None

    @staticmethod
    def insert(
        client: Client,
        table: str,
        data: Dict[str, Any]
    ) -> Dict:
        """
        Insert a new record

        Args:
            client: Supabase client
            table: Table name
            data: Record data

        Returns:
            Inserted record
        """
        # Convert UUIDs to strings
        clean_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                clean_data[key] = str(value)
            elif value is None:
                continue  # Skip None values
            else:
                clean_data[key] = value

        response = client.table(table).insert(clean_data).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def update(
        client: Client,
        table: str,
        id_value: UUID,
        data: Dict[str, Any],
        id_column: str = 'id'
    ) -> Optional[Dict]:
        """
        Update a record by ID

        Args:
            client: Supabase client
            table: Table name
            id_value: ID value (required)
            data: Update data
            id_column: Primary key column name (default: 'id')

        Returns:
            Updated record or None
        """
        # Convert UUIDs to strings
        clean_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                clean_data[key] = str(value)
            elif value is not None:
                clean_data[key] = value

        # Add updated_at timestamp
        clean_data['updated_at'] = datetime.utcnow().isoformat()

        response = client.table(table).update(clean_data).eq(
            id_column, str(id_value)
        ).is_('deleted_at', 'null').execute()

        return response.data[0] if response.data else None

    @staticmethod
    def soft_delete(
        client: Client,
        table: str,
        id_value: UUID,
        id_column: str = 'id'
    ) -> bool:
        """
        Soft delete a record by setting deleted_at timestamp

        Args:
            client: Supabase client
            table: Table name
            id_value: ID value (required)
            id_column: Primary key column name (default: 'id')

        Returns:
            True if deleted, False otherwise
        """
        response = client.table(table).update({
            'deleted_at': datetime.utcnow().isoformat()
        }).eq(id_column, str(id_value)).is_('deleted_at', 'null').execute()

        return len(response.data) > 0 if response.data else False
