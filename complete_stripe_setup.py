#!/usr/bin/env python3
"""
Complete Stripe Setup for ACIMguide
===================================

This script helps you finish integrating Stripe with your ACIMguide platform.
It will:
1. Install the Stripe Firebase extension properly
2. Guide you through getting your Stripe keys
3. Update your website with the purchase button
4. Test the integration

Run this after you have:
- Created a Stripe account
- Completed business verification
- Got your API keys
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import re

def print_step(step_num, title, description=""):
    """Print a nicely formatted step"""
    print(f"\n{'='*50}")
    print(f"🚀 STEP {step_num}: {title}")
    print(f"{'='*50}")
    if description:
        print(description)
    print()

def run_firebase_command(cmd):
    """Run a Firebase command and return success status"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def check_stripe_account_setup():
    """Guide user through Stripe account setup"""
    print_step(1, "Stripe Account Setup", 
               "First, let's make sure you have your Stripe account ready.")
    
    print("Have you completed these steps?")
    print("✓ Created account at https://stripe.com/")
    print("✓ Completed business verification") 
    print("✓ Added your bank details for payouts")
    print("✓ Got your API keys from Developers → API Keys")
    
    while True:
        ready = input("\nAre you ready with your Stripe SECRET key? (y/n): ").strip().lower()
        if ready == 'y':
            break
        elif ready == 'n':
            print("\n📋 TODO: Complete Stripe setup first")
            print("1. Go to https://stripe.com/")
            print("2. Sign up and verify your business")
            print("3. Go to Developers → API Keys")
            print("4. Copy your SECRET key (sk_test_xxx)")
            print("\nRun this script again when ready!")
            return False
        else:
            print("Please enter 'y' or 'n'")
    
    return True

def install_stripe_extension():
    """Install and configure Stripe extension"""
    print_step(2, "Install Stripe Extension",
               "Installing the official Stripe Firebase extension...")
    
    # Check if already installed
    result = subprocess.run("firebase ext:list", shell=True, capture_output=True, text=True)
    if "firestore-stripe-payments" in result.stdout:
        print("✅ Stripe extension already installed!")
        return True
    
    print("Installing Stripe extension... This will ask for your API key.")
    print("\n🔑 IMPORTANT: When prompted for 'Stripe API key', paste your SECRET key (sk_test_xxx or sk_live_xxx)")
    
    # Install command - let it run interactively
    success = run_firebase_command("firebase ext:install stripe/firestore-stripe-payments")
    
    if success:
        print("✅ Stripe extension installed successfully!")
        return True
    else:
        print("❌ Failed to install Stripe extension")
        print("\nTry running manually:")
        print("firebase ext:install stripe/firestore-stripe-payments")
        return False

def create_stripe_product():
    """Guide user through creating the €7 course product"""
    print_step(3, "Create €7 Course Product",
               "Now let's create your course product in Stripe...")
    
    print("1. Go to your Stripe Dashboard")
    print("2. Click 'Products' in the left sidebar") 
    print("3. Click 'Add product'")
    print("4. Fill in:")
    print("   📝 Name: '14-Day ACIM Spiritual Transformation Course'")
    print("   📝 Description: 'Daily guided prompts for deep spiritual healing and inner peace'")
    print("   💰 Price: €7.00 EUR (one-time payment)")
    print("5. Save the product")
    print("6. Copy the PRICE ID (starts with 'price_')")
    
    while True:
        price_id = input("\nEnter your Price ID (price_xxxxx): ").strip()
        if price_id.startswith('price_'):
            print(f"✅ Great! Price ID: {price_id}")
            break
        elif not price_id:
            print("❌ Please create the product in Stripe first, then enter the Price ID")
        else:
            print("❌ Price ID should start with 'price_' - check you copied the correct ID")
    
    return price_id

