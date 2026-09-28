# encoding: UTF-8
import json
from datetime import datetime

from logger import logger
from ..dao.chatIssueDao import ChatIssueDao
from ..model.bugModel import Bug
from ..model.caseModel import TestCase
from ..model.chatIssueModel import ChatIssueImport, ChatIssueItem
from ..service.bugService import BugService
from ..service.caseService import CaseService
from ..service.chatIssueParser import parse_chat_issue_markdown


class ChatIssueService(object):

    @staticmethod
    def import_text(session, req_data, user_id=None):
        text = ChatIssueService._get(req_data, 'text', 'rawText', 'content') or ''
        project_id = ChatIssueService._get(req_data, 'projectId', 'project_id')
        if not str(text).strip():
            return {}, '导入文本不能为空'
        if project_id in (None, ''):
            return {}, 'projectId 为必传参数'
        source_type = (ChatIssueService._get(req_data, 'sourceType', 'source_type') or 'paste').strip()
        split_by_day = ChatIssueService._get(req_data, 'splitByDay', 'split_by_day')
        if split_by_day is None:
            split_by_day = True
        else:
            split_by_day = split_by_day in (True, 1, '1', 'true', 'True')

        parsed = parse_chat_issue_markdown(text)
        if not parsed:
            return {}, '未能解析出问题条目，请使用「## 日期」+「**1. 标题**」格式'
        if not split_by_day and len(parsed) > 1:
            merged_items = []
            for block in parsed:
                for it in block['items']:
                    if block.get('dayLabel'):
                        it = dict(it)
                        it['detail'] = '【{}】\n{}'.format(block['dayLabel'], it.get('detail') or '').strip()
                    merged_items.append(it)
            parsed = [{
                'dayLabel': '',
                'title': (ChatIssueService._get(req_data, 'title') or '聊天问题批量导入')[:120],
                'items': merged_items,
                'rawText': text,
            }]

        product_id = ChatIssueService._to_int_or_none(
            ChatIssueService._get(req_data, 'productId', 'product_id')
        )
        product_name = ChatIssueService._get(req_data, 'productName', 'product_name') or ''
        project_name = ChatIssueService._get(req_data, 'projectName', 'project_name') or ''
        created = []
        for block in parsed:
            session_no = ChatIssueService._next_session_no(session)
            title = (ChatIssueService._get(req_data, 'title') if len(parsed) == 1 else None) or block['title']
            batch, err = ChatIssueDao.create(session, ChatIssueImport, {
                'session_no': session_no,
                'title': str(title)[:255],
                'source_type': source_type,
                'raw_text': block.get('rawText') or text,
                'product_id': product_id,
                'product_name': product_name,
                'project_id': int(project_id),
                'project_name': project_name,
                'status': 'ready',
                'day_label': block.get('dayLabel') or '',
                'created_by': user_id,
                'meta': {'format': 'doubao_daily', 'itemCount': len(block['items'])},
                'is_delete': 0,
            })
            if err:
                return {}, err
            item_rows = []
            for idx, it in enumerate(block['items'], start=1):
                detail = it.get('detail') or ''
                images = it.get('images') or []
                if images and '截图' not in detail:
                    detail = (detail + '\n\n相关截图：\n' + '\n'.join(images)).strip()
                obj, ierr = ChatIssueDao.create(session, ChatIssueItem, {
                    'import_id': batch.id,
                    'sort_no': idx,
                    'title': (it.get('title') or '未命名问题')[:500],
                    'detail': detail,
                    'suggest_type': it.get('suggestType') or 'bug',
                    'severity': 2,
                    'item_status': 'parsed',
                    'ai_analysis': {},
                    'source_ref': str(it.get('sourceRef') or idx)[:128],
                    'created_by': user_id,
                    'is_delete': 0,
                })
                if ierr:
                    return {}, ierr
                item_rows.append(obj)
            created.append(ChatIssueService._serialize_batch(batch, item_rows))
        return {'list': created, 'total': len(created)}, ''

    @staticmethod
    def list_imports(session, req_data):
        items, total = ChatIssueDao.list_imports(session, req_data)
        return {
            'list': [ChatIssueService._serialize_batch(i) for i in items],
            'total': total,
        }, ''

    @staticmethod
    def detail(session, import_id):
        batch = ChatIssueDao.get_by_id(session, ChatIssueImport, import_id)
        if not batch:
            return {}, '未查询到导入 Session'
        items = ChatIssueDao.list_items(session, import_id)
        return ChatIssueService._serialize_batch(batch, items), ''

    @staticmethod
    def update_item(session, req_data, user_id=None):
        item_id = ChatIssueService._get(req_data, 'itemId', 'item_id', 'id')
        if not item_id:
            return {}, 'itemId 为必传参数'
        item = ChatIssueDao.get_by_id(session, ChatIssueItem, item_id)
        if not item:
            return {}, '未查询到候选条目'
        update_info = {}
        for keys, col in [
            (('title',), 'title'),
            (('detail',), 'detail'),
            (('suggestType', 'suggest_type'), 'suggest_type'),
        ]:
            val = ChatIssueService._get(req_data, *keys)
            if val is not None:
                update_info[col] = val
        severity = ChatIssueService._get(req_data, 'severity')
        if severity is not None:
            update_info['severity'] = int(severity)
        ai_analysis = ChatIssueService._get(req_data, 'aiAnalysis', 'ai_analysis')
        if ai_analysis is not None and isinstance(ai_analysis, dict):
            update_info['ai_analysis'] = ai_analysis
            if item.item_status == 'parsed':
                update_info['item_status'] = 'analyzed'
        if not update_info:
            return ChatIssueService._serialize_item(item), ''
        _, err = ChatIssueDao.update_by_id(session, ChatIssueItem, item_id, update_info)
        if err:
            return {}, err
        item = ChatIssueDao.get_by_id(session, ChatIssueItem, item_id)
        return ChatIssueService._serialize_item(item), ''

    @staticmethod
    def delete_item(session, req_data, user_id=None):
        item_id = ChatIssueService._get(req_data, 'itemId', 'item_id', 'id')
        if not item_id:
            return {}, 'itemId 为必传参数'
        _, err = ChatIssueDao.update_by_id(session, ChatIssueItem, item_id, {'is_delete': 1})
        if err:
            return {}, err
        return {'id': int(item_id)}, ''

    @staticmethod
    def analyze(session, req_data, user_id=None):
        import_id = ChatIssueService._get(req_data, 'importId', 'import_id', 'sessionId', 'id')
        item_ids = ChatIssueService._get(req_data, 'itemIds', 'item_ids') or []
        if not import_id:
            return {}, 'importId 为必传参数'
        if isinstance(item_ids, str):
            item_ids = [x.strip() for x in item_ids.split(',') if x.strip()]
        batch = ChatIssueDao.get_by_id(session, ChatIssueImport, import_id)
        if not batch:
            return {}, '未查询到导入 Session'
        if item_ids:
            items = ChatIssueDao.get_items_by_ids(session, import_id, item_ids)
        else:
            items = [i for i in ChatIssueDao.list_items(session, import_id) if i.item_status in ('parsed', 'analyzed')]
        if not items:
            return {}, '没有可分析的候选条目'
        results = []
        errors = []
        for item in items:
            analysis, err = ChatIssueService._ai_analyze_item(item)
            if err or not analysis:
                errors.append({'itemId': item.id, 'message': err or 'AI 分析失败'})
                continue
            _, uerr = ChatIssueDao.update_by_id(session, ChatIssueItem, item.id, {
                'ai_analysis': analysis,
                'item_status': 'analyzed',
            })
            if uerr:
                errors.append({'itemId': item.id, 'message': uerr})
                continue
            refreshed = ChatIssueDao.get_by_id(session, ChatIssueItem, item.id)
            results.append(ChatIssueService._serialize_item(refreshed))
        return {'items': results, 'errors': errors}, ''

    @staticmethod
    def dismiss(session, req_data, user_id=None):
        import_id = ChatIssueService._get(req_data, 'importId', 'import_id', 'sessionId')
        item_ids = ChatIssueService._get(req_data, 'itemIds', 'item_ids') or []
        if not import_id or not item_ids:
            return {}, 'importId、itemIds 为必传参数'
        if isinstance(item_ids, str):
            item_ids = [x.strip() for x in item_ids.split(',') if x.strip()]
        items = ChatIssueDao.get_items_by_ids(session, import_id, item_ids)
        for item in items:
            ChatIssueDao.update_by_id(session, ChatIssueItem, item.id, {'item_status': 'dismissed'})
        return ChatIssueService.detail(session, import_id)

    @staticmethod
    def confirm_to_bug(session, req_data, user_id=None):
        import_id = ChatIssueService._get(req_data, 'importId', 'import_id', 'sessionId')
        item_ids = ChatIssueService._get(req_data, 'itemIds', 'item_ids') or []
        append_ai = ChatIssueService._get(req_data, 'appendAiAnalysis', 'append_ai_analysis')
        if append_ai is None:
            append_ai = True
        else:
            append_ai = append_ai in (True, 1, '1', 'true', 'True')
        if not import_id or not item_ids:
            return {}, 'importId、itemIds 为必传参数'
        if isinstance(item_ids, str):
            item_ids = [x.strip() for x in item_ids.split(',') if x.strip()]
        batch = ChatIssueDao.get_by_id(session, ChatIssueImport, import_id)
        if not batch:
            return {}, '未查询到导入 Session'
        if not batch.product_id:
            return {}, '导入 Session 缺少 productId，无法创建 Bug'
        items = ChatIssueDao.get_items_by_ids(session, import_id, item_ids)
        if not items:
            return {}, '未找到选中的候选条目'
        created = []
        for item in items:
            if item.linked_bug_id:
                created.append({'itemId': item.id, 'bugId': item.linked_bug_id, 'skipped': True})
                continue
            if item.item_status == 'dismissed':
                continue
            description = (item.detail or '').strip() or '来自聊天问题导入 {}'.format(batch.session_no)
            if append_ai:
                description = ChatIssueService._append_ai_to_description(description, item.ai_analysis or {})
            bug_key = BugService.generate_bug_key(session)
            bug_id, err = BugService.create(session, Bug, {
                'bug_key': bug_key,
                'title': item.title[:200],
                'description': description[:4000],
                'bug_type': 1,
                'severity': int(item.severity or 2),
                'priority': 2,
                'status': 0,
                'reporter_id': user_id,
                'product_id': batch.product_id,
                'project_id': batch.project_id,
                'environment': '',
                'steps': (item.detail or '')[:2000],
                'attachments': [],
                'is_delete': 0,
            })
            if err:
                return {}, '条目「{}」建 Bug 失败：{}'.format(item.title, err)
            ChatIssueDao.update_by_id(session, ChatIssueItem, item.id, {
                'linked_bug_id': bug_id,
                'item_status': 'confirmed',
            })
            created.append({'itemId': item.id, 'bugId': bug_id, 'bugKey': bug_key})
        ChatIssueService._refresh_batch_status(session, import_id)
        return {'created': created, 'detail': ChatIssueService.detail(session, import_id)[0]}, ''

    @staticmethod
    def to_case(session, req_data, user_id=None):
        import_id = ChatIssueService._get(req_data, 'importId', 'import_id', 'sessionId')
        item_ids = ChatIssueService._get(req_data, 'itemIds', 'item_ids') or []
        create = ChatIssueService._get(req_data, 'create') in (True, 1, '1', 'true', 'True')
        if not import_id or not item_ids:
            return {}, 'importId、itemIds 为必传参数'
        if isinstance(item_ids, str):
            item_ids = [x.strip() for x in item_ids.split(',') if x.strip()]
        batch = ChatIssueDao.get_by_id(session, ChatIssueImport, import_id)
        if not batch:
            return {}, '未查询到导入 Session'
        items = ChatIssueDao.get_items_by_ids(session, import_id, item_ids)
        if not items:
            return {}, '未找到选中的候选条目'
        results = []
        for item in items:
            steps = (item.detail or item.title or '').strip()
            draft = {
                'projectId': batch.project_id,
                'title': item.title[:120],
                'preconditions': '来源：聊天问题导入 {}{}'.format(
                    batch.session_no, (' / ' + batch.day_label) if batch.day_label else ''
                ),
                'steps': steps,
                'expectedResults': '问题已修复且回归通过',
                'priority': 2,
            }
            if not create:
                results.append({'itemId': item.id, 'draft': draft, 'created': False})
                continue
            case_key = CaseService.next_case_key(session, batch.project_id, None, batch.product_id)
            case_id, err = CaseService.create(session, TestCase, {
                'project_id': batch.project_id,
                'module_id': None,
                'case_key': case_key,
                'title': draft['title'],
                'preconditions': draft['preconditions'],
                'steps': draft['steps'],
                'expected_results': draft['expectedResults'],
                'priority': 2,
                'case_type': 1,
                'tags': ['聊天导入', batch.session_no],
                'status': 1,
                'is_auto': 0,
                'is_ai_generated': 1,
                'created_by': user_id,
                'is_delete': 0,
            })
            if err:
                return {}, '条目「{}」建用例失败：{}'.format(item.title, err)
            ChatIssueDao.update_by_id(session, ChatIssueItem, item.id, {'linked_case_id': case_id})
            results.append({'itemId': item.id, 'draft': draft, 'created': True, 'caseId': case_id, 'caseKey': case_key})
        return {'results': results}, ''

    @staticmethod
    def _ai_analyze_item(item):
        try:
            from ..service.aiService import AIService
            prompt = (
                '你是资深测试/研发助手。根据以下问题条目，输出 JSON（不要 markdown），字段：'
                'possibleCauses(字符串数组，可能原因，最多5条)、'
                'suggestions(字符串数组，改进建议，最多5条)、'
                'riskNote(字符串，风险提示可空)。\n'
                '标题：{}\n详情：{}\n请基于给定信息推断，勿编造未提及的系统名。'
            ).format(item.title or '', (item.detail or '')[:2500])
            text, err = AIService.chat_plain(prompt)
            if err or not text:
                return {}, err or 'AI 无返回'
            data = ChatIssueService._extract_json(text)
            if not data:
                return {
                    'possibleCauses': [str(text).strip()[:500]],
                    'suggestions': [],
                    'riskNote': 'AI 未返回结构化 JSON，已降级为原文',
                }, ''
            return {
                'possibleCauses': list(data.get('possibleCauses') or data.get('causes') or [])[:5],
                'suggestions': list(data.get('suggestions') or data.get('improvements') or [])[:5],
                'riskNote': str(data.get('riskNote') or data.get('risk') or '')[:500],
            }, ''
        except Exception as exc:
            logger.warning('chat issue ai analyze failed: %s', exc)
            return {}, str(exc)

    @staticmethod
    def _extract_json(text):
        text = (text or '').strip()
        if text.startswith('```'):
            text = text.strip('`')
            if text.startswith('json'):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return None
        return None

    @staticmethod
    def _append_ai_to_description(description, analysis):
        if not analysis:
            return description
        parts = [description, '', '—— AI 分析（仅供参考）——']
        causes = analysis.get('possibleCauses') or []
        suggestions = analysis.get('suggestions') or []
        if causes:
            parts.append('可能原因：')
            parts.extend(['- {}'.format(c) for c in causes])
        if suggestions:
            parts.append('改进建议：')
            parts.extend(['- {}'.format(s) for s in suggestions])
        if analysis.get('riskNote'):
            parts.append('风险提示：{}'.format(analysis.get('riskNote')))
        return '\n'.join(parts)

    @staticmethod
    def _refresh_batch_status(session, import_id):
        items = ChatIssueDao.list_items(session, import_id)
        if not items:
            status = 'draft'
        elif all(i.item_status in ('confirmed', 'dismissed') for i in items):
            status = 'done'
        elif any(i.item_status == 'confirmed' for i in items):
            status = 'partial'
        else:
            status = 'ready'
        ChatIssueDao.update_by_id(session, ChatIssueImport, import_id, {'status': status})

    @staticmethod
    def _next_session_no(session):
        prefix = 'CI{}'.format(datetime.now().strftime('%Y%m%d'))
        last = session.query(ChatIssueImport).filter(
            ChatIssueImport.session_no.like(prefix + '%')
        ).order_by(ChatIssueImport.id.desc()).first()
        seq = 1
        if last and last.session_no and last.session_no.startswith(prefix):
            try:
                seq = int(last.session_no[len(prefix):]) + 1
            except Exception:
                seq = 1
        return '{}{:04d}'.format(prefix, seq)

    @staticmethod
    def _serialize_batch(obj, items=None):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        result = {
            'id': data.get('id'),
            'sessionNo': data.get('session_no'),
            'title': data.get('title'),
            'sourceType': data.get('source_type'),
            'rawText': data.get('raw_text') or '',
            'productId': data.get('product_id'),
            'productName': data.get('product_name') or '',
            'projectId': data.get('project_id'),
            'projectName': data.get('project_name') or '',
            'status': data.get('status'),
            'dayLabel': data.get('day_label') or '',
            'createdBy': data.get('created_by'),
            'meta': data.get('meta') or {},
            'createdTime': ChatIssueService._fmt_time(data.get('created_time')),
            'updatedTime': ChatIssueService._fmt_time(data.get('updated_time')),
        }
        if items is not None:
            result['items'] = [ChatIssueService._serialize_item(i) for i in items]
            result['itemCount'] = len(items)
        return result

    @staticmethod
    def _serialize_item(obj):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        return {
            'id': data.get('id'),
            'importId': data.get('import_id'),
            'sortNo': data.get('sort_no'),
            'title': data.get('title'),
            'detail': data.get('detail') or '',
            'suggestType': data.get('suggest_type') or 'bug',
            'severity': data.get('severity'),
            'itemStatus': data.get('item_status'),
            'aiAnalysis': data.get('ai_analysis') or {},
            'linkedBugId': data.get('linked_bug_id'),
            'linkedCaseId': data.get('linked_case_id'),
            'sourceRef': data.get('source_ref') or '',
            'createdTime': ChatIssueService._fmt_time(data.get('created_time')),
        }

    @staticmethod
    def _fmt_time(value):
        if not value:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)

    @staticmethod
    def _to_int_or_none(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def _get(req_data, *keys, default=None):
        for key in keys:
            if req_data is None:
                break
            if key in req_data and req_data.get(key) is not None:
                return req_data.get(key)
        return default
