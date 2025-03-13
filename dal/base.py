from typing import List, Any, Dict
from sqlalchemy import select, inspect, update, delete, and_, in_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, Session



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
                # conditions = [
                #     getattr(cls.model, k).in_(v) if k == "status" else getattr(cls.model, k) == v
                #     for k, v in filters.items()
                # ]
                # query = query.filter(and_(*conditions))

                conditions = []
                for k, v in filters.items():
                    column = getattr(cls.model, k, None)
                    if column is not None:
                        if isinstance(v, list):  # If value is a list, use IN
                            conditions.append(column.in_(v))
                        else:
                            conditions.append(column == v)

                if conditions:
                    query = query.filter(and_(*conditions))  # Apply all conditions

            # result = session.execute(query)
            # return result.scalars().all()
            return query

        except SQLAlchemyError as e:
            print(e)
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
            print(e)
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
