# encoding: UTF-8
import math
import os
import re

from ..dao.documentSourceDao import DocumentSourceDao
from ..dao.knowledgeDao import KnowledgeDao
from ..model.documentSourceModel import DocumentSource
from ..model.knowledgeModel import KnowledgeChunk, KnowledgeChatSession, KnowledgeChatMessage
from .aiService import AIService
from .documentSourceService import DocumentSourceService


class KnowledgeService:
    DEFAULT_TOP_K = 5

    @staticmethod
    def list_documents(session, req_data):
        filters = [DocumentSource.is_delete == 0]
        product_id = req_data.get('productId') or req_data.get('product_id')
        project_id = req_data.get('projectId') or req_data.get('project_id')
        status = req_data.get('status')
        keyword = req_data.get('keyword')
        if product_id:
            filters.append(DocumentSource.product_id == int(product_id))
        if project_id:
            filters.append(DocumentSource.project_id == int(project_id))
        if status not in (None, ''):
            filters.append(DocumentSource.status == int(status))
        if keyword:
            filters.append(DocumentSource.source.ilike(f'%{keyword}%'))
        page_no = int(req_data.get('pageNo', req_data.get('page', 1)))
        page_size = int(req_data.get('pageSize', req_data.get('size', 20)))
        return KnowledgeDao.list_documents_with_chunk_count(session, filters, page_no, page_size)

    @staticmethod
    def parse_document_to_chunks(session, document_id, max_chars=1600):
        document = DocumentSourceDao.get_by_id(session, document_id)
        if not document:
            return {}, '文档不存在'
        content = document.content or ''
        if not content.strip():
            content = DocumentSourceService.extract_document_content(document)
            if not content.strip():
                return {}, '文档内容为空或解析失败'
            DocumentSourceDao.update_by_id(session, document.id, {
                'content': content,
                'status': DocumentSourceService.DOCUMENT_STATUS_PARSED
            })
        chunks = KnowledgeService._split_content(content, max_chars=max_chars)
        if not chunks:
            return {}, '未生成有效分片'
        KnowledgeDao.soft_delete_chunks_by_document(session, document.id)
        model_setting = KnowledgeService.get_model_setting(session, {'projectId': document.project_id})
        for index, chunk in enumerate(chunks, 1):
            chunk_content = chunk.get('content') or ''
            embedding, embedding_model = AIService.get_embedding(chunk_content, model_setting)
            item = KnowledgeChunk(
                document_id=document.id,
                product_id=document.product_id,
                project_id=document.project_id,
                chunk_no=index,
                title=chunk.get('title') or f'分片{index}',
                content=chunk_content,
                keywords=KnowledgeService._extract_keywords(chunk_content),
                embedding=embedding,
                embedding_model=embedding_model or model_setting.get('embeddingModel') or model_setting.get('embedding_model') or 'text-embedding-3-small',
                token_count=max(1, len(chunk_content) // 2),
                status=1,
                is_delete=0
            )
            KnowledgeDao.create(session, item)
        session.flush()
        return {'documentId': document.id, 'chunkCount': len(chunks), 'contentLength': len(content)}, ''

    @staticmethod
    def search(session, req_data):
        query = (req_data.get('query') or '').strip()
        if not query:
            return [], 'query 为必传参数'
        top_k = int(req_data.get('topK') or req_data.get('top_k') or KnowledgeService.DEFAULT_TOP_K)
        product_id = req_data.get('productId') or req_data.get('product_id')
        project_id = req_data.get('projectId') or req_data.get('project_id')
        document_ids = req_data.get('documentIds') or req_data.get('document_ids') or []
        if isinstance(document_ids, str):
            document_ids = [i for i in re.split(r'[,，]', document_ids) if i]
        if not product_id or not project_id:
            return [], 'productId、projectId 为必传参数'
        setting = KnowledgeService.get_model_setting(session, req_data)
        hits = KnowledgeService._hybrid_retrieve(session, query, product_id, project_id, document_ids, top_k, setting)
        return hits, ''

    @staticmethod
    def chat(session, req_data):
        query = (req_data.get('query') or '').strip()
        if not query:
            return {}, 'query 为必传参数'
        mode = req_data.get('mode') or 'hybrid'
        product_id = req_data.get('productId') or req_data.get('product_id')
        project_id = req_data.get('projectId') or req_data.get('project_id')
        if not product_id or not project_id:
            return {}, 'productId、projectId 为必传参数'
        user_id = req_data.get('createdBy') or req_data.get('created_by') or req_data.get('userId') or req_data.get('user_id')
        setting = KnowledgeService.get_model_setting(session, req_data)
        top_k = int(req_data.get('topK') or req_data.get('top_k') or setting.get('topK') or setting.get('top_k') or KnowledgeService.DEFAULT_TOP_K)
        evidence = []
        answer = ''
        if mode in ('local', 'hybrid'):
            evidence, err_msg = KnowledgeService.search(session, dict(req_data, topK=top_k))
            if err_msg:
                return {}, err_msg
        if mode == 'local':
            answer = KnowledgeService._local_answer(query, evidence)
        else:
            answer, err_msg = AIService.chat_with_context(query, evidence, setting)
            if err_msg:
                return {}, err_msg
        session_id = req_data.get('sessionId') or req_data.get('session_id')
        if not session_id:
            chat_session = KnowledgeChatSession(
                product_id=int(product_id),
                project_id=int(project_id),
                title=query[:80],
                created_by=user_id,
                is_delete=0
            )
            session_id = KnowledgeDao.create(session, chat_session)
        KnowledgeDao.create(session, KnowledgeChatMessage(
            session_id=int(session_id), role='user', content=query, mode=mode,
            evidence=[], model_config=KnowledgeService._safe_setting_snapshot(setting), is_delete=0
        ))
        KnowledgeDao.create(session, KnowledgeChatMessage(
            session_id=int(session_id), role='assistant', content=answer, mode=mode,
            evidence=evidence, model_config=KnowledgeService._safe_setting_snapshot(setting), is_delete=0
        ))
        session.flush()
        return {'sessionId': int(session_id), 'answer': answer, 'evidence': evidence, 'mode': mode, 'model': setting.get('model')}, ''

    @staticmethod
    def get_model_setting(session, req_data):
        scope_type = req_data.get('scopeType') or req_data.get('scope_type') or 'project'
        scope_id = req_data.get('scopeId') or req_data.get('scope_id') or req_data.get('projectId') or req_data.get('project_id') or 0
        item = KnowledgeDao.get_setting(session, scope_type, scope_id)
        if not item and scope_type != 'global':
            item = KnowledgeDao.get_setting(session, 'global', 0)
        if item:
            return KnowledgeService._setting_to_dict(item)
        return {
            'scopeType': scope_type,
            'scopeId': int(scope_id or 0),
            'provider': 'custom',
            'apiBase': '',
            'model': '',
            'embeddingModel': 'text-embedding-3-small',
            'temperature': 0.3,
            'maxTokens': 2048,
            'topK': KnowledgeService.DEFAULT_TOP_K,
            'scoreThreshold': 0,
            'useEnvKey': 1
        }

    @staticmethod
    def save_model_setting(session, req_data):
        scope_type = req_data.get('scopeType') or req_data.get('scope_type') or 'project'
        scope_id = req_data.get('scopeId') or req_data.get('scope_id') or req_data.get('projectId') or req_data.get('project_id') or 0
        data = {
            'provider': req_data.get('provider') or 'custom',
            'api_base': req_data.get('apiBase') or req_data.get('api_base'),
            'model': req_data.get('model'),
            'embedding_model': req_data.get('embeddingModel') or req_data.get('embedding_model') or 'text-embedding-3-small',
            'temperature': req_data.get('temperature', 0.3),
            'max_tokens': req_data.get('maxTokens') or req_data.get('max_tokens') or 2048,
            'top_k': req_data.get('topK') or req_data.get('top_k') or KnowledgeService.DEFAULT_TOP_K,
            'score_threshold': req_data.get('scoreThreshold') or req_data.get('score_threshold') or 0,
            'use_env_key': req_data.get('useEnvKey') if req_data.get('useEnvKey') is not None else req_data.get('use_env_key', 1),
            'status': req_data.get('status', 1),
            'created_by': req_data.get('createdBy') or req_data.get('created_by')
        }
        setting_id = KnowledgeDao.upsert_setting(session, scope_type, scope_id, data)
        session.flush()
        return setting_id, ''

    @staticmethod
    def list_sessions(session, req_data):
        return KnowledgeDao.list_sessions(
            session,
            req_data.get('productId') or req_data.get('product_id'),
            req_data.get('projectId') or req_data.get('project_id'),
            int(req_data.get('pageNo', 1)),
            int(req_data.get('pageSize', 20))
        )

    @staticmethod
    def list_messages(session, req_data):
        session_id = req_data.get('sessionId') or req_data.get('session_id')
        if not session_id:
            return [], 'sessionId 为必传参数'
        return KnowledgeDao.list_messages(session, session_id), ''

    @staticmethod
    def delete_session(session, req_data):
        session_id = req_data.get('sessionId') or req_data.get('session_id')
        if not session_id:
            return 0, 'sessionId 为必传参数'
        return KnowledgeDao.delete_session(session, session_id), ''

    @staticmethod
    def soft_delete_document_chunks(session, document_id):
        return KnowledgeDao.soft_delete_chunks_by_document(session, document_id)

    @staticmethod
    def _split_content(content, max_chars=1600):
        sections = AIService._split_document_content(content, max_chars=max_chars)
        return sections or [{'title': '文档内容', 'content': content[:max_chars]}]

    @staticmethod
    def _extract_keywords(content):
        words = [w for w in re.split(r'[^0-9A-Za-z\u4e00-\u9fa5]+', content or '') if len(w) >= 2]
        result = []
        for word in words:
            if word not in result:
                result.append(word[:32])
            if len(result) >= 20:
                break
        return result

    @staticmethod
    def _query_terms(query):
        text = (query or '').strip()
        terms = [t for t in re.split(r'\s+|[,，。？！?；;、]', text) if t]
        cn_terms = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        for term in cn_terms:
            if term not in terms:
                terms.append(term)
            for size in (2, 3, 4):
                for index in range(0, max(0, len(term) - size + 1)):
                    token = term[index:index + size]
                    if token not in terms:
                        terms.append(token)
        if text and text not in terms:
            terms.insert(0, text)
        return terms[:30]

    @staticmethod
    def _hybrid_retrieve(session, query, product_id, project_id, document_ids, top_k, setting):
        keywords = KnowledgeService._query_terms(query)
        keyword_chunks = KnowledgeDao.query_chunks_by_keywords(
            session, product_id, project_id, document_ids, keywords[:12], limit=max(300, top_k * 40)
        )
        scope_chunks = KnowledgeDao.list_scope_chunks(
            session, product_id, project_id, document_ids, limit=max(1000, top_k * 120)
        )
        query_embedding_cache = {}
        score_map = {}
        for chunk in keyword_chunks:
            keyword_score = KnowledgeService._score_chunk(chunk, query, keywords)
            if keyword_score > 0:
                score_map.setdefault(chunk.id, {'chunk': chunk, 'keyword': 0.0, 'vector': 0.0})['keyword'] = keyword_score
        for chunk in scope_chunks:
            query_embedding = KnowledgeService._query_embedding_for_chunk(query, chunk, setting, query_embedding_cache)
            vector_score = KnowledgeService._vector_similarity(query_embedding, chunk.embedding)
            if vector_score > 0:
                score_map.setdefault(chunk.id, {'chunk': chunk, 'keyword': 0.0, 'vector': 0.0})['vector'] = vector_score
        if not score_map:
            return []
        max_keyword = max([item['keyword'] for item in score_map.values()] or [1.0]) or 1.0
        ranked = []
        for item in score_map.values():
            keyword_norm = item['keyword'] / max_keyword if item['keyword'] else 0.0
            vector_norm = max(0.0, min(1.0, (item['vector'] + 1.0) / 2.0)) if item['vector'] else 0.0
            final_score = round(keyword_norm * 0.45 + vector_norm * 0.55, 6)
            if final_score <= 0:
                continue
            ranked.append((final_score, item['chunk'], keyword_norm, vector_norm))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [KnowledgeService._hit_to_dict(chunk, score, query, keyword_score=keyword_norm, vector_score=vector_norm) for score, chunk, keyword_norm, vector_norm in ranked[:top_k]]

    @staticmethod
    def _query_embedding_for_chunk(query, chunk, setting, cache):
        embedding_model = chunk.embedding_model or setting.get('embeddingModel') or setting.get('embedding_model') or 'text-embedding-3-small'
        if embedding_model.startswith('local-hash'):
            cache_key = 'local-hash'
            if cache_key not in cache:
                cache[cache_key] = AIService._hash_embedding(query)
            return cache[cache_key]
        cache_key = embedding_model
        if cache_key not in cache:
            scoped_setting = dict(setting or {})
            scoped_setting['embeddingModel'] = embedding_model
            cache[cache_key] = AIService.get_embedding(query, scoped_setting)[0]
        return cache[cache_key]

    @staticmethod
    def _vector_similarity(left, right):
        if not left or not right:
            return 0.0
        try:
            if isinstance(right, str):
                import json
                right = json.loads(right)
            size = min(len(left), len(right))
            if size <= 0:
                return 0.0
            dot = sum(float(left[i]) * float(right[i]) for i in range(size))
            left_norm = math.sqrt(sum(float(item) * float(item) for item in left[:size]))
            right_norm = math.sqrt(sum(float(item) * float(item) for item in right[:size]))
            if left_norm <= 0 or right_norm <= 0:
                return 0.0
            return round(dot / (left_norm * right_norm), 6)
        except Exception:
            return 0.0

    @staticmethod
    def _score_chunk(chunk, query, keywords):
        title = (chunk.title or '').lower()
        content = (chunk.content or '').lower()
        q = query.lower()
        score = 0.0
        if q and q in title:
            score += 50
        if q and q in content:
            score += 20 + min(content.count(q), 5) * 5
        for keyword in keywords:
            k = keyword.lower()
            if not k:
                continue
            if k in title:
                score += 12
            if k in content:
                score += 4 + min(content.count(k), 5)
        return round(score, 4)

    @staticmethod
    def _hit_to_dict(chunk, score, query, keyword_score=0, vector_score=0):
        return {
            'chunkId': chunk.id,
            'documentId': chunk.document_id,
            'chunkNo': chunk.chunk_no,
            'title': chunk.title,
            'source': KnowledgeService._document_source(chunk),
            'snippet': KnowledgeService._snippet(chunk.content, query, size=900),
            'score': score,
            'keywordScore': round(keyword_score, 6),
            'vectorScore': round(vector_score, 6)
        }

    @staticmethod
    def _document_source(chunk):
        return f'文档#{chunk.document_id}'

    @staticmethod
    def _snippet(content, query, size=220):
        text = re.sub(r'\s+', ' ', content or '').strip()
        if len(text) <= size:
            return text
        pos = text.lower().find((query or '').lower()) if query else -1
        if pos < 0:
            return text[:size] + '...'
        start = max(0, pos - size // 3)
        return ('...' if start > 0 else '') + text[start:start + size] + ('...' if start + size < len(text) else '')

    @staticmethod
    def _local_answer(query, evidence):
        if not evidence:
            return '当前知识库未找到充分依据，请补充需求文档或调整关键词后重试。'
        lines = [f'本地检索已找到 {len(evidence)} 条相关证据：']
        for index, item in enumerate(evidence, 1):
            lines.append(f'[{index}] {item.get("title") or "文档片段"}：{item.get("snippet") or ""}')
        return '\n'.join(lines)

    @staticmethod
    def _setting_to_dict(item):
        return {
            'id': item.id,
            'scopeType': item.scope_type,
            'scopeId': item.scope_id,
            'provider': item.provider,
            'apiBase': item.api_base,
            'model': item.model,
            'embeddingModel': item.embedding_model or 'text-embedding-3-small',
            'temperature': float(item.temperature) if item.temperature is not None else 0.3,
            'maxTokens': item.max_tokens,
            'topK': item.top_k,
            'scoreThreshold': float(item.score_threshold) if item.score_threshold is not None else 0,
            'useEnvKey': item.use_env_key,
            'status': item.status
        }

    @staticmethod
    def _safe_setting_snapshot(setting):
        return {k: v for k, v in (setting or {}).items() if k not in ('apiKey', 'api_key')}
