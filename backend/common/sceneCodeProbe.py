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
    '.sql', '.xml', '.yml', '.yaml', '.prisma', '.json', '.properties',
    '.toml', '.ini', '.conf', '.gradle', '.cs', '.swift',
}
PRIORITY_NAME_HINTS = (
    'model', 'entity', 'domain', 'mapper', 'repository', 'dao', 'schema',
    'migration', 'sql', 'po', 'do', 'dto', 'table', 'persist', 'post',
    'config', 'setting', 'constant', 'const', 'enum', 'option', 'dict',
    'scene', 'scenario', 'map', 'background', 'ip', 'endpoint', 'service',
)
# 中文业务词 → 代码里常见英文片段，提升「问代码逻辑」命中率
CN_CODE_ALIASES = {
    '场景图': ['scene', 'scenemap', 'scene_map', 'scenario', 'background', 'bg', 'poster', 'cover', 'map'],
    '场景': ['scene', 'scenario', 'stage', 'scenemap'],
    '配置': ['config', 'setting', 'option', 'constant', 'enum', 'dict', 'properties'],
    '常量': ['const', 'constant', 'enum', 'define'],
    '枚举': ['enum', 'enums', 'constant'],
    '逻辑': ['service', 'handler', 'logic', 'biz', 'business', 'usecase'],
    '选择': ['select', 'choose', 'option', 'pick'],
    '用户': ['user', 'member', 'account', 'customer'],
    '订单': ['order', 'trade', 'bill'],
    '时长': ['duration', 'time', 'seconds', 'usage'],
    '图片': ['image', 'img', 'picture', 'photo', 'avatar'],
    '开关': ['switch', 'toggle', 'flag', 'enable', 'disable'],
}
MAX_SCAN_FILES = 400
MAX_SELECTED = 12
MAX_FILE_CHARS = 2800
MAX_HINT_CHARS = 9000
SYNC_TIMEOUT_SEC = 35
STALE_SEC = 30 * 60  # 30 分钟内已拉取则跳过 sync


