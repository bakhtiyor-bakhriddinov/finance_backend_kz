from datetime import timedelta, date
from typing import Optional

from sqlalchemy import func, and_, text, or_, case, select, literal_column, cast, Date
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from dal.base import BaseDAO
from models.accesses import Accesses
from models.budgets import Budgets
from models.buyers import Buyers
from models.clients import Clients
from models.contracts import Contracts
from models.departments import Departments
from models.expense_types import ExpenseTypes
from models.files import Files
from models.invoices import Invoices
from models.logs import Logs
from models.payer_companies import PayerCompanies
from models.payment_types import PaymentTypes
from models.permission_groups import PermissionGroups
from models.permissions import Permissions
from models.requests import Requests
from models.role_department_relations import RoleDepartments
from models.roles import Roles
from models.suppliers import Suppliers
from models.transactions import Transactions
from models.users import Users
from models.limits import Limits


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


class PayerCompanyDAO(BaseDAO):
    model = PayerCompanies


class DepartmentDAO(BaseDAO):
    model = Departments

    @classmethod
    async def get_department_total_budget(cls, session: Session, department_id, start_date, finish_date, payment_date):
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
        elif payment_date is not None:
            result = result.filter(
                and_(
                    payment_date >= Budgets.start_date,
                    payment_date <= Budgets.finish_date
                )
            )

        return result.first()


    @classmethod
    async def get_department_expense(cls, session: Session, department_id, start_date, finish_date, payment_date: Optional[date] = None):
        result = [0]
        if start_date is not None and finish_date is not None:
            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).join(
                ExpenseTypes, Requests.expense_type_id == ExpenseTypes.id
            ).filter(
                and_(
                    and_(
                        Requests.department_id == department_id,
                        Transactions.request_id.isnot(None),
                        Transactions.status != 4,
                        Requests.status != 4,
                        func.date(Requests.payment_time).between(start_date, finish_date)
                    ),
                    or_(
                        Requests.approved == True,
                        and_(
                            Requests.approved == False,
                            ExpenseTypes.purchasable == True,
                        )
                    )
                )
            ).first()

        if payment_date is not None:
            current_year = float(payment_date.year)
            current_month = float(payment_date.month)

            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).join(
                ExpenseTypes, Requests.expense_type_id == ExpenseTypes.id
            ).filter(
                and_(
                    and_(
                        Requests.department_id == department_id,
                        Transactions.request_id.isnot(None),
                        Transactions.status != 4,
                        Requests.status != 4,
                        func.date_part('year', Requests.payment_time) == current_year,
                        func.date_part('month', Requests.payment_time) == current_month
                    ),
                    or_(
                        Requests.approved == True,
                        and_(
                            Requests.approved == False,
                            ExpenseTypes.purchasable == True,
                        )
                    )
                )
            ).first()

        return result


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
                    AND r.status = 0 
                    AND EXTRACT(YEAR FROM t.created_at::DATE) = EXTRACT(YEAR FROM budget_months.month_series)
                    AND EXTRACT(MONTH FROM t.created_at::DATE) = EXTRACT(MONTH FROM budget_months.month_series)
                ) AS pending_requests,
                (
                    SELECT 
                        COUNT(r.id) AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND t.status = 6
                    AND r.status = 6 
                    AND EXTRACT(YEAR FROM r.payment_time::DATE) = EXTRACT(YEAR FROM budget_months.month_series)
                    AND EXTRACT(MONTH FROM r.payment_time::DATE) = EXTRACT(MONTH FROM budget_months.month_series)
                ) AS delayed_requests,
                (
                    SELECT 
                        COUNT(r.id) AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND r.approved IS False 
                    AND r.status IN (0,1,2,3)
                ) AS not_approved_requests
            
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
                        r.payment_time AS month_series,
                        'expense' AS value_type,
                        t.value AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    INNER JOIN expense_types e ON r.expense_type_id = e.id
                    WHERE 
                        t.request_id IS NOT NULL 
                        AND r.department_id = :department_id 
                        AND t.status <> 4 
                        AND r.payment_time::DATE BETWEEN :start_date AND :finish_date
                        AND (
                                r.approved IS TRUE 
                                OR (
                                    r.approved IS FALSE 
                                    AND e.purchasable IS TRUE
                                )
                        )
                    
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
                    AND r.status = 0 
                    AND t.created_at::DATE BETWEEN :start_date AND :finish_date
                    
                    UNION ALL
                    
                    SELECT 
                        r.payment_time AS month_series,
                        'delayed' AS value_type,
                        t.value AS value
                    FROM transactions t
                    INNER JOIN requests r ON t.request_id = r.id
                    WHERE t.request_id IS NOT NULL 
                    AND r.department_id = :department_id 
                    AND t.status = 6
                    AND r.status = 6 
                    AND r.payment_time::DATE BETWEEN :start_date AND :finish_date
            ) AS budget_months
            
            GROUP BY year, month, value_type, pending_requests, delayed_requests, not_approved_requests
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
    async def sum_count_query(cls, session: Session, filters: dict = None):
        # Get base filtered query from get_all()
        base_query = await cls.get_all(session, filters)

        subq = base_query.with_only_columns(
            cls.model.id.label("id"),
            cls.model.sum.label("sum")
        ).subquery()

        query = select(
            func.count(subq.c.id).label("total_requests"),
            func.sum(subq.c.sum).label("total_sum")
        ).select_from(subq)

        query = session.execute(query).first()

        return {
            "total_requests": query.total_requests or 0,
            "total_sum": float(query.total_sum or 0)
        }


    @classmethod
    async def get_excel(cls, session: Session, filters):

        query = await cls.get_all(
            session=session,
            filters=filters if filters else None
        )
        query = query.join(
            Departments, cls.model.department_id == Departments.id
        ).join(
            ExpenseTypes, cls.model.expense_type_id == ExpenseTypes.id
        ).join(
            Clients, cls.model.client_id == Clients.id
        ).join(
            PaymentTypes, cls.model.payment_type_id == PaymentTypes.id
        )
        return session.execute(query.order_by(cls.model.number.desc())).scalars().all()

    @classmethod
    async def get_financier_metrics(cls, session: Session, filters: dict = None):
        try:
            metrics = {}
            # unpaid_filters = {k: v for k, v in (filters or {}).items() if k in ["approved", "status"]}
            unpaid_filters = {"approved": True, "status": [0, 1, 2, 3]}
            unpaid_requests = await cls.sum_count_query(session, unpaid_filters)
            metrics["unpaid_requests"] = unpaid_requests

            paid_filters = {"approved": True, "status": [5]}
            paid_requests = await cls.sum_count_query(session, paid_filters)
            metrics["paid_requests"] = paid_requests

            department_filters = {k: v for k, v in (filters or {}).items() if k in ["start_date", "finish_date"]}
            base_query = await cls.get_all(session, department_filters)
            # Apply additional joins to the base query
            join_query = base_query.join(Departments, cls.model.department_id == Departments.id)
            # Subquery selecting required columns including department_name
            subq = join_query.with_only_columns(
                Departments.name.label("department_name"),
                cls.model.id,
                cls.model.sum,
                cls.model.status
            ).subquery()

            # Replace the SELECT part with aggregates
            department_requests = select(
                subq.c.department_name,
                func.count(subq.c.id).label("total_requests"),
                func.sum(subq.c.sum).label("total_sum"),
                func.sum(
                    case((subq.c.status == 5, 1), else_=0)
                ).label("paid_requests"),  # Number of requests with status = 5
                (
                    (func.sum(case((subq.c.status == 5, 1), else_=0)) / func.count(subq.c.id)) * 100
                ).label("paid_requests_percent")
            ).select_from(
                subq
            ).group_by(
                subq.c.department_name
            )
            department_requests = session.execute(department_requests).all()
            metrics["department_metrics"] = [
                {
                    "department_name": row.department_name,
                    "total_requests": row.total_requests,
                    "total_sum": float(row.total_sum or 0),
                    "paid_requests": row.paid_requests,
                    "paid_requests_percent": float(row.paid_requests_percent or 0)
                }
                for row in department_requests
            ]

            return metrics

        except SQLAlchemyError as e:
            print("SQLAlchemyError: \n", e)
            return None



