from contextlib import asynccontextmanager, contextmanager
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import Depends
from sqlalchemy.orm import Session

from core.config import settings
from core.session import session_maker, create_sequence, get_db
from dal.dao import PermissionGroupDAO, PermissionDAO, RoleDAO, AccessDAO, UserDAO, RequestDAO
from utils.permissions import permission_groups
from utils.utils import Hasher


timezonetash = pytz.timezone('Asia/Tashkent')



scheduler = BackgroundScheduler()

if not scheduler.running:
    print("🚀 Starting scheduler...")
    scheduler.start()  # ✅ Start only once


# scheduler_lock = threading.Lock()




def get_scheduler():
    return scheduler




#create new permission
@asynccontextmanager
async def create_permissions_lifespan():
    @contextmanager
    def get_session():
        with session_maker() as session:
            yield session  # Ensure session is properly yielded
            session.close()

    with get_session() as session:
        for key, value in permission_groups.items():
            permission_group = await PermissionGroupDAO.add(session=session, **{"name": key})
            print("created permission_group: ", permission_group)
            if permission_group is not None:
                permission_group_id = permission_group.id

                for name, action in value.items():
                    permission = await PermissionDAO.get_by_attributes(session=session, filters={"group_id": permission_group_id, "name": name}, first=True)
                    print("permission: ", permission)
                    if permission is None:
                        created_permission = await PermissionDAO.add(session=session, **{"name": name, "action": action, "group_id": permission_group_id})
                        print("created permission: ", created_permission)

                session.commit()

    yield  #--------------  HERE YOU CAN WRITE LOG ON CLOSING AFTER YIELD ------------



#---------------------- CREATE ROLE AND USERS FOR DEFAULT ADMIN USER --------------------------
@asynccontextmanager
async def create_role_lifespan():
    @contextmanager
    def get_session():
        with session_maker() as session:
            yield session  # Ensure session is properly yielded
            session.close()

    with get_session() as session:
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
                        permission = await PermissionDAO.get_by_attributes(session=session, filters={"action": action}, first=True)
                        print("Permission: ", permission.action)
                        if permission is not None:
                            await AccessDAO.add(session=session, **{"permission_id": permission.id, "role_id": role_id})
                            session.commit()


            user = UserDAO.add(
                session=session,
                **{
                    "username": settings.admin_role,
                    "password": Hasher.get_password_hash(settings.admin_password),
                    "role_id": role_id
                }
            )
            session.commit()
            print("Created Admin user: ", user)

    yield  #--------------  HERE YOU CAN WRITE LOG ON CLOSING AFTER YIELD ------------



async def request_status_update(db: Session = Depends(get_db)):
    today = datetime.now(tz=timezonetash).date()
    query = await RequestDAO.get_all(session=db, filters={"status": 1, "payment_time": today})
    requests = db.execute(query).scalars().all()
    for request in requests:
        # time.sleep(1)
        await RequestDAO.update(session=db, data={"id": request.id, "status": 2})




async def status_updater():
    job_scheduler: BackgroundScheduler = get_scheduler()
    # trigger = CronTrigger(
    #     hour=11, minute=30, second=00, timezone=timezonetash
    # )
    trigger = IntervalTrigger(minutes=10)
    job_scheduler.add_job(request_status_update, trigger=trigger, id='update_request_status')


@asynccontextmanager
async def run_updater():
    await status_updater()
    yield


@asynccontextmanager
async def combined_lifespan(app):
    async with create_permissions_lifespan(), create_role_lifespan(), create_sequence(), run_updater():
        print("Started tasks ...")
        #-----------   BEFORE YIELD WHEN STARTING UP ALL THE FUNCTIONS WORK ---------
        yield
