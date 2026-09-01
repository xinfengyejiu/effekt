# encoding: UTF-8
import io
from fastapi import APIRouter, Request, Depends, UploadFile
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage, ImmutableMultiDict
from app.core.database import get_db
from app.core.security import require_permission
from app.core.response import api_success, api_failure
from app.api.controller.performanceController import PerformanceController

router = APIRouter(tags=["performance"])


class FlaskRequestAdapter:
    """适配 FastAPI 请求到 Flask 风格请求，用于文件上传控制器"""
    def __init__(self, file_content, filename, content_type, form_data=None):
        file_storage = FileStorage(stream=io.BytesIO(file_content), filename=filename, content_type=content_type)
        self.files = ImmutableMultiDict([('file', file_storage)])
        self.form = ImmutableMultiDict(list((form_data or {}).items()))


def _performance_response(controller, action, id_key='id'):
    """统一处理性能测试控制器的响应"""
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return api_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return api_success(data={id_key: ret})
        return api_success(data=ret)
    finally:
        controller.close_session()


# ============ 场景管理 ============

@router.get("/performance/scenarios")
async def performance_scenario_list(
    request: Request,
    user: dict = Depends(require_permission("performance:scenario:list")),
    db: Session = Depends(get_db),
):
    """场景列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.scenario_list)


@router.post("/performance/scenarios")
async def performance_scenario_create(
    request: Request,
    user: dict = Depends(require_permission("performance:scenario:create")),
    db: Session = Depends(get_db),
):
    """创建场景"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.scenario_create)


@router.get("/performance/scenarios/{scenario_id}")
async def performance_scenario_detail(
    scenario_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:scenario:list")),
    db: Session = Depends(get_db),
):
    """场景详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.scenario_detail(scenario_id))


@router.put("/performance/scenarios/{scenario_id}")
async def performance_scenario_update(
    scenario_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:scenario:update")),
    db: Session = Depends(get_db),
):
    """更新场景"""
    body = await request.json()
    body['id'] = scenario_id
    controller = PerformanceController(body)
    return _performance_response(controller, lambda: controller.scenario_update(scenario_id))


@router.delete("/performance/scenarios/{scenario_id}")
async def performance_scenario_delete(
    scenario_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:scenario:delete")),
    db: Session = Depends(get_db),
):
    """删除场景"""
    controller = PerformanceController({'id': scenario_id})
    return _performance_response(controller, lambda: controller.scenario_delete(scenario_id))


# ============ 测试机器管理 ============

@router.get("/performance/test-machines")
async def performance_machine_list(
    request: Request,
    user: dict = Depends(require_permission("performance:machine:list")),
    db: Session = Depends(get_db),
):
    """测试机器列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.machine_list)


@router.get("/performance/test-machines/available")
async def performance_machine_available(
    request: Request,
    user: dict = Depends(require_permission("performance:machine:list")),
    db: Session = Depends(get_db),
):
    """可用测试机器列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.machine_list(True))


@router.post("/performance/test-machines")
async def performance_machine_create(
    request: Request,
    user: dict = Depends(require_permission("performance:machine:save")),
    db: Session = Depends(get_db),
):
    """创建测试机器"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.machine_create)


@router.get("/performance/test-machines/{machine_id}")
async def performance_machine_detail(
    machine_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:machine:list")),
    db: Session = Depends(get_db),
):
    """测试机器详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.machine_detail(machine_id))


@router.put("/performance/test-machines/{machine_id}")
async def performance_machine_update(
    machine_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:machine:save")),
    db: Session = Depends(get_db),
):
    """更新测试机器"""
    body = await request.json()
    body['id'] = machine_id
    controller = PerformanceController(body)
    return _performance_response(controller, lambda: controller.machine_update(machine_id))


@router.delete("/performance/test-machines/{machine_id}")
async def performance_machine_delete(
    machine_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:machine:delete")),
    db: Session = Depends(get_db),
):
    """删除测试机器"""
    controller = PerformanceController({'id': machine_id})
    return _performance_response(controller, lambda: controller.machine_delete(machine_id))


# ============ 脚本管理 ============

@router.get("/performance/scripts")
async def performance_script_list(
    request: Request,
    user: dict = Depends(require_permission("performance:script:list")),
    db: Session = Depends(get_db),
):
    """脚本列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.script_list)


