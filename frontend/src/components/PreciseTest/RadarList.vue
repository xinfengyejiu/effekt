<template>
  <div class="page-wrap precise-page">
    <page-section title="变更影响雷达">
      <template slot="extra">
        <el-button size="small" @click="openTrace">代码追溯</el-button>
        <el-button size="small" type="primary" @click="openCreate">新建雷达分析</el-button>
      </template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品名称">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="请选择产品" style="width:180px;" @change="onQueryProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="请先选择产品" style="width:180px;">
            <el-option v-for="item in queryProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model.trim="queryForm.keyword" clearable placeholder="编号/标题/commit" style="width:200px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchList">查询</el-button>
          <el-button :disabled="loading" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="分析编号" min-width="150" show-overflow-tooltip>
          <template slot-scope="scope">
            <el-link type="primary" @click="goDetail(scope.row)">{{ scope.row.analysis_no || scope.row.analysisNo || scope.row.id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="160" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.title || '-' }}</template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template slot-scope="scope">{{ scope.row.source_type || scope.row.sourceType || '-' }}</template>
        </el-table-column>
        <el-table-column label="Commit" min-width="120" show-overflow-tooltip>
          <template slot-scope="scope">{{ shortCommit(scope.row.commit_id || scope.row.commitId || scope.row.target_commit) }}</template>
        </el-table-column>
        <el-table-column label="产品" min-width="110" show-overflow-tooltip>
          <template slot-scope="scope">{{ preciseProductName(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="项目" min-width="120" show-overflow-tooltip>
          <template slot-scope="scope">{{ preciseProjectName(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager-wrap">
        <el-pagination background layout="total, sizes, prev, pager, next, jumper"
          :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total"
          @size-change="handleSizeChange" @current-change="handleCurrentChange" />
      </div>
    </page-section>

    <el-dialog title="新建变更影响雷达" :visible.sync="dialogVisible" width="720px"
      :close-on-click-modal="false" :close-on-press-escape="false">
      <el-form ref="createForm" :model="form" :rules="rules" label-width="120px" size="small">
        <el-form-item label="产品名称" prop="productId">
          <el-select v-model="form.productId" clearable filterable placeholder="请选择产品" style="width:100%;" @change="onFormProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="projectId">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="请先选择产品" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model.trim="form.title" placeholder="可选" /></el-form-item>
        <el-form-item label="Commit/MR URL">
          <el-input v-model.trim="form.gitUrl" type="textarea" :rows="2" placeholder="粘贴 GitLab Commit 或 MR 链接（含 commit_id）" @blur="onUrlBlur" />
        </el-form-item>
        <el-form-item label="Git仓库" prop="repositoryUrl">
          <el-input v-model.trim="form.repositoryUrl" placeholder="可由 URL 自动解析，或手动填写" />
        </el-form-item>
        <el-form-item label="目标 Commit" prop="targetCommit">
          <el-input v-model.trim="form.targetCommit" placeholder="可由 URL 自动解析" />
        </el-form-item>
        <el-form-item label="Base Commit">
          <el-input v-model.trim="form.baseCommit" placeholder="可选，默认取 commit^" />
        </el-form-item>
        <el-form-item label="分支">
          <el-input v-model.trim="form.branchName" placeholder="可选" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">启动分析</el-button>
      </span>
    </el-dialog>

    <el-dialog title="代码追溯：查 Commit ID / 时间" :visible.sync="traceVisible" width="820px"
      :close-on-click-modal="false" :close-on-press-escape="false">
      <el-form :model="traceForm" label-width="100px" size="small">
        <el-form-item label="Git仓库" required>
          <el-input v-model.trim="traceForm.repositoryUrl" placeholder="如 https://xxx/group/repo.git" />
        </el-form-item>
        <el-form-item label="文件路径">
          <el-input v-model.trim="traceForm.filePath" placeholder="建议填写，如 app/api/controller/caseController.py" />
        </el-form-item>
        <el-form-item label="代码片段" required>
          <el-input v-model="traceForm.code" type="textarea" :rows="4" placeholder="粘贴变更相关的有效代码行" />
        </el-form-item>
      </el-form>
      <el-table v-if="traceRows.length" :data="traceRows" border size="small" max-height="320">
        <el-table-column label="Git Commit ID" min-width="260">
          <template slot-scope="scope"><span style="font-family:Consolas,monospace;word-break:break-all;">{{ scope.row.commit_id }}</span></template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="170" prop="date" />
        <el-table-column label="作者" width="110" prop="author" show-overflow-tooltip />
        <el-table-column label="说明" min-width="180" prop="remark" show-overflow-tooltip />
      </el-table>
      <div v-else-if="traceSearched" style="color:#909399;padding:8px 0;">未命中历史提交</div>
      <span slot="footer">
        <el-button @click="traceVisible=false">关闭</el-button>
        <el-button type="primary" :loading="traceLoading" @click="submitTrace">查询</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getImpactRadarList, runImpactRadar, parseImpactRadarUrl, traceImpactRadarCode } from '@/api/impactRadarApi'
import productProjectSelectMixin from './productProjectSelectMixin'

const STATUS = { 1: '待解析', 2: '已解析', 3: 'AI已分析', 4: '已推荐', 5: '执行中', 6: '已完成', 7: '失败' }

export default {
  name: 'ImpactRadarList',
  components: { PageSection },
  mixins: [productProjectSelectMixin],
  data() {
    return {
      loading: false,
      saving: false,
      dialogVisible: false,
      traceVisible: false,
      traceLoading: false,
      traceSearched: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      queryForm: { productId: '', projectId: '', keyword: '' },
      form: {},
      traceForm: { repositoryUrl: '', filePath: '', code: '' },
      traceRows: [],
      rules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        repositoryUrl: [{ required: true, message: '请填写 Git 仓库', trigger: 'blur' }],
        targetCommit: [{ required: true, message: '请填写目标 Commit', trigger: 'blur' }]
      }
    }
  },
  created() { this.fetchList() },
  methods: {
    listOf(res) {
      const d = res && res.data ? res.data : res || {}
      return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 }
    },
    fetchList() {
      this.loading = true
      getImpactRadarList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize }))
        .then(res => {
          const d = this.listOf(res)
          this.rows = d.rows
          this.total = d.total || this.rows.length
          this.fillPreciseProjectNames(this.rows)
        })
        .finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', keyword: '' }
      this.queryProjectOptions = []
      this.pageNo = 1
      this.fetchList()
    },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    onQueryProductChange(productId) { this.queryForm.projectId = ''; this.loadProjectOptions(productId, 'queryProjectOptions') },
    onFormProductChange(productId) { this.form.projectId = ''; this.loadProjectOptions(productId, 'projectOptions') },
    openCreate() {
      this.form = { productId: '', projectId: '', gitUrl: '', repositoryUrl: '', targetCommit: '', baseCommit: '', branchName: '', title: '' }
      this.projectOptions = []
      this.dialogVisible = true
    },
    openTrace() {
      this.traceForm = { repositoryUrl: '', filePath: '', code: '' }
      this.traceRows = []
      this.traceSearched = false
      this.traceVisible = true
    },
    submitTrace() {
      if (!(this.traceForm.repositoryUrl || '').trim()) {
        this.$message.warning('请填写 Git 仓库')
        return
      }
      if (!(this.traceForm.code || '').trim()) {
        this.$message.warning('请输入代码片段')
        return
      }
      this.traceLoading = true
      this.traceSearched = false
      traceImpactRadarCode({
        repository_url: this.traceForm.repositoryUrl,
        file_path: this.traceForm.filePath,
        code: this.traceForm.code
      }).then(res => {
        const d = (res && res.data) || res || {}
        this.traceRows = d.commits || []
        this.traceSearched = true
        if (!this.traceRows.length) this.$message.warning('未命中历史提交')
        else this.$message.success('找到 ' + this.traceRows.length + ' 条相关提交')
      }).finally(() => { this.traceLoading = false })
    },
    onUrlBlur() {
      if (!this.form.gitUrl) return
      parseImpactRadarUrl({ git_url: this.form.gitUrl }).then(res => {
        const d = (res && res.data) || res || {}
        if (d.repository_url && !this.form.repositoryUrl) this.form.repositoryUrl = d.repository_url
        if (d.commit_id && !this.form.targetCommit) this.form.targetCommit = d.commit_id
      }).catch(() => {})
    },
    submitCreate() {
      this.$refs.createForm.validate(valid => {
        if (!valid) return
        this.saving = true
        const payload = this.buildPreciseProjectPayload({
          productId: this.form.productId,
          projectId: this.form.projectId,
          title: this.form.title,
          git_url: this.form.gitUrl,
          repository_url: this.form.repositoryUrl,
          target_commit: this.form.targetCommit,
          base_commit: this.form.baseCommit,
          branch_name: this.form.branchName,
          options: { enable_lineage: true, enable_recommend: true }
        })
        runImpactRadar(payload).then(res => {
          this.$message.success('雷达分析完成')
          this.dialogVisible = false
          const data = (res && res.data) || {}
          const id = (data.run && (data.run.id || data.run.precise_analysis_id)) || data.precise_analysis_id
          if (id) this.$router.push({ path: '/precise/radar/detail', query: { id } })
          else this.fetchList()
        }).finally(() => { this.saving = false })
      })
    },
    goDetail(row) { this.$router.push({ path: '/precise/radar/detail', query: { id: row.id } }) },
    shortCommit(v) { return v ? String(v).slice(0, 10) : '-' },
    statusLabel(s) { return STATUS[s] || (s == null ? '-' : String(s)) },
    statusTag(s) { return { 1: 'info', 2: 'primary', 3: 'warning', 4: 'success', 5: 'warning', 6: 'success', 7: 'danger' }[s] || 'info' }
  }
}
</script>

<style scoped>
.pager-wrap { margin-top: 16px; text-align: right; }
</style>
