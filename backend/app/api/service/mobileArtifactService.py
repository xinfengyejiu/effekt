# encoding: UTF-8
import hashlib
import html
import mimetypes
import os
import re
from pathlib import Path
from string import Template

from app.core.config import MOBILE_AUTOMATION_ARTIFACT_ROOT
from app.api.dao.mobileAutomationDao import MobileAutomationDao


# 兼容旧路径模式（无项目名前缀）
_OLD_EXECUTION_NO_PATTERN = re.compile(r'^MA\d{17}$')
# 路径分隔符，用于区分新旧结构
_PATH_SEPARATOR = '/'


class MobileArtifactService(object):

    @staticmethod
    def _sanitize_project_name(project_name):
        """将项目名转为安全的目录名：去除非法字符，限制长度。"""
        if not project_name:
            return None
        name = re.sub(r'[^\w\u4e00-\u9fff\-.]', '_', project_name.strip())
        if not name:
            name = 'unknown'
        return name[:64]

    @staticmethod
    def execution_root(execution_no, project_name=None):
        """获取执行产物根目录。

        Args:
            execution_no: 执行编号，如 MA20260730143025123
            project_name: 项目名称（可选）。提供后按 项目名/执行号/ 组织目录；
                          不提供时回退到旧版扁平结构，兼容历史数据。
        """
        root = Path(MOBILE_AUTOMATION_ARTIFACT_ROOT).resolve()
        safe_name = MobileArtifactService._sanitize_project_name(project_name)
        if safe_name:
            path = (root / safe_name / execution_no).resolve()
        else:
            path = (root / execution_no).resolve()
        if root not in path.parents and path != root:
            raise ValueError('非法产物目录')
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def safe_relative_path(path):
        root = Path(MOBILE_AUTOMATION_ARTIFACT_ROOT).resolve()
        resolved = Path(path).resolve()
        if root not in resolved.parents:
            raise ValueError('产物路径不在受控目录内')
        return resolved.relative_to(root).as_posix()

    @staticmethod
    def resolve_relative_path(relative_path):
        root = Path(MOBILE_AUTOMATION_ARTIFACT_ROOT).resolve()
        resolved = (root / relative_path).resolve()
        if root not in resolved.parents or not resolved.is_file():
            raise ValueError('产物不存在或路径非法')
        return resolved

    @staticmethod
    def resolve_execution_root_from_execution_no(execution_no):
        """仅凭 execution_no 定位执行产物目录，兼容新旧两种目录结构。

        新结构：{ARTIFACT_ROOT}/{project_name}/{execution_no}/
        旧结构：{ARTIFACT_ROOT}/{execution_no}/
        """
        root = Path(MOBILE_AUTOMATION_ARTIFACT_ROOT).resolve()

        # 优先查找新结构（按项目名子目录）
        if root.is_dir():
            for project_dir in root.iterdir():
                if project_dir.is_dir():
                    execution_dir = project_dir / execution_no
                    if execution_dir.is_dir():
                        return execution_dir

        # 回退旧结构
        legacy_dir = root / execution_no
        if legacy_dir.is_dir():
            return legacy_dir

        # 都不存在则返回默认位置（由调用方决定是否创建）
        return root / execution_no

    @staticmethod
    def read_text_auto(path, max_chars=None):
        """读取控制台日志：兼容 Windows 下 pytest 的 GBK 输出与 UTF-8 混写。"""
        raw = Path(path).read_bytes()
        chunks = []
        for line in raw.splitlines(True):
            decoded = None
            for encoding in ('utf-8', 'gbk', 'cp936'):
                try:
                    decoded = line.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if decoded is None:
                decoded = line.decode('utf-8', errors='replace')
            chunks.append(decoded)
        text = ''.join(chunks)
        if max_chars is not None and max_chars > 0 and len(text) > max_chars:
            return text[-max_chars:]
        return text

    @staticmethod
    def generate_html_report(execution, case_items, console_log_path=None):
        status_labels = {0: '待触发', 3: '执行中', 4: '成功', 5: '失败', 6: '已取消', 7: '触发失败'}
        case_status_labels = {0: '待执行', 1: '执行中', 2: '通过', 3: '失败', 4: '阻塞', 5: '跳过', 6: '未找到', 7: '已取消'}
        ext = execution.ext or {}
        execution_root = MobileArtifactService.execution_root(
            execution.execution_no, ext.get('project_name')
        )
        report_path = execution_root / 'report.html'
        console_log = ''
        if console_log_path and Path(console_log_path).is_file():
            console_log = MobileArtifactService.read_text_auto(console_log_path, max_chars=50000)
        case_rows = ''.join(
            '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td><span class="status status-{3}">{4}</span></td><td>{5}</td></tr>'.format(
                item.run_order or '-', html.escape(str(item.case_key or '-')), html.escape(str(item.case_title or '-')),
                item.status, case_status_labels.get(item.status, str(item.status)),
                html.escape(str(item.error_message or item.result_message or '-'))
            ) for item in case_items
        ) or '<tr><td colspan="5" class="empty">暂无用例执行数据</td></tr>'
        def value(item):
            return html.escape(str(item or '-'))
        status = status_labels.get(execution.status, str(execution.status))
        report_html = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>移动自动化执行报告</title><style>