class ContractDAO(BaseDAO):
    model = Contracts


class InvoiceDAO(BaseDAO):
    model = Invoices


class FileDAO(BaseDAO):
    model = Files


class LogDAO(BaseDAO):
    model = Logs


class LimitDAO(BaseDAO):
    model = Limits


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
    async def get_filtered_budget_sum(cls, session: Session, department_id, expense_type_id, start_date: date, finish_date: date):
        result = session.query(
            func.sum(Transactions.value)
        ).join(
            Budgets, Transactions.budget_id == Budgets.id
        ).filter(
            and_(
                Budgets.department_id == department_id,
                Budgets.expense_type_id == expense_type_id,
                Transactions.status == 5,
                start_date >= Budgets.start_date,
                start_date <= Budgets.finish_date,
                finish_date >= Budgets.start_date,
                finish_date <= Budgets.finish_date
                # Budgets.start_date.between(start_date, finish_date),
                # Budgets.finish_date.between(start_date, finish_date)
            )
        ).first()
        return result


    @classmethod
    async def get_filtered_budget_expense(cls, session: Session, department_id, expense_type_id, start_date: date, finish_date: date):

        if start_date == finish_date:
            current_year = float(start_date.year)
            current_month = float(start_date.month)

            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).join(
                ExpenseTypes, Requests.expense_type_id == ExpenseTypes.id
            ).filter(
                and_(
                    and_(
                        Requests.department_id == department_id,
                        Requests.expense_type_id == expense_type_id,
                        Transactions.status != 4,
                        Requests.status != 4,
                        func.date_part('year', Requests.payment_time) == current_year,
                        func.date_part('month', Requests.payment_time) == current_month
                    ),
                    or_(
                        Requests.approved == True,
                        and_(
                            Requests.approved == False,
                            ExpenseTypes.purchasable == True,
                        )
                    )
                )
                # or_(
                #     and_(
                #         Requests.department_id == department_id,
                #         Requests.expense_type_id == expense_type_id,
                #         Transactions.status != 4,
                #         Requests.status != 4,
                #         Requests.approved == True,
                #         # func.date(Requests.payment_time).between(start_date, finish_date)
                #         func.date_part('year', Requests.payment_time) == current_year,
                #         func.date_part('month', Requests.payment_time) == current_month
                #     ),
                #     and_(
                #         Requests.department_id == department_id,
                #         Requests.expense_type_id == expense_type_id,
                #         Transactions.status != 4,
                #         Requests.status != 4,
                #         Requests.approved == False,
                #         ExpenseTypes.purchasable == True,
                #         func.date_part('year', Requests.payment_time) == current_year,
                #         func.date_part('month', Requests.payment_time) == current_month
                #     )
                # )
            ).first()

        else:
            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).join(
                ExpenseTypes, Requests.expense_type_id == ExpenseTypes.id
            ).filter(
                and_(
                    and_(
                        Requests.department_id == department_id,
                        Requests.expense_type_id == expense_type_id,
                        Transactions.status != 4,
                        Requests.status != 4,
                        func.date(Requests.payment_time).between(start_date, finish_date)
                    ),
                    or_(
                        Requests.approved == True,
                        and_(
                            Requests.approved == False,
                            ExpenseTypes.purchasable == True,
                        )
                    )
                )
            ).first()

        return result

    @classmethod
    async def get_budget_delayed_sum(cls, session: Session, department_id, expense_type_id, start_date: date, finish_date: date):

        if start_date == finish_date:
            current_year = float(start_date.year)
            current_month = float(start_date.month)

            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).filter(
                and_(
                    Requests.department_id == department_id,
                    Requests.expense_type_id == expense_type_id,
                    Transactions.status == 6,
                    Requests.status == 6,
                    Requests.approved == True,
                    func.date_part('year', Requests.payment_time) == current_year,
                    func.date_part('month', Requests.payment_time) == current_month
                )
            ).first()

        else:
            result = session.query(
                func.sum(Transactions.value)
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).filter(
                and_(
                    Requests.department_id == department_id,
                    Requests.expense_type_id == expense_type_id,
                    Transactions.status == 6,
                    Requests.status == 6,
                    Requests.approved == True,
                    func.date(Requests.payment_time).between(start_date, finish_date)
                )
            ).first()

        return result

    @classmethod
    async def get_budget_by_attributes(cls, session: Session, department_id, expense_type_id, created_date: date):
        result = session.query(
            Budgets
        ).filter(
            and_(
                Budgets.department_id == department_id,
                Budgets.expense_type_id == expense_type_id,
                created_date >= Budgets.start_date,
                created_date <= Budgets.finish_date
            )
        ).first()
        return result


    @classmethod
    async def get_calendar_budget_details(
            cls,
            session: Session,
            start_date,
            finish_date,
            budget_id,
            department_id,
            expense_type_id,
            days
    ):
        # --- CTE 1: Date Series ---
        date_series_cte = select(
            func.date(
                func.generate_series(
                    start_date,
                    finish_date,
                    literal_column("interval '1 day'")
                )
            ).label("date")
        ).cte("date_series")

        # --- CTE 2: Transactions Aggregated By Date ---
        tx_date = func.date(Transactions.created_at)

        if days > 1:
            # Subquery to calculate budget
            budget_scalar = (
                select((func.sum(Transactions.value) / days).label("daily_budget"))
                .where(
                    and_(
                        Transactions.value > 0,
                        Transactions.status == 5,
                        Transactions.budget_id == budget_id
                    )
                )
                .scalar_subquery()
            )
            transactions_cte = select(
                tx_date.label("date"),
                func.sum(case((Transactions.value < 0, -Transactions.value), else_=0)).label("expense")
            ).join(
                Requests, Transactions.request_id == Requests.id
            ).filter(
                and_(
                    Transactions.status == 5,
                    Requests.department_id == department_id,
                    Requests.expense_type_id == expense_type_id
                )
            ).group_by(tx_date).cte("tx_agg")

            # --- Final Query: Join transactions to date_series ---
            result_query = select(
                date_series_cte.c.date.label("date"),
                budget_scalar.label("budget"),
                func.coalesce(transactions_cte.c.expense, 0).label("expense"),
                (budget_scalar - func.coalesce(transactions_cte.c.expense, 0)).label("balance")
            ).select_from(
                date_series_cte.outerjoin(
                    transactions_cte,
                    transactions_cte.c.date == date_series_cte.c.date
                )
            ).order_by(date_series_cte.c.date)

        else:
            transactions_cte = select(
                tx_date.label("date"),
                func.sum(
                    case((Transactions.value > 0, Transactions.value), else_=0)
                ).label("budget"),
                func.sum(
                    case((Transactions.value < 0, -Transactions.value), else_=0)
                ).label("expense"),
                func.sum(Transactions.value).label("balance")
            ).outerjoin(
                Requests, Transactions.request_id == Requests.id
            ).filter(
                and_(
                    Transactions.status == 5,
                    or_(
                        Transactions.budget_id == budget_id,
                        and_(
                            Requests.department_id == department_id,
                            Requests.expense_type_id == expense_type_id
                        )
                    )
                )
            ).group_by(tx_date).cte("tx_agg")


            # --- Final Query: Join transactions to date_series ---
            result_query = select(
                date_series_cte.c.date.label("date"),
                transactions_cte.c.budget.label("budget"),
                func.coalesce(transactions_cte.c.expense, 0).label("expense"),
                func.coalesce(transactions_cte.c.balance, 0).label("balance")
            ).select_from(
                date_series_cte.outerjoin(
                    transactions_cte,
                    transactions_cte.c.date == date_series_cte.c.date
                )
            ).order_by(date_series_cte.c.date)

        results = session.execute(result_query).fetchall()
        return results


