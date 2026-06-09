# encoding: UTF-8
from sqlalchemy.exc import OperationalError
from flask import Blueprint, request
import traceback

from common.apiResponse import ApiResponse
from logger import logger
from .utils.authMiddleware import login_required, permission_required, should_skip_auth
from .controller.updateSqlProjectController import UpdateSqlProjectController
from .controller.projectController import ProjectController
from .controller.caseController import CaseController
from .controller.planController import PlanController
from .controller.reportController import ReportController
from .controller.dataBuilderController import DataBuilderController
from .controller.productController import ProductController
from .controller.rbacController import RbacController
from .controller.userController import UserController
from .controller.bugController import BugController, BugUploadController
from .controller.projectHookController import ProjectHookController
from .controller.automationController import AutomationController
from .controller.skillController import SkillController
from .controller.documentSourceController import DocumentSourceController
from .controller.mockController import MockController
from .controller.aiAgentController import AiAgentController
from .controller.aiToolController import AiToolController
from .controller.aiMcpController import AiMcpController
from .controller.aiFlowController import AiFlowController
from .controller.aiTaskController import AiTaskController
from .controller.aiReportController import AiReportController
from .controller.knowledgeController import KnowledgeController
from .controller.performanceController import PerformanceController
from .controller.preciseTestController import PreciseTestController

api = Blueprint('api', __name__)


@api.before_request
def api_before_request():
    if request.method == 'OPTIONS' or should_skip_auth(request.path):
        return None
    token = request.headers.get('accessToken') or request.headers.get('accesstoken') or request.headers.get('Authorization')
    if not token:
        return ApiResponse.build_failure(40001, msg='缺少token！')
    return None


@api.route('/list', methods=['GET'])
@login_required
@permission_required('sql_project:list')
def get_list():
    request_args = request.args
    controller = UpdateSqlProjectController(request_args)
    try:
        ret = controller.query_smart_manage_sql_data()
        return ApiResponse.build_success(20000, data=ret)
    except OperationalError:
        return ApiResponse.build_failure(40008, msg='数据库连接超时，请稍后重试！')
    except Exception as e:
        from logger import logger
        logger.exception(f'get_list failed, args={dict(request_args)}, err={e}')
        return ApiResponse.build_failure(40008, msg=str(e))


@api.route('/create', methods=['POST'])
@login_required
@permission_required('sql_project:create')
def create_sql_project():
    req_json = request.get_json() or {}
    controller = UpdateSqlProjectController(req_json)
    create_id, err_msg = controller.create_sql_project()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'sqlId': create_id})


@api.route('/detail', methods=['GET'])
@login_required
@permission_required('sql_project:detail')
def get_sql_project_detail():
    request_args = request.args
    controller = UpdateSqlProjectController(request_args)
    ret, err_msg = controller.get_sql_project_detail()
    if err_msg:
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/delete', methods=['POST'])
@login_required
@permission_required('sql_project:delete')
def delete_sql_project():
    req_json = request.get_json() or {}
    controller = UpdateSqlProjectController(req_json)
    delete_id, err_msg = controller.delete_sql_project()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'sqlId': delete_id})


@api.route('/execute', methods=['POST'])
@login_required
@permission_required('sql_project:execute')
def execute_sql_project():
    """按 SQL 配置中的项目和环境执行目标 SQL。"""
    req_json = request.get_json() or {}
    controller = UpdateSqlProjectController(req_json)
    ret, err_msg = controller.execute_sql_project()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/project/list', methods=['GET'])
@login_required
@permission_required('project:list')
def project_list():
    controller = ProjectController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.project_list())
    finally:
        controller.close_session()



@api.route('/project/detail', methods=['GET'])
@login_required
@permission_required('project:detail')
def project_detail():
    controller = ProjectController(request.args)
    try:
        ret, err_msg = controller.project_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/project/create', methods=['POST'])
@login_required
@permission_required('project:create')
def project_create():
    controller = ProjectController(request.get_json() or {})
    try:
        create_id, err_msg = controller.project_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/project/update', methods=['POST'])
@login_required
@permission_required('project:update')
def project_update():
    controller = ProjectController(request.get_json() or {})
    try:
        update_id, err_msg = controller.project_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/project/delete', methods=['POST'])
@login_required
@permission_required('project:delete')
def project_delete():
    controller = ProjectController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.project_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/environment/list', methods=['GET'])
@login_required
@permission_required('environment:list')
def environment_list():
    """分页查询环境配置列表。"""
    controller = ProjectController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.environment_list())
    finally:
        controller.close_session()


@api.route('/environment/create', methods=['POST'])
@login_required
@permission_required('environment:create')
def environment_create():
    controller = ProjectController(request.get_json() or {})
    try:
        create_id, err_msg = controller.environment_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/environment/update', methods=['POST'])
@login_required
@permission_required('environment:update')
def environment_update():
    controller = ProjectController(request.get_json() or {})
    try:
        update_id, err_msg = controller.environment_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/environment/delete', methods=['POST'])
@login_required
@permission_required('environment:delete')
def environment_delete():
    controller = ProjectController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.environment_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/project/member/list', methods=['GET'])
@login_required
@permission_required('project_member:list')
def project_member_list():
    controller = ProjectController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.member_list())
    finally:
        controller.close_session()


@api.route('/project/member/create', methods=['POST'])
@login_required
@permission_required('project_member:create')
def project_member_create():
    """批量添加项目成员。"""
    controller = ProjectController(request.get_json() or {})
    try:
        result, err_msg = controller.member_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': result})
    finally:
        controller.close_session()


@api.route('/project/hook/list', methods=['GET'])
@login_required
@permission_required('project_hook:list')
def project_hook_list():
    controller = ProjectHookController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.hook_list())
    finally:
        controller.close_session()


