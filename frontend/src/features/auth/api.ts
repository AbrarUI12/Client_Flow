import { apiRequest } from '../../lib/apiClient'
import type { AuthUser, LoginCredentials, TokenResponse } from './types'

export function loginRequest(credentials: LoginCredentials): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    authenticated: false,
    body: JSON.stringify(credentials),
  })
}

export function getCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>('/auth/me')
}

export function logoutRequest(): Promise<void> {
  return apiRequest<void>('/auth/logout', { method: 'POST' })
}
