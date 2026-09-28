# encoding: UTF-8
"""变更影响雷达：挂靠 precise_analysis，聚合行级血缘 + 必测清单。"""
from __future__ import unicode_literals

import time

from common.sqlSession import SqlSession
from ..dao.preciseTestDao import PreciseTestDao
from ..model.contractModel import ContractSuite
from ..model.inspectionModel import InspectionGroup
from ..model.preciseTestModel import (
    PreciseAnalysis, PreciseChangedFile, PreciseLineageItem, PreciseRecommendation,
)
from .gitDiffService import GitDiffService
from .gitLineageService import GitLineageService
from .preciseTestService import PreciseTestService


class ImpactRadarService(object):

    @staticmethod
    def _session():
        return SqlSession()

    @staticmethod
    def parse_url(git_url):
        return GitLineageService.parse_git_url(git_url)

    @classmethod
    def trace_code(cls, payload):
        """输入仓库 + 文件路径 + 代码片段，返回匹配到的 commit id / 时间。"""
        payload = payload or {}
        repository_url = (payload.get('repository_url') or payload.get('repositoryUrl') or '').strip()
        branch_name = (payload.get('branch_name') or payload.get('branchName') or '').strip() or None
        file_path = (payload.get('file_path') or payload.get('filePath') or '').strip() or None
        code = payload.get('code') or payload.get('snippet') or payload.get('modified_row') or ''
        max_commits = int(payload.get('max_commits') or payload.get('maxCommits') or 20)
        if not repository_url:
            return {}, 'repository_url 必传'
        repo_path, err = GitDiffService.ensure_repo(repository_url, branch_name)
        if err:
            return {}, err
        histories, trace_err = GitLineageService.trace_code(
            repo_path, code, file_path=file_path, max_commits=max_commits
        )
        if trace_err:
            return {}, trace_err
        return {
            'repository_url': repository_url,
            'file_path': file_path or '',
            'code': (code or '').strip(),
            'total': len(histories),
            'commits': histories,
        }, ''

    @classmethod
    def run(cls, payload, user=None):
        """创建并执行一次雷达分析。"""
        payload = payload or {}
        options = payload.get('options') or {}
        enable_lineage = options.get('enable_lineage', True)
        enable_recommend = options.get('enable_recommend', True)
        max_pickaxe = int(options.get('max_pickaxe_per_file') or GitLineageService.MAX_PICKAXE_PER_FILE)

        product_id = payload.get('product_id') or payload.get('productId')
        project_id = payload.get('project_id') or payload.get('projectId')
        git_url = (payload.get('git_url') or payload.get('gitUrl') or '').strip()
        repository_url = (payload.get('repository_url') or payload.get('repositoryUrl') or '').strip()
        branch_name = (payload.get('branch_name') or payload.get('branchName') or '').strip() or None
        base_commit = (payload.get('base_commit') or payload.get('baseCommit') or '').strip()
        target_commit = (payload.get('target_commit') or payload.get('targetCommit') or '').strip()
        title = (payload.get('title') or '').strip()
        analysis_id = payload.get('analysis_id') or payload.get('analysisId') or payload.get('precise_analysis_id')

        source_type = 'manual_commit'
        source_ref = git_url or ''
        commit_id = target_commit

        if git_url:
            parsed, err = GitLineageService.parse_git_url(git_url)
            if err and not repository_url:
                return {}, err
            if parsed:
                source_type = parsed.get('source_type') or 'git_url'
                source_ref = parsed.get('source_ref') or git_url
                if not repository_url:
                    repository_url = parsed.get('repository_url') or ''
                if not commit_id:
                    commit_id = parsed.get('commit_id') or ''

        if not commit_id and target_commit:
            commit_id = target_commit
        if not repository_url:
            return {}, 'repository_url 或可解析的 git_url 必传'
        if not commit_id and not (base_commit and target_commit):
            return {}, 'commit_id / target_commit 必传（或提供含 commit 的 git_url）'

        session = cls._session()
        try:
            if analysis_id:
                analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
                if not analysis:
                    return {}, '未查询到对应精准分析'
                repository_url = repository_url or analysis.repository_url
                branch_name = branch_name or analysis.branch_name
                commit_id = commit_id or analysis.commit_id or analysis.target_commit
                base_commit = base_commit or analysis.base_commit
                target_commit = target_commit or analysis.target_commit or commit_id
                product_id = product_id or analysis.product_id
                project_id = project_id or analysis.project_id
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis.id, {
                    'source_type': source_type or analysis.source_type or 'radar',
                    'source_ref': source_ref or analysis.source_ref,
                    'commit_id': commit_id,
                    'repository_url': repository_url,
                    'status': 1,
                })
            else:
                if not product_id or not project_id:
                    return {}, 'product_id / project_id 必传'
                target_commit = target_commit or commit_id
                analysis_no = 'IR{}'.format(int(time.time() * 1000))
                created_by = None
                if user:
                    created_by = user.get('user_id') or user.get('id')
                analysis_id, create_err = PreciseTestDao.create(session, PreciseAnalysis, {
                    'analysis_no': analysis_no,
                    'product_id': int(product_id),
                    'project_id': int(project_id),
                    'repository_url': repository_url,
                    'branch_name': branch_name,
                    'base_commit': base_commit or None,
                    'target_commit': target_commit,
                    'title': title or '变更影响雷达 {}'.format((commit_id or '')[:8]),
                    'description': source_ref or '',
                    'status': 1,
                    'source_type': source_type or 'radar',
                    'source_ref': source_ref,
                    'commit_id': commit_id,
                    'must_test_assets': {},
                    'created_by': created_by,
                    'is_delete': 0,
                })
                if create_err:
                    return {}, create_err
                analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)

            repo_path, err = GitDiffService.ensure_repo(repository_url, branch_name)
            if err:
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 7})
                return {}, err

            if not base_commit and commit_id:
                parent, parent_err = GitLineageService.parent_commit(repo_path, commit_id)
                if not parent_err and parent:
                    base_commit = parent
                    PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                        'base_commit': base_commit,
                        'target_commit': commit_id,
                    })

            if base_commit and (target_commit or commit_id):
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                    'base_commit': base_commit,
                    'target_commit': target_commit or commit_id,
                })
                diff, diff_err = PreciseTestService.parse_diff(session, analysis_id)
                if diff_err:
                    show_text, _ = GitLineageService.git_show(repo_path, commit_id)
                    summary = {
                        'changedFiles': GitLineageService.changed_file_summary_from_show(show_text),
                        'fileCount': 0,
                        'fallback': True,
                        'diffError': diff_err,
                    }
                    summary['fileCount'] = len(summary['changedFiles'])
                    PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                        'diff_summary_json': summary,
                        'status': 2,
                    })
                else:
                    PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 2})

            lineage_items = []
            if enable_lineage and commit_id:
                lineage_items, lineage_err = GitLineageService.analyze_commit_lineage(
                    repo_path, commit_id, max_pickaxe_per_file=max_pickaxe
                )
                if lineage_err:
                    PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                        'status': 7,
                        'description': (source_ref or '') + '\nlineage_error: ' + lineage_err,
                    })
                    return {}, lineage_err
                PreciseTestDao.delete_by_filters(
                    session, PreciseLineageItem,
                    [PreciseLineageItem.analysis_id == int(analysis_id)]
                )
                rows = []
                for item in lineage_items:
                    rows.append({
                        'analysis_id': int(analysis_id),
                        'file_path': item.get('file_path') or '',
                        'modified_row': item.get('modified_row') or '',
                        'row_kind': item.get('row_kind') or 'deleted',
                        'histories': item.get('histories') or [],
                        'is_delete': 0,
                    })
                if rows:
                    PreciseTestDao.batch_create(session, PreciseLineageItem, rows)

            must_test = {'cases': [], 'contracts': [], 'inspections': [], 'ai_status': 'skipped'}
            if enable_recommend:
                # 契约/巡检深链可同步拿到；AI 影响 + 推荐用例放到专用后台线程，避免拖死本次请求
                must_test['contracts'] = cls._link_contracts(session, project_id or analysis.project_id)
                must_test['inspections'] = cls._link_inspections(session, project_id or analysis.project_id)
                must_test['ai_status'] = 'pending'
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                    'must_test_assets': must_test,
                    'status': 2,
                })
                from app.core.ai_executor import submit_ai_background
                submit_ai_background(cls._background_ai_recommend, int(analysis_id), int(project_id or analysis.project_id or 0))
            else:
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {'status': 2})

            return cls.detail(session, analysis_id)
        finally:
            session.close()

    @classmethod
    def _background_ai_recommend(cls, analysis_id, project_id):
        """后台线程：AI 影响分析 + 必测用例推荐，写回 must_test_assets。"""
        from logger import logger
        session = cls._session()
        try:
            analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
            if not analysis:
                return
            assets = dict(analysis.must_test_assets or {})
            assets['ai_status'] = 'running'
            PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                'must_test_assets': assets,
                'status': 3,
            })
            try:
                PreciseTestService.ai_impact(session, analysis_id)
            except Exception as exc:
                logger.warning('雷达后台 AI 影响分析失败 analysis_id=%s: %s', analysis_id, exc)
            _, rec_err = PreciseTestService.generate_recommendations(session, analysis_id)
            analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
            assets = dict((analysis.must_test_assets if analysis else None) or {})
            if not rec_err:
                assets['cases'] = cls._serialize_recommendations(session, analysis_id)
            assets['contracts'] = cls._link_contracts(session, project_id or (analysis.project_id if analysis else None))
            assets['inspections'] = cls._link_inspections(session, project_id or (analysis.project_id if analysis else None))
            assets['ai_status'] = 'done' if not rec_err else 'failed'
            if rec_err:
                assets['ai_error'] = str(rec_err)
            PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                'must_test_assets': assets,
                'status': 4 if not rec_err else 7,
            })
            logger.info('雷达后台推荐完成 analysis_id=%s status=%s', analysis_id, assets.get('ai_status'))
        except Exception as exc:
            logger.exception('雷达后台推荐异常 analysis_id=%s: %s', analysis_id, exc)
            try:
                analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
                assets = dict((analysis.must_test_assets if analysis else None) or {})
                assets['ai_status'] = 'failed'
                assets['ai_error'] = str(exc)
                PreciseTestDao.update_by_id(session, PreciseAnalysis, analysis_id, {
                    'must_test_assets': assets,
                    'status': 7,
                })
            except Exception:
                pass
        finally:
            session.close()

    @classmethod
    def recompute_lineage(cls, analysis_id, options=None):
        options = options or {}
        max_pickaxe = int(options.get('max_pickaxe_per_file') or GitLineageService.MAX_PICKAXE_PER_FILE)
        session = cls._session()
        try:
            analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
            if not analysis:
                return {}, '未查询到分析任务'
            commit_id = analysis.commit_id or analysis.target_commit
            if not commit_id:
                return {}, '分析缺少 commit_id / target_commit'
            repo_path, err = GitDiffService.ensure_repo(analysis.repository_url, analysis.branch_name)
            if err:
                return {}, err
            lineage_items, lineage_err = GitLineageService.analyze_commit_lineage(
                repo_path, commit_id, max_pickaxe_per_file=max_pickaxe
            )
            if lineage_err:
                return {}, lineage_err
            PreciseTestDao.delete_by_filters(
                session, PreciseLineageItem,
                [PreciseLineageItem.analysis_id == int(analysis_id)]
            )
            rows = [{
                'analysis_id': int(analysis_id),
                'file_path': item.get('file_path') or '',
                'modified_row': item.get('modified_row') or '',
                'row_kind': item.get('row_kind') or 'deleted',
                'histories': item.get('histories') or [],
                'is_delete': 0,
            } for item in lineage_items]
            if rows:
                PreciseTestDao.batch_create(session, PreciseLineageItem, rows)
            return cls.detail(session, analysis_id)
        finally:
            session.close()

    @classmethod
    def list_runs(cls, filters=None, page_no=1, page_size=20):
        filters = filters or {}
        session = cls._session()
        try:
            from sqlalchemy import or_
            query_filters = [PreciseAnalysis.is_delete == 0]
            source_type = filters.get('source_type') or filters.get('sourceType')
            product_id = filters.get('product_id') or filters.get('productId')
            project_id = filters.get('project_id') or filters.get('projectId')
            keyword = (filters.get('keyword') or '').strip()
            if product_id not in (None, ''):
                query_filters.append(PreciseAnalysis.product_id == int(product_id))
            if project_id not in (None, ''):
                query_filters.append(PreciseAnalysis.project_id == int(project_id))
            if source_type:
                query_filters.append(PreciseAnalysis.source_type == source_type)
            else:
                query_filters.append(or_(
                    PreciseAnalysis.source_type.in_(['radar', 'git_url', 'mr_url']),
                    PreciseAnalysis.analysis_no.like('IR%'),
                    PreciseAnalysis.commit_id.isnot(None),
                ))
            if keyword:
                like = '%{}%'.format(keyword)
                query_filters.append(or_(
                    PreciseAnalysis.title.like(like),
                    PreciseAnalysis.analysis_no.like(like),
                    PreciseAnalysis.commit_id.like(like),
                    PreciseAnalysis.source_ref.like(like),
                ))
            items, total = PreciseTestDao.list_by_filters(
                session, PreciseAnalysis, query_filters, page_no, page_size,
                PreciseAnalysis.created_time
            )
            rows = []
            for item in items:
                row = item.to_dict() if hasattr(item, 'to_dict') else {}
                row['precise_analysis_id'] = item.id
                rows.append(row)
            return {'list': rows, 'total': total}, ''
        finally:
            session.close()

    @classmethod
    def detail(cls, session_or_id, analysis_id=None):
        """兼容 detail(session, id) 与 detail(id)。"""
        own_session = False
        if analysis_id is None:
            analysis_id = session_or_id
            session = cls._session()
            own_session = True
        else:
            session = session_or_id
        try:
            analysis = PreciseTestDao.get_by_id(session, PreciseAnalysis, analysis_id)
            if not analysis:
                return {}, '未查询到分析任务'
            changed, _ = PreciseTestDao.list_by_filters(
                session, PreciseChangedFile,
                [PreciseChangedFile.analysis_id == int(analysis_id), PreciseChangedFile.is_delete == 0],
                None, None
            )
            lineage, _ = PreciseTestDao.list_by_filters(
                session, PreciseLineageItem,
                [PreciseLineageItem.analysis_id == int(analysis_id), PreciseLineageItem.is_delete == 0],
                None, None, PreciseLineageItem.id
            )
            must_test = analysis.must_test_assets or {}
            if not must_test.get('cases'):
                must_test = dict(must_test)
                must_test['cases'] = cls._serialize_recommendations(session, analysis_id)
            run = analysis.to_dict() if hasattr(analysis, 'to_dict') else {}
            run['precise_analysis_id'] = analysis.id
            changed_files = []
            for item in changed:
                changed_files.append({
                    'path': item.file_path,
                    'file_path': item.file_path,
                    'change_type': item.change_type,
                    'added': len(item.added_lines or []),
                    'deleted': len(item.deleted_lines or []),
                })
            if not changed_files and analysis.diff_summary_json:
                summary = analysis.diff_summary_json or {}
                for item in summary.get('changedFiles') or []:
                    changed_files.append({
                        'path': item.get('path') or item.get('filePath') or item.get('file_path'),
                        'file_path': item.get('path') or item.get('filePath') or item.get('file_path'),
                        'added': item.get('added') or len(item.get('addedLines') or []),
                        'deleted': item.get('deleted') or len(item.get('deletedLines') or []),
                    })
            lineage_rows = []
            for item in lineage:
                histories = item.histories or []
                latest = histories[0] if histories else {}
                lineage_rows.append({
                    'id': item.id,
                    'file_path': item.file_path,
                    'modified_row': item.modified_row,
                    'row_kind': item.row_kind,
                    'histories': histories,
                    'latest_commit_id': latest.get('commit_id') or '',
                    'latest_date': latest.get('date') or '',
                    'latest_author': latest.get('author') or '',
                    'latest_remark': latest.get('remark') or '',
                })
            commit_id = run.get('commit_id') or run.get('target_commit')
            if commit_id and run.get('repository_url'):
                try:
                    repo_path, _ = GitDiffService.ensure_repo(run.get('repository_url'), run.get('branch_name'))
                    if repo_path:
                        meta, _ = GitLineageService.get_commit_meta(repo_path, commit_id)
                        if meta:
                            run['commit_date'] = meta.get('date')
                            run['commit_author'] = meta.get('author')
                            run['commit_remark'] = meta.get('remark')
                except Exception:
                    pass
            data = {
                'run': run,
                'changed_files': changed_files,
                'lineage': lineage_rows,
                'must_test': must_test,
            }
            return data, ''
        finally:
            if own_session:
                session.close()

    @staticmethod
    def _serialize_recommendations(session, analysis_id):
        items, _ = PreciseTestDao.list_by_filters(
            session, PreciseRecommendation,
            [PreciseRecommendation.analysis_id == int(analysis_id), PreciseRecommendation.is_delete == 0],
            None, None
        )
        cases = []
        for item in items:
            if not item.case_id and not item.api_path:
                continue
            cases.append({
                'case_id': item.case_id,
                'title': item.module_name or item.api_path or '',
                'module_name': item.module_name,
                'api_path': item.api_path,
                'priority': item.recommend_level,
                'risk_level': item.risk_level,
                'reason': item.reason or item.ai_reason,
                'route': '/test-platform/case?caseId={}'.format(item.case_id) if item.case_id else '',
            })
        return cases

    @staticmethod
    def _link_contracts(session, project_id):
        if not project_id:
            return []
        try:
            suites = session.query(ContractSuite).filter(
                ContractSuite.project_id == int(project_id),
                ContractSuite.is_delete == 0,
                ContractSuite.enabled == 1,
            ).order_by(ContractSuite.id.desc()).limit(10).all()
        except Exception:
            return []
        return [{
            'suite_id': item.id,
            'name': item.name,
            'route': '/contract/suite/edit?id={}'.format(item.id),
        } for item in suites]

    @staticmethod
    def _link_inspections(session, project_id):
        if not project_id:
            return []
        try:
            groups = session.query(InspectionGroup).filter(
                InspectionGroup.project_id == int(project_id),
                InspectionGroup.is_delete == 0,
                InspectionGroup.enabled == 1,
            ).order_by(InspectionGroup.id.desc()).limit(10).all()
        except Exception:
            return []
        return [{
            'group_id': item.id,
            'name': item.name,
            'route': '/inspection/tasks?groupId={}'.format(item.id),
        } for item in groups]
