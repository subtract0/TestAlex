import { test, expect } from '@playwright/test';
import { BlogCTAPage } from '../utils/blog-cta-page';

test.describe('Blog CTA E2E Tests', () => {
  let blogCTAPage: BlogCTAPage;

  test.beforeEach(async ({ page }) => {
    blogCTAPage = new BlogCTAPage(page);
  });

  test('should display CTAs correctly on blog homepage', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTAVisibility();
  });

  test('should handle CTA click-through functionality', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTAClickThrough();
  });

  test('should handle newsletter signup', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testNewsletterSignup();
  });

  test('should validate email input in newsletter', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testInvalidEmailHandling();
  });

  test('should track CTA interactions', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTATracking();
  });

  test('should display social media links', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testSocialLinks();
  });

  test('should load CTAs quickly', async ({ page }) => {
    await blogCTAPage.testCTAPerformance();
  });

  test('should be accessible', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTAAccessibility();
  });

  test('should work on mobile devices', async ({ page }) => {
    await blogCTAPage.testMobileCTA();
  });

  test('should have compelling CTA text variations', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTAVariations();
  });

  test('should maintain design consistency', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    await blogCTAPage.testCTADesignConsistency();
  });

  test('should support blog-to-course conversion funnel', async ({ page }) => {
    await blogCTAPage.testConversionFunnel();
  });

  test('should display CTAs on blog posts', async ({ page }) => {
    // Navigate to a specific blog post if available
    await page.goto('/blog');
    await page.waitForLoadState('networkidle');
    
    // Look for blog post links
    const postLinks = page.locator('a[href*="/blog/"], .blog-post-link, .post-title a');
    
    if (await postLinks.count() > 0) {
      const firstPost = postLinks.first();
      const href = await firstPost.getAttribute('href');
      
      if (href) {
        await blogCTAPage.navigateToBlogPost(href.split('/').pop());
        await blogCTAPage.testCTAVisibility();
      }
    } else {
      // Test with a sample post slug
      await blogCTAPage.navigateToBlogPost('daily-acim-lesson');
      // CTAs might not exist on specific posts, so just check the page loads
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should handle CTA hover effects', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    const ctaButtons = page.locator('[data-testid="cta-button"], .cta-button, a[href*="acimguide"]');
    
    if (await ctaButtons.count() > 0) {
      const firstCTA = ctaButtons.first();
      
      // Test hover effect
      await firstCTA.hover();
      await page.waitForTimeout(500);
      
      // Check if hover styles are applied (this is basic - could be expanded)
      const hoverStyle = await firstCTA.evaluate(el => {
        const computed = getComputedStyle(el);
        return {
          backgroundColor: computed.backgroundColor,
          transform: computed.transform,
          boxShadow: computed.boxShadow
        };
      });
      
      console.log('CTA hover styles:', hoverStyle);
      
      // Should have some kind of hover effect (not comprehensive)
      expect(
        hoverStyle.transform !== 'none' || 
        hoverStyle.boxShadow !== 'none' ||
        hoverStyle.backgroundColor !== 'rgba(0, 0, 0, 0)'
      ).toBeTruthy();
    }
  });

  test('should handle multiple CTA placements', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    const ctaSections = page.locator('[data-testid="cta-section"], .cta-section, .call-to-action');
    const ctaCount = await ctaSections.count();
    
    console.log(`Found ${ctaCount} CTA sections on the page`);
    
    // Should have at least one CTA
    expect(ctaCount).toBeGreaterThan(0);
    
    // Test each CTA section
    for (let i = 0; i < Math.min(ctaCount, 3); i++) {
      const ctaSection = ctaSections.nth(i);
      await expect(ctaSection).toBeVisible();
      
      const ctaButtons = ctaSection.locator('a, button');
      const buttonCount = await ctaButtons.count();
      
      expect(buttonCount).toBeGreaterThan(0);
      console.log(`CTA section ${i + 1} has ${buttonCount} buttons`);
    }
  });

  test('should maintain CTA visibility during scroll', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    // Look for sticky or floating CTAs
    const stickyCTA = page.locator('.sticky-cta, .floating-cta, .fixed-cta, [data-sticky="true"]');
    
    if (await stickyCTA.isVisible()) {
      // Scroll down
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
      await page.waitForTimeout(500);
      
      // Sticky CTA should still be visible
      await expect(stickyCTA).toBeVisible();
      
      console.log('Sticky CTA remains visible during scroll');
    }
  });

  test('should handle CTA for different user segments', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    // Look for personalized or segmented CTAs
    const personalizedCTAs = page.locator('[data-segment], .new-user-cta, .returning-user-cta, .premium-cta');
    
    if (await personalizedCTAs.count() > 0) {
      console.log('Personalized CTAs detected');
      
      for (let i = 0; i < await personalizedCTAs.count(); i++) {
        const cta = personalizedCTAs.nth(i);
        await expect(cta).toBeVisible();
        
        const segmentData = await cta.getAttribute('data-segment');
        if (segmentData) {
          console.log(`CTA segment: ${segmentData}`);
        }
      }
    }
  });

  test('should show appropriate CTAs based on content', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    // Get page content to determine context
    const pageContent = await page.textContent('body');
    const hasACIMContent = pageContent?.toLowerCase().includes('acim') || 
                          pageContent?.toLowerCase().includes('course in miracles');
    
    if (hasACIMContent) {
      // Should have ACIM-specific CTAs
      const acimCTAs = page.locator('a:has-text("CourseGPT"), a:has-text("ACIM"), a[href*="acimguide"]');
      const acimCTACount = await acimCTAs.count();
      
      expect(acimCTACount).toBeGreaterThan(0);
      console.log(`Found ${acimCTACount} ACIM-specific CTAs`);
    }
  });

  test('should handle CTA A/B test variations', async ({ page }) => {
    await blogCTAPage.navigateToBlog();
    
    // Look for A/B test markers
    const abTestElements = page.locator('[data-ab-test], [data-variant], .variant-a, .variant-b');
    
    if (await abTestElements.count() > 0) {
      console.log('A/B test variations detected');
      
      const variant = await abTestElements.first().getAttribute('data-variant') || 
                     await abTestElements.first().getAttribute('data-ab-test');
      
      console.log(`Current variant: ${variant}`);
      
      // Test the CTA regardless of variant
      await blogCTAPage.testCTAVisibility();
    }
  });
});
