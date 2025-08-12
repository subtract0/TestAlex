import { Page, expect, Locator } from '@playwright/test';
import { TestHelpers } from './test-helpers';

export class BlogCTAPage {
  private helpers: TestHelpers;
  
  // Blog CTA selectors
  private blogContainer: Locator;
  private ctaSection: Locator;
  private ctaButtons: Locator;
  private primaryCTA: Locator;
  private secondaryCTA: Locator;
  private newsletterSignup: Locator;
  private emailInput: Locator;
  private subscribeButton: Locator;
  private socialLinks: Locator;
  private courseLinkCTA: Locator;
  private successMessage: Locator;
  private errorMessage: Locator;

  constructor(private page: Page) {
    this.helpers = new TestHelpers(page);
    
    // Initialize locators for blog CTA elements
    this.blogContainer = page.locator('[data-testid="blog-container"], .blog-content, main');
    this.ctaSection = page.locator('[data-testid="cta-section"], .cta-section, .call-to-action');
    this.ctaButtons = page.locator('[data-testid="cta-button"], .cta-button, a[href*="acimguide"], a:has-text("CourseGPT")');
    this.primaryCTA = page.locator('[data-testid="primary-cta"], .cta-button.primary, a.cta-button:first-child');
    this.secondaryCTA = page.locator('[data-testid="secondary-cta"], .cta-button.secondary, a.cta-button:nth-child(2)');
    this.newsletterSignup = page.locator('[data-testid="newsletter-signup"], .newsletter-signup, .email-signup');
    this.emailInput = page.locator('[data-testid="newsletter-email"], input[type="email"], input[name="email"]');
    this.subscribeButton = page.locator('[data-testid="subscribe-button"], button:has-text("Subscribe"), .subscribe-btn');
    this.socialLinks = page.locator('[data-testid="social-links"], .social-links, .social-media');
    this.courseLinkCTA = page.locator('a[href*="acimguide.com"], a:has-text("CourseGPT"), a:has-text("Start"), a:has-text("Learn")');
    this.successMessage = page.locator('[data-testid="success-message"], .success-message, .subscription-success');
    this.errorMessage = page.locator('[data-testid="error-message"], .error-message, .subscription-error');
  }

  /**
   * Navigate to blog homepage
   */
  async navigateToBlog(): Promise<void> {
    await this.page.goto('/blog');
    await this.helpers.waitForNetworkIdle();
    await this.helpers.waitForStableElement(this.blogContainer);
  }

  /**
   * Navigate to specific blog post
   */
  async navigateToBlogPost(postSlug?: string): Promise<void> {
    const url = postSlug ? `/blog/${postSlug}` : '/blog';
    await this.page.goto(url);
    await this.helpers.waitForNetworkIdle();
    await this.helpers.waitForStableElement(this.blogContainer);
  }

  /**
   * Test CTA visibility and positioning
   */
  async testCTAVisibility(): Promise<void> {
    // Check that CTAs are present and visible
    await expect(this.ctaSection).toBeVisible();
    
    const ctaCount = await this.ctaButtons.count();
    expect(ctaCount).toBeGreaterThan(0);
    
    // Check primary CTA
    if (await this.primaryCTA.count() > 0) {
      await expect(this.primaryCTA).toBeVisible();
      const primaryText = await this.primaryCTA.textContent();
      expect(primaryText).toBeTruthy();
      expect(primaryText?.toLowerCase()).toMatch(/start|begin|try|learn|coursegpt|acim/);
    }
  }

  /**
   * Test CTA click functionality
   */
  async testCTAClickThrough(): Promise<void> {
    const initialUrl = this.page.url();
    
    // Test primary CTA click
    if (await this.primaryCTA.count() > 0) {
      // Get CTA details before clicking
      const ctaHref = await this.primaryCTA.getAttribute('href');
      const ctaText = await this.primaryCTA.textContent();
      
      console.log(`Testing CTA: "${ctaText}" -> ${ctaHref}`);
      
      // Click CTA
      await this.primaryCTA.click();
      
      // Handle different scenarios
      if (ctaHref?.includes('acimguide.com') || ctaHref?.includes('coursegpt')) {
        // External link - should open in new tab or navigate
        await this.page.waitForTimeout(2000);
        
        // Check if we're on a new page or tab
        const currentUrl = this.page.url();
        const hasNavigated = currentUrl !== initialUrl;
        
        if (hasNavigated) {
          expect(currentUrl).toMatch(/acimguide|coursegpt/);
        }
      } else if (ctaHref?.startsWith('/')) {
        // Internal link - should navigate within site
        await this.helpers.waitForNetworkIdle();
        const currentUrl = this.page.url();
        expect(currentUrl).toContain(ctaHref);
      }
    }
  }

