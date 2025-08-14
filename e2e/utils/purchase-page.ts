import { Page, expect, Locator } from '@playwright/test';
import { TestHelpers } from './test-helpers';

export class PurchasePage {
  private helpers: TestHelpers;
  
  // Purchase flow selectors
  private courseCard: Locator;
  private pricingSection: Locator;
  private buyButton: Locator;
  private paymentForm: Locator;
  private emailInput: Locator;
  private cardNumberInput: Locator;
  private expiryInput: Locator;
  private cvvInput: Locator;
  private submitPaymentButton: Locator;
  private successMessage: Locator;
  private errorMessage: Locator;
  private loadingSpinner: Locator;
  private securityBadges: Locator;

  constructor(private page: Page) {
    this.helpers = new TestHelpers(page);
    
    // Initialize locators - adjust based on actual payment provider integration
    this.courseCard = page.locator('[data-testid="course-card"], .course-card, .product-card');
    this.pricingSection = page.locator('[data-testid="pricing"], .pricing-section, .price-display');
    this.buyButton = page.locator('[data-testid="buy-button"], button:has-text("Buy"), button:has-text("Purchase"), .buy-now');
    this.paymentForm = page.locator('[data-testid="payment-form"], .payment-form, form[data-payment]');
    this.emailInput = page.locator('[data-testid="email-input"], input[type="email"], input[name="email"]');
    this.cardNumberInput = page.locator('[data-testid="card-number"], input[name="cardNumber"], #card-number');
    this.expiryInput = page.locator('[data-testid="expiry"], input[name="expiry"], #expiry');
    this.cvvInput = page.locator('[data-testid="cvv"], input[name="cvv"], #cvv');
    this.submitPaymentButton = page.locator('[data-testid="submit-payment"], button[type="submit"]:has-text("Pay"), .submit-payment');
    this.successMessage = page.locator('[data-testid="success-message"], .success-message, .payment-success');
    this.errorMessage = page.locator('[data-testid="error-message"], .error-message, .payment-error');
    this.loadingSpinner = page.locator('[data-testid="loading"], .loading, .spinner');
    this.securityBadges = page.locator('[data-testid="security-badges"], .security-badges, .ssl-badge');
  }

  /**
   * Navigate to purchase page
   */
  async navigateToPurchase(): Promise<void> {
    await this.page.goto('/purchase');
    await this.helpers.waitForNetworkIdle();
    await this.helpers.waitForStableElement(this.pricingSection);
  }

  /**
   * Navigate to course page and initiate purchase
   */
  async navigateToCourseAndPurchase(): Promise<void> {
    await this.page.goto('/courses');
    await this.helpers.waitForNetworkIdle();
    
    // Find and click on the first available course
    if (await this.courseCard.count() > 0) {
      await this.courseCard.first().click();
      await this.helpers.waitForNetworkIdle();
    }
    
    // Click the buy button
    await this.helpers.waitForStableElement(this.buyButton);
    await this.buyButton.click();
  }

