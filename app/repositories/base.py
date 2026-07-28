import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel as PydanticBaseModel
from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PydanticBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PydanticBaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic CRUD repository with async Tortoise ORM."""

    def __init__(self, model: Type[ModelType], session: Any = None):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Fetch a single record by its UUID."""
        return await self.model.get_or_none(id=id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        return await self.model.all().offset(skip).limit(limit)

    async def create(self, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """Create a new database record from a Pydantic schema or dict."""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)

        return await self.model.create(**create_data)

    async def update(
        self,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing database record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db_obj.save()
        return db_obj

    async def delete(self, id: uuid.UUID) -> Optional[ModelType]:
        """Delete a record by UUID."""
        db_obj = await self.get(id)
        if db_obj:
            await db_obj.delete()
        return db_obj
