const puppeteer = require('puppeteer');

async function testFormatting() {
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('🧪 Testing message formatting...');
    
    await page.goto('https://acim-guide-production.web.app', { 
      waitUntil: 'networkidle2',
      timeout: 20000 
    });
    
    // Wait for authentication
    await page.waitForFunction(() => {
      const status = document.getElementById('status');
      return status && status.textContent.includes('Ready');
    }, { timeout: 15000 });
    
    console.log('✅ Page authenticated successfully');
    
    // Check how many messages we have initially
    const initialMessageCount = await page.evaluate(() => {
      return document.querySelectorAll('.message.assistant .message-content').length;
    });
    
    console.log(`📊 Initial assistant messages: ${initialMessageCount}`);
    
    // Test sending a message that might have formatting issues
    await page.type('#messageInput', 'Explain lesson 239 of ACIM');
    await page.click('#sendButton');
    
    // Wait for AI response (functions take 12-18 seconds according to logs)
    console.log('⏳ Waiting for AI response...');
    await new Promise(resolve => setTimeout(resolve, 20000));
    
    // Check message count again
    const finalMessageCount = await page.evaluate(() => {
      return document.querySelectorAll('.message.assistant .message-content').length;
    });
    
    console.log(`📊 Final assistant messages: ${finalMessageCount}`);
    
    if (finalMessageCount <= initialMessageCount) {
      console.log('⚠️  No new AI response received, testing welcome message formatting');
    }
    
    // Check for formatting artifacts in the actual AI response (not welcome message)
    const result = await page.evaluate(() => {
      const messages = document.querySelectorAll('.message.assistant .message-content');
      
      // Find the actual AI response (should be the one that mentions lesson 239)
      let responseMessage = null;
      for (const message of messages) {
        const text = message.textContent || '';
        if (text.toLowerCase().includes('lesson') && text.length > 200) {
          responseMessage = message;
          break;
        }
      }
      
      if (!responseMessage) {
        // Fallback to last message if no lesson response found
        responseMessage = messages[messages.length - 1];
      }
      
      if (!responseMessage) return { issues: ['No response received'], html: '', text: '' };
      
      const html = responseMessage.innerHTML;
      const text = responseMessage.textContent;
      const issues = [];
      
      // Check for REAL formatting artifacts (not legitimate HTML)
      if (html.includes('**') && !html.includes('</strong>')) issues.push('Unprocessed asterisks found');
      if (html.includes('*>')) issues.push('Asterisk-arrow artifacts found');
      if (html.includes('section-break')) issues.push('Section break artifacts found');
      
      // Only flag problematic bracket patterns, not legitimate HTML
      if (html.match(/>{4,}|<{4,}/)) {
        const matches = html.match(/>{4,}|<{4,}/g);
        issues.push(`Problematic bracket artifacts found: ${matches.join(', ')}`);
      }
      if (html.match(/\*{4,}/)) {
        const matches = html.match(/\*{4,}/g);
        issues.push(`Multiple asterisk artifacts found: ${matches.join(', ')}`);
      }
      
      // Check for unusual patterns
      if (html.includes('\\n')) issues.push('Escaped newlines found');
      if (html.match(/\*\*\*[^*]/)) issues.push('Triple asterisk patterns found');
      
      // Check if it's just the welcome message
      if (text.includes('Welcome to ACIM Guide') && text.length < 400) {
        issues.push('Only welcome message found - no actual AI response yet');
      }
      
      return { issues, html: html.substring(0, 1000), text: text.substring(0, 400) };
    });
    
    console.log('\n📋 Last assistant message (first 800 chars of HTML):');
    console.log(result.html);
    console.log('\n📝 Text content (first 300 chars):');
    console.log(result.text);
    
    const formattingIssues = result.issues;
    
    if (formattingIssues.length === 0) {
      console.log('✅ All formatting tests passed! No artifacts detected.');
      return true;
    } else {
      console.log('⚠️  Formatting issues detected:');
      formattingIssues.forEach(issue => console.log(`   - ${issue}`));
      return false;
    }
    
  } catch (error) {
    console.error('❌ Formatting test failed:', error);
    return false;
  } finally {
    await browser.close();
  }
}

testFormatting().then((success) => {
  console.log(success ? '🎉 Formatting is clean!' : '💥 Formatting needs more work.');
  process.exit(success ? 0 : 1);
});
