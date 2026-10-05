import { expect, test } from '@playwright/test'

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

test('follow-up can be scheduled, edited, grouped, and completed', async ({ page }) => {
  const unique = Date.now()
  const contactName = `Follow-up Client ${unique}`
  const initialNote = `Call about scope ${unique}`
  const editedNote = `Confirm proposal decision ${unique}`

  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)

  await page.goto('/leads/new')
  await page.getByRole('textbox', { name: 'Contact name', exact: true }).fill(contactName)
  await page.getByRole('button', { name: 'Create lead' }).click()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()

  await page.getByRole('button', { name: 'Add', exact: true }).click()
  const createDialog = page.getByRole('dialog', { name: 'Add follow-up' })
  await expect(createDialog).toBeVisible()
  await createDialog.getByLabel('Due date and time').fill(`${dateInDhaka()}T10:00`)
  await createDialog.getByLabel('Note', { exact: true }).fill(initialNote)
  await createDialog.getByRole('button', { name: 'Add follow-up' }).click()

  await expect(page.getByText('Follow-up added', { exact: true })).toBeVisible()
  await expect(page.getByText(initialNote)).toBeVisible()
  await page.goto('/follow-ups')
  const todaySection = page.getByRole('region', { name: 'Today' })
  await expect(todaySection.getByText(initialNote)).toBeVisible()

  await todaySection.getByRole('button', { name: 'Edit' }).click()
  const editDialog = page.getByRole('dialog', { name: 'Edit follow-up' })
  await editDialog.getByLabel('Note', { exact: true }).fill(editedNote)
  await editDialog.getByRole('button', { name: 'Save changes' }).click()
  await expect(todaySection.getByText(editedNote)).toBeVisible()

  await page.setViewportSize({ width: 390, height: 844 })
  await todaySection.getByRole('button', { name: 'Complete' }).click()
  const completedSection = page.getByRole('region', { name: 'Completed' })
  await expect(completedSection.getByText(editedNote)).toBeVisible()
  await expect(completedSection.getByText(/Completed/).last()).toBeVisible()
  await expect(todaySection.getByText(editedNote)).toHaveCount(0)

  await completedSection.getByRole('link', { name: contactName }).click()
  await expect(page.getByRole('heading', { name: contactName })).toBeVisible()
  await expect(page.getByText(editedNote)).toBeVisible()
  await expect(page.getByText(/Completed/).last()).toBeVisible()
})
