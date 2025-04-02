from typing import Dict, Any

from dns.reversename import to_address
from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session

from dal.base import BaseDAO
from models.roles import Roles
from models.role_department_relations import RoleDepartments
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


class RoleDepartmentDAO(BaseDAO):
    model = RoleDepartments


class AccessDAO(BaseDAO):
    model = Accesses


class UserDAO(BaseDAO):
    model = Users


class DepartmentDAO(BaseDAO):
    model = Departments

    @classmethod
    async def get_department_total_budget(cls, session: Session, department_id, start_date, finish_date):
        result = session.query(
            func.sum(Transactions.value)
        ).join(
            Budgets
        ).filter(
            and_(
                Budgets.department_id == department_id,
                Transactions.budget_id.isnot(None)
            )
        )
        if start_date is not None and finish_date is not None:
            result = result.filter(
                and_(
                    Budgets.start_date.between(start_date, finish_date),
                    Budgets.finish_date.between(start_date, finish_date)
                )
            )

        return result.first()


    @classmethod
    async def get_department_monthly_budget(cls, session: Session, department_id, start_date, finish_date):
        query = """
            SELECT 
                EXTRACT(YEAR FROM month_series) AS year,
                EXTRACT(MONTH FROM month_series) AS month,
                value_type AS type,
                SUM(value) AS sum
            FROM (
                SELECT 
                    generate_series(b.start_date, b.finish_date, INTERVAL '1 month') AS month_series,
                    'budget' AS value_type,
                    t.value AS value
                FROM transactions t
                LEFT JOIN budgets b ON t.budget_id = b.id
                WHERE t.budget_id IS NOT NULL 
                AND b.department_id = :department_id
            
                UNION ALL
            
                SELECT 
                    t.created_at AS month_series,
                    'expense' AS value_type,
                    t.value AS value
                FROM transactions t
                LEFT JOIN requests r ON t.request_id = r.id
                WHERE t.request_id IS NOT NULL 
                AND r.department_id = :department_id
        """
        params = {"department_id": department_id}

        # Add strict filters only if dates are provided
        if start_date is not None:
            query += " AND b.start_date BETWEEN :start_date AND :finish_date"
            params["start_date"] = start_date
        if finish_date is not None:
            query += " AND b.finish_date BETWEEN :start_date AND :finish_date"
            params["finish_date"] = finish_date


        query += """
            ) AS budget_months
            GROUP BY year, month, value_type
            ORDER BY year, month, value_type;
        """

        result = session.execute(text(query), params).fetchall()
        return result

    # @classmethod
    # async def get_department_monthly_budget(cls, session: Session, department_id, start_date, finish_date):
    #     result = session.query(
    #         func.sum(Transactions.value)
    #     ).join(
    #         Budgets
    #     ).filter(
    #         and_(
    #             Budgets.department_id == department_id,
    #             Budgets.start_date.between(start_date, finish_date),
    #             Budgets.finish_date.between(start_date, finish_date),
    #             Transactions.budget_id.isnot(None)
    #         )
    #     ).group_by(
    #
    #     ).first()
    #     return result


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
    async def get_department_transactions(cls, session: Session, department_id, start_date, finish_date, page, size):
        result = session.query(
            Transactions
        ).join(
            Budgets
        ).filter(
            Budgets.department_id == department_id
        )
        if start_date is not None and finish_date is not None:
            result = result.filter(
                func.date(Transactions.created_at).between(start_date, finish_date)
            )

        result = result.order_by(
            Transactions.created_at.desc()
        ).offset((page - 1) * size).limit(size).all()
        return result

    @classmethod
    async def get_department_all_transactions(cls, session: Session, department_id, start_date, finish_date):
        total_transactions = session.query(
            Transactions
        ).join(
            Budgets
        ).filter(
            Budgets.department_id == department_id
        )
        if start_date is not None and finish_date is not None:
            total_transactions = total_transactions.filter(
                func.date(Transactions.created_at).between(start_date, finish_date)
            )
        total_transactions = total_transactions.count()
        return total_transactions

    @classmethod
    async def get_budget_transactions(cls, session: Session, budget_id):
        transactions = session.query(
            Transactions
        ).filter(
            Transactions.budget_id == budget_id
        ).all()
        return transactions