@api.route('/project/hook/detail', methods=['GET'])
@login_required
@permission_required('project_hook:detail')
def project_hook_detail():
    controller = ProjectHookController(request.args)
    try:
        ret, err_msg = controller.hook_detail()
        if err_msg:
            return ApiResponse.build_failure(40016, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/project/hook/create', methods=['POST'])
@login_required
@permission_required('project_hook:create')
def project_hook_create():
    controller = ProjectHookController(request.get_json() or {})
    try:
        hook_id, err_msg = controller.hook_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': hook_id})
    finally:
        controller.close_session()


@api.route('/project/hook/update', methods=['POST'])
@login_required
@permission_required('project_hook:update')
def project_hook_update():
    controller = ProjectHookController(request.get_json() or {})
    try:
        hook_id, err_msg = controller.hook_update()
        if err_msg:
            return ApiResponse.build_failure(40010, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': hook_id})
    finally:
        controller.close_session()


@api.route('/project/hook/delete', methods=['POST'])
@login_required
@permission_required('project_hook:delete')
def project_hook_delete():
    controller = ProjectHookController(request.get_json() or {})
    try:
        hook_id, err_msg = controller.hook_delete()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': hook_id})
    finally:
        controller.close_session()


@api.route('/project/hook/send', methods=['POST'])
@login_required
@permission_required('project_hook:send')
def project_hook_send():
    controller = ProjectHookController(request.get_json() or {})
    try:
        success, result = controller.hook_send()
        if not success:
            if isinstance(result, str):
                return ApiResponse.build_failure(40012, msg=result)
            elif isinstance(result, list) and result:
                errors = [r.get('error') for r in result if not r.get('success') and r.get('error')]
                error_msg = errors[0] if errors else '发送失败'
                return ApiResponse.build_failure(40012, msg=error_msg, data=result)
            else:
                return ApiResponse.build_failure(40012, msg='发送失败', data=result)
        return ApiResponse.build_success(20000, data=result)
    finally:
        controller.close_session()


@api.route('/product/list', methods=['GET'])
@login_required
@permission_required('product:list')
def product_list():
    controller = ProductController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.product_list())
    finally:
        controller.close_session()


@api.route('/product/detail', methods=['GET'])
@login_required
@permission_required('product:detail')
def product_detail():
    controller = ProductController(request.args)
    try:
        ret, err_msg = controller.product_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/product/create', methods=['POST'])
@login_required
@permission_required('product:create')
def product_create():
    controller = ProductController(request.get_json() or {})
    try:
        create_id, err_msg = controller.product_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/product/update', methods=['POST'])
@login_required
@permission_required('product:update')
def product_update():
    controller = ProductController(request.get_json() or {})
    try:
        update_id, err_msg = controller.product_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/product/delete', methods=['POST'])
@login_required
@permission_required('product:delete')
def product_delete():
    controller = ProductController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.product_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/module/tree', methods=['GET'])
@login_required
@permission_required('module:list')
def module_tree():
    try:
        return ApiResponse.build_success(20000, data=CaseController(request.args).module_list())
    except Exception as e:
        logger.error(f'module_tree异常：{str(e)}, 请求参数：{dict(request.args)}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40009, msg=f'查询失败：{str(e)[:100]}')


@api.route('/module/create', methods=['POST'])
@login_required
@permission_required('module:create')
def module_create():
    try:
        create_id, err_msg = CaseController(request.get_json() or {}).module_create()
        if err_msg:
            logger.warning(f'module_create失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    except Exception as e:
        logger.error(f'module_create异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40009, msg=f'创建失败：{str(e)[:100]}')


@api.route('/module/update', methods=['POST'])
@login_required
@permission_required('module:update')
def module_update():
    try:
        update_id, err_msg = CaseController(request.get_json() or {}).module_update()
        if err_msg:
            logger.warning(f'module_update失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    except Exception as e:
        logger.error(f'module_update异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40012, msg=f'更新失败：{str(e)[:100]}')


@api.route('/module/delete', methods=['POST'])
@login_required
@permission_required('module:delete')
def module_delete():
    try:
        delete_id, err_msg = CaseController(request.get_json() or {}).module_delete()
        if err_msg:
            logger.warning(f'module_delete失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    except Exception as e:
        logger.error(f'module_delete异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40012, msg=f'删除失败：{str(e)[:100]}')


@api.route('/case/list', methods=['GET'])
@login_required
@permission_required('case:list')
def case_list():
    try:
        controller = CaseController(request.args)
        return ApiResponse.build_success(20000, data=controller.case_list())
    except Exception as e:
        logger.error(f'case_list异常：{str(e)}, 请求参数：{dict(request.args)}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40009, msg=f'查询失败：{str(e)[:100]}')


@api.route('/case/detail', methods=['GET'])
@login_required
@permission_required('case:detail')
def case_detail():
    ret, err_msg = CaseController(request.args).case_detail()
    if err_msg:
        logger.warning(f'case_detail失败：{err_msg}, 请求参数：{dict(request.args)}')
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/case/create', methods=['POST'])
@login_required
@permission_required('case:create')
def case_create():
    try:
        create_id, err_msg = CaseController(request.get_json() or {}).case_create()
        if err_msg:
            logger.warning(f'case_create失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    except Exception as e:
        logger.error(f'case_create异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40009, msg=f'创建失败：{str(e)[:100]}')


@api.route('/case/update', methods=['POST'])
@login_required
@permission_required('case:update')
def case_update():
    try:
        update_id, err_msg = CaseController(request.get_json() or {}).case_update()
        if err_msg:
            logger.warning(f'case_update失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    except Exception as e:
        logger.error(f'case_update异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40012, msg=f'更新失败：{str(e)[:100]}')


@api.route('/case/delete', methods=['POST'])
@login_required
@permission_required('case:delete')
def case_delete():
    try:
        ret, err_msg = CaseController(request.get_json() or {}).case_delete()
        if err_msg:
            logger.warning(f'case_delete失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    except Exception as e:
        logger.error(f'case_delete异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40012, msg=f'删除失败：{str(e)[:100]}')


@api.route('/case/restore', methods=['POST'])
@login_required
@permission_required('case:update')
def case_restore():
    try:
        ret, err_msg = CaseController(request.get_json() or {}).case_restore()
        if err_msg:
            logger.warning(f'case_restore失败：{err_msg}, 请求参数：{request.get_json()}')
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    except Exception as e:
        logger.error(f'case_restore异常：{str(e)}, 请求参数：{request.get_json()}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40012, msg=f'恢复失败：{str(e)[:100]}')


@api.route('/case/import', methods=['POST'])
@login_required
@permission_required('case:create')
def case_import():
    import os
    from flask import send_file
    
    try:
        if 'file' not in request.files:
            logger.warning('case_import失败：请上传文件')
            return ApiResponse.build_failure(40009, msg='请上传文件')
        
        file = request.files['file']
        if file.filename == '':
            logger.warning('case_import失败：请选择文件')
            return ApiResponse.build_failure(40009, msg='请选择文件')
        
        project_id = request.form.get('projectId')
        if not project_id:
            logger.warning('case_import失败：projectId 为必传参数')
            return ApiResponse.build_failure(40009, msg='projectId 为必传参数')
        
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        attachment_dir = os.path.join(root_dir, 'attachment')
        # 确保 attachment 目录存在
        os.makedirs(attachment_dir, exist_ok=True)
        temp_path = os.path.join(attachment_dir, 'temp_import.xlsx')
        file.save(temp_path)
        
        controller = CaseController({})
        try:
            success_count, err_msg = controller.case_import(temp_path, project_id)
            if err_msg and ('失败' in err_msg or success_count == 0):
                logger.warning(f'case_import失败：{err_msg}, projectId={project_id}')
                return ApiResponse.build_failure(40009, msg=err_msg)
            logger.info(f'case_import成功：成功{success_count}条, projectId={project_id}')
            return ApiResponse.build_success(20000, data={'successCount': success_count, 'message': err_msg})
        finally:
            controller.close_session()
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        logger.error(f'case_import异常：{str(e)}, projectId={request.form.get("projectId")}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40009, msg=f'导入失败：{str(e)[:100]}')


@api.route('/import/template', methods=['GET'])
@login_required
def import_template():
    import os
    from flask import send_file
    
    template_path = CaseController.get_template_path()
    if not os.path.exists(template_path):
        return ApiResponse.build_failure(40011, msg='模板文件不存在')
    
    return send_file(template_path, as_attachment=True, attachment_filename='测试用例模版.xlsx')


@api.route('/case/snapshot/create', methods=['POST'])
@login_required
@permission_required('case_snapshot:create')
def case_snapshot_create():
    create_id, err_msg = CaseController(request.get_json() or {}).snapshot_create()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': create_id})


@api.route('/case/snapshot/list', methods=['GET'])
@login_required
@permission_required('case_snapshot:list')
def case_snapshot_list():
    return ApiResponse.build_success(20000, data=CaseController(request.args).snapshot_list())


@api.route('/case/review/create', methods=['POST'])
@login_required
@permission_required('case_review:create')
def case_review_create():
    create_id, err_msg = CaseController(request.get_json() or {}).review_create()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': create_id})


@api.route('/case/review/update', methods=['POST'])
@login_required
@permission_required('case_review:update')
def case_review_update():
    update_id, err_msg = CaseController(request.get_json() or {}).review_update()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': update_id})


@api.route('/case/review/list', methods=['GET'])
@login_required
@permission_required('case_review:list')
def case_review_list():
    return ApiResponse.build_success(20000, data=CaseController(request.args).review_list())


@api.route('/plan/list', methods=['GET'])
@login_required
@permission_required('plan:list')
def plan_list():
    return ApiResponse.build_success(20000, data=PlanController(request.args).plan_list())


@api.route('/plan/detail', methods=['GET'])
@login_required
@permission_required('plan:detail')
def plan_detail():
    ret, err_msg = PlanController(request.args).plan_detail()
    if err_msg:
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/plan/create', methods=['POST'])
@login_required
@permission_required('plan:create')
def plan_create():
    create_id, err_msg = PlanController(request.get_json() or {}).plan_create()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': create_id})


@api.route('/plan/update', methods=['POST'])
@login_required
@permission_required('plan:update')
def plan_update():
    update_id, err_msg = PlanController(request.get_json() or {}).plan_update()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': update_id})


@api.route('/plan/delete', methods=['POST'])
@login_required
@permission_required('plan:delete')
def plan_delete():
    delete_id, err_msg = PlanController(request.get_json() or {}).plan_delete()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': delete_id})


@api.route('/plan/round/create', methods=['POST'])
@login_required
@permission_required('plan_round:create')
def plan_round_create():
    create_id, err_msg = PlanController(request.get_json() or {}).round_create()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': create_id})


@api.route('/plan/round/list', methods=['GET'])
@login_required
@permission_required('plan_round:list')
def plan_round_list():
    return ApiResponse.build_success(20000, data=PlanController(request.args).round_list())


@api.route('/plan/case/add', methods=['POST'])
@login_required
@permission_required('plan_case:add')
def plan_case_add():
    added_count, err_msg = PlanController(request.get_json() or {}).plan_case_add()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'addedCount': added_count})


@api.route('/plan/case/list', methods=['GET'])
@login_required
@permission_required('plan_case:list')
def plan_case_list():
    return ApiResponse.build_success(20000, data=PlanController(request.args).plan_case_list())


@api.route('/plan/case/execute', methods=['POST'])
@login_required
@permission_required('plan_case:execute')
def plan_case_execute():
    update_id, err_msg = PlanController(request.get_json() or {}).plan_case_execute()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': update_id})


@api.route('/plan/progress', methods=['GET'])
@login_required
@permission_required('plan:progress')
def plan_progress():
    ret, err_msg = PlanController(request.args).progress()
    if err_msg:
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/automation/case/run', methods=['POST'])
@login_required
@permission_required('automation:run')
def automation_case_run():
    controller = AutomationController(request.get_json() or {})
    try:
        ret, err_msg = controller.case_run()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/automation/plan/run', methods=['POST'])
@login_required
@permission_required('automation:run')
def automation_plan_run():
    controller = AutomationController(request.get_json() or {})
    try:
        ret, err_msg = controller.plan_run()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/automation/execution/list', methods=['GET'])
@login_required
@permission_required('automation:list')
def automation_execution_list():
    controller = AutomationController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.execution_list())
    finally:
        controller.close_session()


@api.route('/automation/execution/detail', methods=['GET'])
@login_required
@permission_required('automation:detail')
def automation_execution_detail():
    controller = AutomationController(request.args)
    try:
        ret, err_msg = controller.execution_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/automation/execution/case/list', methods=['GET'])
@login_required
@permission_required('automation:detail')
def automation_execution_case_list():
    controller = AutomationController(request.args)
    try:
        ret, err_msg = controller.execution_case_list()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/automation/execution/poll', methods=['POST'])
@login_required
@permission_required('automation:detail')
def automation_execution_poll():
    from ..api.service.jenkinsPollService import JenkinsPollService
    from ..api.dao.automationDao import AutomationDao
    
    req_data = request.get_json() or {}
    execution_id = req_data.get('executionId') or req_data.get('execution_id')
    
    from ..api.controller.baseCrudController import BaseCrudController
    controller = BaseCrudController(req_data)
    
    try:
        if execution_id:
            success, msg = JenkinsPollService.poll_jenkins_build_status(controller.session, execution_id)
            if not success:
                return ApiResponse.build_failure(40012, msg=msg)
            execution = AutomationDao.get_execution_by_id(controller.session, execution_id)
            return ApiResponse.build_success(20000, data=execution.to_dict() if execution else {'id': execution_id, 'message': msg})
        else:
            JenkinsPollService.poll_all_pending_executions(controller.session)
            return ApiResponse.build_success(20000, data={'message': '轮询完成'})
    finally:
        controller.close_session()


@api.route('/automation/execution/case/pull', methods=['GET'])
def automation_execution_case_pull():
    req_data = dict(request.args)
    req_data['_callback_token'] = request.headers.get('X-CALLBACK-TOKEN', '')
    controller = AutomationController(req_data)
    try:
        ret, err_msg = controller.execution_case_pull()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/automation/execution/queued', methods=['POST'])
def automation_execution_queued():
    req_data = request.get_json() or {}
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return ApiResponse.build_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_queued()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/automation/execution/start', methods=['POST'])
def automation_execution_start():
    req_data = request.get_json() or {}
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return ApiResponse.build_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_start()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/automation/execution/case/result', methods=['POST'])
def automation_execution_case_result():
    req_data = request.get_json() or {}
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return ApiResponse.build_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_case_result()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/automation/execution/finish', methods=['POST'])
def automation_execution_finish():
    req_data = request.get_json() or {}
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return ApiResponse.build_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_finish()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/automation/execution/abort', methods=['POST'])
def automation_execution_abort():
    req_data = request.get_json() or {}
    req_data['_callback_secret'] = request.headers.get('X-CALLBACK-SECRET', '')
    controller = AutomationController(req_data)
    try:
        ok, err_msg = controller.validate_callback_secret()
        if not ok:
            return ApiResponse.build_failure(40004, msg=err_msg)
        update_id, err_msg = controller.execution_abort()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


# =========================
# 测试 Skills 与业务规则接口
# =========================


@api.route('/skill/create', methods=['POST'])
@login_required
@permission_required('skill:create')
def skill_create():
    controller = SkillController(request.get_json() or {})
    try:
        create_id, err_msg = controller.skill_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/skill/update', methods=['POST'])
@login_required
@permission_required('skill:update')
def skill_update():
    controller = SkillController(request.get_json() or {})
    try:
        update_id, err_msg = controller.skill_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/skill/delete', methods=['POST'])
@login_required
@permission_required('skill:delete')
def skill_delete():
    controller = SkillController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.skill_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/skill/detail', methods=['GET'])
@login_required
@permission_required('skill:detail')
def skill_detail():
    controller = SkillController(request.args)
    try:
        ret, err_msg = controller.skill_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/skill/list', methods=['GET'])
@login_required
@permission_required('skill:list')
def skill_list():
    controller = SkillController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.skill_list())
    finally:
        controller.close_session()


@api.route('/skill-rule/list', methods=['GET'])
@login_required
@permission_required('skill:list')
def skill_rule_list():
    controller = SkillController(request.args)
    try:
        ret, err_msg = controller.skill_rule_list()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/business-rule/create', methods=['POST'])
@login_required
@permission_required('business-rule:create')
def business_rule_create():
    controller = SkillController(request.get_json() or {})
    try:
        create_id, err_msg = controller.business_rule_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/business-rule/update', methods=['POST'])
@login_required
@permission_required('business-rule:update')
def business_rule_update():
    controller = SkillController(request.get_json() or {})
    try:
        update_id, err_msg = controller.business_rule_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/business-rule/delete', methods=['POST'])
@login_required
@permission_required('business-rule:delete')
def business_rule_delete():
    controller = SkillController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.business_rule_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/business-rule/detail', methods=['GET'])
@login_required
@permission_required('business-rule:detail')
def business_rule_detail():
    controller = SkillController(request.args)
    try:
        ret, err_msg = controller.business_rule_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/business-rule/list', methods=['GET'])
@login_required
@permission_required('business-rule:list')
def business_rule_list():
    controller = SkillController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.business_rule_list())
    finally:
        controller.close_session()


# =========================
# 报告接口
# =========================


@api.route('/report/list', methods=['GET'])
@login_required
@permission_required('report:list')
def report_list():
    """分页查询测试报告列表。"""
    controller = ReportController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.report_list())
    finally:
        controller.close_session()


@api.route('/report/detail', methods=['GET'])
@login_required
@permission_required('report:detail')
def report_detail():
    controller = ReportController(request.args)
    try:
        ret, err_msg = controller.report_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/report/generate', methods=['POST'])
@login_required
@permission_required('report:generate')
def report_generate():
    controller = ReportController(request.get_json() or {})
    try:
        create_id, err_msg = controller.report_generate()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


# =========================
# 造数器与造数任务接口
# =========================


@api.route('/data/builder/list', methods=['GET'])
@login_required
@permission_required('data_builder:list')
def data_builder_list():
    """分页查询造数器列表。"""
    return ApiResponse.build_success(20000, data=DataBuilderController(request.args).builder_list())


@api.route('/data/builder/detail', methods=['GET'])
@login_required
@permission_required('data_builder:detail')
def data_builder_detail():
    ret, err_msg = DataBuilderController(request.args).builder_detail()
    if err_msg:
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/data/builder/create', methods=['POST'])
@login_required
@permission_required('data_builder:create')
def data_builder_create():
    create_id, err_msg = DataBuilderController(request.get_json() or {}).builder_create()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': create_id})


@api.route('/data/builder/update', methods=['POST'])
@login_required
@permission_required('data_builder:update')
def data_builder_update():
    update_id, err_msg = DataBuilderController(request.get_json() or {}).builder_update()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': update_id})


@api.route('/data/builder/delete', methods=['POST'])
@login_required
@permission_required('data_builder:delete')
def data_builder_delete():
    delete_id, err_msg = DataBuilderController(request.get_json() or {}).builder_delete()
    if err_msg:
        return ApiResponse.build_failure(40012, msg=err_msg)
    return ApiResponse.build_success(20000, data={'id': delete_id})


@api.route('/data/builder/execute', methods=['POST'])
@login_required
@permission_required('data_builder:execute')
def data_builder_execute():
    ret, err_msg = DataBuilderController(request.get_json() or {}).builder_execute()
    if err_msg:
        return ApiResponse.build_failure(40009, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/data/task/status', methods=['GET'])
@login_required
@permission_required('data_task:status')
def data_task_status():
    ret, err_msg = DataBuilderController(request.args).task_status()
    if err_msg:
        return ApiResponse.build_failure(40011, msg=err_msg)
    return ApiResponse.build_success(20000, data=ret)


@api.route('/role/list', methods=['GET'])
@login_required
@permission_required('role:list')
def role_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.role_list())
    finally:
        controller.close_session()


@api.route('/role/page/list', methods=['GET'])
@login_required
@permission_required('role:list')
def role_page_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.role_page_list())
    finally:
        controller.close_session()


@api.route('/role/detail', methods=['GET'])
@login_required
@permission_required('role:detail')
def role_detail():
    controller = RbacController(request.args)
    try:
        ret, err_msg = controller.role_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/role/create', methods=['POST'])
@login_required
@permission_required('role:create')
def role_create():
    controller = RbacController(request.get_json() or {})
    try:
        create_id, err_msg = controller.role_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/role/update', methods=['POST'])
@login_required
@permission_required('role:update')
def role_update():
    controller = RbacController(request.get_json() or {})
    try:
        update_id, err_msg = controller.role_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/role/delete', methods=['POST'])
@login_required
@permission_required('role:delete')
def role_delete():
    controller = RbacController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.role_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/permission/list', methods=['GET'])
@login_required
@permission_required('permission:list')
def permission_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.permission_list())
    finally:
        controller.close_session()


@api.route('/permission/detail', methods=['GET'])
@login_required
@permission_required('permission:detail')
def permission_detail():
    controller = RbacController(request.args)
    try:
        ret, err_msg = controller.permission_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/permission/create', methods=['POST'])
@login_required
@permission_required('permission:create')
def permission_create():
    controller = RbacController(request.get_json() or {})
    try:
        create_id, err_msg = controller.permission_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/permission/update', methods=['POST'])
@login_required
@permission_required('permission:update')
def permission_update():
    controller = RbacController(request.get_json() or {})
    try:
        update_id, err_msg = controller.permission_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/permission/delete', methods=['POST'])
@login_required
@permission_required('permission:delete')
def permission_delete():
    controller = RbacController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.permission_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/menu/tree', methods=['GET'])
@login_required
@permission_required('menu:list')
def menu_tree():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.menu_tree())
    finally:
        controller.close_session()


@api.route('/menu/current/list', methods=['GET'])
@login_required
def current_menu_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.current_menu_list())
    finally:
        controller.close_session()


@api.route('/role/menu/tree', methods=['GET'])
@login_required
@permission_required('role_menu:list')
def role_menu_tree():
    controller = RbacController(request.args)
    try:
        ret, err_msg = controller.role_menu_tree()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/menu/detail', methods=['GET'])
@login_required
@permission_required('menu:detail')
def menu_detail():
    controller = RbacController(request.args)
    try:
        ret, err_msg = controller.menu_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/menu/create', methods=['POST'])
@login_required
@permission_required('menu:create')
def menu_create():
    controller = RbacController(request.get_json() or {})
    try:
        create_id, err_msg = controller.menu_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/menu/update', methods=['POST'])
@login_required
@permission_required('menu:update')
def menu_update():
    controller = RbacController(request.get_json() or {})
    try:
        update_id, err_msg = controller.menu_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/menu/delete', methods=['POST'])
@login_required
@permission_required('menu:delete')
def menu_delete():
    controller = RbacController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.menu_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/role/permission/list', methods=['GET'])
@login_required
@permission_required('role_permission:list')
def role_permission_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.role_permission_list())
    finally:
        controller.close_session()


@api.route('/role/permission/assign', methods=['POST'])
@login_required
@permission_required('role_permission:assign')
def role_permission_assign():
    controller = RbacController(request.get_json() or {})
    try:
        role_id, err_msg = controller.role_permission_assign()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': role_id})
    finally:
        controller.close_session()


@api.route('/role/menu/list', methods=['GET'])
@login_required
@permission_required('role_menu:list')
def role_menu_list():
    controller = RbacController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.role_menu_list())
    finally:
        controller.close_session()


@api.route('/role/menu/assign', methods=['POST'])
@login_required
@permission_required('role_menu:assign')
def role_menu_assign():
    controller = RbacController(request.get_json() or {})
    try:
        role_id, err_msg = controller.role_menu_assign()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': role_id})
    finally:
        controller.close_session()


@api.route('/user/list', methods=['GET'])
@login_required
@permission_required('user:list')
def user_list():
    controller = UserController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.user_list())
    finally:
        controller.close_session()


@api.route('/user/detail', methods=['GET'])
@login_required
@permission_required('user:detail')
def user_detail():
    controller = UserController(request.args)
    try:
        ret, err_msg = controller.user_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/user/create', methods=['POST'])
@login_required
@permission_required('user:create')
def user_create():
    controller = UserController(request.get_json() or {})
    try:
        create_id, err_msg = controller.user_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/user/update', methods=['POST'])
@login_required
@permission_required('user:update')
def user_update():
    controller = UserController(request.get_json() or {})
    try:
        update_id, err_msg = controller.user_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/user/delete', methods=['POST'])
@login_required
@permission_required('user:delete')
def user_delete():
    controller = UserController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.user_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/user/role/list', methods=['GET'])
@login_required
@permission_required('user_role:list')
def user_role_list():
    controller = UserController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.user_role_list())
    finally:
        controller.close_session()


@api.route('/user/role/assign', methods=['POST'])
@login_required
@permission_required('user_role:assign')
def user_role_assign():
    controller = UserController(request.get_json() or {})
    try:
        user_id, err_msg = controller.user_role_assign()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': user_id})
    finally:
        controller.close_session()


@api.route('/auth/register', methods=['POST'])
def auth_register():
    controller = UserController(request.get_json() or {})
    try:
        create_id, err_msg = controller.register()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/auth/login', methods=['POST'])
def auth_login():
    controller = UserController(request.get_json() or {})
    try:
        ret, err_msg = controller.login()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    except OperationalError:
        return ApiResponse.build_failure(40011, msg='数据库连接失败，请稍后重试！')
    finally:
        controller.close_session()


@api.route('/auth/refresh', methods=['POST'])
def auth_refresh():
    from .utils.authMiddleware import validate_refresh_token, create_token, create_refresh_token, revoke_refresh_token, get_current_user_id
    
    req_json = request.get_json() or {}
    refresh_token = req_json.get('refreshToken') or req_json.get('refresh_token')
    access_token = req_json.get('accessToken') or req_json.get('access_token')
    
    if refresh_token:
        user_id = validate_refresh_token(refresh_token)
        if user_id:
            revoke_refresh_token(refresh_token)
            new_token, expire_seconds = create_token(user_id)
            new_refresh_token, refresh_expire_seconds = create_refresh_token(user_id)
            return ApiResponse.build_success(20000, data={
                'token': new_token,
                'token_type': 'Bearer',
                'expires_in': expire_seconds,
                'refresh_token': new_refresh_token,
                'refresh_expires_in': refresh_expire_seconds
            })
        return ApiResponse.build_failure(40001, msg='refresh_token无效或已过期')
    
    elif access_token:
        user_id = get_current_user_id(access_token)
        if user_id:
            new_token, expire_seconds = create_token(user_id)
            return ApiResponse.build_success(20000, data={
                'token': new_token,
                'token_type': 'Bearer',
                'expires_in': expire_seconds
            })
        return ApiResponse.build_failure(451, msg='access_token无效或已过期')
    
    return ApiResponse.build_failure(40003, msg='请提供refresh_token或access_token')


@api.route('/bug/list', methods=['GET'])
@login_required
@permission_required('bug:list')
def bug_list():
    controller = BugController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.bug_list())
    finally:
        controller.close_session()


@api.route('/bug/detail', methods=['GET'])
@login_required
@permission_required('bug:detail')
def bug_detail():
    controller = BugController(request.args)
    try:
        ret, err_msg = controller.bug_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/bug/create', methods=['POST'])
@login_required
@permission_required('bug:create')
def bug_create():
    controller = BugController(request.get_json() or {})
    try:
        bug_id, err_msg = controller.bug_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': bug_id})
    finally:
        controller.close_session()


@api.route('/bug/update', methods=['POST'])
@login_required
@permission_required('bug:update')
def bug_update():
    controller = BugController(request.get_json() or {})
    try:
        bug_id, err_msg = controller.bug_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': bug_id})
    finally:
        controller.close_session()


@api.route('/bug/delete', methods=['POST'])
@login_required
@permission_required('bug:delete')
def bug_delete():
    controller = BugController(request.get_json() or {})
    try:
        bug_id, err_msg = controller.bug_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': bug_id})
    finally:
        controller.close_session()


@api.route('/bug/history/add', methods=['POST'])
@login_required
@permission_required('bug:update')
def bug_history_add():
    controller = BugController(request.get_json() or {})
    try:
        success, err_msg = controller.bug_history_add()
        if err_msg:
            return ApiResponse.build_failure(40015, msg=err_msg)
        return ApiResponse.build_success(20000, data={'success': success})
    finally:
        controller.close_session()


@api.route('/bug/comment/add', methods=['POST'])
@login_required
@permission_required('bug:comment')
def bug_comment_add():
    controller = BugController(request.get_json() or {})
    try:
        comment_id, err_msg = controller.bug_comment_add()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': comment_id})
    finally:
        controller.close_session()


@api.route('/bug/stats', methods=['GET'])
@login_required
@permission_required('bug:stats')
def bug_stats():
    controller = BugController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.bug_stats())
    finally:
        controller.close_session()


@api.route('/bug/upload', methods=['POST'])
@login_required
@permission_required('bug:create')
def bug_upload():
    controller = BugUploadController(request)
    try:
        file_url, err_msg = controller.bug_upload()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'url': file_url})
    finally:
        controller.close_session()


