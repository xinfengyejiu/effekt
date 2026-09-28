# encoding: UTF-8
"""Git 行级血缘：URL 解析、噪声过滤、diff 有效行提取、pickaxe（git log -S）。

移植自 D:\\javaTest analysis/GitLogExample.java，与精准测试 GitDiffService 配合使用。
"""
from __future__ import unicode_literals

import re
import subprocess
from collections import OrderedDict


class GitLineageService(object):
    COMMIT_ID_RE = re.compile(r'(?:commit_id=|/commit/|/-/commit/)([0-9a-fA-F]{7,40})')
    MR_PATH_RE = re.compile(r'/merge_requests?/(\d+)', re.I)
    REPO_FROM_COMMIT_RE = re.compile(
        r'^(https?://[^/]+/.+?)(?:/-)?/(?:commit|merge_requests?)/', re.I
    )
    REPO_FROM_QUERY_RE = re.compile(r'^(https?://[^/]+/.+?)/-/merge_requests?/', re.I)

    MAX_PICKAXE_PER_FILE = 30
    MAX_PICKAXE_GLOBAL = 80
    PICKAXE_TIMEOUT = 60
    SHOW_TIMEOUT = 120

    @staticmethod
    def is_not_actual_code(line):
        """噪声行过滤（对齐 javaTest.isNotActualCode）。"""
        trimmed = (line or '').strip()
        if not trimmed:
            return True
        if trimmed.startswith('+') or trimmed.startswith('-'):
            return True
        prefixes = (
            '//', 'import', 'log', '/**', '*', '*/', '@', 'package', ';', '/)', '(',
            ',', '\\', 'console.', '});', '} catch', 'try {',
        )
        if any(trimmed.startswith(p) for p in prefixes):
            return True
        if trimmed in ('}', '{'):
            return True
        return False

    @staticmethod
    def strip_diff_prefix(line):
        text = line or ''
        if text.startswith('+') or text.startswith('-') or text.startswith(' '):
            return text[1:].strip()
        return text.strip()

    @classmethod
    def extract_commit_id(cls, url):
        raw = (url or '').strip().replace(' ', '')
        if not raw:
            return ''
        match = cls.COMMIT_ID_RE.search(raw)
        return match.group(1) if match else ''

    @classmethod
    def extract_mr_iid(cls, url):
        raw = (url or '').strip().replace(' ', '')
        match = cls.MR_PATH_RE.search(raw)
        return match.group(1) if match else ''

    @classmethod
    def extract_repository_url(cls, url):
        """从 Commit/MR URL 推断可 clone 的仓库地址（.git）。"""
        raw = (url or '').strip().replace(' ', '')
        if not raw:
            return ''
        for pattern in (cls.REPO_FROM_COMMIT_RE, cls.REPO_FROM_QUERY_RE):
            match = pattern.search(raw)
            if match:
                base = match.group(1).rstrip('/')
                if base.endswith('.git'):
                    return base
                return base + '.git'
        if raw.endswith('.git') or raw.endswith('.git/'):
            return raw.rstrip('/')
        if '/-/' not in raw and 'commit' not in raw.lower() and 'merge_request' not in raw.lower():
            return raw.rstrip('/') + ('' if raw.endswith('.git') else '.git')
        return ''

    @classmethod
    def parse_git_url(cls, git_url):
        """解析 Commit/MR URL → commit_id / repository_url / source_type。"""
        raw = (git_url or '').strip()
        commit_id = cls.extract_commit_id(raw)
        mr_iid = cls.extract_mr_iid(raw)
        repository_url = cls.extract_repository_url(raw)
        source_type = 'git_url'
        if mr_iid:
            source_type = 'mr_url'
        elif commit_id:
            source_type = 'git_url'
        elif not repository_url and raw:
            return {}, '无法从 URL 解析仓库或 commit，请提供 Commit/MR 链接或显式 repository_url + commit'
        return {
            'commit_id': commit_id,
            'mr_iid': mr_iid,
            'repository_url': repository_url,
            'source_type': source_type,
            'source_ref': raw,
        }, ''

    @staticmethod
    def _run_git(args, cwd=None, timeout=120):
        completed = subprocess.run(
            ['git'] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, shell=False
        )
        stdout = completed.stdout.decode('utf-8', errors='ignore')
        stderr = completed.stderr.decode('utf-8', errors='ignore')
        if completed.returncode != 0:
            return '', stderr or stdout or 'git命令执行失败'
        return stdout, ''

    @classmethod
    def git_show(cls, repo_path, commit_id):
        if not repo_path or not commit_id:
            return '', 'repo_path 与 commit_id 必传'
        out, err = cls._run_git(['show', '--format=fuller', commit_id], cwd=repo_path, timeout=cls.SHOW_TIMEOUT)
        if err:
            return '', err
        return out, ''

    @classmethod
    def is_merge_commit(cls, repo_path, commit_id):
        out, err = cls._run_git(['rev-list', '--parents', '-n', '1', commit_id], cwd=repo_path, timeout=30)
        if err or not out.strip():
            return False, err
        parts = out.strip().split()
        return len(parts) > 2, ''

    @classmethod
    def parent_commit(cls, repo_path, commit_id):
        out, err = cls._run_git(['rev-parse', '{}^'.format(commit_id)], cwd=repo_path, timeout=30)
        if err:
            return '', err
        return out.strip(), ''

    @classmethod
    def find_context_for_addition(cls, diff_lines, line_index):
        """纯新增块：向上下找有效上下文行作 pickaxe 锚定。"""
        block_start = line_index
        while block_start > 0 and diff_lines[block_start - 1].startswith('+'):
            block_start -= 1
        block_end = line_index
        while block_end < len(diff_lines) - 1 and diff_lines[block_end + 1].startswith('+'):
            block_end += 1

        context_start = block_start - 1
        while context_start >= 0 and cls.is_not_actual_code(diff_lines[context_start]):
            context_start -= 1
        context_end = block_end + 1
        while context_end < len(diff_lines) and cls.is_not_actual_code(diff_lines[context_end]):
            context_end += 1

        context = []
        if context_start >= 0:
            context.append(diff_lines[context_start])
        if context_end < len(diff_lines):
            context.append(diff_lines[context_end])
        return context

    @classmethod
    def split_diff_by_file(cls, show_text):
        """按 diff --git 切文件，返回 OrderedDict[path] = lines。"""
        files = OrderedDict()
        current_path = None
        current_lines = []
        for line in (show_text or '').splitlines():
            if line.startswith('diff --git '):
                if current_path is not None:
                    files[current_path] = current_lines
                parts = line.split(' ')
                path = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith('b/') else parts[-1]
                current_path = path
                current_lines = []
            elif current_path is not None:
                current_lines.append(line)
        if current_path is not None:
            files[current_path] = current_lines
        return files

    @classmethod
    def collect_search_rows(cls, file_diff_lines):
        """收集 deleted 有效行 + 新增块上下文锚定行。"""
        rows = []
        seen = set()
        for idx, line in enumerate(file_diff_lines):
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                continue
            if line.startswith('-') and not line.startswith('---'):
                content = cls.strip_diff_prefix(line)
                if content and not cls.is_not_actual_code(content):
                    key = ('deleted', content)
                    if key not in seen:
                        seen.add(key)
                        rows.append({'modified_row': content, 'row_kind': 'deleted'})
            elif line.startswith('+') and not line.startswith('+++'):
                content = cls.strip_diff_prefix(line)
                if content and not cls.is_not_actual_code(content):
                    key = ('added', content)
                    if key not in seen and len(content) >= 8:
                        seen.add(key)
                        rows.append({'modified_row': content, 'row_kind': 'context_for_add'})
                    contexts = cls.find_context_for_addition(file_diff_lines, idx)
                    for ctx in contexts:
                        ctx_content = cls.strip_diff_prefix(ctx)
                        if not ctx_content or cls.is_not_actual_code(ctx_content):
                            continue
                        key = ('context', ctx_content)
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append({'modified_row': ctx_content, 'row_kind': 'context_for_add'})
        return rows

    @classmethod
    def get_commit_meta(cls, repo_path, commit_id):
        """查询单个 commit 的完整 id / 作者 / 时间 / 说明。"""
        if not repo_path or not commit_id:
            return {}, 'repo_path 与 commit_id 必传'
        out, err = cls._run_git(
            ['show', '-s', '--format=%H|%an|%ae|%ad|%s', '--date=iso', commit_id],
            cwd=repo_path, timeout=30
        )
        if err or not out.strip():
            return {}, err or '未找到该 commit'
        parts = out.strip().split('|', 4)
        if len(parts) < 5:
            return {}, 'commit 元信息解析失败'
        commit_hash, author, email, date, subject = parts
        return {
            'commit_id': commit_hash,
            'author': author,
            'email': email,
            'date': date,
            'remark': subject,
            'branch_name': cls._branch_containing(repo_path, commit_hash),
        }, ''

    @classmethod
    def pickaxe_histories(cls, repo_path, search_string, file_path=None, max_commits=15):
        """git log -S <string> [-- <file>]，返回历史提交摘要列表。"""
        search = (search_string or '').strip()
        if not search or len(search) < 4:
            return []
        args = [
            'log', '-S', search, '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso', '-n', str(max_commits),
        ]
        if file_path:
            args.extend(['--', file_path])
        out, err = cls._run_git(args, cwd=repo_path, timeout=cls.PICKAXE_TIMEOUT)
        if err or not out.strip():
            return []
        histories = []
        for line in out.splitlines():
            parts = line.split('|', 4)
            if len(parts) < 5:
                continue
            commit_hash, author, email, date, subject = parts
            branch = cls._branch_containing(repo_path, commit_hash)
            snippet = cls._show_snippet(repo_path, commit_hash, file_path, search)
            histories.append({
                'commit_id': commit_hash,
                'author': author,
                'email': email,
                'date': date,
                'remark': subject,
                'branch_name': branch,
                'change_detail': snippet,
            })
        return histories

    @classmethod
    def trace_code(cls, repo_path, code, file_path=None, max_commits=20):
        """按文件路径 + 代码片段追溯引入/变更过的 commit id 与时间。"""
        search = (code or '').strip()
        if not search:
            return [], '请输入要追溯的代码片段'
        if len(search) < 4:
            return [], '代码片段过短，请至少输入 4 个有效字符'
        histories = cls.pickaxe_histories(repo_path, search, file_path=file_path, max_commits=max_commits)
        # 兜底：文件路径下用 git log -G（正则）再试一次（对格式化改动更友好）
        if not histories and file_path:
            args = [
                'log', '-G', search, '--pretty=format:%H|%an|%ae|%ad|%s',
                '--date=iso', '-n', str(max_commits), '--', file_path,
            ]
            out, err = cls._run_git(args, cwd=repo_path, timeout=cls.PICKAXE_TIMEOUT)
            if not err and out.strip():
                for line in out.splitlines():
                    parts = line.split('|', 4)
                    if len(parts) < 5:
                        continue
                    commit_hash, author, email, date, subject = parts
                    histories.append({
                        'commit_id': commit_hash,
                        'author': author,
                        'email': email,
                        'date': date,
                        'remark': subject,
                        'branch_name': cls._branch_containing(repo_path, commit_hash),
                        'change_detail': cls._show_snippet(repo_path, commit_hash, file_path, search),
                    })
        return histories, ''

    @classmethod
    def _branch_containing(cls, repo_path, commit_hash):
        out, err = cls._run_git(
            ['branch', '-a', '--contains', commit_hash], cwd=repo_path, timeout=20
        )
        if err or not out.strip():
            return ''
        for line in out.splitlines():
            name = line.strip().lstrip('* ').strip()
            if name.startswith('remotes/'):
                name = name[len('remotes/'):]
            if 'HEAD' in name:
                continue
            return name
        return ''

    @classmethod
    def _show_snippet(cls, repo_path, commit_hash, file_path, search, max_chars=400):
        if not file_path:
            return ''
        out, err = cls._run_git(
            ['show', '{}:{}'.format(commit_hash, file_path)], cwd=repo_path, timeout=30
        )
        if err or not out:
            return ''
        idx = out.find(search)
        if idx < 0:
            return out[:max_chars]
        start = max(0, idx - 80)
        end = min(len(out), idx + len(search) + 80)
        return out[start:end]

    @classmethod
    def analyze_commit_lineage(cls, repo_path, commit_id, max_pickaxe_per_file=None, max_pickaxe_global=None):
        """对单 commit 做 show → 有效行 → pickaxe，返回 lineage 列表。"""
        max_per_file = max_pickaxe_per_file or cls.MAX_PICKAXE_PER_FILE
        max_global = max_pickaxe_global or cls.MAX_PICKAXE_GLOBAL

        is_merge, err = cls.is_merge_commit(repo_path, commit_id)
        if err:
            return [], err
        if is_merge:
            return [], '目标为 merge commit，请指定具体业务 commit（可从 MR diffs?commit_id= 取得）'

        show_text, err = cls.git_show(repo_path, commit_id)
        if err:
            return [], err
        if not show_text.strip():
            return [], 'git show 结果为空'

        files = cls.split_diff_by_file(show_text)
        lineage = []
        global_count = 0
        for file_path, lines in files.items():
            if global_count >= max_global:
                break
            search_rows = cls.collect_search_rows(lines)
            file_count = 0
            for row in search_rows:
                if file_count >= max_per_file or global_count >= max_global:
                    break
                histories = cls.pickaxe_histories(repo_path, row['modified_row'], file_path)
                lineage.append({
                    'file_path': file_path,
                    'modified_row': row['modified_row'],
                    'row_kind': row['row_kind'],
                    'histories': histories,
                })
                file_count += 1
                global_count += 1

        lineage.sort(key=lambda item: len(item.get('modified_row') or ''), reverse=True)
        return lineage, ''

    @classmethod
    def changed_file_summary_from_show(cls, show_text):
        """从 git show 文本生成轻量变更面摘要。"""
        files = cls.split_diff_by_file(show_text)
        result = []
        for path, lines in files.items():
            added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
            deleted = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
            result.append({'path': path, 'file_path': path, 'added': added, 'deleted': deleted})
        return result
