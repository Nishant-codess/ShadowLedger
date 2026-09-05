import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Defensibility Benchmark', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/benchmark');
  });

  test('should render benchmark page and defensibility title', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/Defensibility & Benchmark Evaluation/i);
  });

  test('should show precision and zero unsafe auto-resolutions KPI', async ({ page }) => {
    await expect(page.getByText(/Deterministic Baseline Precision/i).first()).toBeVisible();
    await expect(page.getByText(/Unsafe Auto-Resolutions/i).first()).toBeVisible();
  });

  test('should render scenario breakdown rows', async ({ page }) => {
    // SCN_01 exact match
    await expect(page.getByText(/1-to-1 Exact Commerce Match/i)).toBeVisible();
    // SCN_04 Kirana
    await expect(page.getByText(/Kirana Non-Monetary Settlement/i)).toBeVisible();
    // SCN_12 Adversarial
    await expect(page.getByText(/Adversarial Deceptive Near-Match/i)).toBeVisible();
  });
});
