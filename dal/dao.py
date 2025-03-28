from typing import Dict, Any

from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session

from dal.base import BaseDAO
from models.roles import Roles
from models.permission_groups import PermissionGroups
from models.permissions import Permissions
from models.users import Users
from models.accesses import Accesses
from models.departments import Departments
from models.clients import Clients
from models.expense_types import ExpenseTypes
from models.payment_types import PaymentTypes
from models.buyers import Buyers
from models.suppliers import Suppliers
from models.requests import Requests
from models.contracts import Contracts
from models.invoices import Invoices
from models.files import Files
from models.logs import Logs
from models.budgets import Budgets
from models.transactions import Transactions



class PermissionGroupDAO(BaseDAO):
    model = PermissionGroups


class PermissionDAO(BaseDAO):
    model = Permissions


class RoleDAO(BaseDAO):
    model = Roles


class AccessDAO(BaseDAO):
    model = Accesses


class UserDAO(BaseDAO):
    model = Users


class DepartmentDAO(BaseDAO):
    model = Departments

    @classmethod
    async def get_department_total_budget(cls, session: Session, department_id):
        result = session.query(
            func.sum(Transactions.value)
        ).join(
            Budgets
        ).filter(
            and_(
                Budgets.department_id == department_id
            )
        ).first()
        return result


    @classmethod
    async def get_department_monthly_budget(cls, session: Session, department_id):
        result = session.execute(
            text("""
                    SELECT 
                        EXTRACT(YEAR FROM month_series) AS year,
                        EXTRACT(MONTH FROM month_series) AS month,
                        SUM(value) AS sum
                    FROM (
                        SELECT 
                            generate_series(start_date, finish_date, INTERVAL '1 month') AS month_series,
                            value
                        FROM budgets
                        WHERE department_id = :department_id
                    ) AS budget_months
                    GROUP BY year, month
                    ORDER BY year, month;
                """),
            {"department_id": department_id}
        ).fetchall()

        return result


class ClientDAO(BaseDAO):
    model = Clients


class ExpenseTypeDAO(BaseDAO):
    model = ExpenseTypes


class PaymentTypeDAO(BaseDAO):
    model = PaymentTypes


class BuyerDAO(BaseDAO):
    model = Buyers


class SupplierDAO(BaseDAO):
    model = Suppliers


class RequestDAO(BaseDAO):
    model = Requests


class ContractDAO(BaseDAO):
    model = Contracts


class InvoiceDAO(BaseDAO):
    model = Invoices


class FileDAO(BaseDAO):
    model = Files


class LogDAO(BaseDAO):
    model = Logs


class BudgetDAO(BaseDAO):
    model = Budgets

    @classmethod
    async def get_budget_sum(cls, session: Session, budget_id):
        result = session.query(
            func.sum(Transactions.value)
        ).filter(
            and_(
                Transactions.budget_id == budget_id
            )
        ).first()
        return result


class TransactionDAO(BaseDAO):
    model = Transactions

    @classmethod
    async def get_department_transactions(cls, session: Session, department_id):
        result = session.query(
            Transactions
        ).join(
            Budgets
        ).filter(
            Budgets.department_id == department_id
        ).all()
        return result
