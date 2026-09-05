import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Exception Workbench', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/exceptions');
  });

  test('should render exception workbench with header and cases list', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/Exception Workbench/i);
    await expect(page.getByText('Kirana Inventory Settlement')).toBeVisible();
    await expect(page.getByText('Mobility QR Digital Trace')).toBeVisible();
  });

  test('should filter cases by status tab', async ({ page }) => {
    // Click Auto-Resolved filter
    const autoResolvedBtn = page.getByRole('button', { name: /Auto-Resolved/i });
    await autoResolvedBtn.click();
    await expect(page.getByText('Kirana Inventory Settlement')).toBeVisible();
    await expect(page.getByText('Mobility QR Digital Trace')).not.toBeVisible();

    // Click Human Review filter
    const humanReviewBtn = page.getByRole('button', { name: /Human Review/i });
    await humanReviewBtn.click();
    await expect(page.getByText('Mobility QR Digital Trace')).toBeVisible();
    await expect(page.getByText('Kirana Inventory Settlement')).not.toBeVisible();

    // Click All Cases filter
    const allBtn = page.getByRole('button', { name: /All Cases/i });
    await allBtn.click();
    await expect(page.getByText('Kirana Inventory Settlement')).toBeVisible();
    await expect(page.getByText('Mobility QR Digital Trace')).toBeVisible();
  });

  test('should search cases by query', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/Search case, scenario, or ID/i);
    await searchInput.fill('kirana');
    await expect(page.getByText('Kirana Inventory Settlement')).toBeVisible();
    await expect(page.getByText('Mobility QR Digital Trace')).not.toBeVisible();

    await searchInput.fill('mobility');
    await expect(page.getByText('Mobility QR Digital Trace')).toBeVisible();
    await expect(page.getByText('Kirana Inventory Settlement')).not.toBeVisible();
  });

  test('should navigate to case detail when clicking inspect link', async ({ page }) => {
    const inspectLink = page.getByRole('link', { name: /Inspect →/i }).first();
    await inspectLink.click();
    await expect(page).toHaveURL(/\/cases\/case_kirana_001/);
  });
});
