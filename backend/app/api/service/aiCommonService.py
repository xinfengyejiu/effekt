# encoding: UTF-8
import re
from datetime import datetime

from ..controller.baseCrudController import BaseCrudController
from ..dao.aiBaseDao import AiBaseDao
from ..model.productModel import Product
from ..model.projectModel import Project


class AiCommonService(object):
    VALID_STATUS = {1, 2, 3}

    @staticmethod
    def get(req_data, *keys, default=None):
        for key in keys:
            value = req_data.get(key)
            if value not in (None, ''):
                return value
        return default

    @staticmethod
    def gen_no(prefix):
        return f'{prefix}{datetime.now().strftime("%Y%m%d%H%M%S%f")[:20]}'

    @staticmethod
    def fill_product_project_names(session, data, req_data):
        product_id = AiCommonService.get(req_data, 'productId', 'product_id')
        project_id = AiCommonService.get(req_data, 'projectId', 'project_id')
        product_name = AiCommonService.get(req_data, 'productName', 'product_name')
        project_name = AiCommonService.get(req_data, 'projectName', 'project_name')
        if product_id not in (None, ''):
            data['product_id'] = int(product_id)
            if not product_name:
                product = session.query(Product).filter(Product.id == int(product_id), Product.is_delete == 0).first()
                product_name = product.name if product else ''
            data['product_name'] = product_name
        if project_id not in (None, ''):
            data['project_id'] = int(project_id)
            if not project_name:
                project = session.query(Project).filter(Project.id == int(project_id), Project.is_delete == 0).first()
                project_name = project.name if project else ''
            data['project_name'] = project_name
        return data

    @staticmethod
    def fill_product_project_list(session, items):
        rows = BaseCrudController.serialize_list(items)
        project_ids = [row.get('projectId') or row.get('project_id') for row in rows if row.get('projectId') or row.get('project_id')]
        product_ids = [row.get('productId') or row.get('product_id') for row in rows if row.get('productId') or row.get('product_id')]
        projects = {}
        products = {}
        if project_ids:
            project_rows = session.query(Project).filter(Project.id.in_([int(i) for i in project_ids]), Project.is_delete == 0).all()
            projects = {int(item.id): item for item in project_rows}
            product_ids.extend([item.product_id for item in project_rows if item.product_id])
        product_ids = [int(i) for i in product_ids if i]
        if product_ids:
            product_rows = session.query(Product).filter(Product.id.in_(list(set(product_ids))), Product.is_delete == 0).all()
            products = {int(item.id): item.name for item in product_rows}
        for row in rows:
            project_id = row.get('projectId') or row.get('project_id')
            project = projects.get(int(project_id)) if project_id else None
            if project:
                row['projectId'] = int(project.id)
                row['project_id'] = int(project.id)
                row['projectName'] = row.get('projectName') or row.get('project_name') or project.name
                row['project_name'] = row.get('project_name') or row.get('projectName') or project.name
                if not (row.get('productId') or row.get('product_id')) and project.product_id:
                    row['productId'] = int(project.product_id)
                    row['product_id'] = int(project.product_id)
            product_id = row.get('productId') or row.get('product_id')
            product_name = products.get(int(product_id)) if product_id else None
            if product_name:
                row['productName'] = row.get('productName') or row.get('product_name') or product_name
                row['product_name'] = row.get('product_name') or row.get('productName') or product_name
        return rows

    @staticmethod
    def list_result(items, total, session=None, with_product_project=False):
        if session and with_product_project:
            return {'list': AiCommonService.fill_product_project_list(session, items), 'total': total}
        return {'list': BaseCrudController.serialize_list(items), 'total': total}

    @staticmethod
    def create_record(session, model_cls, data, required_fields, unique_checker=None):
        for field in required_fields:
            if data.get(field) in (None, ''):
                return 0, f'{field} 为必传参数'
        if unique_checker:
            exists = unique_checker()
            if exists:
                return 0, '编码已存在'
        obj, err_msg = AiBaseDao.create(session, model_cls, data)
        if err_msg:
            return 0, err_msg
        return obj.id, ''

    @staticmethod
    def camel_to_snake(name):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    @staticmethod
    def pick_update_info(req_data, allowed_fields):
        update_info = {}
        for key, value in req_data.items():
            field = key if key in allowed_fields else AiCommonService.camel_to_snake(key)
            if field in allowed_fields:
                update_info[field] = value
        return update_info

    @staticmethod
    def update_record(session, model_cls, req_data, allowed_fields, id_keys=('id',)):
        obj_id = AiCommonService.get(req_data, *id_keys)
        if not obj_id:
            return 0, f'{id_keys[0]} 为必传参数'
        update_info = AiCommonService.pick_update_info(req_data, allowed_fields)
        if not update_info:
            return 0, '没有可更新字段'
        return AiBaseDao.update_by_id(session, model_cls, obj_id, update_info)

    @staticmethod
    def delete_record(session, model_cls, req_data, id_keys=('id',)):
        obj_id = AiCommonService.get(req_data, *id_keys)
        if not obj_id:
            return 0, f'{id_keys[0]} 为必传参数'
        return AiBaseDao.soft_delete(session, model_cls, obj_id)

    @staticmethod
    def detail_record(session, model_cls, obj_id):
        obj = AiBaseDao.get_by_id(session, model_cls, obj_id)
        if not obj:
            return {}, '未查询到对应记录！'
        return BaseCrudController.serialize(obj), ''
