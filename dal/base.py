from typing import List, Any, Dict

from sqlalchemy import select, inspect, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload



class BaseDAO:
    model = None  # Устанавливается в дочернем классе

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        # Добавить одну запись
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            # await session.commit()
            await session.flush()
            await session.refresh(new_instance)
            return new_instance
        except SQLAlchemyError as e:
            await session.rollback()
            print("SQLAlchemyError: ", e)
            return None



    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[Dict[str, Any]]):
        new_instances = [cls.model(**values) for values in instances]
        session.add_all(new_instances)
        try:
            # await session.commit()
            await session.flush()
            await session.refresh(new_instances)
            return new_instances
        except SQLAlchemyError as e:
            await session.rollback()
            print("ACCESSES ERROR: \n", e)
            return None


    @classmethod
    async def get_by_attributes(cls, session: AsyncSession, filters: Dict[str, Any], first: bool = False):
        """
        Retrieves records filtered by given attributes.

        :param session: AsyncSession - SQLAlchemy async session.
        :param filters: Dict[str, Any] - Dictionary where keys are column names and values are filter values.
        :param first: bool - Whether to return only the first match.
        :return: Single model instance if `first=True`, else a list of instances.
        """
        try:
            query = select(cls.model)
            # Dynamically load all relationships using `joinedload`
            # for rel in inspect(cls.model).relationships:
            #     query = query.options(joinedload(getattr(cls.model, rel.key)))

            # Load all relationships recursively
            # query = query.options(*cls._eager_load_relationships(cls.model))
            query = query.filter_by(**filters)

            result = await session.execute(query)
            return result.scalars().first() if first else result.scalars().all()
        except SQLAlchemyError as e:
            print("SQLAlchemyError: \n", e)
            return None


    @classmethod
    async def get_all(cls, session: AsyncSession, filters: dict = None):
        try:
            query = select(cls.model)
            if filters is not None:
                query = query.filter_by(**filters)

            result = await session.execute(query)
            return result.scalars().unique().all()

        except SQLAlchemyError as e:
            print(e)
            return None


    @classmethod
    async def update(cls, session: AsyncSession, data):
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
            result = await session.execute(query)

            # await session.commit()
            await session.flush()
            instance = result.scalars().first()  # Get the updated instance
            if instance:
                await session.refresh(instance)  # Refresh without re-querying

            return instance

        except SQLAlchemyError as e:
            await session.rollback()
            print(e)
            return None


    @classmethod
    async def delete(cls, session: AsyncSession, filters: dict):
        try:
            query = (
                delete(cls.model)
                .filter_by(**filters)
                .returning(cls.model)
            )
            result = await session.execute(query)
            # await session.commit()
            await session.flush()
            deleted_objects = result.scalars().unique().all()
            return deleted_objects

        except SQLAlchemyError as e:
            await session.rollback()
            print(e)
            return None


    # @classmethod
    # def _eager_load_relationships(cls, model, depth=2):
    #     """
    #     Recursively loads relationships up to a given depth.
    #
    #     :param model: The SQLAlchemy model to inspect.
    #     :param depth: The depth of relationship loading (default=2, to avoid infinite recursion).
    #     :return: List of joinedload options.
    #     """
    #     options = []
    #     if depth <= 0:
    #         return options
    #
    #     for rel in inspect(model).relationships:
    #         rel_attr = getattr(model, rel.key)
    #         loader = joinedload(rel_attr)
    #
    #         # If the related model has further relationships, load them as well
    #         if rel.mapper.class_ != model:  # Prevent self-referencing loops
    #             sub_options = cls._eager_load_relationships(rel.mapper.class_, depth - 1)
    #             for sub_option in sub_options:
    #                 loader = loader.joinedload(sub_option)
    #
    #         options.append(loader)
    #
    #     return options
