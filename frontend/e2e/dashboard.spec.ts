import { expect, test } from '@playwright/test'

test('dashboard reflects newly created lead through one summary read model', async ({ page }) => {
  let summaryRequests = 0
  page.on('request', (request) => {
    if (request.url().includes('/api/v1/dashboard/summary')) summaryRequests += 1
  })

  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)

  await expect(page.getByRole('heading', { name: /Good to see you/ })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Lead pipeline' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Recent leads' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Overdue follow-ups' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Upcoming follow-ups' })).toBeVisible()
  await expect.poll(() => summaryRequests).toBe(1)

  const totalCard = page.getByRole('link').filter({ hasText: 'Total leads' })
  const initialTotal = Number(await totalCard.locator('p').nth(1).textContent())
  const contactName = `Dashboard Lead ${Date.now()}`

  await page.goto('/leads/new')
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('button', { name: 'Create lead' }).click()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()

  await page.goto('/dashboard')
  await expect(page.getByText(contactName)).toBeVisible()
  await expect.poll(async () => Number(await totalCard.locator('p').nth(1).textContent())).toBeGreaterThanOrEqual(initialTotal + 1)

  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.getByRole('heading', { name: 'Lead pipeline' })).toBeVisible()
  await expect(page.getByText('Total leads')).toBeVisible()
})
