import { test, expect } from '@playwright/test'

/**
 * Run sequentially: one Next dev server + heavy /api/data loads — parallel workers
 * caused flaky hydration (e.g. lang toggle click not updating document).
 */
test.describe.serial('Platform UI/UX', () => {
  /** App routes from Sidebar NAV_ITEMS (single-segment paths). */
  const ROUTES = [
    '/dashboard',
    '/decisions',
    '/profile',
    '/products',
    '/pricing',
    '/coverage',
    '/competitors',
    '/categories',
    '/recommendations',
  ] as const

  function attachPageErrors(page: import('@playwright/test').Page): string[] {
    const errors: string[] = []
    page.on('pageerror', err => errors.push(err.message))
    return errors
  }

  test.describe('UI smoke', () => {
    test('home redirects to dashboard', async ({ page }) => {
      await page.goto('/')
      await expect(page).toHaveURL(/\/dashboard/)
    })

    for (const path of ROUTES) {
      test(`shell + page title: ${path}`, async ({ page }) => {
        const pageErrors = attachPageErrors(page)
        await page.goto(path, { waitUntil: 'domcontentloaded' })

        await expect(page.locator('aside')).toBeVisible()
        await expect(page.locator('main')).toBeVisible()
        await expect(page.locator('main').locator('header').locator('h1')).toBeVisible({ timeout: 120_000 })

        expect(pageErrors, `pageerror on ${path}: ${pageErrors.join('; ')}`).toEqual([])
      })
    }
  })

  test.describe('UX flows', () => {
    test('sidebar navigation switches route', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
      await expect(page.locator('main header h1')).toBeVisible({ timeout: 120_000 })

      const sideNav = page.locator('aside nav')
      await sideNav.getByRole('link', { name: /مركز اتخاذ القرار|Decision Hub/ }).click()
      await expect(page).toHaveURL(/\/decisions/)
      await expect(page.locator('main header h1')).toBeVisible()

      await sideNav.getByRole('link', { name: /تحليل المنتجات|Product Intelligence/ }).click()
      await expect(page).toHaveURL(/\/products/)
    })

    test('language toggle switches copy (EN ↔ AR)', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
      await expect(page.locator('main header h1')).toBeVisible({ timeout: 120_000 })

      const dashNav = page.locator('aside a[href="/dashboard"]')
      await expect(dashNav).toContainText(/نظرة عامة على الأداء|Business Overview/)

      const topbar = page.getByTestId('app-topbar')
      await topbar.getByRole('button', { name: /^EN$/ }).click()
      await expect(page.locator('html')).toHaveAttribute('lang', 'en', { timeout: 30_000 })
      await expect(dashNav).toContainText('Business Overview')

      await topbar.getByRole('button', { name: /^عر$/ }).click()
      await expect(page.locator('html')).toHaveAttribute('lang', 'ar', { timeout: 30_000 })
      await expect(dashNav).toContainText('نظرة عامة على الأداء')
    })

    test('data source toggle is reachable (Supermarket / Delivery)', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
      await expect(page.locator('main header h1')).toBeVisible({ timeout: 120_000 })

      const topbar = page.getByTestId('app-topbar')
      await topbar.getByRole('button', { name: /متاجر التجزئة|Retail Market/ }).click()
      await topbar.getByRole('button', { name: /تطبيقات التوصيل|Delivery Apps/ }).click()
      await expect(page.locator('main')).toBeVisible()
    })
  })

  test.describe('Layout / a11y basics', () => {
    test('main landmark and one primary heading per view', async ({ page }) => {
      await page.goto('/decisions', { waitUntil: 'domcontentloaded' })
      await expect(page.locator('main header h1')).toBeVisible({ timeout: 120_000 })
      await expect(page.locator('main').locator('header h1')).toHaveCount(1)
    })
  })
})
