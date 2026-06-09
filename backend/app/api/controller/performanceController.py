# encoding: UTF-8
import hashlib
import json
import os
import re
import secrets
import time
from datetime import datetime
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from werkzeug.utils import secure_filename

from common.jenkinsRequest import JenkinsRequest
from const import PERFORMANCE_JENKINS_JOB, PLATFORM_BASE_URL

from .baseCrudController import BaseCrudController
from ..model.performanceModel import (
    PerformanceAiAnalysis,
    PerformanceBaseline,
    PerformanceExecutionConfig,
    PerformanceExecutionRun,
    PerformanceGateResult,
    PerformanceMetric,
    PerformanceMonitorSource,
    PerformanceReport,
    PerformanceScenario,
    PerformanceScript,
    PerformanceScriptVersion,
    PerformanceTestMachine,
)
from ..service.aiService import AIService
from ..service.performanceService import PerformanceService


class PerformanceController(BaseCrudController):
    """性能测试模块接口骨架。"""

    @staticmethod
    def _snake_key(name):
        result = []
        for char in name:
            if char.isupper():
                result.append('_')
                result.append(char.lower())
            else:
                result.append(char)
        return ''.join(result).lstrip('_')

    def _json_body(self):
        if hasattr(self.req_data, 'get_json'):
            return self.req_data.get_json(silent=True) or {}
        return self.req_data or {}

    def _query_args(self):
        if hasattr(self.req_data, 'args'):
            return self.req_data.args
        return self.req_data or {}

    def _page(self):
        req_data = self._query_args()
        return (self._get(req_data, 'pageNo', 'page', default=1),
                self._get(req_data, 'pageSize', 'size', default=20))

    def _collect(self, req_data, fields):
        data = {}
        for field in fields:
            value = self._get(req_data, field, self._snake_key(field))
            if value is not None:
                data[self._snake_key(field)] = value
        return data

    def _list(self, model_cls, filters, order_column=None, soft_delete=True):
        page_no, page_size = self._page()
        items, total = PerformanceService.list_by_filters(self.session, model_cls, filters, page_no, page_size,
                                                          order_column or getattr(model_cls, 'created_time', None),
                                                          soft_delete)
        return {'list': self.serialize_list(items, ['is_delete']), 'total': total}

    def _detail(self, model_cls, obj_id, name='id', soft_delete=True):
        if not obj_id:
            return {}, f'{name} 为必传参数'
        item = PerformanceService.get_by_id(self.session, model_cls, obj_id, soft_delete)
        if not item:
            return {}, '未查询到对应记录！'
        return self.serialize(item, ['is_delete']), ''

    def _create(self, model_cls, required_fields, allowed_fields, defaults=None):
        req_data = self._json_body()
        for field in required_fields:
            if not self._get(req_data, field, self._snake_key(field)):
                return 0, f'{field} 为必传参数'
        add_info = self._collect(req_data, allowed_fields)
        for key, value in (defaults or {}).items():
            add_info.setdefault(key, value)
        return PerformanceService.create(self.session, model_cls, add_info)

    def _update(self, model_cls, obj_id, allowed_fields, name='id', soft_delete=True):
        if not obj_id:
            return 0, f'{name} 为必传参数'
        req_data = self._json_body()
        update_info = self._collect(req_data, allowed_fields)
        if not update_info:
            return int(obj_id), ''
        return PerformanceService.update_by_id(self.session, model_cls, obj_id, update_info, soft_delete)

    def _delete(self, model_cls, obj_id, name='id'):
        if not obj_id:
            return 0, f'{name} 为必传参数'
        return PerformanceService.delete_by_id(self.session, model_cls, obj_id)

    def scenario_list(self):
        req_data = self._query_args()
        filters = []
        keyword = self._get(req_data, 'keyword', 'name')
        status = self._get(req_data, 'status')
        project_id = self._get(req_data, 'projectId', 'project_id')
        product_id = self._get(req_data, 'productId', 'product_id')
        if keyword:
            filters.append(PerformanceScenario.name.like('%{}%'.format(keyword)))
        if status not in (None, ''):
            filters.append(PerformanceScenario.status == int(status))
        if project_id:
            filters.append(PerformanceScenario.project_id == int(project_id))
        if product_id:
            filters.append(PerformanceScenario.product_id == int(product_id))
        return self._list(PerformanceScenario, filters)

    def scenario_create(self):
        allowed_fields = ['name', 'code', 'description', 'projectId', 'productId', 'envCode', 'status', 'ownerId',
                          'createdBy', 'ext']
        defaults = {'code': 'PERF{}'.format(int(time.time() * 1000)), 'status': 1, 'is_delete': 0}
        return self._create(PerformanceScenario, ['name'], allowed_fields, defaults)

    def scenario_detail(self, scenario_id):
        return self._detail(PerformanceScenario, scenario_id, 'scenarioId')

    def scenario_update(self, scenario_id):
        allowed_fields = ['name', 'code', 'description', 'projectId', 'productId', 'envCode', 'status', 'ownerId', 'ext']
        return self._update(PerformanceScenario, scenario_id, allowed_fields, 'scenarioId')

    def scenario_delete(self, scenario_id):
        return self._delete(PerformanceScenario, scenario_id, 'scenarioId')

    def machine_list(self, available_only=False):
        req_data = self._query_args()
        filters = []
        keyword = self._get(req_data, 'keyword', 'name')
        status = self._get(req_data, 'status')
        tool_type = self._get(req_data, 'toolType', 'tool_type')
        if keyword:
            filters.append(PerformanceTestMachine.name.like('%{}%'.format(keyword)))
        if status not in (None, ''):
            filters.append(PerformanceTestMachine.status == int(status))
        if tool_type:
            filters.append(PerformanceTestMachine.supported_tools_json.contains([tool_type]))
        if available_only:
            filters.append(PerformanceTestMachine.status.in_([1, 2]))
        return self._list(PerformanceTestMachine, filters)

    def machine_create(self):
        fields = ['name', 'jenkinsAgentName', 'jenkinsLabel', 'osType', 'host', 'ip', 'supportedToolsJson',
                  'toolVersionsJson', 'workDir', 'maxConcurrentTasks', 'currentRunningTasks', 'cpuCores', 'memoryGb',
                  'status', 'tagsJson', 'envJson', 'remark']
        return self._create(PerformanceTestMachine, ['name', 'jenkinsLabel'], fields, {'status': 1, 'is_delete': 0})

    def machine_update(self, machine_id):
        fields = ['name', 'jenkinsAgentName', 'jenkinsLabel', 'osType', 'host', 'ip', 'supportedToolsJson',
                  'toolVersionsJson', 'workDir', 'maxConcurrentTasks', 'currentRunningTasks', 'cpuCores', 'memoryGb',
                  'status', 'tagsJson', 'envJson', 'remark']
        return self._update(PerformanceTestMachine, machine_id, fields, 'machineId')

    def machine_detail(self, machine_id):
        return self._detail(PerformanceTestMachine, machine_id, 'machineId')

    def machine_delete(self, machine_id):
        return self._delete(PerformanceTestMachine, machine_id, 'machineId')

    def script_list(self):
        req_data = self._query_args()
        filters = []
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        tool_type = self._get(req_data, 'toolType', 'tool_type')
        if scenario_id:
            filters.append(PerformanceScript.scenario_id == int(scenario_id))
        if tool_type:
            filters.append(PerformanceScript.tool_type == tool_type)
        return self._list(PerformanceScript, filters)

    def script_upload(self):
        req_data = self.req_data.form if hasattr(self.req_data, 'form') else self._json_body()
        for field in ['scenarioId', 'name', 'toolType']:
            if not self._get(req_data, field, self._snake_key(field)):
                return 0, f'{field} 为必传参数'
        fields = ['scenarioId', 'name', 'toolType', 'description', 'createdBy', 'ext']
        add_info = self._collect(req_data, fields)
        add_info.update({'status': 1, 'is_delete': 0})
        script_id, err_msg = PerformanceService.create(self.session, PerformanceScript, add_info)
        if err_msg:
            return script_id, err_msg
        upload_file = self.req_data.files.get('file') if hasattr(self.req_data, 'files') else None
        if not upload_file:
            return script_id, ''
        filename = secure_filename(upload_file.filename or '')
        if not filename:
            return script_id, ''
        version = str(int(time.time() * 1000))
        base_dir = os.path.abspath(os.path.join(os.getcwd(), 'resources', 'performance_scripts', str(add_info.get('scenario_id')), str(script_id), version))
        os.makedirs(base_dir, exist_ok=True)
        package_path = os.path.join(base_dir, filename)
        upload_file.save(package_path)
        with open(package_path, 'rb') as file_obj:
            content = file_obj.read()
        version_id, version_err = PerformanceService.create(self.session, PerformanceScriptVersion, {
            'script_id': script_id,
            'version': version,
            'package_path': package_path,
            'main_file': filename,
            'checksum': hashlib.md5(content).hexdigest(),
            'file_size': len(content),
            'generator_type': 'upload',
            'created_by': add_info.get('created_by')
        })
        if version_err:
            return script_id, version_err
        PerformanceService.update_by_id(self.session, PerformanceScript, script_id, {'current_version_id': version_id})
        return {'scriptId': script_id, 'versionId': version_id}, ''

    def _script_file_name(self, tool_type, script_name):
        ext_map = {'jmeter': 'jmx', 'k6': 'js', 'locust': 'py'}
        ext = ext_map.get((tool_type or '').lower(), 'txt')
        safe_name = secure_filename(script_name or 'performance_script') or 'performance_script'
        if not safe_name.lower().endswith('.{}'.format(ext)):
            safe_name = '{}.{}'.format(os.path.splitext(safe_name)[0], ext)
        return safe_name

    def _strip_code_fence(self, content):
        content = (content or '').strip()
        match = re.match(r'^```(?:xml|jmx|javascript|js|python|py)?\s*([\s\S]*?)\s*```$', content, re.IGNORECASE)
        return match.group(1).strip() if match else content

    def _first_plan_item(self, plan_obj, key, default=None):
        value = plan_obj.get(key) if isinstance(plan_obj, dict) else None
        if isinstance(value, list) and value:
            return value[0] or default
        return value or default

    def _safe_int(self, value, default):
        try:
            return int(value)
        except Exception:
            return default

    def _standard_jmeter_jmx(self, plan_obj, prompt_text, script_name):
        thread_group = self._first_plan_item(plan_obj, 'threadGroups', {}) or {}
        request = self._first_plan_item(plan_obj, 'requests', {}) or {}
        threads = self._safe_int(thread_group.get('threads') or thread_group.get('numThreads'), 1)
        ramp_up = self._safe_int(thread_group.get('rampUpSeconds') or thread_group.get('rampUp'), 1)
        duration = self._safe_int(thread_group.get('durationSeconds') or thread_group.get('duration'), 300)
        method = str(request.get('method') or 'GET').upper()
        raw_url = str(request.get('url') or request.get('path') or request.get('endpoint') or '/')
        parsed = urlparse(raw_url if raw_url.startswith(('http://', 'https://')) else 'http://example.com{}'.format(raw_url if raw_url.startswith('/') else '/' + raw_url))
        path = parsed.path or '/'
        if parsed.query:
            path = '{}?{}'.format(path, parsed.query)
        body = request.get('body') or ''
        return '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{test_name}" enabled="true">
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="用户定义的变量" enabled="true"><collectionProp name="Arguments.arguments"/></elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="标准线程组" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="循环控制器" enabled="true"><boolProp name="LoopController.continue_forever">true</boolProp><intProp name="LoopController.loops">-1</intProp></elementProp>
        <stringProp name="ThreadGroup.num_threads">{threads}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">{ramp_up}</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">{duration}</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{sampler_name}" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="用户定义的变量" enabled="true"><collectionProp name="Arguments.arguments"/></elementProp>
          <stringProp name="HTTPSampler.domain">{domain}</stringProp>
          <stringProp name="HTTPSampler.port">{port}</stringProp>
          <stringProp name="HTTPSampler.protocol">{protocol}</stringProp>
          <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
          <stringProp name="HTTPSampler.path">{path}</stringProp>
          <stringProp name="HTTPSampler.method">{method}</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.postBodyRaw">{body}</stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
