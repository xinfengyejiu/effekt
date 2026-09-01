# encoding: UTF-8
from sqlalchemy import func, cast, Date

from ..model.bugModel import Bug, BugComment, BugHistory
from ..model.userModel import User
from ..model.caseModel import Module
from logger import logger


class BugDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning(f'{model_cls.__name__}新增失败！{err}')
            return 0, f'新增失败！{err}'
        return obj.id, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info)
        err = session.done(close=False)
        if err:
            logger.error(f'{model_cls.__name__}更新失败！id: {obj_id}, err: {err}')
            return 0, f'更新失败！{err}'
        if not update_res:
            return 0, '未查询到对应记录！'
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_by_filters(session, model_cls, filter_list, page=1, limit=20, order_column=None, asc=False):
        query = session.query(model_cls).filter(*filter_list)
        if hasattr(model_cls, 'is_delete'):
            query = query.filter(model_cls.is_delete == 0)
        total = query.count()
        if order_column is not None:
            order_expr = order_column.asc() if asc else order_column.desc()
            if hasattr(model_cls, 'id'):
                id_order_expr = model_cls.id.asc() if asc else model_cls.id.desc()
                query = query.order_by(order_expr, id_order_expr)
            else:
                query = query.order_by(order_expr)
        rets = query.offset((int(page) - 1) * int(limit)).limit(int(limit)).all()
        return rets, total

    @staticmethod
    def delete_by_id(session, model_cls, obj_id):
        return BugDao.update_by_id(session, model_cls, obj_id, {'is_delete': 1})

    @staticmethod
    def generate_bug_key(session):
        max_key = session.query(func.max(Bug.bug_key)).filter(Bug.bug_key.like('BUG-%')).scalar()
        if max_key:
            num = int(max_key.split('-')[1]) + 1
        else:
            num = 1
        return f'BUG-{num:03d}'

    @staticmethod
    def get_comments(session, bug_id):
        return session.query(BugComment).filter(
            BugComment.bug_id == int(bug_id),
            BugComment.is_delete == 0
        ).order_by(BugComment.created_time.desc()).all()

    @staticmethod
    def get_history(session, bug_id):
        return session.query(BugHistory).filter(
            BugHistory.bug_id == int(bug_id)
        ).order_by(BugHistory.created_time.desc()).all()

    @staticmethod
    def add_history(session, bug_id, field_name, old_value, new_value, operator_id):
        session.add(BugHistory(
            bug_id=bug_id,
            field_name=field_name,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            operator_id=operator_id
        ))
        err = session.done(close=False)
        if err:
            logger.warning(f'BugHistory新增失败！{err}')
            return False
        return True

    @staticmethod
    def get_stats(session, product_id=None, project_id=None):
        query = session.query(Bug).filter(Bug.is_delete == 0)
        if product_id:
            query = query.filter(Bug.product_id == int(product_id))
        if project_id:
            query = query.filter(Bug.project_id == int(project_id))

        total = query.count()
        new_count = query.filter(Bug.status == 0).count()
        pending_count = query.filter(Bug.status == 1).count()
        in_progress_count = query.filter(Bug.status == 2).count()
        resolved_count = query.filter(Bug.status == 3).count()
        closed_count = query.filter(Bug.status == 4).count()
        rejected_count = query.filter(Bug.status == 5).count()

        by_status = {}
        for status in range(6):
            by_status[str(status)] = query.filter(Bug.status == status).count()

        by_solution = {}
        solution_results = session.query(
            Bug.solution, func.count(Bug.id)
        ).filter(Bug.is_delete == 0)
        if product_id:
            solution_results = solution_results.filter(Bug.product_id == int(product_id))
        if project_id:
            solution_results = solution_results.filter(Bug.project_id == int(project_id))
        solution_results = solution_results.filter(Bug.solution.isnot(None)).group_by(Bug.solution).all()
        for solution, count in solution_results:
            by_solution[solution] = count

        by_reporter = {}
        reporter_results = session.query(
            User.real_name, func.count(Bug.id)
        ).join(User, Bug.reporter_id == User.id).filter(Bug.is_delete == 0)
        if product_id:
            reporter_results = reporter_results.filter(Bug.product_id == int(product_id))
        if project_id:
            reporter_results = reporter_results.filter(Bug.project_id == int(project_id))
        reporter_results = reporter_results.group_by(User.real_name).all()
        for name, count in reporter_results:
            by_reporter[name] = count

        by_assignee = {}
        assignee_results = session.query(
            User.real_name, func.count(Bug.id)
        ).outerjoin(User, Bug.assignee_id == User.id).filter(Bug.is_delete == 0)
        if product_id:
            assignee_results = assignee_results.filter(Bug.product_id == int(product_id))
        if project_id:
            assignee_results = assignee_results.filter(Bug.project_id == int(project_id))
        assignee_results = assignee_results.group_by(User.real_name).all()
        for name, count in assignee_results:
            by_assignee[name or '未指派'] = count

        by_resolver = {}
        resolver_results = session.query(
            User.real_name, func.count(Bug.id)
        ).outerjoin(User, Bug.resolved_by == User.id).filter(Bug.is_delete == 0)
        if product_id:
            resolver_results = resolver_results.filter(Bug.product_id == int(product_id))
        if project_id:
            resolver_results = resolver_results.filter(Bug.project_id == int(project_id))
        resolver_results = resolver_results.group_by(User.real_name).all()
        for name, count in resolver_results:
            by_resolver[name or '未解决'] = count

        by_module = {}
        module_results = session.query(
            Module.name, func.count(Bug.id)
        ).outerjoin(Module, Bug.module_id == Module.id).filter(Bug.is_delete == 0)
        if product_id:
            module_results = module_results.filter(Bug.product_id == int(product_id))
        if project_id:
            module_results = module_results.filter(Bug.project_id == int(project_id))
        module_results = module_results.group_by(Module.name).all()
        for name, count in module_results:
            by_module[name or '未分类'] = count

        by_version = {}
        version_results = session.query(
            Bug.resolve_version, func.count(Bug.id)
        ).filter(Bug.is_delete == 0)
        if product_id:
            version_results = version_results.filter(Bug.product_id == int(product_id))
        if project_id:
            version_results = version_results.filter(Bug.project_id == int(project_id))
        version_results = version_results.filter(Bug.resolve_version.isnot(None)).group_by(Bug.resolve_version).all()
        for version, count in version_results:
            by_version[version] = count

        by_activation = {}

        daily_new = {}
        daily_new_results = session.query(
            cast(Bug.created_time, Date).label('stat_date'),
            func.count(Bug.id)
        ).filter(Bug.is_delete == 0)
        if product_id:
            daily_new_results = daily_new_results.filter(Bug.product_id == int(product_id))
        if project_id:
            daily_new_results = daily_new_results.filter(Bug.project_id == int(project_id))
        daily_new_results = daily_new_results.group_by('stat_date').order_by('stat_date').all()
        for date, count in daily_new_results:
            daily_new[str(date)] = count

        daily_resolved = {}

        daily_closed = {}

        return {
            'total': total,
            'new': new_count,
            'pending': pending_count,
            'in_progress': in_progress_count,
            'resolved': resolved_count,
            'closed': closed_count,
            'rejected': rejected_count,
            'by_status': by_status,
            'by_solution': by_solution,
            'by_reporter': by_reporter,
            'by_assignee': by_assignee,
            'by_resolver': by_resolver,
            'by_module': by_module,
            'by_version': by_version,
            'by_activation': by_activation,
            'daily_new': daily_new,
            'daily_resolved': daily_resolved,
            'daily_closed': daily_closed
        }
