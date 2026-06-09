# encoding: UTF-8
from sqlalchemy import BigInteger, Column, Integer, Numeric, SmallInteger, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from common.sqlSession import to_dict

Base = declarative_base()
Base.to_dict = to_dict


class PreciseAnalysis(Base):
    __tablename__ = 'precise_analysis'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_no = Column(String(64), nullable=False, comment='分析编号')
    product_id = Column(BigInteger, comment='产品ID')
    project_id = Column(BigInteger, comment='项目ID')
    repository_url = Column(String(512), comment='Git仓库地址')
    branch_name = Column(String(128), comment='分支名称')
    base_commit = Column(String(128), comment='对比基线Commit')
    target_commit = Column(String(128), comment='目标Commit')
    title = Column(String(255), comment='分析标题')
    description = Column(Text, comment='分析说明')
    diff_summary_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='Git Diff解析摘要JSON')
    ai_impact_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='AI影响分析结果JSON')
    status = Column(SmallInteger, default=1, comment='状态：1待解析 2已解析Diff 3AI已分析 4已推荐 5执行中 6已完成 7失败')
    risk_level = Column(String(32), comment='风险等级')
    created_by = Column(BigInteger, comment='创建人用户ID')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseChangedFile(Base):
    __tablename__ = 'precise_changed_file'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    file_path = Column(String(1024), comment='变更文件路径')
    change_type = Column(String(32), comment='变更类型')
    changed_lines = Column(JSONB, server_default=text("'[]'::jsonb"), comment='变更行号列表JSON')
    added_lines = Column(JSONB, server_default=text("'[]'::jsonb"), comment='新增行号列表JSON')
    deleted_lines = Column(JSONB, server_default=text("'[]'::jsonb"), comment='删除行号列表JSON')
    code_snippets = Column(JSONB, server_default=text("'[]'::jsonb"), comment='变更代码片段JSON')
    ai_summary = Column(Text, comment='AI文件变更摘要')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseRelationMap(Base):
    __tablename__ = 'precise_relation_map'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    product_id = Column(BigInteger, comment='产品ID')
    project_id = Column(BigInteger, comment='项目ID')
    relation_type = Column(String(64), comment='关系类型')
    source_type = Column(String(64), comment='源节点类型')
    source_key = Column(String(1024), comment='源节点唯一键')
    target_type = Column(String(64), comment='目标节点类型')
    target_key = Column(String(1024), comment='目标节点唯一键')
    weight = Column(Numeric(10, 4), default=1, comment='关系权重')
    confidence = Column(Numeric(10, 4), default=1, comment='关系置信度')
    source_origin = Column(String(64), default='manual', comment='关系来源')
    status = Column(SmallInteger, default=1, comment='状态：0禁用 1启用')
    created_by = Column(BigInteger, comment='创建人用户ID')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseRecommendation(Base):
    __tablename__ = 'precise_recommendation'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    case_id = Column(BigInteger, comment='测试用例ID')
    script_id = Column(BigInteger, comment='自动化脚本ID')
    module_name = Column(String(255), comment='模块名称')
    api_path = Column(String(512), comment='接口路径')
    recommend_level = Column(String(16), comment='推荐等级')
    execute_type = Column(String(32), comment='执行类型')
    risk_level = Column(String(32), comment='风险等级')
    reason = Column(Text, comment='规则推荐原因')
    ai_reason = Column(Text, comment='AI推荐原因')
    confidence = Column(Numeric(10, 4), comment='推荐置信度')
    accepted = Column(SmallInteger, default=1, comment='是否采纳：0否 1是')
    execution_status = Column(SmallInteger, default=0, comment='执行状态')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseExecution(Base):
    __tablename__ = 'precise_execution'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    execution_no = Column(String(64), comment='执行编号')
    jenkins_job_name = Column(String(255), comment='Jenkins任务名称')
    jenkins_queue_id = Column(String(128), comment='Jenkins队列ID')
    jenkins_build_number = Column(String(128), comment='Jenkins构建号')
    jenkins_build_url = Column(String(1024), comment='Jenkins构建地址')
    console_url = Column(String(1024), comment='Jenkins控制台地址')
    callback_token = Column(String(128), comment='回调校验Token')
    status = Column(SmallInteger, default=1, comment='状态：1待触发 2排队中 3执行中 4成功 5失败 6取消')
    start_time = Column(TIMESTAMP, comment='开始时间')
    end_time = Column(TIMESTAMP, comment='结束时间')
    error_message = Column(Text, comment='错误信息')
    created_by = Column(BigInteger, comment='创建人用户ID')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseCoverageReport(Base):
    __tablename__ = 'precise_coverage_report'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    execution_id = Column(BigInteger, comment='执行记录ID')
    report_no = Column(String(64), comment='覆盖率报告编号')
    coverage_type = Column(String(32), comment='覆盖率类型')
    tool_type = Column(String(32), comment='覆盖率工具类型')
    artifact_url = Column(String(1024), comment='Jenkins归档产物地址')
    local_path = Column(String(1024), comment='本地覆盖率文件路径')
    summary_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='覆盖率摘要JSON')
    status = Column(SmallInteger, default=1, comment='状态：1解析成功 2解析失败')
    created_by = Column(BigInteger, comment='创建人用户ID')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseIncrementalCoverage(Base):
    __tablename__ = 'precise_incremental_coverage'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    coverage_report_id = Column(BigInteger, nullable=False, comment='覆盖率报告ID')
    file_path = Column(String(1024), comment='文件路径')
    changed_line_count = Column(Integer, default=0, comment='变更有效行数')
    covered_changed_line_count = Column(Integer, default=0, comment='已覆盖变更行数')
    uncovered_changed_line_count = Column(Integer, default=0, comment='未覆盖变更行数')
    incremental_line_rate = Column(Numeric(10, 4), comment='增量行覆盖率')
    uncovered_lines = Column(JSONB, server_default=text("'[]'::jsonb"), comment='未覆盖变更行列表JSON')
    detail_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='文件级覆盖率详情JSON')
    ai_risk_json = Column(JSONB, server_default=text("'{}'::jsonb"), comment='AI未覆盖风险分析JSON')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')


class PreciseQualityGate(Base):
    __tablename__ = 'precise_quality_gate'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(BigInteger, nullable=False, comment='变更分析ID')
    gate_status = Column(String(32), comment='门禁状态')
    line_rate_threshold = Column(Numeric(10, 4), default=80, comment='增量覆盖率阈值')
    actual_line_rate = Column(Numeric(10, 4), comment='实际增量覆盖率')
    p0_case_pass_rate = Column(Numeric(10, 4), comment='P0推荐用例通过率')
    p1_case_pass_rate = Column(Numeric(10, 4), comment='P1推荐用例通过率')
    risk_level = Column(String(32), comment='综合风险等级')
    block_reasons = Column(JSONB, server_default=text("'[]'::jsonb"), comment='阻断原因JSON')
    suggestions = Column(JSONB, server_default=text("'[]'::jsonb"), comment='处理建议JSON')
    ai_conclusion = Column(Text, comment='AI结论')
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'), comment='更新时间')
    is_delete = Column(SmallInteger, default=0, comment='软删除标记：0未删除 1已删除')