'''.format(
            test_name=escape(script_name or 'AI生成JMeter脚本'),
            sampler_name=escape(request.get('name') or prompt_text or '接口请求'),
            threads=threads,
            ramp_up=ramp_up,
            duration=duration,
            domain=escape(parsed.hostname or '${HOST}'),
            port=escape(str(parsed.port or '')),
            protocol=escape(parsed.scheme or 'http'),
            path=escape(path),
            method=escape(method),
            body=escape(str(body))
        )

    def _normalize_generated_script_content(self, tool_type, content, plan_obj, prompt_text, script_name):
        content = self._strip_code_fence(content)
        if (tool_type or '').lower() != 'jmeter':
            return content
        lower_content = content.lower()
        if 'kg.apc.' in lower_content or 'ultimatethreadgroup' in lower_content or '<jmetertestplan' not in lower_content:
            return self._standard_jmeter_jmx(plan_obj, prompt_text, script_name)
        return content

    def _save_generated_script_version(self, scenario_id, script_id, tool_type, script_name, content, plan, prompt, created_by=None):
        version = str(int(time.time() * 1000))
        filename = self._script_file_name(tool_type, script_name)
        base_dir = os.path.abspath(os.path.join(os.getcwd(), 'resources', 'performance_scripts', str(scenario_id), str(script_id), version))
        os.makedirs(base_dir, exist_ok=True)
        package_path = os.path.join(base_dir, filename)
        with open(package_path, 'w', encoding='utf-8') as file_obj:
            file_obj.write(content or '')
        content_bytes = (content or '').encode('utf-8')
        version_id, version_err = PerformanceService.create(self.session, PerformanceScriptVersion, {
            'script_id': script_id,
            'version': version,
            'package_path': package_path,
            'main_file': filename,
            'checksum': hashlib.md5(content_bytes).hexdigest(),
            'file_size': len(content_bytes),
            'generator_type': 'ai_generated',
            'ai_prompt': prompt,
            'structure_plan_json': plan if isinstance(plan, (dict, list)) else {},
            'created_by': created_by
        })
        if version_err:
            return 0, version_err
        PerformanceService.update_by_id(self.session, PerformanceScript, script_id, {'current_version_id': version_id})
        return version_id, ''

    def script_generate_plan(self):
        req_data = self._json_body()
        prompt_text = self._get(req_data, 'prompt', default='')
        tool_type = self._get(req_data, 'toolType', 'tool_type', default='jmeter')
        if not prompt_text:
            return {}, 'prompt 为必传参数'
        output_schema = json.dumps({
            'plan': {
                'target': '压测目标',
                'toolType': 'jmeter/k6/locust',
                'threadGroups': [{'name': '线程组', 'threads': 4, 'rampUpSeconds': 60, 'durationSeconds': 300}],
                'requests': [{'name': '接口名称', 'method': 'GET/POST', 'path': '/api/path', 'headers': {}, 'body': ''}],
                'assertions': [],
                'metrics': ['响应时间', '吞吐量', '错误率'],
                'notes': []
            },
            'prompt': '原始需求'
        }, ensure_ascii=False)
        ai_prompt = '''
