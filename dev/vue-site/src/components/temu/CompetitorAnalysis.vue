<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Link, Refresh, Search, Setting } from '@element-plus/icons-vue'
import {
  analyzeCompetitors,
  deleteCompetitor,
  fetchCompetitorReports,
  fetchCompetitors,
  saveCompetitor,
} from '@/api/temuCompetitors'

defineProps({
  useBackendData: { type: Boolean, default: false },
})

const loading = ref(false)
const analyzing = ref(false)
const competitors = ref([])
const reports = ref([])
const settingsOpen = ref(true)

const form = reactive({
  id: '',
  label: '',
  url: '',
})

function resetForm() {
  form.id = ''
  form.label = ''
  form.url = ''
}

async function loadCompetitors() {
  loading.value = true
  try {
    const res = await fetchCompetitors()
    competitors.value = res.data || []
  } catch {
    competitors.value = []
  } finally {
    loading.value = false
  }
}

function editCompetitor(row) {
  form.id = row.id
  form.label = row.label
  form.url = row.url
  settingsOpen.value = true
}

async function submitCompetitor() {
  if (!form.label.trim()) {
    ElMessage.warning('请填写店铺备注名称')
    return
  }
  if (!form.url.trim()) {
    ElMessage.warning('请填写竞争对手店铺网址')
    return
  }

  loading.value = true
  try {
    await saveCompetitor({
      id: form.id || undefined,
      label: form.label.trim(),
      url: form.url.trim(),
    })
    ElMessage.success(form.id ? '已更新竞争对手' : '已添加竞争对手')
    resetForm()
    await loadCompetitors()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    loading.value = false
  }
}

async function removeCompetitor(row) {
  try {
    await ElMessageBox.confirm(`确定移除竞争对手「${row.label}」？历史爬取数据将一并删除。`, '确认', {
      type: 'warning',
      confirmButtonText: '移除',
      cancelButtonText: '取消',
    })
    await deleteCompetitor(row.id)
    reports.value = reports.value.filter((item) => item.id !== row.id)
    ElMessage.success('已移除')
    await loadCompetitors()
  } catch {
    // cancelled
  }
}

async function loadReports() {
  try {
    const res = await fetchCompetitorReports(competitors.value)
    if (res.competitors?.length) {
      competitors.value = res.competitors
    }
    reports.value = res.data || []
  } catch {
    reports.value = []
  }
}

