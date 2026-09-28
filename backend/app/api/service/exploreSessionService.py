# encoding: UTF-8
import os
import uuid
from datetime import datetime

from logger import logger
from ..dao.exploreSessionDao import ExploreSessionDao
from ..model.bugModel import Bug
from ..model.caseModel import TestCase
from ..model.exploreSessionModel import ExploreSession, ExploreSessionEntry
from ..service.bugService import BugService
from ..service.caseService import CaseService

ENTRY_TYPES = {'note', 'step', 'screenshot', 'finding', 'blocker'}
ACTIVE_WRITE_STATUSES = {'active'}
UPLOAD_FOLDER = 'attachment/explore_session'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class ExploreSessionService(object):

    @staticmethod
    def create_session(session, req_data, user_id=None):
        title = (ExploreSessionService._get(req_data, 'title') or '').strip()
        project_id = ExploreSessionService._get(req_data, 'projectId', 'project_id')
        if not title or project_id in (None, ''):
            return {}, 'title、projectId 为必传参数'
        status = (ExploreSessionService._get(req_data, 'status') or 'draft').strip().lower()
        if status not in ('draft', 'active'):
            status = 'draft'
        now = datetime.now()
        add_info = {
            'session_no': ExploreSessionService._next_session_no(session),
            'title': title,
            'charter': ExploreSessionService._get(req_data, 'charter') or '',
            'out_of_scope': ExploreSessionService._get(req_data, 'outOfScope', 'out_of_scope') or '',
            'product_id': ExploreSessionService._to_int_or_none(
                ExploreSessionService._get(req_data, 'productId', 'product_id')
            ),
            'product_name': ExploreSessionService._get(req_data, 'productName', 'product_name') or '',
            'project_id': int(project_id),
            'project_name': ExploreSessionService._get(req_data, 'projectName', 'project_name') or '',
            'plan_id': ExploreSessionService._to_int_or_none(
                ExploreSessionService._get(req_data, 'planId', 'plan_id')
            ),
            'environment': ExploreSessionService._get(req_data, 'environment') or '',
            'status': status,
            'summary': '',
            'started_at': now if status == 'active' else None,
            'created_by': user_id,
            'meta': ExploreSessionService._get(req_data, 'meta') or {},
            'is_delete': 0,
        }
        obj, err = ExploreSessionDao.create(session, ExploreSession, add_info)
        if err:
            return {}, err
        return ExploreSessionService._serialize_session(obj), ''

    @staticmethod
    def list_sessions(session, req_data):
        items, total = ExploreSessionDao.list_sessions(session, req_data)
        return {
            'list': [ExploreSessionService._serialize_session(item) for item in items],
            'total': total,
        }, ''

    @staticmethod
    def detail(session, session_id):
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        entries = ExploreSessionDao.list_entries(session, session_id)
        data = ExploreSessionService._serialize_session(obj)
        data['entries'] = [ExploreSessionService._serialize_entry(e) for e in entries]
        return data, ''

    @staticmethod
    def update_session(session, req_data, user_id=None):
        session_id = ExploreSessionService._get(req_data, 'sessionId', 'session_id', 'id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        update_info = {}
        mapping = [
            (('title',), 'title'),
            (('charter',), 'charter'),
            (('outOfScope', 'out_of_scope'), 'out_of_scope'),
            (('environment',), 'environment'),
            (('productName', 'product_name'), 'product_name'),
            (('projectName', 'project_name'), 'project_name'),
            (('summary',), 'summary'),
        ]
        for keys, column in mapping:
            value = ExploreSessionService._get(req_data, *keys)
            if value is not None:
                update_info[column] = value
        plan_id = ExploreSessionService._get(req_data, 'planId', 'plan_id')
        if plan_id is not None:
            update_info['plan_id'] = ExploreSessionService._to_int_or_none(plan_id)
        meta = ExploreSessionService._get(req_data, 'meta')
        if meta is not None:
            update_info['meta'] = meta
        if not update_info:
            return ExploreSessionService.detail(session, session_id)
        _, err = ExploreSessionDao.update_by_id(session, ExploreSession, session_id, update_info)
        if err:
            return {}, err
        return ExploreSessionService.detail(session, session_id)

    @staticmethod
    def start_session(session, session_id, user_id=None):
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ('draft', 'active'):
            return {}, '仅 draft 状态可开始'
        if obj.status == 'active':
            return ExploreSessionService.detail(session, session_id)
        _, err = ExploreSessionDao.update_by_id(session, ExploreSession, session_id, {
            'status': 'active',
            'started_at': datetime.now(),
        })
        if err:
            return {}, err
        return ExploreSessionService.detail(session, session_id)

    @staticmethod
    def end_session(session, req_data, user_id=None):
        session_id = ExploreSessionService._get(req_data, 'sessionId', 'session_id', 'id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status != 'active':
            return {}, '仅 active 状态可结束'
        summary = ExploreSessionService._get(req_data, 'summary')
        if summary is None or str(summary).strip() == '':
            summary = ExploreSessionService._build_template_summary(session, session_id, obj)
        use_ai = ExploreSessionService._get(req_data, 'useAiSummary', 'use_ai_summary')
        if use_ai in (True, 1, '1', 'true', 'True'):
            ai_summary = ExploreSessionService._try_ai_summary(session, session_id, obj)
            if ai_summary:
                summary = ai_summary
        _, err = ExploreSessionDao.update_by_id(session, ExploreSession, session_id, {
            'status': 'ended',
            'ended_at': datetime.now(),
            'summary': summary,
        })
        if err:
            return {}, err
        return ExploreSessionService.detail(session, session_id)

    @staticmethod
    def archive_session(session, session_id, user_id=None):
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ('ended', 'archived'):
            return {}, '仅 ended 状态可归档'
        _, err = ExploreSessionDao.update_by_id(session, ExploreSession, session_id, {
            'status': 'archived',
        })
        if err:
            return {}, err
        return ExploreSessionService.detail(session, session_id)

    @staticmethod
    def add_entry(session, req_data, user_id=None):
        session_id = ExploreSessionService._get(req_data, 'sessionId', 'session_id')
        entry_type = (ExploreSessionService._get(req_data, 'entryType', 'entry_type') or '').strip().lower()
        if not session_id:
            return {}, 'sessionId 为必传参数'
        if entry_type not in ENTRY_TYPES:
            return {}, 'entryType 仅支持 note/step/screenshot/finding/blocker'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ACTIVE_WRITE_STATUSES:
            return {}, '仅 active 状态可写入时间线'
        content = ExploreSessionService._get(req_data, 'content') or ''
        payload = ExploreSessionService._get(req_data, 'payload') or {}
        if not isinstance(payload, dict):
            payload = {}
        sort_no = ExploreSessionDao.next_sort_no(session, session_id)
        entry, err = ExploreSessionDao.create(session, ExploreSessionEntry, {
            'session_id': int(session_id),
            'entry_type': entry_type,
            'content': content,
            'payload': payload,
            'sort_no': sort_no,
            'created_by': user_id,
            'is_delete': 0,
        })
        if err:
            return {}, err
        return ExploreSessionService._serialize_entry(entry), ''

    @staticmethod
    def update_entry(session, req_data, user_id=None):
        entry_id = ExploreSessionService._get(req_data, 'entryId', 'entry_id', 'id')
        if not entry_id:
            return {}, 'entryId 为必传参数'
        entry = ExploreSessionDao.get_by_id(session, ExploreSessionEntry, entry_id)
        if not entry:
            return {}, '未查询到对应条目'
        sess = ExploreSessionDao.get_by_id(session, ExploreSession, entry.session_id)
        if not sess or sess.status not in ACTIVE_WRITE_STATUSES:
            return {}, '仅 active 状态可修改时间线'
        update_info = {}
        content = ExploreSessionService._get(req_data, 'content')
        if content is not None:
            update_info['content'] = content
        payload = ExploreSessionService._get(req_data, 'payload')
        if payload is not None and isinstance(payload, dict):
            update_info['payload'] = payload
        entry_type = ExploreSessionService._get(req_data, 'entryType', 'entry_type')
        if entry_type:
            entry_type = str(entry_type).strip().lower()
            if entry_type not in ENTRY_TYPES:
                return {}, 'entryType 非法'
            update_info['entry_type'] = entry_type
        if not update_info:
            return ExploreSessionService._serialize_entry(entry), ''
        _, err = ExploreSessionDao.update_by_id(session, ExploreSessionEntry, entry_id, update_info)
        if err:
            return {}, err
        entry = ExploreSessionDao.get_by_id(session, ExploreSessionEntry, entry_id)
        return ExploreSessionService._serialize_entry(entry), ''

    @staticmethod
    def delete_entry(session, req_data, user_id=None):
        entry_id = ExploreSessionService._get(req_data, 'entryId', 'entry_id', 'id')
        if not entry_id:
            return {}, 'entryId 为必传参数'
        entry = ExploreSessionDao.get_by_id(session, ExploreSessionEntry, entry_id)
        if not entry:
            return {}, '未查询到对应条目'
        sess = ExploreSessionDao.get_by_id(session, ExploreSession, entry.session_id)
        if not sess or sess.status not in ACTIVE_WRITE_STATUSES:
            return {}, '仅 active 状态可删除时间线'
        _, err = ExploreSessionDao.update_by_id(session, ExploreSessionEntry, entry_id, {'is_delete': 1})
        if err:
            return {}, err
        return {'id': int(entry_id)}, ''

    @staticmethod
    def upload_screenshot(session, flask_request, user_id=None):
        session_id = flask_request.form.get('sessionId') or flask_request.form.get('session_id')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ACTIVE_WRITE_STATUSES:
            return {}, '仅 active 状态可上传截图'
        if 'file' not in flask_request.files:
            return {}, '未找到上传文件'
        file = flask_request.files['file']
        if not file or not file.filename:
            return {}, '文件名不能为空'
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return {}, '不支持的文件格式，仅支持：{}'.format(', '.join(sorted(ALLOWED_EXTENSIONS)))
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_UPLOAD_BYTES:
            return {}, '图片超过 5MB 上限'
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = 'explore-{}-{}.{}'.format(timestamp, uuid.uuid4().hex[:8], ext)
        rel_path = '{}/{}'.format(UPLOAD_FOLDER.replace('\\', '/'), filename)
        abs_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(abs_path)
        content = flask_request.form.get('content') or '截图'
        sort_no = ExploreSessionDao.next_sort_no(session, session_id)
        entry, err = ExploreSessionDao.create(session, ExploreSessionEntry, {
            'session_id': int(session_id),
            'entry_type': 'screenshot',
            'content': content,
            'payload': {
                'path': rel_path,
                'url': '/{}'.format(rel_path),
                'fileName': filename,
                'originalName': file.filename,
            },
            'sort_no': sort_no,
            'created_by': user_id,
            'is_delete': 0,
        })
        if err:
            return {}, err
        return ExploreSessionService._serialize_entry(entry), ''

    @staticmethod
    def to_bug(session, req_data, user_id=None):
        session_id = ExploreSessionService._get(req_data, 'sessionId', 'session_id')
        title = (ExploreSessionService._get(req_data, 'title') or '').strip()
        entry_ids = ExploreSessionService._get(req_data, 'entryIds', 'entry_ids') or []
        if not session_id:
            return {}, 'sessionId 为必传参数'
        if not title:
            return {}, 'title 为必传参数'
        if isinstance(entry_ids, str):
            entry_ids = [x.strip() for x in entry_ids.split(',') if x.strip()]
        if not isinstance(entry_ids, list) or not entry_ids:
            return {}, 'entryIds 为必传参数'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ('active', 'ended'):
            return {}, '仅 active/ended 状态可转 Bug'
        entries = ExploreSessionDao.get_entries_by_ids(session, session_id, entry_ids)
        if not entries:
            return {}, '未找到选中的时间线条目'
        steps = ExploreSessionService._entries_to_steps_text(entries)
        attachments = []
        for entry in entries:
            if entry.entry_type != 'screenshot':
                continue
            payload = entry.payload or {}
            path = payload.get('path') or payload.get('url') or ''
            if path:
                attachments.append({
                    'name': payload.get('fileName') or payload.get('originalName') or 'screenshot',
                    'url': path if str(path).startswith('/') else '/{}'.format(path),
                    'path': path,
                })
        bug_key = BugService.generate_bug_key(session)
        add_info = {
            'bug_key': bug_key,
            'title': title,
            'description': ExploreSessionService._get(req_data, 'description') or (
                '来自探索 Session {}：{}'.format(obj.session_no, obj.title)
            ),
            'bug_type': int(ExploreSessionService._get(req_data, 'bugType', 'bug_type', default=1) or 1),
            'severity': int(ExploreSessionService._get(req_data, 'severity', default=2) or 2),
            'priority': int(ExploreSessionService._get(req_data, 'priority', default=2) or 2),
            'status': 0,
            'reporter_id': user_id,
            'assignee_id': ExploreSessionService._to_int_or_none(
                ExploreSessionService._get(req_data, 'assigneeId', 'assignee_id')
            ),
            'product_id': obj.product_id,
            'project_id': obj.project_id,
            'module_id': ExploreSessionService._to_int_or_none(
                ExploreSessionService._get(req_data, 'moduleId', 'module_id')
            ),
            'plan_id': obj.plan_id,
            'environment': obj.environment or '',
            'steps': steps,
            'attachments': attachments,
            'is_delete': 0,
        }
        if not add_info['product_id']:
            return {}, 'Session 缺少 productId，无法创建 Bug'
        bug_id, err = BugService.create(session, Bug, add_info)
        if err:
            return {}, err
        ExploreSessionDao.link_entries(session, [e.id for e in entries], bug_id=bug_id)
        return {'bugId': bug_id, 'bugKey': bug_key, 'entryIds': [e.id for e in entries]}, ''

    @staticmethod
    def to_case_draft(session, req_data, user_id=None):
        session_id = ExploreSessionService._get(req_data, 'sessionId', 'session_id')
        entry_ids = ExploreSessionService._get(req_data, 'entryIds', 'entry_ids') or []
        create = ExploreSessionService._get(req_data, 'create') in (True, 1, '1', 'true', 'True')
        if not session_id:
            return {}, 'sessionId 为必传参数'
        if isinstance(entry_ids, str):
            entry_ids = [x.strip() for x in entry_ids.split(',') if x.strip()]
        if not isinstance(entry_ids, list) or not entry_ids:
            return {}, 'entryIds 为必传参数'
        obj = ExploreSessionDao.get_by_id(session, ExploreSession, session_id)
        if not obj:
            return {}, '未查询到对应 Session'
        if obj.status not in ('active', 'ended'):
            return {}, '仅 active/ended 状态可转用例'
        entries = ExploreSessionDao.get_entries_by_ids(session, session_id, entry_ids)
        if not entries:
            return {}, '未找到选中的时间线条目'
        title = (ExploreSessionService._get(req_data, 'title') or '').strip() or (
            '探索用例-{}'.format(obj.title)[:120]
        )
        steps_from_req = ExploreSessionService._get(req_data, 'steps')
        if steps_from_req is not None and str(steps_from_req).strip() != '':
            steps = str(steps_from_req).strip()
        else:
            steps = ExploreSessionService._entries_to_steps_text(entries)
        preconditions = ExploreSessionService._get(req_data, 'preconditions') or (
            '探索 Session：{}（{}）'.format(obj.session_no, obj.environment or '未填环境')
        )
        expected = ExploreSessionService._get(req_data, 'expectedResults', 'expected_results') or '与探索发现一致，无异常阻断'
        draft = {
            'projectId': obj.project_id,
            'title': title,
            'preconditions': preconditions,
            'steps': steps,
            'expectedResults': expected,
            'priority': int(ExploreSessionService._get(req_data, 'priority', default=2) or 2),
            'caseType': 1,
            'tags': ['探索Session', obj.session_no],
            'isAiGenerated': 1,
            'sessionId': int(session_id),
            'entryIds': [e.id for e in entries],
        }
        if not create:
            return {'draft': draft, 'created': False}, ''
        module_id = ExploreSessionService._to_int_or_none(
            ExploreSessionService._get(req_data, 'moduleId', 'module_id')
        )
        case_key = CaseService.next_case_key(session, obj.project_id, module_id, obj.product_id)
        case_id, err = CaseService.create(session, TestCase, {
            'project_id': obj.project_id,
            'module_id': module_id,
            'case_key': case_key,
            'title': title,
            'preconditions': preconditions,
            'steps': steps,
            'expected_results': expected,
            'priority': draft['priority'],
            'case_type': 1,
            'tags': draft['tags'],
            'status': 1,
            'is_auto': 0,
            'is_ai_generated': 1,
            'created_by': user_id,
            'is_delete': 0,
        })
        if err:
            return {}, err
        ExploreSessionDao.link_entries(session, [e.id for e in entries], case_id=case_id)
        return {'draft': draft, 'created': True, 'caseId': case_id, 'caseKey': case_key}, ''

    @staticmethod
    def _next_session_no(session):
        prefix = 'ES{}'.format(datetime.now().strftime('%Y%m%d'))
        like = '{}%'.format(prefix)
        last = session.query(ExploreSession).filter(
            ExploreSession.session_no.like(like)
        ).order_by(ExploreSession.id.desc()).first()
        seq = 1
        if last and last.session_no and last.session_no.startswith(prefix):
            tail = last.session_no[len(prefix):]
            try:
                seq = int(tail) + 1
            except Exception:
                seq = 1
        return '{}{:04d}'.format(prefix, seq)

    @staticmethod
    def _build_template_summary(session, session_id, obj):
        entries = ExploreSessionDao.list_entries(session, session_id)
        counts = {}
        for entry in entries:
            counts[entry.entry_type] = counts.get(entry.entry_type, 0) + 1
        finding_lines = [
            '- {}'.format((e.content or '').strip()[:120])
            for e in entries if e.entry_type == 'finding' and (e.content or '').strip()
        ][:10]
        parts = [
            'Session {}「{}」已结束。'.format(obj.session_no, obj.title),
            '章程：{}'.format((obj.charter or '（未填）')[:200]),
            '条目统计：{}'.format(
                ', '.join('{}={}'.format(k, v) for k, v in sorted(counts.items())) or '无'
            ),
        ]
        if finding_lines:
            parts.append('主要发现：\n' + '\n'.join(finding_lines))
        return '\n'.join(parts)

    @staticmethod
    def _try_ai_summary(session, session_id, obj):
        try:
            from ..service.aiService import AIService
            entries = ExploreSessionDao.list_entries(session, session_id)
            lines = []
            for entry in entries[:40]:
                lines.append('[{}] {}'.format(entry.entry_type, (entry.content or '')[:200]))
            prompt = (
                '你是测试助手。请根据探索测试 Session 时间线写一段中文摘要（120-200字），'
                '包含范围、关键步骤与发现，不要编造未出现的事实。\n'
                '标题：{}\n章程：{}\n时间线：\n{}'
            ).format(obj.title, obj.charter or '', '\n'.join(lines) or '（空）')
            text, err = AIService.chat_plain(prompt)
            if err or not text:
                return ''
            return str(text).strip()[:2000]
        except Exception as exc:
            logger.warning('explore session AI summary failed: %s', exc)
            return ''

    @staticmethod
    def _entries_to_steps_text(entries):
        lines = []
        idx = 1
        for entry in entries:
            text = (entry.content or '').strip()
            if entry.entry_type == 'screenshot':
                payload = entry.payload or {}
                path = payload.get('path') or payload.get('url') or ''
                lines.append('{}. [截图] {} {}'.format(idx, text or '见附件', path).strip())
                idx += 1
            elif entry.entry_type in ('step', 'note', 'finding', 'blocker'):
                label = {
                    'step': '步骤',
                    'note': '备注',
                    'finding': '发现',
                    'blocker': '阻塞',
                }.get(entry.entry_type, entry.entry_type)
                if text:
                    lines.append('{}. [{}] {}'.format(idx, label, text))
                    idx += 1
        return '\n'.join(lines) if lines else ''

    @staticmethod
    def _serialize_session(obj):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        return {
            'id': data.get('id'),
            'sessionNo': data.get('session_no'),
            'title': data.get('title'),
            'charter': data.get('charter') or '',
            'outOfScope': data.get('out_of_scope') or '',
            'productId': data.get('product_id'),
            'productName': data.get('product_name') or '',
            'projectId': data.get('project_id'),
            'projectName': data.get('project_name') or '',
            'planId': data.get('plan_id'),
            'environment': data.get('environment') or '',
            'status': data.get('status'),
            'summary': data.get('summary') or '',
            'startedAt': ExploreSessionService._fmt_time(data.get('started_at')),
            'endedAt': ExploreSessionService._fmt_time(data.get('ended_at')),
            'createdBy': data.get('created_by'),
            'meta': data.get('meta') or {},
            'createdTime': ExploreSessionService._fmt_time(data.get('created_time')),
            'updatedTime': ExploreSessionService._fmt_time(data.get('updated_time')),
        }

    @staticmethod
    def _serialize_entry(obj):
        if not obj:
            return {}
        data = obj.to_dict() if hasattr(obj, 'to_dict') else {}
        return {
            'id': data.get('id'),
            'sessionId': data.get('session_id'),
            'entryType': data.get('entry_type'),
            'content': data.get('content') or '',
            'payload': data.get('payload') or {},
            'sortNo': data.get('sort_no'),
            'linkedBugId': data.get('linked_bug_id'),
            'linkedCaseId': data.get('linked_case_id'),
            'createdBy': data.get('created_by'),
            'createdTime': ExploreSessionService._fmt_time(data.get('created_time')),
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
