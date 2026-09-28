# encoding: UTF-8
from logger import logger
from ..model.chatIssueModel import ChatIssueImport, ChatIssueItem


class ChatIssueDao(object):
    @staticmethod
    def create(session, model_cls, add_info):
        obj = model_cls(**add_info)
        session.add(obj)
        err = session.done(close=False)
        if err:
            logger.warning('%s create failed: %s', model_cls.__name__, err)
            return None, '新增失败：{}'.format(err)
        return obj, ''

    @staticmethod
    def update_by_id(session, model_cls, obj_id, update_info, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        update_res = session.query(model_cls).filter(*filters).update(update_info, synchronize_session=False)
        err = session.done(close=False)
        if err:
            return 0, '更新失败：{}'.format(err)
        if not update_res:
            return 0, '未查询到对应记录'
        return int(obj_id), ''

    @staticmethod
    def get_by_id(session, model_cls, obj_id, soft_delete=True):
        filters = [model_cls.id == int(obj_id)]
        if soft_delete and hasattr(model_cls, 'is_delete'):
            filters.append(model_cls.is_delete == 0)
        return session.query(model_cls).filter(*filters).first()

    @staticmethod
    def list_imports(session, req_data):
        query = session.query(ChatIssueImport).filter(ChatIssueImport.is_delete == 0)
        product_id = ChatIssueDao._get(req_data, 'productId', 'product_id')
        project_id = ChatIssueDao._get(req_data, 'projectId', 'project_id')
        status = ChatIssueDao._get(req_data, 'status')
        keyword = ChatIssueDao._get(req_data, 'keyword')
        if product_id not in (None, ''):
            query = query.filter(ChatIssueImport.product_id == int(product_id))
        if project_id not in (None, ''):
            query = query.filter(ChatIssueImport.project_id == int(project_id))
        if status not in (None, ''):
            query = query.filter(ChatIssueImport.status == status)
        if keyword:
            like = '%{}%'.format(keyword)
            query = query.filter(
                (ChatIssueImport.title.like(like)) | (ChatIssueImport.session_no.like(like))
            )
        total = query.count()
        page, limit = ChatIssueDao._page(req_data)
        items = query.order_by(ChatIssueImport.created_time.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def list_items(session, import_id):
        return session.query(ChatIssueItem).filter(
            ChatIssueItem.import_id == int(import_id),
            ChatIssueItem.is_delete == 0,
        ).order_by(ChatIssueItem.sort_no.asc(), ChatIssueItem.id.asc()).all()

    @staticmethod
    def get_items_by_ids(session, import_id, item_ids):
        if not item_ids:
            return []
        ids = [int(x) for x in item_ids]
        return session.query(ChatIssueItem).filter(
            ChatIssueItem.import_id == int(import_id),
            ChatIssueItem.id.in_(ids),
            ChatIssueItem.is_delete == 0,
        ).order_by(ChatIssueItem.sort_no.asc(), ChatIssueItem.id.asc()).all()

    @staticmethod
    def _page(req_data):
        try:
            page = int(req_data.get('pageNo') or req_data.get('page') or 1)
        except Exception:
            page = 1
        try:
            limit = int(req_data.get('pageSize') or req_data.get('limit') or 20)
        except Exception:
            limit = 20
        return max(page, 1), min(max(limit, 1), 200)

    @staticmethod
    def _get(req_data, *keys):
        for key in keys:
            if key in req_data and req_data.get(key) not in (None,):
                return req_data.get(key)
        return None