async function runAnalysis() {
  analyzing.value = true
  try {
    const res = await analyzeCompetitors(competitors.value)
    competitors.value = res.competitors || []
    reports.value = res.data || []
    const totalNew = reports.value.reduce((s, r) => s + r.summary.newToday, 0)
    const totalSpikes = reports.value.reduce((s, r) => s + r.summary.salesSpikes, 0)
    if (!reports.value.length) {
      ElMessage.warning('未生成分析报告，请刷新页面后重试')
      return
    }
    ElMessage.success(`爬取完成：发现 ${totalNew} 个今日上新，${totalSpikes} 个销量异常`)
  } catch (err) {
    ElMessage.error(err.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

function severityType(severity) {
  return severity === 'high' ? 'danger' : 'warning'
}

onMounted(async () => {
  await loadCompetitors()
  await loadReports()
})
</script>

<template>
  <div class="competitor-analysis">
    <el-alert
      v-if="useBackendData"
      type="info"
      :closable="false"
      show-icon
      title="竞店爬取尚未接入本项目 Python 爬虫"
      description="当前竞店分析仍使用本地 Demo 数据；可在 backend/python 扩展竞店爬虫后，由 Java API 统一对外提供。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never" class="settings-card">
      <template #header>
        <div class="settings-head">
          <el-space>
            <el-icon><Setting /></el-icon>
            <span>竞店设置</span>
            <el-text size="small" type="info">系统每日自动爬取竞店商品，对比历史数据识别上新与销量异常</el-text>
          </el-space>
          <el-button text @click="settingsOpen = !settingsOpen">
            {{ settingsOpen ? '收起' : '展开' }}
          </el-button>
        </div>
      </template>

      <div v-show="settingsOpen">
        <el-form label-width="100px" class="settings-form" @submit.prevent="submitCompetitor">
          <el-form-item label="店铺备注">
            <el-input
              v-model="form.label"
              placeholder="如：美国站头部竞店 A"
              maxlength="40"
              show-word-limit
              clearable
            />
          </el-form-item>
          <el-form-item label="店铺网址">
            <el-input
              v-model="form.url"
              placeholder="https://www.temu.com/xxx 或粘贴完整店铺链接"
              clearable
            >
              <template #prefix>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-space>
              <el-button type="primary" :loading="loading" @click="submitCompetitor">
                {{ form.id ? '保存修改' : '添加竞店' }}
              </el-button>
              <el-button v-if="form.id" @click="resetForm">取消编辑</el-button>
            </el-space>
          </el-form-item>
        </el-form>

        <el-table
          v-loading="loading"
          :data="competitors"
          size="small"
          empty-text="暂未添加竞争对手，请在上方输入网址"
          class="competitor-table"
        >
          <el-table-column prop="label" label="备注名称" min-width="120" />
          <el-table-column label="店铺网址" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <el-link :href="row.url" target="_blank" type="primary" :underline="false">
                {{ row.url }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column label="最近爬取" width="160">
            <template #default="{ row }">
              <el-text v-if="row.lastAnalyzedAt" size="small">{{ row.lastAnalyzedAt }}</el-text>
              <el-text v-else size="small" type="info">未爬取</el-text>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="editCompetitor(row)">编辑</el-button>
              <el-button link type="danger" @click="removeCompetitor(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="settings-actions">
          <el-button
            type="primary"
            :icon="Search"
            :loading="analyzing"
            :disabled="!competitors.length"
            @click="runAnalysis"
          >
            执行今日爬取分析
          </el-button>
          <el-text size="small" type="info">
            每日爬取一次，自动对比昨日快照，抽取竞店新品与销量激增商品
          </el-text>
        </div>
      </div>
    </el-card>

    <el-empty
      v-if="!reports.length"
      description="添加竞店网址后，点击「执行今日爬取分析」查看上新与异常数据"
      :image-size="96"
    />

    <div v-else class="report-list">
      <el-card
        v-for="report in reports"
        :key="report.id"
        shadow="never"
        class="report-card"
      >
        <template #header>
          <div class="report-head">
            <div>
              <strong>{{ report.label }}</strong>
              <el-text size="small" type="info">{{ report.host }}</el-text>
            </div>
            <el-space>
              <el-tag size="small" effect="plain">
                <el-icon style="vertical-align: -2px"><Refresh /></el-icon>
                {{ report.crawlDate }} 爬取
              </el-tag>
              <el-text size="small" type="info">已存 {{ report.snapshotCount }} 天快照</el-text>
              <el-link :href="report.url" target="_blank" type="primary">访问店铺</el-link>
            </el-space>
          </div>
        </template>

        <div class="summary-row">
          <div class="summary-item">
            <span>在售商品</span>
            <strong>{{ report.summary.totalProducts }}</strong>
          </div>
          <div class="summary-item highlight">
            <span>今日上新</span>
            <strong>{{ report.summary.newToday }}</strong>
          </div>
          <div class="summary-item">
            <span>近 7 日上新</span>
            <strong>{{ report.summary.recentListings }}</strong>
          </div>
          <div class="summary-item warn">
            <span>销量异常</span>
            <strong>{{ report.summary.salesSpikes }}</strong>
          </div>
        </div>

        <div class="section">
          <div class="section-head">
            <strong>近期上新</strong>
            <el-text size="small" type="info">对比 {{ report.previousCrawlDate || '历史' }} 快照识别的新品</el-text>
          </div>
          <el-table
            v-if="report.recentListings.length"
            :data="report.recentListings"
            size="small"
            stripe
          >
            <el-table-column prop="name" label="商品名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="category" label="品类" width="100" />
            <el-table-column label="售价" width="100" align="right" prop="priceText" />
            <el-table-column label="上架时间" width="110">
              <template #default="{ row }">
                <el-tag
                  :type="row.daysSinceListed === 0 ? 'success' : 'info'"
                  size="small"
                  effect="plain"
                >
                  {{ row.listedLabel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="日销" prop="dailySales" width="80" align="center" />
            <el-table-column label="累计销量" prop="totalSales" width="100" align="center" />
            <el-table-column label="链接" width="80" align="center">
              <template #default="{ row }">
                <el-link :href="row.url" target="_blank" type="primary" size="small">查看</el-link>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="近 7 日暂无新上架商品" :image-size="64" />
        </div>

        <div class="section">
          <div class="section-head">
            <strong>销量异常</strong>
            <el-text size="small" type="info">日销较 7 日均值涨幅 ≥50% 或较昨日涨幅 ≥80%</el-text>
          </div>
          <el-table
            v-if="report.salesSpikes.length"
            :data="report.salesSpikes"
            size="small"
            stripe
          >
            <el-table-column prop="name" label="商品名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="category" label="品类" width="100" />
            <el-table-column label="异常类型" width="100">
              <template #default="{ row }">
                <el-tag :type="severityType(row.severity)" size="small" effect="dark">
                  {{ row.anomalyType }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="今日日销" prop="dailySales" width="90" align="center" />
            <el-table-column label="昨日日销" prop="prevDailySales" width="90" align="center" />
            <el-table-column label="7 日均销" prop="avg7DailySales" width="90" align="center" />
            <el-table-column label="较昨日" width="90" align="center">
              <template #default="{ row }">
                <el-text type="danger">{{ row.growthVsPrevText }}</el-text>
              </template>
            </el-table-column>
            <el-table-column label="较均值" width="90" align="center">
              <template #default="{ row }">
                <el-text type="danger">{{ row.growthVsAvgText }}</el-text>
              </template>
            </el-table-column>
            <el-table-column label="售价" width="100" align="right" prop="priceText" />
          </el-table>
          <el-empty v-else description="暂无销量异常商品" :image-size="64" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.competitor-analysis {
  display: grid;
  gap: 16px;
}

.settings-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.settings-form {
  max-width: 720px;
  margin-bottom: 8px;
}

.competitor-table {
  margin-bottom: 16px;
}

.settings-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  padding-top: 4px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.report-list {
  display: grid;
  gap: 16px;
}

.report-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.report-head strong {
  display: block;
  margin-bottom: 4px;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.summary-item {
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  background: var(--el-fill-color-light);
}

.summary-item.highlight strong {
  color: var(--el-color-success);
}

.summary-item.warn strong {
  color: var(--el-color-danger);
}

.summary-item span {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.summary-item strong {
  font-size: 22px;
}

.section {
  margin-bottom: 20px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}

@media (max-width: 768px) {
  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