class SceneCodeProbe(object):

    @classmethod
    def build_hint(cls, project_id, user_text, matched_tables=None):
        """
        返回 (hint_text, meta)
        meta: repoUrl, branch, codeFiles, codeError, repos, missingRepoTip, synced
        """
        meta = {
            'repoUrl': '',
            'branch': '',
            'codeFiles': [],
            'codeError': '',
            'repos': [],
            'missingRepoTip': '',
            'synced': False,
            'usedCache': False,
        }
        if project_id in (None, ''):
            meta['codeError'] = '缺少 projectId，跳过代码探查'
            meta['missingRepoTip'] = '想要更准确查询，建议在项目里面配置 Git 代码仓库哦'
            return '', meta

        session_wrap = None
        try:
            from app.api.service.projectCodePrdService import ProjectCodePrdService
            session_wrap = SqlSession()
            repos = ProjectCodePrdService.list_git_repos(session_wrap.session, project_id, enabled_only=True)
            if not repos:
                meta['codeError'] = '项目未配置 Git 仓库'
                meta['missingRepoTip'] = '想要更准确查询，建议在项目里面配置 Git 代码仓库哦'
                return '', meta

            keywords = cls._keywords(user_text, matched_tables)
            all_selected = []
            repo_metas = []
            errors = []

            for repo in repos:
                info = ProjectCodePrdService.git_repo_to_dict(repo)
                repo_url = (info.get('repoUrl') or '').strip()
                branch = (info.get('defaultBranch') or 'master').strip() or 'master'
                name = (info.get('name') or '仓库').strip()
                role = (info.get('roleTag') or '').strip()
                if not repo_url:
                    continue
                if not ProjectCodePrdService._is_safe_git_url(repo_url):
                    errors.append('{} 地址不合法'.format(name))
                    continue
                label = '{}-{}'.format(name, role or 'code')
                repo_dir = ProjectCodePrdService._get_repo_work_dir(
                    session_wrap.session, project_id, branch, repo_label=label
                )
                # 兼容旧单仓目录（无 label）
                legacy_dir = ProjectCodePrdService._get_repo_work_dir(
                    session_wrap.session, project_id, branch, repo_label=''
                )
                use_dir = repo_dir
                need_sync = cls._need_sync(repo_dir)
                if need_sync and not (Path(repo_dir) / '.git').exists() and (Path(legacy_dir) / '.git').exists() and len(repos) == 1:
                    use_dir = legacy_dir
                    need_sync = cls._need_sync(legacy_dir)

                sync_err = ''
                used_cache = False
                if need_sync:
                    sync_err = cls._sync_repo_soft(ProjectCodePrdService, repo_url, branch, use_dir)
                    meta['synced'] = True
                    if sync_err and not (Path(use_dir) / '.git').exists():
                        errors.append('{}: {}'.format(name, sync_err))
                        repo_metas.append({
                            'name': name, 'repoUrl': repo_url, 'branch': branch, 'roleTag': role,
                            'synced': False, 'error': sync_err,
                        })
                        continue
                    if sync_err:
                        used_cache = True
                        meta['usedCache'] = True
                else:
                    used_cache = True
                    meta['usedCache'] = True

                selected = cls._select_files(str(use_dir), keywords, matched_tables or [])
                for item in selected:
                    item = dict(item)
                    item['repoName'] = name
                    item['repoUrl'] = repo_url
                    item['branch'] = branch
                    item['roleTag'] = role
                    item['path'] = '[{}] {}'.format(name, item.get('path'))
                    all_selected.append(item)
                repo_metas.append({
                    'name': name,
                    'repoUrl': repo_url,
                    'branch': branch,
                    'roleTag': role,
                    'synced': need_sync and not sync_err,
                    'usedCache': used_cache,
                    'fileCount': len(selected),
                    'error': sync_err or '',
                })

            meta['repos'] = repo_metas
            if repo_metas:
                meta['repoUrl'] = repo_metas[0].get('repoUrl') or ''
                meta['branch'] = repo_metas[0].get('branch') or ''

            if not all_selected:
                meta['codeError'] = '；'.join(errors) if errors else '已配置仓库，但未匹配到相关代码文件'
                return '', meta

            all_selected.sort(key=lambda x: (-x.get('score', 0), x.get('path') or ''))
            picked = all_selected[:MAX_SELECTED]
            meta['codeFiles'] = [item['path'] for item in picked]
            if errors and not meta['codeError']:
                meta['codeError'] = '部分仓库同步异常：' + '；'.join(errors[:3])
            hint = cls._format_hint_multi(picked, keywords)
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
    def _need_sync(cls, repo_dir):
        """无本地仓或超过 STALE_SEC 未 fetch 则需要拉取。"""
        import time
        root = Path(repo_dir)
        if not (root / '.git').exists():
            return True
        marker = root / '.git' / 'FETCH_HEAD'
        if not marker.exists():
            marker = root / '.git' / 'HEAD'
        try:
            age = time.time() - marker.stat().st_mtime
            return age > STALE_SEC
        except Exception:
            return True

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
            for cn, aliases in CN_CODE_ALIASES.items():
                if cn in token or token in cn or cn in text:
                    words.update(aliases)
        for cn, aliases in CN_CODE_ALIASES.items():
            if cn in text:
                words.add(cn)
                words.update(aliases)
        if '帖子' in text:
            words.update(['post', 'posts', 'article', 'feed'])
        if '评论' in text:
            words.update(['comment', 'comments', 'reply'])
        if re.search(r'(?i)\bip\b|选.?ip|选择.?ip', text):
            words.update(['ip', 'host', 'endpoint', 'server', 'address'])
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
        for signal in (
            '@entity', '@table', '__tablename__', 'create table', 'foreign key',
            'mapper', 'repository', 'enum', 'const ', 'constant', 'config',
            'switch', 'case ', 'export const', 'final static',
        ):
            if signal in lower:
                score += 2
        return score

    @classmethod
    def _format_hint(cls, repo_url, branch, selected, keywords):
        lines = [
            '以下代码摘录来自项目配置的 Git 仓库（已自动拉取），可用于表映射查数或代码逻辑问答：',
            '仓库：{} @ {}'.format(repo_url, branch),
            '关键词：{}'.format(', '.join(keywords[:24]) if keywords else '（启发式）'),
            '要求：优先遵循实体/表映射、配置常量、枚举与业务分支；禁止编造代码中不存在的表、字段或枚举值。',
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

    @classmethod
    def _format_hint_multi(cls, selected, keywords):
        lines = [
            '以下代码摘录来自项目配置的一个或多个 Git 仓库（微服务/前后端可多仓；已按需拉取最新或使用近期缓存）。',
            '既可用于判断查哪张表，也可直接回答配置/枚举/流程等代码逻辑问题。',
            '关键词：{}'.format(', '.join(keywords[:24]) if keywords else '（启发式）'),
            '要求：只基于代码与表结构；不确定则说明缺文件/缺配置；禁止编造。',
            '',
        ]
        for item in selected:
            lines.append('### [{}|{}] {} (score={})'.format(
                item.get('repoName') or '',
                item.get('roleTag') or '',
                item.get('path'),
                item.get('score'),
            ))
            lines.append('```')
            lines.append((item.get('content') or '').rstrip())
            lines.append('```')
            lines.append('')
        text = '\n'.join(lines).strip()
        if len(text) > MAX_HINT_CHARS:
            return text[:MAX_HINT_CHARS] + '\n...（代码上下文已截断）'
        return text