# =========================
# 文档源接口 (PRD文档/飞书链接)
# =========================

@api.route('/document/list', methods=['GET'])
@login_required
@permission_required('document:list')
def document_list():
    controller = DocumentSourceController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.document_list())
    finally:
        controller.close_session()


@api.route('/document/detail', methods=['GET'])
@login_required
@permission_required('document:detail')
def document_detail():
    controller = DocumentSourceController(request.args)
    try:
        ret, err_msg = controller.document_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/document/create', methods=['POST'])
@login_required
@permission_required('document:create')
def document_create():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        create_id, err_msg = controller.document_create()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': create_id})
    finally:
        controller.close_session()


@api.route('/document/update', methods=['POST'])
@login_required
@permission_required('document:update')
def document_update():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        update_id, err_msg = controller.document_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': update_id})
    finally:
        controller.close_session()


@api.route('/document/delete', methods=['POST'])
@login_required
@permission_required('document:delete')
def document_delete():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        delete_id, err_msg = controller.document_delete()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': delete_id})
    finally:
        controller.close_session()


@api.route('/document/refresh', methods=['POST'])
@login_required
@permission_required('document:update')
def document_refresh():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        success, err_msg = controller.document_refresh()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'success': success})
    finally:
        controller.close_session()


@api.route('/document/generate-cases', methods=['POST'])
@login_required
@permission_required('document:generate')
def document_generate_cases():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        ret, err_msg = controller.document_generate_cases()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/document/match-modules', methods=['POST'])
@login_required
@permission_required('document:generate')
def document_match_modules():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        ret = controller.document_match_modules()
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/document/import-cases', methods=['POST'])
@login_required
@permission_required('document:import')
def document_import_cases():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        success_count, err_msg = controller.document_import_cases()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data={'successCount': success_count})
    finally:
        controller.close_session()


