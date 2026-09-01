<template>
  <div class="page-wrap">
    <page-section title="用例管理">
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select
            v-model="selectedProductId"
            filterable
            clearable
            placeholder="请选择产品"
            style="width: 220px;"
            @change="handleProductChange"
            @focus="loadProductOptions">
            <el-option
              v-for="item in productOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select
            v-model="selectedProjectId"
            filterable
            clearable
            placeholder="请选择项目"
            style="width: 240px;"
            :disabled="!selectedProductId"
            @change="handleProjectChange">
            <el-option
              v-for="item in projectOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
      </el-form>

      <el-tabs v-model="activeTab" class="case-list-tabs" style="margin-top: 8px;">
        <el-tab-pane label="模块列表" name="modules">
          <div class="module-list-toolbar">
            <el-button
              size="small"
              icon="el-icon-refresh"
              :disabled="!selectedProjectId"
              :loading="moduleLoading"
              @click="refreshModuleList">
              刷新
            </el-button>
            <el-button type="primary" size="small" :disabled="!selectedProjectId" @click="openModuleCreate">新增模块</el-button>
          </div>
          <el-table v-loading="moduleLoading" :data="pagedModuleData" border style="margin-top: 8px;">
            <el-table-column prop="id" label="模块ID" width="100"></el-table-column>
            <el-table-column prop="name" label="模块名称" min-width="160"></el-table-column>
            <el-table-column prop="parent_name" label="父模块名称" min-width="160"></el-table-column>
            <el-table-column prop="sort_order" label="排序" width="90"></el-table-column>
            <el-table-column prop="path" label="路径" min-width="180"></el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" @click="openModuleEdit(scope.row)">编辑</el-button>
                <el-button type="text" style="color: #F56C6C;" @click="removeModule(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="modulePageNo"
              :page-size="modulePageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="moduleTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleModuleSizeChange"
              @current-change="handleModuleCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>

        <el-tab-pane label="用例列表" name="cases">
          <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
            <el-form-item label="用例标题">
              <el-input v-model="queryForm.keyword" clearable style="width: 180px;" @keyup.enter.native="fetchList"></el-input>
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="queryForm.priority" clearable style="width: 100px;">
                <el-option label="P0" :value="0"></el-option>
                <el-option label="P1" :value="1"></el-option>
                <el-option label="P2" :value="2"></el-option>
                <el-option label="P3" :value="3"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="标签">
              <el-input v-model="queryForm.tag" clearable style="width: 140px;" @keyup.enter.native="fetchList"></el-input>
            </el-form-item>
            <el-form-item label="创建人">
              <el-input v-model="queryForm.creator" clearable style="width: 140px;" @keyup.enter.native="fetchList"></el-input>
            </el-form-item>
            <el-form-item label="创建时间">
              <el-date-picker
                v-model="createdTimeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="yyyy-MM-dd"
                style="width: 260px;"
                @change="handleCreatedTimeChange">
              </el-date-picker>
            </el-form-item>
            <el-form-item class="more-filter-item">
              <el-popover
                v-model="moreFilterVisible"
                placement="bottom-start"
                width="620"
                trigger="click">
                <div class="more-filter-wrap">
                  <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
                    <el-form-item label="用例编号">
                      <el-input
                        v-model="queryForm.caseKeysText"
                        type="textarea"
                        :rows="3"
                        clearable
                        placeholder="支持多个编号，逗号/空格/换行分隔"
                        style="width: 480px;">
                      </el-input>
                    </el-form-item>
                    <el-form-item label="模块">
                      <el-select v-model="queryForm.moduleId" clearable filterable style="width: 180px;">
                        <el-option
                          v-for="item in flatModuleOptions"
                          :key="item.id"
                          :label="item.name"
                          :value="item.id">
                        </el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="类型">
                      <el-select v-model="queryForm.caseType" clearable style="width: 180px;">
                        <el-option label="功能" :value="1"></el-option>
                        <el-option label="性能" :value="2"></el-option>
                        <el-option label="安全" :value="3"></el-option>
                        <el-option label="接口" :value="4"></el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="状态">
                      <el-select v-model="queryForm.status" clearable style="width: 180px;">
                        <el-option label="正常" :value="1"></el-option>
                        <el-option label="已废弃" :value="2"></el-option>
                        <el-option label="评审中" :value="3"></el-option>
                        <el-option label="评审通过" :value="4"></el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="是否自动化">
                      <el-select v-model="queryForm.isAuto" clearable style="width: 180px;">
                        <el-option label="未实现" :value="0"></el-option>
                        <el-option label="已实现" :value="1"></el-option>
                      </el-select>
                    </el-form-item>
                  </el-form>
                  <div class="more-filter-footer">
                    <el-button size="small" @click="moreFilterVisible = false">取消</el-button>
                    <el-button type="primary" size="small" :disabled="!selectedProjectId" @click="applyMoreFilters">搜索</el-button>
                  </div>
                </div>
                <el-button slot="reference" size="small">更多筛选</el-button>
              </el-popover>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :disabled="!selectedProjectId" @click="fetchList">查询</el-button>
            </el-form-item>
            <el-form-item>
              <el-button size="small" @click="resetQuery">重置</el-button>
            </el-form-item>
            <el-form-item class="case-action-buttons-item">
              <el-button type="primary" size="small" :disabled="!selectedProjectId" @click="goEditor()">新建用例</el-button>
              <el-button size="small" :disabled="!selectedProjectId" @click="openCaseImportDialog">导入Excel</el-button>
              <el-button size="small" :disabled="!selectedProjectId" :loading="caseExporting" @click="handleCaseExport">导出Excel</el-button>
              <el-popover
                v-model="columnSettingVisible"
                placement="bottom-end"
                width="300"
                trigger="click">
                <div class="column-setting-wrap">
                  <div class="column-setting-title">自定义列表展示字段</div>
                  <el-checkbox-group v-model="selectedCaseColumnKeys" @change="handleColumnSelectionChange">
                    <el-checkbox v-for="item in allCaseColumns" :key="item.key" :label="item.key">{{ item.label }}</el-checkbox>
                  </el-checkbox-group>
                </div>
                <el-button slot="reference" size="small">自定义列表展示字段</el-button>
              </el-popover>
            </el-form-item>
          </el-form>

          <el-table v-loading="loading" :data="tableData" border style="margin-top: 8px;">
            <el-table-column
              v-for="column in visibleCaseColumns"
              :key="column.key"
              :label="column.label"
              :prop="column.prop"
              :min-width="column.minWidth"
              :width="column.width">
              <template slot-scope="scope">
                <template v-if="column.key === 'tags'">
                  <template v-if="Array.isArray(getCaseColumnValue(scope.row, 'tags'))">
                    <el-tag v-for="tag in getCaseColumnValue(scope.row, 'tags')" :key="tag" size="mini" style="margin-right: 4px;">{{ tag }}</el-tag>
                  </template>
                  <span v-else>{{ formatTags(getCaseColumnValue(scope.row, 'tags')) }}</span>
                </template>
                <template v-else>
                  {{ formatCaseColumnValue(column.key, getCaseColumnValue(scope.row, column.key)) }}
                </template>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" @click="goEditor(scope.row)">编辑</el-button>
                <el-button type="text" @click="handleCopyCase(scope.row)">复制</el-button>
                <el-button type="text" @click="openAutoGenDialog(scope.row)">生成自动化用例</el-button>
                <el-button type="text" style="color: #F56C6C;" @click="remove(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="pageNo"
              :page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="用例脑图" name="case-mindmap">
          <div class="toolbar-wrap">
            <el-button size="small" :disabled="!selectedProjectId" @click="fetchCaseMindmapData">刷新结构</el-button>
            <el-button size="small" :disabled="!selectedProjectId" @click="toggleMindmapCollapsed">{{ mindmapCollapsed ? '展开展示' : '合并展示' }}</el-button>
          </div>
          <div v-loading="caseMindmapLoading" class="mindmap-wrap">
            <el-tree
              v-if="caseMindmapTreeData && caseMindmapTreeData.length > 0"
              ref="mindmapTreeRef"
              :key="mindmapRenderKey"
              :data="caseMindmapTreeData"
              node-key="id"
              :default-expanded-keys="mindmapDefaultExpandedKeys"
              :expand-on-click-node="false"
              @node-expand="handleMindmapNodeExpand"
              :props="{ children: 'children', label: 'name' }"
              class="xmind-tree">
              <div slot-scope="{ data }" class="mindmap-node-wrap">
                <span class="mindmap-node" :class="{
                  'mindmap-node-project': data.nodeTypeLabel === '项目',
                  'mindmap-node-module': data.nodeTypeLabel === '模块',
                  'mindmap-node-case': data.nodeTypeLabel === '用例',
                  'mindmap-node-active': selectedMindmapCase && selectedMindmapCase.id === data.id
                }" @click.stop="handleMindmapNodeClick(data)">
                  <span class="mindmap-node-head">
                    <span class="mindmap-node-title">{{ data.name }}</span>
                    <el-tag
                      v-if="data.nodeTypeLabel === '用例'"
                      size="mini"
                      class="mindmap-node-case-status"
                      :type="formatStatusTagType(data.status)">
                      {{ formatStatus(data.status) || '未知状态' }}
                    </el-tag>
                  </span>
                  <span class="mindmap-node-meta">
                    <el-tag size="mini" :type="data.nodeTypeLabel === '项目' ? 'success' : (data.nodeTypeLabel === '模块' ? 'warning' : 'info')">{{ data.nodeTypeLabel }}</el-tag>
                    <span v-if="data.creator" class="mindmap-meta-text">创建人：{{ data.creator }}</span>
                    <span v-if="data.updatedTime" class="mindmap-meta-text">更新时间：{{ data.updatedTime }}</span>
                  </span>
                </span>
                <div v-if="data.nodeTypeLabel === '用例' && selectedMindmapCase && selectedMindmapCase.id === data.id" class="mindmap-inline-detail">
                  <div class="mindmap-inline-detail-line"></div>
                  <div class="mindmap-inline-detail-card">
                    <div class="mindmap-inline-detail-header">
                      <div class="mindmap-inline-detail-title">用例详情</div>
                      <el-tag size="mini" :type="formatStatusTagType(data.status)">{{ formatStatus(data.status) || '未知状态' }}</el-tag>
                    </div>
                    <template v-if="mindmapCaseEditing">
                      <div class="mindmap-inline-detail-item">
                        <b>前置条件：</b>
                        <el-input v-model="mindmapCaseEditForm.preconditions" type="textarea" :rows="2"></el-input>
                      </div>
                      <div class="mindmap-inline-detail-item">
                        <b>测试步骤：</b>
                        <el-input v-model="mindmapCaseEditForm.steps" type="textarea" :rows="4"></el-input>
                      </div>
                      <div class="mindmap-inline-detail-item">
                        <b>预期结果：</b>
                        <el-input v-model="mindmapCaseEditForm.expectedResults" type="textarea" :rows="2"></el-input>
                      </div>
                      <div class="mindmap-inline-actions">
                        <el-button size="mini" @click="cancelMindmapCaseEdit">取消</el-button>
                        <el-button type="primary" size="mini" :loading="mindmapCaseSaving" @click="saveMindmapCaseEdit">保存</el-button>
                      </div>
                    </template>
                    <template v-else>
                      <div class="mindmap-inline-detail-item"><b>前置条件：</b>{{ data.preconditions || '无' }}</div>
                      <div class="mindmap-inline-detail-item"><b>测试步骤：</b>{{ formatMindmapSteps(data.steps) || '无' }}</div>
                      <div class="mindmap-inline-detail-item"><b>预期结果：</b>{{ data.expectedResults || '无' }}</div>
                      <div class="mindmap-inline-actions">
                        <el-button size="mini" :loading="mindmapCaseReviewing" @click="startMindmapCaseReview">评审</el-button>
                        <el-button type="primary" plain size="mini" @click="startMindmapCaseEdit">编辑</el-button>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </el-tree>
            <div v-else class="mindmap-empty">暂无结构数据</div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI生成用例" name="ai-case-import">
          <div class="ai-case-import-wrap">
            <p class="ai-case-import-tip">
              按条件查询用例；在下方文档列表中勾选要参与生成的文档，可在「技能与业务规则」中多选当前项目的 Skill 与规则；设置生成参数后点击「生成用例」。「导入」为上传 PDF 或新建飞书文档（与文档源「新建」一致）；Excel 导入用例请在「用例列表」Tab 使用「导入Excel」。
            </p>
            <el-form :inline="true" :model="aiQueryForm" size="small" class="ai-case-query-form" @submit.native.prevent>
              <el-form-item label="模块">
                <el-select v-model="aiQueryForm.moduleId" clearable filterable placeholder="全部" style="width: 200px;">
                  <el-option
                    v-for="item in flatModuleOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id">
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="用例标题">
                <el-input v-model="aiQueryForm.keyword" clearable style="width: 160px;" @keyup.enter.native="fetchAiCaseList"></el-input>
              </el-form-item>
              <el-form-item label="优先级">
                <el-select v-model="aiQueryForm.priority" clearable style="width: 100px;">
                  <el-option label="P0" :value="0"></el-option>
                  <el-option label="P1" :value="1"></el-option>
                  <el-option label="P2" :value="2"></el-option>
                  <el-option label="P3" :value="3"></el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="标签">
                <el-input v-model="aiQueryForm.tag" clearable style="width: 120px;" @keyup.enter.native="fetchAiCaseList"></el-input>
              </el-form-item>
              <el-form-item label="创建人">
                <el-input v-model="aiQueryForm.creator" clearable style="width: 120px;" @keyup.enter.native="fetchAiCaseList"></el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :disabled="!selectedProjectId" @click="fetchAiCaseList">查询</el-button>
              </el-form-item>
              <el-form-item>
                <el-button size="small" @click="resetAiQuery">重置</el-button>
              </el-form-item>
              <el-form-item>
                <el-button size="small" :disabled="!selectedProjectId" @click="openAiDocumentCreateDialog">导入</el-button>
              </el-form-item>
              <el-form-item>
                <el-button
                  type="success"
                  size="small"
                  :disabled="!selectedProjectId || aiGenerateLoading"
                  :loading="aiGenerateLoading"
                  @click="handleAiGenerateCases">
                  生成用例
                </el-button>
                <el-button
                  v-if="aiGenerateLoading"
                  type="danger"
                  size="small"
                  plain
                  :loading="aiCancelLoading"
                  :disabled="aiCancelLoading"
                  @click="handleAiCancelGenerate">
                  停止生成
                </el-button>
              </el-form-item>
            </el-form>

            <!-- AI生成用例进度条 -->
            <div v-if="aiGenProgress.visible" class="ai-gen-progress-bar">
              <div class="ai-gen-progress-head">
                <div class="ai-gen-progress-title">
                  <i class="el-icon-loading"></i>
                  <span>AI 正在生成测试用例</span>
                </div>
                <span v-if="aiGenProgress.totalChunks > 0" class="ai-gen-progress-count">
                  第 {{ aiGenProgress.chunkIndex }} / {{ aiGenProgress.totalChunks }} 段
                </span>
              </div>
              <div class="ai-gen-current-module">
                当前生成模块：{{ aiGenProgress.chunkTitle || '正在准备生成任务...' }}
              </div>
              <el-progress
                v-if="aiGenProgress.totalChunks > 0"
                :percentage="Math.round((Math.max(aiGenProgress.chunkIndex - 1, 0) / aiGenProgress.totalChunks) * 100)"
                :status="aiGenProgress.chunkIndex >= aiGenProgress.totalChunks ? 'success' : ''"
                style="margin-bottom: 8px;">
              </el-progress>
              <div v-if="aiGenProgress.casesCount > 0 || aiGenProgress.totalCasesSoFar > 0 || aiGenProgress.totalSkipped > 0" style="color: #67c23a; font-size: 13px;">
                当前测试点生成 {{ aiGenProgress.casesCount || 0 }} 条；累计生成 {{ aiGenProgress.totalCasesSoFar }} 条，已跳过重复 {{ aiGenProgress.totalSkipped || 0 }} 条
              </div>
              <div v-if="aiGenProgress.logs.length > 0" class="ai-gen-log-list">
                <div
                  v-for="(log, index) in aiGenProgress.logs"
                  :key="index"
                  :class="['ai-gen-log-item', 'is-' + (log.level || 'info')]">
                  <span class="ai-gen-log-time">{{ log.time }}</span>
                  <span class="ai-gen-log-agent" v-if="log.agentName">{{ log.agentName }}</span>
                  <span class="ai-gen-log-message">{{ log.message }}</span>
                </div>
              </div>
              <div v-if="aiGenProgress.errors.length > 0" style="color: #e6a23c; font-size: 12px; margin-top: 4px;">
                ⚠ {{ aiGenProgress.errors.length }} 个分段生成失败，其余分段继续中...
              </div>
            </div>

            <div class="ai-gen-params-bar">
              <span class="ai-gen-params-label">生成参数</span>
              <el-select v-model="aiGenForm.priority" size="small" style="width: 100px; margin-left: 8px;">
                <el-option label="P0" :value="1"></el-option>
                <el-option label="P1" :value="2"></el-option>
                <el-option label="P2" :value="3"></el-option>
              </el-select>
              <span class="ai-gen-params-hint">（与接口约定：1-P0 / 2-P1 / 3-P2）</span>
              <span style="margin-left: 16px;">用例类型</span>
              <el-input-number v-model="aiGenForm.caseType" :min="1" :max="99" size="small" style="margin-left: 8px; width: 100px;"></el-input-number>
              <span style="margin-left: 16px;">标签</span>
              <el-select
                v-model="aiGenForm.tags"
                multiple
                filterable
                allow-create
                default-first-option
                size="small"
                placeholder="标签"
                style="margin-left: 8px; width: 220px;">
                <el-option label="AI生成" value="AI生成"></el-option>
              </el-select>
            </div>

            <div class="ai-doc-block">
              <div class="ai-doc-block-title">文档来源（勾选后参与「生成用例」）</div>
              <el-table
                v-loading="aiDocLoading"
                :data="aiDocList"
                border
                size="small"
                max-height="240"
                row-key="id"
                @selection-change="onAiDocSelectionChange">
                <el-table-column type="selection" width="46"></el-table-column>
                <el-table-column prop="id" label="文档ID" width="80"></el-table-column>
                <el-table-column label="类型" width="72">
                  <template slot-scope="scope">
                    <el-tag size="mini" :type="scope.row.type === 2 ? 'warning' : 'info'">{{ scope.row.type === 2 ? '飞书' : 'PDF' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="文件名称" min-width="160" show-overflow-tooltip>
                  <template slot-scope="scope">{{ formatAiDocFileName(scope.row) }}</template>
                </el-table-column>
                <el-table-column label="飞书链接" min-width="200" show-overflow-tooltip>
                  <template slot-scope="scope">{{ scope.row.type === 2 ? (scope.row.source || '—') : '—' }}</template>
                </el-table-column>
                <el-table-column label="操作" width="80" fixed="right" align="center">
                  <template slot-scope="scope">
                    <el-button type="text" size="mini" style="color: #F56C6C;" @click="removeAiDoc(scope.row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="ai-doc-block ai-skill-rule-block">
              <div class="ai-doc-block-title">技能与业务规则（可选，选择后随「生成用例」一并提交）</div>
              <div v-loading="aiSkillRuleLoading" class="ai-skill-rule-selects">
                <el-select
                  v-model="aiGenSelectedSkillIds"
                  multiple
                  filterable
                  clearable
                  collapse-tags
                  placeholder="选择技能（当前项目下全部 Skill）"
                  size="small"
                  style="width: 100%;"
                  :disabled="!projectId">
                  <el-option
                    v-for="s in aiSkillOptions"
                    :key="'ai-sk-' + s.id"
                    :label="formatAiSkillOptionLabel(s)"
                    :value="Number(s.id)">
                  </el-option>
                </el-select>
                <el-select
                  v-model="aiGenSelectedRuleIds"
                  multiple
                  filterable
                  clearable
                  collapse-tags
                  placeholder="选择业务规则（当前项目下全部规则）"
                  size="small"
                  style="width: 100%;"
                  :disabled="!projectId">
                  <el-option
                    v-for="r in aiRuleOptions"
                    :key="'ai-ru-' + r.id"
                    :label="formatAiRuleOptionLabel(r)"
                    :value="Number(r.id)">
                  </el-option>
                </el-select>
              </div>
            </div>

            <div class="ai-case-table-toolbar">
              <div class="ai-case-table-title">用例列表</div>
              <div class="ai-case-table-toolbar-actions">
                <el-button
                  type="primary"
                  size="small"
                  plain
                  :disabled="!projectId || !aiSelectedCases.length"
                  :loading="aiBatchSyncing"
                  @click="batchSyncAiCases">
                  批量同步
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  plain
                  :disabled="!projectId || !aiSelectedCases.length"
                  :loading="aiBatchDeleting"
                  @click="batchRemoveAiCases">
                  批量删除
                </el-button>
              </div>
            </div>
            <el-table
              ref="aiCaseTable"
              v-loading="aiLoading"
              :data="aiTableData"
              border
              row-key="id"
              style="margin-top: 8px;"
              @selection-change="onAiCaseSelectionChange">
              <el-table-column type="selection" width="46"></el-table-column>
              <el-table-column
                label="模块路径"
                prop="module_path"
                min-width="200"
                show-overflow-tooltip>
                <template slot-scope="scope">{{ scope.row.module_path || scope.row.modulePath || '—' }}</template>
              </el-table-column>
              <el-table-column label="模块名称" prop="module_name" min-width="140" show-overflow-tooltip>
                <template slot-scope="scope">
                  {{ formatCaseColumnValue('moduleName', getCaseColumnValue(scope.row, 'moduleName')) }}
                </template>
              </el-table-column>
              <el-table-column
                v-for="column in visibleAiCaseColumnsWithoutModuleName"
                :key="'ai-' + column.key"
                :label="column.label"
                :prop="column.prop"
                :min-width="column.minWidth"
                :width="column.width">
                <template slot-scope="scope">
                  <template v-if="column.key === 'tags'">
                    <template v-if="Array.isArray(getCaseColumnValue(scope.row, 'tags'))">
                      <el-tag v-for="tag in getCaseColumnValue(scope.row, 'tags')" :key="tag" size="mini" style="margin-right: 4px;">{{ tag }}</el-tag>
                    </template>
                    <span v-else>{{ formatTags(getCaseColumnValue(scope.row, 'tags')) }}</span>
                  </template>
                  <template v-else>
                    {{ formatCaseColumnValue(column.key, getCaseColumnValue(scope.row, column.key)) }}
                  </template>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="300" fixed="right">
                <template slot-scope="scope">
                  <el-button type="text" @click="openAiCaseDetail(scope.row)">查看详情</el-button>
                  <el-button type="text" @click="goEditor(scope.row)">编辑</el-button>
                  <el-button type="text" @click="syncAiCase(scope.row)">同步</el-button>
                  <el-button type="text" style="color: #F56C6C;" @click="remove(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="margin-top: 16px; text-align: right;">
              <el-pagination
                :current-page="aiCasePageNo"
                :page-size="aiCasePageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="aiCaseTotal"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleAiCaseSizeChange"
                @current-change="handleAiCaseCurrentChange">
              </el-pagination>
            </div>

            <document-source-panel
              ref="aiDocumentPanel"
              class="document-source-panel-host--hidden"
              :compact="true"
              :product-id="selectedProductId"
              :project-id="selectedProjectId"
              :table-height="360"
              @document-changed="fetchAiDocList">
            </document-source-panel>
          </div>
        </el-tab-pane>
      </el-tabs>
    </page-section>

    <el-dialog :title="moduleDialogMode === 'edit' ? '编辑模块' : '新增模块'" :visible.sync="moduleDialogVisible" width="520px" @close="resetModuleForm">
      <el-form ref="moduleForm" :model="moduleForm" :rules="moduleRules" label-width="100px" size="small">
        <el-form-item label="产品" prop="productId">
          <el-select v-model="moduleForm.productId" filterable clearable placeholder="请选择产品" style="width: 100%;" @change="handleModuleProductChange" @focus="loadProductOptions">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="moduleForm.projectId" filterable clearable placeholder="请选择项目" style="width: 100%;" :disabled="!moduleForm.productId" @change="handleModuleProjectChange">
            <el-option v-for="item in moduleProjectOptions" :key="item.id" :label="item.name" :value="item.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="模块名称" prop="name">
          <el-input v-model="moduleForm.name"></el-input>
        </el-form-item>
        <el-form-item label="父模块">
          <el-select v-model="moduleForm.parentId" filterable placeholder="不选则为根模块" style="width: 100%;" :disabled="!moduleForm.projectId">
            <el-option label="无（根模块）" value="0"></el-option>
            <el-option v-for="item in moduleParentOptions" :key="item.id" :label="item.name" :value="String(item.id)"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input v-model="moduleForm.sortOrder"></el-input>
        </el-form-item>
        <el-form-item label="路径">
          <el-input v-model="moduleForm.path"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button size="small" @click="moduleDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="moduleSubmitting" @click="submitModule">{{ moduleDialogMode === 'edit' ? '保存' : '确定' }}</el-button>
      </span>
    </el-dialog>

    <el-dialog
      title="用例详情"
      :visible.sync="aiCaseDetailVisible"
      width="760px"
      top="6vh"
      append-to-body
      custom-class="case-ai-detail-dialog"
      @closed="resetAiCaseDetailDialog">
      <div v-loading="aiCaseDetailLoading" class="ai-case-detail-wrap">
        <template v-if="!aiCaseDetailLoading && aiCaseDetailRowPresent">
          <div class="ai-case-detail-title">{{ aiCaseDetail.title || '—' }}</div>
          <el-descriptions :column="2" size="small" border class="ai-case-detail-desc">
            <el-descriptions-item label="用例编号">{{ aiCaseDetail.case_key || aiCaseDetail.caseKey || '—' }}</el-descriptions-item>
            <el-descriptions-item label="模块">{{ aiCaseDetail.module_name || aiCaseDetail.moduleName || '—' }}</el-descriptions-item>
            <el-descriptions-item label="优先级">{{ formatPriority(aiCaseDetail.priority) }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ formatCaseType(aiCaseDetail.case_type != null ? aiCaseDetail.case_type : aiCaseDetail.caseType) }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ formatStatus(aiCaseDetail.status) }}</el-descriptions-item>
            <el-descriptions-item label="是否自动化">
              {{ formatIsAuto(aiCaseDetail.is_auto != null ? aiCaseDetail.is_auto : aiCaseDetail.isAuto) }}
            </el-descriptions-item>
            <el-descriptions-item label="创建人" :span="2">
              {{ aiCaseDetail.created_by_name || aiCaseDetail.creator || aiCaseDetail.creator_name || '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">
              {{ aiCaseDetail.created_time || aiCaseDetail.create_time || aiCaseDetail.createdTime || '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="标签" :span="2">
              <template v-if="Array.isArray(aiCaseDetail.tags) && aiCaseDetail.tags.length">
                <el-tag v-for="t in aiCaseDetail.tags" :key="t" size="mini" style="margin-right: 4px;">{{ t }}</el-tag>
              </template>
              <span v-else>{{ formatTags(aiCaseDetail.tags) || '—' }}</span>
            </el-descriptions-item>
          </el-descriptions>
          <div class="ai-case-detail-block">
            <div class="ai-case-detail-label">前置条件</div>
            <div class="ai-case-detail-text">{{ aiCaseDetail.preconditions || '—' }}</div>
          </div>
          <div class="ai-case-detail-block">
            <div class="ai-case-detail-label">测试步骤</div>
            <div class="ai-case-detail-text">{{ formatAiCaseDetailSteps(aiCaseDetail.steps) || '—' }}</div>
          </div>
          <div class="ai-case-detail-block">
            <div class="ai-case-detail-label">预期结果</div>
            <div class="ai-case-detail-text">
              {{ aiCaseDetail.expected_results || aiCaseDetail.expectedResults || '—' }}
            </div>
          </div>
        </template>
        <div v-else-if="!aiCaseDetailLoading && !aiCaseDetailRowPresent" class="ai-case-detail-empty">暂无详情数据</div>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" size="small" @click="aiCaseDetailVisible = false">关闭</el-button>
      </span>
    </el-dialog>

    <el-dialog
      title="生成自动化用例"
      :visible.sync="autoGenDialogVisible"
      width="560px"
      append-to-body
      custom-class="case-auto-gen-dialog"
      @closed="resetAutoGenDialog">
      <el-form ref="autoGenFormRef" :model="autoGenForm" :rules="autoGenRules" label-width="120px" size="small">
        <el-form-item label="当前用例">
          <span class="auto-gen-case-title">{{ autoGenRowTitle }}</span>
        </el-form-item>
        <el-form-item label="生成类型" prop="automationType">
          <el-select v-model="autoGenForm.automationType" placeholder="请选择" style="width: 100%;">
            <el-option label="生成 UI 自动化用例" value="ui"></el-option>
            <el-option label="生成接口自动化用例" value="api"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提示词" prop="prompt">
          <el-input
            v-model="autoGenForm.prompt"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="补充生成要求、风格或约束等，将一并提交给后端">
          </el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button size="small" @click="autoGenDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="autoGenSubmitting" @click="submitAutoGen">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="批量上传" :visible.sync="caseImportDialogVisible" width="780px" @close="resetImportDialog">
      <div class="case-import-panel">
        <div class="case-import-icon">X</div>
        <div class="case-import-title">上传用例</div>
        <div class="case-import-subtitle">仅支持 xlsx、xls 文件，系统将自动解析用例数据</div>
        <el-form class="case-import-form" :model="importForm" label-width="72px" size="small">
          <el-form-item label="产品">
            <el-select
              v-model="importForm.productId"
              filterable
              clearable
              placeholder="请选择产品"
              style="width: 100%;"
              @focus="loadProductOptions"
              @change="handleImportProductChange">
              <el-option
                v-for="item in productOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目">
            <el-select
              v-model="importForm.projectId"
              filterable
              clearable
              placeholder="请选择项目"
              style="width: 100%;"
              :disabled="!importForm.productId">
              <el-option
                v-for="item in importProjectOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div
          class="case-import-dropzone"
          @dragover.prevent
          @drop.prevent="onImportFileDrop">
          <div class="case-import-drop-text">
            拖拽文件到此处，或<span class="link-text" @click="triggerImportFileSelect">点击选择</span>
          </div>
          <div class="case-import-file-tip">仅支持 .xlsx 和 .xls 格式，最大文件大小 20MB</div>
          <div v-if="importFile" class="case-import-file-name">当前文件：{{ importFile.name }}</div>
          <input
            ref="importFileInput"
            class="hidden-file-input"
            type="file"
            accept=".xls,.xlsx"
            @change="onImportFileChange">
        </div>
        <div class="case-import-actions">
          <el-button type="text" @click="downloadImportTemplate">下载标准模板</el-button>
          <el-button type="primary" :disabled="!importFile || !importForm.productId || !importForm.projectId" :loading="importSubmitting" @click="submitCaseImport">开始上传并解析</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import echarts from 'echarts'
import PageSection from '@/components/TestPlatform/common/PageSection'
import DocumentSourcePanel from '@/components/TestPlatform/Case/DocumentSourcePanel'
import {
  copyCase,
  createModule,
  deleteCase,
  deleteModule,
  downloadCaseImportTemplate,
  exportCaseExcel,
  generateCaseAutomation,
  getCaseDetail,
  getCaseList,
  getModuleTree,
  importCaseExcel,
  restoreCases,
  updateCase,
  updateModule
} from '@/api/caseApi'
import { deleteDocument, getDocumentList, generateDocumentCases, generateDocumentCasesStreaming, cancelDocumentCaseGeneration, getDocumentCaseGenerationStatus } from '@/api/documentApi'
import { getSkillList, getBusinessRuleList } from '@/api/skillRuleApi'
import { getProductList } from '@/api/productApi'
import { getProjectDetail, getProjectList } from '@/api/projectApi'
import {
  readLastProductProjectCache,
  saveLastProductProjectCache,
  pickIdFromOptions
} from '@/utils/lastProductProjectCache'

export default {
  name: 'CaseList',
  components: { PageSection, DocumentSourcePanel },
  data() {
    const routeTab = this.$route.query.tab
    let initialTab = 'modules'
    if (routeTab === 'cases') {
      initialTab = 'cases'
    } else if (routeTab === 'case-mindmap') {
      initialTab = 'case-mindmap'
    } else if (routeTab === 'ai-case-import' || routeTab === 'ai-cases') {
      initialTab = 'ai-case-import'
    }
    return {
      activeTab: initialTab,
      loading: false,
      moduleLoading: false,
      moduleSubmitting: false,
      moduleDialogVisible: false,
      moduleDialogMode: 'create',
      editingModuleId: '',
      caseMindmapLoading: false,
      caseMindmapTreeData: [],
      mindmapCollapsed: true,
      mindmapRenderKey: 0,
      selectedMindmapCase: null,
      mindmapCaseEditing: false,
      mindmapCaseSaving: false,
      mindmapCaseReviewing: false,
      mindmapCaseEditForm: {
        preconditions: '',
        steps: '',
        expectedResults: ''
      },
      projectId: this.$route.query.projectId || '',
      selectedProductId: '',
      selectedProjectId: this.$route.query.projectId ? Number(this.$route.query.projectId) : '',
      productOptions: [],
      projectOptions: [],
      moduleProjectOptions: [],
      moduleParentOptions: [],
      modulePageNo: 1,
      modulePageSize: 20,
      pageNo: 1,
      pageSize: 20,
      total: 0,
      moreFilterVisible: false,
      columnSettingVisible: false,
      caseImportDialogVisible: false,
      importSubmitting: false,
      caseExporting: false,
      caseExportProgressVisible: false,
      caseExportProgress: 0,
      caseExportProgressText: '正在请求导出数据，请稍候...',
      createdTimeRange: [],
      importFile: null,
      importForm: {
        productId: '',
        projectId: ''
      },
      importProjectOptions: [],
      queryForm: {
        keyword: '',
        priority: '',
        creator: '',
        createdStartTime: '',
        createdEndTime: '',
        caseKeysText: '',
        moduleId: '',
        caseType: '',
        status: '',
        isAuto: '',
        tag: ''
      },
      allCaseColumns: [
        { key: 'title', label: '用例标题', prop: 'title', minWidth: 220 },
        { key: 'moduleName', label: '模块名称', prop: 'module_name', minWidth: 140 },
        { key: 'priority', label: '优先级', prop: 'priority', width: 90 },
        { key: 'tags', label: '标签', prop: 'tags', minWidth: 180 },
        { key: 'creator', label: '创建人', prop: 'creator', minWidth: 120 },
        { key: 'createdTime', label: '创建时间', prop: 'created_time', minWidth: 160 },
        { key: 'caseType', label: '类型', prop: 'case_type', width: 90 },
        { key: 'status', label: '状态', prop: 'status', width: 100 },
        { key: 'isAuto', label: '是否自动化', prop: 'is_auto', width: 110 },
        { key: 'caseKey', label: '用例编号', prop: 'case_key', minWidth: 120 },
        { key: 'projectName', label: '项目名称', prop: 'project_name', minWidth: 140 }
      ],
      selectedCaseColumnKeys: ['title', 'moduleName', 'priority', 'tags', 'creator', 'createdTime'],
      moduleQueryForm: {
        projectId: this.$route.query.projectId || ''
      },
      moduleForm: {
        productId: '',
        projectId: this.$route.query.projectId || '',
        name: '',
        parentId: '0',
        sortOrder: '0',
        path: ''
      },
      moduleRules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        name: [{ required: true, message: '请输入模块名称', trigger: 'blur' }]
      },
      tableData: [],
      moduleData: [],
      aiQueryForm: {
        moduleId: '',
        keyword: '',
        priority: '',
        tag: '',
        creator: ''
      },
      aiCasePageNo: 1,
      aiCasePageSize: 20,
      aiCaseTotal: 0,
      aiTableData: [],
      aiLoading: false,
      aiDocList: [],
      aiDocLoading: false,
      aiSelectedDocIds: [],
      aiGenForm: {
        priority: 2,
        caseType: 1,
        tags: ['AI生成']
      },
      aiSkillOptions: [],
      aiRuleOptions: [],
      aiSkillRuleLoading: false,
      aiGenSelectedSkillIds: [],
      aiGenSelectedRuleIds: [],
      aiGenerateLoading: false,
      aiCancelLoading: false,
      aiGenerationId: '',
      aiGenerateStream: null,
      aiGenerationStatusTimer: null,
      aiGenProgress: {
        visible: false,
        chunkIndex: 0,
        totalChunks: 0,
        chunkTitle: '',
        casesCount: 0,
        totalCasesSoFar: 0,
        totalSkipped: 0,
        errors: [],
        logs: []
      },
      aiSelectedCases: [],
      aiBatchDeleting: false,
      aiBatchSyncing: false,
      aiCaseDetailVisible: false,
      aiCaseDetailLoading: false,
      aiCaseDetail: {},
      autoGenDialogVisible: false,
      autoGenSubmitting: false,
      autoGenRow: null,
      autoGenForm: {
        automationType: 'ui',
        prompt: ''
      },
      autoGenRules: {
        automationType: [{ required: true, message: '请选择生成类型', trigger: 'change' }],
        prompt: [{ required: true, message: '请输入提示词', trigger: 'blur' }]
      }
    }
  },
  computed: {
    visibleCaseColumns() {
      return this.allCaseColumns.filter(item => this.selectedCaseColumnKeys.includes(item.key))
    },
    /** AI 用例列表：模块路径后紧跟模块名称，其余列不再重复渲染模块名称 */
    visibleAiCaseColumnsWithoutModuleName() {
      return this.visibleCaseColumns.filter(item => item.key !== 'moduleName')
    },
    filteredModuleData() {
      return this.moduleData || []
    },
    moduleTotal() {
      return (this.filteredModuleData || []).length
    },
    pagedModuleData() {
      const start = (this.modulePageNo - 1) * this.modulePageSize
      const end = start + this.modulePageSize
      return (this.filteredModuleData || []).slice(start, end)
    },
    flatModuleOptions() {
      const result = []
      const walk = (list, prefix) => {
        ;(list || []).forEach(item => {
          const name = prefix ? `${prefix} / ${item.name}` : item.name
          result.push({
            id: item.id,
            name
          })
          const children = item.children || item.child_list || item.childList || []
          if (Array.isArray(children) && children.length > 0) {
            walk(children, name)
          }
        })
      }
      walk(this.moduleData, '')
      return result
    },
    aiCaseDetailRowPresent() {
      const d = this.aiCaseDetail
      if (!d || typeof d !== 'object') return false
      if (d.id !== undefined && d.id !== null && d.id !== '') return true
      if (d.title) return true
      return Object.keys(d).length > 0
    },
    autoGenRowTitle() {
      const r = this.autoGenRow
      if (!r) return '—'
      return r.title || r.case_key || r.caseKey || (r.id != null ? `用例 #${r.id}` : '—')
    },
    mindmapDefaultExpandedKeys() {
      // 合并展示模式下全部收起，正常模式下只展开根节点（项目节点）
      if (this.mindmapCollapsed) return []
      const treeData = this.caseMindmapTreeData || []
      return treeData.map(item => item.id)
    },
  },
  watch: {
    activeTab(val) {
      if (val === 'case-mindmap') {
        this.fetchCaseMindmapData()
      }
      if (val === 'ai-case-import' && this.projectId) {
        this.fetchAiCaseList()
        this.fetchAiDocList()
        this.fetchAiSkillRuleOptions()
        this.checkAiGenerationStatus()
      }
    }
  },
  methods: {
    loadProductOptions() {
      if (this.productOptions && this.productOptions.length > 0) {
        return Promise.resolve()
      }
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.productOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.productOptions = []
      })
    },
    loadProjectOptionsByProduct(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.projectOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.projectOptions = []
      })
    },
    loadImportProjectOptions(productId) {
      if (!productId) {
        this.importProjectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.importProjectOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.importProjectOptions = []
      })
    },
    loadModuleProjectOptionsByProduct(productId) {
      if (!productId) {
        this.moduleProjectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const data = res && res.data ? res.data : res || {}
        this.moduleProjectOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.moduleProjectOptions = []
      })
    },
    loadModuleParentOptionsByProject(projectId) {
      if (!projectId) {
        this.moduleParentOptions = []
        return Promise.resolve()
      }
      return getModuleTree({ projectId }).then(res => {
        const data = (res && res.data) || res || {}
        const list = data.list || data.items || []
        this.moduleParentOptions = Array.isArray(list) ? list : []
      }).catch(() => {
        this.moduleParentOptions = []
      })
    },
    handleProductChange(val) {
      this.selectedProjectId = ''
      this.projectId = ''
      this.moduleQueryForm.projectId = ''
      this.tableData = []
      this.total = 0
      this.moduleData = []
      this.aiTableData = []
      this.aiCaseTotal = 0
      this.aiDocList = []
      this.aiSelectedDocIds = []
      this.aiSkillOptions = []
      this.aiRuleOptions = []
      this.aiGenSelectedSkillIds = []
      this.aiGenSelectedRuleIds = []
      this.clearAiCaseTableSelection()
      this.loadProjectOptionsByProduct(val)
    },
    handleProjectChange(val) {
      this.projectId = val || ''
      this.moduleQueryForm.projectId = val || ''
      this.pageNo = 1
      this.modulePageNo = 1
      if (!val) {
        this.tableData = []
        this.total = 0
        this.moduleData = []
        this.aiTableData = []
        this.aiCaseTotal = 0
        this.aiDocList = []
        this.aiSelectedDocIds = []
        this.aiSkillOptions = []
        this.aiRuleOptions = []
        this.aiGenSelectedSkillIds = []
        this.aiGenSelectedRuleIds = []
        this.clearAiCaseTableSelection()
        return
      }
      saveLastProductProjectCache(this.selectedProductId, val)
      this.fetchModuleList()
      this.fetchList()
      this.fetchCaseMindmapData()
      if (this.activeTab === 'ai-case-import') {
        this.aiCasePageNo = 1
        this.fetchAiCaseList()
        this.fetchAiDocList()
        this.fetchAiSkillRuleOptions()
      }
    },
    restoreSharedProductProjectCache() {
      const cached = readLastProductProjectCache()
      if (!cached) return Promise.resolve()
      const { productId: pid, projectId: projId } = cached
      if (pid === '' || pid === undefined || pid === null || projId === '' || projId === undefined || projId === null) {
        return Promise.resolve()
      }
      const hasProduct = (this.productOptions || []).some(p => String(p.id) === String(pid))
      if (!hasProduct) return Promise.resolve()
      this.selectedProductId = pickIdFromOptions(this.productOptions, pid)
      return this.loadProjectOptionsByProduct(this.selectedProductId).then(() => {
        const hasProject = (this.projectOptions || []).some(p => String(p.id) === String(projId))
        if (!hasProject) return
        const picked = pickIdFromOptions(this.projectOptions, projId)
        this.selectedProjectId = picked
        this.projectId = picked
        this.moduleQueryForm.projectId = picked
      })
    },
    fetchModuleList() {
      if (!this.moduleQueryForm.projectId) {
        this.moduleData = []
        return
      }
      this.moduleLoading = true
      getModuleTree(this.cleanParams(this.moduleQueryForm)).then(res => {
        const data = (res && res.data) || res || {}
        const list = data.list || data.items || []
        this.moduleData = Array.isArray(list) ? list : []
        this.modulePageNo = 1
      }).catch(() => {
        this.moduleData = []
      }).finally(() => {
        this.moduleLoading = false
      })
    },
    fetchCaseMindmapData() {
      if (!this.projectId) {
        this.caseMindmapTreeData = []
        this.selectedMindmapCase = null
        this.mindmapCaseEditing = false
        return
      }
      this.caseMindmapLoading = true
      getModuleTree({
        projectId: this.projectId,
        parentId: 0,
        pageNo: 1,
        pageSize: 200
      }).then(res => {
        const data = (res && res.data) || res || {}
        const rootModules = data.list || data.items || []
        this.caseMindmapTreeData = this.buildCaseMindmapTree(Array.isArray(rootModules) ? rootModules : [])
        this.mindmapRenderKey += 1
        this.selectedMindmapCase = null
        this.mindmapCaseEditing = false
      }).catch(() => {
        this.caseMindmapTreeData = []
        this.selectedMindmapCase = null
        this.mindmapCaseEditing = false
      }).finally(() => {
        this.caseMindmapLoading = false
      })
    },
    toggleMindmapCollapsed() {
      this.mindmapCollapsed = !this.mindmapCollapsed
      this.mindmapRenderKey += 1
    },
    handleMindmapNodeClick(node) {
      if (!node) {
        return
      }
      if (node.nodeTypeLabel === '模块') {
        const tree = this.$refs.mindmapTreeRef
        if (tree && tree.store) {
          const storeNode = tree.store.nodesMap && tree.store.nodesMap[node.id]
          const currentlyExpanded = storeNode ? storeNode.expanded : false
          if (currentlyExpanded) {
            storeNode.expanded = false
            return
          }
        }
        this.expandMindmapModuleCases(node)
        return
      }
      if (node.nodeTypeLabel === '用例') {
        this.selectedMindmapCase = node
        this.mindmapCaseEditing = false
      }
    },
    // el-tree 展开事件：展开一个模块时，保留当前路径，只收起其他分支
    handleMindmapNodeExpand(expandedData, expandedNode) {
      if (!expandedData || expandedData.nodeTypeLabel !== '模块') return
      this.collapseMindmapOtherBranches(expandedNode)
    },
    expandMindmapStoreNode(nodeId) {
      const tree = this.$refs.mindmapTreeRef
      if (!tree || !tree.store) return
      const storeNode = tree.store.nodesMap && tree.store.nodesMap[nodeId]
      if (!storeNode) return
      storeNode.expanded = true
      this.collapseMindmapOtherBranches(storeNode)
    },
    collapseMindmapOtherBranches(currentNode) {
      const tree = this.$refs.mindmapTreeRef
      if (!tree || !tree.root || !currentNode) return
      const keepIds = new Set()
      let node = currentNode
      while (node && node.data) {
        keepIds.add(node.data.id)
        node = node.parent
      }
      const walk = (children) => {
        if (!children) return
        children.forEach(child => {
          if (child.data && child.data.nodeTypeLabel === '模块' && !keepIds.has(child.data.id)) {
            child.expanded = false
          }
          if (child.childNodes && child.childNodes.length > 0) {
            walk(child.childNodes)
          }
        })
      }
      this.$nextTick(() => {
        walk(tree.root.childNodes)
      })
    },
    expandMindmapModuleCases(moduleNode) {
      if (!moduleNode || !moduleNode.rawId) {
        return
      }
      const moduleId = moduleNode.rawId
      if (moduleNode._childrenChecked && moduleNode._casesLoaded) {
        // 已加载子节点，直接切换展开/收起
        const tree = this.$refs.mindmapTreeRef
        if (tree && tree.store) {
          const storeNode = tree.store.nodesMap && tree.store.nodesMap[moduleNode.id]
          if (storeNode) {
            storeNode.expanded = !storeNode.expanded
            if (storeNode.expanded) {
              this.collapseMindmapOtherBranches(storeNode)
            }
          }
        }
        return
      }
      if (moduleNode._childrenLoading || moduleNode._casesLoading) {
        return
      }
      moduleNode._childrenLoading = true
      getModuleTree({
        projectId: this.projectId,
        parentId: moduleId,
        pageNo: 1,
        pageSize: 200
      }).then(res => {
        const data = (res && res.data) || res || {}
        const children = data.list || data.items || []
        const childList = Array.isArray(children) ? children : []
        moduleNode._childrenChecked = true
        if (childList.length > 0) {
          const childNodes = childList.map(item => this.buildMindmapModuleNode(item))
          moduleNode.children = childNodes
          // 使用 updateKeyChildren 增量更新，避免整树重渲染丢失手风琴状态
          const tree = this.$refs.mindmapTreeRef
          if (tree && tree.store) {
            tree.updateKeyChildren(moduleNode.id, childNodes)
            this.expandMindmapStoreNode(moduleNode.id)
          }
          return
        }
        moduleNode._casesLoading = true
        const query = Object.assign({}, this.queryForm, {
          moduleId,
          created_by_name: this.queryForm.creator
        })
        delete query.creator
        const params = this.cleanParams(Object.assign({}, query, {
          pageNo: 1,
          pageSize: 20
        }))
        return getCaseList(this.projectId, params).then(caseRes => {
          const caseData = (caseRes && caseRes.data) || caseRes || {}
          const list = caseData.list || caseData.items || []
          const caseNodes = (Array.isArray(list) ? list : []).map(item => this.buildMindmapCaseNode(item))
          const tree = this.$refs.mindmapTreeRef
          if (tree) {
            tree.updateKeyChildren(moduleNode.id, caseNodes)
            this.expandMindmapStoreNode(moduleNode.id)
          }
          moduleNode.children = caseNodes
          moduleNode._casesLoaded = true
        }).finally(() => {
          moduleNode._casesLoading = false
        })
      }).finally(() => {
        moduleNode._childrenLoading = false
      })
    },
    startMindmapCaseEdit() {
      if (!this.selectedMindmapCase) return
      this.mindmapCaseEditForm = {
        preconditions: this.selectedMindmapCase.preconditions || '',
        steps: this.formatMindmapSteps(this.selectedMindmapCase.steps) || '',
        expectedResults: this.selectedMindmapCase.expectedResults || ''
      }
      this.mindmapCaseEditing = true
    },
    cancelMindmapCaseEdit() {
      this.mindmapCaseEditing = false
    },
    saveMindmapCaseEdit() {
      if (!this.selectedMindmapCase || !this.selectedMindmapCase.rawId) {
        return
      }
      const caseId = this.selectedMindmapCase.rawId
      const payload = this.cleanParams({
        preconditions: this.mindmapCaseEditForm.preconditions,
        steps: this.mindmapCaseEditForm.steps,
        expectedResults: this.mindmapCaseEditForm.expectedResults
      })
      this.mindmapCaseSaving = true
      updateCase(this.projectId, caseId, payload).then(() => {
        this.$message.success('保存成功')
        this.selectedMindmapCase.preconditions = this.mindmapCaseEditForm.preconditions
        this.selectedMindmapCase.steps = this.mindmapCaseEditForm.steps
        this.selectedMindmapCase.expectedResults = this.mindmapCaseEditForm.expectedResults
        this.mindmapCaseEditing = false
        this.fetchList()
      }).finally(() => {
        this.mindmapCaseSaving = false
      })
    },
    startMindmapCaseReview() {
      if (!this.selectedMindmapCase || !this.selectedMindmapCase.rawId) {
        return
      }
      const caseId = this.selectedMindmapCase.rawId
      this.mindmapCaseReviewing = true
      // 先进入评审中
      updateCase(this.projectId, caseId, { status: 3 }).then(() => {
        this.selectedMindmapCase.status = 3
        return this.$confirm('是否评审通过？', '评审确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          // 确定后评审通过，状态置为 4
          return updateCase(this.projectId, caseId, { status: 4 }).then(() => {
            this.selectedMindmapCase.status = 4
            this.$message.success('评审通过')
          })
        }).catch(() => {
          // 取消仅关闭弹框，保持评审中
          this.selectedMindmapCase.status = 3
        })
      }).finally(() => {
        this.mindmapCaseReviewing = false
        this.fetchList()
      })
    },
    formatMindmapSteps(steps) {
      if (!steps) return ''
      if (typeof steps === 'string') return steps
      if (Array.isArray(steps)) {
        return steps.map(item => {
          if (typeof item === 'string') return item
          return item.action || item.step || item.text || item.content || ''
        }).filter(Boolean).join('\n')
      }
      return String(steps)
    },
    formatStatusTagType(status) {
      if (status === 0) return 'info'
      if (status === 1) return 'success'
      if (status === 3) return 'warning'
      if (status === 2) return 'info'
      if (status === 4) return 'success'
      return ''
    },
    buildCaseMindmapTree(rootModules) {
      const moduleChildren = (rootModules || []).map(item => this.buildMindmapModuleNode(item))
      const currentProject = (this.projectOptions || []).find(item => String(item.id) === String(this.projectId))
      return [{
        id: `project-${this.projectId}`,
        rawId: this.projectId,
        nodeTypeLabel: '项目',
        name: (currentProject && currentProject.name) || `项目-${this.projectId}`,
        creator: '',
        updatedTime: '',
        children: moduleChildren
      }]
    },
    buildMindmapModuleNode(item) {
      return {
        id: `module-${item.id}`,
        rawId: item.id,
        nodeTypeLabel: '模块',
        name: item.name || `模块-${item.id}`,
        creator: '',
        updatedTime: item.updated_time || item.updatedTime || '',
        parentId: item.parent_id || item.parentId || 0,
        _childrenChecked: false,
        _childrenLoading: false,
        _casesLoaded: false,
        _casesLoading: false,
        children: []
      }
    },
    buildMindmapCaseNode(item) {
      return {
        id: `case-${item.id}`,
        rawId: item.id,
        nodeTypeLabel: '用例',
        name: item.title || item.case_key || `用例-${item.id}`,
        creator: item.created_by_name || '',
        updatedTime: item.updated_time || item.updatedTime || '',
        status: item.status,
        preconditions: item.preconditions || '',
        steps: item.steps || '',
        expectedResults: item.expected_results || item.expectedResults || ''
      }
    },
    refreshModuleList() {
      if (!this.selectedProjectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.fetchModuleList()
    },
    handleModuleSizeChange(size) {
      this.modulePageSize = size
      this.modulePageNo = 1
    },
    handleModuleCurrentChange(page) {
      this.modulePageNo = page
    },
    openModuleCreate() {
      this.moduleDialogMode = 'create'
      this.editingModuleId = ''
      this.moduleDialogVisible = true
      this.moduleForm.productId = this.selectedProductId || ''
      this.moduleForm.projectId = this.selectedProjectId || this.moduleQueryForm.projectId || this.projectId || ''
      this.moduleForm.parentId = '0'
      this.loadModuleProjectOptionsByProduct(this.moduleForm.productId)
      this.loadModuleParentOptionsByProject(this.moduleForm.projectId)
    },
    openModuleEdit(row) {
      this.moduleDialogMode = 'edit'
      this.editingModuleId = row.id
      this.moduleDialogVisible = true
      this.moduleForm.productId = this.selectedProductId || ''
      this.moduleForm.projectId = row.project_id || row.projectId || this.selectedProjectId || this.moduleQueryForm.projectId || this.projectId || ''
      this.moduleForm.name = row.name || ''
      this.moduleForm.parentId = String(row.parent_id || row.parentId || 0)
      this.moduleForm.sortOrder = String(row.sort_order || row.sortOrder || 0)
      this.moduleForm.path = row.path || ''
      this.loadModuleProjectOptionsByProduct(this.moduleForm.productId)
      this.loadModuleParentOptionsByProject(this.moduleForm.projectId).then(() => {
        this.moduleParentOptions = (this.moduleParentOptions || []).filter(item => item.id !== row.id)
      })
    },
    handleModuleProductChange(val) {
      this.moduleForm.projectId = ''
      this.moduleForm.parentId = '0'
      this.moduleParentOptions = []
      this.loadModuleProjectOptionsByProduct(val)
    },
    handleModuleProjectChange(val) {
      this.moduleForm.parentId = '0'
      this.loadModuleParentOptionsByProject(val)
    },
    resetModuleForm() {
      this.moduleDialogMode = 'create'
      this.editingModuleId = ''
      this.moduleForm = {
        productId: this.selectedProductId || '',
        projectId: this.selectedProjectId || this.moduleQueryForm.projectId || this.projectId || '',
        name: '',
        parentId: '0',
        sortOrder: '0',
        path: ''
      }
      this.loadModuleParentOptionsByProject(this.moduleForm.projectId)
      this.$nextTick(() => {
        this.$refs.moduleForm && this.$refs.moduleForm.clearValidate()
      })
    },
    submitModule() {
      this.$refs.moduleForm.validate(valid => {
        if (!valid) {
          return
        }
        this.moduleSubmitting = true
        const payload = this.cleanParams({
          projectId: this.moduleForm.projectId,
          name: this.moduleForm.name,
          parentId: this.moduleForm.parentId,
          sortOrder: this.moduleForm.sortOrder,
          path: this.moduleForm.path
        })
        const request = this.moduleDialogMode === 'edit'
          ? updateModule(Object.assign({ moduleId: this.editingModuleId }, payload))
          : createModule(payload)
        request.then(() => {
          this.$message({ type: 'success', message: this.moduleDialogMode === 'edit' ? '保存成功' : '新增成功' })
          this.moduleDialogVisible = false
          if (this.selectedProjectId !== this.moduleForm.projectId) {
            this.selectedProjectId = this.moduleForm.projectId
            this.projectId = this.moduleForm.projectId
            this.moduleQueryForm.projectId = this.moduleForm.projectId
          }
          this.fetchModuleList()
        }).finally(() => {
          this.moduleSubmitting = false
        })
      })
    },
    removeModule(row) {
      this.$confirm('确认删除该模块吗？', '提示', { type: 'warning' }).then(() => {
        deleteModule({ moduleId: row.id }).then(() => {
          this.$message({ type: 'success', message: '删除成功' })
          this.fetchModuleList()
        })
      }).catch(() => {})
    },
    fetchList() {
      if (!this.projectId) {
        this.tableData = []
        this.total = 0
        return
      }
      this.loading = true
      const query = Object.assign({}, this.queryForm, {
        // 后端创建人字段为 created_by_name
        created_by_name: this.queryForm.creator
      })
      delete query.creator
      const caseKeys = this.normalizeCaseKeys(query.caseKeysText)
      delete query.caseKeysText
      if (caseKeys.length) {
        query.caseKeys = caseKeys.join(',')
      }
      const params = this.cleanParams(Object.assign({}, query, {
        pageNo: this.pageNo,
        pageSize: this.pageSize
      }))
      getCaseList(this.projectId, params).then(res => {
        const data = (res && res.data) || res || {}
        const list = data.list || data.items || []
        this.tableData = Array.isArray(list) ? list : []
        this.total = Number(data.total || this.tableData.length || 0)
      }).catch(() => {
        this.tableData = []
        this.total = 0
      }).finally(() => {
        this.loading = false
      })
    },
    fetchAiCaseList() {
      if (!this.projectId) {
        this.aiTableData = []
        this.aiCaseTotal = 0
        return
      }
      this.aiLoading = true
      const query = Object.assign({}, this.aiQueryForm, {
        created_by_name: this.aiQueryForm.creator
      })
      delete query.creator
      const params = this.cleanParams(
        Object.assign({}, query, {
          pageNo: this.aiCasePageNo,
          pageSize: this.aiCasePageSize,
          status: 0,
          is_ai_generated: 1,
          module_status: 0
        })
      )
      getCaseList(this.projectId, params)
        .then(res => {
          const data = (res && res.data) || res || {}
          const list = data.list || data.items || []
          this.aiTableData = Array.isArray(list) ? list : []
          this.aiCaseTotal = Number(data.total || this.aiTableData.length || 0)
        })
        .catch(() => {
          this.aiTableData = []
          this.aiCaseTotal = 0
        })
        .finally(() => {
          this.aiLoading = false
          this.clearAiCaseTableSelection()
        })
    },
    fetchAiDocList() {
      if (!this.projectId) {
        this.aiDocList = []
        this.aiSelectedDocIds = []
        return
      }
      this.aiDocLoading = true
      getDocumentList(
        this.cleanParams({
          productId: this.selectedProductId || undefined,
          projectId: this.projectId,
          pageNo: 1,
          pageSize: 500
        })
      )
        .then(res => {
          const data = (res && res.data) || res || {}
          const list = data.list || data.items || []
          this.aiDocList = Array.isArray(list) ? list : []
        })
        .catch(() => {
          this.aiDocList = []
        })
        .finally(() => {
          this.aiDocLoading = false
        })
    },
    fetchAiSkillRuleOptions() {
      if (!this.projectId) {
        this.aiSkillOptions = []
        this.aiRuleOptions = []
        this.aiGenSelectedSkillIds = []
        this.aiGenSelectedRuleIds = []
        return Promise.resolve()
      }
      const pid = Number(this.projectId)
      if (!Number.isFinite(pid) || pid <= 0) {
        return Promise.resolve()
      }
      this.aiSkillRuleLoading = true
      const base = { projectId: pid, pageNo: 1, pageSize: 1000 }
      const parseList = res => {
        const data = (res && res.data) || res || {}
        const list = data.list || data.items || []
        return Array.isArray(list) ? list : []
      }
      return Promise.all([
        getSkillList(base).then(parseList).catch(() => []),
        getBusinessRuleList(base).then(parseList).catch(() => [])
      ])
        .then(([skills, rules]) => {
          this.aiSkillOptions = skills.filter(s => s && s.id !== undefined && s.id !== null && s.id !== '')
          this.aiRuleOptions = rules.filter(r => r && r.id !== undefined && r.id !== null && r.id !== '')
          const sidSet = new Set(
            this.aiSkillOptions.map(s => Number(s.id)).filter(n => Number.isFinite(n) && n > 0)
          )
          const ridSet = new Set(
            this.aiRuleOptions.map(r => Number(r.id)).filter(n => Number.isFinite(n) && n > 0)
          )
          this.aiGenSelectedSkillIds = (this.aiGenSelectedSkillIds || []).filter(id =>
            sidSet.has(Number(id))
          )
          this.aiGenSelectedRuleIds = (this.aiGenSelectedRuleIds || []).filter(id =>
            ridSet.has(Number(id))
          )
        })
        .finally(() => {
          this.aiSkillRuleLoading = false
        })
    },
    formatAiSkillOptionLabel(s) {
      if (!s) return ''
      const name = s.name || `ID ${s.id}`
      return s.code ? `${name} · ${s.code}` : name
    },
    formatAiRuleOptionLabel(r) {
      if (!r) return ''
      const name = r.name || `ID ${r.id}`
      const code = r.rule_code || r.ruleCode
      return code ? `${name} · ${code}` : name
    },
    resetAiQuery() {
      this.aiQueryForm = {
        moduleId: '',
        keyword: '',
        priority: '',
        tag: '',
        creator: ''
      }
      this.aiCasePageNo = 1
      this.fetchAiCaseList()
    },
    onAiDocSelectionChange(rows) {
      this.aiSelectedDocIds = (rows || []).map(r => r.id).filter(id => id !== undefined && id !== null)
    },
    removeAiDoc(row) {
      const documentId = row && row.id
      if (documentId === undefined || documentId === null || documentId === '') {
        this.$message.warning('无法识别文档ID')
        return
      }
      this.$confirm('确认删除该文档？删除后无法用于生成用例。', '提示', { type: 'warning' })
        .then(() => deleteDocument({ documentId }))
        .then(() => {
          this.$message.success('已删除')
          this.fetchAiDocList()
          const panel = this.$refs.aiDocumentPanel
          if (panel && typeof panel.fetchDocuments === 'function') {
            panel.fetchDocuments()
          }
        })
        .catch(() => {})
    },
    onAiCaseSelectionChange(rows) {
      this.aiSelectedCases = Array.isArray(rows) ? rows.slice() : []
    },
    clearAiCaseTableSelection() {
      this.aiSelectedCases = []
      this.$nextTick(() => {
        const t = this.$refs.aiCaseTable
        if (t && typeof t.clearSelection === 'function') {
          t.clearSelection()
        }
      })
    },
    batchRemoveAiCases() {
      const rows = this.aiSelectedCases || []
      if (!rows.length) {
        this.$message.warning('请先勾选要删除的用例')
        return
      }
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.$confirm(`确认删除选中的 ${rows.length} 条用例吗？`, '提示', { type: 'warning' })
        .then(() => {
          this.aiBatchDeleting = true
          const pid = this.projectId
          const chain = rows.reduce(
            (p, row) =>
              p.then(acc => {
                const id = row && row.id
                if (id === undefined || id === null || id === '') {
                  return { ok: acc.ok, fail: acc.fail + 1 }
                }
                return deleteCase(pid, id)
                  .then(() => ({ ok: acc.ok + 1, fail: acc.fail }))
                  .catch(() => ({ ok: acc.ok, fail: acc.fail + 1 }))
              }),
            Promise.resolve({ ok: 0, fail: 0 })
          )
          return chain
        })
        .then(({ ok, fail }) => {
          if (ok) {
            this.$message({
              type: 'success',
              message: fail ? `已删除 ${ok} 条，${fail} 条失败` : `已删除 ${ok} 条用例`
            })
          } else {
            this.$message({ type: 'error', message: '删除失败，请稍后重试' })
          }
          this.clearAiCaseTableSelection()
          this.fetchAiCaseList()
          this.fetchList()
          this.fetchCaseMindmapData()
        })
        .catch(() => {})
        .finally(() => {
          this.aiBatchDeleting = false
        })
    },
    batchSyncAiCases() {
      const rows = this.aiSelectedCases || []
      const ids = rows
        .map(r => (r && r.id !== undefined && r.id !== null ? Number(r.id) : NaN))
        .filter(id => Number.isFinite(id) && id > 0)
      if (!ids.length) {
        this.$message.warning('请先勾选要同步的用例')
        return
      }
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.$confirm(
        `确认将选中的 ${ids.length} 条用例恢复为「正常」状态？（仅支持当前为已删除/待恢复状态的用例，将同步到常规用例列表）`,
        '批量同步',
        { type: 'info', confirmButtonText: '确定同步' }
      )
        .then(() => {
          this.aiBatchSyncing = true
          return restoreCases(ids)
        })
        .then(res => {
          const d = (res && res.data) || res || {}
          const n = d.updatedCount
          this.$message.success(
            n !== undefined && n !== null ? `已同步 ${n} 条用例` : '同步成功'
          )
          this.clearAiCaseTableSelection()
          this.fetchAiCaseList()
          this.fetchList()
          this.fetchCaseMindmapData()
        })
        .catch(() => {})
        .finally(() => {
          this.aiBatchSyncing = false
        })
    },
    syncAiCase(row) {
      const id = row && row.id
      if (id === undefined || id === null || id === '') {
        this.$message.warning('无法识别用例ID')
        return
      }
      const numId = Number(id)
      if (!Number.isFinite(numId) || numId <= 0) {
        this.$message.warning('用例ID无效')
        return
      }
      this.$confirm(
        '确认将该用例恢复为「正常」状态并同步到常规用例列表？（仅支持状态为已删除/待恢复的用例）',
        '同步用例',
        { type: 'info', confirmButtonText: '确定同步' }
      )
        .then(() => restoreCases([numId]))
        .then(res => {
          const d = (res && res.data) || res || {}
          const n = d.updatedCount
          this.$message.success(
            n !== undefined && n !== null ? `已同步 ${n} 条用例` : '同步成功'
          )
          this.fetchAiCaseList()
          this.fetchList()
          this.fetchCaseMindmapData()
        })
        .catch(() => {})
    },
    formatAiDocFileName(row) {
      if (!row) return '—'
      if (row.type === 2) {
        return '—'
      }
      const s = String(row.source || '')
      if (!s) return '—'
      const norm = s.replace(/\\/g, '/')
      const parts = norm.split('/')
      return parts[parts.length - 1] || s
    },
    resetAiGenerateState() {
      this.aiGenerateLoading = false
      this.aiCancelLoading = false
      this.aiGenerationId = ''
      this.aiGenerateStream = null
      this.stopAiGenerationStatusPolling()
    },
    stopAiGenerationStatusPolling() {
      if (this.aiGenerationStatusTimer) {
        clearInterval(this.aiGenerationStatusTimer)
        this.aiGenerationStatusTimer = null
      }
    },
    startAiGenerationStatusPolling() {
      if (this.aiGenerationStatusTimer) return
      this.aiGenerationStatusTimer = setInterval(() => {
        this.checkAiGenerationStatus()
      }, 5000)
    },
    formatAiGenLogTime(value) {
      if (!value) return new Date().toLocaleTimeString()
      const ts = Number(value)
      if (Number.isFinite(ts)) {
        return new Date(ts * 1000).toLocaleTimeString()
      }
      return String(value)
    },
    applyAiGenerationStatus(status = {}) {
      if (!status) return
      const running = status.status === 'running' || status.status === 'stopping'
      this.aiGenerateLoading = running
      this.aiCancelLoading = status.status === 'stopping'
      this.aiGenerationId = status.generationId || this.aiGenerationId
      this.aiGenProgress.visible = running || this.aiGenProgress.visible
      this.aiGenProgress.chunkIndex = status.chunkIndex || 0
      this.aiGenProgress.totalChunks = status.totalChunks || 0
      this.aiGenProgress.chunkTitle = status.chunkTitle || (running ? '后台仍在生成测试用例' : '')
      this.aiGenProgress.casesCount = status.casesCount || this.aiGenProgress.casesCount || 0
      this.aiGenProgress.totalCasesSoFar = status.totalCasesSoFar || 0
      this.aiGenProgress.totalSkipped = status.totalSkipped || 0
      this.aiGenProgress.errors = status.errors || []
      this.aiGenProgress.logs = (status.logs || []).map(item => ({
        time: this.formatAiGenLogTime(item.time),
        level: item.level || 'info',
        agentName: item.agentName || '',
        message: item.message || 'agent 状态更新'
      }))
      if (running) {
        this.startAiGenerationStatusPolling()
      } else {
        this.stopAiGenerationStatusPolling()
        this.fetchAiCaseList()
        this.fetchList()
        this.fetchCaseMindmapData()
        this.fetchAiDocList()
      }
    },
    checkAiGenerationStatus() {
      if (!this.projectId && !this.aiGenerationId) return Promise.resolve()
      const params = {}
      if (this.aiGenerationId) params.generationId = this.aiGenerationId
      if (this.projectId) params.projectId = this.projectId
      return getDocumentCaseGenerationStatus(params).then(res => {
        const data = (res && res.data) || res || {}
        if (data.status === 'running' || data.status === 'stopping') {
          this.applyAiGenerationStatus(data)
        } else if (this.aiGenerateLoading && (data.status === 'done' || data.status === 'cancelled' || data.status === 'error' || data.status === 'idle')) {
          if (data.status !== 'idle') {
            this.applyAiGenerationStatus(data)
          }
          this.resetAiGenerateState()
          setTimeout(() => {
            this.aiGenProgress.visible = false
          }, 3000)
        }
      }).catch(() => {})
    },
    pushAiGenLog(data = {}) {
      const logs = this.aiGenProgress.logs || []
      const message = data.message || data.chunkTitle || 'agent 状态更新'
      logs.push({
        time: new Date().toLocaleTimeString(),
        level: data.level || 'info',
        agentName: data.agentName || '',
        message
      })
      this.aiGenProgress.logs = logs.slice(-12)
    },
    createAiGenerationId() {
      if (window.crypto && window.crypto.randomUUID) {
        return window.crypto.randomUUID()
      }
      return `gen-${Date.now()}-${Math.random().toString(16).slice(2)}`
    },
    handleAiCancelGenerate() {
      if (!this.aiGenerationId) {
        this.$message.warning('暂未获取到生成任务ID，请稍后再试')
        return
      }
      if (this.aiCancelLoading) {
        return
      }
      const generationId = this.aiGenerationId
      this.aiCancelLoading = true
      this.aiGenerateLoading = true
      this.aiGenProgress.visible = true
      this.pushAiGenLog({ level: 'warning', message: '已请求停止生成，等待后台任务实际结束' })
      this.startAiGenerationStatusPolling()
      cancelDocumentCaseGeneration({ generationId })
        .catch(err => {
          const msg = err && err.message ? err.message : '停止生成请求发送失败'
          this.$message.warning(msg)
        })
    },
    handleAiGenerateCases() {
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      if (this.aiGenerateLoading) {
        this.$message.warning('当前已有AI生成任务正在执行，请等待结束或先停止生成')
        return
      }
      if (!this.aiSelectedDocIds.length) {
        this.$message.warning('请先在文档列表中勾选至少一个文档')
        return
      }
      const tags =
        Array.isArray(this.aiGenForm.tags) && this.aiGenForm.tags.length
          ? this.aiGenForm.tags.slice()
          : ['AI生成']
      const normalizePositiveIds = arr =>
        (Array.isArray(arr) ? arr : [])
          .map(id => Number(id))
          .filter(id => Number.isFinite(id) && id > 0)
      const skillIds = normalizePositiveIds(this.aiGenSelectedSkillIds)
      const ruleIds = normalizePositiveIds(this.aiGenSelectedRuleIds)
      this.$confirm('请选择本次AI生成方式。接着执行会跳过已完成的需求点，只从未完成或失败的需求点继续；重新开始会清空本次文档和参数下的断点记录后从头生成。', 'AI生成方式', {
        confirmButtonText: '接着执行',
        cancelButtonText: '重新开始',
        distinguishCancelAndClose: true,
        type: 'warning'
      }).then(() => {
        this.startAiGenerateCases('resume', tags, skillIds, ruleIds)
      }).catch(action => {
        if (action === 'cancel') {
          this.startAiGenerateCases('restart', tags, skillIds, ruleIds)
        }
      })
    },
    startAiGenerateCases(resumeMode, tags, skillIds, ruleIds) {
      const generationId = this.createAiGenerationId()
      const payload = {
        documentIds: this.aiSelectedDocIds.slice(),
        projectId: Number(this.projectId),
        generationId,
        resumeMode,
        priority: this.aiGenForm.priority,
        caseType: this.aiGenForm.caseType,
        tags
      }
      if (skillIds.length) payload.skillIds = skillIds
      if (ruleIds.length) payload.ruleIds = ruleIds

      // 使用SSE流式生成，实时显示进度
      this.aiGenerateLoading = true
      this.aiCancelLoading = false
      this.aiGenerationId = generationId
      this.aiGenerateStream = null
      this.aiGenProgress.visible = true
      this.aiGenProgress.chunkIndex = 0
      this.aiGenProgress.totalChunks = 0
      this.aiGenProgress.chunkTitle = ''
      this.aiGenProgress.casesCount = 0
      this.aiGenProgress.totalCasesSoFar = 0
      this.aiGenProgress.totalSkipped = 0
      this.aiGenProgress.errors = []
      this.aiGenProgress.logs = []
      this.startAiGenerationStatusPolling()

      this.aiGenerateStream = generateDocumentCasesStreaming(
        payload,
        // onEvent: 收到SSE事件
        (parsed) => {
          const event = parsed.event
          const data = parsed.data || {}
          if (event === 'start') {
            this.aiGenerationId = data.generationId || this.aiGenerationId
          } else if (event === 'agent_plan') {
            this.aiGenProgress.totalChunks = data.totalChunks || 0
            this.aiGenProgress.chunkTitle = data.message || '已拆分测试点任务，正在并发生成'
            if (data.resumeSkippedCount) {
              this.pushAiGenLog({
                level: 'info',
                message: `断点续跑：已跳过${data.resumeSkippedCount}个已完成生成点，继续执行剩余${data.totalChunks || 0}个生成点`
              })
            }
          } else if (event === 'agent_start') {
            this.aiGenProgress.chunkIndex = data.chunkIndex || this.aiGenProgress.chunkIndex
            this.aiGenProgress.totalChunks = data.totalChunks || this.aiGenProgress.totalChunks
            this.aiGenProgress.chunkTitle = data.chunkTitle || data.agentName || ''
            this.aiGenProgress.casesCount = 0
          } else if (event === 'agent_log') {
            this.pushAiGenLog(data)
          } else if (event === 'ai_retry') {
            this.pushAiGenLog(Object.assign({}, data, { level: 'warning' }))
          } else if (event === 'heartbeat') {
            this.aiGenProgress.chunkIndex = data.chunkIndex || this.aiGenProgress.chunkIndex
            this.aiGenProgress.totalChunks = data.totalChunks || this.aiGenProgress.totalChunks
            this.aiGenProgress.chunkTitle = data.chunkTitle || this.aiGenProgress.chunkTitle
            this.pushAiGenLog(data)
          } else if (event === 'chunk_start') {
            this.aiGenProgress.chunkIndex = data.chunkIndex || 0
            this.aiGenProgress.totalChunks = data.totalChunks || 0
            this.aiGenProgress.chunkTitle = data.chunkTitle || ''
            this.aiGenProgress.casesCount = 0
            this.aiGenProgress.totalCasesSoFar = data.totalCasesSoFar || this.aiGenProgress.totalCasesSoFar
          } else if (event === 'progress') {
            this.aiGenProgress.chunkIndex = data.chunkIndex || 0
            this.aiGenProgress.totalChunks = data.totalChunks || 0
            this.aiGenProgress.chunkTitle = data.chunkTitle || ''
            this.aiGenProgress.casesCount = data.casesCount || 0
            this.aiGenProgress.totalCasesSoFar = data.totalCasesSoFar || 0
            this.aiGenProgress.totalSkipped = data.totalSkipped || this.aiGenProgress.totalSkipped || 0
          } else if (event === 'chunk_error') {
            this.aiGenProgress.errors.push({
              chunkIndex: data.chunkIndex,
              error: data.error
            })
          } else if (event === 'cancelled') {
            const importedCount = data.importedCount || 0
            const skippedCount = data.skippedCount || 0
            this.$message.info(importedCount > 0 || skippedCount > 0 ? `已停止生成，已导入${importedCount}条，跳过重复${skippedCount}条` : '已停止生成')
            this.fetchAiCaseList()
            this.fetchList()
            this.fetchCaseMindmapData()
            this.fetchAiDocList()
          } else if (event === 'done') {
            const totalCases = data.totalCases || 0
            const importedCount = data.importedCount || data.totalImported || 0
            const skippedCount = data.skippedCount || data.totalSkipped || 0
            this.aiGenProgress.totalSkipped = skippedCount
            if (totalCases > 0 || importedCount > 0 || skippedCount > 0) {
              this.$message.success(`生成完成，共返回${totalCases}条，已导入${importedCount}条，跳过重复${skippedCount}条`)
              this.fetchAiCaseList()
              this.fetchList()
              this.fetchCaseMindmapData()
              this.fetchAiDocList()
            } else if (data.resumeSkippedCount) {
              this.$message.success(data.message || `所有生成点已完成，已跳过${data.resumeSkippedCount}个生成点`)
            } else {
              this.$message.warning('AI未生成任何测试用例，请检查文档内容')
            }
            if (data.hasError || (data.failedChunks && data.failedChunks.length)) {
              const errMsgs = (data.failedChunks || []).map(f => f.error || '未知错误').join('; ')
              if (errMsgs) {
                this.$message.warning(`部分分段生成失败: ${errMsgs}`)
              }
            }
          } else if (event === 'error') {
            this.$message.error(data.message || '生成失败')
            this.resetAiGenerateState()
            setTimeout(() => {
              this.aiGenProgress.visible = false
            }, 3000)
          } else if (event === 'import_error') {
            this.$message.error(`导入失败: ${data.error}`)
          }
        },
        // onError: 网络错误
        (err) => {
          this.$message.error(`生成连接中断: ${err.message || '网络错误'}，正在查询后台生成状态`)
          this.aiGenerateStream = null
          this.checkAiGenerationStatus()
          this.startAiGenerationStatusPolling()
        },
        // onDone: 流结束
        () => {
          this.checkAiGenerationStatus().then(() => {
            if (!this.aiGenerateLoading) {
              setTimeout(() => {
                this.aiGenProgress.visible = false
              }, 3000)
            }
          })
        }
      )
    },
    handleAiCaseSizeChange(size) {
      this.aiCasePageSize = size
      this.aiCasePageNo = 1
      this.fetchAiCaseList()
    },
    handleAiCaseCurrentChange(page) {
      this.aiCasePageNo = page
      this.fetchAiCaseList()
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchList()
    },
    handleCurrentChange(page) {
      this.pageNo = page
      this.fetchList()
    },
    handleCreatedTimeChange(value) {
      const range = Array.isArray(value) ? value : []
      this.queryForm.createdStartTime = range[0] || ''
      this.queryForm.createdEndTime = range[1] || ''
    },
    applyMoreFilters() {
      this.moreFilterVisible = false
      this.pageNo = 1
      this.fetchList()
      if (this.activeTab === 'case-mindmap') {
        this.fetchCaseMindmapData()
      }
    },
    resetQuery() {
      this.queryForm = {
        keyword: '',
        priority: '',
        creator: '',
        createdStartTime: '',
        createdEndTime: '',
        caseKeysText: '',
        moduleId: '',
        caseType: '',
        status: '',
        isAuto: '',
        tag: ''
      }
      this.createdTimeRange = []
      this.pageNo = 1
      this.fetchList()
      if (this.activeTab === 'case-mindmap') {
        this.fetchCaseMindmapData()
      }
    },
    handleColumnSelectionChange(value) {
      if (value.length === 0) {
        this.$message.warning('至少保留一个展示字段')
        this.selectedCaseColumnKeys = ['title']
      }
    },
    getCaseColumnValue(row, key) {
      const map = {
        title: row.title,
        moduleName: row.module_name,
        priority: row.priority,
        tags: row.tags,
        creator: row.created_by_name || row.creator || row.creator_name || row.create_user || row.createUser || row.created_by || '',
        createdTime: row.created_time || row.create_time || row.createdTime || row.createTime || '',
        caseType: row.case_type,
        status: row.status,
        isAuto: row.is_auto,
        caseKey: row.case_key,
        projectName: row.project_name
      }
      return map[key]
    },
    formatCaseColumnValue(key, value) {
      if (key === 'priority') return this.formatPriority(value)
      if (key === 'caseType') return this.formatCaseType(value)
      if (key === 'status') return this.formatStatus(value)
      if (key === 'isAuto') return this.formatIsAuto(value)
      return value
    },
    openCaseImportDialog() {
      this.importForm.productId = this.selectedProductId || ''
      this.importForm.projectId = this.selectedProjectId || this.projectId || ''
      this.loadProductOptions()
      if (this.importForm.productId) {
        this.loadImportProjectOptions(this.importForm.productId).then(() => {
          const hasProject = (this.importProjectOptions || []).some(item => String(item.id) === String(this.importForm.projectId))
          if (this.importForm.projectId && !hasProject) {
            this.importForm.projectId = ''
          }
        })
      } else {
        this.importProjectOptions = []
      }
      this.caseImportDialogVisible = true
    },
    handleImportProductChange(productId) {
      this.importForm.projectId = ''
      this.loadImportProjectOptions(productId)
    },
    openAiDocumentCreateDialog() {
      if (!this.selectedProductId || !this.selectedProjectId) {
        this.$message.warning('请先选择产品与项目')
        return
      }
      this.$nextTick(() => {
        const panel = this.$refs.aiDocumentPanel
        if (panel && typeof panel.openCreateDialog === 'function') {
          panel.openCreateDialog()
        }
      })
    },
    resetImportDialog() {
      this.importFile = null
      this.importForm = {
        productId: '',
        projectId: ''
      }
      this.importProjectOptions = []
      if (this.$refs.importFileInput) {
        this.$refs.importFileInput.value = ''
      }
    },
    triggerImportFileSelect() {
      this.$refs.importFileInput && this.$refs.importFileInput.click()
    },
    onImportFileChange(event) {
      const files = event && event.target && event.target.files ? event.target.files : []
      const file = files[0]
      this.setImportFile(file)
    },
    onImportFileDrop(event) {
      const files = event && event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : []
      const file = files[0]
      this.setImportFile(file)
    },
    setImportFile(file) {
      if (!file) {
        return
      }
      const lowerName = String(file.name || '').toLowerCase()
      const isExcel = lowerName.endsWith('.xls') || lowerName.endsWith('.xlsx')
      if (!isExcel) {
        this.$message.warning('仅支持 .xls 或 .xlsx 文件')
        return
      }
      const maxSize = 20 * 1024 * 1024
      if (file.size > maxSize) {
        this.$message.warning('文件大小不能超过 20MB')
        return
      }
      this.importFile = file
    },
    downloadImportTemplate() {
      const projectId = this.importForm.projectId || this.selectedProjectId
      if (!projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      downloadCaseImportTemplate(projectId).then(res => {
        const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = '用例导入模板.xlsx'
        link.click()
        window.URL.revokeObjectURL(url)
      })
    },
    ensureExportBlob(res) {
      const blob = res instanceof Blob ? res : new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const type = String(blob.type || '').toLowerCase()
      if (type.indexOf('application/json') === -1) {
        return Promise.resolve(blob)
      }
      return blob.text().then(text => {
        try {
          const data = JSON.parse(text)
          throw new Error(data.message || data.msg || '用例导出失败')
        } catch (err) {
          if (err && err.message && err.message !== 'Unexpected end of JSON input') {
            throw err
          }
          throw new Error('用例导出失败')
        }
      })
    },
    formatFileSize(size) {
      const value = Number(size) || 0
      if (value >= 1024 * 1024) {
        return `${(value / 1024 / 1024).toFixed(2)} MB`
      }
      if (value >= 1024) {
        return `${(value / 1024).toFixed(1)} KB`
      }
      return `${value} B`
    },
    handleCaseExport() {
      const productId = this.selectedProductId
      const projectId = this.selectedProjectId || this.projectId
      if (!projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.caseExporting = true
      this.caseExportProgressVisible = true
      this.caseExportProgress = 5
      this.caseExportProgressText = '正在请求导出数据，请稍候...'
      exportCaseExcel(productId, projectId, event => {
        const loaded = event && event.loaded ? event.loaded : 0
        const total = event && event.total ? event.total : 0
        if (total > 0) {
          this.caseExportProgress = Math.min(95, Math.round((loaded / total) * 100))
          this.caseExportProgressText = `正在下载文件：${this.formatFileSize(loaded)} / ${this.formatFileSize(total)}`
        } else {
          this.caseExportProgress = Math.min(90, this.caseExportProgress + 10)
          this.caseExportProgressText = `正在生成文件，已接收 ${this.formatFileSize(loaded)}`
        }
      }).then(res => this.ensureExportBlob(res)).then(blob => {
        this.caseExportProgress = 100
        this.caseExportProgressText = '文件已生成，正在触发浏览器下载...'
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        const project = (this.projectOptions || []).find(item => Number(item.id) === Number(projectId))
        link.href = url
        link.download = `${(project && project.name) || '测试用例'}-全量用例.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        this.$message.success('用例导出成功')
        setTimeout(() => {
          this.caseExportProgressVisible = false
        }, 800)
      }).catch(err => {
        this.caseExportProgressText = (err && err.message) || '用例导出失败'
        this.$message.error(this.caseExportProgressText)
      }).finally(() => {
        this.caseExporting = false
      })
    },
    submitCaseImport() {
      const productId = this.importForm.productId
      const projectId = this.importForm.projectId
      if (!productId) {
        this.$message.warning('请先选择产品')
        return
      }
      if (!projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      if (!this.importFile) {
        this.$message.warning('请先选择导入文件')
        return
      }
      this.importSubmitting = true
      importCaseExcel(productId, projectId, this.importFile).then(() => {
        this.$message.success('导入并解析成功')
        this.caseImportDialogVisible = false
        this.selectedProductId = productId
        this.selectedProjectId = projectId
        this.projectId = projectId
        this.moduleQueryForm.projectId = projectId
        saveLastProductProjectCache(productId, projectId)
        this.loadProjectOptionsByProduct(productId)
        this.fetchList()
        this.fetchAiCaseList()
        this.fetchCaseMindmapData()
      }).finally(() => {
        this.importSubmitting = false
      })
    },
    openAiCaseDetail(row) {
      const caseId = row && row.id
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      if (caseId === undefined || caseId === null || caseId === '') {
        this.$message.warning('无法识别用例')
        return
      }
      this.aiCaseDetailVisible = true
      this.aiCaseDetailLoading = true
      this.aiCaseDetail = {}
      getCaseDetail(this.projectId, caseId)
        .then(res => {
          const data = (res && res.data) || res || {}
          this.aiCaseDetail = data && typeof data === 'object' ? data : {}
        })
        .catch(() => {
          this.aiCaseDetail = {}
        })
        .finally(() => {
          this.aiCaseDetailLoading = false
        })
    },
    resetAiCaseDetailDialog() {
      this.aiCaseDetail = {}
      this.aiCaseDetailLoading = false
    },
    formatAiCaseDetailSteps(steps) {
      if (!steps) return ''
      if (typeof steps === 'string') return steps
      if (Array.isArray(steps)) {
        return steps
          .map(item => {
            if (item === null || item === undefined) return ''
            if (typeof item === 'string') return item
            return (
              item.action ||
              item.step ||
              item.description ||
              item.text ||
              item.content ||
              ''
            )
          })
          .filter(Boolean)
          .join('\n')
      }
      return String(steps)
    },
    extractExpectedFromSteps(steps) {
      if (!Array.isArray(steps) || steps.length === 0) return ''
      const first = steps[0]
      if (first && typeof first === 'object') {
        return (
          first.expected ||
          first.expected_result ||
          first.expectedResult ||
          ''
        )
      }
      return ''
    },
    openAutoGenDialog(row) {
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      if (!row || row.id === undefined || row.id === null || row.id === '') {
        this.$message.warning('用例数据无效')
        return
      }
      this.autoGenRow = row
      this.autoGenForm = { automationType: 'ui', prompt: '' }
      this.autoGenDialogVisible = true
      this.$nextTick(() => {
        if (this.$refs.autoGenFormRef) {
          this.$refs.autoGenFormRef.clearValidate()
        }
      })
    },
    resetAutoGenDialog() {
      this.autoGenRow = null
      this.autoGenForm = { automationType: 'ui', prompt: '' }
      this.$nextTick(() => {
        if (this.$refs.autoGenFormRef) {
          this.$refs.autoGenFormRef.clearValidate()
        }
      })
    },
    submitAutoGen() {
      if (!this.$refs.autoGenFormRef) {
        return
      }
      this.$refs.autoGenFormRef.validate(valid => {
        if (!valid) return
        if (!this.projectId || !this.autoGenRow || !this.autoGenRow.id) {
          return
        }
        this.autoGenSubmitting = true
        const row = this.autoGenRow
        const product = (this.productOptions || []).find(p => String(p.id) === String(this.selectedProductId))
        const project = (this.projectOptions || []).find(p => String(p.id) === String(this.projectId))
        const productName = (product && product.name) || ''
        getCaseDetail(this.projectId, row.id)
          .then(res => {
            const d = (res && res.data) || res || {}
            const caseKey = d.caseKey || d.case_key || row.caseKey || row.case_key || ''
            const moduleName = d.moduleName || d.module_name || row.moduleName || row.module_name || ''
            const projectName =
              d.projectName ||
              d.project_name ||
              row.projectName ||
              row.project_name ||
              (project && project.name) ||
              ''
            const steps = this.formatAiCaseDetailSteps(d.steps) || ''
            let expectedResults = d.expectedResults != null ? d.expectedResults : d.expected_results
            if (expectedResults === undefined || expectedResults === null || expectedResults === '') {
              expectedResults = this.extractExpectedFromSteps(d.steps)
            }
            if (expectedResults !== undefined && expectedResults !== null && typeof expectedResults !== 'string') {
              expectedResults = String(expectedResults)
            }
            return generateCaseAutomation({
              projectId: this.projectId,
              caseId: row.id,
              automationType: this.autoGenForm.automationType,
              prompt: String(this.autoGenForm.prompt || '').trim(),
              caseKey,
              moduleName,
              productName,
              projectName,
              steps,
              expectedResults: expectedResults || ''
            })
          })
          .then(res => {
            const msg = (res && (res.msg || res.message)) || '已提交生成任务'
            this.$message.success(msg)
            this.autoGenDialogVisible = false
          })
          .catch(() => {})
          .finally(() => {
            this.autoGenSubmitting = false
          })
      })
    },
    goEditor(row) {
      this.$router.push({
        path: '/test-platform/case/editor',
        query: {
          productId: this.selectedProductId || undefined,
          projectId: this.projectId,
          caseId: row && row.id
        }
      })
    },
    goReview(row) {
      this.$router.push({ path: '/test-platform/case/review', query: { projectId: this.projectId, caseId: row.id } })
    },
    handleCopyCase(row) {
      copyCase(this.projectId, row.id).then(() => {
        this.$message({ type: 'success', message: '复制成功' })
        if (this.activeTab === 'ai-case-import') {
          this.fetchAiCaseList()
        } else {
          this.fetchList()
        }
      })
    },
    remove(row) {
      this.$confirm('确认删除该用例吗？', '提示', { type: 'warning' }).then(() => {
        deleteCase(this.projectId, row.id).then(() => {
          this.$message({ type: 'success', message: '删除成功' })
          if (this.activeTab === 'ai-case-import') {
            this.fetchAiCaseList()
          } else {
            this.fetchList()
          }
        })
      }).catch(() => {})
    },
    cleanParams(params) {
      return Object.keys(params).reduce((result, key) => {
        if (Array.isArray(params[key])) {
          if (params[key].length > 0) result[key] = params[key]
          return result
        }
        if (params[key] !== '' && params[key] !== undefined && params[key] !== null) {
          result[key] = params[key]
        }
        return result
      }, {})
    },
    normalizeCaseKeys(value) {
      if (Array.isArray(value)) {
        return value.map(item => String(item || '').trim()).filter(Boolean)
      }
      return String(value || '')
        .split(/[\s,，;；]+/)
        .map(item => item.trim())
        .filter(Boolean)
    },
    formatPriority(value) {
      const map = { 0: 'P0', 1: 'P1', 2: 'P2', 3: 'P3' }
      return map[value] || value
    },
    formatCaseType(value) {
      const map = { 1: '功能', 2: '性能', 3: '安全', 4: '接口' }
      return map[value] || value
    },
    formatStatus(value) {
      const map = { 0: '已删除/待恢复', 1: '正常', 2: '已废弃', 3: '评审中', 4: '评审通过' }
      return map[value] || value
    },
    formatIsAuto(value) {
      const map = { 0: '未实现', 1: '已实现' }
      return map[value] || value
    },
    formatTags(tags) {
      return Array.isArray(tags) ? tags.join('、') : (tags || '')
    }
  },
  created() {
    this.loadProductOptions().then(() => {
      const routeProductId = this.$route.query.productId ? Number(this.$route.query.productId) : ''
      if (routeProductId) {
        this.selectedProductId = routeProductId
        return this.loadProjectOptionsByProduct(routeProductId)
      }
      if (this.selectedProjectId) {
        return getProjectDetail(this.selectedProjectId).then(res => {
          const data = res && res.data ? res.data : res || {}
          const productId = data.productId || data.product_id || ''
          if (productId) {
            this.selectedProductId = productId
            return this.loadProjectOptionsByProduct(productId)
          }
        }).catch(() => {})
      }
      return this.restoreSharedProductProjectCache()
    }).finally(() => {
      if (this.selectedProjectId) {
        this.projectId = this.selectedProjectId
        this.moduleQueryForm.projectId = this.selectedProjectId
        this.fetchModuleList()
        this.fetchList()
        if (this.activeTab === 'ai-case-import') {
          this.fetchAiCaseList()
          this.fetchAiDocList()
          this.fetchAiSkillRuleOptions()
        }
        this.checkAiGenerationStatus()
      }
    })
  },
  mounted() {
  },
  beforeDestroy() {
    this.stopAiGenerationStatusPolling()
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}

.toolbar-wrap {
  text-align: right;
  margin-top: 8px;
}

.module-list-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.case-action-buttons-item {
  float: right;
  margin-right: 0 !important;
}

.more-filter-wrap {
  padding: 4px 0;
}

.more-filter-footer {
  border-top: 1px solid #ebeef5;
  text-align: right;
  padding-top: 10px;
}

.column-setting-wrap {
  max-height: 320px;
  overflow-y: auto;
}

.column-setting-title {
  color: #606266;
  font-weight: 500;
  margin-bottom: 8px;
}

.case-export-progress-panel {
  padding: 8px 4px 4px;
}

.case-export-progress-title {
  color: #f8fafc;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
}

.case-export-progress-desc {
  color: #94a3b8;
  font-size: 13px;
  line-height: 20px;
  margin-bottom: 14px;
}

.case-import-panel {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 28px 24px;
  text-align: center;
}

.case-import-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  color: #fff;
  background: #1e40af;
  font-weight: 600;
  margin-bottom: 8px;
}

.case-import-title {
  font-size: 28px;
  color: #f8fafc;
  margin-bottom: 6px;
}

.case-import-subtitle {
  color: #94a3b8;
  margin-bottom: 16px;
}

.case-import-form {
  max-width: 520px;
  margin: 0 auto 16px;
  text-align: left;
}

.case-import-form /deep/ .el-form-item {
  margin-bottom: 12px;
}

.case-import-form /deep/ .el-form-item__label {
  color: #cbd5e1;
}

.case-import-dropzone {
  border: 1px dashed rgba(56, 189, 248, 0.36);
  border-radius: 4px;
  padding: 28px 20px;
  margin: 0 auto;
  max-width: 520px;
  background: #1e293b;
}

.case-import-drop-text {
  color: #cbd5e1;
  margin-bottom: 10px;
}

.link-text {
  color: #1e40af;
  cursor: pointer;
}

.case-import-file-tip {
  color: #94a3b8;
}

.case-import-file-name {
  margin-top: 8px;
  color: #f8fafc;
}

.case-import-actions {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.hidden-file-input {
  display: none;
}

.document-source-panel-host--hidden {
  position: fixed;
  right: 0;
  bottom: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  z-index: -1;
}

.ai-case-import-wrap {
  margin-top: 4px;
}

.ai-case-import-tip {
  margin: 0 0 12px;
  padding: 10px 12px;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 4px;
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.5;
}

.ai-case-query-form {
  margin-bottom: 8px;
}

.ai-gen-progress-bar {
  position: sticky;
  top: 0;
  z-index: 12;
  margin: 8px 0 12px;
  padding: 12px 16px;
  background: #10202c;
  border: 1px solid rgba(52, 211, 153, 0.36);
  border-radius: 4px;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
}

.ai-gen-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.ai-gen-progress-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #dcfce7;
  font-weight: 600;
}

.ai-gen-progress-title .el-icon-loading {
  color: #34d399;
  font-size: 16px;
}

.ai-gen-progress-count {
  flex: none;
  color: #a7f3d0;
  font-size: 13px;
}

.ai-gen-current-module {
  margin-bottom: 8px;
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
}

.ai-gen-log-list {
  max-height: 120px;
  overflow-y: auto;
  margin: 8px 0;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.36);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 4px;
}

.ai-gen-log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #cbd5e1;
  font-size: 12px;
  line-height: 1.6;
}

.ai-gen-log-item.is-warning {
  color: #fde68a;
}

.ai-gen-log-item.is-error {
  color: #fecaca;
}

.ai-gen-log-time {
  flex: none;
  color: #94a3b8;
}

.ai-gen-log-agent {
  flex: none;
  color: #86efac;
  font-weight: 600;
}

.ai-gen-log-message {
  min-width: 0;
  word-break: break-word;
}

.ai-gen-params-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: #162033;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  font-size: 13px;
  color: #cbd5e1;
}

.ai-gen-params-label {
  font-weight: 600;
  color: #f8fafc;
}

.ai-gen-params-hint {
  margin-left: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.ai-doc-block {
  margin-bottom: 16px;
}

.ai-doc-block-title {
  font-weight: 600;
  font-size: 13px;
  color: #f8fafc;
  margin-bottom: 8px;
}

.ai-skill-rule-block .ai-skill-rule-selects {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-case-table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.ai-case-table-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.ai-case-table-title {
  font-weight: 600;
  font-size: 14px;
  color: #f8fafc;
  margin-bottom: 0;
}

/* 用例脑图 - release 版 el-tree 卡片展示 */
.mindmap-wrap {
  margin-top: 8px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  background: #1e293b;
  padding: 14px 12px;
  min-height: 280px;
  overflow: auto;
}

.xmind-tree {
  min-width: 980px;
  background: transparent;
}

.xmind-tree /deep/ .el-tree-node {
  position: relative;
}

.xmind-tree /deep/ .el-tree-node__content {
  height: auto;
  padding: 8px 0;
}

.xmind-tree /deep/ .el-tree-node__children {
  position: relative;
  margin-left: 12px;
  padding-left: 22px;
}

.xmind-tree /deep/ .el-tree-node__children:before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 10px;
  border-left: 1px solid #b7d0e8;
}

.xmind-tree /deep/ .el-tree-node__content:before {
  content: '';
  position: absolute;
  left: -14px;
  top: 50%;
  width: 14px;
  border-top: 1px solid #8fb8de;
}

.xmind-tree /deep/ .el-tree > .el-tree-node > .el-tree-node__content:before {
  display: none;
}

.mindmap-node {
  display: inline-flex;
  flex-direction: column;
  gap: 6px;
  min-width: 220px;
  max-width: 760px;
  background: #111827;
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 8px;
  padding: 8px 10px;
  box-shadow: 0 1px 8px rgba(56, 189, 248, 0.12);
}

.mindmap-node-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

.mindmap-node-case-status {
  flex-shrink: 0;
  margin-top: 1px;
}

.mindmap-node-wrap {
  display: inline-flex;
  align-items: flex-start;
}

.mindmap-node-title {
  flex: 1;
  min-width: 0;
  color: #f8fafc;
  font-weight: 600;
  line-height: 1.4;
  word-break: break-word;
}

.mindmap-node-project {
  border-color: #67c23a;
  box-shadow: 0 1px 6px rgba(103, 194, 58, 0.16);
}

.mindmap-node-module {
  border-color: #e6a23c;
  box-shadow: 0 1px 6px rgba(230, 162, 60, 0.14);
}

.mindmap-node-case {
  border-color: #7fb3e3;
}

.mindmap-node-active {
  border-color: #fbbf24;
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.22), 0 1px 8px rgba(56, 189, 248, 0.12);
}

.mindmap-inline-detail {
  display: inline-flex;
  align-items: stretch;
  margin-left: 14px;
}

.mindmap-inline-detail-line {
  width: 18px;
  margin-top: 22px;
  border-top: 1px solid #8fb8de;
}

.mindmap-inline-detail-card {
  width: 420px;
  max-width: 620px;
  background: #111827;
  border: 1px solid rgba(56, 189, 248, 0.26);
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 1px 8px rgba(56, 189, 248, 0.12);
}

.mindmap-inline-detail-title {
  color: #f8fafc;
  font-weight: 600;
}

.mindmap-inline-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.mindmap-inline-detail-item {
  color: #cbd5e1;
  line-height: 1.6;
  margin-bottom: 6px;
  white-space: pre-wrap;
}

.mindmap-inline-detail-item:last-child {
  margin-bottom: 0;
}

.mindmap-inline-actions {
  text-align: right;
  margin-top: 8px;
}

.mindmap-node-meta {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.mindmap-meta-text {
  color: #94a3b8;
  font-size: 12px;
}

.mindmap-empty {
  color: #94a3b8;
  text-align: center;
  line-height: 220px;
}

.ai-case-detail-wrap {
  min-height: 120px;
}

.ai-case-detail-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 14px;
}

.ai-case-detail-desc {
  margin-bottom: 16px;
}

.ai-case-detail-block {
  margin-top: 14px;
}

.ai-case-detail-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}

.ai-case-detail-text {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px 12px;
  border-radius: 4px;
}

.ai-case-detail-empty {
  text-align: center;
  color: #94a3b8;
  padding: 32px 0;
  font-size: 13px;
}

.auto-gen-case-title {
  font-weight: 500;
  line-height: 1.5;
  word-break: break-word;
}

body.theme-light .ai-case-import-tip {
  color: #475569;
}

body.theme-light .case-export-progress-title {
  color: #111827;
}

body.theme-light .case-export-progress-desc {
  color: #64748b;
}

body.theme-light .ai-gen-progress-bar {
  background: #f0fdf4;
  border-color: #bbf7d0;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.1);
}

body.theme-light .ai-gen-progress-title {
  color: #166534;
}

body.theme-light .ai-gen-progress-count {
  color: #15803d;
}

body.theme-light .ai-gen-current-module {
  color: #334155;
}

body.theme-light .ai-gen-log-list {
  background: rgba(255, 255, 255, 0.72);
  border-color: #bbf7d0;
}

body.theme-light .ai-gen-log-item {
  color: #334155;
}

body.theme-light .ai-gen-log-item.is-warning {
  color: #b45309;
}

body.theme-light .ai-gen-log-item.is-error {
  color: #b91c1c;
}

body.theme-light .ai-gen-log-time {
  color: #64748b;
}

body.theme-light .ai-gen-log-agent {
  color: #15803d;
}

body.theme-light .ai-gen-params-bar {
  background: #f1f6ff;
  border-color: #dbe5f3;
  color: #334155;
}

body.theme-light .ai-gen-params-label,
body.theme-light .ai-doc-block-title,
body.theme-light .ai-case-table-title {
  color: #111827;
}

body.theme-light .ai-gen-params-hint {
  color: #64748b;
}

body.theme-light .mindmap-wrap {
  background: #f8fbff;
  border-color: #dbe5f3;
}

body.theme-light .xmind-tree /deep/ .el-tree-node__children:before {
  border-left-color: #cbd5e1;
}

body.theme-light .xmind-tree /deep/ .el-tree-node__content:before {
  border-top-color: #94a3b8;
}

body.theme-light .mindmap-node {
  background: #ffffff;
  border-color: #dbe5f3;
  box-shadow: 0 1px 6px rgba(37, 99, 235, 0.08);
}

body.theme-light .mindmap-node-title {
  color: #111827;
}

body.theme-light .mindmap-node-project {
  border-color: #67c23a;
  box-shadow: 0 1px 6px rgba(103, 194, 58, 0.12);
}

body.theme-light .mindmap-node-module {
  border-color: #e6a23c;
  box-shadow: 0 1px 6px rgba(230, 162, 60, 0.1);
}

body.theme-light .mindmap-node-case {
  border-color: #93c5fd;
}

body.theme-light .mindmap-inline-detail-line {
  border-top-color: #94a3b8;
}

body.theme-light .mindmap-inline-detail-card {
  background: #ffffff;
  border-color: #dbe5f3;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
}

body.theme-light .mindmap-inline-detail-title {
  color: #111827;
}

body.theme-light .mindmap-inline-detail-item {
  color: #475569;
}

body.theme-light .mindmap-meta-text,
body.theme-light .mindmap-empty {
  color: #64748b;
}
</style>

<!-- 非 scoped：Tab / append-to-body 弹窗 / 日期范围在深浅色下与整站一致 -->
<style>
.case-list-tabs .el-tabs__item {
  color: #94a3b8;
}

.case-list-tabs .el-tabs__item:hover {
  color: #cbd5e1;
}

.case-list-tabs .el-tabs__item.is-active {
  color: #1e40af;
}

.case-list-tabs .el-tabs__nav-wrap::after {
  background-color: rgba(148, 163, 184, 0.18);
}

body.theme-light .case-list-tabs .el-tabs__item {
  color: #64748b;
}

body.theme-light .case-list-tabs .el-tabs__item:hover {
  color: #334155;
}

body.theme-light .case-list-tabs .el-tabs__item.is-active {
  color: #2563eb;
}

body.theme-light .case-list-tabs .el-tabs__nav-wrap::after {
  background-color: #e2e8f0;
}

.el-dialog.case-auto-gen-dialog {
  background: #111827;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.el-dialog.case-auto-gen-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.el-dialog.case-auto-gen-dialog .el-dialog__title,
.el-dialog.case-auto-gen-dialog .el-dialog__body,
.el-dialog.case-auto-gen-dialog .el-form-item__label {
  color: #e5e7eb;
}

.el-dialog.case-auto-gen-dialog .auto-gen-case-title {
  color: #f1f5f9;
}

.el-dialog.case-auto-gen-dialog .el-input__inner,
.el-dialog.case-auto-gen-dialog .el-textarea__inner,
.el-dialog.case-auto-gen-dialog .el-select .el-input__inner {
  background-color: #1e293b;
  border-color: rgba(148, 163, 184, 0.28);
  color: #f8fafc;
}

.el-dialog.case-auto-gen-dialog .el-input__inner::placeholder,
.el-dialog.case-auto-gen-dialog .el-textarea__inner::placeholder {
  color: #64748b;
}

body.theme-light .el-dialog.case-auto-gen-dialog {
  background: #ffffff;
  border-color: #e5e7eb;
}

body.theme-light .el-dialog.case-auto-gen-dialog .el-dialog__header {
  border-bottom-color: #ebeef5;
}

body.theme-light .el-dialog.case-auto-gen-dialog .el-dialog__title,
body.theme-light .el-dialog.case-auto-gen-dialog .el-dialog__body,
body.theme-light .el-dialog.case-auto-gen-dialog .el-form-item__label {
  color: #303133;
}

body.theme-light .el-dialog.case-auto-gen-dialog .auto-gen-case-title {
  color: #111827;
}

body.theme-light .el-dialog.case-auto-gen-dialog .el-input__inner,
body.theme-light .el-dialog.case-auto-gen-dialog .el-textarea__inner,
body.theme-light .el-dialog.case-auto-gen-dialog .el-select .el-input__inner {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
}

.page-wrap .el-date-editor .el-input__inner {
  background-color: #1e293b;
  border-color: rgba(148, 163, 184, 0.28);
  color: #f8fafc;
}

.page-wrap .el-date-editor .el-range-input {
  background-color: transparent;
  color: #f8fafc;
}

.page-wrap .el-date-editor .el-range-separator {
  color: #94a3b8;
}

.page-wrap .el-date-editor .el-range-input::placeholder {
  color: #64748b;
}

body.theme-light .page-wrap .el-date-editor .el-input__inner {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
}

body.theme-light .page-wrap .el-date-editor .el-range-input {
  color: #606266;
}

body.theme-light .page-wrap .el-date-editor .el-range-separator {
  color: #909399;
}

/* AI 用例详情弹窗（append-to-body） */
.el-dialog.case-ai-detail-dialog {
  background: #111827;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.el-dialog.case-ai-detail-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.el-dialog.case-ai-detail-dialog .el-dialog__title {
  color: #f8fafc;
}

.el-dialog.case-ai-detail-dialog .el-dialog__body {
  color: #e5e7eb;
}

.el-dialog.case-ai-detail-dialog .ai-case-detail-title {
  color: #f8fafc;
}

.el-dialog.case-ai-detail-dialog .ai-case-detail-label {
  color: #dbeafe;
}

.el-dialog.case-ai-detail-dialog .ai-case-detail-text {
  color: #e5e7eb;
  background: #1e293b;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.el-dialog.case-ai-detail-dialog .ai-case-detail-empty {
  color: #94a3b8;
}

.el-dialog.case-ai-detail-dialog .el-descriptions__body {
  background-color: #111827;
  color: #e5e7eb;
}

.el-dialog.case-ai-detail-dialog .el-descriptions-item__label {
  color: #94a3b8;
  background: #1f2937;
}

.el-dialog.case-ai-detail-dialog .el-descriptions-item__content {
  color: #e5e7eb;
  background: #111827;
}

.el-dialog.case-ai-detail-dialog .el-descriptions__body .el-descriptions__table {
  border-color: rgba(148, 163, 184, 0.2);
}

.el-dialog.case-ai-detail-dialog .el-descriptions__body .el-descriptions-item__cell {
  border-color: rgba(148, 163, 184, 0.2);
}

body.theme-light .el-dialog.case-ai-detail-dialog {
  background: #ffffff;
  border-color: #e5e7eb;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-dialog__header {
  border-bottom-color: #ebeef5;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-dialog__title {
  color: #303133;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-dialog__body {
  color: #303133;
}

body.theme-light .el-dialog.case-ai-detail-dialog .ai-case-detail-title {
  color: #111827;
}

body.theme-light .el-dialog.case-ai-detail-dialog .ai-case-detail-label {
  color: #303133;
}

body.theme-light .el-dialog.case-ai-detail-dialog .ai-case-detail-text {
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

body.theme-light .el-dialog.case-ai-detail-dialog .ai-case-detail-empty {
  color: #909399;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-descriptions__body {
  background-color: #ffffff;
  color: #303133;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-descriptions-item__label {
  color: #606266;
  background: #fafafa;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-descriptions-item__content {
  color: #303133;
  background: #ffffff;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-descriptions__body .el-descriptions__table {
  border-color: #ebeef5;
}

body.theme-light .el-dialog.case-ai-detail-dialog .el-descriptions__body .el-descriptions-item__cell {
  border-color: #ebeef5;
}
</style>
