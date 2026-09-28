# encoding: UTF-8
"""拉取项目 Git 仓库，抽取与造数相关的代码上下文。"""
from __future__ import unicode_literals

import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

from common.sqlSession import SqlSession
from logger import logger

IGNORE_DIRS = {
    '.git', 'node_modules', 'dist', 'build', '__pycache__', '.venv', 'venv',
    'target', '.idea', '.vscode', 'vendor', 'coverage', 'downloads-git',
}
INCLUDE_EXTS = {
    '.py', '.js', '.ts', '.tsx', '.vue', '.java', '.go', '.kt', '.php',
    '.sql', '.xml', '.yml', '.yaml', '.prisma',
}
PRIORITY_NAME_HINTS = (
    'model', 'entity', 'domain', 'mapper', 'repository', 'dao', 'schema',
    'migration', 'sql', 'po', 'do', 'dto', 'table', 'persist', 'post',
)
MAX_SCAN_FILES = 400
MAX_SELECTED = 12
MAX_FILE_CHARS = 2800
MAX_HINT_CHARS = 9000
SYNC_TIMEOUT_SEC = 35


class SceneCodeProbe(object):

    @classmethod
    def build_hint(cls, project_id, user_text, matched_tables=None):
        """
        返回 (hint_text, meta)
        meta: repoUrl, branch, codeFiles, codeError
        """
        meta = {
            'repoUrl': '',
            'branch': '',
            'codeFiles': [],
            'codeError': '',
        }
        if project_id in (None, ''):
            meta['codeError'] = '缺少 projectId，跳过代码探查'
            return '', meta

        session_wrap = None
        try:
            from app.api.service.projectCodePrdService import ProjectCodePrdService
            session_wrap = SqlSession()
            cfg = ProjectCodePrdService.get_config_by_project(session_wrap.session, project_id)
            if not cfg or not (cfg.repo_url or '').strip():
                meta['codeError'] = '项目未配置 Git 仓库（请到项目设置 → 代码仓库）'
                return '', meta
            repo_url = (cfg.repo_url or '').strip()
            branch = (cfg.default_branch or 'master').strip() or 'master'
            meta['repoUrl'] = repo_url
            meta['branch'] = branch

            if not ProjectCodePrdService._is_safe_git_url(repo_url):
                meta['codeError'] = 'Git 仓库地址格式不正确'
                return '', meta

            repo_dir = ProjectCodePrdService._get_repo_work_dir(session_wrap.session, project_id, branch)
            sync_err = cls._sync_repo_soft(ProjectCodePrdService, repo_url, branch, repo_dir)
            if sync_err and not (Path(repo_dir) / '.git').exists():
                meta['codeError'] = sync_err
                return '', meta
            if sync_err:
                meta['codeError'] = '仓库同步未完成，使用本地缓存：{}'.format(sync_err)

            keywords = cls._keywords(user_text, matched_tables)
            selected = cls._select_files(str(repo_dir), keywords, matched_tables or [])
            if not selected:
                if not meta['codeError']:
                    meta['codeError'] = '已拉取仓库，但未匹配到相关代码文件'
                return '', meta

            meta['codeFiles'] = [item['path'] for item in selected]
            hint = cls._format_hint(repo_url, branch, selected, keywords)
            return hint, meta
        except Exception as exc:
            logger.warning('SceneCodeProbe 失败 project_id=%s err=%s', project_id, exc)
            meta['codeError'] = '代码探查失败：{}'.format(exc)
            return '', meta
        finally:
            if session_wrap is not None:
                try:
                    session_wrap.close()
                except Exception:
                    pass

    @classmethod
    def _sync_repo_soft(cls, service_cls, repo_url, branch, repo_dir):
        """限时同步；超时则返回错误但不阻塞过久。"""
        def _job():
            return service_cls._sync_repo(repo_url, branch, repo_dir)

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_job)
            return future.result(timeout=SYNC_TIMEOUT_SEC) or ''
        except FuturesTimeout:
            return '拉取/更新仓库超时（{}s）'.format(SYNC_TIMEOUT_SEC)
        except Exception as exc:
            return '拉取仓库失败：{}'.format(exc)
        finally:
            executor.shutdown(wait=False)

    @classmethod
    def _keywords(cls, user_text, matched_tables):
        text = user_text or ''
        words = set()
        for token in re.findall(r'[a-zA-Z][a-zA-Z0-9_]{1,40}', text):
            words.add(token.lower())
        for token in re.findall(r'[\u4e00-\u9fff]{2,8}', text):
            words.add(token)
        if '帖子' in text:
            words.update(['post', 'posts', 'article', 'feed'])
        if '评论' in text:
            words.update(['comment', 'comments', 'reply'])
        for table in matched_tables or []:
            name = str(table or '').strip()
            if not name:
                continue
            words.add(name.lower())
            words.add(name.lower().replace('_', ''))
            for part in re.split(r'[_\-]', name):
                if len(part) >= 2:
                    words.add(part.lower())
        return [w for w in words if w]

    @classmethod
    def _select_files(cls, repo_dir, keywords, matched_tables):
        if not os.path.isdir(repo_dir):
            return []
        candidates = []
        for root, dirs, files in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in INCLUDE_EXTS:
                    continue
                path = os.path.join(root, filename)
                rel = os.path.relpath(path, repo_dir).replace('\\', '/')
                if len(candidates) >= MAX_SCAN_FILES:
                    break
                score = cls._score_path(rel, keywords, matched_tables)
                if score <= 0 and not any(h in rel.lower() for h in PRIORITY_NAME_HINTS):
                    continue
                if score <= 0:
                    score = 1
                candidates.append((score, rel, path, ext))
            if len(candidates) >= MAX_SCAN_FILES:
                break

        candidates.sort(key=lambda x: (-x[0], x[1]))
        selected = []
        for score, rel, path, ext in candidates[:MAX_SELECTED * 3]:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read(MAX_FILE_CHARS + 200)
            except Exception:
                continue
            content_score = cls._score_content(content, keywords, matched_tables)
            total = score + content_score
            if total <= 0:
                continue
            selected.append({
                'path': rel,
                'score': total,
                'ext': ext,
                'content': content[:MAX_FILE_CHARS],
            })
            if len(selected) >= MAX_SELECTED:
                break
        selected.sort(key=lambda x: (-x['score'], x['path']))
        return selected[:MAX_SELECTED]

    @classmethod
    def _score_path(cls, rel_path, keywords, matched_tables):
        lower = (rel_path or '').lower()
        score = 0
        for hint in PRIORITY_NAME_HINTS:
            if hint in lower:
                score += 3
        for table in matched_tables or []:
            t = str(table or '').lower()
            if t and t in lower:
                score += 10
            compact = t.replace('_', '')
            if compact and compact in lower.replace('_', '').replace('-', ''):
                score += 6
        for kw in keywords:
            kw_l = str(kw).lower()
            if len(kw_l) >= 2 and kw_l in lower:
                score += 4
        return score

    @classmethod
    def _score_content(cls, content, keywords, matched_tables):
        lower = (content or '').lower()
        score = 0
        for table in matched_tables or []:
            t = str(table or '').lower()
            if not t:
                continue
            if t in lower:
                score += 8
            if 'insert into {}'.format(t) in lower or 'from {}'.format(t) in lower:
                score += 6
        for kw in keywords:
            kw_l = str(kw).lower()
            if len(kw_l) >= 2 and kw_l in lower:
                score += 2
        for signal in ('@entity', '@table', '__tablename__', 'create table', 'foreign key', 'mapper', 'repository'):
            if signal in lower:
                score += 2
        return score

    @classmethod
    def _format_hint(cls, repo_url, branch, selected, keywords):
        lines = [
            '以下代码摘录来自项目配置的 Git 仓库（已自动拉取），请结合表结构和代码逻辑生成造数 SQL：',
            '仓库：{} @ {}'.format(repo_url, branch),
            '关键词：{}'.format(', '.join(keywords[:24]) if keywords else '（启发式）'),
            '要求：优先遵循实体/表映射、必填字段、默认值与外键依赖；禁止编造代码中不存在的表或字段。',
            '',
        ]
        for item in selected:
            lines.append('### 文件 {} (score={})'.format(item.get('path'), item.get('score')))
            lines.append('```')
            lines.append((item.get('content') or '').rstrip())
            lines.append('```')
            lines.append('')
        text = '\n'.join(lines).strip()
        if len(text) > MAX_HINT_CHARS:
            return text[:MAX_HINT_CHARS] + '\n...（代码上下文已截断）'
        return text
