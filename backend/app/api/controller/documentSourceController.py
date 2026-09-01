# encoding: UTF-8
import os
import re
import uuid
import json as json_module
from datetime import datetime
from flask import current_app, g, Response, stream_with_context

from .baseCrudController import BaseCrudController
from ..model.documentSourceModel import DocumentSource
from ..model.productModel import Product
from ..model.projectModel import Project
from ..service.documentSourceService import DocumentSourceService


class DocumentSourceController(BaseCrudController):
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'markdown', 'docx', 'xlsx', 'xls'}

    def document_cancel_generate_cases(self):
        """取消正在进行的AI用例生成。"""
        from ..service.aiService import cancel_generation

        generation_id = self._get(self.req_data, 'generationId', 'generation_id')
        if not generation_id:
            return False, 'generationId 为必传参数'
        cancel_generation(generation_id)
        return True, ''

    def document_generation_status(self):
        """查询当前AI用例生成状态，供页面刷新后恢复进度。"""
        from ..service.aiService import get_generation_status

        generation_id = self._get(self.req_data, 'generationId', 'generation_id')
        project_id = self._get(self.req_data, 'projectId', 'project_id')
        status = get_generation_status(generation_id=generation_id, project_id=project_id)
        return status or {'status': 'idle'}

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
    
    def document_generate_cases_streaming(self):
        """SSE流式生成测试用例，实时返回进度"""
        from ..service.aiService import AIService, clear_cancel_generation, init_generation_status, update_generation_status
        from ..dao.documentSourceDao import DocumentSourceDao
        from common.sqlSession import SqlSession

        document_id = self._get(self.req_data, 'documentId', 'id')
        document_ids = self._get(self.req_data, 'documentIds', 'document_ids', default=[])
        generation_id = self._get(self.req_data, 'generationId', 'generation_id') or str(uuid.uuid4())
        resume_mode = self._get(self.req_data, 'resumeMode', 'resume_mode', default='resume')

        if document_id:
            document_ids = [document_id]

        if not document_ids or not isinstance(document_ids, list) or len(document_ids) == 0:
            return self._make_sse_error('documentId 或 documentIds 为必传参数')

        project_id = self._get(self.req_data, 'projectId', 'project_id')
        user_id = getattr(g, 'current_user_id', None) or self._get(self.req_data, 'userId', 'user_id')

        if not project_id:
            return self._make_sse_error('projectId 为必传参数')
        if not user_id:
            return self._make_sse_error('未获取到当前登录用户')

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

        clear_cancel_generation(generation_id)
        init_generation_status(generation_id, project_id=project_id, document_ids=document_ids)

        def generate():
            session_closed = False
            failed_docs = []

            def emit(event_type, data):
                update_generation_status(generation_id, event_type, data)
                return self._sse_event(event_type, data)

            try:
                yield emit("start", {
                    "message": "开始AI生成测试用例",
                    "generationId": generation_id,
                    "totalDocs": len(document_ids),
                    "failedDocs": failed_docs
                })
                yield emit("preparing", {
                    "message": "正在解析文档并准备生成上下文",
                    "generationId": generation_id,
                    "totalDocs": len(document_ids)
                })

                combined_content = []
                for doc_id in document_ids:
                    document = DocumentSourceDao.get_by_id(self.session, doc_id)
                    if not document:
                        failed_docs.append({'documentId': doc_id, 'error': '文档不存在'})
                        continue
                    content = document.content
                    if document.type in (
                        DocumentSourceService.DOCUMENT_TYPE_PDF,
                        DocumentSourceService.DOCUMENT_TYPE_EXCEL,
                        DocumentSourceService.DOCUMENT_TYPE_MARKDOWN
                    ) and not content:
                        file_path = os.path.join(os.getcwd(), document.source)
                        if not os.path.exists(file_path):
                            failed_docs.append({'documentId': doc_id, 'error': '文件不存在'})
                            continue
                        content = DocumentSourceService.extract_document_content(document)
                        if not content:
                            failed_docs.append({'documentId': doc_id, 'error': '文档内容为空'})
                            continue
                        DocumentSourceDao.update_by_id(self.session, doc_id, {
                            'content': content,
                            'status': DocumentSourceService.DOCUMENT_STATUS_PARSED
                        })
                    if not content:
                        failed_docs.append({'documentId': doc_id, 'error': '文档内容为空'})
                        continue
                    combined_content.append(f"【文档ID: {doc_id}】\n{content}\n")

                if failed_docs and not combined_content:
                    yield emit('error', {'message': '所有文档解析失败: ' + '; '.join(f.get('error', '') for f in failed_docs)})
                    return

                if not combined_content:
                    yield emit('error', {'message': '没有可处理的文档内容'})
                    return

                merged_content = "\n---\n".join(combined_content)
                context_template, context_err = DocumentSourceService._attach_generation_context(self.session, template)
                if context_err:
                    yield emit('error', {'message': context_err})
                    return
                resume_context = DocumentSourceService.build_existing_case_resume_context(self.session, int(project_id))
                if resume_context:
                    context_template['existing_case_context'] = resume_context

                self.session.commit()

                self.close_session()
                session_closed = True

                yield emit("prepared", {
                    "message": "文档解析完成，开始AI分段生成",
                    "generationId": generation_id,
                    "failedDocs": failed_docs
                })

                all_cases = []
                has_error = False

                for event in AIService.generate_test_cases_streaming(
                    merged_content,
                    context_template,
                    session_factory=SqlSession,
                    document_id=document_ids[0],
                    user_id=user_id,
                    generation_id=generation_id,
                    document_ids=document_ids,
                    resume_mode=resume_mode
                ):
                    event_type = event.get("type")

                    if event_type == "agent_plan":
                        yield emit("agent_plan", {
                            "totalChunks": event.get("totalChunks", 0),
                            "originalTotalChunks": event.get("originalTotalChunks", event.get("totalChunks", 0)),
                            "resumeSkippedCount": event.get("resumeSkippedCount", 0),
                            "agentCount": event.get("agentCount", 0),
                            "message": event.get("message", "已拆分测试点任务")
                        })

                    elif event_type == "agent_log":
                        yield emit("agent_log", {
                            "level": event.get("level", "info"),
                            "agentName": event.get("agentName", ""),
                            "chunkIndex": event.get("chunkIndex"),
                            "totalChunks": event.get("totalChunks"),
                            "chunkTitle": event.get("chunkTitle", ""),
                            "message": event.get("message", "")
                        })

                    elif event_type == "agent_start":
                        yield emit("agent_start", {
                            "chunkIndex": event.get("chunkIndex", 0),
                            "totalChunks": event.get("totalChunks", 0),
                            "chunkTitle": event.get("chunkTitle", ""),
                            "agentName": event.get("agentName", "")
                        })

                    elif event_type == "chunk_start":
                        yield emit("chunk_start", {
                            "chunkIndex": event["chunkIndex"],
                            "totalChunks": event["totalChunks"],
                            "chunkTitle": event["chunkTitle"],
                            "totalCasesSoFar": event.get("totalCasesSoFar", 0)
                        })

                    elif event_type == "heartbeat":
                        yield emit("heartbeat", {
                            "chunkIndex": event.get("chunkIndex"),
                            "totalChunks": event.get("totalChunks"),
                            "chunkTitle": event.get("chunkTitle"),
                            "agentName": event.get("agentName", ""),
                            "elapsedSeconds": event.get("elapsedSeconds", 0),
                            "message": event.get("message", "AI仍在生成当前分段")
                        })


                    elif event_type == "ai_retry":
                        yield emit("ai_retry", {
                            "level": event.get("level", "warning"),
                            "agentName": event.get("agentName", ""),
                            "chunkIndex": event.get("chunkIndex"),
                            "totalChunks": event.get("totalChunks"),
                            "chunkTitle": event.get("chunkTitle"),
                            "retryCount": event.get("retryCount", 0),
                            "retryDelay": event.get("retryDelay", 0),
                            "message": event.get("message", "AI网关超时，等待后继续重试")
                        })

                    elif event_type == "progress":

                        chunk_cases = event.get("cases", [])
                        all_cases.extend(chunk_cases)
                        yield emit("progress", {
                            "chunkIndex": event["chunkIndex"],
                            "totalChunks": event["totalChunks"],
                            "chunkTitle": event["chunkTitle"],
                            "casesCount": event.get("casesCount", len(chunk_cases)),
                            "totalCasesSoFar": event["totalCasesSoFar"],
                            "importedCount": event.get("importedCount", 0),
                            "skippedCount": event.get("skippedCount", 0),
                            "totalSkipped": event.get("totalSkipped", 0),
                            "importError": event.get("importError", "")
                        })

                    elif event_type == "chunk_error":

                        has_error = True
                        yield emit("chunk_error", {
                            "chunkIndex": event["chunkIndex"],
                            "totalChunks": event["totalChunks"],
                            "chunkTitle": event.get("chunkTitle", ""),
                            "error": event["error"]
                        })

                    elif event_type == "cancelled":

                        yield emit("cancelled", {
                            "message": "已停止生成测试用例",
                            "generationId": generation_id,
                            "totalCases": event.get("totalCases", 0),
                            "importedCount": event.get("totalImported", 0),
                            "skippedCount": event.get("totalSkipped", 0),
                            "failedChunks": event.get("failedChunks", [])

                        })
                        return

                    elif event_type == "done":
                        final_cases = event.get("cases", [])
                        success_count = event.get("totalImported", 0)
                        status_session = SqlSession()
                        try:
                            for doc_id in document_ids:
                                if doc_id not in [f['documentId'] for f in failed_docs]:
                                    DocumentSourceDao.update_by_id(status_session, doc_id, {
                                        'status': DocumentSourceService.DOCUMENT_STATUS_GENERATED
                                    })
                            status_session.commit()
                        finally:
                            status_session.close()

                        yield emit("done", {
                            "totalCases": len(final_cases),
                            "importedCount": success_count,
                            "skippedCount": event.get("totalSkipped", 0),
                            "failedChunks": event.get("failedChunks", []),
                            "resumeSkippedCount": event.get("resumeSkippedCount", 0),
                            "message": event.get("message", ""),
                            "hasError": has_error
                        })


                    elif event_type == "error":
                        yield emit("error", {
                            "message": event.get("message", "未知错误"),
                            "failedChunks": event.get("failedChunks", [])
                        })
            except Exception as e:
                current_app.logger.error(f'流式生成用例失败: {str(e)}')
                yield emit("error", {"message": f"生成用例失败：{str(e)}"})
            finally:
                clear_cancel_generation(generation_id)
                if not session_closed:
                    self.close_session()

        headers = {
            'Cache-Control': 'no-cache, no-transform',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
        return Response(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)

    @staticmethod
    def _sse_event(event_type, data):
        payload = json_module.dumps(data, ensure_ascii=False)
        return f"data: {json_module.dumps({'event': event_type, 'data': data}, ensure_ascii=False)}\n\n"

    @staticmethod
    def _make_sse_error(message):
        data = json_module.dumps({'event': 'error', 'data': {'message': message}}, ensure_ascii=False)
        return Response(f"data: {data}\n\n", mimetype='text/event-stream')

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
            err_details = '; '.join([f.get('error', '未知错误') for f in failed_docs])
            return {'cases': [], 'total': 0, 'failed': failed_docs}, f'生成失败: {err_details}'
        
        if not all_cases:
            return {'cases': [], 'total': 0, 'failed': []}, 'AI未生成任何测试用例，请检查文档内容是否包含可测试的需求描述'
        
        # 直接导入到用例表，自动创建不存在的模块
        success_count, msg = DocumentSourceService.import_cases(
            self.session, 
            document_ids[0],  # 使用第一个文档ID作为关联
            all_cases, 
            user_id,
            auto_create_module=True  # 自动创建模块
        )
        
        if msg:
            return {'cases': all_cases, 'total': len(all_cases), 'failed': [{'error': msg}]}, f'导入失败: {msg}'
        
        # 提交事务
        self.session.commit()
        current_app.logger.info(f'AI生成用例导入成功: {success_count}条')
        
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
            return None, '不支持的文件格式，仅支持：pdf、xlsx、xls、md、markdown'
        
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

            # 根据扩展名决定 type：1=PDF，3=Excel，4=Markdown
            if ext in ('xlsx', 'xls'):
                document_type = DocumentSourceService.DOCUMENT_TYPE_EXCEL
            elif ext in ('md', 'markdown', 'txt'):
                document_type = DocumentSourceService.DOCUMENT_TYPE_MARKDOWN
            else:
                document_type = DocumentSourceService.DOCUMENT_TYPE_PDF

            content = ''
            if document_type == DocumentSourceService.DOCUMENT_TYPE_MARKDOWN:
                content = DocumentSourceService.extract_document_content(type('DocumentFile', (), {
                    'content': '',
                    'source': relative_path,
                    'type': document_type
                })())

            # 创建文档源记录
            data = {
                'product_id': product_id,
                'project_id': project_id,
                'source': relative_path,
                'type': document_type,
                'content': content,
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
