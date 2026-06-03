# encoding: UTF-8
from flask import g

from .baseCrudController import BaseCrudController
from .documentSourceController import DocumentSourceController
from ..service.knowledgeService import KnowledgeService


class KnowledgeController(BaseCrudController):
    def document_list(self):
        rows, total = KnowledgeService.list_documents(self.session, self.req_data)
        items = []
        for document, chunk_count in rows:
            item = self.serialize(document, ['is_delete'])
            item['chunkCount'] = chunk_count
            item['knowledgeStatus'] = 1 if chunk_count else 0
            items.append(item)
        return {'list': items, 'total': total}

    def document_upload(self):
        controller = DocumentSourceController(self.req_data)
        controller.close_session()
        try:
            controller.session = self.session
            ret, err_msg = controller.document_upload()
            if err_msg:
                return None, err_msg
            auto_parse = self.req_data.form.get('autoParse')
            if str(auto_parse).lower() in ('1', 'true', 'yes'):
                parse_ret, parse_err = KnowledgeService.parse_document_to_chunks(self.session, ret.get('documentId'))
                if parse_err:
                    return ret, parse_err
                ret.update(parse_ret)
            self.session.commit()
            return ret, ''
        except Exception as e:
            self.session.rollback()
            return None, f'上传失败：{str(e)}'

    def document_parse(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return {}, 'documentId 为必传参数'
        try:
            ret, err_msg = KnowledgeService.parse_document_to_chunks(self.session, document_id)
            if err_msg:
                self.session.rollback()
                return {}, err_msg
            self.session.commit()
            return ret, ''
        except Exception as e:
            self.session.rollback()
            return {}, f'解析入库失败：{str(e)}'

    def document_delete(self):
        document_id = self._get(self.req_data, 'documentId', 'id')
        if not document_id:
            return 0, 'documentId 为必传参数'
        from ..service.documentSourceService import DocumentSourceService
        try:
            result, msg = DocumentSourceService.delete(self.session, document_id)
            if msg:
                self.session.rollback()
                return 0, msg
            KnowledgeService.soft_delete_document_chunks(self.session, document_id)
            self.session.commit()
            return result, ''
        except Exception as e:
            self.session.rollback()
            return 0, f'删除失败：{str(e)}'

    def search(self):
        return KnowledgeService.search(self.session, self.req_data)

    def chat(self):
        req_data = dict(self.req_data or {})
        if 'createdBy' not in req_data and getattr(g, 'current_user_id', None):
            req_data['createdBy'] = getattr(g, 'current_user_id')
        try:
            ret, err_msg = KnowledgeService.chat(self.session, req_data)
            if err_msg:
                self.session.rollback()
                return {}, err_msg
            self.session.commit()
            return ret, ''
        except Exception as e:
            self.session.rollback()
            return {}, f'问答失败：{str(e)}'

    def session_list(self):
        items, total = KnowledgeService.list_sessions(self.session, self.req_data)
        return {'list': self.serialize_list(items, ['is_delete']), 'total': total}

    def message_list(self):
        items, err_msg = KnowledgeService.list_messages(self.session, self.req_data)
        if err_msg:
            return [], err_msg
        return self.serialize_list(items, ['is_delete']), ''

    def session_delete(self):
        try:
            ret, err_msg = KnowledgeService.delete_session(self.session, self.req_data)
            if err_msg:
                self.session.rollback()
                return 0, err_msg
            self.session.commit()
            return ret, ''
        except Exception as e:
            self.session.rollback()
            return 0, f'删除会话失败：{str(e)}'

    def model_setting_detail(self):
        return KnowledgeService.get_model_setting(self.session, self.req_data), ''

    def model_setting_save(self):
        try:
            setting_id, err_msg = KnowledgeService.save_model_setting(self.session, self.req_data)
            if err_msg:
                self.session.rollback()
                return 0, err_msg
            self.session.commit()
            return setting_id, ''
        except Exception as e:
            self.session.rollback()
            return 0, f'保存模型设置失败：{str(e)}'

    def model_setting_test(self):
        setting = KnowledgeService.get_model_setting(self.session, self.req_data)
        from ..service.aiService import AIService
        answer, err_msg = AIService.chat_with_context('请回复：连接正常', [], setting)
        if err_msg:
            return {'success': False, 'message': err_msg}, ''
        return {'success': True, 'message': answer[:200]}, ''
