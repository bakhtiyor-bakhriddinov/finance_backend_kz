from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from schemas.base_model import TunedModel
from schemas.users import GetUsers


class Departments(TunedModel):
    id: UUID
    name: str
    is_active: Optional[bool]
    head: Optional[GetUsers] = None
    created_at: Optional[datetime]


class Department(Departments):
    updated_at: Optional[datetime] = None


class CreateDepartment(TunedModel):
    name: str
    user_id: Optional[UUID] = None

    # def __init__(self, /, **kwargs):
    #     # Assign all attributes normally
    #     super().__init__(**kwargs)
    #     for key, value in kwargs.items():
    #         setattr(self, key, value)
    #
    #     # Get attributes from parent classes (Department, Departments)
    #     parent_attrs = set(vars(Department)) | set(vars(Departments))
    #
    #     # Remove inherited attributes, keeping only those in CreateDepartment
    #     for attr in list(self.__dict__):
    #         if attr in parent_attrs:
    #             delattr(self, attr)



class UpdateDepartment(TunedModel):
    id: UUID
    name: Optional[str] = None
    is_active: Optional[bool] = None
    client_id: Optional[UUID] = None