body{margin:0;background:#f6f8fb;color:#172033;font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}.wrap{max-width:1120px;margin:32px auto;padding:0 24px}.hero{background:#172b4d;color:#fff;padding:28px 32px;border-radius:12px}.hero h1{margin:0 0 8px;font-size:24px}.meta{opacity:.78}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}.metric,.panel{background:#fff;border:1px solid #e7ebf2;border-radius:10px}.metric{padding:16px}.metric strong{display:block;font-size:22px}.panel{margin-top:20px;overflow:hidden}.panel h2{font-size:16px;margin:0;padding:14px 18px;border-bottom:1px solid #e7ebf2}.details{display:grid;grid-template-columns:repeat(2,1fr);padding:8px 18px}.details div{padding:9px 0;border-bottom:1px dashed #e7ebf2}.details span{color:#6b778c;display:inline-block;min-width:88px}table{width:100%;border-collapse:collapse}th,td{padding:11px 14px;border-bottom:1px solid #edf0f5;text-align:left;vertical-align:top}th{background:#f8fafc;color:#526071}.status{padding:2px 8px;border-radius:999px;font-size:12px}.status-2,.status-4{background:#e8f7ee;color:#16824a}.status-3,.status-5,.status-7{background:#fff0f0;color:#d64545}.status-0,.status-1,.status-6{background:#eef3fb;color:#4d6f9e}pre{margin:0;padding:16px 18px;background:#111827;color:#d6e2f0;white-space:pre-wrap;word-break:break-word;max-height:460px;overflow:auto}.empty{text-align:center;color:#8a94a6;padding:24px}@media(max-width:700px){.grid{grid-template-columns:1fr}.details{grid-template-columns:1fr}.wrap{padding:0 12px;margin:12px auto}.hero{border-radius:8px}}</style></head><body><main class="wrap"><header class="hero"><h1>移动自动化执行报告</h1><div class="meta">执行单号：{execution_no}　生成时间：{created_time}</div></header><section class="grid"><div class="metric"><span>执行状态</span><strong>{status}</strong></div><div class="metric"><span>通过 / 失败</span><strong>{passed} / {failed}</strong></div><div class="metric"><span>总用例数</span><strong>{total}</strong></div></section><section class="panel"><h2>执行配置</h2><div class="details"><div><span>环境</span>{env}</div><div><span>设备</span>{device}</div><div><span>应用</span>{app}</div><div><span>脚本</span>{script}</div><div><span>开始时间</span>{start}</div><div><span>结束时间</span>{end}</div></div></section><section class="panel"><h2>用例结果</h2><table><thead><tr><th>#</th><th>用例编号</th><th>用例标题</th><th>状态</th><th>结果摘要</th></tr></thead><tbody>{case_rows}</tbody></table></section><section class="panel"><h2>控制台日志</h2><pre>{console_log}</pre></section></main></body></html>'''
        style_end = report_html.index('</style>')
        report_html = report_html[:style_end].replace('{', '{{').replace('}', '}}') + report_html[style_end:]
        report_path.write_text(report_html.format(
            execution_no=value(execution.execution_no), created_time=value(execution.created_time), status=value(status),
            passed=value(execution.passed_count), failed=value(execution.failed_count), total=value(execution.total_count),
            env=value(execution.env_code), device=value(ext.get('device_serial')), app=value(ext.get('app_package')),
            script=value(ext.get('script_selector')), start=value(execution.start_time), end=value(execution.end_time),
            case_rows=case_rows, console_log=html.escape(console_log or '暂无控制台日志')
        ), encoding='utf-8')
        return report_path

    @staticmethod
    def register_file(session, execution_id, file_path, artifact_type, execution_case_id=None, step_id=None):
        path = Path(file_path)
        if not path.is_file():
            return None
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        return MobileAutomationDao.create_artifact(session, {
            'execution_id': int(execution_id),
            'execution_case_id': int(execution_case_id) if execution_case_id else None,
            'step_id': int(step_id) if step_id else None,
            'artifact_type': artifact_type,
            'relative_path': MobileArtifactService.safe_relative_path(path),
            'content_type': mimetypes.guess_type(path.name)[0] or 'application/octet-stream',
            'size_bytes': path.stat().st_size,
            'checksum': checksum,
        })
