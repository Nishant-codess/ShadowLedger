import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Command Center Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/');
  });

  test('should render page title and header branding', async ({ page }) => {
    await expect(page).toHaveTitle(/ShadowLedger/);
    await expect(page.locator('header')).toContainText('ShadowLedger');
    await expect(page.locator('header')).toContainText('Track 04');
  });

  test('should toggle between Explain Mode and Investigate Mode', async ({ page }) => {
    const explainBtn = page.getByRole('button', { name: /EXPLAIN/i });
    const investigateBtn = page.getByRole('button', { name: /INVESTIGATE/i });

    await expect(explainBtn).toBeVisible();
    await expect(investigateBtn).toBeVisible();

    // Switch to Investigate mode
    await investigateBtn.click();
    await expect(investigateBtn).toHaveClass(/bg-\[#1c1917\]/);

    // Switch back to Explain mode
    await explainBtn.click();
    await expect(explainBtn).toHaveClass(/bg-white/);
  });

  test('should display summary KPI metrics', async ({ page }) => {
    await expect(page.getByText(/Total Ingested Gross Volume/i).first()).toBeVisible();
    await expect(page.getByText(/Explained Value/i).first()).toBeVisible();
    await expect(page.getByText(/Unexplained Value at Risk/i).first()).toBeVisible();
    await expect(page.getByText(/Auto-Resolved/i).first()).toBeVisible();
  });

  test('should render the three hero demo showcase cards', async ({ page }) => {
    // Hero A: Kirana Store
    await expect(page.getByText(/THE MISSING ₹2/i).first()).toBeVisible();
    // Hero B: Mobility Ride
    await expect(page.getByText(/THE FARE THAT DOESN'T ADD UP/i).first()).toBeVisible();
    // Hero C: Fleet Patterns
    await expect(page.getByText(/THE PATTERN HIDING IN EXCEPTIONS/i).first()).toBeVisible();
  });

  test('should navigate via Hero Demo CTA to case investigation', async ({ page }) => {
    const liveCaseBtn = page.getByRole('button', { name: /Explore a live case/i });
    await expect(liveCaseBtn).toBeVisible();
    await liveCaseBtn.click();

    await expect(page).toHaveURL(/\/cases\//);
    await expect(page.getByText(/THE MISSING ₹2/i).first()).toBeVisible();
  });

  test('should trigger synthetic batch processing', async ({ page }) => {
    const processBatchBtn = page.getByRole('button', { name: /Process Batch/i });
    await expect(processBatchBtn).toBeVisible();
    await processBatchBtn.click();

    // Verification stats appear
    await expect(page.getByText(/Throughput/i).first()).toBeVisible();
    await expect(page.getByText(/Total Ingested Gross Volume/i).first()).toBeVisible();
  });
});
