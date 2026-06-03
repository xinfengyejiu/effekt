# encoding: UTF-8
import os
import re
import uuid
from datetime import datetime
from flask import current_app, g

from .baseCrudController import BaseCrudController
from ..model.documentSourceModel import DocumentSource
from ..model.productModel import Product
from ..model.projectModel import Project
from ..service.documentSourceService import DocumentSourceService


class DocumentSourceController(BaseCrudController):
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx'}

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def document_list(self):
        items, total = DocumentSourceService.list(self.session, self.req_data)
        return {'list': self.serialize_list(items, ['is_delete']), 'total': total}
    
    def document_detail(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return {}, 'documentId 为必传参数'
        item = DocumentSourceService.get_by_id(self.session, document_id)
        if not item:
            return {}, '未查询到对应文档！'
        return self.serialize(item, ['is_delete']), ''
    
    def document_create(self):
        product_id = self._get(self.req_data, 'productId', 'product_id')
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        source = self._get(self.req_data, 'source')
        
        if not product_id or not project_id or not source:
            return 0, 'productId、projectId、source 为必传参数'
        
        data = {
            'product_id': product_id,
            'project_id': project_id,
            'source': source,
            'type': self._get(self.req_data, 'type', default=1),
            'content': self._get(self.req_data, 'content', default=''),
            'created_by': self._get(self.req_data, 'createdBy', 'created_by')
        }
        
        return DocumentSourceService.create(self.session, data)
    
    def document_update(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return 0, 'documentId 为必传参数'
        
        data = {}
        fields = ['type', 'source', 'content', 'ai_model']
        for field in fields:
            value = self._get(self.req_data, field)
            if value is not None:
                data[field] = value
        
        return DocumentSourceService.update(self.session, document_id, data)
    
    def document_delete(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return 0, 'documentId 为必传参数'
        result, msg = DocumentSourceService.delete(self.session, document_id)
        if msg:
            return 0, msg
        err = self.session.done(close=False)
        if err:
            return 0, f'删除失败！{err}'
        return result, ''
    
    def document_refresh(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return False, 'documentId 为必传参数'
        return DocumentSourceService.refresh_content(self.session, document_id)
    
    def document_generate_cases(self):
        # 支持单个文档ID或多个文档ID
        document_id = self._get(self.req_data, 'documentId', 'id')
        document_ids = self._get(self.req_data, 'documentIds', 'document_ids', default=[])
        
        # 如果传了单个ID，转换为列表
        if document_id:
            document_ids = [document_id]
        
        if not document_ids or not isinstance(document_ids, list) or len(document_ids) == 0:
            return [], 'documentId 或 documentIds 为必传参数'
        
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        user_id = getattr(g, 'current_user_id', None) or self._get(self.req_data, 'userId', 'user_id')
        
        if not project_id:
            return [], 'projectId 为必传参数'
        if not user_id:
            return [], '未获取到当前登录用户'
        
        template = {
            'project_id': int(project_id),
            'priority': int(self._get(self.req_data, 'priority', default=2)),
            'case_type': int(self._get(self.req_data, 'caseType', 'case_type', default=1)),
            'tags': self._get(self.req_data, 'tags', default=['AI生成']),
            'skill_ids': self._get(self.req_data, 'skillIds', 'skill_ids', default=[]),
            'rule_ids': self._get(self.req_data, 'ruleIds', 'rule_ids', default=[])
        }
        
        if isinstance(template['tags'], str):
            template['tags'] = template['tags'].split(',')
        
        # 批量生成测试用例（合并多个文档内容）
        all_cases, failed_docs = DocumentSourceService.generate_cases_batch(
            self.session, document_ids, template
        )
        
        if failed_docs:
            return {'cases': [], 'total': 0, 'failed': failed_docs}, ''
        
        # 直接导入到用例表，自动创建不存在的模块
        success_count, msg = DocumentSourceService.import_cases(
            self.session, 
            document_ids[0],  # 使用第一个文档ID作为关联
            all_cases, 
            user_id,
            auto_create_module=True  # 自动创建模块
        )
        
        if msg:
            return {'cases': all_cases, 'total': len(all_cases), 'failed': [{'error': msg}]}, ''
        
        # 提交事务
        self.session.commit()
        
        return {
            'cases': all_cases, 
            'total': len(all_cases),
            'importedCount': success_count,
            'failed': []
        }, ''
    
    def document_match_modules(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        cases = self._get(self.req_data, 'cases', default=[])
        
        if not document_id:
            return [], 'documentId 为必传参数'
        
        document = DocumentSourceService.get_by_id(self.session, document_id)
        if not document:
            return [], '文档不存在'
        
        return DocumentSourceService.match_modules(self.session, document.project_id, cases), ''
    
    def document_import_cases(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        cases = self._get(self.req_data, 'cases', default=[])
        user_id = self._get(self.req_data, 'userId', 'user_id')
        
        if not document_id:
            return 0, 'documentId 为必传参数'
        
        if not isinstance(cases, list):
            return 0, 'cases 必须为数组'
        
        return DocumentSourceService.import_cases(self.session, document_id, cases, user_id)
    
    def document_batch_create_modules(self):
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        module_names = self._get(self.req_data, 'moduleNames', 'module_names', default=[])
        
        if not project_id:
            return [], 'projectId 为必传参数'
        
        if not isinstance(module_names, list):
            return [], 'moduleNames 必须为数组'
        
        modules = DocumentSourceService.batch_create_modules(self.session, project_id, module_names)
        return self.serialize_list(modules, ['is_delete']), ''
    
    def document_upload(self):
        if 'file' not in self.req_data.files:
            return None, '未找到上传文件'
        
        file = self.req_data.files['file']
        if file.filename == '':
            return None, '文件名不能为空'
        
        if not self.allowed_file(file.filename):
            return None, '不支持的文件格式，仅支持：pdf、txt、md、docx'
        
        # 文件上传使用 form 表单获取参数
        product_id = self.req_data.form.get('productId')
        project_id = self.req_data.form.get('projectId')
        created_by = self.req_data.form.get('createdBy')
        
        if not product_id or not project_id:
            return None, 'productId、projectId 为必传参数'
        
        # 获取产品和项目名称
        product = self.session.query(Product).filter(Product.id == int(product_id), Product.is_delete == 0).first()
        if not product:
            return None, '产品不存在'
        
        project = self.session.query(Project).filter(Project.id == int(project_id), Project.is_delete == 0).first()
        if not project:
            return None, '项目不存在'
        
        try:
            # 创建文件夹结构：uploads/{产品名称}/{项目名称}
            base_upload_path = os.path.join(os.getcwd(), self.UPLOAD_FOLDER)
            product_folder = os.path.join(base_upload_path, product.name)
            project_folder = os.path.join(product_folder, project.name)
            
            os.makedirs(project_folder, exist_ok=True)
            
            # 获取原始文件扩展名
            ext = file.filename.rsplit('.', 1)[1].lower()
            # 生成安全的文件名（保留原始文件名的主要部分，替换特殊字符）
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            # 从原始文件名中提取主名称（不包含扩展名）
            original_name = file.filename.rsplit('.', 1)[0]
            # 替换特殊字符为下划线，但保留中文字符
            safe_name = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', original_name)
            # 限制文件名长度，避免过长
            safe_name = safe_name[:50] if len(safe_name) > 50 else safe_name
            # 组合文件名
            new_filename = f'{timestamp}-{safe_name}-{uuid.uuid4().hex[:8]}.{ext}'
            
            # 保存文件
            file_path = os.path.join(project_folder, new_filename)
            file.save(file_path)
            
            # 计算相对路径用于数据库存储
            relative_path = os.path.join(self.UPLOAD_FOLDER, product.name, project.name, new_filename)
            # 转换为统一的路径格式
            relative_path = relative_path.replace('\\', '/')
            
            # 创建文档源记录
            data = {
                'product_id': product_id,
                'project_id': project_id,
                'source': relative_path,
                'type': 1,
                'content': '',
                'created_by': created_by
            }
            
            document_id, msg = DocumentSourceService.create(self.session, data)
            if msg:
                return None, msg
            
            # 提交事务
            self.session.commit()
            
            return {'documentId': document_id, 'filePath': relative_path}, ''
        except Exception as e:
            self.session.rollback()
            return None, f'文件上传失败：{str(e)}'
