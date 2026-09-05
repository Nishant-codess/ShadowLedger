import { test, expect } from '@playwright/test';
import { setupApiMocks } from './mocks';

test.describe('Case Detail Investigation Workspace', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto('/cases/case_kirana_001');
  });

  test('should render case investigation header and status badge', async ({ page }) => {
    await expect(page.getByText(/auto resolve/i).first()).toBeVisible();
    await expect(page.getByText(/94%/i).first()).toBeVisible();
  });

  test('should display reconstructed value-flow facts in Explain Mode', async ({ page }) => {
    await expect(page.getByText(/WHAT WE KNOW/i).first()).toBeVisible();
    await expect(page.getByText(/Observed Facts/i).first()).toBeVisible();
    await expect(page.getByText(/Grocery Purchase/i).first()).toBeVisible();
  });

  test('should generate and render Local AI Explanation card', async ({ page }) => {
    const generateBtn = page.getByRole('button', { name: /Generate AI Investigation Narrative/i });
    await expect(generateBtn).toBeVisible();
    await generateBtn.click();

    await expect(page.getByText(/Reconstructed Barter Change Settlement/i)).toBeVisible();
    await expect(page.getByText(/Cadbury Dairy Milk/i).first()).toBeVisible();
  });

  test('should toggle to Investigate View and show taxonomy and ledger controls', async ({ page }) => {
    // Switch to Investigate mode via button on page
    const detailsBtn = page.getByRole('button', { name: /Show Investigation Details/i });
    await detailsBtn.click();

    // Verify Investigate View sections
    await expect(page.getByText(/Applied Four-Level Event Taxonomy/i)).toBeVisible();
    await expect(page.getByText(/Official Ledger/i).first()).toBeVisible();
    await expect(page.getByText(/Shadow Ledger/i).first()).toBeVisible();
    await expect(page.getByText(/Human-in-the-Loop Operator Controls/i)).toBeVisible();
  });

  test('should submit operator notes in audit trail', async ({ page }) => {
    // Switch to investigate mode
    await page.getByRole('button', { name: /Show Investigation Details/i }).click();

    const notesInput = page.getByPlaceholder(/Optional operator investigation notes/i);
    await notesInput.fill('Verified with Kirana store merchant log book.');

    const approveBtn = page.getByRole('button', { name: /Approve Settlement/i });
    await approveBtn.click();

    // Success notification
    await expect(page.getByText(/recorded in audit trail/i)).toBeVisible();
  });

  test('should display Case Not Found state for invalid ID', async ({ page }) => {
    await page.route(/\/api\/cases\/invalid_case_id$/, async (route) => {
      await route.fulfill({ status: 404, body: '' });
    });

    await page.goto('/cases/invalid_case_id');
    await expect(page.getByText(/Case Not Found/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /Return to Exception Workbench/i })).toBeVisible();
  });
});
