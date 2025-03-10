from contextlib import asynccontextmanager

import pytz

from core.config import settings
from core.session import async_session_maker, create_sequence
from dal.dao import PermissionGroupDAO, PermissionDAO, RoleDAO, AccessDAO, UserDAO
from utils.permissions import permission_groups
from utils.utils import Hasher

timezonetash = pytz.timezone('Asia/Tashkent')



@asynccontextmanager
async def get_session():
    async with async_session_maker() as session:
        yield session  # Ensure session is properly yielded
        await session.close()



#create new permission
@asynccontextmanager
async def create_permissions_lifespan():
    async with get_session() as session:
        for key, value in permission_groups.items():
            # permission_group = await _get_permission_group_by_attributes(session=session, data={"name": key})
            # permission_group = await _create_permission_group(session=session, data={"name": key})
            permission_group = await PermissionGroupDAO.add(session=session, **{"name": key})
            print("created permission_group: ", permission_group)
            if permission_group is not None:
                permission_group_id = permission_group.id

                for name, action in value.items():
                    # permission = await _get_permission_by_attributes(session=session, data={"group_id": permission_group_id, "name": name})
                    permission = await PermissionDAO.get_by_attributes(session=session, filters={"group_id": permission_group_id, "name": name}, first=True)
                    print("permission: ", permission)
                    if permission is None:
                        # created_permission = await _create_permission(session=session, data={"name": name, "action": action, "group_id": permission_group_id})
                        created_permission = await PermissionDAO.add(session=session, **{"name": name, "action": action, "group_id": permission_group_id})
                        print("created permission: ", created_permission)

                await session.commit()

    yield  #--------------  HERE YOU CAN WRITE LOG ON CLOSING AFTER YIELD ------------


#---------------------- CREATE ROLE AND USERS FOR DEFAULT ADMIN USER --------------------------
@asynccontextmanager
async def create_role_lifespan():
    async with get_session() as session:
        role = await RoleDAO.get_by_attributes(session=session, filters={"name": settings.admin_role, "description": 'Superuser'}, first=True)
        print("ROLE: ", role)
        if not role:
            role = await RoleDAO.add(session=session, **{"name": settings.admin_role, "description": 'Superuser'})

        if role is not None:
            role_id = role.id
            role_permissions = []
            if role.accesses is not None:
                for access in role.accesses:
                    role_permissions.append(access.permission.action)

            for key, value in permission_groups.items():
                for name, action in value.items():
                    if action not in role_permissions:
                        # permission = await _get_permission_by_attributes(session=session, data={"action": action})
                        permission = await PermissionDAO.get_by_attributes(session=session, filters={"action": action}, first=True)
                        print("Permission: ", permission.action)
                        if permission is not None:
                            # await _create_access(session=session, data={"permission_id": permission.id, "role_id": role_id})
                            # access_id = uuid.uuid4()
                            # access_objs.append({"id": access_id, "permission_id": permission.id, "role_id": role_id})
                            await AccessDAO.add(session=session, **{"permission_id": permission.id, "role_id": role_id})
                            await session.commit()


            # user = await _create_user(
            #     session=session,
            #     data={
            #         "username": settings.admin_role,
            #         "password": Hasher.get_password_hash(settings.admin_password),
            #         "role_id": role_id
            #     }
            # )
            user = await UserDAO.add(
                session=session,
                **{
                    "username": settings.admin_role,
                    "password": Hasher.get_password_hash(settings.admin_password),
                    "role_id": role_id
                }
            )
            await session.commit()
            print("Created Admin user: ", user)

    yield  #--------------  HERE YOU CAN WRITE LOG ON CLOSING AFTER YIELD ------------



@asynccontextmanager
async def combined_lifespan(app):
    async with create_permissions_lifespan(), create_role_lifespan(), create_sequence():
        print("Started tasks ...")
        #-----------   BEFORE YIELD WHEN STARTING UP ALL THE FUNCTIONS WORK ---------
        yield
