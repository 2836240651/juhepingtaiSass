import { hasBackendSession } from './backendSession'
import {
  fetchBackendTaskFeedbacks,
  fetchBackendTodayOpsFeedback,
  submitBackendTaskFeedback,
} from './opsFeedbackApi'
import { fetchOpsFeedback, submitOpsFeedback, fetchFeedbacksByTaskId } from './opsFeedbackLocal'

export async function loadTodayOpsFeedback(options = {}, auth = null) {
  if (hasBackendSession(auth)) {
    const data = await fetchBackendTodayOpsFeedback()
    return { success: true, data }
  }
  return {
    success: true,
    data: fetchOpsFeedback(options),
  }
}

export async function loadTaskFeedbacks(taskId, auth = null) {
  if (hasBackendSession(auth)) {
    const data = await fetchBackendTaskFeedbacks(taskId)
    return { success: true, data }
  }
  return {
    success: true,
    data: fetchFeedbacksByTaskId(taskId),
  }
}

export async function submitTaskFeedback(payload, auth = null) {
  if (hasBackendSession(auth)) {
    const data = await submitBackendTaskFeedback(payload)
    return { success: true, data }
  }
  return submitOpsFeedback(payload)
}