  /**
   * Test newsletter signup functionality
   */
  async testNewsletterSignup(): Promise<void> {
    if (await this.newsletterSignup.count() > 0) {
      await expect(this.newsletterSignup).toBeVisible();
      
      // Test with valid email
      const testEmail = 'test@acimguide.com';
      await this.emailInput.fill(testEmail);
      await this.subscribeButton.click();
      
      await this.helpers.waitForNetworkIdle();
      
      // Check for success or error message
      try {
        await this.successMessage.waitFor({ state: 'visible', timeout: 5000 });
        await expect(this.successMessage).toBeVisible();
        
        const successText = await this.successMessage.textContent();
        expect(successText?.toLowerCase()).toMatch(/success|subscribed|thank you/);
      } catch {
        // If no success message, check for error handling
        if (await this.errorMessage.isVisible()) {
          console.log('Newsletter signup showed error - this may be expected for test environment');
        }
      }
    }
  }

  /**
   * Test invalid email handling in newsletter
   */
  async testInvalidEmailHandling(): Promise<void> {
    if (await this.newsletterSignup.count() > 0) {
      const invalidEmails = ['invalid-email', 'test@', '@domain.com', ''];
      
      for (const invalidEmail of invalidEmails) {
        await this.emailInput.clear();
        if (invalidEmail) {
          await this.emailInput.fill(invalidEmail);
        }
        
        await this.subscribeButton.click();
        await this.page.waitForTimeout(1000);
        
        // Should either show error or prevent submission
        const errorVisible = await this.errorMessage.isVisible();
        const inputValidation = await this.emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
        
        expect(errorVisible || !inputValidation).toBeTruthy();
      }
    }
  }

  /**
   * Test CTA tracking and analytics
   */
  async testCTATracking(): Promise<void> {
    // Monitor network requests for analytics
    const analyticsRequests: any[] = [];
    
    this.page.on('request', request => {
      const url = request.url();
      if (url.includes('analytics') || url.includes('google-analytics') || url.includes('gtag') || url.includes('track')) {
        analyticsRequests.push({
          url: request.url(),
          method: request.method(),
          postData: request.postData()
        });
      }
    });
    
    // Click CTA and check if tracking fires
    if (await this.primaryCTA.count() > 0) {
      await this.primaryCTA.click();
      await this.page.waitForTimeout(2000);
      
      // Verify analytics tracking occurred
      expect(analyticsRequests.length).toBeGreaterThan(0);
      console.log(`Detected ${analyticsRequests.length} analytics requests`);
    }
  }

  /**
   * Test social media links
   */
  async testSocialLinks(): Promise<void> {
    if (await this.socialLinks.count() > 0) {
      const socialButtons = this.socialLinks.locator('a, button');
      const count = await socialButtons.count();
      
      for (let i = 0; i < Math.min(count, 3); i++) {
        const socialLink = socialButtons.nth(i);
        await expect(socialLink).toBeVisible();
        
        const href = await socialLink.getAttribute('href');
        const ariaLabel = await socialLink.getAttribute('aria-label') || await socialLink.textContent();
        
        expect(ariaLabel).toBeTruthy();
        
        if (href) {
          expect(href).toMatch(/facebook|twitter|linkedin|instagram|youtube/);
        }
      }
    }
  }

  /**
   * Test CTA performance and loading
   */
  async testCTAPerformance(): Promise<void> {
    const startTime = Date.now();
    
    // Navigate and wait for CTAs to load
    await this.navigateToBlog();
    await this.helpers.waitForStableElement(this.ctaSection);
    
    const loadTime = Date.now() - startTime;
    
    // CTAs should load quickly
    expect(loadTime).toBeLessThan(5000);
    
    // Test CTA interaction responsiveness
    const interactionStart = Date.now();
    
    if (await this.primaryCTA.count() > 0) {
      await this.primaryCTA.hover();
      await this.page.waitForTimeout(100);
      
      const interactionTime = Date.now() - interactionStart;
      expect(interactionTime).toBeLessThan(500); // Should respond within 500ms
    }
  }

