import { readFile } from 'node:fs/promises'

import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function dateInDhaka(): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Dhaka',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${values.year}-${values.month}-${values.day}`
}

async function apiTotal(page: Page, path: string): Promise<number> {
  const token = await page.evaluate(() => sessionStorage.getItem('clientflow.access_token'))
  const response = await page.request.get(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  expect(response.ok()).toBe(true)
  return ((await response.json()) as { total: number }).total
}

test('complete MVP workflow runs once per action, even when submit buttons are double-clicked', async ({ page }) => {
  const unique = Date.now()
  const contactName = `MVP Client ${unique}`

  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByRole('heading', { name: 'Recent leads' })).toBeVisible()

  // Create the lead with in-app navigation so the cached dashboard must be refreshed afterward.
  await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Leads' }).click()
  await page.getByRole('link', { name: 'Add Lead', exact: true }).first().click()
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill('MVP Initial Studio')
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('QUALIFIED')
  await page.getByRole('spinbutton', { name: 'Estimated value', exact: true }).fill('5000')
  await page.getByRole('button', { name: 'Create lead' }).dblclick()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()
  expect(await apiTotal(page, `/leads?search=${encodeURIComponent(contactName)}`)).toBe(1)
  const leadId = page.url().split('/').pop()

  await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Dashboard' }).click()
  await expect(page.getByRole('link', { name: new RegExp(contactName) })).toBeVisible()
  await page.getByRole('link', { name: new RegExp(contactName) }).click()

  await page.getByRole('link', { name: 'Edit', exact: true }).click()
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill('MVP Edited Studio')
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByText('Lead updated', { exact: true })).toBeVisible()
  await expect(page.getByText('MVP Edited Studio').first()).toBeVisible()

  await page.getByRole('link', { name: 'Create quotation', exact: true }).first().click()
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
  await expect(page.getByRole('complementary').getByText(/330\.75/)).toBeVisible()
  await page.getByRole('button', { name: 'Save draft' }).dblclick()

  await expect(page).toHaveURL(/\/quotations\/[0-9a-f-]+$/)
  const quoteNumber = (await page.getByRole('heading', { name: /^Q-\d{4}-\d{6}$/ }).textContent()) || ''
  await expect(page.getByText(/330\.75/).last()).toBeVisible()
  expect(await apiTotal(page, `/leads/${leadId}/quotations`)).toBe(1)

  await page.getByRole('button', { name: 'Mark sent' }).click()
  const sendDialog = page.getByRole('dialog', { name: `Mark ${quoteNumber} as sent?` })
  await sendDialog.getByRole('button', { name: 'Mark sent' }).dblclick()
  await expect(page.getByText('Sent', { exact: true })).toBeVisible()

  const pdfDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download PDF' }).click()
  const pdfDownload = await pdfDownloadPromise
  expect(pdfDownload.suggestedFilename()).toBe(`quotation-${quoteNumber}.pdf`)
  const pdf = await readFile((await pdfDownload.path())!)
  expect(pdf.subarray(0, 5).toString()).toBe('%PDF-')

  await page.getByRole('link', { name: contactName }).click()
  await expect(page.getByText('Quoted', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Add', exact: true }).click()
  const followUpDialog = page.getByRole('dialog', { name: 'Add follow-up' })
  await followUpDialog.getByLabel('Due date and time').fill(`${dateInDhaka()}T16:00`)
  await followUpDialog.getByLabel('Note', { exact: true }).fill(`Confirm decision ${unique}`)
  await followUpDialog.getByRole('button', { name: 'Add follow-up' }).dblclick()
  await expect(page.getByText(`Confirm decision ${unique}`)).toBeVisible()
  expect(await apiTotal(page, `/follow-ups?lead_id=${leadId}`)).toBe(1)
  await page.getByRole('button', { name: 'Complete' }).click()
  await expect(page.getByText(/Completed/).last()).toBeVisible()

  await page.getByRole('link', { name: quoteNumber }).click()
  await page.getByRole('button', { name: 'Accept', exact: true }).click()
  const acceptDialog = page.getByRole('dialog', { name: `Accept ${quoteNumber}?` })
  await acceptDialog.getByRole('button', { name: 'Accept quotation' }).dblclick()
  await expect(page.getByText('Accepted', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: contactName }).click()
  await expect(page.getByText('Won', { exact: true }).first()).toBeVisible()

  await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Leads' }).click()
  const csvDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export CSV' }).click()
  const csv = await readFile((await (await csvDownloadPromise).path())!, 'utf8')
  const leadRow = csv.split('\r\n').find((line) => line.startsWith(contactName))
  expect(leadRow).toContain('MVP Edited Studio')
  expect(leadRow).toContain('Won')
})
