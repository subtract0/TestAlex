#!/usr/bin/env python3
"""
Stripe Setup Helper Script
==========================

This script helps you complete the Stripe integration with your Firebase project.
Run this after you have your Stripe API keys.

Steps this script helps with:
1. Verify Stripe extension is installed
2. Guide you through setting the API key
3. Create a test product for your €7 course
4. Test the integration
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, capture=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
        if capture:
            return result.returncode == 0, result.stdout, result.stderr
        else:
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_firebase_login():
    """Check if user is logged into Firebase"""
    success, stdout, stderr = run_command("firebase whoami")
    if success and "not logged in" not in stdout:
        print(f"✅ Firebase login: {stdout.strip()}")
        return True
    else:
        print("❌ Not logged into Firebase. Run: firebase login")
        return False

def check_stripe_extension():
    """Check if Stripe extension is installed"""
    success, stdout, stderr = run_command("firebase ext:list")
    if success and "firestore-stripe-payments" in stdout:
        print("✅ Stripe extension is installed")
        return True
    else:
        print("❌ Stripe extension not found. Installing...")
        install_extension()
        return True

def install_extension():
    """Install the Stripe extension if not present"""
    print("Installing Stripe extension...")
    cmd = "firebase ext:install stripe/firestore-stripe-payments --non-interactive"
    success, stdout, stderr = run_command(cmd, capture=False)
    if success:
        print("✅ Stripe extension installed successfully")
    else:
        print("❌ Failed to install Stripe extension")
        print("Run manually: firebase ext:install stripe/firestore-stripe-payments")

def setup_stripe_api_key():
    """Guide user through setting up Stripe API key"""
    print("\n🔑 Setting up Stripe API Key")
    print("=" * 40)
    
    print("1. Go to https://stripe.com/")
    print("2. Sign up/Login to your account")
    print("3. Go to Developers → API Keys")
    print("4. Copy your SECRET key (starts with sk_test_ or sk_live_)")
    print("5. Keep it ready - we'll set it as a Firebase secret")
    
    input("\nPress Enter when you have your Stripe SECRET key ready...")
    
    print("\nNow let's set it in Firebase:")
    print("Run this command and paste your SECRET key when prompted:")
    print("firebase functions:secrets:set ext-firestore-stripe-payments-STRIPE_API_KEY")
    
    proceed = input("\nDid you run the command above? (y/n): ").lower().strip()
    if proceed == 'y':
        print("✅ Great! API key should be set")
        return True
    else:
        print("⏸️  Please run that command, then re-run this script")
        return False

def create_course_product_guide():
    """Guide user through creating the €7 course product"""
    print("\n💰 Creating Your €7 Course Product")
    print("=" * 40)
    
    print("1. Go to your Stripe Dashboard")
    print("2. Click 'Products' in the left sidebar")
    print("3. Click 'Add product'")
    print("4. Fill in these details:")
    print("   - Name: '14-Day ACIM Spiritual Transformation Course'")
    print("   - Description: 'Daily guided prompts for deep spiritual healing'")
    print("   - Price: €7.00 EUR (one-time payment)")
    print("5. Save the product")
    print("6. Copy the PRICE ID (starts with 'price_')")
    
    price_id = input("\nEnter your Price ID (price_xxxxx): ").strip()
    
    if price_id.startswith('price_'):
        print(f"✅ Price ID saved: {price_id}")
        
        # Save price ID to a config file
        config_file = Path(__file__).parent / "stripe_config.txt"
        with open(config_file, 'w') as f:
            f.write(f"COURSE_PRICE_ID={price_id}\n")
        
        return price_id
    else:
        print("❌ Invalid price ID format. It should start with 'price_'")
        return None

def create_purchase_button_code(price_id):
    """Generate the purchase button code"""
    print("\n🛒 Creating Purchase Button Code")
    print("=" * 40)
    
    button_code = f'''
<!-- Add this to your ACIMguide website -->
<div class="course-purchase-section">
    <h3>🌟 14-Day ACIM Transformation Course</h3>
    <p>Daily guided spiritual prompts for deep healing and inner peace</p>
    
    <div class="price">
        <span class="amount">€7</span>
        <span class="period">one-time</span>
    </div>
    
    <button onclick="purchaseCourse()" class="purchase-btn">
        Start Your Transformation ✨
    </button>
    
    <p class="guarantee">💰 30-day money-back guarantee</p>
</div>

<script>
async function purchaseCourse() {{
    try {{
        // Create checkout session
        const createCheckoutSession = firebase.functions().httpsCallable('ext-firestore-stripe-payments-createCheckoutSession');
        
        const {{ data }} = await createCheckoutSession({{
            price: '{price_id}',
            success_url: window.location.origin + '/course-access',
            cancel_url: window.location.origin + '/pricing',
            metadata: {{
                course: '14-day-acim-transformation'
            }}
        }});
        
        // Redirect to Stripe Checkout
        window.location = data.url;
        
    }} catch (error) {{
        console.error('Error creating checkout session:', error);
        alert('Payment error. Please try again.');
    }}
}}
</script>

<style>
.course-purchase-section {{
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    text-align: center;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}}

.price {{ margin: 1rem 0; }}
.amount {{ font-size: 2.5rem; font-weight: bold; color: #2196F3; }}
.period {{ color: #666; margin-left: 0.5rem; }}

.purchase-btn {{
    background: #2196F3;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 8px;
    cursor: pointer;
    margin: 1rem 0;
    transition: background 0.3s;
}}

.purchase-btn:hover {{ background: #1976D2; }}
.guarantee {{ font-size: 0.9rem; color: #666; }}
</style>
'''
    
    # Save to file
    button_file = Path(__file__).parent / "purchase_button.html"
    with open(button_file, 'w') as f:
        f.write(button_code)
    
    print(f"✅ Purchase button code saved to: {button_file}")
    print("📋 Copy this code into your ACIMguide website!")

def deploy_changes():
    """Deploy the changes to Firebase"""
    print("\n🚀 Deploying Changes")
    print("=" * 25)
    
    print("Deploy your Firebase functions and hosting:")
    print("firebase deploy")
    
    deploy = input("\nDeploy now? (y/n): ").lower().strip()
    if deploy == 'y':
        print("Deploying...")
        success, stdout, stderr = run_command("firebase deploy", capture=False)
        if success:
            print("✅ Deployment successful!")
        else:
            print("❌ Deployment failed. Check the errors above.")
    else:
        print("⏸️  Remember to deploy when you're ready: firebase deploy")

def test_stripe_integration():
    """Guide user through testing the integration"""
    print("\n🧪 Testing Your Stripe Integration")
    print("=" * 35)
    
    print("Test cards to use:")
    print("✅ Success: 4242424242424242")
    print("❌ Decline: 4000000000000002") 
    print("🔐 Requires Auth: 4000002500003155")
    print("(Use any future date for expiry and any 3-digit CVC)")
    
    print("\nTest process:")
    print("1. Go to your website with the purchase button")
    print("2. Click 'Start Your Transformation'")
    print("3. Complete checkout with a test card")
    print("4. Check Stripe Dashboard for the payment")
    print("5. Check Firebase Console → Firestore → customers")

def main():
    """Main setup function"""
    print("🚀 Stripe Setup Helper for ACIMguide")
    print("=" * 40)
    
    # Check prerequisites
    if not check_firebase_login():
        return
    
    if not check_stripe_extension():
        return
    
    # Setup API key
    if not setup_stripe_api_key():
        return
    
    # Create product
    price_id = create_course_product_guide()
    if not price_id:
        print("⏸️  Complete the product creation, then re-run this script")
        return
    
    # Generate purchase button code
    create_purchase_button_code(price_id)
    
    # Deploy
    deploy_changes()
    
    # Test
    test_stripe_integration()
    
    print("\n🎉 Stripe Setup Complete!")
    print("=" * 30)
    print("Next steps:")
    print("1. Add purchase button to your website")
    print("2. Test with Stripe test cards")
    print("3. Switch to live mode when ready")
    print("4. Start selling courses! 💰")
    
    print("\n🤖 Use your Business RAG for ongoing help:")
    print("python /home/am/TestAlex/agentic-rag-system/business_intelligence_rag.py")

if __name__ == "__main__":
    main()