@api.route('/document/batch-create-modules', methods=['POST'])
@login_required
@permission_required('module:create')
def document_batch_create_modules():
    controller = DocumentSourceController(request.get_json() or {})
    try:
        ret, err_msg = controller.document_batch_create_modules()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/document/upload', methods=['POST'])
@login_required
@permission_required('document:create')
def document_upload():
    controller = DocumentSourceController(request)
    try:
        ret, err_msg = controller.document_upload()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


# =========================
# 性能测试接口
# =========================


def _performance_response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return ApiResponse.build_success(20000, data={id_key: ret})
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/performance/scenarios', methods=['GET'])
@login_required
@permission_required('performance:scenario:list')
def performance_scenario_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.scenario_list)


@api.route('/performance/scenarios', methods=['POST'])
@login_required
@permission_required('performance:scenario:create')
def performance_scenario_create():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.scenario_create)


@api.route('/performance/scenarios/<int:scenario_id>', methods=['GET'])
@login_required
@permission_required('performance:scenario:list')
def performance_scenario_detail(scenario_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.scenario_detail(scenario_id))


@api.route('/performance/scenarios/<int:scenario_id>', methods=['PUT'])
@login_required
@permission_required('performance:scenario:update')
def performance_scenario_update(scenario_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.scenario_update(scenario_id))


