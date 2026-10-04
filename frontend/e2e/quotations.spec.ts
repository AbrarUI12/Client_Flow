import { expect, test } from '@playwright/test'

test('lead quotation can move from draft through accepted with accurate totals', async ({ page }) => {
  const unique = Date.now()
  const contactName = `Quotation Client ${unique}`

  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)

  await page.goto('/leads/new')
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill('Quotation Test Studio')
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('QUALIFIED')
  await page.getByRole('spinbutton', { name: 'Estimated value', exact: true }).fill('5000')
  await page.getByRole('button', { name: 'Create lead' }).click()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()

  await page.getByRole('link', { name: 'Create quotation', exact: true }).first().click()
  await expect(page.getByText('Selected client')).toBeVisible()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()

  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Discovery and strategy')
  await page.getByRole('spinbutton', { name: 'Quantity', exact: true }).fill('2')
  await page.getByRole('spinbutton', { name: 'Unit price', exact: true }).fill('100')

  await page.getByRole('button', { name: 'Add item' }).click()
  await page.getByRole('textbox', { name: 'Description', exact: true }).nth(1).fill('Interface design')
  await page.getByRole('spinbutton', { name: 'Quantity', exact: true }).nth(1).fill('1.5')
  await page.getByRole('spinbutton', { name: 'Unit price', exact: true }).nth(1).fill('50')

  await page.getByRole('button', { name: 'Add item' }).click()
  await page.getByRole('textbox', { name: 'Description', exact: true }).nth(2).fill('Implementation')
  await page.getByRole('spinbutton', { name: 'Quantity', exact: true }).nth(2).fill('3')
  await page.getByRole('spinbutton', { name: 'Unit price', exact: true }).nth(2).fill('25')
  await page.getByRole('spinbutton', { name: 'Discount (%)', exact: true }).fill('10')
  await page.getByRole('spinbutton', { name: 'Tax (%)', exact: true }).fill('5')
  await page.getByRole('textbox', { name: 'Notes', exact: true }).fill('Three-item browser proposal.')

  const preview = page.getByRole('complementary')
  await expect(preview.getByText(/330\.75/)).toBeVisible()
  await page.getByRole('button', { name: 'Save draft' }).click()

  await expect(page).toHaveURL(/\/quotations\/[0-9a-f-]+$/)
  const quoteNumber = await page.getByRole('heading', { name: /^Q-\d{4}-\d{6}$/ }).textContent()
  expect(quoteNumber).toMatch(/^Q-\d{4}-\d{6}$/)
  await expect(page.getByText('Draft', { exact: true })).toBeVisible()
  await expect(page.getByText(/330\.75/).last()).toBeVisible()

  await page.getByRole('link', { name: 'Edit', exact: true }).click()
  await page.getByRole('spinbutton', { name: 'Unit price', exact: true }).nth(2).fill('30')
  await expect(page.getByRole('complementary').getByText(/344\.93/)).toBeVisible()
  await page.getByRole('button', { name: 'Save and mark sent' }).click()
  await expect(page.getByText(/344\.93/).last()).toBeVisible()
  await expect(page.getByText('Sent', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Edit', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Accept' }).click()
  await expect(page.getByText('Accepted', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: contactName }).click()
  await expect(page.getByText('Won', { exact: true })).toBeVisible()
  await expect(page.getByText('Accepted', { exact: true })).toBeVisible()

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/quotations')
  await page.getByRole('searchbox', { name: 'Search quotations' }).fill(contactName)
  await expect(page.getByRole('link', { name: quoteNumber || '' })).toBeVisible()
})
