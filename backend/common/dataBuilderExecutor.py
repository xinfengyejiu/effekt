# encoding: UTF-8
"""造数器执行器：模板渲染 + steps（sql / set_var / assert）。"""
from __future__ import unicode_literals

import operator
import random
import re
import string

from common.sceneSqlRunner import SceneSqlRunner


class DataBuilderExecutor(object):
    """安全执行造数定义：不跑用户脚本；sql 走 SceneSqlRunner。"""

    OPS = {
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '<': operator.lt,
    }

    def __init__(self, builder_def, env=None, project_id=None):
        self.builder_def = builder_def or {}
        self.steps = self.builder_def.get('steps') or []
        self.env = env or {}
        self.project_id = project_id
        self.context = {'env': self.env, 'param': {}, 'steps': {}}
        self.step_logs = []

    def execute(self, params=None):
        params = params or {}
        self.context['param'] = params
        self.context['steps'] = {}
        self.step_logs = []

        if self.steps:
            for index, step in enumerate(self.steps):
                if not isinstance(step, dict):
                    raise ValueError('steps[{}] 必须是对象'.format(index))
                step_type = (step.get('type') or '').strip().lower()
                step_name = (step.get('name') or 'step_{}'.format(index)).strip()
                if step_type == 'sql':
                    result = self._run_sql_step(step, step_name)
                elif step_type == 'set_var':
                    result = self._run_set_var_step(step, step_name)
                elif step_type == 'assert':
                    result = self._run_assert_step(step, step_name)
                else:
                    raise ValueError('不支持的 step.type={}（仅支持 sql/set_var/assert）'.format(step_type))
                self.context['steps'][step_name] = result
                self.step_logs.append({
                    'name': step_name,
                    'type': step_type,
                    'ok': True,
                    'summary': self._step_summary(step_type, result),
                })
        output = self.builder_def.get('output')
        rendered_output = self._render_template(output) if output is not None else {}
        return {
            'params': params,
            'steps': self.context.get('steps') or {},
            'stepLogs': self.step_logs,
            'output': rendered_output,
        }

    def _run_sql_step(self, step, step_name):
        db_project = step.get('db_project') or step.get('dbProject') or step.get('project') or ''
        env = step.get('env') or step.get('run_env') or step.get('runEnv') or ''
        sql_tpl = step.get('sql') or ''
        sql_text = self._render_template(sql_tpl)
        data, err = SceneSqlRunner.run(
            db_project, env, sql_text, project_id=self.project_id
        )
        if err:
            raise ValueError('[{}] {}'.format(step_name, err))
        extracted = {}
        extract_map = step.get('extract') or {}
        first_row = data.get('firstRow') or {}
        for alias, field in extract_map.items():
            key = str(field).lstrip('$.')
            extracted[alias] = first_row.get(key)
            # 同步写入 param，便于后续模板与 output 使用
            self.context['param'][alias] = extracted[alias]
        result = {
            'rowCount': data.get('rowCount') or 0,
            'rows': data.get('rows') or [],
            'firstRow': first_row,
        }
        result.update(extracted)
        return result

    def _run_set_var_step(self, step, step_name):
        vars_map = step.get('vars') or {}
        bound = {}
        for key, tpl in vars_map.items():
            value = self._render_template(tpl)
            bound[key] = value
            self.context['param'][key] = value
        return bound

    def _run_assert_step(self, step, step_name):
        expr = (step.get('expr') or '').strip()
        if not expr:
            raise ValueError('[{}] assert.expr 为空'.format(step_name))
        matched = re.match(
            r'^([A-Za-z0-9_.]+)\s*(>=|<=|==|!=|>|<)\s*(.+)$',
            expr
        )
        if not matched:
            raise ValueError('[{}] assert.expr 格式不支持：{}'.format(step_name, expr))
        left_path, op, right_raw = matched.group(1), matched.group(2), matched.group(3).strip()
        left = self._resolve_path(left_path)
        right = self._parse_literal(right_raw)
        cmp_fn = self.OPS.get(op)
        try:
            ok = cmp_fn(self._to_number_if_possible(left), self._to_number_if_possible(right))
        except Exception:
            ok = cmp_fn(left, right)
        if not ok:
            raise ValueError('[{}] 断言失败：{} (实际左值={})'.format(step_name, expr, left))
        return {'passed': True, 'expr': expr, 'left': left, 'right': right}

    def _step_summary(self, step_type, result):
        if step_type == 'sql':
            return 'rowCount={}'.format(result.get('rowCount'))
        if step_type == 'set_var':
            return 'vars={}'.format(list((result or {}).keys()))
        if step_type == 'assert':
            return 'passed'
        return ''

    def _render_template(self, obj):
        if isinstance(obj, str):
            return re.sub(r'\{\{([^}]+)\}\}', lambda m: str(self._get_value(m.group(1).strip())), obj)
        if isinstance(obj, dict):
            return {k: self._render_template(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._render_template(item) for item in obj]
        return obj

    def _get_value(self, expr):
        if expr.startswith('random_string(') and expr.endswith(')'):
            length = int(expr[len('random_string('):-1] or 8)
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
        if expr == 'random_phone()':
            return '1{}{}'.format(
                random.choice(['3', '5', '7', '8', '9']),
                ''.join(random.choice(string.digits) for _ in range(9))
            )
        return self._resolve_path(expr)

    def _resolve_path(self, expr):
        current = self.context
        for part in str(expr).split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            if current is None:
                return ''
        return current

    @staticmethod
    def _parse_literal(raw):
        text = raw.strip()
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
        if text.lower() in ('true', 'false'):
            return text.lower() == 'true'
        if text.lower() == 'null':
            return None
        try:
            if '.' in text:
                return float(text)
            return int(text)
        except Exception:
            return text

    @staticmethod
    def _to_number_if_possible(value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, (int, float)):
            return value
        try:
            text = str(value).strip()
            if '.' in text:
                return float(text)
            return int(text)
        except Exception:
            return value