@router.post("/performance/scripts/upload")
async def performance_script_upload(
    request: Request,
    file: UploadFile,
    user: dict = Depends(require_permission("performance:script:upload")),
    db: Session = Depends(get_db),
):
    """上传脚本"""
    contents = await file.read()
    form_data = dict(request.query_params)
    flask_request = FlaskRequestAdapter(contents, file.filename, file.content_type, form_data)
    controller = PerformanceController(flask_request)
    return _performance_response(controller, controller.script_upload)


@router.post("/performance/scripts/generate-plan")
async def performance_script_generate_plan(
    request: Request,
    user: dict = Depends(require_permission("performance:script:generate")),
    db: Session = Depends(get_db),
):
    """生成压测计划"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.script_generate_plan)


@router.post("/performance/scripts/generate-script")
async def performance_script_generate_script(
    request: Request,
    user: dict = Depends(require_permission("performance:script:generate")),
    db: Session = Depends(get_db),
):
    """生成压测脚本"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.script_generate_script)


@router.get("/performance/scripts/{script_id}")
async def performance_script_detail(
    script_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:script:list")),
    db: Session = Depends(get_db),
):
    """脚本详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.script_detail(script_id))


@router.get("/performance/scripts/{script_id}/versions")
async def performance_script_version_list(
    script_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:script:list")),
    db: Session = Depends(get_db),
):
    """脚本版本列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.script_version_list(script_id))


@router.get("/performance/scripts/versions/{version_id}/download")
async def performance_script_version_download(
    version_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:script:download")),
    db: Session = Depends(get_db),
):
    """下载脚本版本"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.script_version_download(version_id))


# ============ 执行配置 ============

@router.get("/performance/execution-configs")
async def performance_execution_config_list(
    request: Request,
    user: dict = Depends(require_permission("performance:config:list")),
    db: Session = Depends(get_db),
):
    """执行配置列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.execution_config_list)


@router.post("/performance/execution-configs")
async def performance_execution_config_create(
    request: Request,
    user: dict = Depends(require_permission("performance:config:save")),
    db: Session = Depends(get_db),
):
    """创建执行配置"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.execution_config_create)


@router.put("/performance/execution-configs/{config_id}")
async def performance_execution_config_update(
    config_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:config:save")),
    db: Session = Depends(get_db),
):
    """更新执行配置"""
    body = await request.json()
    body['id'] = config_id
    controller = PerformanceController(body)
    return _performance_response(controller, lambda: controller.execution_config_update(config_id))


@router.get("/performance/execution-configs/{config_id}")
async def performance_execution_config_detail(
    config_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:config:list")),
    db: Session = Depends(get_db),
):
    """执行配置详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.execution_config_detail(config_id))


# ============ 执行管理 ============

@router.post("/performance/runs")
async def performance_run_create(
    request: Request,
    user: dict = Depends(require_permission("performance:run:execute")),
    db: Session = Depends(get_db),
):
    """创建执行"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.run_create)


@router.get("/performance/runs")
async def performance_run_list(
    request: Request,
    user: dict = Depends(require_permission("performance:run:list")),
    db: Session = Depends(get_db),
):
    """执行列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.run_list)


@router.post("/performance/runs/sync-jenkins")
async def performance_sync_jenkins_runs(
    request: Request,
    user: dict = Depends(require_permission("performance:run:list")),
    db: Session = Depends(get_db),
):
    """同步 Jenkins 执行记录"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.sync_jenkins_runs)


@router.get("/performance/runs/{run_id}")
async def performance_run_detail(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:run:detail")),
    db: Session = Depends(get_db),
):
    """执行详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.run_detail(run_id))


@router.post("/performance/runs/{run_id}/stop")
async def performance_run_stop(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:run:stop")),
    db: Session = Depends(get_db),
):
    """停止执行"""
    controller = PerformanceController({'id': run_id})
    return _performance_response(controller, lambda: controller.run_stop(run_id))


@router.post("/performance/runs/{run_id}/retry")
async def performance_run_retry(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:run:retry")),
    db: Session = Depends(get_db),
):
    """重试执行"""
    controller = PerformanceController({'id': run_id})
    return _performance_response(controller, lambda: controller.run_retry(run_id))


# ============ Jenkins 回调 ============

