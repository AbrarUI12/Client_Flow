import { useQuery } from '@tanstack/react-query'

import { apiRequest } from '../../lib/apiClient'

export type HealthResponse = {
  status: 'ok'
  service: string
  version: string
}

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiRequest<HealthResponse>('/health'),
  })
}