@api.route('/performance/scenarios/<int:scenario_id>', methods=['DELETE'])
@login_required
@permission_required('performance:scenario:delete')
def performance_scenario_delete(scenario_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.scenario_delete(scenario_id))


@api.route('/performance/test-machines', methods=['GET'])
@login_required
@permission_required('performance:machine:list')
def performance_machine_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.machine_list)


@api.route('/performance/test-machines/available', methods=['GET'])
@login_required
@permission_required('performance:machine:list')
def performance_machine_available():
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.machine_list(True))


@api.route('/performance/test-machines', methods=['POST'])
@login_required
@permission_required('performance:machine:save')
def performance_machine_create():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.machine_create)


@api.route('/performance/test-machines/<int:machine_id>', methods=['GET'])
@login_required
@permission_required('performance:machine:list')
def performance_machine_detail(machine_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.machine_detail(machine_id))


@api.route('/performance/test-machines/<int:machine_id>', methods=['PUT'])
@login_required
@permission_required('performance:machine:save')
def performance_machine_update(machine_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.machine_update(machine_id))


@api.route('/performance/test-machines/<int:machine_id>', methods=['DELETE'])
@login_required
@permission_required('performance:machine:delete')
def performance_machine_delete(machine_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.machine_delete(machine_id))


@api.route('/performance/scripts', methods=['GET'])
@login_required
@permission_required('performance:script:list')
def performance_script_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.script_list)


@api.route('/performance/scripts/upload', methods=['POST'])
@login_required
@permission_required('performance:script:upload')
def performance_script_upload():
    controller = PerformanceController(request)
    return _performance_response(controller, controller.script_upload)


@api.route('/performance/scripts/generate-plan', methods=['POST'])
@login_required
@permission_required('performance:script:generate')
def performance_script_generate_plan():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.script_generate_plan)


@api.route('/performance/scripts/generate-script', methods=['POST'])
@login_required
@permission_required('performance:script:generate')
def performance_script_generate_script():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.script_generate_script)


@api.route('/performance/scripts/<int:script_id>', methods=['GET'])
@login_required
@permission_required('performance:script:list')
def performance_script_detail(script_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.script_detail(script_id))


@api.route('/performance/scripts/<int:script_id>/versions', methods=['GET'])
@login_required
@permission_required('performance:script:list')
def performance_script_version_list(script_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.script_version_list(script_id))


@api.route('/performance/scripts/versions/<int:version_id>/download', methods=['GET'])
@login_required
@permission_required('performance:script:download')
def performance_script_version_download(version_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.script_version_download(version_id))


@api.route('/performance/execution-configs', methods=['GET'])
@login_required
@permission_required('performance:config:list')
def performance_execution_config_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.execution_config_list)


@api.route('/performance/execution-configs', methods=['POST'])
@login_required
@permission_required('performance:config:save')
def performance_execution_config_create():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.execution_config_create)


@api.route('/performance/execution-configs/<int:config_id>', methods=['PUT'])
@login_required
@permission_required('performance:config:save')
def performance_execution_config_update(config_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.execution_config_update(config_id))


@api.route('/performance/execution-configs/<int:config_id>', methods=['GET'])
@login_required
@permission_required('performance:config:list')
def performance_execution_config_detail(config_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.execution_config_detail(config_id))


@api.route('/performance/runs', methods=['POST'])
@login_required
@permission_required('performance:run:execute')
def performance_run_create():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.run_create)


@api.route('/performance/runs', methods=['GET'])
@login_required
@permission_required('performance:run:list')
def performance_run_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.run_list)


@api.route('/performance/runs/sync-jenkins', methods=['POST'])
@login_required
@permission_required('performance:run:list')
def performance_run_sync_jenkins():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.sync_jenkins_runs)


@api.route('/performance/runs/<int:run_id>', methods=['GET'])
@login_required
@permission_required('performance:run:detail')
def performance_run_detail(run_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.run_detail(run_id))


@api.route('/performance/runs/<int:run_id>/stop', methods=['POST'])
@login_required
@permission_required('performance:run:stop')
def performance_run_stop(run_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.run_stop(run_id))


@api.route('/performance/runs/<int:run_id>/retry', methods=['POST'])
@login_required
@permission_required('performance:run:retry')
def performance_run_retry(run_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.run_retry(run_id))


@api.route('/performance/jenkins/callback', methods=['POST'])
def performance_jenkins_callback():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.jenkins_callback)


@api.route('/performance/reports/<int:run_id>', methods=['GET'])
@login_required
@permission_required('performance:report:detail')
def performance_report_detail(run_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.report_detail(run_id))


@api.route('/performance/reports/<int:run_id>/metrics', methods=['GET'])
@login_required
@permission_required('performance:report:detail')
def performance_report_metrics(run_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.report_metrics(run_id))


