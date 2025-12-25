import asyncio
import threading
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, date

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import Depends
from sqlalchemy import text, and_, func, select
from sqlalchemy.orm import Session

from core.config import settings
from core.session import session_maker, create_sequence, get_db
from dal.dao import PermissionGroupDAO, PermissionDAO, RoleDAO, AccessDAO, UserDAO, RequestDAO, TransactionDAO
from utils.permissions import permission_groups
from utils.utils import Hasher, send_telegram_message

timezonetash = pytz.timezone('Asia/Tashkent')

# ✅ Get the main event loop at startup
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)


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
            permission_group = await PermissionGroupDAO.get_by_attributes(session=session, filters={"name": key}, first=True)
            if permission_group:
                permission_group_id = permission_group.id
            else:
                permission_group = await PermissionGroupDAO.add(session=session, **{"name": key})
                permission_group_id = permission_group.id

            # print("created permission_group: ", permission_group)
            # if permission_group is not None:
            #     permission_group_id = permission_group.id

            for name, action in value.items():
                permission = await PermissionDAO.get_by_attributes(session=session, filters={"group_id": permission_group_id, "name": name}, first=True)
                # print("permission: ", permission)
                if permission is None:
                    created_permission = await PermissionDAO.add(session=session, **{"name": name, "action": action, "group_id": permission_group_id})
                    # print("created permission: ", created_permission)

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
                        # print("Permission: ", permission.action)
                        if permission is not None:
                            await AccessDAO.add(session=session, **{"permission_id": permission.id, "role_id": role_id})
                            session.commit()


            user = await UserDAO.add(
                session=session,
                **{
                    "username": settings.admin_role,
                    "password": Hasher.get_password_hash(settings.admin_password),
                    "role_id": role_id
                }
            )
            session.commit()

    yield  #--------------  HERE YOU CAN WRITE LOG ON CLOSING AFTER YIELD ------------



async def request_status_update():
    @contextmanager
    def get_session():
        with session_maker() as session:
            yield session  # Ensure session is properly yielded
            session.close()

    with get_session() as session:
        print("\n--------- Started request status updater job working every 30 minutes ------------\n")
        today = date.today()
        today_query = await RequestDAO.get_all(
            session=session,
            filters={
                "status": [1, 6],
                "payment_time": today,
                "approved": True
            }
        )
        today_requests = session.execute(today_query).scalars().all()
        for request in today_requests:
            # time.sleep(1)
            updated_request = await RequestDAO.update(session=session, data={"id": request.id, "status": 2})
            transaction = await TransactionDAO.get_by_attributes(session=session, filters={"request_id": updated_request.id},
                                                                 first=True)
            if transaction:
                data = {
                    "id": transaction.id,
                    "status": updated_request.status
                }
                await TransactionDAO.update(session=session, data=data)

            try:
                send_telegram_message(
                    chat_id=request.client.tg_id,
                    message_text=f"Сегодня срок оплаты вашей заявки #{request.number}s"
                )
            except Exception as e:
                print("Sending Error: ", e)

        expired_requests = session.query(RequestDAO.model).filter(
            and_(
                RequestDAO.model.status.in_([1, 2, 3, 6]),
                RequestDAO.model.approved == True,
                func.date(RequestDAO.model.payment_time) < today
            )
        ).all()
        for request in expired_requests:
            # time.sleep(1)
            updated_request = await RequestDAO.update(session=session, data={"id": request.id, "status": 3})
            transaction = await TransactionDAO.get_by_attributes(session=session,
                                                                 filters={"request_id": updated_request.id},
                                                                 first=True)
            if transaction:
                data = {
                    "id": transaction.id,
                    "status": updated_request.status
                }
                await TransactionDAO.update(session=session, data=data)

        session.commit()



# ✅ Use `run_coroutine_threadsafe` to run async function from a thread
def run_async_job():
    future = asyncio.run_coroutine_threadsafe(request_status_update(), main_loop)
    future.result()  # Ensures exceptions are properly raised


async def status_updater():
    job_scheduler: BackgroundScheduler = get_scheduler()
    # trigger = CronTrigger(
    #     hour=11, minute=30, second=00, timezone=timezonetash
    # )
    trigger = IntervalTrigger(minutes=30)
    job_scheduler.add_job(run_async_job, trigger=trigger, id='update_request_status')



# ✅ Start the asyncio event loop in a separate thread
def start_event_loop():
    asyncio.set_event_loop(main_loop)
    main_loop.run_forever()


event_loop_thread = threading.Thread(target=start_event_loop, daemon=True)
event_loop_thread.start()



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
