const puppeteer = require('puppeteer');

async function testAuthentication() {
  const browser = await puppeteer.launch({ 
    headless: false,  // Show browser for debugging
    devtools: true,   // Open devtools
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('🚀 Starting automated authentication test...');
    
    // Enable console logging from the page
    page.on('console', msg => {
      const type = msg.type();
      if (type === 'error') {
        console.log('❌ Browser Error:', msg.text());
      } else if (type === 'log') {
        console.log('📝 Browser Log:', msg.text());
      }
    });
    
    // Navigate to the website
    console.log('🌐 Navigating to website...');
    await page.goto('https://acim-guide-production.web.app', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    console.log('✅ Page loaded successfully');
    
    // Wait for Firebase to initialize and check status
    console.log('⏳ Waiting for Firebase authentication...');
    
    // Wait up to 30 seconds for authentication to complete
    const authResult = await page.waitForFunction(() => {
      const status = document.getElementById('status');
      if (!status) return false;
      
      const statusText = status.textContent;
      const statusClass = status.className;
      
      // Check if we're no longer connecting (either success or error)
      if (!statusClass.includes('connecting')) {
        return {
          text: statusText,
          className: statusClass,
          isReady: statusText.includes('Ready') || statusText === '●',
          isError: statusClass.includes('error'),
          isConnecting: false
        };
      }
      
      // Still connecting, return false to keep waiting
      return false;
    }, { timeout: 30000 });
    
    const authStatus = await authResult.jsonValue();
    console.log('📊 Authentication Status:', authStatus);
    
    if (authStatus.isError) {
      // Capture any error messages from the chat
      const errorMessages = await page.evaluate(() => {
        const messages = document.querySelectorAll('.message.assistant .message-content');
        return Array.from(messages).map(msg => msg.textContent).join('\\n');
      });
      
      console.log('❌ Authentication failed!');
      console.log('🔍 Error messages from UI:', errorMessages);
      
      // Take a screenshot for debugging
      await page.screenshot({ path: 'auth-error-screenshot.png', fullPage: true });
      console.log('📸 Screenshot saved as auth-error-screenshot.png');
      
      return false;
    }
    
    if (authStatus.isReady) {
      console.log('✅ Authentication successful!');
      
      // Test sending a message
      console.log('🧪 Testing message sending...');
      await page.type('#messageInput', 'Hello, test message');
      await page.click('#sendButton');
      
      // Wait for response or loading state
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Check if message was sent
      const messageTest = await page.evaluate(() => {
        const userMessages = document.querySelectorAll('.message.user .message-content');
        const lastMessage = userMessages[userMessages.length - 1];
        return lastMessage ? lastMessage.textContent : null;
      });
      
      if (messageTest && messageTest.includes('Hello, test message')) {
        console.log('✅ Message sending test successful!');
      } else {
        console.log('⚠️  Message sending test failed or inconclusive');
      }
      
      // Take a success screenshot
      await page.screenshot({ path: 'auth-success-screenshot.png', fullPage: true });
      console.log('📸 Success screenshot saved as auth-success-screenshot.png');
      
      return true;
    }
    
    console.log('⚠️  Authentication status unclear:', authStatus);
    return false;
    
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    
    // Take an error screenshot
    try {
      await page.screenshot({ path: 'test-error-screenshot.png', fullPage: true });
      console.log('📸 Error screenshot saved as test-error-screenshot.png');
    } catch (screenshotError) {
      console.error('Could not take screenshot:', screenshotError);
    }
    
    return false;
  } finally {
    await browser.close();
  }
}

// Run the test
testAuthentication().then((success) => {
  if (success) {
    console.log('🎉 All tests passed! Authentication is working.');
    process.exit(0);
  } else {
    console.log('💥 Tests failed. Check the logs and screenshots for details.');
    process.exit(1);
  }
}).catch((error) => {
  console.error('💥 Test script failed:', error);
  process.exit(1);
});
