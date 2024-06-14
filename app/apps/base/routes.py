from typing import Any, Generic, Type, TypeVar

from core.exceptions import BaseHTTPException
from fastapi import APIRouter, BackgroundTasks, Request
from server.config import Settings

from .handlers import create_dto, update_dto
from .models import BaseEntity, TaskBaseEntity

# Define a type variable
T = TypeVar("T", bound=BaseEntity)
TE = TypeVar("TE", bound=TaskBaseEntity)


class AbstractBaseRouter(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        user_dependency: Any,
        *args,
        resource_name: str = None,
        tags: list[str] = None,
        **kwargs,
    ):
        self.model = model
        self.user_dependency = user_dependency
        if resource_name is None:
            resource_name = f"/{model.__name__.lower()}s"
        if tags is None:
            tags = [model.__name__]
        self.router = APIRouter(prefix=resource_name, tags=tags, **kwargs)

        self.router.add_api_route(
            "/",
            self.list_items,
            methods=["GET"],
            response_model=list[self.model],
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.retrieve_item,
            methods=["GET"],
            response_model=self.model,
        )
        self.router.add_api_route(
            "/",
            self.create_item,
            methods=["POST"],
            response_model=self.model,
            status_code=201,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.update_item,
            methods=["PATCH"],
            response_model=self.model,
        )
        self.router.add_api_route(
            "/{uid:uuid}",
            self.delete_item,
            methods=["DELETE"],
            response_model=self.model,
        )

    async def get_user(self, request: Request, *args, **kwargs):
        if self.user_dependency is None:
            return None
        return await self.user_dependency(request)

    async def list_items(
        self,
        request: Request,
        offset: int = 0,
        limit: int = 10,
    ):
        user = await self.get_user(request)
        limit = max(limit, Settings.page_max_limit)

        items_query = (
            self.model.get_query(user=user)
            .sort("-created_at")
            .skip(offset)
            .limit(limit)
        )
        items = await items_query.to_list()
        return items

    async def retrieve_item(
        self,
        request: Request,
        uid,
    ):
        user = await self.get_user(request)
        item = await self.model.get_item(uid, user)
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        return item

    async def create_item(
        self,
        request: Request,
    ):
        user = await self.get_user(request)
        item = await create_dto(self.model)(request, user)

        await item.save()
        return item

    async def update_item(
        self,
        request: Request,
        uid,
    ):
        user = await self.get_user(request)
        item = await update_dto(self.model)(request, user)
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        await item.save()
        return item

    async def delete_item(
        self,
        request: Request,
        uid,
    ):
        user = await self.get_user(request)
        item = await self.model.get_item(uid, user)
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        item.is_deleted = True
        await item.save()
        return item


class AbstractTaskRouter(AbstractBaseRouter[TE]):
    def __init__(self, model: Type[TE], user_dependency: Any, *args, **kwargs):
        super().__init__(model, user_dependency, *args, **kwargs)
        self.router.add_api_route(
            "/{uid:uuid}/start",
            self.start,
            methods=["POST"],
            response_model=self.model,
        )

    async def start(self, request: Request, uid, background_tasks: BackgroundTasks):
        user = await self.get_user(request)
        item = await self.model.get_item(uid, user)
        if item is None:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message=f"{self.model.__name__.capitalize()} not found",
            )
        background_tasks.add_task(item.start_processing)
        return item.model_dump()
