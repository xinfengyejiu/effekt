<template>
  <div class="page-wrap">
    <page-section title="巡检报告">
      <el-form inline size="small" style="margin-bottom: 16px">
        <el-form-item label="时间范围">
          <el-radio-group v-model="days" @change="fetchTrend" size="small">
            <el-radio-button :label="7">近7天</el-radio-button>
            <el-radio-button :label="14">近14天</el-radio-button>
            <el-radio-button :label="30">近30天</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <!-- 趋势表格 -->
      <el-table :data="trendData" stripe border size="small" v-loading="loading">
        <el-table-column label="日期" prop="date" width="120"></el-table-column>
        <el-table-column label="执行次数" prop="total" width="100"></el-table-column>
        <el-table-column label="通过" width="100">
          <template slot-scope="scope">
            <span style="color: #67C23A">{{ scope.row.passed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="失败" width="100">
          <template slot-scope="scope">
            <span :style="{color: scope.row.failed > 0 ? '#F56C6C' : ''}">{{ scope.row.failed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="通过率" width="120">
          <template slot-scope="scope">
            <el-progress :percentage="calcRate(scope.row)" :color="calcColor(scope.row)" :stroke-width="14" :text-inside="true"></el-progress>
          </template>
        </el-table-column>
        <el-table-column label="状态">
          <template slot-scope="scope">
            <el-tag size="mini" v-if="scope.row.total === 0" type="info">无执行</el-tag>
            <el-tag size="mini" v-else-if="scope.row.failed === 0" type="success">全部通过</el-tag>
            <el-tag size="mini" v-else type="danger">有失败</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getInspectionTrend } from '@/api/inspectionApi'

export default {
  name: 'InspectionReport',
  components: { PageSection },
  data() {
    return { loading: false, days: 7, trendData: [] }
  },
  created() { this.fetchTrend() },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    fetchTrend() {
      this.loading = true
      getInspectionTrend({ days: this.days }).then(res => {
        this.trendData = this.dataOf(res) || []
      }).finally(() => { this.loading = false })
    },
    calcRate(row) {
      if (!row.total) return 0
      return Math.round(row.passed * 100 / row.total)
    },
    calcColor(row) {
      var rate = this.calcRate(row)
      if (rate >= 80) return '#67C23A'
      if (rate >= 50) return '#E6A23C'
      return '#F56C6C'
    }
  }
}
</script>
