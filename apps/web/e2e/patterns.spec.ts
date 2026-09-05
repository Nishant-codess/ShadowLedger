import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Fleet Patterns Investigation', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/patterns');
  });

  test('should display fleet patterns header and hero badge', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/PATTERN/i);
    await expect(page.getByText(/Fleet Investigation/i).first()).toBeVisible();
  });

  test('should display pattern cards with common cause and evidence strength', async ({ page }) => {
    // Pattern 1: Inventory Substitution
    await expect(page.getByText(/INVENTORY_SUBSTITUTION/i)).toBeVisible();
    await expect(page.getByText(/Dairy Milk/i).first()).toBeVisible();

    // Pattern 2: Off Ledger Cash
    await expect(page.getByText(/OFF_LEDGER_CASH_DEVIATION/i)).toBeVisible();
    await expect(page.getByText(/Airport toll bridge detour/i)).toBeVisible();
  });

  test('should display aggregated value at risk and total exceptions', async ({ page }) => {
    await expect(page.getByText(/Total Value at Risk/i)).toBeVisible();
    await expect(page.getByText(/Linked Cases/i).first()).toBeVisible();
  });
});