@router.post("/performance/jenkins/callback")
async def performance_jenkins_callback(
    request: Request,
):
    """Jenkins 回调接口，无需认证"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.jenkins_callback)


# ============ 报告管理 ============

@router.get("/performance/reports/{run_id}")
async def performance_report_detail(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:report:detail")),
    db: Session = Depends(get_db),
):
    """报告详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.report_detail(run_id))


@router.get("/performance/reports/{run_id}/metrics")
async def performance_report_metrics(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:report:detail")),
    db: Session = Depends(get_db),
):
    """报告指标"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.report_metrics(run_id))


@router.get("/performance/reports/{run_id}/gate-results")
async def performance_report_gate_results(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:report:detail")),
    db: Session = Depends(get_db),
):
    """报告质量门禁结果"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.report_gate_results(run_id))


@router.get("/performance/reports/{run_id}/native")
async def performance_report_native(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:report:detail")),
    db: Session = Depends(get_db),
):
    """报告原始数据"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.report_native(run_id))


@router.post("/performance/reports/{run_id}/ai-analysis")
async def performance_report_ai_analysis(
    run_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:report:ai")),
    db: Session = Depends(get_db),
):
    """报告 AI 分析"""
    body = await request.json()
    body['run_id'] = run_id
    controller = PerformanceController(body)
    return _performance_response(controller, lambda: controller.report_ai_analysis(run_id))


# ============ 基线管理 ============

@router.get("/performance/baselines")
async def performance_baseline_list(
    request: Request,
    user: dict = Depends(require_permission("performance:baseline:list")),
    db: Session = Depends(get_db),
):
    """基线列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.baseline_list)


@router.post("/performance/baselines/from-run")
async def performance_baseline_from_run(
    request: Request,
    user: dict = Depends(require_permission("performance:baseline:save")),
    db: Session = Depends(get_db),
):
    """从执行创建基线"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.baseline_from_run)


@router.put("/performance/baselines/{baseline_id}/active")
async def performance_baseline_active(
    baseline_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:baseline:save")),
    db: Session = Depends(get_db),
):
    """激活基线"""
    controller = PerformanceController({'id': baseline_id})
    return _performance_response(controller, lambda: controller.baseline_active(baseline_id))


@router.put("/performance/baselines/{baseline_id}/deprecated")
async def performance_baseline_deprecated(
    baseline_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:baseline:save")),
    db: Session = Depends(get_db),
):
    """废弃基线"""
    controller = PerformanceController({'id': baseline_id})
    return _performance_response(controller, lambda: controller.baseline_deprecated(baseline_id))


# ============ 监控源管理 ============

@router.get("/performance/monitor-sources")
async def performance_monitor_source_list(
    request: Request,
    user: dict = Depends(require_permission("performance:monitor:list")),
    db: Session = Depends(get_db),
):
    """监控源列表"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, controller.monitor_source_list)


@router.post("/performance/monitor-sources")
async def performance_monitor_source_create(
    request: Request,
    user: dict = Depends(require_permission("performance:monitor:save")),
    db: Session = Depends(get_db),
):
    """创建监控源"""
    body = await request.json()
    controller = PerformanceController(body)
    return _performance_response(controller, controller.monitor_source_create)


@router.get("/performance/monitor-sources/{source_id}")
async def performance_monitor_source_detail(
    source_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:monitor:list")),
    db: Session = Depends(get_db),
):
    """监控源详情"""
    controller = PerformanceController(dict(request.query_params))
    return _performance_response(controller, lambda: controller.monitor_source_detail(source_id))


@router.put("/performance/monitor-sources/{source_id}")
async def performance_monitor_source_update(
    source_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:monitor:save")),
    db: Session = Depends(get_db),
):
    """更新监控源"""
    body = await request.json()
    body['id'] = source_id
    controller = PerformanceController(body)
    return _performance_response(controller, lambda: controller.monitor_source_update(source_id))


@router.delete("/performance/monitor-sources/{source_id}")
async def performance_monitor_source_delete(
    source_id: int,
    request: Request,
    user: dict = Depends(require_permission("performance:monitor:delete")),
    db: Session = Depends(get_db),
):
    """删除监控源"""
    controller = PerformanceController({'id': source_id})
    return _performance_response(controller, lambda: controller.monitor_source_delete(source_id))
