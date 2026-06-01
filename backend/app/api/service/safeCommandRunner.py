# encoding: UTF-8
import os
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from string import Formatter

from const import AI_DEFAULT_TIMEOUT_SECONDS, AI_DENY_COMMAND_KEYWORDS, AI_EXECUTION_LOG_DIR, AI_MAX_OUTPUT_BYTES, AI_WORKSPACE_ROOTS


class SafeCommandRunner(object):
    @staticmethod
    def _resolve_path(path_value):
        if not path_value:
            return None
        return Path(path_value).resolve()

    @staticmethod
    def validate_workspace(workspace_path, workspace_policy=None):
        workspace = SafeCommandRunner._resolve_path(workspace_path)
        if not workspace:
            return None, 'workspacePath 为必传参数'
        if not workspace.exists() or not workspace.is_dir():
            return None, 'workspacePath 不存在或不是目录'
        allowed_roots = (workspace_policy or {}).get('allowedRoots') or AI_WORKSPACE_ROOTS
        resolved_roots = [SafeCommandRunner._resolve_path(root) for root in allowed_roots if root]
        if not any(root == workspace or root in workspace.parents for root in resolved_roots if root):
            return None, 'workspacePath 不在允许根目录内'
        return workspace, ''

    @staticmethod
    def render_command(command_template, input_payload):
        input_payload = input_payload or {}
        allowed_keys = {field_name for _, field_name, _, _ in Formatter().parse(command_template) if field_name}
        safe_values = {}
        for key in allowed_keys:
            value = input_payload.get(key)
            if value is None:
                return '', f'缺少命令参数：{key}'
            safe_values[key] = str(value)
        try:
            return command_template.format(**safe_values), ''
        except Exception as e:
            return '', f'命令模板渲染失败：{e}'

    @staticmethod
    def validate_command(command_text, entrypoint=None):
        normalized = command_text.strip()
        if not normalized:
            return [], '命令不能为空'
        lower_command = normalized.lower()
        for keyword in AI_DENY_COMMAND_KEYWORDS:
            if keyword.lower() in lower_command:
                return [], f'命令包含禁止关键字：{keyword}'
        try:
            args = shlex.split(normalized, posix=False)
        except ValueError as e:
            return [], f'命令解析失败：{e}'
        if not args:
            return [], '命令不能为空'
        if entrypoint:
            first = Path(args[0].strip('"')).name.lower()
            allowed = Path(str(entrypoint).strip('"')).name.lower()
            if first != allowed:
                return [], '实际命令入口与注册入口不一致'
        return args, ''

    @staticmethod
    def run(command_text, workspace_path, timeout_seconds=None, entrypoint=None, workspace_policy=None, log_prefix='ai_exec'):
        workspace, err_msg = SafeCommandRunner.validate_workspace(workspace_path, workspace_policy)
        if err_msg:
            return {'status': 'failed', 'errorMessage': err_msg}, err_msg
        args, err_msg = SafeCommandRunner.validate_command(command_text, entrypoint)
        if err_msg:
            return {'status': 'failed', 'errorMessage': err_msg}, err_msg

        timeout_seconds = int(timeout_seconds or AI_DEFAULT_TIMEOUT_SECONDS)
        log_dir = Path(AI_EXECUTION_LOG_DIR) / datetime.now().strftime('%Y%m%d')
        log_dir.mkdir(parents=True, exist_ok=True)
        suffix = f'{log_prefix}_{int(time.time() * 1000)}'
        stdout_path = log_dir / f'{suffix}.out.log'
        stderr_path = log_dir / f'{suffix}.err.log'
        start_time = time.time()
        try:
            proc = subprocess.run(
                args,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                shell=False,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout_text = (proc.stdout or '')[:AI_MAX_OUTPUT_BYTES]
            stderr_text = (proc.stderr or '')[:AI_MAX_OUTPUT_BYTES]
            stdout_path.write_text(stdout_text, encoding='utf-8')
            stderr_path.write_text(stderr_text, encoding='utf-8')
            duration = int(time.time() - start_time)
            status = 'success' if proc.returncode == 0 else 'failed'
            result = {
                'status': status,
                'returnCode': proc.returncode,
                'stdoutPath': str(stdout_path),
                'stderrPath': str(stderr_path),
                'stdoutPreview': stdout_text[:2000],
                'stderrPreview': stderr_text[:2000],
                'durationSeconds': duration
            }
            return result, '' if status == 'success' else stderr_text[:500] or '执行失败'
        except subprocess.TimeoutExpired as e:
            duration = int(time.time() - start_time)
            stdout_path.write_text((e.stdout or '')[:AI_MAX_OUTPUT_BYTES] if isinstance(e.stdout, str) else '', encoding='utf-8')
            stderr_path.write_text((e.stderr or '')[:AI_MAX_OUTPUT_BYTES] if isinstance(e.stderr, str) else '执行超时', encoding='utf-8')
            return {
                'status': 'timeout',
                'stdoutPath': str(stdout_path),
                'stderrPath': str(stderr_path),
                'durationSeconds': duration,
                'errorMessage': '执行超时'
            }, '执行超时'
        except FileNotFoundError:
            return {'status': 'failed', 'errorMessage': '命令入口不存在'}, '命令入口不存在'
        except Exception as e:
            return {'status': 'failed', 'errorMessage': str(e)}, str(e)
