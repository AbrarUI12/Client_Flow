import { expect, test } from '@playwright/test'

test('demo user can log in, refresh the tab session, and log out', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible()
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText('Session secured')).toBeVisible()
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem('clientflow.access_token')))
    .not.toBeNull()

  await page.reload()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText('Good to see you, ClientFlow.')).toBeVisible()

  await page.getByRole('button', { name: 'Log out' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem('clientflow.access_token')))
    .toBeNull()
})
