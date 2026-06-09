<template>
  <div class="page-wrap performance-page">
    <page-section title="测试机资源池">
      <template slot="extra"><el-button size="small" type="primary" @click="openCreate">新增测试机</el-button></template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="工具"><el-select v-model="queryForm.toolType" clearable placeholder="全部" style="width:120px;"><el-option label="JMeter" value="jmeter" /><el-option label="k6" value="k6" /><el-option label="Locust" value="locust" /></el-select></el-form-item>
        <el-form-item label="状态"><el-select v-model="queryForm.status" clearable placeholder="全部" style="width:120px;"><el-option label="可用" :value="1" /><el-option label="停用" :value="0" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="fetchList">查询</el-button><el-button @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column prop="name" label="机器名称" min-width="160" />
        <el-table-column label="地址" min-width="180"><template slot-scope="scope">{{ scope.row.host || scope.row.ip || scope.row.host_ip || '-' }}</template></el-table-column>
        <el-table-column label="工具" width="110"><template slot-scope="scope">{{ toolText(scope.row) }}</template></el-table-column>
        <el-table-column label="容量" width="100"><template slot-scope="scope">{{ scope.row.capacity || scope.row.max_concurrent_tasks || scope.row.maxConcurrentTasks || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="90"><template slot-scope="scope"><el-tag size="mini" :type="Number(scope.row.status) === 1 ? 'success' : 'info'">{{ Number(scope.row.status) === 1 ? '可用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="更新时间" min-width="160"><template slot-scope="scope">{{ scope.row.updated_time || scope.row.updatedTime || '-' }}</template></el-table-column>
        <el-table-column label="操作" width="140" fixed="right"><template slot-scope="scope"><el-button type="text" @click="openEdit(scope.row)">编辑</el-button><el-button type="text" class="danger-text" @click="deleteRow(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
      <div class="pager-wrap"><el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" /></div>
    </page-section>

    <el-dialog :title="dialogMode === 'create' ? '新增测试机' : '编辑测试机'" :visible.sync="dialogVisible" width="540px" @close="resetForm">
      <el-form ref="form" :model="form" :rules="rules" label-width="100px" size="small">
        <el-form-item label="机器名称" prop="name"><el-input v-model.trim="form.name" maxlength="128" /></el-form-item>
        <el-form-item label="Host/IP" prop="host"><el-input v-model.trim="form.host" maxlength="128" /></el-form-item>
        <el-form-item label="Jenkins Label" prop="jenkinsLabel"><el-input v-model.trim="form.jenkinsLabel" maxlength="128" placeholder="用于 Runner 选择节点" /></el-form-item>
        <el-form-item label="工具类型" prop="toolType"><el-select v-model="form.toolType" style="width:100%;"><el-option label="JMeter" value="jmeter" /><el-option label="k6" value="k6" /><el-option label="Locust" value="locust" /></el-select></el-form-item>
        <el-form-item label="容量"><el-input-number v-model="form.capacity" :min="1" :max="100000" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status" style="width:100%;"><el-option label="可用" :value="1" /><el-option label="停用" :value="0" /></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model.trim="form.description" type="textarea" :rows="3" maxlength="255" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button size="small" @click="dialogVisible = false">取消</el-button><el-button size="small" type="primary" :loading="submitting" @click="submitForm">确定</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { createPerformanceMachine, deletePerformanceMachine, getPerformanceMachineList, updatePerformanceMachine } from '@/api/performanceApi'
const defaultForm = () => ({ id: '', name: '', host: '', jenkinsLabel: '', toolType: 'jmeter', capacity: 1, status: 1, description: '' })
export default {
  name: 'PerformanceMachinePool',
  components: { PageSection },
  data() { return { loading: false, submitting: false, dialogVisible: false, dialogMode: 'create', rows: [], total: 0, pageNo: 1, pageSize: 20, queryForm: { toolType: '', status: '' }, form: defaultForm(), rules: { name: [{ required: true, message: '请输入机器名称', trigger: 'blur' }], host: [{ required: true, message: '请输入Host/IP', trigger: 'blur' }], jenkinsLabel: [{ required: true, message: '请输入 Jenkins Label', trigger: 'blur' }], toolType: [{ required: true, message: '请选择工具类型', trigger: 'change' }] } } },
  created() { this.fetchList() },
  methods: {
    listOf(res) { const d = res && res.data ? res.data : res || {}; return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 } },
    fetchList() { this.loading = true; getPerformanceMachineList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => { const d = this.listOf(res); this.rows = d.rows; this.total = d.total || this.rows.length }).catch(() => { this.rows = []; this.total = 0 }).finally(() => { this.loading = false }) },
    resetQuery() { this.queryForm = { toolType: '', status: '' }; this.pageNo = 1; this.fetchList() },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    openCreate() { this.dialogMode = 'create'; this.form = defaultForm(); this.dialogVisible = true },
    openEdit(row) { this.dialogMode = 'edit'; this.form = Object.assign(defaultForm(), row, { id: this.rowId(row), toolType: this.toolValue(row), host: row.host || row.ip || row.host_ip || '', jenkinsLabel: row.jenkinsLabel || row.jenkins_label || '' }); this.dialogVisible = true },
    toolValue(row) { const tools = row.supported_tools_json || row.supportedToolsJson; return row.toolType || row.tool_type || (Array.isArray(tools) ? tools[0] : '') || '' },
    toolText(row) { const tools = row.supported_tools_json || row.supportedToolsJson; return row.toolType || row.tool_type || (Array.isArray(tools) ? tools.join(', ') : '') || '-' },
    rowId(row) { return row.id || row.machineId || row.machine_id },
    buildPayload() { return { name: this.form.name, host: this.form.host, jenkinsLabel: this.form.jenkinsLabel, supportedToolsJson: [this.form.toolType], maxConcurrentTasks: this.form.capacity, status: this.form.status, remark: this.form.description } },
    resetForm() { this.form = defaultForm(); this.submitting = false; if (this.$refs.form) this.$refs.form.resetFields() },
    deleteRow(row) { const id = this.rowId(row); if (!id) return; this.$confirm('确认删除该测试机？', '提示').then(() => deletePerformanceMachine(id).then(() => { this.$message.success('删除成功'); this.fetchList() })).catch(() => {}) },
    submitForm() { this.$refs.form.validate(valid => { if (!valid) return; this.submitting = true; const payload = this.buildPayload(); const req = this.dialogMode === 'create' ? createPerformanceMachine(payload) : updatePerformanceMachine(this.form.id, payload); req.then(() => { this.$message.success('保存成功'); this.dialogVisible = false; this.fetchList() }).finally(() => { this.submitting = false }) }) }
  }
}
</script>

<style scoped>.pager-wrap { margin-top: 16px; text-align: right; }.danger-text { color: #F56C6C; }</style>