@api.route('/performance/reports/<int:run_id>/gate-results', methods=['GET'])
@login_required
@permission_required('performance:report:detail')
def performance_report_gate_results(run_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.report_gate_results(run_id))


@api.route('/performance/reports/<int:run_id>/native', methods=['GET'])
@login_required
@permission_required('performance:report:detail')
def performance_report_native(run_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.report_native(run_id))


@api.route('/performance/reports/<int:run_id>/ai-analysis', methods=['POST'])
@login_required
@permission_required('performance:report:ai')
def performance_report_ai_analysis(run_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.report_ai_analysis(run_id))


@api.route('/performance/baselines', methods=['GET'])
@login_required
@permission_required('performance:baseline:list')
def performance_baseline_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.baseline_list)


@api.route('/performance/baselines/from-run', methods=['POST'])
@login_required
@permission_required('performance:baseline:save')
def performance_baseline_from_run():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.baseline_from_run)


@api.route('/performance/baselines/<int:baseline_id>/active', methods=['PUT'])
@login_required
@permission_required('performance:baseline:save')
def performance_baseline_active(baseline_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.baseline_active(baseline_id))


@api.route('/performance/baselines/<int:baseline_id>/deprecated', methods=['PUT'])
@login_required
@permission_required('performance:baseline:save')
def performance_baseline_deprecated(baseline_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.baseline_deprecated(baseline_id))


@api.route('/performance/monitor-sources', methods=['GET'])
@login_required
@permission_required('performance:monitor:list')
def performance_monitor_source_list():
    controller = PerformanceController(request.args)
    return _performance_response(controller, controller.monitor_source_list)


@api.route('/performance/monitor-sources', methods=['POST'])
@login_required
@permission_required('performance:monitor:save')
def performance_monitor_source_create():
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, controller.monitor_source_create)


@api.route('/performance/monitor-sources/<int:source_id>', methods=['GET'])
@login_required
@permission_required('performance:monitor:list')
def performance_monitor_source_detail(source_id):
    controller = PerformanceController(request.args)
    return _performance_response(controller, lambda: controller.monitor_source_detail(source_id))


@api.route('/performance/monitor-sources/<int:source_id>', methods=['PUT'])
@login_required
@permission_required('performance:monitor:save')
def performance_monitor_source_update(source_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.monitor_source_update(source_id))


@api.route('/performance/monitor-sources/<int:source_id>', methods=['DELETE'])
@login_required
@permission_required('performance:monitor:delete')
def performance_monitor_source_delete(source_id):
    controller = PerformanceController(request.get_json() or {})
    return _performance_response(controller, lambda: controller.monitor_source_delete(source_id))


# =========================
# 需求问答 / 知识库接口
# =========================


def _knowledge_response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return ApiResponse.build_success(20000, data={id_key: ret})
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/knowledge/document/list', methods=['GET'])
@login_required
@permission_required('knowledge:list')
def knowledge_document_list():
    controller = KnowledgeController(request.args)
    return _knowledge_response(controller, controller.document_list)


@api.route('/knowledge/document/upload', methods=['POST'])
@login_required
@permission_required('knowledge:upload')
def knowledge_document_upload():
    controller = KnowledgeController(request)
    return _knowledge_response(controller, controller.document_upload)


@api.route('/knowledge/document/parse', methods=['POST'])
@login_required
@permission_required('knowledge:parse')
def knowledge_document_parse():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.document_parse)


@api.route('/knowledge/document/delete', methods=['POST'])
@login_required
@permission_required('knowledge:delete')
def knowledge_document_delete():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.document_delete)


@api.route('/knowledge/search', methods=['POST'])
@login_required
@permission_required('knowledge:search')
def knowledge_search():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.search)


@api.route('/knowledge/chat', methods=['POST'])
@login_required
@permission_required('knowledge:chat')
def knowledge_chat():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.chat)


@api.route('/knowledge/chat/session/list', methods=['GET'])
@login_required
@permission_required('knowledge:chat')
def knowledge_session_list():
    controller = KnowledgeController(request.args)
    return _knowledge_response(controller, controller.session_list)


@api.route('/knowledge/chat/message/list', methods=['GET'])
@login_required
@permission_required('knowledge:chat')
def knowledge_message_list():
    controller = KnowledgeController(request.args)
    return _knowledge_response(controller, controller.message_list)


@api.route('/knowledge/chat/session/delete', methods=['POST'])
@login_required
@permission_required('knowledge:chat')
def knowledge_session_delete():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.session_delete)


@api.route('/knowledge/model-setting/detail', methods=['GET'])
@login_required
@permission_required('knowledge:setting')
def knowledge_model_setting_detail():
    controller = KnowledgeController(request.args)
    return _knowledge_response(controller, controller.model_setting_detail)


@api.route('/knowledge/model-setting/save', methods=['POST'])
@login_required
@permission_required('knowledge:setting')
def knowledge_model_setting_save():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.model_setting_save)


@api.route('/knowledge/model-setting/test', methods=['POST'])
@login_required
@permission_required('knowledge:setting')
def knowledge_model_setting_test():
    controller = KnowledgeController(request.get_json() or {})
    return _knowledge_response(controller, controller.model_setting_test)


# =========================
# 智能 Mock 服务接口
# =========================

@api.route('/mock/document/import', methods=['POST'])
@login_required
@permission_required('mock:document:import')
def mock_document_import():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.document_import()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/mock/document/upload-import', methods=['POST'])
@login_required
@permission_required('mock:document:import')
def mock_document_upload_import():
    controller = MockController(request)
    try:
        ret, err_msg = controller.document_upload_import()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/mock/document/url-import', methods=['POST'])
@login_required
@permission_required('mock:document:import')
def mock_document_url_import():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.document_url_import()
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/mock/document/list', methods=['GET'])
@login_required
@permission_required('mock:document:list')
def mock_document_list():
    controller = MockController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.document_list())
    finally:
        controller.close_session()


@api.route('/mock/interface/list', methods=['GET'])
@login_required
@permission_required('mock:interface:list')
def mock_interface_list():
    controller = MockController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.interface_list())
    finally:
        controller.close_session()


@api.route('/mock/interface/detail', methods=['GET'])
@login_required
@permission_required('mock:interface:detail')
def mock_interface_detail():
    controller = MockController(request.args)
    try:
        ret, err_msg = controller.interface_detail()
        if err_msg:
            return ApiResponse.build_failure(40011, msg=err_msg)
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/mock/interface/update', methods=['POST'])
@login_required
@permission_required('mock:interface:update')
def mock_interface_update():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.interface_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/interface/enable', methods=['POST'])
@login_required
@permission_required('mock:interface:enable')
def mock_interface_enable():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.interface_enable()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/interface/disable', methods=['POST'])
@login_required
@permission_required('mock:interface:disable')
def mock_interface_disable():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.interface_disable()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/scene/list', methods=['GET'])
@login_required
@permission_required('mock:scene:list')
def mock_scene_list():
    controller = MockController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.scene_list())
    finally:
        controller.close_session()


@api.route('/mock/scene/update', methods=['POST'])
@login_required
@permission_required('mock:scene:update')
def mock_scene_update():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.scene_update()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/scene/enable', methods=['POST'])
@login_required
@permission_required('mock:scene:enable')
def mock_scene_enable():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.scene_enable()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/scene/disable', methods=['POST'])
@login_required
@permission_required('mock:scene:disable')
def mock_scene_disable():
    controller = MockController(request.get_json() or {})
    try:
        ret, err_msg = controller.scene_disable()
        if err_msg:
            return ApiResponse.build_failure(40012, msg=err_msg)
        return ApiResponse.build_success(20000, data={'id': ret})
    finally:
        controller.close_session()


@api.route('/mock/log/list', methods=['GET'])
@login_required
@permission_required('mock:log:list')
def mock_log_list():
    controller = MockController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.log_list())
    finally:
        controller.close_session()


@api.route('/mock/parse-issue/list', methods=['GET'])
@login_required
@permission_required('mock:parse-issue:list')
def mock_parse_issue_list():
    controller = MockController(request.args)
    try:
        return ApiResponse.build_success(20000, data=controller.parse_issue_list())
    finally:
        controller.close_session()


