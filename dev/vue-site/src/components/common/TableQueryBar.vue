<script setup>
const keyword = defineModel('keyword', { type: String, default: '' })
const page = defineModel('page', { type: Number, default: 1 })
const pageSize = defineModel('pageSize', { type: Number, default: 20 })

defineProps({
  total: { type: Number, default: 0 },
  placeholder: { type: String, default: '搜索 SKU / 商品名称 / 店铺' },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
})
</script>

<template>
  <div class="table-query-bar">
    <el-input
      v-model="keyword"
      clearable
      :placeholder="placeholder"
      class="table-query-bar__search"
    />
    <el-text type="info" class="table-query-bar__total">共 {{ total }} 条</el-text>
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="pageSizes"
      layout="sizes, prev, pager, next, jumper"
      background
      small
      class="table-query-bar__pager"
    />
  </div>
</template>

<style scoped>
.table-query-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.table-query-bar__search {
  width: min(320px, 100%);
}

.table-query-bar__total {
  flex: 1;
  min-width: 72px;
}

.table-query-bar__pager {
  margin-left: auto;
}
</style>
