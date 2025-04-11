from datetime import timedelta, date
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
                Transactions.budget_id.isnot(None),
                Transactions.status == 5
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
                EXTRACT(YEAR FROM budget_months.month_series) AS year,
                EXTRACT(MONTH FROM budget_months.month_series) AS month,
                value_type AS type,
                SUM(value) AS sum,
                (
                    SELECT 
                        COUNT(r.id) AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND t.status = 0 
                    AND EXTRACT(YEAR FROM t.created_at::DATE) = EXTRACT(YEAR FROM budget_months.month_series)
                    AND EXTRACT(MONTH FROM t.created_at::DATE) = EXTRACT(MONTH FROM budget_months.month_series)
                ) AS pending_requests
            FROM (
                    SELECT 
                        generate_series(b.start_date, b.finish_date, INTERVAL '1 month') AS month_series,
                        'budget' AS value_type,
                        t.value AS value
                    FROM transactions t
                    INNER JOIN budgets b ON t.budget_id = b.id
                    WHERE t.budget_id IS NOT NULL 
                    AND b.department_id = :department_id 
                    AND t.status = 5 
                    AND b.start_date BETWEEN :start_date AND :finish_date 
                    AND b.finish_date BETWEEN :start_date AND :finish_date
                
                    UNION ALL
                
                    SELECT 
                        t.created_at AS month_series,
                        'expense' AS value_type,
                        t.value AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND t.status IN (1, 2, 3, 5) 
                    AND t.created_at::DATE BETWEEN :start_date AND :finish_date
                    
                    UNION ALL
                    
                    SELECT 
                        t.created_at AS month_series,
                        'pending' AS value_type,
                        t.value AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND t.status = 0 
                    AND t.created_at::DATE BETWEEN :start_date AND :finish_date
            
            ) AS budget_months
            GROUP BY year, month, value_type, pending_requests
            ORDER BY year, month, value_type;
        """
        params = {
            "department_id": department_id,
            "start_date": start_date,
            "finish_date": finish_date
        }

        # Add strict filters only if dates are provided
        # if start_date is not None:
        #     query += " AND b.start_date BETWEEN :start_date AND :finish_date"
        #     params["start_date"] = start_date
        # if finish_date is not None:
        #     query += " AND b.finish_date BETWEEN :start_date AND :finish_date"
        #     params["finish_date"] = finish_date


        # query += """
        #     ) AS budget_months
        #     GROUP BY year, month, value_type
        #     ORDER BY year, month, value_type;
        # """

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

    @classmethod
    async def get_excel(cls, session: Session, start_date, finish_date):
        finish_date = finish_date + timedelta(days=1)
        query = session.query(
            cls.model
        ).join(
            Departments, cls.model.department_id == Departments.id
        ).join(
            ExpenseTypes, cls.model.expense_type_id == ExpenseTypes.id
        ).join(
            Clients, cls.model.client_id == Clients.id
        ).join(
            PaymentTypes, cls.model.payment_type_id == PaymentTypes.id
        ).filter(
            func.date(cls.model.created_at).between(start_date, finish_date)
        )
        return query.order_by(cls.model.number.desc()).all()


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
                Transactions.budget_id == budget_id,
                Transactions.status == 5
            )
        ).first()
        return result

    @classmethod
    async def get_filtered_budget_sum(cls, session: Session, department_id, expense_type_id, current_date: date):
        result = session.query(
            func.sum(Transactions.value)
        ).join(
            Budgets, Transactions.budget_id == Budgets.id
        ).filter(
            and_(
                Budgets.department_id == department_id,
                Budgets.expense_type_id == expense_type_id,
                Transactions.status == 5,
                current_date >= Budgets.start_date,
                current_date <= Budgets.finish_date
            )
        ).first()
        return result


    @classmethod
    async def get_filtered_budget_expense(cls, session: Session, department_id, expense_type_id, current_date: date):
        current_year = float(current_date.year)
        current_month = float(current_date.month)

        result = session.query(
            func.sum(Transactions.value)
        ).join(
            Requests, Transactions.request_id == Requests.id
        ).filter(
            and_(
                Requests.department_id == department_id,
                Requests.expense_type_id == expense_type_id,
                Transactions.status != 4,
                func.date_part('year', Transactions.created_at) == current_year,
                func.date_part('month', Transactions.created_at) == current_month
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

    @classmethod
    async def get_calendar_transactions(cls, session: Session, start_date, finish_date):
        result = session.query(
            func.date(Requests.payment_time),
            PaymentTypes.name,
            func.sum(-Transactions.value)
        ).join(
            Requests, Transactions.request_id == Requests.id
        ).join(
            PaymentTypes, Requests.payment_type_id == PaymentTypes.id
        ).filter(
            and_(
                func.date(Requests.payment_time).between(start_date, finish_date),
                Transactions.status.in_([1, 2, 3, 5])
            )
        ).group_by(
            func.date(Requests.payment_time),
            PaymentTypes.name
        ).all()

        # result = session.query(
        #     func.date(Requests.payment_time),
        #     PaymentTypes.name,
        #     func.sum(Requests.sum)
        # ).join(
        #     PaymentTypes, Requests.payment_type_id == PaymentTypes.id
        # ).filter(
        #     and_(
        #         func.date(Requests.payment_time).between(start_date, finish_date),
        #         Requests.status.in_([1, 2, 3, 5])
        #     )
        # ).group_by(
        #     func.date(Requests.payment_time),
        #     PaymentTypes.name
        # ).all()

        return result