@api.route('/mock/runtime/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@login_required
@permission_required('mock:runtime:access')
def mock_runtime(path):
    body = request.get_json(silent=True) or {}
    headers = dict(request.headers)
    query = request.args.to_dict(flat=True)
    controller = MockController({})
    try:
        response, err_msg = controller.runtime(request.method, path, query, body, headers)
        if err_msg:
            logger.warning(f'mock_runtime提示：{err_msg}, path={path}, query={query}')
        return response
    except Exception as e:
        logger.error(f'mock_runtime异常：{str(e)}, path={path}, query={query}, 堆栈：{traceback.format_exc()}')
        return ApiResponse.build_failure(40008, msg=str(e))
    finally:
        controller.close_session()


# =========================
# AI 测试中枢接口
# =========================


def _ai_response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return ApiResponse.build_success(20000, data={id_key: ret})
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/ai/agent/create', methods=['POST'])
@login_required
@permission_required('ai_agent:create')
def ai_agent_create():
    controller = AiAgentController(request.get_json() or {})
    return _ai_response(controller, controller.agent_create)


@api.route('/ai/agent/update', methods=['POST'])
@login_required
@permission_required('ai_agent:update')
def ai_agent_update():
    controller = AiAgentController(request.get_json() or {})
    return _ai_response(controller, controller.agent_update)


@api.route('/ai/agent/delete', methods=['POST'])
@login_required
@permission_required('ai_agent:delete')
def ai_agent_delete():
    controller = AiAgentController(request.get_json() or {})
    return _ai_response(controller, controller.agent_delete)


@api.route('/ai/agent/list', methods=['GET'])
@login_required
@permission_required('ai_agent:list')
def ai_agent_list():
    controller = AiAgentController(request.args)
    return _ai_response(controller, controller.agent_list)


@api.route('/ai/agent/detail', methods=['GET'])
@login_required
@permission_required('ai_agent:detail')
def ai_agent_detail():
    controller = AiAgentController(request.args)
    return _ai_response(controller, controller.agent_detail)


@api.route('/ai/agent/test', methods=['POST'])
@login_required
@permission_required('ai_agent:execute')
def ai_agent_test():
    controller = AiAgentController(request.get_json() or {})
    return _ai_response(controller, controller.agent_test)


@api.route('/ai/agent/execute', methods=['POST'])
@login_required
@permission_required('ai_agent:execute')
def ai_agent_execute():
    controller = AiAgentController(request.get_json() or {})
    return _ai_response(controller, controller.agent_execute)


@api.route('/ai/agent/execution/list', methods=['GET'])
@login_required
@permission_required('ai_agent:detail')
def ai_agent_execution_list():
    controller = AiAgentController(request.args)
    return _ai_response(controller, controller.execution_list)


@api.route('/ai/agent/execution/detail', methods=['GET'])
@login_required
@permission_required('ai_agent:detail')
def ai_agent_execution_detail():
    controller = AiAgentController(request.args)
    return _ai_response(controller, controller.execution_detail)


@api.route('/ai/tool/create', methods=['POST'])
@login_required
@permission_required('ai_tool:create')
def ai_tool_create():
    controller = AiToolController(request.get_json() or {})
    return _ai_response(controller, controller.tool_create)


@api.route('/ai/tool/update', methods=['POST'])
@login_required
@permission_required('ai_tool:update')
def ai_tool_update():
    controller = AiToolController(request.get_json() or {})
    return _ai_response(controller, controller.tool_update)


@api.route('/ai/tool/delete', methods=['POST'])
@login_required
@permission_required('ai_tool:delete')
def ai_tool_delete():
    controller = AiToolController(request.get_json() or {})
    return _ai_response(controller, controller.tool_delete)


@api.route('/ai/tool/list', methods=['GET'])
@login_required
@permission_required('ai_tool:list')
def ai_tool_list():
    controller = AiToolController(request.args)
    return _ai_response(controller, controller.tool_list)


@api.route('/ai/tool/detail', methods=['GET'])
@login_required
@permission_required('ai_tool:detail')
def ai_tool_detail():
    controller = AiToolController(request.args)
    return _ai_response(controller, controller.tool_detail)


@api.route('/ai/tool/test', methods=['POST'])
@login_required
@permission_required('ai_tool:execute')
def ai_tool_test():
    controller = AiToolController(request.get_json() or {})
    return _ai_response(controller, controller.tool_test)


@api.route('/ai/tool/execute', methods=['POST'])
@login_required
@permission_required('ai_tool:execute')
def ai_tool_execute():
    controller = AiToolController(request.get_json() or {})
    return _ai_response(controller, controller.tool_execute)


@api.route('/ai/tool/execution/list', methods=['GET'])
@login_required
@permission_required('ai_tool:detail')
def ai_tool_execution_list():
    controller = AiToolController(request.args)
    return _ai_response(controller, controller.execution_list)


@api.route('/ai/tool/execution/detail', methods=['GET'])
@login_required
@permission_required('ai_tool:detail')
def ai_tool_execution_detail():
    controller = AiToolController(request.args)
    return _ai_response(controller, controller.execution_detail)


@api.route('/ai/mcp/create', methods=['POST'])
@login_required
@permission_required('ai_mcp:create')
def ai_mcp_create():
    controller = AiMcpController(request.get_json() or {})
    return _ai_response(controller, controller.mcp_create)


@api.route('/ai/mcp/update', methods=['POST'])
@login_required
@permission_required('ai_mcp:update')
def ai_mcp_update():
    controller = AiMcpController(request.get_json() or {})
    return _ai_response(controller, controller.mcp_update)


@api.route('/ai/mcp/delete', methods=['POST'])
@login_required
@permission_required('ai_mcp:delete')
def ai_mcp_delete():
    controller = AiMcpController(request.get_json() or {})
    return _ai_response(controller, controller.mcp_delete)


@api.route('/ai/mcp/list', methods=['GET'])
@login_required
@permission_required('ai_mcp:list')
def ai_mcp_list():
    controller = AiMcpController(request.args)
    return _ai_response(controller, controller.mcp_list)


@api.route('/ai/mcp/detail', methods=['GET'])
@login_required
@permission_required('ai_mcp:detail')
def ai_mcp_detail():
    controller = AiMcpController(request.args)
    return _ai_response(controller, controller.mcp_detail)


@api.route('/ai/mcp/test', methods=['POST'])
@login_required
@permission_required('ai_mcp:call')
def ai_mcp_test():
    controller = AiMcpController(request.get_json() or {})
    return _ai_response(controller, controller.mcp_test)


@api.route('/ai/mcp/call', methods=['POST'])
@login_required
@permission_required('ai_mcp:call')
def ai_mcp_call():
    controller = AiMcpController(request.get_json() or {})
    return _ai_response(controller, controller.mcp_call)


@api.route('/ai/mcp/call/log/list', methods=['GET'])
@login_required
@permission_required('ai_mcp:detail')
def ai_mcp_call_log_list():
    controller = AiMcpController(request.args)
    return _ai_response(controller, controller.call_log_list)


@api.route('/ai/mcp/call/log/detail', methods=['GET'])
@login_required
@permission_required('ai_mcp:detail')
def ai_mcp_call_log_detail():
    controller = AiMcpController(request.args)
    return _ai_response(controller, controller.call_log_detail)


@api.route('/ai/flow/create', methods=['POST'])
@login_required
@permission_required('ai_flow:create')
def ai_flow_create():
    controller = AiFlowController(request.get_json() or {})
    return _ai_response(controller, controller.flow_create)


@api.route('/ai/flow/update', methods=['POST'])
@login_required
@permission_required('ai_flow:update')
def ai_flow_update():
    controller = AiFlowController(request.get_json() or {})
    return _ai_response(controller, controller.flow_update)


@api.route('/ai/flow/delete', methods=['POST'])
@login_required
@permission_required('ai_flow:delete')
def ai_flow_delete():
    controller = AiFlowController(request.get_json() or {})
    return _ai_response(controller, controller.flow_delete)


@api.route('/ai/flow/list', methods=['GET'])
@login_required
@permission_required('ai_flow:list')
def ai_flow_list():
    controller = AiFlowController(request.args)
    return _ai_response(controller, controller.flow_list)


@api.route('/ai/flow/detail', methods=['GET'])
@login_required
@permission_required('ai_flow:detail')
def ai_flow_detail():
    controller = AiFlowController(request.args)
    return _ai_response(controller, controller.flow_detail)


@api.route('/ai/flow/execute', methods=['POST'])
@login_required
@permission_required('ai_flow:execute')
def ai_flow_execute():
    controller = AiFlowController(request.get_json() or {})
    return _ai_response(controller, controller.flow_execute)


@api.route('/ai/flow/execution/list', methods=['GET'])
@login_required
@permission_required('ai_flow:detail')
def ai_flow_execution_list():
    controller = AiFlowController(request.args)
    return _ai_response(controller, controller.execution_list)


@api.route('/ai/flow/execution/detail', methods=['GET'])
@login_required
@permission_required('ai_flow:detail')
def ai_flow_execution_detail():
    controller = AiFlowController(request.args)
    return _ai_response(controller, controller.execution_detail)


@api.route('/ai/task/create', methods=['POST'])
@login_required
@permission_required('ai_task:create')
def ai_task_create():
    controller = AiTaskController(request.get_json() or {})
    return _ai_response(controller, controller.task_create)


@api.route('/ai/task/list', methods=['GET'])
@login_required
@permission_required('ai_task:list')
def ai_task_list():
    controller = AiTaskController(request.args)
    return _ai_response(controller, controller.task_list)


@api.route('/ai/task/detail', methods=['GET'])
@login_required
@permission_required('ai_task:detail')
def ai_task_detail():
    controller = AiTaskController(request.args)
    return _ai_response(controller, controller.task_detail)


@api.route('/ai/task/execute', methods=['POST'])
@login_required
@permission_required('ai_task:execute')
def ai_task_execute():
    controller = AiTaskController(request.get_json() or {})
    return _ai_response(controller, controller.task_execute)


@api.route('/ai/task/cancel', methods=['POST'])
@login_required
@permission_required('ai_task:cancel')
def ai_task_cancel():
    controller = AiTaskController(request.get_json() or {})
    return _ai_response(controller, controller.task_cancel)


@api.route('/ai/report/create', methods=['POST'])
@login_required
@permission_required('ai_report:create')
def ai_report_create():
    controller = AiReportController(request.get_json() or {})
    return _ai_response(controller, controller.report_create)


@api.route('/ai/report/list', methods=['GET'])
@login_required
@permission_required('ai_report:list')
def ai_report_list():
    controller = AiReportController(request.args)
    return _ai_response(controller, controller.report_list)


@api.route('/ai/report/detail', methods=['GET'])
@login_required
@permission_required('ai_report:detail')
def ai_report_detail():
    controller = AiReportController(request.args)
    return _ai_response(controller, controller.report_detail)


# =========================
# AI 精准测试与增量覆盖率接口
# =========================


def _precise_response(controller, action, id_key='id'):
    try:
        result = action()
        if isinstance(result, tuple) and len(result) == 2:
            ret, err_msg = result
        else:
            ret, err_msg = result, ''
        if err_msg:
            return ApiResponse.build_failure(40009, msg=err_msg)
        if isinstance(ret, int):
            return ApiResponse.build_success(20000, data={id_key: ret})
        return ApiResponse.build_success(20000, data=ret)
    finally:
        controller.close_session()


@api.route('/precise/analysis/create', methods=['POST'])
@login_required
@permission_required('precise:analysis:create')
def precise_analysis_create():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.analysis_create, 'analysisId')


