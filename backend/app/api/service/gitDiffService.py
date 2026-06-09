# encoding: UTF-8
import hashlib
import os
import re
import subprocess

from const import BASEDIR


class GitDiffService(object):
    REPO_ROOT = os.path.join(BASEDIR, 'resources', 'precise_repos')
    MAX_SNIPPETS_PER_FILE = 20
    MAX_TEXT_FILE_BYTES = 1024 * 1024
    BINARY_EXTENSIONS = {
        '.7z', '.apk', '.bin', '.bmp', '.class', '.doc', '.docx', '.ear', '.exe', '.gif', '.gz', '.ico',
        '.jar', '.jpeg', '.jpg', '.pdf', '.png', '.rar', '.so', '.tar', '.war', '.webp', '.xls', '.xlsx',
        '.zip'
    }

    @staticmethod
    def _run_git(args, cwd=None, timeout=120):
        completed = subprocess.run(['git'] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=timeout, shell=False)
        stdout = completed.stdout.decode('utf-8', errors='ignore')
        stderr = completed.stderr.decode('utf-8', errors='ignore')
        if completed.returncode != 0:
            return '', stderr or stdout or 'git命令执行失败'
        return stdout, ''

    @staticmethod
    def _repo_dir(repository_url):
        digest = hashlib.md5((repository_url or '').encode('utf-8')).hexdigest()
        return os.path.join(GitDiffService.REPO_ROOT, digest)

    @staticmethod
    def _is_binary_or_large_file(full_path):
        ext = os.path.splitext(full_path)[1].lower()
        if ext in GitDiffService.BINARY_EXTENSIONS:
            return True
        try:
            if os.path.getsize(full_path) > GitDiffService.MAX_TEXT_FILE_BYTES:
                return True
            with open(full_path, 'rb') as handler:
                sample = handler.read(8192)
            return b'\x00' in sample
        except Exception:
            return True

    @staticmethod
    def _clean_json_text(value):
        return (value or '').replace('\x00', '')

    @staticmethod
    def _clean_json_value(value):
        if isinstance(value, dict):
            return {key: GitDiffService._clean_json_value(val) for key, val in value.items()}
        if isinstance(value, list):
            return [GitDiffService._clean_json_value(val) for val in value]
        if isinstance(value, str):
            return GitDiffService._clean_json_text(value)
        return value

    @staticmethod
    def ensure_repo(repository_url, branch_name=None):
        if not repository_url:
            return '', 'repositoryUrl 为必传参数'
        os.makedirs(GitDiffService.REPO_ROOT, exist_ok=True)
        if os.path.isdir(os.path.join(repository_url, '.git')):
            return repository_url, ''
        repo_path = GitDiffService._repo_dir(repository_url)
        if not os.path.isdir(os.path.join(repo_path, '.git')):
            out, err = GitDiffService._run_git(['clone', '--depth', '200', repository_url, repo_path], timeout=300)
            if err:
                return '', err
        GitDiffService._run_git(['fetch', '--all', '--tags'], cwd=repo_path, timeout=180)
        if branch_name:
            GitDiffService._run_git(['checkout', branch_name], cwd=repo_path, timeout=60)
            GitDiffService._run_git(['pull'], cwd=repo_path, timeout=180)
        return repo_path, ''

    @staticmethod
    def parse_diff(repository_url, branch_name, base_commit, target_commit):
        repo_path, err = GitDiffService.ensure_repo(repository_url, branch_name)
        if err:
            return {}, err
        if not base_commit or not target_commit:
            return {}, 'baseCommit 和 targetCommit 为必传参数'
        diff_text, err = GitDiffService._run_git(['diff', '--unified=20', base_commit, target_commit], cwd=repo_path, timeout=180)
        if err:
            return {}, err
        changed_files = GitDiffService.parse_changed_files(diff_text)
        GitDiffService.extract_code_snippets(repo_path, changed_files)
        return GitDiffService._clean_json_value({'changedFiles': changed_files, 'fileCount': len(changed_files)}), ''

    @staticmethod
    def get_code_snippets(repository_url, branch_name, commit, file_path, line_numbers, context=3):
        repo_path, err = GitDiffService.ensure_repo(repository_url, branch_name)
        if err or not file_path:
            return []
        content = ''
        if commit:
            content, _ = GitDiffService._run_git(['show', '{}:{}'.format(commit, file_path)], cwd=repo_path, timeout=60)
        if not content:
            full_path = os.path.join(repo_path, file_path)
            if os.path.isfile(full_path) and not GitDiffService._is_binary_or_large_file(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as handler:
                        content = handler.read()
                except Exception:
                    content = ''
        if not content:
            return []
        lines = content.splitlines()
        ranges = []
        for line_no in sorted(set([int(item) for item in (line_numbers or []) if item])):
            ranges.append([max(1, int(line_no) - int(context)), min(len(lines), int(line_no) + int(context)), int(line_no)])
        merged = []
        for start, end, line_no in ranges:
            if merged and start <= merged[-1]['end'] + 1:
                merged[-1]['end'] = max(merged[-1]['end'], end)
                merged[-1]['line'] = min(merged[-1]['line'], line_no)
            else:
                merged.append({'start': start, 'end': end, 'line': line_no})
        snippets = []
        for item in merged:
            start = item['start']
            end = item['end']
            snippets.append({
                'line': item['line'],
                'start': start,
                'end': end,
                'content': GitDiffService._clean_json_text('\n'.join(lines[start - 1:end]))
            })
        return snippets

    @staticmethod
    def parse_changed_files(diff_text):
        files = []
        current = None
        old_line = 0
        new_line = 0
        for line in (diff_text or '').splitlines():
            if line.startswith('diff --git '):
                if current:
                    current['changedLines'] = sorted(set(current['changedLines']))
                    current['addedLines'] = sorted(set(current['addedLines']))
                    current['deletedLines'] = sorted(set(current['deletedLines']))
                    files.append(current)
                parts = line.split(' ')
                file_path = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith('b/') else parts[-1]
                current = {'filePath': file_path, 'changeType': 'modified', 'changedLines': [],
                           'addedLines': [], 'deletedLines': [], 'codeSnippets': []}
            elif current and line.startswith('new file mode'):
                current['changeType'] = 'added'
            elif current and line.startswith('deleted file mode'):
                current['changeType'] = 'deleted'
            elif current and line.startswith('rename to '):
                current['filePath'] = line.replace('rename to ', '').strip()
                current['changeType'] = 'renamed'
            elif current and line.startswith('@@'):
                match = re.search(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    old_line = int(match.group(1))
                    new_line = int(match.group(2))
            elif current and line.startswith('+') and not line.startswith('+++'):
                current['changedLines'].append(new_line)
                current['addedLines'].append(new_line)
                new_line += 1
            elif current and line.startswith('-') and not line.startswith('---'):
                current['deletedLines'].append(old_line)
                old_line += 1
            elif current:
                old_line += 1
                new_line += 1
        if current:
            current['changedLines'] = sorted(set(current['changedLines']))
            current['addedLines'] = sorted(set(current['addedLines']))
            current['deletedLines'] = sorted(set(current['deletedLines']))
            files.append(current)
        return files

    @staticmethod
    def extract_code_snippets(repo_path, changed_files):
        for item in changed_files:
            full_path = os.path.join(repo_path, item.get('filePath') or '')
            snippets = []
            if os.path.isfile(full_path) and not GitDiffService._is_binary_or_large_file(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as handler:
                        lines = handler.readlines()
                    for line_no in (item.get('changedLines') or [])[:GitDiffService.MAX_SNIPPETS_PER_FILE]:
                        start = max(1, int(line_no) - 3)
                        end = min(len(lines), int(line_no) + 3)
                        snippets.append({'line': line_no, 'start': start, 'end': end,
                                         'content': GitDiffService._clean_json_text(
                                             ''.join(lines[start - 1:end])[:4000])})
                except Exception:
                    snippets = []
            item['codeSnippets'] = snippets
        return changed_files
