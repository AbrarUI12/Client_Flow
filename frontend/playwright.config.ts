import { defineConfig } from '@playwright/test'

const publicBaseUrl = process.env.PLAYWRIGHT_BASE_URL?.replace(/\/$/, '')

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  reporter: 'line',
  timeout: publicBaseUrl ? 120_000 : 30_000,
  expect: {
    timeout: publicBaseUrl ? 20_000 : 5_000,
  },
  use: {
    baseURL: publicBaseUrl || 'http://localhost:5173',
    channel: 'chrome',
    headless: true,
    trace: 'retain-on-failure',
  },
})