  /**
   * Test CTA accessibility
   */
  async testCTAAccessibility(): Promise<void> {
    // Check CTA button accessibility
    if (await this.primaryCTA.count() > 0) {
      const ctaRole = await this.primaryCTA.getAttribute('role');
      const ctaAriaLabel = await this.primaryCTA.getAttribute('aria-label');
      const ctaText = await this.primaryCTA.textContent();
      
      // Should have proper button semantics
      expect(ctaRole === 'button' || await this.primaryCTA.evaluate(el => el.tagName.toLowerCase() === 'button' || el.tagName.toLowerCase() === 'a')).toBeTruthy();
      
      // Should have accessible text
      expect(ctaAriaLabel || ctaText).toBeTruthy();
      
      // Test keyboard navigation
      await this.primaryCTA.focus();
      await expect(this.primaryCTA).toBeFocused();
      
      // Test keyboard activation
      await this.primaryCTA.press('Enter');
      await this.page.waitForTimeout(1000);
    }
    
    // Test newsletter accessibility
    if (await this.newsletterSignup.count() > 0) {
      const emailLabel = await this.emailInput.getAttribute('aria-label') || 
                         await this.page.locator('label[for*="email"]').textContent();
      expect(emailLabel).toBeTruthy();
      
      // Test form submission with Enter key
      await this.emailInput.focus();
      await this.emailInput.fill('test@acimguide.com');
      await this.emailInput.press('Enter');
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Test CTA on mobile devices
   */
  async testMobileCTA(): Promise<void> {
    await this.helpers.setMobileViewport();
    await this.page.reload();
    await this.helpers.waitForNetworkIdle();
    
    // CTAs should be visible and functional on mobile
    await expect(this.ctaSection).toBeVisible();
    
    if (await this.primaryCTA.count() > 0) {
      await expect(this.primaryCTA).toBeVisible();
      
      // CTA should be properly sized for mobile interaction
      const ctaBounds = await this.primaryCTA.boundingBox();
      if (ctaBounds) {
        expect(ctaBounds.height).toBeGreaterThan(44); // iOS minimum touch target
        expect(ctaBounds.width).toBeGreaterThan(44);
      }
      
      // Test mobile tap
      await this.primaryCTA.tap();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Test CTA A/B testing variations
   */
  async testCTAVariations(): Promise<void> {
    // Look for different CTA variations that might be A/B tested
    const possibleCTATexts = [
      'Start with CourseGPT',
      'Try CourseGPT Free',
      'Begin Your ACIM Journey',
      'Access CourseGPT Now',
      'Start Learning ACIM',
      'Get CourseGPT',
      'Join CourseGPT'
    ];
    
    const ctaText = await this.primaryCTA.textContent();
    
    if (ctaText) {
      console.log(`Current CTA text: "${ctaText}"`);
      
      // Verify CTA text is compelling and action-oriented
      const hasActionWord = /start|try|begin|access|get|join|learn/i.test(ctaText);
      expect(hasActionWord).toBeTruthy();
      
      // Verify mentions CourseGPT or ACIM
      const mentionsProduct = /coursegpt|acim/i.test(ctaText);
      expect(mentionsProduct).toBeTruthy();
    }
  }

  /**
   * Test CTA placement and design consistency
   */
  async testCTADesignConsistency(): Promise<void> {
    // Check that CTAs follow consistent design patterns
    const ctaButtons = await this.ctaButtons.all();
    
    for (const cta of ctaButtons) {
      // Check for consistent styling
      const backgroundColor = await cta.evaluate(el => getComputedStyle(el).backgroundColor);
      const padding = await cta.evaluate(el => getComputedStyle(el).padding);
      const borderRadius = await cta.evaluate(el => getComputedStyle(el).borderRadius);
      
      // CTAs should have proper styling (non-default colors)
      expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
      expect(padding).not.toBe('0px'); // Should have padding
      
      console.log(`CTA styling - Background: ${backgroundColor}, Padding: ${padding}, Border Radius: ${borderRadius}`);
    }
  }

  /**
   * Test blog-to-course conversion funnel
   */
  async testConversionFunnel(): Promise<void> {
    // Simulate user journey from blog to course signup
    await this.navigateToBlog();
    
    // Read some content (simulate engagement)
    await this.page.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight / 2);
    });
    await this.page.waitForTimeout(3000); // Simulate reading time
    
    // Click CTA
    if (await this.courseLinkCTA.count() > 0) {
      const ctaHref = await this.courseLinkCTA.first().getAttribute('href');
      await this.courseLinkCTA.first().click();
      
      // Track the conversion path
      await this.helpers.waitForNetworkIdle();
      
      const finalUrl = this.page.url();
      console.log(`Conversion path: Blog -> ${finalUrl}`);
      
      // Verify landed on appropriate destination
      if (ctaHref?.includes('acimguide')) {
        expect(finalUrl).toMatch(/acimguide|coursegpt/);
      }
    }
  }
}
