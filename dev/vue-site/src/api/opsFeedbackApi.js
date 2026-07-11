import { service } from './request'

function mapFeedback(row) {
  if (!row) return row
  return {
    id: row.id,
    taskId: row.taskId || row.task_id,
    employeeId: row.employeeId || row.employee_id || '',
    employeeName: row.employeeName || row.employee_name || '',
    employeeRole: row.employeeRole || row.employee_role || '',
    platform: row.platform || '',
    platformKey: row.platformKey || row.platform_key || '',
    taskTitle: row.taskTitle || row.task_title || '',
    category: row.category || '',
    outcome: row.outcome || 'in_progress',
    outcomeLabel: row.outcomeLabel || row.outcome_label || '',
    feedback: row.feedback || '',
    storeName: row.storeName || row.store_name || '—',
    date: row.date || row.feedback_date || '',
    submittedAt: row.submittedAt || row.submitted_at || '',
  }
}

export async function fetchBackendTodayOpsFeedback() {
  const res = await service.get('/api/ops-feedback/today', { skipGlobalErrorToast: true })
  return (res?.data || []).map(mapFeedback)
}

export async function fetchBackendTaskFeedbacks(taskId) {
  const res = await service.get('/api/ops-feedback', {
    params: { task_id: taskId },
    skipGlobalErrorToast: true,
  })
  return (res?.data || []).map(mapFeedback)
}

export async function submitBackendTaskFeedback(payload) {
  const res = await service.post('/api/ops-feedback', payload)
  return mapFeedback(res?.data)
}
