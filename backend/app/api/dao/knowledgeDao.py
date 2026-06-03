# encoding: UTF-8
from sqlalchemy import func, or_

from ..model.documentSourceModel import DocumentSource
from ..model.knowledgeModel import KnowledgeChunk, KnowledgeChatSession, KnowledgeChatMessage, KnowledgeModelSetting


class KnowledgeDao:
    @staticmethod
    def create(session, item):
        session.add(item)
        session.flush()
        return item.id

    @staticmethod
    def soft_delete_chunks_by_document(session, document_id):
        return session.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == int(document_id),
            KnowledgeChunk.is_delete == 0
        ).update({'is_delete': 1})

    @staticmethod
    def count_chunks_by_document(session, document_id):
        return session.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == int(document_id),
            KnowledgeChunk.is_delete == 0,
            KnowledgeChunk.status == 1
        ).count()

    @staticmethod
    def count_chunks_by_documents(session, document_ids):
        if not document_ids:
            return {}
        rows = session.query(KnowledgeChunk.document_id, func.count(KnowledgeChunk.id)).filter(
            KnowledgeChunk.document_id.in_([int(i) for i in document_ids]),
            KnowledgeChunk.is_delete == 0,
            KnowledgeChunk.status == 1
        ).group_by(KnowledgeChunk.document_id).all()
        return {row[0]: row[1] for row in rows}

    @staticmethod
    def list_documents_with_chunk_count(session, filters, page_no=1, page_size=20):
        subq = session.query(
            KnowledgeChunk.document_id.label('document_id'),
            func.count(KnowledgeChunk.id).label('chunk_count')
        ).filter(
            KnowledgeChunk.is_delete == 0,
            KnowledgeChunk.status == 1
        ).group_by(KnowledgeChunk.document_id).subquery()
        query = session.query(DocumentSource, func.coalesce(subq.c.chunk_count, 0)).outerjoin(
            subq, DocumentSource.id == subq.c.document_id
        ).filter(*filters).order_by(DocumentSource.created_time.desc())
        total = query.count()
        rows = query.offset((page_no - 1) * page_size).limit(page_size).all()
        return rows, total

    @staticmethod
    def query_chunks(session, product_id=None, project_id=None, document_ids=None, keyword=None, limit=200):
        filters = KnowledgeDao._chunk_scope_filters(product_id, project_id, document_ids)
        if keyword:
            filters.append(or_(KnowledgeChunk.title.ilike(f'%{keyword}%'), KnowledgeChunk.content.ilike(f'%{keyword}%')))
        return session.query(KnowledgeChunk).filter(*filters).order_by(KnowledgeChunk.updated_time.desc()).limit(limit).all()

    @staticmethod
    def query_chunks_by_keywords(session, product_id=None, project_id=None, document_ids=None, keywords=None, limit=300):
        filters = KnowledgeDao._chunk_scope_filters(product_id, project_id, document_ids)
        keyword_filters = []
        for keyword in keywords or []:
            if keyword:
                keyword_filters.append(or_(KnowledgeChunk.title.ilike(f'%{keyword}%'), KnowledgeChunk.content.ilike(f'%{keyword}%')))
        if keyword_filters:
            filters.append(or_(*keyword_filters))
        return session.query(KnowledgeChunk).filter(*filters).order_by(KnowledgeChunk.updated_time.desc()).limit(limit).all()

    @staticmethod
    def list_scope_chunks(session, product_id=None, project_id=None, document_ids=None, limit=1000):
        filters = KnowledgeDao._chunk_scope_filters(product_id, project_id, document_ids)
        return session.query(KnowledgeChunk).filter(*filters).order_by(KnowledgeChunk.updated_time.desc()).limit(limit).all()

    @staticmethod
    def _chunk_scope_filters(product_id=None, project_id=None, document_ids=None):
        filters = [KnowledgeChunk.is_delete == 0, KnowledgeChunk.status == 1]
        if product_id:
            filters.append(KnowledgeChunk.product_id == int(product_id))
        if project_id:
            filters.append(KnowledgeChunk.project_id == int(project_id))
        if document_ids:
            filters.append(KnowledgeChunk.document_id.in_([int(i) for i in document_ids]))
        return filters

    @staticmethod
    def get_setting(session, scope_type, scope_id):
        return session.query(KnowledgeModelSetting).filter(
            KnowledgeModelSetting.scope_type == scope_type,
            KnowledgeModelSetting.scope_id == int(scope_id or 0),
            KnowledgeModelSetting.is_delete == 0,
            KnowledgeModelSetting.status == 1
        ).order_by(KnowledgeModelSetting.updated_time.desc()).first()

    @staticmethod
    def upsert_setting(session, scope_type, scope_id, data):
        item = KnowledgeDao.get_setting(session, scope_type, scope_id)
        if not item:
            item = KnowledgeModelSetting(scope_type=scope_type, scope_id=int(scope_id or 0), is_delete=0)
            session.add(item)
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        session.flush()
        return item.id

    @staticmethod
    def list_sessions(session, product_id=None, project_id=None, page_no=1, page_size=20):
        filters = [KnowledgeChatSession.is_delete == 0]
        if product_id:
            filters.append(KnowledgeChatSession.product_id == int(product_id))
        if project_id:
            filters.append(KnowledgeChatSession.project_id == int(project_id))
        query = session.query(KnowledgeChatSession).filter(*filters).order_by(KnowledgeChatSession.updated_time.desc())
        total = query.count()
        return query.offset((page_no - 1) * page_size).limit(page_size).all(), total

    @staticmethod
    def list_messages(session, session_id):
        return session.query(KnowledgeChatMessage).filter(
            KnowledgeChatMessage.session_id == int(session_id),
            KnowledgeChatMessage.is_delete == 0
        ).order_by(KnowledgeChatMessage.created_time.asc()).all()

    @staticmethod
    def delete_session(session, session_id):
        session.query(KnowledgeChatMessage).filter(KnowledgeChatMessage.session_id == int(session_id)).update({'is_delete': 1})
        return session.query(KnowledgeChatSession).filter(
            KnowledgeChatSession.id == int(session_id),
            KnowledgeChatSession.is_delete == 0
        ).update({'is_delete': 1})
