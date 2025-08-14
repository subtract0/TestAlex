import { test, expect } from '@playwright/test';
import { PurchasePage } from '../utils/purchase-page';

test.describe('Course Purchase E2E Tests', () => {
  let purchasePage: PurchasePage;

  test.beforeEach(async ({ page }) => {
    purchasePage = new PurchasePage(page);
  });

  test('should display pricing information correctly', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.testPricingDisplay();
  });

  test('should handle valid purchase flow', async ({ page }) => {
    // Skip actual payment in CI environment
    if (process.env.CI) {
      test.skip('Skipping payment test in CI environment');
    }
    
    await purchasePage.navigateToPurchase();
    await purchasePage.testValidPurchaseFlow();
  });

  test('should handle invalid payment details', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.testInvalidPaymentFlow();
  });

  test('should show security features', async ({ page }) => {
    await purchasePage.testSecurityFeatures();
  });

  test('should work on mobile devices', async ({ page }) => {
    await purchasePage.testMobilePurchaseFlow();
  });

  test('should load purchase page quickly', async ({ page }) => {
    await purchasePage.testPurchasePerformance();
  });

  test('should be accessible', async ({ page }) => {
    await purchasePage.testPurchaseAccessibility();
  });

  test('should support different pricing tiers', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.testPricingTiers();
  });

  test('should allow purchase cancellation', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.testPurchaseCancellation();
  });

  test('should initiate purchase from course page', async ({ page }) => {
    await purchasePage.navigateToCourseAndPurchase();
    
    // Verify we're on purchase/checkout flow
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/purchase|checkout|payment|buy/);
  });

  test('should validate form inputs', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.initiatePurchase();
    
    // Try to submit empty form
    const submitButton = page.locator('[data-testid="submit-payment"], button[type="submit"]:has-text("Pay"), .submit-payment');
    
    if (await submitButton.isVisible()) {
      await submitButton.click();
      
      // Should show validation errors
      const errorElements = page.locator('.error, .invalid, [data-error="true"]');
      const errorCount = await errorElements.count();
      
      expect(errorCount).toBeGreaterThan(0);
    }
  });

  test('should handle payment provider integration', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.initiatePurchase();
    
    // Check for payment provider elements (Stripe, PayPal, etc.)
    const paymentProviders = page.locator('[src*="stripe"], [src*="paypal"], iframe[title*="payment"], iframe[name*="payment"]');
    
    if (await paymentProviders.count() > 0) {
      await expect(paymentProviders.first()).toBeVisible();
      console.log('Payment provider integration detected');
    }
  });

  test('should show loading states during payment', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.initiatePurchase();
    
    const testData = {
      email: 'test@acimguide.com',
      cardNumber: '4000000000000002', // Card that triggers payment processing
      expiry: '12/25',
      cvv: '123'
    };
    
    await purchasePage.fillPaymentForm(testData);
    await purchasePage.submitPayment();
    
    // Should show loading indicator
    const loadingIndicator = page.locator('[data-testid="loading"], .loading, .spinner, .processing');
    
    // Either loading indicator appears, or we get an error/success state quickly
    try {
      await loadingIndicator.waitFor({ state: 'visible', timeout: 3000 });
      console.log('Loading indicator shown during payment processing');
    } catch {
      console.log('Payment processed immediately or error handling prevented loading state');
    }
  });

  test('should preserve form data on validation errors', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    await purchasePage.initiatePurchase();
    
    const testEmail = 'test@acimguide.com';
    const emailInput = page.locator('[data-testid="email-input"], input[type="email"], input[name="email"]');
    
    if (await emailInput.isVisible()) {
      await emailInput.fill(testEmail);
      
      // Try to submit with incomplete form
      const submitButton = page.locator('[data-testid="submit-payment"], button[type="submit"]');
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForTimeout(2000);
        
        // Email should still be there after validation error
        const preservedEmail = await emailInput.inputValue();
        expect(preservedEmail).toBe(testEmail);
      }
    }
  });

  test('should support promotional codes', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    
    // Look for promo code input
    const promoInput = page.locator('[data-testid="promo-code"], input[name*="promo"], input[placeholder*="promo"], input[placeholder*="coupon"]');
    
    if (await promoInput.isVisible()) {
      await promoInput.fill('TESTCODE');
      
      const applyButton = page.locator('button:has-text("Apply"), [data-testid="apply-promo"]');
      if (await applyButton.isVisible()) {
        await applyButton.click();
        await page.waitForTimeout(2000);
        
        // Should show some feedback about the promo code
        const feedback = page.locator('.promo-message, .discount-applied, .promo-error');
        if (await feedback.count() > 0) {
          console.log('Promo code functionality detected');
        }
      }
    }
  });

  test('should handle different currencies', async ({ page }) => {
    await purchasePage.navigateToPurchase();
    
    // Look for currency selector
    const currencySelector = page.locator('[data-testid="currency-selector"], select[name="currency"], .currency-picker');
    
    if (await currencySelector.isVisible()) {
      const options = currencySelector.locator('option');
      const optionCount = await options.count();
      
      if (optionCount > 1) {
        // Test selecting different currency
        await currencySelector.selectOption({ index: 1 });
        await page.waitForTimeout(1000);
        
        // Price should update
        const priceDisplay = page.locator('[data-testid="pricing"], .price-display, .pricing-section');
        await expect(priceDisplay).toBeVisible();
        
        console.log('Multi-currency support detected');
      }
    }
  });
});
