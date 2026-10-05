import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

async function login(page: Page) {
  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
}

async function completeLeadWorkflow(page: Page, viewportName: string) {
  const unique = `${viewportName}-${Date.now()}`
  const contactName = `Session Five ${unique}`
  const editedCompany = `Northstar ${unique}`

  await login(page)
  await page.goto('/leads')
  await expect(page.getByRole('heading', { name: 'Leads', exact: true, level: 2 })).toBeVisible()

  await page.getByRole('link', { name: 'Add Lead', exact: true }).first().click()
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill('Initial Company')
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(`session-five-${Date.now()}@example.com`)
  await page.getByRole('combobox', { name: 'Source', exact: true }).selectOption('REFERRAL')
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('QUALIFIED')
  await page.getByRole('spinbutton', { name: 'Estimated value', exact: true }).fill('12500.50')
  await page.getByRole('textbox', { name: 'Notes', exact: true }).fill('Created through the Session 5 browser acceptance test.')
  await page.getByRole('button', { name: 'Create lead' }).click()

  await expect(page).toHaveURL(/\/leads\/[0-9a-f-]+$/)
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()
  await expect(page.getByText('Lead created', { exact: true })).toBeVisible()
  await expect(page.getByText('12,500.50')).toBeVisible()

  await page.getByRole('link', { name: 'Edit', exact: true }).click()
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill(editedCompany)
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('CONTACTED')
  await page.getByRole('button', { name: 'Save changes' }).click()

  await expect(page).toHaveURL(/\/leads\/[0-9a-f-]+$/)
  await expect(page.getByText(editedCompany).first()).toBeVisible()
  await expect(page.getByText('Contacted', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: 'Back to leads' }).click()
  await page.getByRole('searchbox', { name: 'Search leads' }).fill(unique)
  await expect(page).toHaveURL(new RegExp(`search=${viewportName}`))
  await expect(page.getByRole('link', { name: contactName }).first()).toBeVisible()

  await page.getByRole('combobox', { name: 'Filter by status' }).selectOption('CONTACTED')
  await expect(page).toHaveURL(/status=CONTACTED/)
  await page.getByRole('link', { name: contactName }).first().click()

  await page.getByRole('button', { name: 'Archive lead' }).click()
  const dialog = page.getByRole('dialog', { name: `Archive ${contactName}?` })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Cancel' })).toBeFocused()
  await dialog.getByRole('button', { name: 'Archive lead' }).click()

  await expect(page).toHaveURL(/\/leads$/)
  await page.getByRole('searchbox', { name: 'Search leads' }).fill(unique)
  await expect(page.getByRole('heading', { name: 'No leads match these filters' })).toBeVisible()
  await expect(page.getByRole('link', { name: contactName })).toHaveCount(0)
}

test('lead workflow works on desktop', async ({ page }) => {
  await completeLeadWorkflow(page, 'desktop')
})

test.describe('mobile lead workflow', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('lead workflow works on a narrow screen', async ({ page }) => {
    await completeLeadWorkflow(page, 'mobile')
  })
})
