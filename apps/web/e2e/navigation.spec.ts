import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Global Navigation & Layout', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/');
  });

  test('should navigate to Exception Workbench', async ({ page }) => {
    await page.getByRole('link', { name: /Exception Workbench/i }).click();
    await expect(page).toHaveURL(/\/exceptions/);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/Exception Workbench/i);
  });

  test('should navigate to Fleet Patterns', async ({ page }) => {
    await page.getByRole('link', { name: /Fleet Patterns/i }).click();
    await expect(page).toHaveURL(/\/patterns/);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/PATTERN/i);
  });

  test('should navigate to Defensibility Benchmark', async ({ page }) => {
    await page.getByRole('link', { name: /Defensibility Benchmark/i }).click();
    await expect(page).toHaveURL(/\/benchmark/);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/Defensibility/i);
  });

  test('should navigate back to Command Center from logo link', async ({ page }) => {
    await page.goto('/exceptions');
    await page.locator('header a', { hasText: /ShadowLedger/i }).first().click();
    await expect(page).toHaveURL('/');
  });

  test('should display footer with project details', async ({ page }) => {
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    await expect(footer).toContainText(/ShadowLedger/i);
    await expect(footer).toContainText(/Track 04/i);
  });
});
