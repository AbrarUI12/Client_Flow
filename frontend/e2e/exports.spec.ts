import { readFile } from 'node:fs/promises'

import { expect, test } from '@playwright/test'

test('lead CSV and owned quotation PDF download from the working UI', async ({ page }) => {
  const unique = Date.now()
  const contactName = `Export Browser ${unique}`

  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)

  await page.goto('/leads/new')
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('textbox', { name: 'Company', exact: true }).fill('Northstar, "CSV" Studio')
  await page.getByRole('textbox', { name: 'Phone', exact: true }).fill('+8801700000000')
  await page.getByRole('combobox', { name: 'Source', exact: true }).selectOption('LINKEDIN')
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('QUALIFIED')
  await page.getByRole('spinbutton', { name: 'Estimated value', exact: true }).fill('4321.50')
  await page.getByRole('textbox', { name: 'Notes', exact: true }).fill('CSV line one,\nCSV line two.')
  await page.getByRole('button', { name: 'Create lead' }).click()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()
  const leadUrl = page.url()

  await page.goto('/leads')
  const csvDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export CSV' }).click()
  const csvDownload = await csvDownloadPromise
  await expect(page.getByText('Lead export downloaded', { exact: true })).toBeVisible()
  expect(csvDownload.suggestedFilename()).toMatch(/^clientflow-leads-\d{4}-\d{2}-\d{2}\.csv$/)
  const csvPath = await csvDownload.path()
  expect(csvPath).not.toBeNull()
  const csv = await readFile(csvPath!, 'utf8')
  expect(csv).toContain(contactName)
  expect(csv).toContain('"Northstar, ""CSV"" Studio"')
  expect(csv).toContain("'+8801700000000")
  expect(csv).toContain('4321.50')

  await page.goto(leadUrl)
  await page.getByRole('link', { name: 'Create quotation', exact: true }).first().click()
  await page.getByRole('textbox', { name: 'Description', exact: true }).fill('Export-ready service')
  await page.getByRole('spinbutton', { name: 'Quantity', exact: true }).fill('2')
  await page.getByRole('spinbutton', { name: 'Unit price', exact: true }).fill('125.25')
  await page.getByRole('textbox', { name: 'Notes', exact: true }).fill('Downloaded through the Session 10 UI.')
  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page).toHaveURL(/\/quotations\/[0-9a-f-]+$/)

  const quoteNumber = await page.getByRole('heading', { name: /^Q-\d{4}-\d{6}$/ }).textContent()
  const pdfDownloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download PDF' }).click()
  const pdfDownload = await pdfDownloadPromise
  await expect(page.getByText('Quotation PDF downloaded', { exact: true })).toBeVisible()
  expect(pdfDownload.suggestedFilename()).toBe(`quotation-${quoteNumber}.pdf`)
  const pdfPath = await pdfDownload.path()
  expect(pdfPath).not.toBeNull()
  const pdf = await readFile(pdfPath!)
  expect(pdf.subarray(0, 5).toString()).toBe('%PDF-')

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/leads')
  await expect(page.getByRole('button', { name: 'Export CSV' })).toBeVisible()
})
