export type AuthUser = {
  id: string
  email: string
  full_name: string
  business_name: string
  business_address: string
  business_phone: string
  currency_code: string
  timezone: string
}

export type TokenResponse = {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export type LoginCredentials = {
  email: string
  password: string
}
