<template>
  <div class="ai-platform-page">
    <page-section title="AI 测试中枢">
      <template slot="extra">
        <el-button size="small" icon="el-icon-refresh" @click="refreshCurrent">刷新</el-button>
      </template>
      <div class="hero-panel">
        <div>
          <div class="hero-title">Agent、Tool、MCP、Skill Flow 的统一编排入口</div>
          <div class="hero-desc">把风险分析、测试推荐、自动化执行和报告沉淀串成一个可追溯的智能测试闭环。</div>
        </div>
        <div class="hero-metrics">
          <div class="metric-card"><b>{{ agentTotal }}</b><span>Agents</span></div>
          <div class="metric-card"><b>{{ toolTotal }}</b><span>Tools</span></div>
          <div class="metric-card"><b>{{ taskTotal }}</b><span>Tasks</span></div>
          <div class="metric-card"><b>{{ reportTotal }}</b><span>Reports</span></div>
        </div>
      </div>
    </page-section>

    <el-tabs v-model="activeTab" type="border-card" @tab-click="handleTabClick">
      <el-tab-pane label="Agent 注册中心" name="agent">
        <div class="toolbar">
          <el-input v-model.trim="agentQuery.keyword" size="small" clearable placeholder="搜索 Agent" class="search-input" @keyup.enter.native="fetchAgents"></el-input>
          <el-select v-model="agentQuery.status" size="small" clearable placeholder="状态" class="status-select">
            <el-option label="启用" :value="1"></el-option>
            <el-option label="停用" :value="2"></el-option>
            <el-option label="草稿" :value="3"></el-option>
          </el-select>
          <el-button type="primary" size="small" @click="fetchAgents">查询</el-button>
          <el-button size="small" @click="openAgentDialog()">新建 Agent</el-button>
          <el-button size="small" @click="openAgentExecutionDialog()">执行记录</el-button>
        </div>
        <el-table v-loading="agentLoading" :data="agents" border style="width: 100%;">
          <el-table-column prop="agentCode" label="编码" min-width="140" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="name" label="名称" min-width="150"></el-table-column>
          <el-table-column prop="entrypoint" label="入口命令" min-width="180" show-overflow-tooltip></el-table-column>
          <el-table-column prop="timeoutSeconds" label="超时(s)" width="90"></el-table-column>
          <el-table-column prop="status" label="状态" width="90"><template slot-scope="scope">{{ statusText(scope.row.status) }}</template></el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openAgentDialog(scope.row)">编辑</el-button>
              <el-button type="text" @click="openRunDialog('agent', scope.row)">执行</el-button>
              <el-button type="text" style="color: #F56C6C;" @click="removeAgent(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="测试工具市场" name="tool">
        <div class="toolbar">
          <el-input v-model.trim="toolQuery.keyword" size="small" clearable placeholder="搜索工具" class="search-input" @keyup.enter.native="fetchTools"></el-input>
          <el-select v-model="toolQuery.toolType" size="small" clearable filterable allow-create default-first-option placeholder="工具类型" class="status-select">
            <el-option v-for="item in toolTypeOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
          </el-select>
          <el-button type="primary" size="small" @click="fetchTools">查询</el-button>
          <el-button size="small" @click="openToolDialog()">新建工具</el-button>
          <el-button size="small" @click="openRecordDialog('tool')">执行记录</el-button>
        </div>
        <el-table v-loading="toolLoading" :data="tools" border style="width: 100%;">
          <el-table-column prop="toolCode" label="编码" min-width="140" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="name" label="名称" min-width="150"></el-table-column>
          <el-table-column prop="toolType" label="类型" width="100"></el-table-column>
          <el-table-column prop="commandTemplate" label="命令模板" min-width="260" show-overflow-tooltip></el-table-column>
          <el-table-column prop="status" label="状态" width="90"><template slot-scope="scope">{{ statusText(scope.row.status) }}</template></el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openToolDialog(scope.row)">编辑</el-button>
              <el-button type="text" @click="openRunDialog('tool', scope.row)">执行</el-button>
              <el-button type="text" style="color: #F56C6C;" @click="removeTool(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="MCP 连接" name="mcp">
        <div class="toolbar">
          <el-input v-model.trim="mcpQuery.keyword" size="small" clearable placeholder="搜索 MCP" class="search-input" @keyup.enter.native="fetchMcps"></el-input>
          <el-button type="primary" size="small" @click="fetchMcps">查询</el-button>
          <el-button size="small" @click="openMcpDialog()">新建连接</el-button>
          <el-button size="small" @click="openRecordDialog('mcp')">调用日志</el-button>
        </div>
        <el-table v-loading="mcpLoading" :data="mcps" border style="width: 100%;">
          <el-table-column prop="connectorCode" label="编码" min-width="140" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="name" label="名称" min-width="150"></el-table-column>
          <el-table-column prop="connectorType" label="类型" width="120"></el-table-column>
          <el-table-column prop="endpoint" label="地址" min-width="220" show-overflow-tooltip></el-table-column>
          <el-table-column prop="status" label="状态" width="90"><template slot-scope="scope">{{ statusText(scope.row.status) }}</template></el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openMcpDialog(scope.row)">编辑</el-button>
              <el-button type="text" @click="callMcp(scope.row)">测试</el-button>
              <el-button type="text" style="color: #F56C6C;" @click="removeMcp(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="Skill Flow" name="flow">
        <div class="toolbar">
          <el-input v-model.trim="flowQuery.keyword" size="small" clearable placeholder="搜索 Flow" class="search-input" @keyup.enter.native="fetchFlows"></el-input>
          <el-button type="primary" size="small" @click="fetchFlows">查询</el-button>
          <el-button size="small" @click="openFlowDialog()">新建 Flow</el-button>
          <el-button size="small" @click="openRecordDialog('flow')">执行记录</el-button>
        </div>
        <el-table v-loading="flowLoading" :data="flows" border style="width: 100%;">
          <el-table-column prop="flowCode" label="编码" min-width="140" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="name" label="名称" min-width="160"></el-table-column>
          <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip></el-table-column>
          <el-table-column prop="status" label="状态" width="90"><template slot-scope="scope">{{ statusText(scope.row.status) }}</template></el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="openFlowDialog(scope.row)">编辑</el-button>
              <el-button type="text" @click="executeFlow(scope.row)">试运行</el-button>
              <el-button type="text" style="color: #F56C6C;" @click="removeFlow(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="智能测试任务" name="task">
        <div class="toolbar">
          <el-input v-model.trim="taskQuery.keyword" size="small" clearable placeholder="搜索任务" class="search-input" @keyup.enter.native="fetchTasks"></el-input>
          <el-button type="primary" size="small" @click="fetchTasks">查询</el-button>
          <el-button size="small" @click="openTaskDialog()">新建任务</el-button>
        </div>
        <el-table v-loading="taskLoading" :data="tasks" border style="width: 100%;">
          <el-table-column prop="taskNo" label="任务号" min-width="160" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="sourceType" label="来源" width="120"></el-table-column>
          <el-table-column prop="taskType" label="类型" width="140"></el-table-column>
          <el-table-column prop="status" label="状态" width="120"></el-table-column>
          <el-table-column prop="createdTime" label="创建时间" min-width="160"></el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" @click="executeTask(scope.row)">执行</el-button>
              <el-button type="text" @click="openTaskDetail(scope.row)">结果</el-button>
              <el-button type="text" @click="cancelTask(scope.row)">取消</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="AI 报告" name="report">
        <div class="toolbar">
          <el-input v-model.trim="reportQuery.keyword" size="small" clearable placeholder="搜索报告" class="search-input" @keyup.enter.native="fetchReports"></el-input>
          <el-button type="primary" size="small" @click="fetchReports">查询</el-button>
          <el-button size="small" @click="openReportDialog()">生成报告</el-button>
        </div>
        <el-table v-loading="reportLoading" :data="reports" border style="width: 100%;">
          <el-table-column prop="reportNo" label="报告号" min-width="160" show-overflow-tooltip></el-table-column>
          <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
          <el-table-column prop="title" label="标题" min-width="220"></el-table-column>
          <el-table-column prop="reportType" label="类型" width="120"></el-table-column>
          <el-table-column prop="riskLevel" label="风险" width="100"></el-table-column>
          <el-table-column prop="createdTime" label="创建时间" min-width="160"></el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template slot-scope="scope"><el-button type="text" @click="openReportDetail(scope.row)">查看</el-button></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog :title="agentForm.id ? '编辑 Agent' : '新建 Agent'" :visible.sync="agentDialogVisible" width="680px">
      <el-form :model="agentForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="agentForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(agentForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="agentForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(agentForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="编码"><el-input v-model.trim="agentForm.agentCode"></el-input></el-form-item>
        <el-form-item label="名称"><el-input v-model.trim="agentForm.name"></el-input></el-form-item>
        <el-form-item label="类型"><el-select v-model="agentForm.agentType" style="width: 100%;"><el-option label="coding-agent" :value="1"></el-option><el-option label="qa-agent" :value="2"></el-option><el-option label="security-agent" :value="3"></el-option><el-option label="report-agent" :value="4"></el-option></el-select></el-form-item>
        <el-form-item label="入口命令"><el-input v-model.trim="agentForm.entrypoint" placeholder="例如 python --version"></el-input></el-form-item>
        <el-form-item label="版本"><el-input v-model.trim="agentForm.version"></el-input></el-form-item>
        <el-form-item label="说明"><el-input v-model="agentForm.description" type="textarea" :rows="3"></el-input></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="agentForm.status"><el-radio :label="1">启用</el-radio><el-radio :label="2">停用</el-radio><el-radio :label="3">草稿</el-radio></el-radio-group></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="agentDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitAgent">保存</el-button></span>
    </el-dialog>

    <el-dialog :title="toolForm.id ? '编辑工具' : '新建工具'" :visible.sync="toolDialogVisible" width="720px">
      <el-form :model="toolForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="toolForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(toolForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="toolForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(toolForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="编码"><el-input v-model.trim="toolForm.toolCode"></el-input></el-form-item>
        <el-form-item label="名称"><el-input v-model.trim="toolForm.name"></el-input></el-form-item>
        <el-form-item label="类型"><el-select v-model="toolForm.toolType" filterable allow-create default-first-option placeholder="请选择或输入工具类型" style="width: 100%;"><el-option v-for="item in toolTypeOptions" :key="item.value" :label="item.label" :value="item.value"></el-option></el-select></el-form-item>
        <el-form-item label="命令模板"><el-input v-model="toolForm.commandTemplate" type="textarea" :rows="3" placeholder="pytest {test_path}"></el-input></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="toolForm.status"><el-radio :label="1">启用</el-radio><el-radio :label="2">停用</el-radio><el-radio :label="3">草稿</el-radio></el-radio-group></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="toolDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitTool">保存</el-button></span>
    </el-dialog>

    <el-dialog :title="mcpForm.id ? '编辑 MCP' : '新建 MCP'" :visible.sync="mcpDialogVisible" width="680px">
      <el-form :model="mcpForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="mcpForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(mcpForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="mcpForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(mcpForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="编码"><el-input v-model.trim="mcpForm.connectorCode"></el-input></el-form-item>
        <el-form-item label="名称"><el-input v-model.trim="mcpForm.name"></el-input></el-form-item>
        <el-form-item label="类型"><el-input v-model.trim="mcpForm.connectorType" placeholder="github/jira/db/log"></el-input></el-form-item>
        <el-form-item label="地址"><el-input v-model.trim="mcpForm.endpoint"></el-input></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="mcpForm.status"><el-radio :label="1">启用</el-radio><el-radio :label="2">停用</el-radio><el-radio :label="3">草稿</el-radio></el-radio-group></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="mcpDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitMcp">保存</el-button></span>
    </el-dialog>

    <el-dialog :title="flowForm.id ? '编辑 Flow' : '新建 Flow'" :visible.sync="flowDialogVisible" width="720px">
      <el-form :model="flowForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="flowForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(flowForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="flowForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(flowForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="编码"><el-input v-model.trim="flowForm.flowCode"></el-input></el-form-item>
        <el-form-item label="名称"><el-input v-model.trim="flowForm.name"></el-input></el-form-item>
        <el-form-item label="说明"><el-input v-model="flowForm.description" type="textarea" :rows="3"></el-input></el-form-item>
        <el-form-item label="Flow JSON"><el-input v-model="flowForm.flowDefinitionText" type="textarea" :rows="5" placeholder='{"steps":[]}'></el-input></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="flowForm.status"><el-radio :label="1">启用</el-radio><el-radio :label="2">停用</el-radio><el-radio :label="3">草稿</el-radio></el-radio-group></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="flowDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitFlow">保存</el-button></span>
    </el-dialog>

    <el-dialog title="新建智能测试任务" :visible.sync="taskDialogVisible" width="680px">
      <el-form :model="taskForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="taskForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(taskForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="taskForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(taskForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="来源类型"><el-input v-model.trim="taskForm.sourceType" placeholder="manual/pr/requirement"></el-input></el-form-item>
        <el-form-item label="任务类型"><el-input v-model.trim="taskForm.taskType" placeholder="risk-analysis/regression/agent-run"></el-input></el-form-item>
        <el-form-item label="输入参数"><el-input v-model="taskForm.inputPayloadText" type="textarea" :rows="5" placeholder='{"requirement":"..."}'></el-input></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="taskDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitTask">保存</el-button></span>
    </el-dialog>

    <el-dialog title="生成 AI 报告" :visible.sync="reportDialogVisible" width="680px">
      <el-form :model="reportForm" label-width="100px" size="small">
        <el-form-item label="产品"><el-select v-model="reportForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleProductChange(reportForm)"><el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="项目"><el-select v-model="reportForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" @change="handleProjectChange(reportForm)"><el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option></el-select></el-form-item>
        <el-form-item label="标题"><el-input v-model.trim="reportForm.title"></el-input></el-form-item>
        <el-form-item label="报告类型"><el-input v-model.trim="reportForm.reportType" placeholder="risk/quality/execution"></el-input></el-form-item>
        <el-form-item label="内容"><el-input v-model="reportForm.contentText" type="textarea" :rows="6" placeholder='{"summary":"..."}'></el-input></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="reportDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitReport">保存</el-button></span>
    </el-dialog>

    <el-dialog title="执行配置" :visible.sync="runDialogVisible" width="680px">
      <el-form :model="runForm" label-width="100px" size="small">
        <el-form-item label="产品名称"><el-input v-model="runForm.productName" disabled></el-input></el-form-item>
        <el-form-item label="项目名称"><el-input v-model="runForm.projectName" disabled></el-input></el-form-item>
        <el-form-item label="工作区"><el-input v-model.trim="runForm.workspacePath" placeholder="D:\\zhyy\\effekt-interface"></el-input></el-form-item>
        <el-form-item label="命令/参数"><el-input v-model="runForm.command" type="textarea" :rows="3" placeholder="Agent 可填命令；Tool 使用命令模板"></el-input></el-form-item>
        <el-form-item label="输入 JSON"><el-input v-model="runForm.inputPayloadText" type="textarea" :rows="5" placeholder='{"test_path":"tests"}'></el-input></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="runDialogVisible=false">取消</el-button><el-button type="primary" size="small" @click="submitRun">执行</el-button></span>
    </el-dialog>

    <el-dialog title="Agent 执行记录" :visible.sync="agentExecutionDialogVisible" width="1100px">
      <div class="toolbar">
        <el-input v-model.trim="agentExecutionQuery.agentId" size="small" clearable placeholder="Agent ID" class="status-select"></el-input>
        <el-input v-model.trim="agentExecutionQuery.projectId" size="small" clearable placeholder="项目 ID" class="status-select"></el-input>
        <el-select v-model="agentExecutionQuery.status" size="small" clearable placeholder="状态" class="status-select">
          <el-option label="执行中" value="running"></el-option>
          <el-option label="成功" value="success"></el-option>
          <el-option label="失败" value="failed"></el-option>
          <el-option label="取消" value="canceled"></el-option>
        </el-select>
        <el-button type="primary" size="small" @click="fetchAgentExecutions">查询</el-button>
      </div>
      <el-table v-loading="agentExecutionLoading" :data="agentExecutions" border style="width: 100%;">
        <el-table-column prop="executionNo" label="执行编号" min-width="170" show-overflow-tooltip></el-table-column>
        <el-table-column prop="agentName" label="Agent" min-width="140" show-overflow-tooltip></el-table-column>
        <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="commandSnapshot" label="命令" min-width="220" show-overflow-tooltip></el-table-column>
        <el-table-column prop="status" label="状态" width="100"></el-table-column>
        <el-table-column prop="durationSeconds" label="耗时(s)" width="90"></el-table-column>
        <el-table-column prop="createdTime" label="创建时间" min-width="160"></el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template slot-scope="scope"><el-button type="text" @click="openExecutionDetail(scope.row)">详情</el-button></template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <el-pagination small layout="total, prev, pager, next" :current-page.sync="agentExecutionQuery.page" :page-size="agentExecutionQuery.limit" :total="agentExecutionTotal" @current-change="fetchAgentExecutions"></el-pagination>
      </div>
    </el-dialog>

    <el-dialog :title="recordDialogTitle" :visible.sync="recordDialogVisible" width="1100px">
      <div class="toolbar">
        <el-input v-model.trim="recordQuery.relatedId" size="small" clearable :placeholder="recordRelatedPlaceholder" class="status-select"></el-input>
        <el-input v-model.trim="recordQuery.projectId" size="small" clearable placeholder="项目 ID" class="status-select"></el-input>
        <el-select v-model="recordQuery.status" size="small" clearable placeholder="状态" class="status-select">
          <el-option label="执行中" value="running"></el-option>
          <el-option label="成功" value="success"></el-option>
          <el-option label="失败" value="failed"></el-option>
          <el-option label="取消" value="canceled"></el-option>
        </el-select>
        <el-button type="primary" size="small" @click="fetchRecords">查询</el-button>
      </div>
      <el-table v-loading="recordLoading" :data="records" border style="width: 100%;">
        <el-table-column prop="recordNo" label="编号" min-width="170" show-overflow-tooltip></el-table-column>
        <el-table-column prop="name" label="对象" min-width="140" show-overflow-tooltip></el-table-column>
        <el-table-column prop="productName" label="产品名称" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="projectName" label="项目名称" min-width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="commandSnapshot" label="命令/动作" min-width="220" show-overflow-tooltip></el-table-column>
        <el-table-column prop="status" label="状态" width="100"></el-table-column>
        <el-table-column prop="durationSeconds" label="耗时(s)" width="90"></el-table-column>
        <el-table-column prop="createdTime" label="创建时间" min-width="160"></el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template slot-scope="scope"><el-button type="text" @click="openRecordDetail(scope.row)">详情</el-button></template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <el-pagination small layout="total, prev, pager, next" :current-page.sync="recordQuery.page" :page-size="recordQuery.limit" :total="recordTotal" @current-change="fetchRecords"></el-pagination>
      </div>
    </el-dialog>

    <el-dialog title="执行详情" :visible.sync="executionDetailDialogVisible" width="760px">
      <el-descriptions :column="2" border size="small" v-if="executionDetail">
        <el-descriptions-item label="执行编号">{{ executionDetail.executionNo }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ executionDetail.status }}</el-descriptions-item>
        <el-descriptions-item label="产品名称">{{ executionDetail.productName }}</el-descriptions-item>
        <el-descriptions-item label="项目名称">{{ executionDetail.projectName }}</el-descriptions-item>
        <el-descriptions-item label="工作区" :span="2">{{ executionDetail.workspacePath }}</el-descriptions-item>
        <el-descriptions-item label="命令" :span="2">{{ executionDetail.commandSnapshot }}</el-descriptions-item>
        <el-descriptions-item label="stdout" :span="2">{{ executionDetail.stdoutPath || '-' }}</el-descriptions-item>
        <el-descriptions-item label="stderr" :span="2">{{ executionDetail.stderrPath || '-' }}</el-descriptions-item>
        <el-descriptions-item label="错误" :span="2">{{ executionDetail.errorMessage || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-input class="detail-json" type="textarea" :rows="10" readonly :value="executionDetailText"></el-input>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getAiAgentList, createAiAgent, updateAiAgent, deleteAiAgent, executeAiAgent, getAiAgentExecutionList, getAiAgentExecutionDetail,
  getAiToolList, createAiTool, updateAiTool, deleteAiTool, executeAiTool, getAiToolExecutionList, getAiToolExecutionDetail,
  getAiMcpList, createAiMcp, updateAiMcp, deleteAiMcp, callAiMcp, getAiMcpCallLogList, getAiMcpCallLogDetail,
  getAiFlowList, createAiFlow, updateAiFlow, deleteAiFlow, executeAiFlow, getAiFlowExecutionList, getAiFlowExecutionDetail,
  getAiTaskList, getAiTaskDetail, createAiTask, executeAiTask, cancelAiTask,
  getAiReportList, getAiReportDetail, createAiReport
} from '@/api/aiPlatformApi'

const normalizeAiRow = row => Object.assign({}, row, {
  recordNo: row.executionNo || row.execution_no || row.callNo || row.call_no || row.logNo || row.log_no || row.id,
  name: row.name || row.toolName || row.tool_name || row.agentName || row.agent_name || row.connectorName || row.connector_name || row.flowName || row.flow_name || row.action || '-',
  agentCode: row.agentCode || row.agent_code,
  agentType: row.agentType || row.agent_type,
  toolCode: row.toolCode || row.tool_code,
  toolType: row.toolType || row.tool_type,
  commandTemplate: row.commandTemplate || row.command_template,
  connectorCode: row.connectorCode || row.connector_code,
  connectorType: row.connectorType || row.connector_type,
  flowCode: row.flowCode || row.flow_code,
  flowDefinition: row.flowDefinition || row.flow_definition,
  taskNo: row.taskNo || row.task_no,
  taskType: row.taskType || row.task_type,
  sourceType: row.sourceType || row.source_type,
  reportNo: row.reportNo || row.report_no,
  reportType: row.reportType || row.report_type,
  riskLevel: row.riskLevel || row.risk_level,
  executionNo: row.executionNo || row.execution_no,
  agentId: row.agentId || row.agent_id,
  agentName: row.agentName || row.agent_name,
  toolId: row.toolId || row.tool_id,
  toolName: row.toolName || row.tool_name,
  connectorId: row.connectorId || row.connector_id,
  connectorName: row.connectorName || row.connector_name,
  flowId: row.flowId || row.flow_id,
  flowName: row.flowName || row.flow_name,
  workspacePath: row.workspacePath || row.workspace_path,
  taskType: row.taskType || row.task_type,
  inputPayload: row.inputPayload || row.input_payload,
  commandSnapshot: row.commandSnapshot || row.command_snapshot || row.action || row.method,
  stdoutPath: row.stdoutPath || row.stdout_path,
  stderrPath: row.stderrPath || row.stderr_path,
  resultPayload: row.resultPayload || row.result_payload,
  errorMessage: row.errorMessage || row.error_message,
  durationSeconds: row.durationSeconds || row.duration_seconds,
  createdTime: row.createdTime || row.created_time,
  updatedTime: row.updatedTime || row.updated_time
})
const listData = res => {
  const data = res && res.data ? res.data : res || {}
  return { list: (data.list || data.items || []).map(normalizeAiRow), total: Number(data.total || 0) }
}
const parseJson = text => {
  if (!text) return {}
  try { return JSON.parse(text) } catch (e) { throw new Error('JSON 格式不正确') }
}
const jsonText = value => JSON.stringify(value || {}, null, 2)
const defaultAgent = () => ({ productId: '', productName: '', projectId: '', projectName: '', agentCode: '', name: '', agentType: 2, entrypoint: '', version: '', description: '', status: 1 })
const defaultTool = () => ({ productId: '', productName: '', projectId: '', projectName: '', toolCode: '', name: '', toolType: 'unit', commandTemplate: '', status: 1 })
const defaultMcp = () => ({ productId: '', productName: '', projectId: '', projectName: '', connectorCode: '', name: '', connectorType: '', endpoint: '', status: 1 })
const defaultFlow = () => ({ productId: '', productName: '', projectId: '', projectName: '', flowCode: '', name: '', description: '', flowDefinitionText: '{\n  "steps": []\n}', status: 1 })
const defaultTask = () => ({ productId: '', productName: '', projectId: '', projectName: '', sourceType: 'manual', taskType: 'pr_risk', inputPayloadText: '{}' })
const defaultReport = () => ({ productId: '', productName: '', projectId: '', projectName: '', title: '', reportType: 'quality', contentText: '{}' })

export default {
  name: 'AiPlatform',
  components: { PageSection },
  data() {
    return {
      activeTab: 'agent',
      agentLoading: false,
      toolLoading: false,
      mcpLoading: false,
      flowLoading: false,
      taskLoading: false,
      reportLoading: false,
      agents: [], tools: [], mcps: [], flows: [], tasks: [], reports: [],
      productOptions: [],
      projectOptions: [],
      toolTypeOptions: [
        { label: '单元测试', value: 'unit' },
        { label: '接口测试', value: 'api' },
        { label: '端到端测试', value: 'e2e' },
        { label: '安全测试', value: 'security' },
        { label: '大模型测试', value: 'llm' }
      ],
      agentTotal: 0, toolTotal: 0, taskTotal: 0, reportTotal: 0,
      agentQuery: { keyword: '', status: '', page: 1, limit: 20 },
      toolQuery: { keyword: '', toolType: '', page: 1, limit: 20 },
      mcpQuery: { keyword: '', page: 1, limit: 20 },
      flowQuery: { keyword: '', page: 1, limit: 20 },
      taskQuery: { keyword: '', page: 1, limit: 20 },
      reportQuery: { keyword: '', page: 1, limit: 20 },
      agentDialogVisible: false,
      toolDialogVisible: false,
      mcpDialogVisible: false,
      flowDialogVisible: false,
      taskDialogVisible: false,
      reportDialogVisible: false,
      runDialogVisible: false,
      agentExecutionDialogVisible: false,
      recordDialogVisible: false,
      executionDetailDialogVisible: false,
      agentExecutionLoading: false,
      recordLoading: false,
      recordMode: '',
      agentForm: defaultAgent(),
      toolForm: defaultTool(),
      mcpForm: defaultMcp(),
      flowForm: defaultFlow(),
      taskForm: defaultTask(),
      reportForm: defaultReport(),
      runMode: '',
      runTarget: null,
      runForm: { productName: '', projectName: '', projectId: '', workspacePath: 'D:\\zhyy\\effekt-interface', command: '', inputPayloadText: '{}' },
      agentExecutions: [],
      records: [],
      agentExecutionTotal: 0,
      recordTotal: 0,
      agentExecutionQuery: { agentId: '', projectId: '', status: '', page: 1, limit: 10 },
      recordQuery: { relatedId: '', projectId: '', status: '', page: 1, limit: 10 },
      executionDetail: null
    }
  },
  mounted() {
    this.fetchProductOptions()
    this.fetchAllSummary()
    this.fetchAgents()
  },
  computed: {
    executionDetailText() {
      return this.executionDetail ? JSON.stringify(this.executionDetail, null, 2) : ''
    },
    recordDialogTitle() {
      return { tool: '工具执行记录', mcp: 'MCP 调用日志', flow: 'Flow 执行记录' }[this.recordMode] || '执行记录'
    },
    recordRelatedPlaceholder() {
      return { tool: '工具 ID', mcp: 'MCP ID', flow: 'Flow ID' }[this.recordMode] || '对象 ID'
    }
  },
  methods: {
    statusText(status) {
      return { 1: '启用', 2: '停用', 3: '草稿' }[Number(status)] || status || '-'
    },
    fetchProductOptions() {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.productOptions = data.items || data.list || data.data || []
      }).catch(() => { this.productOptions = [] })
    },
    fetchProjectOptions(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, productId, product_id: productId, status: 1 }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.projectOptions = data.items || data.list || data.data || []
      }).catch(() => { this.projectOptions = [] })
    },
    applyProductProject(form, row) {
      const productId = row ? (row.productId || row.product_id || '') : ''
      const projectId = row ? (row.projectId || row.project_id || '') : ''
      form.productId = productId
      form.productName = row ? (row.productName || row.product_name || '') : ''
      form.projectId = projectId
      form.projectName = row ? (row.projectName || row.project_name || '') : ''
      if (productId) this.fetchProjectOptions(productId)
      else this.projectOptions = []
      return form
    },
    handleProductChange(form) {
      const product = this.productOptions.find(item => String(item.id) === String(form.productId))
      form.productName = product ? product.name : ''
      form.projectId = ''
      form.projectName = ''
      this.fetchProjectOptions(form.productId)
    },
    handleProjectChange(form) {
      const project = this.projectOptions.find(item => String(item.id) === String(form.projectId))
      form.projectName = project ? project.name : ''
    },
    buildPayload(form, extra) {
      return Object.assign({}, form, extra || {}, {
        product_id: form.productId,
        product_name: form.productName,
        project_id: form.projectId,
        project_name: form.projectName
      })
    },
    handleTabClick() { this.refreshCurrent() },
    refreshCurrent() {
      const map = { agent: this.fetchAgents, tool: this.fetchTools, mcp: this.fetchMcps, flow: this.fetchFlows, task: this.fetchTasks, report: this.fetchReports }
      return map[this.activeTab] && map[this.activeTab]()
    },
    fetchAllSummary() {
      this.fetchAgents(false)
      this.fetchTools(false)
      this.fetchTasks(false)
      this.fetchReports(false)
    },
    fetchAgents(showLoading = true) {
      this.agentLoading = !!showLoading
      return getAiAgentList(this.agentQuery).then(res => {
        const ret = listData(res)
        this.agents = ret.list
        this.agentTotal = ret.total
      }).catch(() => { this.agents = [] }).finally(() => { this.agentLoading = false })
    },
    fetchTools(showLoading = true) {
      this.toolLoading = !!showLoading
      return getAiToolList(this.toolQuery).then(res => {
        const ret = listData(res)
        this.tools = ret.list
        this.toolTotal = ret.total
      }).catch(() => { this.tools = [] }).finally(() => { this.toolLoading = false })
    },
    fetchMcps() {
      this.mcpLoading = true
      return getAiMcpList(this.mcpQuery).then(res => { this.mcps = listData(res).list }).catch(() => { this.mcps = [] }).finally(() => { this.mcpLoading = false })
    },
    fetchFlows() {
      this.flowLoading = true
      return getAiFlowList(this.flowQuery).then(res => { this.flows = listData(res).list }).catch(() => { this.flows = [] }).finally(() => { this.flowLoading = false })
    },
    fetchTasks(showLoading = true) {
      this.taskLoading = !!showLoading
      return getAiTaskList(this.taskQuery).then(res => {
        const ret = listData(res)
        this.tasks = ret.list
        this.taskTotal = ret.total
      }).catch(() => { this.tasks = [] }).finally(() => { this.taskLoading = false })
    },
    fetchReports(showLoading = true) {
      this.reportLoading = !!showLoading
      return getAiReportList(this.reportQuery).then(res => {
        const ret = listData(res)
        this.reports = ret.list
        this.reportTotal = ret.total
      }).catch(() => { this.reports = [] }).finally(() => { this.reportLoading = false })
    },
    openAgentDialog(row) { this.agentForm = this.applyProductProject(Object.assign(defaultAgent(), row || {}), row); this.agentDialogVisible = true },
    submitAgent() {
      const api = this.agentForm.id ? updateAiAgent : createAiAgent
      api(this.buildPayload(this.agentForm)).then(() => { this.$message.success('保存成功'); this.agentDialogVisible = false; this.fetchAgents() })
    },
    removeAgent(row) { this.confirmDelete(() => deleteAiAgent({ agentId: row.id }).then(() => this.fetchAgents())) },
    openToolDialog(row) { this.toolForm = this.applyProductProject(Object.assign(defaultTool(), row || {}), row); this.toolDialogVisible = true },
    submitTool() {
      const api = this.toolForm.id ? updateAiTool : createAiTool
      api(this.buildPayload(this.toolForm)).then(() => { this.$message.success('保存成功'); this.toolDialogVisible = false; this.fetchTools() })
    },
    removeTool(row) { this.confirmDelete(() => deleteAiTool({ toolId: row.id }).then(() => this.fetchTools())) },
    openMcpDialog(row) { this.mcpForm = this.applyProductProject(Object.assign(defaultMcp(), row ? normalizeAiRow(row) : {}), row); this.mcpDialogVisible = true },
    submitMcp() {
      const api = this.mcpForm.id ? updateAiMcp : createAiMcp
      api(this.buildPayload(this.mcpForm)).then(() => { this.$message.success('保存成功'); this.mcpDialogVisible = false; this.fetchMcps() })
    },
    removeMcp(row) { this.confirmDelete(() => deleteAiMcp({ connectorId: row.id }).then(() => this.fetchMcps())) },
    callMcp(row) {
      callAiMcp({ connectorId: row.id, action: 'test', inputPayload: {} }).then(res => {
        this.$message.success('调用完成')
        this.showInlineResult(res)
        if (this.recordDialogVisible && this.recordMode === 'mcp') this.fetchRecords()
      })
    },
    openFlowDialog(row) {
      this.flowForm = this.applyProductProject(Object.assign(defaultFlow(), row || {}), row)
      this.flowForm.flowDefinitionText = row ? jsonText(row.flowDefinition || row.flow_definition) : defaultFlow().flowDefinitionText
      this.flowDialogVisible = true
    },
    submitFlow() {
      let payload
      try { payload = this.buildPayload(this.flowForm, { flowDefinition: parseJson(this.flowForm.flowDefinitionText) }) } catch (e) { return this.$message.error(e.message) }
      const api = payload.id ? updateAiFlow : createAiFlow
      api(payload).then(() => { this.$message.success('保存成功'); this.flowDialogVisible = false; this.fetchFlows() })
    },
    removeFlow(row) { this.confirmDelete(() => deleteAiFlow({ flowId: row.id }).then(() => this.fetchFlows())) },
    executeFlow(row) {
      executeAiFlow({ flowId: row.id, inputPayload: {} }).then(res => {
        this.$message.success('已触发试运行')
        this.showInlineResult(res)
        if (this.recordDialogVisible && this.recordMode === 'flow') this.fetchRecords()
      })
    },
    openTaskDialog() { this.taskForm = defaultTask(); this.projectOptions = []; this.taskDialogVisible = true },
    submitTask() {
      let inputPayload
      try { inputPayload = parseJson(this.taskForm.inputPayloadText) } catch (e) { return this.$message.error(e.message) }
      createAiTask(this.buildPayload(this.taskForm, { sourcePayload: inputPayload })).then(() => { this.$message.success('保存成功'); this.taskDialogVisible = false; this.fetchTasks() })
    },
    executeTask(row) { executeAiTask({ taskId: row.id }).then(() => { this.$message.success('已执行'); this.fetchTasks(); this.openTaskDetail(row) }) },
    openTaskDetail(row) {
      getAiTaskDetail({ taskId: row.id }).then(res => this.showInlineResult(res))
    },
    cancelTask(row) { cancelAiTask({ taskId: row.id }).then(() => { this.$message.success('已取消'); this.fetchTasks() }) },
    openReportDialog() { this.reportForm = defaultReport(); this.projectOptions = []; this.reportDialogVisible = true },
    submitReport() {
      let content
      try { content = parseJson(this.reportForm.contentText) } catch (e) { return this.$message.error(e.message) }
      createAiReport(this.buildPayload(this.reportForm, { content })).then(res => { this.$message.success('保存成功'); this.reportDialogVisible = false; this.fetchReports(); this.showInlineResult(res) })
    },
    openReportDetail(row) {
      getAiReportDetail({ reportId: row.id }).then(res => this.showInlineResult(res))
    },
    openRunDialog(mode, row) {
      this.runMode = mode
      this.runTarget = row
      this.runForm = {
        productName: row.productName || row.product_name || '',
        projectName: row.projectName || row.project_name || '',
        projectId: row.projectId || row.project_id || '',
        workspacePath: 'D:\\zhyy\\effekt-interface',
        command: mode === 'agent' ? (row.entrypoint || '') : '',
        inputPayloadText: '{}'
      }
      this.runDialogVisible = true
    },
    submitRun() {
      let inputPayload
      try { inputPayload = parseJson(this.runForm.inputPayloadText) } catch (e) { return this.$message.error(e.message) }
      const payload = Object.assign({}, this.runForm, { inputPayload })
      const api = this.runMode === 'agent' ? executeAiAgent : executeAiTool
      if (this.runMode === 'agent') payload.agentId = this.runTarget.id
      if (this.runMode === 'tool') payload.toolId = this.runTarget.id
      api(payload).then(res => {
        this.$message.success('执行完成')
        this.runDialogVisible = false
        this.showInlineResult(res)
        if (this.runMode === 'agent' && this.agentExecutionDialogVisible) this.fetchAgentExecutions()
        if (this.runMode === 'tool' && this.recordDialogVisible && this.recordMode === 'tool') this.fetchRecords()
      })
    },
    openAgentExecutionDialog(row) {
      this.agentExecutionQuery = Object.assign({}, this.agentExecutionQuery, { agentId: row && row.id ? row.id : '', page: 1 })
      this.agentExecutionDialogVisible = true
      this.fetchAgentExecutions()
    },
    fetchAgentExecutions() {
      this.agentExecutionLoading = true
      return getAiAgentExecutionList(this.agentExecutionQuery).then(res => {
        const ret = listData(res)
        this.agentExecutions = ret.list
        this.agentExecutionTotal = ret.total
      }).catch(() => { this.agentExecutions = []; this.agentExecutionTotal = 0 }).finally(() => { this.agentExecutionLoading = false })
    },
    openExecutionDetail(row) {
      getAiAgentExecutionDetail({ executionId: row.id }).then(res => this.openDetailResult(res))
    },
    openRecordDialog(mode) {
      this.recordMode = mode
      this.recordQuery = { relatedId: '', projectId: '', status: '', page: 1, limit: 10 }
      this.recordDialogVisible = true
      this.fetchRecords()
    },
    buildRecordParams() {
      const params = Object.assign({}, this.recordQuery)
      if (this.recordMode === 'tool') params.toolId = params.relatedId
      if (this.recordMode === 'mcp') params.connectorId = params.relatedId
      if (this.recordMode === 'flow') params.flowId = params.relatedId
      delete params.relatedId
      return params
    },
    fetchRecords() {
      const apiMap = { tool: getAiToolExecutionList, mcp: getAiMcpCallLogList, flow: getAiFlowExecutionList }
      const api = apiMap[this.recordMode]
      if (!api) return Promise.resolve()
      this.recordLoading = true
      return api(this.buildRecordParams()).then(res => {
        const ret = listData(res)
        this.records = ret.list
        this.recordTotal = ret.total
      }).catch(() => { this.records = []; this.recordTotal = 0 }).finally(() => { this.recordLoading = false })
    },
    openRecordDetail(row) {
      const apiMap = { tool: getAiToolExecutionDetail, mcp: getAiMcpCallLogDetail, flow: getAiFlowExecutionDetail }
      const paramMap = { tool: { executionId: row.id }, mcp: { logId: row.id }, flow: { executionId: row.id } }
      const api = apiMap[this.recordMode]
      if (!api) return
      api(paramMap[this.recordMode]).then(res => this.openDetailResult(res))
    },
    openDetailResult(res) {
      const data = res && res.data ? res.data : res || {}
      this.executionDetail = normalizeAiRow(data)
      this.executionDetailDialogVisible = true
    },
    showInlineResult(res) {
      this.openDetailResult(res)
    },
    confirmDelete(done) {
      this.$confirm('确认删除该记录？', '提示', { type: 'warning' }).then(() => done()).then(() => this.$message.success('删除成功')).catch(() => {})
    }
  }
}
</script>