你是资深性能测试工程师。请根据用户目标生成结构化压测方案，最终只输出 JSON，不要输出 Markdown。
JSON 格式：{output_schema}
工具方式：{tool_type}
用户目标：{prompt_text}
'''.strip().format(output_schema=output_schema, tool_type=tool_type, prompt_text=prompt_text)
        result, err_msg = AIService.request_json(ai_prompt, 'AI生成压测方案')
        if err_msg:
            return {}, err_msg
        if isinstance(result, dict):
            result.setdefault('prompt', prompt_text)
            return result, ''
        return {'plan': result, 'prompt': prompt_text}, ''

    def script_generate_script(self):
        req_data = self._json_body()
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        prompt_text = self._get(req_data, 'prompt', default='')
        tool_type = self._get(req_data, 'toolType', 'tool_type', default='jmeter')
        script_name = self._get(req_data, 'name', default='') or 'AI生成{}脚本'.format(tool_type)
        created_by = self._get(req_data, 'createdBy', 'created_by')
        plan = self._get(req_data, 'plan', default={})
        if not scenario_id:
            return 0, 'scenarioId 为必传参数'
        if not prompt_text and not plan:
            return 0, 'prompt 为必传参数'
        if isinstance(plan, str):
            try:
                plan_obj = json.loads(plan)
            except Exception:
                plan_obj = {'raw': plan}
        else:
            plan_obj = plan or {}
        output_schema = json.dumps({'script_name': '脚本名称', 'main_file': '主文件名', 'description': '脚本说明', 'content': '完整脚本文本'}, ensure_ascii=False)
        ai_prompt = '''
