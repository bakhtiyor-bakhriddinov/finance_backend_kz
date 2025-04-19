import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from routers.life_span import combined_lifespan
from routers.roles import roles_router
from routers.users import users_router
from routers.permissions import permissions_router
from routers.departments import departments_router
from routers.expense_types import expense_types_router
from routers.payment_types import payment_types_router
from routers.clients import clients_router
from routers.buyers import buyers_router
from routers.suppliers import suppliers_router
from routers.requests import requests_router
from routers.files import files_router
from routers.contracts import contracts_router
from routers.logs import logs_router
from routers.statistics import statistics_router
from routers.accounting import accounting_router
from routers.settings import settings_router
from routers.budgets import budgets_router
from routers.transactions import transactions_router
from routers.transfers import transfers_router


# app = FastAPI(
#     swagger_ui_parameters={"docExpansion": "none"},
#     docs_url=None,
#     redoc_url=None,
#     openapi_url=None
# )
# app.include_router(user_router)

app = FastAPI(title="Finance System ...", lifespan=combined_lifespan)

main_router = APIRouter()


main_router.include_router(permissions_router, tags=['Permissions'])
main_router.include_router(roles_router, tags=['Roles'])
main_router.include_router(users_router, tags=['Users'])
main_router.include_router(clients_router, tags=['Clients'])
main_router.include_router(departments_router, tags=['Departments'])
main_router.include_router(budgets_router, tags=['Budgets'])
main_router.include_router(transactions_router, tags=['Transactions'])
main_router.include_router(expense_types_router, tags=['Expense Types'])
main_router.include_router(payment_types_router, tags=['Payment Types'])
main_router.include_router(buyers_router, tags=['Buyers'])
main_router.include_router(suppliers_router, tags=['Suppliers'])
main_router.include_router(requests_router, tags=['Requests'])
main_router.include_router(statistics_router, tags=['Statistics'])
main_router.include_router(accounting_router, tags=['Accounting'])
main_router.include_router(transfers_router, tags=['Transfers'])
main_router.include_router(logs_router, tags=['Logs'])
main_router.include_router(files_router, tags=['Files'])
main_router.include_router(contracts_router, tags=['Contracts'])
main_router.include_router(settings_router, tags=['Settings'])



app.include_router(main_router)

add_pagination(app)


app.mount("/files", StaticFiles(directory="files"), name="files")



origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)
