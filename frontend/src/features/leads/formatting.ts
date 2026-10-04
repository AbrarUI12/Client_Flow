import type { LeadSource, LeadStatus } from './types'

export const statusLabels: Record<LeadStatus, string> = {
  NEW: 'New',
  CONTACTED: 'Contacted',
  QUALIFIED: 'Qualified',
  QUOTED: 'Quoted',
  WON: 'Won',
  LOST: 'Lost',
}

export const sourceLabels: Record<LeadSource, string> = {
  WEBSITE: 'Website',
  REFERRAL: 'Referral',
  LINKEDIN: 'LinkedIn',
  UPWORK: 'Upwork',
  FIVERR: 'Fiverr',
  EMAIL: 'Email',
  PHONE: 'Phone',
  OTHER: 'Other',
}

export function formatMoney(value: string, currencyCode = 'USD'): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

export function formatDate(value: string, timeZone?: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeZone,
  }).format(new Date(value))
}