<style scoped>
.ai-platform-page {
  --ai-panel-bg: #111827;
  --ai-panel-bg-soft: #172033;
  --ai-control-bg: #1e293b;
  --ai-hover-bg: #1e293b;
  --ai-border: rgba(148, 163, 184, 0.22);
  --ai-text: #f8fafc;
  --ai-muted: #cbd5e1;
  --ai-accent: #1e40af;
  --ai-shadow: rgba(0, 0, 0, 0.18);
  padding: 0;
}
body.theme-light .ai-platform-page {
  --ai-panel-bg: #ffffff;
  --ai-panel-bg-soft: #f8fbff;
  --ai-control-bg: #ffffff;
  --ai-hover-bg: #eaf2ff;
  --ai-border: #dbe5f3;
  --ai-text: #111827;
  --ai-muted: #64748b;
  --ai-accent: #2563eb;
  --ai-shadow: rgba(37, 99, 235, 0.08);
}
.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 96px;
  padding: 18px 22px;
  border: 1px solid var(--ai-border);
  border-radius: 14px;
  color: var(--ai-text);
  background: linear-gradient(135deg, var(--ai-panel-bg-soft) 0%, var(--ai-panel-bg) 100%);
  box-shadow: 0 10px 28px var(--ai-shadow);
}
.hero-title { font-size: 20px; font-weight: 800; margin-bottom: 8px; }
.hero-desc { color: var(--ai-muted); font-size: 13px; }
.hero-metrics { display: flex; gap: 12px; }
.metric-card {
  width: 88px;
  padding: 12px 10px;
  border-radius: 12px;
  text-align: center;
  background: var(--ai-panel-bg);
  border: 1px solid var(--ai-border);
}
.metric-card b { display: block; font-size: 22px; color: var(--ai-text); }
.metric-card span { display: block; margin-top: 4px; font-size: 12px; color: var(--ai-muted); }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.pagination-bar { display: flex; justify-content: flex-end; margin-top: 12px; }
.detail-json { margin-top: 12px; }
.search-input { width: 260px; }
.status-select { width: 140px; }
.ai-platform-page /deep/ .el-tabs--border-card {
  background: var(--ai-panel-bg);
  border-color: var(--ai-border);
  box-shadow: 0 2px 10px var(--ai-shadow);
}
.ai-platform-page /deep/ .el-tabs--border-card > .el-tabs__header {
  background: var(--ai-panel-bg-soft);
  border-bottom-color: var(--ai-border);
}
.ai-platform-page /deep/ .el-tabs--border-card > .el-tabs__header .el-tabs__item {
  color: var(--ai-muted);
}
.ai-platform-page /deep/ .el-tabs--border-card > .el-tabs__header .el-tabs__item.is-active {
  background: var(--ai-panel-bg);
  border-right-color: var(--ai-border);
  border-left-color: var(--ai-border);
  color: var(--ai-accent);
}
.ai-platform-page /deep/ .el-tabs--border-card > .el-tabs__content,
.ai-platform-page /deep/ .el-table,
.ai-platform-page /deep/ .el-table__expanded-cell,
.ai-platform-page /deep/ .el-table tr,
.ai-platform-page /deep/ .el-table td {
  background: var(--ai-panel-bg) !important;
  color: var(--ai-text) !important;
}
.ai-platform-page /deep/ .el-table th {
  background: var(--ai-panel-bg-soft) !important;
  color: var(--ai-text) !important;
}
.ai-platform-page /deep/ .el-table .cell,
.ai-platform-page /deep/ .el-table th > .cell,
.ai-platform-page /deep/ .el-table__body-wrapper {
  color: inherit !important;
}
.ai-platform-page /deep/ .el-table--enable-row-hover .el-table__body tr:hover > td {
  background: var(--ai-hover-bg) !important;
  color: var(--ai-text) !important;
}
.ai-platform-page /deep/ .el-table--border,
.ai-platform-page /deep/ .el-table--group,
.ai-platform-page /deep/ .el-table td,
.ai-platform-page /deep/ .el-table th.is-leaf {
  border-color: var(--ai-border) !important;
}
.ai-platform-page /deep/ .el-input__inner,
.ai-platform-page /deep/ .el-textarea__inner,
.ai-platform-page /deep/ .el-select .el-input__inner {
  background: var(--ai-control-bg);
  border-color: var(--ai-border);
  color: var(--ai-text);
}
.ai-platform-page /deep/ .el-input__inner::placeholder,
.ai-platform-page /deep/ .el-textarea__inner::placeholder {
  color: var(--ai-muted);
}
.ai-platform-page /deep/ .el-input__inner:hover,
.ai-platform-page /deep/ .el-input__inner:focus,
.ai-platform-page /deep/ .el-textarea__inner:hover,
.ai-platform-page /deep/ .el-textarea__inner:focus {
  border-color: var(--ai-accent);
}
.ai-platform-page /deep/ .el-button:not(.el-button--primary):not(.el-button--text) {
  background: var(--ai-control-bg);
  border-color: var(--ai-border);
  color: var(--ai-text);
}
.ai-platform-page /deep/ .el-button:not(.el-button--primary):not(.el-button--text):hover,
.ai-platform-page /deep/ .el-button:not(.el-button--primary):not(.el-button--text):focus {
  background: var(--ai-hover-bg);
  border-color: var(--ai-accent);
  color: var(--ai-accent);
}
.ai-platform-page /deep/ .el-table .el-button--text {
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.ai-platform-page /deep/ .el-table .el-button--text:hover,
.ai-platform-page /deep/ .el-table .el-button--text:focus {
  border: 0;
  background: transparent;
  box-shadow: none;
}
</style>