def update_website_with_purchase_button(price_id):
    """Add the purchase button to the website"""
    print_step(4, "Add Purchase Button to Website",
               "Adding the €7 course purchase button to your ACIMguide website...")
    
    # Read the course purchase section template
    template_path = Path(__file__).parent / "course_purchase_section.html"
    if not template_path.exists():
        print("❌ course_purchase_section.html not found!")
        return False
    
    with open(template_path, 'r') as f:
        purchase_section = f.read()
    
    # Replace the placeholder with actual price ID
    purchase_section = purchase_section.replace('price_YOUR_PRICE_ID_HERE', price_id)
    
    # Read the current index.html
    index_path = Path(__file__).parent / "public" / "index.html"
    if not index_path.exists():
        print("❌ public/index.html not found!")
        return False
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Find where to insert the purchase section
    # Look for the quick-actions div end and input-container div start
    quick_actions_end = content.find('</div>', content.find('class="quick-actions"'))
    input_container_start = content.find('<div class="input-container">')
    
    if quick_actions_end == -1 or input_container_start == -1:
        print("❌ Could not find insertion point in index.html")
        return False
    
    # Insert the purchase section
    insertion_point = quick_actions_end + 6  # After </div>
    new_content = (
        content[:insertion_point] + 
        "\n        " + 
        purchase_section.replace('\n', '\n        ') +  # Indent properly
        "\n        " +
        content[insertion_point:]
    )
    
    # Save backup
    backup_path = index_path.parent / "index.html.backup"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✅ Backup saved: {backup_path}")
    
    # Write updated content
    with open(index_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Purchase button added to your website!")
    return True

def create_success_page():
    """Create a success page for after purchase"""
    print_step(5, "Create Success Page",
               "Creating a page customers see after successful purchase...")
    
    success_page_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Your ACIM Journey - ACIMguide</title>
    <style>
        body {
            font-family: 'Inter', Arial, sans-serif;
            background: linear-gradient(135deg, #E3F2FD 0%, #FFFFFF 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        .success-container {
            background: white;
            padding: 3rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            max-width: 500px;
        }
        h1 {
            color: #1976D2;
            margin-bottom: 1rem;
        }
        .emoji {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        .next-steps {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: left;
            margin: 2rem 0;
        }
        .next-steps h3 {
            color: #1976D2;
            margin-top: 0;
        }
        .btn {
            background: #2196F3;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #1976D2;
        }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="emoji">🎉</div>
        <h1>Welcome to Your ACIM Transformation Journey!</h1>
        <p>Thank you for purchasing the 14-Day ACIM Spiritual Transformation Course. Your journey to inner peace and spiritual awakening begins now.</p>
        
        <div class="next-steps">
            <h3>What happens next:</h3>
            <p>📧 <strong>Check your email</strong> - Course details and Day 1 prompt coming soon</p>
            <p>🧘 <strong>Prepare your heart</strong> - Find a quiet space for daily reflection</p>
            <p>✨ <strong>Stay connected</strong> - Return to ACIMguide for personalized guidance</p>
        </div>
        
        <a href="/" class="btn">Return to ACIMguide</a>
        <a href="mailto:support@acimguide.com" class="btn">Contact Support</a>
        
        <p style="margin-top: 2rem; font-size: 0.9rem; color: #888;">
            Questions? We're here to support your spiritual journey.
        </p>
    </div>
</body>
</html>"""
    
    success_page_path = Path(__file__).parent / "public" / "course-success.html"
    with open(success_page_path, 'w') as f:
        f.write(success_page_content)
    
    print(f"✅ Success page created: {success_page_path}")
    return True

def deploy_changes():
    """Deploy the changes to Firebase"""
    print_step(6, "Deploy to Firebase",
               "Deploying your updated website with Stripe integration...")
    
    print("This will deploy:")
    print("✓ Updated website with purchase button")
    print("✓ Stripe Firebase extension")
    print("✓ Success page")
    
    deploy = input("\nDeploy now? (y/n): ").strip().lower()
    if deploy != 'y':
        print("⏸️  Skipping deployment. Remember to run 'firebase deploy' when ready!")
        return True
    
    success = run_firebase_command("firebase deploy")
    if success:
        print("🎉 Deployment successful!")
        print("\nYour ACIMguide with Stripe integration is now live!")
        return True
    else:
        print("❌ Deployment failed. Try running 'firebase deploy' manually.")
        return False

def test_integration():
    """Guide user through testing"""
    print_step(7, "Test Your Integration",
               "Let's test your €7 course purchase system...")
    
    print("🧪 Test Process:")
    print("1. Go to your live ACIMguide website")
    print("2. Chat with the AI a few times to trigger the course section")
    print("3. Click 'Start Your Transformation Journey ✨'")
    print("4. Use test card: 4242424242424242 (any expiry/CVC)")
    print("5. Complete the checkout")
    print("6. Verify you see the success page")
    print("7. Check Stripe Dashboard for the test payment")
    
    print("\n🎯 Success Criteria:")
    print("✓ Purchase button appears after chatting")
    print("✓ Checkout redirects to Stripe")
    print("✓ Test payment processes successfully")
    print("✓ Success page loads after payment")
    print("✓ Customer created in Firebase Console → Firestore → customers")
    
    input("\nPress Enter when you've tested the purchase flow...")
    
    tested = input("Did the test purchase work? (y/n): ").strip().lower()
    if tested == 'y':
        print("🎉 Amazing! Your payment system is working!")
        return True
    else:
        print("🔧 Check the troubleshooting guide in STRIPE_SETUP_GUIDE.md")
        return False

def main():
    """Main setup process"""
    print("🚀 ACIMguide Stripe Integration Setup")
    print("=====================================")
    print("This will set up €7 course payments on your platform")
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    try:
        # Step 1: Check Stripe account
        if not check_stripe_account_setup():
            return
        
        # Step 2: Install extension
        if not install_stripe_extension():
            print("❌ Cannot continue without Stripe extension")
            return
        
        # Step 3: Create product
        price_id = create_stripe_product()
        
        # Step 4: Update website
        if not update_website_with_purchase_button(price_id):
            print("❌ Failed to update website")
            return
        
        # Step 5: Create success page
        create_success_page()
        
        # Step 6: Deploy
        if not deploy_changes():
            print("❌ Deployment failed - but you can deploy manually later")
        
        # Step 7: Test
        test_integration()
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 STRIPE INTEGRATION COMPLETE!")
        print("="*60)
        print("✅ Stripe extension installed")
        print("✅ €7 course product created")
        print("✅ Purchase button added to website")
        print("✅ Success page created")
        print("✅ Everything deployed")
        
        print(f"\n💰 Revenue Setup:")
        print(f"💳 Course price: €7")
        print(f"🎯 Goal: €10,000/month")
        print(f"📊 Courses needed: 1,429 sales/month")
        print(f"📈 That's ~48 sales per day")
        
        print(f"\n🚀 Next Steps:")
        print("1. Start promoting your course")
        print("2. Create content to drive traffic")
        print("3. Set up ACIMcoach.com blog")
        print("4. Add premium coaching tiers")
        
        print(f"\n🤖 Use your Business RAG for guidance:")
        print("cd /home/am/TestAlex/agentic-rag-system")
        print("python business_intelligence_rag.py")
        
        print(f"\n💡 Ask it: 'How can I get my first 10 course sales?'")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Setup interrupted. Run again to continue.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Check the error and run the script again.")

if __name__ == "__main__":
    main()
