import { getAppErrorMessage } from '@/utils/appErrorCode'

export function resolveAmazonProductEmptyHint({ errorCode = '', errorMessage = '', syncedAt = '' } = {}) {
  const code = String(errorCode || '').trim()
  const message = String(errorMessage || '').trim()

  if (code === 'AMAZON_LOGIN_REQUIRED' || /未登录|sign in/i.test(message)) {
    return {
      title: 'Amazon 卖家后台未登录',
      description:
        '请在紫鸟浏览器中打开 YOTO 店铺并登录 Seller Central，确认首页可见「全局快照」后再点击 Business Report 刷新。',
      type: 'error',
    }
  }

  if (code === 'AMAZON_NO_PRODUCT_ROWS' || code === 'AMAZON_SYNC_PARTIAL') {
    return {
      title: '同步完成，但 TOP20 仍无有效产品',
      description:
        '运营指标已更新，但 Business Report / 库存页未解析到带 ASIN 的产品行。请确认报表页已加载，或查看 backend/data/amazon-captures 调试截图。',
      type: 'warning',
    }
  }

  if (code === 'AMAZON_SYNC_IN_PROGRESS') {
    return {
      title: '同步任务进行中',
      description: message || '请等待当前同步完成后再刷新。',
      type: 'info',
    }
  }

  if (syncedAt) {
    return {
      title: '暂无有效产品数据',
      description:
        '库内尚无带 ASIN 的产品快照。请点击「Business Report 刷新」重新同步；需紫鸟与同步助手在线。',
      type: 'warning',
    }
  }

  return {
    title: '暂无有效产品数据',
    description: '请先绑定 Amazon 紫鸟店铺并完成一次 Business Report 同步。',
    type: 'warning',
  }
}

export function buildAmazonSyncToast(job = {}) {
  if (job.status === 'partial') {
    return {
      type: 'warning',
      message: getAppErrorMessage(job.error_code, job.error_message || '同步完成，但产品数据为空'),
    }
  }
  if (job.status === 'failed') {
    return {
      type: 'error',
      message: getAppErrorMessage(job.error_code, job.error_message || 'Amazon 数据同步失败'),
    }
  }
  return null
}
