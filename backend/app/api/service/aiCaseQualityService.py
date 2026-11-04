# encoding: UTF-8
"""AI 用例质量：改写率 / 废稿率 / 近重复标记。"""
from __future__ import print_function

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import and_, func, or_, text

from app.api.model.caseModel import AiCaseOrigin, TestCase

logger = logging.getLogger(__name__)

CONTENT_FIELDS = (
    ('title', 'origin_title', 'title'),
    ('preconditions', 'origin_preconditions', 'preconditions'),
    ('steps', 'origin_steps', 'steps'),
    ('expected_results', 'origin_expected_results', 'expected_results'),
)


class AiCaseQualityService(object):

    @staticmethod
    def _orm_session(session):
        """取出底层 SQLAlchemy Session（兼容 common.sqlSession.SqlSession）。"""
        return getattr(session, '_session', session)

    @staticmethod
    def ensure_table(session):
        orm = AiCaseQualityService._orm_session(session)
        orm.execute(text('''
            CREATE TABLE IF NOT EXISTS ai_case_origin (
                id BIGSERIAL PRIMARY KEY,
                case_id BIGINT NOT NULL UNIQUE,
                project_id BIGINT NOT NULL,
                plan_id BIGINT,
                candidate_id VARCHAR(64),
                generation_id VARCHAR(64),
                origin_title VARCHAR(255),
                origin_preconditions TEXT,
                origin_steps TEXT,
                origin_expected_results TEXT,
                status VARCHAR(16) DEFAULT 'intact',
                rewrite_fields VARCHAR(64)[] DEFAULT '{}'::varchar[],
                rewritten_at TIMESTAMP,
                rewritten_by BIGINT,
                abandoned_at TIMESTAMP,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        orm.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_ai_case_origin_project_status
            ON ai_case_origin(project_id, status)
        '''))
        try:
            orm.commit()
        except Exception:
            pass

    @staticmethod
    def normalize_text(value):
        return re.sub(r'\s+', '', str(value or '').strip()).lower()

    @staticmethod
    def record_origin(session, case_obj, meta=None, commit=False):
        """AI 用例入库后写入原貌。已存在则跳过。"""
        if not case_obj or not getattr(case_obj, 'id', None):
            return None
        if int(getattr(case_obj, 'is_ai_generated', 0) or 0) != 1:
            return None
        AiCaseQualityService.ensure_table(session)
        existing = session.query(AiCaseOrigin).filter(AiCaseOrigin.case_id == int(case_obj.id)).first()
        if existing:
            return existing
        meta = meta or {}
        row = AiCaseOrigin(
            case_id=int(case_obj.id),
            project_id=int(case_obj.project_id),
            plan_id=meta.get('plan_id') or meta.get('planId'),
            candidate_id=str(meta.get('candidate_id') or meta.get('candidateId') or '') or None,
            generation_id=str(meta.get('generation_id') or meta.get('generationId') or '') or None,
            origin_title=case_obj.title or '',
            origin_preconditions=case_obj.preconditions or '',
            origin_steps=case_obj.steps or '',
            origin_expected_results=case_obj.expected_results or '',
            status='intact',
            rewrite_fields=[],
            imported_at=datetime.now(),
        )
        session.add(row)
        session.flush()
        if commit:
            session.commit()
        return row

    @staticmethod
    def evaluate_rewrite(session, case_id, user_id=None, commit=False):
        """对比当前用例与 origin，更新改写状态。"""
        if not case_id:
            return None
        AiCaseQualityService.ensure_table(session)
        origin = session.query(AiCaseOrigin).filter(AiCaseOrigin.case_id == int(case_id)).first()
        if not origin:
            return None
        case_obj = session.query(TestCase).filter(TestCase.id == int(case_id)).first()
        if not case_obj:
            return origin

        if int(getattr(case_obj, 'is_delete', 0) or 0) == 1 or int(getattr(case_obj, 'status', 1) or 0) == 2:
            return AiCaseQualityService.mark_abandoned(session, case_id, commit=commit)

        changed = []
        for field_key, origin_attr, case_attr in CONTENT_FIELDS:
            cur = AiCaseQualityService.normalize_text(getattr(case_obj, case_attr, ''))
            old = AiCaseQualityService.normalize_text(getattr(origin, origin_attr, ''))
            if cur != old:
                changed.append(field_key)

        if changed:
            origin.status = 'rewritten'
            origin.rewrite_fields = changed
            if not origin.rewritten_at:
                origin.rewritten_at = datetime.now()
            if user_id not in (None, ''):
                try:
                    origin.rewritten_by = int(user_id)
                except (TypeError, ValueError):
                    pass
        else:
            # 改回与原貌一致：恢复 intact（仍保留 rewritten_at 作审计可选；一期简化为 intact）
            if origin.status != 'abandoned':
                origin.status = 'intact'
                origin.rewrite_fields = []
        session.flush()
        if commit:
            session.commit()
        return origin

    @staticmethod
    def mark_abandoned(session, case_ids, commit=False):
        AiCaseQualityService.ensure_table(session)
        if not isinstance(case_ids, (list, tuple, set)):
            case_ids = [case_ids]
        ids = []
        for cid in case_ids:
            try:
                ids.append(int(cid))
            except (TypeError, ValueError):
                continue
        if not ids:
            return 0
        rows = session.query(AiCaseOrigin).filter(AiCaseOrigin.case_id.in_(ids)).all()
        now = datetime.now()
        for row in rows:
            row.status = 'abandoned'
            if not row.abandoned_at:
                row.abandoned_at = now
        session.flush()
        if commit:
            session.commit()
        return len(rows)

    @staticmethod
    def _parse_range(from_time, to_time):
        def _parse(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            s = str(v).strip().replace('T', ' ')
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    return datetime.strptime(s[:19] if len(s) > 10 and fmt.endswith('%S') else s[:10], fmt)
                except ValueError:
                    continue
            return None
        return _parse(from_time), _parse(to_time)

    @staticmethod
    def summary(session, project_id, from_time=None, to_time=None):
        if not project_id:
            return None, 'projectId 为必传参数'
        AiCaseQualityService.ensure_table(session)
        project_id = int(project_id)
        start, end = AiCaseQualityService._parse_range(from_time, to_time)

        origin_q = session.query(AiCaseOrigin).filter(AiCaseOrigin.project_id == project_id)
        if start:
            origin_q = origin_q.filter(AiCaseOrigin.imported_at >= start)
        if end:
            origin_q = origin_q.filter(AiCaseOrigin.imported_at <= end)
        origins = origin_q.all()

        tracked = len(origins)
        rewritten = sum(1 for o in origins if o.status == 'rewritten')
        abandoned = sum(1 for o in origins if o.status == 'abandoned')
        intact = sum(1 for o in origins if o.status == 'intact')

        # 存量 AI（无 origin）仅作说明，不进改写率分母
        legacy_q = session.query(func.count(TestCase.id)).filter(
            TestCase.project_id == project_id,
            TestCase.is_ai_generated == 1,
            TestCase.is_delete == 0,
            ~TestCase.id.in_(session.query(AiCaseOrigin.case_id).filter(AiCaseOrigin.project_id == project_id))
        )
        legacy_ai_count = int(legacy_q.scalar() or 0)

        denom = tracked if tracked > 0 else 0
        rewrite_rate = round(float(rewritten) / denom, 4) if denom else None
        abandon_rate = round(float(abandoned) / denom, 4) if denom else None
        pass_through_rate = round(float(intact) / denom, 4) if denom else None

        field_counter = Counter()
        day_bucket = defaultdict(lambda: {'imported': 0, 'rewritten': 0, 'abandoned': 0})
        for o in origins:
            for f in (o.rewrite_fields or []):
                field_counter[f] += 1
            day = (o.imported_at or o.created_time or datetime.now()).strftime('%Y-%m-%d')
            day_bucket[day]['imported'] += 1
            if o.status == 'rewritten':
                day_bucket[day]['rewritten'] += 1
            if o.status == 'abandoned':
                day_bucket[day]['abandoned'] += 1

        trend = [{'date': d, **day_bucket[d]} for d in sorted(day_bucket.keys())]
        field_dist = [{'field': k, 'count': v} for k, v in field_counter.most_common()]

        return {
            'projectId': project_id,
            'trackedCount': tracked,
            'rewrittenCount': rewritten,
            'abandonedCount': abandoned,
            'intactCount': intact,
            'rewriteRate': rewrite_rate,
            'abandonRate': abandon_rate,
            'passThroughRate': pass_through_rate,
            'legacyAiCount': legacy_ai_count,
            'legacyNote': '改写率仅统计本版本起有入库原貌的 AI 用例；存量 AI 不计入分母' if legacy_ai_count else '',
            'fieldDistribution': field_dist,
            'trend': trend,
            'from': start.isoformat(sep=' ') if start else None,
            'to': end.isoformat(sep=' ') if end else None,
        }, ''

    @staticmethod
    def rewritten_list(session, project_id, page_no=1, page_size=20, status='rewritten'):
        if not project_id:
            return None, 'projectId 为必传参数'
        AiCaseQualityService.ensure_table(session)
        project_id = int(project_id)
        page_no = max(int(page_no or 1), 1)
        page_size = min(max(int(page_size or 20), 1), 100)
        q = session.query(AiCaseOrigin, TestCase).outerjoin(
            TestCase, TestCase.id == AiCaseOrigin.case_id
        ).filter(AiCaseOrigin.project_id == project_id)
        if status:
            q = q.filter(AiCaseOrigin.status == status)
        total = q.count()
        rows = q.order_by(AiCaseOrigin.rewritten_at.desc().nullslast(), AiCaseOrigin.id.desc())\
            .offset((page_no - 1) * page_size).limit(page_size).all()
        items = []
        for origin, case_obj in rows:
            items.append({
                'caseId': origin.case_id,
                'caseKey': getattr(case_obj, 'case_key', None) if case_obj else None,
                'title': getattr(case_obj, 'title', None) or origin.origin_title,
                'status': origin.status,
                'rewriteFields': origin.rewrite_fields or [],
                'rewrittenAt': origin.rewritten_at.strftime('%Y-%m-%d %H:%M:%S') if origin.rewritten_at else None,
                'rewrittenBy': origin.rewritten_by,
                'importedAt': origin.imported_at.strftime('%Y-%m-%d %H:%M:%S') if origin.imported_at else None,
                'planId': origin.plan_id,
                'candidateId': origin.candidate_id,
            })
        return {'list': items, 'total': total, 'pageNo': page_no, 'pageSize': page_size}, ''

    # ── 近重复（第三波：轻量字符 bigram Jaccard）────────────────

    @staticmethod
    def _bigrams(text):
        s = AiCaseQualityService.normalize_text(text)
        if len(s) < 2:
            return set([s]) if s else set()
        return set(s[i:i + 2] for i in range(len(s) - 1))

    @staticmethod
    def _jaccard(a, b):
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return float(inter) / union if union else 0.0

    @staticmethod
    def annotate_near_duplicates(session, project_id, candidates, threshold=0.72):
        """给候选用例标注 nearDup / nearDupMatches，不自动丢弃。"""
        if not project_id or not isinstance(candidates, list):
            return candidates or []
        existing = session.query(TestCase).filter(
            TestCase.project_id == int(project_id),
            TestCase.is_delete == 0,
        ).order_by(TestCase.id.desc()).limit(800).all()
        existing_feats = []
        for c in existing:
            blob = '{}{}{}'.format(c.title or '', c.steps or '', c.expected_results or '')
            existing_feats.append({
                'caseId': c.id,
                'caseKey': c.case_key,
                'title': c.title,
                'grams': AiCaseQualityService._bigrams(blob),
            })

        annotated = []
        for item in candidates:
            row = dict(item or {})
            blob = '{}{}{}'.format(
                row.get('title') or '',
                row.get('steps') or '',
                row.get('expected_result') or row.get('expectedResults') or '',
            )
            grams = AiCaseQualityService._bigrams(blob)
            matches = []
            for feat in existing_feats:
                score = AiCaseQualityService._jaccard(grams, feat['grams'])
                if score >= threshold:
                    matches.append({
                        'caseId': feat['caseId'],
                        'caseKey': feat['caseKey'],
                        'title': feat['title'],
                        'score': round(score, 3),
                    })
            matches.sort(key=lambda x: x['score'], reverse=True)
            row['nearDup'] = bool(matches)
            row['nearDupMatches'] = matches[:5]
            annotated.append(row)
        return annotated