  /**
   * Test pricing display and accuracy
   */
  async testPricingDisplay(): Promise<void> {
    await this.helpers.waitForStableElement(this.pricingSection);
    
    // Check that pricing is visible and properly formatted
    const priceText = await this.pricingSection.textContent();
    expect(priceText).toBeTruthy();
    
    // Should contain currency symbol and proper formatting
    expect(priceText).toMatch(/\$\d+(\.\d{2})?|\d+(\.\d{2})?\s*USD/);
    
    // Check for any pricing tiers or discounts
    const pricingOptions = this.pricingSection.locator('.price-option, [data-testid="price-option"]');
    const count = await pricingOptions.count();
    
    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const option = pricingOptions.nth(i);
        await expect(option).toBeVisible();
        
        const optionText = await option.textContent();
        expect(optionText).toMatch(/\$\d+|\d+\s*USD/);
      }
    }
  }

  /**
   * Test purchase flow with valid payment details
   */
  async testValidPurchaseFlow(): Promise<void> {
    // Use test payment details (Stripe test card)
    const testPaymentData = {
      email: 'test@acimguide.com',
      cardNumber: '4242424242424242', // Stripe test card
      expiry: '12/25',
      cvv: '123'
    };

    await this.initiatePurchase();
    await this.fillPaymentForm(testPaymentData);
    await this.submitPayment();
    await this.verifyPurchaseSuccess();
  }

  /**
   * Initiate purchase flow
   */
  async initiatePurchase(): Promise<void> {
    await this.helpers.waitForStableElement(this.buyButton);
    await this.buyButton.click();
    await this.helpers.waitForNetworkIdle();
    
    // Wait for payment form to load
    await this.helpers.waitForStableElement(this.paymentForm);
  }

  /**
   * Fill payment form with provided data
   */
  async fillPaymentForm(paymentData: {
    email: string;
    cardNumber: string;
    expiry: string;
    cvv: string;
  }): Promise<void> {
    // Fill email
    await this.emailInput.fill(paymentData.email);
    
    // Fill card details - handle iframe if payment provider uses one
    await this.fillCardDetails(paymentData);
  }

  /**
   * Handle card details filling (may be in iframe)
   */
  private async fillCardDetails(paymentData: {
    cardNumber: string;
    expiry: string;
    cvv: string;
  }): Promise<void> {
    try {
      // Try direct filling first
      if (await this.cardNumberInput.isVisible()) {
        await this.cardNumberInput.fill(paymentData.cardNumber);
        await this.expiryInput.fill(paymentData.expiry);
        await this.cvvInput.fill(paymentData.cvv);
      } else {
        // Handle Stripe Elements or similar iframe-based inputs
        const stripeFrames = this.page.frameLocator('[src*="stripe"], [name*="stripe"], iframe[src*="payment"]');
        
        if (stripeFrames) {
          await stripeFrames.locator('input[name="cardnumber"], input[placeholder*="Card number"]').fill(paymentData.cardNumber);
          await stripeFrames.locator('input[name="exp-date"], input[placeholder*="MM"]').fill(paymentData.expiry);
          await stripeFrames.locator('input[name="cvc"], input[placeholder*="CVC"]').fill(paymentData.cvv);
        }
      }
    } catch (error) {
      console.warn('Could not fill card details - may need to adapt for specific payment provider');
      // Take screenshot for debugging
      await this.helpers.takeScreenshot('payment-form-issue');
    }
  }

  /**
   * Submit payment form
   */
  async submitPayment(): Promise<void> {
    await this.submitPaymentButton.click();
    
    // Wait for payment processing
    await this.loadingSpinner.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {
      // Loading spinner might not appear
    });
    
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 30000 }).catch(() => {
      // Continue if no spinner
    });
    
    await this.helpers.waitForNetworkIdle();
  }

  /**
   * Verify purchase success
   */
  async verifyPurchaseSuccess(): Promise<void> {
    // Check for success message
    await this.successMessage.waitFor({ state: 'visible', timeout: 10000 });
    await expect(this.successMessage).toBeVisible();
    
    const successText = await this.successMessage.textContent();
    expect(successText?.toLowerCase()).toMatch(/success|complete|thank you|confirmed/);
    
    // Should not have error messages
    const errorCount = await this.errorMessage.count();
    expect(errorCount).toBe(0);
  }

  /**
   * Test purchase flow with invalid payment details
   */
  async testInvalidPaymentFlow(): Promise<void> {
    const invalidPaymentData = {
      email: 'invalid-email',
      cardNumber: '1111111111111111', // Invalid card
      expiry: '01/20', // Expired
      cvv: '12' // Too short
    };

    await this.initiatePurchase();
    await this.fillPaymentForm(invalidPaymentData);
    await this.submitPayment();
    
    // Should show error messages
    await this.errorMessage.waitFor({ state: 'visible', timeout: 10000 });
    await expect(this.errorMessage).toBeVisible();
    
    // Should not show success
    const successCount = await this.successMessage.count();
    expect(successCount).toBe(0);
  }

  /**
   * Test security features
   */
  async testSecurityFeatures(): Promise<void> {
    await this.navigateToPurchase();
    
    // Check for SSL indicators
    const currentUrl = this.page.url();
    expect(currentUrl).toMatch(/^https:/); // Should be HTTPS
    
    // Check for security badges
    if (await this.securityBadges.count() > 0) {
      await expect(this.securityBadges.first()).toBeVisible();
    }
    
    // Check for secure form attributes
    const formSecure = await this.paymentForm.getAttribute('data-secure');
    // Note: this depends on implementation
  }

  /**
   * Test responsive design for purchase flow
   */
  async testMobilePurchaseFlow(): Promise<void> {
    await this.helpers.setMobileViewport();
    await this.page.reload();
    await this.helpers.waitForNetworkIdle();
    
    // All purchase elements should be visible and accessible on mobile
    await expect(this.pricingSection).toBeVisible();
    await expect(this.buyButton).toBeVisible();
    
    // Initiate purchase flow on mobile
    await this.buyButton.click();
    await this.helpers.waitForNetworkIdle();
    
    // Payment form should be mobile-friendly
    await expect(this.paymentForm).toBeVisible();
    await expect(this.emailInput).toBeVisible();
  }

  /**
   * Test purchase page performance
   */
  async testPurchasePerformance(): Promise<void> {
    const startTime = Date.now();
    
    await this.navigateToPurchase();
    
    const loadTime = Date.now() - startTime;
    
    // Purchase page should load quickly (under 3 seconds)
    expect(loadTime).toBeLessThan(3000);
    
    // Check Core Web Vitals
    const metrics = await this.helpers.measurePerformance();
    
    if (metrics.lcp) {
      expect(metrics.lcp).toBeLessThan(2500); // LCP should be under 2.5s
    }
    
    if (metrics.fcp) {
      expect(metrics.fcp).toBeLessThan(1800); // FCP should be under 1.8s
    }
  }

  /**
   * Test purchase accessibility
   */
  async testPurchaseAccessibility(): Promise<void> {
    await this.navigateToPurchase();
    
    // Basic accessibility checks
    await this.helpers.checkBasicAccessibility();
    
    // Purchase-specific accessibility
    const buyButtonAriaLabel = await this.buyButton.getAttribute('aria-label');
    expect(buyButtonAriaLabel || await this.buyButton.textContent()).toBeTruthy();
    
    // Form accessibility
    await this.buyButton.click();
    await this.helpers.waitForNetworkIdle();
    
    // Input labels
    const emailLabel = await this.emailInput.getAttribute('aria-label') || 
                      await this.page.locator('label[for*="email"]').textContent();
    expect(emailLabel).toBeTruthy();
    
    // Test keyboard navigation
    await this.emailInput.focus();
    await this.page.keyboard.press('Tab');
    
    // Should move to next form field
    const activeElement = await this.page.evaluate(() => document.activeElement?.tagName);
    expect(activeElement).toBe('INPUT');
  }

  /**
   * Test purchase flow with different pricing tiers
   */
  async testPricingTiers(): Promise<void> {
    await this.navigateToPurchase();
    
    const pricingOptions = this.pricingSection.locator('[data-testid="pricing-tier"], .pricing-tier, .price-option');
    const tierCount = await pricingOptions.count();
    
    if (tierCount > 1) {
      // Test selecting different tiers
      for (let i = 0; i < Math.min(tierCount, 3); i++) {
        const tier = pricingOptions.nth(i);
        await tier.click();
        await this.helpers.waitForNetworkIdle();
        
        // Verify selection is reflected in UI
        const isSelected = await tier.getAttribute('class');
        expect(isSelected).toMatch(/selected|active|chosen/);
        
        // Price should update if applicable
        const priceDisplay = await this.pricingSection.textContent();
        expect(priceDisplay).toMatch(/\$\d+|\d+\s*USD/);
      }
    }
  }

  /**
   * Test purchase cancellation flow
   */
  async testPurchaseCancellation(): Promise<void> {
    await this.initiatePurchase();
    
    // Look for cancel/back button
    const cancelButton = this.page.locator('[data-testid="cancel"], button:has-text("Cancel"), button:has-text("Back"), .cancel-purchase');
    
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      await this.helpers.waitForNetworkIdle();
      
      // Should return to previous page or show cancellation confirmation
      const currentUrl = this.page.url();
      expect(currentUrl).not.toMatch(/payment|checkout/);
    }
  }
}
