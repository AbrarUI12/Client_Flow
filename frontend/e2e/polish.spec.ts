import { expect, test } from '@playwright/test'

test('navigation, page titles, 404, and enlarged mobile text remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/login')
  await expect(page).toHaveTitle('Sign in | ClientFlow')
  await page.getByRole('button', { name: 'Fill demo email and password' }).click()
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page).toHaveTitle('Dashboard | ClientFlow')

  const menuButton = page.getByRole('button', { name: 'Open menu' })
  await menuButton.focus()
  await page.keyboard.press('Enter')
  const navigationDialog = page.getByRole('dialog', { name: 'Main navigation' })
  await expect(navigationDialog).toBeVisible()
  await expect(navigationDialog.getByRole('button', { name: 'Close menu' })).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(navigationDialog).toBeHidden()
  await expect(menuButton).toBeFocused()

  await page.goto('/this-page-does-not-exist')
  await expect(page.getByRole('heading', { name: 'Page not found', level: 2 })).toBeVisible()
  await expect(page).toHaveTitle('Page not found | ClientFlow')

  await page.evaluate(() => {
    document.documentElement.style.fontSize = '200%'
  })
  await page.goto('/leads')
  await expect(page).toHaveTitle('Leads | ClientFlow')
  await expect(page.getByRole('heading', { name: 'Leads', exact: true, level: 2 })).toBeVisible()
  const hasPageOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(hasPageOverflow).toBe(false)
  await expect(page.getByRole('button', { name: 'Export CSV' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Add Lead', exact: true }).first()).toBeVisible()
})

test('primary routes fit mobile, tablet, laptop, and wide layouts', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: 'Fill demo email and password' }).focus()
  await page.keyboard.press('Enter')
  await page.getByRole('button', { name: 'Sign in', exact: true }).focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/dashboard$/)

  const routes = ['/dashboard', '/leads', '/leads/new', '/quotations', '/follow-ups']
  const viewports = [
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1280, height: 800 },
    { width: 1600, height: 1000 },
  ]

  for (const viewport of viewports) {
    await page.setViewportSize(viewport)
    for (const route of routes) {
      await page.goto(route)
      await expect(page.locator('main')).toBeVisible()
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
          ),
        )
        .toBe(true)
    }
  }
})