class TransactionDAO(BaseDAO):
    model = Transactions

    @classmethod
    async def get_department_transactions(cls, session: Session, department_id, start_date, finish_date, page, size):
        result = session.query(
            Transactions
        ).outerjoin(
            Budgets, Transactions.budget_id == Budgets.id
        ).outerjoin(
            Requests, Transactions.request_id == Requests.id
        ).filter(
            or_(
                Budgets.department_id == department_id,
                Requests.department_id == department_id
            )
        )
        if start_date is not None and finish_date is not None:
            result = result.filter(
                # func.date(Transactions.created_at).between(start_date, finish_date)
                func.date(Requests.payment_time).between(start_date, finish_date)
            )

        result = result.order_by(
            Transactions.created_at.desc()
        ).offset((page - 1) * size).limit(size).all()
        return result

    @classmethod
    async def get_department_all_transactions(cls, session: Session, department_id, start_date, finish_date):
        total_transactions = session.query(
            Transactions
        ).outerjoin(
            Budgets, Transactions.budget_id == Budgets.id
        ).outerjoin(
            Requests, Transactions.request_id == Requests.id
        ).filter(
            or_(
                Budgets.department_id == department_id,
                Requests.department_id == department_id
            )
        )
        if start_date is not None and finish_date is not None:
            total_transactions = total_transactions.filter(
                # func.date(Transactions.created_at).between(start_date, finish_date)
                func.date(Requests.payment_time).between(start_date, finish_date)
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
            func.sum(-Transactions.value),
            func.coalesce(func.sum(Limits.value), 0)
        ).join(
            Requests, Transactions.request_id == Requests.id
        ).join(
            PaymentTypes, Requests.payment_type_id == PaymentTypes.id
        ).join(
            Limits,
            func.date(Requests.payment_time).between(Limits.start_date, Limits.finish_date),
            isouter=True
        ).filter(
            and_(
                func.date(Requests.payment_time).between(start_date, finish_date),
                Transactions.status.in_([1, 2, 3, 5, 6])
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
