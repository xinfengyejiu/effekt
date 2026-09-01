<template>
  <page-section title="已登记设备">
    <template slot="extra">
      <el-button size="small" :loading="scanning" @click="scan">扫描 ADB 设备</el-button>
      <el-button size="small" :loading="loading" @click="fetchList">刷新</el-button>
    </template>
    <el-table v-loading="loading" :data="rows" border style="width:100%;">
      <el-table-column prop="serial_no" label="序列号" min-width="190" show-overflow-tooltip />
      <el-table-column label="设备" min-width="150"><template slot-scope="scope">{{ scope.row.display_name || scope.row.model || '-' }}</template></el-table-column>
      <el-table-column label="系统" width="120"><template slot-scope="scope">Android {{ scope.row.android_version || '-' }}</template></el-table-column>
      <el-table-column label="ADB" width="100"><template slot-scope="scope"><el-tag size="mini" :type="adbTag(scope.row.adb_status)">{{ scope.row.adb_status || '-' }}</el-tag></template></el-table-column>
      <el-table-column label="使用状态" width="110"><template slot-scope="scope"><el-tag size="mini" :type="usageTag(scope.row.usage_status)">{{ usageLabel(scope.row.usage_status) }}</el-tag></template></el-table-column>
      <el-table-column prop="device_group" label="分组" min-width="110" show-overflow-tooltip />
      <el-table-column prop="last_seen_time" label="最后发现" min-width="165" show-overflow-tooltip />
      <el-table-column label="操作" width="100" fixed="right"><template slot-scope="scope"><el-button type="text" @click="edit(scope.row)">编辑</el-button></template></el-table-column>
    </el-table>
    <el-dialog title="编辑设备" :visible.sync="dialogVisible" width="480px" :close-on-click-modal="false">
      <el-form ref="form" :model="form" label-width="90px" size="small">
        <el-form-item label="序列号"><el-input v-model="form.serial_no" disabled /></el-form-item>
        <el-form-item label="显示名称"><el-input v-model.trim="form.display_name" /></el-form-item>
        <el-form-item label="设备分组"><el-input v-model.trim="form.device_group" /></el-form-item>
        <el-form-item label="使用状态"><el-select v-model="form.usage_status" style="width:100%;"><el-option label="空闲" value="idle" /><el-option label="禁用" value="disabled" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model.trim="form.remark" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <div slot="footer"><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></div>
    </el-dialog>
  </page-section>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getMobileDeviceList, scanMobileDevices, updateMobileDevice } from '@/api/mobileAutomationApi'

export default {
  name: 'MobileDeviceList',
  components: { PageSection },
  data() { return { loading: false, scanning: false, saving: false, rows: [], dialogVisible: false, form: {} } },
  created() { this.fetchList() },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    fetchList() { this.loading = true; return getMobileDeviceList().then(res => { this.rows = this.dataOf(res).list || [] }).finally(() => { this.loading = false }) },
    scan() { this.scanning = true; scanMobileDevices().then(res => { const list = this.dataOf(res).list || []; this.$message.success('扫描完成，发现 ' + list.length + ' 台设备'); return this.fetchList() }).finally(() => { this.scanning = false }) },
    edit(row) { this.form = Object.assign({ display_name: '', device_group: '', remark: '', usage_status: 'idle' }, row); this.dialogVisible = true },
    save() { this.saving = true; updateMobileDevice(this.form).then(() => { this.$message.success('设备已更新'); this.dialogVisible = false; return this.fetchList() }).finally(() => { this.saving = false }) },
    adbTag(v) { return { online: 'success', offline: 'info', unauthorized: 'danger' }[v] || 'warning' },
    usageTag(v) { return { idle: 'success', running: 'warning', disabled: 'info' }[v] || 'info' },
    usageLabel(v) { return { idle: '空闲', running: '占用中', disabled: '已禁用' }[v] || v || '-' }
  }
}
</script>
