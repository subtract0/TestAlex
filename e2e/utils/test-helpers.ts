import { Page, expect, Locator } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Wait for element to be visible and stable
   */
  async waitForStableElement(locator: Locator, timeout = 10000): Promise<void> {
    await locator.waitFor({ state: 'visible', timeout });
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Take a screenshot with custom name
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true
    });
  }

  /**
   * Check for ACIM content authenticity
   */
  async validateACIMContent(text: string): Promise<boolean> {
    // Check for common ACIM terminology and structure
    const acimKeywords = [
      'Course in Miracles', 'Holy Spirit', 'forgiveness', 'miracle', 
      'lesson', 'workbook', 'manual', 'ego', 'perception', 'truth'
    ];
    
    const hasACIMKeywords = acimKeywords.some(keyword => 
      text.toLowerCase().includes(keyword.toLowerCase())
    );
    
    // Check for typical ACIM lesson structure
    const hasLessonStructure = /lesson \d+/i.test(text) || 
                               /today's lesson/i.test(text) ||
                               /workbook/i.test(text);
    
    return hasACIMKeywords || hasLessonStructure;
  }

  /**
   * Simulate mobile device viewport
   */
  async setMobileViewport(): Promise<void> {
    await this.page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 size
  }

  /**
   * Simulate tablet device viewport
   */
  async setTabletViewport(): Promise<void> {
    await this.page.setViewportSize({ width: 820, height: 1180 }); // iPad size
  }

  /**
   * Check accessibility basics
   */
  async checkBasicAccessibility(): Promise<void> {
    // Check for alt text on images
    const images = await this.page.locator('img').all();
    for (const image of images) {
      const alt = await image.getAttribute('alt');
      expect(alt).toBeTruthy();
    }

    // Check for proper heading hierarchy
    const h1s = await this.page.locator('h1').count();
    expect(h1s).toBeGreaterThanOrEqual(1);
    expect(h1s).toBeLessThanOrEqual(1); // Should have only one h1 per page
  }

  /**
   * Measure Core Web Vitals
   */
  async measurePerformance(): Promise<any> {
    const performanceMetrics = await this.page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const vitals: any = {};
          
          entries.forEach((entry: any) => {
            if (entry.name === 'first-contentful-paint') {
              vitals.fcp = entry.startTime;
            }
            if (entry.entryType === 'largest-contentful-paint') {
              vitals.lcp = entry.startTime;
            }
            if (entry.name === 'first-input-delay') {
              vitals.fid = entry.processingStart - entry.startTime;
            }
          });
          
          resolve(vitals);
        }).observe({ entryTypes: ['paint', 'largest-contentful-paint', 'first-input'] });
        
        // Fallback timeout
        setTimeout(() => resolve({}), 5000);
      });
    });

    return performanceMetrics;
  }

  /**
   * Check for console errors
   */
  async checkConsoleErrors(): Promise<string[]> {
    const errors: string[] = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    return errors;
  }

  /**
   * Wait for network to be idle
   */
  async waitForNetworkIdle(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Simulate slow network conditions
   */
  async simulateSlowNetwork(): Promise<void> {
    const client = await this.page.context().newCDPSession(this.page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: 200 * 1024 / 8, // 200kb/s
      uploadThroughput: 200 * 1024 / 8,
      latency: 100,
    });
  }

  /**
   * Reset network conditions
   */
  async resetNetworkConditions(): Promise<void> {
    const client = await this.page.context().newCDPSession(this.page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: -1,
      uploadThroughput: -1,
      latency: 0,
    });
  }
}
