import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Literal, Union

from beanie import Document, Insert, Replace, before_event
from json_advanced import dumps
from pydantic import BaseModel, Field
from singleton import Singleton
from utils import aionetwork, basic


class BaseEntity(Document):
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = False
    metadata: dict[str, Any] | None = None

    class Settings:
        keep_nulls = False
        validate_on_save = True

    @property
    def create_exclude_set(self) -> list[str]:
        return ["uid", "created_at", "updated_at", "is_deleted"]

    @property
    def create_field_set(self) -> list:
        return []

    @property
    def update_exclude_set(self) -> list:
        return ["uid", "created_at", "updated_at"]

    @property
    def update_field_set(self) -> list:
        return []

    def model_dump_create(self):
        assert not (self.create_exclude_set and self.create_field_set)
        if self.create_field_set:
            return self.model_dump(fields=self.create_field_set)

        return self.model_dump(exclude=self.create_exclude_set)

    def model_dump_update(self):
        assert not (self.update_exclude_set and self.update_field_set)
        if self.update_field_set:
            return self.model_dump(fields=self.update_field_set)

        return self.model_dump(exclude=self.update_exclude_set)

    def expired(self, days: int = 3):
        return (datetime.now() - self.updated_at).days > days

    @before_event([Insert, Replace])
    async def pre_save(self):
        self.updated_at = datetime.now()

    @classmethod
    def get_query(cls, *args, **kwargs):
        query = cls.find(cls.is_deleted == False)
        return query

    @classmethod
    async def get_item(cls, uid, *args, **kwargs) -> "BaseEntity":
        query = cls.get_query(*args, **kwargs).find(cls.uid == uid)
        items = await query.to_list()
        if not items:
            return None
        return items[0]


class OwnedEntity(BaseEntity):
    user_id: uuid.UUID

    @property
    def create_exclude_set(self) -> list[str]:
        return ["uid", "created_at", "updated_at", "is_deleted", "user_id"]

    @property
    def update_exclude_set(self) -> list[str]:
        return ["uid", "created_at", "updated_at", "user_id"]

    def model_dump_create(self, user_id: uuid.UUID):
        assert not (self.create_exclude_set and self.create_field_set)
        if self.create_field_set:
            return self.model_dump(fields=self.create_field_set) | {"user_id": user_id}

        return self.model_dump(exclude=self.create_exclude_set) | {"user_id": user_id}

    def model_dump_update(self):
        assert not (self.update_exclude_set and self.update_field_set)
        if self.update_field_set:
            return self.model_dump(fields=self.update_field_set)

        return self.model_dump(exclude=self.update_exclude_set)

    @classmethod
    def get_query(cls, user, *args, **kwargs):
        query = cls.find(cls.is_deleted == False, cls.user_id == user.uid)
        return query

    @classmethod
    async def get_item(cls, uid, user, *args, **kwargs) -> "OwnedEntity":
        query = cls.get_query(user, *args, **kwargs).find(cls.uid == uid)
        items = await query.to_list()
        if not items:
            return None
        return items[0]


class SignalRegistry(metaclass=Singleton):
    def __init__(self):
        self.signal_map: dict[
            str,
            list[Callable[..., None] | Callable[..., Coroutine[Any, Any, None]]],
        ] = {}


class StepStatus(str, Enum):
    none = "null"
    draft = "draft"
    init = "init"
    processing = "processing"
    paused = "paused"
    done = "done"
    error = "error"


class TaskLogRecord(BaseModel):
    reported_at: datetime = Field(default_factory=datetime.now)
    message: str
    task_status: StepStatus
    duration: int = 0
    data: dict | None = None

    def __eq__(self, other):
        if isinstance(other, TaskLogRecord):
            return (
                self.reported_at == other.reported_at
                and self.message == other.message
                and self.task_status == other.task_status
                and self.duration == other.duration
                and self.data == other.data
            )
        return False

    def __hash__(self):
        return hash((self.reported_at, self.message, self.task_status, self.duration))


class TaskReference(BaseModel):
    task_id: uuid.UUID
    task_type: str

    def __eq__(self, other):
        if isinstance(other, TaskReference):
            return self.task_id == other.task_id and self.task_type == other.task_type
        return False

    def __hash__(self):
        return hash((self.task_id, self.task_type))

    async def get_task_item(self) -> BaseEntity | None:
        task_classes = {
            subclass.__name__: subclass
            for subclass in basic.get_all_subclasses(TaskMixin)
            if issubclass(subclass, BaseEntity)
        }
        # task_classes = self._get_all_task_classes()

        task_class = task_classes.get(self.task_type)
        if not task_class:
            raise ValueError(f"Task type {self.task_type} is not supported.")

        task_item = await task_class.find_one(task_class.uid == self.task_id)
        if not task_item:
            raise ValueError(
                f"No task found with id {self.task_id} of type {self.task_type}."
            )

        return task_item


