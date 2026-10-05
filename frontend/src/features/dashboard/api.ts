import { apiRequest } from '../../lib/apiClient'
import type { DashboardSummary } from './types'

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>('/dashboard/summary')
}