你是资深性能测试脚本工程师。请基于压测目标和方案生成可直接保存的性能测试脚本，最终只输出 JSON，不要输出 Markdown 或代码块。
输出 JSON 格式：{output_schema}
工具方式：{tool_type}
要求：
1. JMeter 必须输出 Apache JMeter 原生 JMX XML，只允许使用 TestPlan、ThreadGroup、LoopController、HTTPSamplerProxy、HeaderManager、ResponseAssertion、ResultCollector 等 JMeter 内置组件。
2. JMeter 禁止使用第三方插件或插件类名，包括 kg.apc.*、UltimateThreadGroup、SteppingThreadGroup、ConcurrencyThreadGroup。
3. k6 输出可执行 JavaScript；Locust 输出 Python locustfile。
4. 信息不足时使用清晰占位变量，不要编造真实密钥。
压测目标：{prompt_text}
结构化方案：{plan_json}
'''.strip().format(output_schema=output_schema, tool_type=tool_type, prompt_text=prompt_text, plan_json=json.dumps(plan_obj, ensure_ascii=False))
        result, err_msg = AIService.request_json(ai_prompt, 'AI生成性能脚本')
        if err_msg:
            return 0, err_msg
        if not isinstance(result, dict):
            return 0, 'AI生成性能脚本格式错误'
        content = result.get('content') or result.get('script') or ''
        if not content:
            return 0, 'AI生成性能脚本缺少 content'
        script_name = result.get('script_name') or result.get('scriptName') or script_name
        content = self._normalize_generated_script_content(tool_type, content, plan_obj, prompt_text, script_name)
        add_info = {
            'scenario_id': int(scenario_id),
            'name': script_name,
            'tool_type': tool_type,
            'description': result.get('description') or 'AI生成性能脚本',
            'status': 1,
            'created_by': created_by,
            'is_delete': 0
        }
        script_id, script_err = PerformanceService.create(self.session, PerformanceScript, add_info)
        if script_err:
            return script_id, script_err
        version_id, version_err = self._save_generated_script_version(int(scenario_id), script_id, tool_type, result.get('main_file') or script_name, content, plan_obj, prompt_text, created_by)
        if version_err:
            return script_id, version_err
        return {'scriptId': script_id, 'versionId': version_id, 'name': script_name, 'toolType': tool_type, 'content': content}, ''

    def script_detail(self, script_id):
        return self._detail(PerformanceScript, script_id, 'scriptId')

    def script_version_list(self, script_id):
        filters = [PerformanceScriptVersion.script_id == int(script_id)]
        return self._list(PerformanceScriptVersion, filters, soft_delete=False)

    def script_version_download(self, version_id):
        item = PerformanceService.get_by_id(self.session, PerformanceScriptVersion, version_id, soft_delete=False)
        if not item:
            return {}, '未查询到对应脚本版本！'
        return {'versionId': item.id, 'packagePath': item.package_path, 'mainFile': item.main_file}, ''

    def execution_config_list(self):
        req_data = self._query_args()
        filters = []
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        if scenario_id:
            filters.append(PerformanceExecutionConfig.scenario_id == int(scenario_id))
        return self._list(PerformanceExecutionConfig, filters)

    def execution_config_create(self):
        fields = ['scenarioId', 'scriptId', 'scriptVersionId', 'name', 'envCode', 'baseUrl', 'concurrentUsers',
                  'durationSeconds', 'rampUpSeconds', 'testMachineId', 'headersJson', 'variablesJson',
                  'parameterFilesJson', 'toolOptionsJson', 'createdBy']
        return self._create(PerformanceExecutionConfig, ['scenarioId', 'name'], fields, {'is_delete': 0})

    def execution_config_update(self, config_id):
        fields = ['scenarioId', 'scriptId', 'scriptVersionId', 'name', 'envCode', 'baseUrl', 'concurrentUsers',
                  'durationSeconds', 'rampUpSeconds', 'testMachineId', 'headersJson', 'variablesJson',
                  'parameterFilesJson', 'toolOptionsJson']
        return self._update(PerformanceExecutionConfig, config_id, fields, 'configId')

    def execution_config_detail(self, config_id):
        return self._detail(PerformanceExecutionConfig, config_id, 'configId')

    def run_create(self):
        req_data = self._json_body()
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        tool_type = self._get(req_data, 'toolType', 'tool_type', default='jmeter')
        if not scenario_id:
            return {}, 'scenarioId 为必传参数'
        if not tool_type:
            return {}, 'toolType 为必传参数'
        script_id = self._get(req_data, 'scriptId', 'script_id')
        script_version_id = self._get(req_data, 'scriptVersionId', 'script_version_id')
        if script_id and not script_version_id:
            script = PerformanceService.get_by_id(self.session, PerformanceScript, script_id)
            if script:
                script_version_id = script.current_version_id
        job_name = self._get(req_data, 'jenkinsJobName', 'jenkins_job_name', default=PERFORMANCE_JENKINS_JOB)
        callback_token = self._get(req_data, 'callbackToken', 'callback_token', default=secrets.token_hex(16))
        ext = self._get(req_data, 'ext', default={}) or {}
        if not isinstance(ext, dict):
            ext = {'raw': ext}
        ext.update({
            'baseUrl': self._get(req_data, 'baseUrl', 'base_url'),
            'concurrentUsers': self._get(req_data, 'concurrentUsers', 'concurrent_users', 'virtualUsers'),
            'durationSeconds': self._get(req_data, 'durationSeconds', 'duration_seconds'),
            'rampUpSeconds': self._get(req_data, 'rampUpSeconds', 'ramp_up_seconds'),
            'gateSummary': self._get(req_data, 'gateSummary', 'gate_summary')
        })
        add_info = {
            'run_no': self._get(req_data, 'runNo', 'run_no', default='PR{}'.format(int(time.time() * 1000))),
            'scenario_id': int(scenario_id),
            'script_id': int(script_id) if script_id else None,
            'script_version_id': int(script_version_id) if script_version_id else None,
            'execution_config_id': self._get(req_data, 'executionConfigId', 'execution_config_id'),
            'tool_type': tool_type,
            'env_code': self._get(req_data, 'envCode', 'env_code'),
            'test_machine_id': self._get(req_data, 'testMachineId', 'test_machine_id', 'machineId'),
            'jenkins_job_name': job_name,
            'status': 1,
            'trigger_type': 'jenkins',
            'trigger_by': self._get(req_data, 'triggerBy', 'trigger_by', 'createdBy'),
            'callback_token': callback_token,
            'ext': ext
        }
        run_id, err_msg = PerformanceService.create(self.session, PerformanceExecutionRun, add_info)
        if err_msg:
            return {}, err_msg
        params = {
            'RUN_ID': run_id,
            'PERFORMANCE_RUN_ID': run_id,
            'SCENARIO_ID': scenario_id,
            'SCRIPT_ID': script_id or '',
            'SCRIPT_VERSION_ID': script_version_id or '',
            'EXECUTION_CONFIG_ID': add_info.get('execution_config_id') or '',
            'TOOL_TYPE': tool_type,
            'ENV_CODE': add_info.get('env_code') or '',
            'TEST_MACHINE_ID': add_info.get('test_machine_id') or '',
            'VIRTUAL_USERS': ext.get('concurrentUsers') or '',
            'DURATION_SECONDS': ext.get('durationSeconds') or '',
            'RAMP_UP_SECONDS': ext.get('rampUpSeconds') or '',
            'CALLBACK_TOKEN': callback_token,
            'PLATFORM_BASE_URL': PLATFORM_BASE_URL
        }
        success, trigger_err, payload = JenkinsRequest().build_with_parameters(params, job_name)
        if not success:
            PerformanceService.update_by_id(self.session, PerformanceExecutionRun, run_id, {'status': 5, 'error_message': trigger_err}, False)
            return {}, trigger_err
        update_info = {
            'status': 2,
            'jenkins_job_name': payload.get('job_name') or job_name,
            'jenkins_queue_id': payload.get('queue_id')
        }
        if payload.get('location'):
            update_info['jenkins_build_url'] = payload.get('location')
        PerformanceService.update_by_id(self.session, PerformanceExecutionRun, run_id, update_info, False)
        item = PerformanceService.get_by_id(self.session, PerformanceExecutionRun, run_id, False)
        return self.serialize(item) if item else {'id': run_id}, ''

    def _jenkins_time(self, millis):
        try:
            return datetime.fromtimestamp(int(millis) / 1000) if millis else None
        except Exception:
            return None

    def _jenkins_status(self, build_info):
        if build_info.get('building'):
            return 3
        result = build_info.get('result')
        if result == 'SUCCESS':
            return 4
        if result == 'ABORTED':
            return 6
        if result in ('FAILURE', 'UNSTABLE', 'NOT_BUILT'):
            return 5
        return 3

    def _artifact_url(self, build_url, artifacts, path):
        if not build_url:
            return None
        for artifact in artifacts or []:
            relative_path = artifact.get('relativePath') or ''
            if relative_path.replace('\\', '/') == path:
                return build_url.rstrip('/') + '/artifact/' + relative_path
        return None

    def _sync_report_from_jenkins(self, run, build_info):
        build_url = build_info.get('url') or run.jenkins_build_url
        artifacts = build_info.get('artifacts') or []
        native_url = self._artifact_url(build_url, artifacts, 'report/index.html')
        raw_url = self._artifact_url(build_url, artifacts, 'result.jtl')
        report = PerformanceService.get_first(self.session, PerformanceReport, [PerformanceReport.run_id == int(run.id)], False)
        report_info = {
            'run_id': int(run.id),
            'scenario_id': int(run.scenario_id),
            'native_report_url': native_url,
            'raw_result_url': raw_url,
            'log_url': build_url.rstrip('/') + '/console' if build_url else None,
            'summary_json': {
                'jenkinsResult': build_info.get('result'),
                'jenkinsBuildNumber': build_info.get('number'),
                'duration': build_info.get('duration')
            }
        }
        if report:
            PerformanceService.update_by_id(self.session, PerformanceReport, report.id, report_info, False)
        else:
            PerformanceService.create(self.session, PerformanceReport, report_info)

    def sync_jenkins_runs(self, limit=50):
        runs, _ = PerformanceService.list_by_filters(
            self.session,
            PerformanceExecutionRun,
            [PerformanceExecutionRun.trigger_type == 'jenkins', PerformanceExecutionRun.status.in_([1, 2, 3])],
            1,
            limit,
            PerformanceExecutionRun.created_time,
            False
        )
        jenkins = JenkinsRequest()
        synced = 0
        for run in runs:
            update_info = {}
            if not run.jenkins_build_number and run.jenkins_queue_id:
                ok, err_msg, queue_item = jenkins.get_queue_item(run.jenkins_queue_id)
                if ok:
                    executable = queue_item.get('executable') or {}
                    if executable.get('number'):
                        update_info.update({
                            'jenkins_build_number': executable.get('number'),
                            'jenkins_build_url': executable.get('url'),
                            'console_url': (executable.get('url') or '').rstrip('/') + '/console',
                            'status': 3
                        })
                    elif queue_item.get('cancelled'):
                        update_info.update({'status': 6, 'error_message': 'Jenkins队列已取消'})
                    else:
                        update_info.update({'status': 2})
                elif err_msg:
                    update_info.update({'error_message': err_msg})
            build_number = update_info.get('jenkins_build_number') or run.jenkins_build_number
            job_name = run.jenkins_job_name or PERFORMANCE_JENKINS_JOB
            if build_number:
                ok, err_msg, build_info = jenkins.get_build_info(job_name, build_number)
                if ok:
                    build_url = build_info.get('url') or run.jenkins_build_url
                    start_time = self._jenkins_time(build_info.get('timestamp'))
                    duration = int((build_info.get('duration') or 0) / 1000) if build_info.get('duration') is not None else None
                    status = self._jenkins_status(build_info)
                    update_info.update({
                        'jenkins_build_number': build_info.get('number') or build_number,
                        'jenkins_build_url': build_url,
                        'console_url': build_url.rstrip('/') + '/console' if build_url else run.console_url,
                        'status': status,
                        'start_time': start_time,
                        'duration_seconds': duration
                    })
                    if status in (4, 5, 6, 7, 8):
                        update_info['end_time'] = self._jenkins_time((build_info.get('timestamp') or 0) + (build_info.get('duration') or 0))
                        if status == 5:
                            update_info['error_message'] = build_info.get('result') or 'Jenkins执行失败'
                        if status == 4:
                            self._sync_report_from_jenkins(run, build_info)
                elif err_msg:
                    update_info.update({'error_message': err_msg})
            if update_info:
                PerformanceService.update_by_id(self.session, PerformanceExecutionRun, run.id, update_info, False)
                synced += 1
        return {'synced': synced}, ''

    def run_list(self):
        self.sync_jenkins_runs()
        req_data = self._query_args()
        filters = []
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        status = self._get(req_data, 'status')
        if scenario_id:
            filters.append(PerformanceExecutionRun.scenario_id == int(scenario_id))
        if status not in (None, ''):
            filters.append(PerformanceExecutionRun.status == int(status))
        result = self._list(PerformanceExecutionRun, filters, soft_delete=False)
        for row in result.get('list') or []:
            report = PerformanceService.get_first(self.session, PerformanceReport, [PerformanceReport.run_id == int(row.get('id'))], False)
            if report:
                row['native_report_url'] = report.native_report_url
                row['raw_result_url'] = report.raw_result_url
                row['log_url'] = report.log_url
        return result

    def run_detail(self, run_id):
        return self._detail(PerformanceExecutionRun, run_id, 'runId', soft_delete=False)

    def run_stop(self, run_id):
        return PerformanceService.update_by_id(self.session, PerformanceExecutionRun, run_id, {'status': 6}, False)

    def run_retry(self, run_id):
        old_run = PerformanceService.get_by_id(self.session, PerformanceExecutionRun, run_id, False)
        if not old_run:
            return 0, '未查询到对应执行记录！'
        add_info = old_run.to_dict()
        add_info.pop('id', None)
        add_info['run_no'] = 'PR{}'.format(int(time.time() * 1000))
        add_info['status'] = 0
        return PerformanceService.create(self.session, PerformanceExecutionRun, add_info)

    def jenkins_callback(self):
        req_data = self._json_body()
        run_id = self._get(req_data, 'runId', 'run_id', 'id')
        if not run_id:
            return 0, 'runId 为必传参数'
        fields = ['jenkinsQueueId', 'jenkinsBuildNumber', 'jenkinsBuildUrl', 'consoleUrl', 'status', 'startTime',
                  'endTime', 'durationSeconds', 'errorMessage', 'ext']
        return self._update(PerformanceExecutionRun, run_id, fields, 'runId', soft_delete=False)

    def report_detail(self, run_id):
        report = PerformanceService.get_first(self.session, PerformanceReport, [PerformanceReport.run_id == int(run_id)], False)
        if not report:
            return {}, '未查询到对应报告！'
        return self.serialize(report), ''

    def report_metrics(self, run_id):
        filters = [PerformanceMetric.run_id == int(run_id)]
        return self._list(PerformanceMetric, filters, soft_delete=False)

    def report_gate_results(self, run_id):
        filters = [PerformanceGateResult.run_id == int(run_id)]
        return self._list(PerformanceGateResult, filters, soft_delete=False)

    def report_native(self, run_id):
        report = PerformanceService.get_first(self.session, PerformanceReport, [PerformanceReport.run_id == int(run_id)], False)
        if not report:
            return {}, '未查询到对应报告！'
        return {'nativeReportUrl': report.native_report_url, 'unifiedReportPath': report.unified_report_path}, ''

    def report_ai_analysis(self, run_id):
        report = PerformanceService.get_first(self.session, PerformanceReport, [PerformanceReport.run_id == int(run_id)], False)
        scenario_id = report.scenario_id if report else self._get(self._json_body(), 'scenarioId', 'scenario_id')
        if not scenario_id:
            return 0, 'scenarioId 为必传参数'
        add_info = {'run_id': int(run_id), 'scenario_id': int(scenario_id), 'analysis_status': 'pending'}
        return PerformanceService.create(self.session, PerformanceAiAnalysis, add_info)

    def baseline_list(self):
        req_data = self._query_args()
        filters = []
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        if scenario_id:
            filters.append(PerformanceBaseline.scenario_id == int(scenario_id))
        return self._list(PerformanceBaseline, filters, soft_delete=False)

    def baseline_from_run(self):
        req_data = self._json_body()
        run_id = self._get(req_data, 'runId', 'run_id')
        scenario_id = self._get(req_data, 'scenarioId', 'scenario_id')
        if not run_id:
            return 0, 'runId 为必传参数'
        if not scenario_id:
            return 0, 'scenarioId 为必传参数'
        fields = ['scriptId', 'scriptVersionId', 'toolType', 'envCode', 'configHash', 'name', 'baselineMetricsJson',
                  'createdBy', 'effectiveTime', 'remark']
        add_info = self._collect(req_data, fields)
        add_info.update({'run_id': int(run_id), 'scenario_id': int(scenario_id), 'status': 1})
        add_info.setdefault('name', 'baseline-{}'.format(run_id))
        add_info.setdefault('tool_type', self._get(req_data, 'toolType', 'tool_type', default='unknown'))
        return PerformanceService.create(self.session, PerformanceBaseline, add_info)

    def baseline_active(self, baseline_id):
        return PerformanceService.update_by_id(self.session, PerformanceBaseline, baseline_id, {'status': 1}, False)

    def baseline_deprecated(self, baseline_id):
        return PerformanceService.update_by_id(self.session, PerformanceBaseline, baseline_id, {'status': 0}, False)

    def monitor_source_list(self):
        req_data = self._query_args()
        filters = []
        source_type = self._get(req_data, 'sourceType', 'source_type')
        if source_type:
            filters.append(PerformanceMonitorSource.source_type == source_type)
        return self._list(PerformanceMonitorSource, filters)

    def monitor_source_create(self):
        fields = ['name', 'sourceType', 'envCode', 'endpoint', 'authConfigJson', 'queryConfigJson', 'enabled']
        return self._create(PerformanceMonitorSource, ['name', 'sourceType'], fields, {'enabled': 1, 'is_delete': 0})

    def monitor_source_detail(self, source_id):
        return self._detail(PerformanceMonitorSource, source_id, 'sourceId')

    def monitor_source_update(self, source_id):
        fields = ['name', 'sourceType', 'envCode', 'endpoint', 'authConfigJson', 'queryConfigJson', 'enabled']
        return self._update(PerformanceMonitorSource, source_id, fields, 'sourceId')

    def monitor_source_delete(self, source_id):
        return self._delete(PerformanceMonitorSource, source_id, 'sourceId')