class TaskReferenceList(BaseModel):
    tasks: list[Union[TaskReference, "TaskReferenceList"]] = []
    mode: Literal["serial", "parallel"] = "serial"

    async def list_processing(self):
        task_items = [task.get_task_item() for task in self.tasks]
        match self.mode:
            case "serial":
                for task_item in task_items:
                    await task_item.start_processing()
            case "parallel":
                await asyncio.gather(*[task.start_processing() for task in task_items])


class TaskMixin:
    task_status: StepStatus = StepStatus.draft
    task_report: str | None = None
    task_progress: int = -1
    task_logs: list[TaskLogRecord] = []
    task_references: TaskReferenceList | None = None

    @classmethod
    def signals(cls):
        registry = SignalRegistry()
        if cls.__name__ not in registry.signal_map:
            registry.signal_map[cls.__name__] = []
        return registry.signal_map[cls.__name__]

    @classmethod
    def add_signal(
        cls,
        signal: Callable[..., None] | Callable[..., Coroutine[Any, Any, None]],
    ):
        cls.signals().append(signal)

    @classmethod
    async def emit_signals(cls, task_instance, **kwargs):
        if task_instance.metadata:
            webhook = task_instance.metadata.get(
                "webhook"
            ) or task_instance.metadata.get("webhook_url")
            if webhook:
                task_dict = task_instance.model_dump()
                task_dict.update({"task_type": task_instance.__class__.__name__})
                task_dict.update(kwargs)
                webhook_signals = [
                    basic.try_except_wrapper(aionetwork.aio_request)(
                        method="post",
                        url=webhook,
                        headers={"Content-Type": "application/json"},
                        data=dumps(task_dict),
                    )
                ]
        else:
            webhook_signals = []

        signals = webhook_signals + [
            (
                basic.try_except_wrapper(signal)(task_instance)
                if asyncio.iscoroutinefunction(signal)
                else basic.try_except_wrapper(signal)(task_instance)
                # asyncio.to_thread(signal, task_instance)
            )
            for signal in cls.signals()
        ]

        await asyncio.gather(*signals)

    async def save_status(
        self,
        status: Literal["draft", "init", "processing", "done", "error"],
        **kwargs,
    ):
        self.task_status = status
        await self.add_log(
            TaskLogRecord(
                task_status=self.task_status,
                message=f"Status changed to {status}",
            ),
            **kwargs,
        )

    async def add_reference(self, task_id: uuid.UUID, **kwargs):
        self.task_references.append(task_id)
        await self.add_log(
            TaskLogRecord(
                task_status=self.task_status,
                message=f"Added reference to task {task_id}",
            ),
            **kwargs,
        )

    async def save_report(self, report: str, **kwargs):
        self.task_report = report
        await self.add_log(
            TaskLogRecord(
                task_status=self.task_status,
                message=report,
            ),
            **kwargs,
        )

    async def add_log(self, log_record: TaskLogRecord, *, emit: bool = True, **kwargs):
        self.task_logs.append(log_record)
        if emit:
            # await self.emit_signals(self)
            await self.save_and_emit()

    async def start_processing(self):
        if self.task_references is None:
            raise NotImplementedError("Subclasses should implement this method")

        await self.task_references.list_processing()

    async def save_and_emit(self):
        try:
            await asyncio.gather(self.save(), self.emit_signals(self))
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    async def update_and_emit(self, **kwargs):
        if kwargs.get("task_status") == "done":
            kwargs["task_progress"] = kwargs.get("task_progress", 100)
            # kwargs["task_report"] = kwargs.get("task_report")

        for key, value in kwargs.items():
            setattr(self, key, value)

        if kwargs.get("task_report"):
            await self.add_log(
                TaskLogRecord(
                    task_status=self.task_status,
                    message=kwargs["task_report"],
                ),
                emit=False,
            )

        await self.save_and_emit()


class TaskBaseEntity(TaskMixin, BaseEntity):
    pass


class TaskOwnedEntity(TaskMixin, OwnedEntity):
    pass


class Language(str, Enum):
    English = "English"
    Persian = "Persian"
