const configuredApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const apiUrl = configuredApiUrl.replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(`API request failed with status ${response.status}.`, response.status)
  }

  return response.json() as Promise<T>
}

