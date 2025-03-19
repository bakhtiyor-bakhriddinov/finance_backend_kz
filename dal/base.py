import re
from datetime import date
from typing import List, Any, Dict

from fastapi_pagination import request
from sqlalchemy import select, inspect, update, delete, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, Session, contains_eager

from models import Requests, Contracts, Files


class BaseDAO:
    model = None  # Устанавливается в дочернем классе

    @classmethod
    async def add(cls, session: Session, **values):
        # Добавить одну запись
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            session.flush()
            # session.refresh(new_instance)
            return new_instance
        except SQLAlchemyError as e:
            session.rollback()
            print("SQLAlchemyError: ", e)
            return None



    @classmethod
    async def add_many(cls, session: Session, instances: List[Dict[str, Any]]):
        new_instances = [cls.model(**values) for values in instances]
        session.add_all(new_instances)
        try:
            # await session.commit()
            session.flush()
            # session.refresh(new_instances)
            return new_instances
        except SQLAlchemyError as e:
            session.rollback()
            print("ACCESSES ERROR: \n", e)
            return None


    @classmethod
    async def get_by_attributes(cls, session: Session, filters: Dict[str, Any] = None, first: bool = False):
        """
        Retrieves records filtered by given attributes.

        :param session: AsyncSession - SQLAlchemy async session.
        :param filters: Dict[str, Any] - Dictionary where keys are column names and values are filter values.
        :param first: bool - Whether to return only the first match.
        :return: Single model instance if `first=True`, else a list of instances.
        """
        try:
            query = select(cls.model)
            if filters is not None:
                query = query.filter_by(**filters)

            result = session.execute(query)
            return result.scalars().first() if first else result.scalars().all()
        except SQLAlchemyError as e:
            print("SQLAlchemyError: \n", e)
            return None


    @classmethod
    async def get_all(cls, session: Session, filters: dict = None):
        try:
            query = select(cls.model)
            if filters is not None:
                conditions = []
                for k, v in filters.items():
                    if k == "status" and isinstance(v, str):
                        v = [int(i) for i in re.findall(r"\d+", str(v))]

                    column = getattr(cls.model, k, None)

                    # if k == "created_at_start" or k == "created_at_finish":
                    #     column = getattr(cls.model, "created_at", None)

                    if column is not None:
                        if k == "status":
                            if isinstance(v, list):
                                conditions.append(column.in_(v))
                            else:
                                conditions.append(column != v)
                        elif k == "payment_time":
                            if v is None:
                                conditions.append(column.isnot(v))
                            else:
                                conditions.append(func.date(column) == v)
                        elif k == "created_at":
                            conditions.append(func.date(column) == v)
                        else:
                            if isinstance(v, str):
                                conditions.append(column.ilike(f"%{v}%"))
                            else:
                                conditions.append(column == v)

                        # elif k == "created_at_start" or k == "created_at_finish":
                        #     if k == "created_at_start":
                        #         conditions.append(column >= v)
                        #     elif k == "created_at_finish":
                        #         conditions.append(column <= v)

                if conditions:
                    query = query.filter(and_(*conditions))  # Apply all conditions

            # result = session.execute(query)
            # return result.scalars().all()
            return query

        except SQLAlchemyError as e:
            print("SQLAlchemyError: \n", e)
            return None


    @classmethod
    async def update(cls, session: Session, data):
        try:
            obj_id = data.pop("id", None)  # Extract `id` from the dictionary

            if obj_id is None:
                raise ValueError("update_data must contain an 'id' key.")
            if data:
                query = (
                    update(cls.model)
                    .where(cls.model.id == obj_id)
                    .values(**data)
                    .returning(cls.model)
                )
            else:
                query = (
                    select(cls.model)
                    .where(cls.model.id == obj_id)
                )
            result = session.execute(query)

            # await session.commit()
            session.flush()
            instance = result.scalars().first()  # Get the updated instance
            if instance:
                session.refresh(instance)  # Refresh without re-querying

            return instance

        except SQLAlchemyError as e:
            session.rollback()
            print("SQLAlchemyError: \n", e)
            return None


    @classmethod
    async def delete(cls, session: Session, filters: dict):
        try:
            query = (
                delete(cls.model)
                .filter_by(**filters)
                .returning(cls.model)
            )
            result = session.execute(query)
            # await session.commit()
            session.flush()
            # deleted_objects = result.scalars().unique().all()
            deleted_objects = result.scalars().all()
            return deleted_objects

        except SQLAlchemyError as e:
            session.rollback()
            print(e)
            return None

    @classmethod
    def _eager_load_relationships(cls, model, depth=2):
        """
        Recursively loads relationships up to a given depth.

        :param model: The SQLAlchemy model to inspect.
        :param depth: The depth of relationship loading (default=2, to avoid infinite recursion).
        :return: List of joinedload options.
        """
        options = []
        if depth <= 0:
            return options

        for rel in inspect(model).relationships:
            # rel_attr = getattr(model, rel.key)
            # loader = joinedload(rel_attr)
            #
            # # If the related model has further relationships, load them as well
            # if rel.mapper.class_ != model:  # Prevent self-referencing loops
            #     sub_options = cls._eager_load_relationships(rel.mapper.class_, depth - 1)
            #     for sub_option in sub_options:
            #         loader = loader.joinedload(sub_option)
            #
            # options.append(loader)
            if hasattr(model, rel.key):  # ✅ Check if relationship exists in the model
                rel_attr = getattr(model, rel.key)
                loader = joinedload(rel_attr)

                if depth > 1 and rel.mapper.class_ != model:  # Prevent self-referencing loops
                    sub_options = cls._eager_load_relationships(rel.mapper.class_, depth - 1)
                    for sub_option in sub_options:
                        loader = loader.options(sub_option)  # ✅ Fix nested loading

                options.append(loader)
            else:
                print(f"Warning: Relationship '{rel.key}' does not exist on {model}")

        return options