@api.route('/precise/analysis/list', methods=['GET'])
@login_required
@permission_required('precise:analysis:list')
def precise_analysis_list():
    controller = PreciseTestController(request.args)
    return _precise_response(controller, controller.analysis_list)


@api.route('/precise/analysis/<int:analysis_id>', methods=['GET'])
@login_required
@permission_required('precise:analysis:detail')
def precise_analysis_detail(analysis_id):
    controller = PreciseTestController(request.args)
    return _precise_response(controller, lambda: controller.analysis_detail(analysis_id))


@api.route('/precise/analysis/<int:analysis_id>/parse-diff', methods=['POST'])
@login_required
@permission_required('precise:analysis:parse')
def precise_analysis_parse_diff(analysis_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.parse_diff(analysis_id))


@api.route('/precise/analysis/<int:analysis_id>/ai-impact', methods=['POST'])
@login_required
@permission_required('precise:analysis:ai')
def precise_analysis_ai_impact(analysis_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.ai_impact(analysis_id))


@api.route('/precise/relations/list', methods=['GET'])
@login_required
@permission_required('precise:relation:list')
def precise_relation_list():
    controller = PreciseTestController(request.args)
    return _precise_response(controller, controller.relation_list)


@api.route('/precise/relations/create', methods=['POST'])
@login_required
@permission_required('precise:relation:create')
def precise_relation_create():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.relation_create, 'relationId')


@api.route('/precise/relations/<int:relation_id>', methods=['PUT'])
@login_required
@permission_required('precise:relation:update')
def precise_relation_update(relation_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.relation_update(relation_id), 'relationId')


@api.route('/precise/relations/<int:relation_id>', methods=['DELETE'])
@login_required
@permission_required('precise:relation:delete')
def precise_relation_delete(relation_id):
    controller = PreciseTestController(request.get_json(silent=True) or {})
    return _precise_response(controller, lambda: controller.relation_delete(relation_id), 'relationId')


@api.route('/precise/relations/import', methods=['POST'])
@login_required
@permission_required('precise:relation:import')
def precise_relation_import():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.relation_import)


@api.route('/precise/analysis/<int:analysis_id>/recommend', methods=['POST'])
@login_required
@permission_required('precise:recommend:create')
def precise_recommendation_generate(analysis_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.recommendation_generate(analysis_id))


@api.route('/precise/analysis/<int:analysis_id>/recommendations', methods=['GET'])
@login_required
@permission_required('precise:recommend:list')
def precise_recommendation_list(analysis_id):
    controller = PreciseTestController(request.args)
    return _precise_response(controller, lambda: controller.recommendation_list(analysis_id))


@api.route('/precise/recommendations/accept', methods=['POST'])
@login_required
@permission_required('precise:recommend:accept')
def precise_recommendation_accept():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.recommendation_accept)


@api.route('/precise/analysis/<int:analysis_id>/execute', methods=['POST'])
@login_required
@permission_required('precise:execute:create')
def precise_execute(analysis_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.execute(analysis_id))


@api.route('/precise/executions/sync-jenkins', methods=['POST'])
@login_required
@permission_required('precise:execution:sync')
def precise_execution_sync_jenkins():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.sync_jenkins)


@api.route('/precise/executions/list', methods=['GET'])
@login_required
@permission_required('precise:execution:list')
def precise_execution_list():
    controller = PreciseTestController(request.args)
    return _precise_response(controller, controller.execution_list)


@api.route('/precise/executions/<int:execution_id>', methods=['GET'])
@login_required
@permission_required('precise:execution:list')
def precise_execution_detail(execution_id):
    controller = PreciseTestController(request.args)
    return _precise_response(controller, lambda: controller.execution_detail(execution_id))


@api.route('/precise/coverage/upload', methods=['POST'])
@login_required
@permission_required('precise:coverage:upload')
def precise_coverage_upload():
    controller = PreciseTestController(request)
    return _precise_response(controller, controller.coverage_upload)


@api.route('/precise/coverage/list', methods=['GET'])
@login_required
@permission_required('precise:coverage:detail')
def precise_coverage_list():
    controller = PreciseTestController(request.args)
    return _precise_response(controller, controller.coverage_list)


@api.route('/precise/coverage/pull-from-jenkins', methods=['POST'])
@login_required
@permission_required('precise:coverage:pull')
def precise_coverage_pull_from_jenkins():
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, controller.coverage_pull_from_jenkins)


@api.route('/precise/coverage/<int:coverage_id>', methods=['GET'])
@login_required
@permission_required('precise:coverage:detail')
def precise_coverage_detail(coverage_id):
    controller = PreciseTestController(request.args)
    return _precise_response(controller, lambda: controller.coverage_detail(coverage_id))


@api.route('/precise/coverage/<int:coverage_id>/calculate-incremental', methods=['POST'])
@login_required
@permission_required('precise:coverage:calculate')
def precise_coverage_calculate_incremental(coverage_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.calculate_incremental(coverage_id))


@api.route('/precise/coverage/<int:coverage_id>/ai-risk-analysis', methods=['POST'])
@login_required
@permission_required('precise:coverage:ai')
def precise_coverage_ai_risk_analysis(coverage_id):
    controller = PreciseTestController(request.get_json() or {})
    return _precise_response(controller, lambda: controller.ai_risk_analysis(coverage_id))


@api.route('/precise/gate/evaluate', methods=['POST'])
@login_required
@permission_required('precise:gate:evaluate')
def precise_gate_evaluate():
    req_json = request.get_json() or {}
    analysis_id = req_json.get('analysisId') or req_json.get('analysis_id')
    controller = PreciseTestController(req_json)
    return _precise_response(controller, lambda: controller.gate_evaluate(analysis_id))


@api.route('/precise/gate/result/<int:analysis_id>', methods=['GET'])
@login_required
@permission_required('precise:gate:result')
def precise_gate_result(analysis_id):
    controller = PreciseTestController(request.args)
    return _precise_response(controller, lambda: controller.gate_result(analysis_id))

