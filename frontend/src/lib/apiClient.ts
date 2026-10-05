import { clearAccessToken, getAccessToken, UNAUTHORIZED_EVENT } from '../features/auth/session'

const configuredApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const apiUrl = configuredApiUrl.replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code = 'REQUEST_FAILED') {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

type ApiRequestOptions = RequestInit & {
  authenticated?: boolean
}

type ErrorBody = {
  detail?: string | { code?: string; message?: string }
}

export type DownloadedFile = {
  blob: Blob
  filename: string
}

async function throwResponseError(response: Response, authenticated: boolean): Promise<never> {
  let message = `API request failed with status ${response.status}.`
  let code = 'REQUEST_FAILED'

  try {
    const body = (await response.json()) as ErrorBody
    if (typeof body.detail === 'string') {
      message = body.detail
    } else if (body.detail) {
      message = body.detail.message || message
      code = body.detail.code || code
    }
  } catch {
    // Keep the safe fallback when an upstream response is not JSON.
  }

  if (response.status === 401 && authenticated) {
    clearAccessToken()
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  }

  throw new ApiError(message, response.status, code)
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { authenticated = true, ...init } = options
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const token = getAccessToken()
  if (authenticated && token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    return throwResponseError(response, authenticated)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export async function apiDownload(path: string): Promise<DownloadedFile> {
  const headers = new Headers({ Accept: 'application/octet-stream' })
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${apiUrl}${path}`, { headers })
  if (!response.ok) return throwResponseError(response, true)

  const disposition = response.headers.get('Content-Disposition') || ''
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plainName = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  let filename = 'clientflow-download'
  try {
    filename = encodedName ? decodeURIComponent(encodedName) : (plainName || filename)
  } catch {
    filename = plainName || filename
  }

  return { blob: await response.blob(), filename }
}

export function saveDownloadedFile(file: DownloadedFile): void {
  const objectUrl = URL.createObjectURL(file.blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = file.filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(objectUrl)
}

