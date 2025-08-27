# 🚀 Stripe Setup Guide - Start Making Money This Week

## 🎯 Goal: Get your €7 courses selling by Friday

---

## Step 1: Create Your Stripe Account (10 minutes)

### 1.1 Sign Up for Stripe
1. Go to https://stripe.com/
2. Click "Start now" 
3. Sign up with your email
4. **Business Name**: "ACIMguide" or "Alex Monas Coaching"
5. **Country**: Your location
6. **Business Type**: Individual or Company (your choice)

### 1.2 Complete Business Verification  
Stripe will ask for:
- Personal details (name, address)
- Tax information (VAT number if you have one)
- Bank account details for payouts
- Phone verification

**⏰ This takes 5-10 minutes but enables you to receive real money**

---

## Step 2: Get Your API Keys (2 minutes)

### 2.1 Get Test Keys (for development)
1. Log into Stripe Dashboard
2. Click "Developers" in left sidebar
3. Click "API keys"
4. **Copy these keys** (you'll need them):
   - `Publishable key` (starts with `pk_test_`)
   - `Secret key` (starts with `sk_test_`)

### 2.2 Get Live Keys (for real money)
1. Toggle "Test data" to OFF in Stripe dashboard
2. Copy the live keys:
   - `Publishable key` (starts with `pk_live_`)
   - `Secret key` (starts with `sk_live_`)

**🔐 Keep these keys secure! Never commit them to code.**

---

## Step 3: Configure Firebase with Stripe

### 3.1 Set Stripe API Key in Firebase
```bash
cd /home/am/TestAlex

# For testing (start with this)
firebase functions:secrets:set STRIPE_API_KEY

# When prompted, paste your SECRET key (sk_test_xxx or sk_live_xxx)
```

### 3.2 Configure the Stripe Extension
The extension is already installed! Now we need to configure it:

```bash
# Configure the extension parameters  
firebase ext:configure firestore-stripe-payments
```

You'll be prompted to update the API key you entered during installation.

---

## Step 4: Create Your €7 Course Product in Stripe

### 4.1 Create Product in Stripe Dashboard
1. Go to Stripe Dashboard → Products
2. Click "Add product"
3. **Name**: "14-Day ACIM Spiritual Transformation Course"
4. **Description**: "Daily guided prompts for deep spiritual healing and inner peace based on A Course in Miracles"
5. **Price**: €7.00 EUR (one-time payment)
6. **Save product**

### 4.2 Copy Product and Price IDs
After creating the product:
1. Click on your product
2. **Copy the Price ID** (starts with `price_`) - you'll need this for the checkout

---

## Step 5: Create Course Purchase Flow

Let me create the purchase button and checkout code for you:

### 5.1 Frontend Purchase Button
```javascript
// Add this to your ACIMguide frontend
async function purchaseCourse() {
    try {
        // Create checkout session
        const createCheckoutSession = firebase.functions().httpsCallable('ext-firestore-stripe-payments-createCheckoutSession');
        
        const { data } = await createCheckoutSession({
            price: 'price_YOUR_PRICE_ID_HERE', // Replace with your actual price ID
            success_url: `${window.location.origin}/course-access`,
            cancel_url: `${window.location.origin}/pricing`,
            metadata: {
                course: '14-day-acim-transformation'
            }
        });
        
        // Redirect to Stripe Checkout
        window.location = data.url;
        
    } catch (error) {
        console.error('Error creating checkout session:', error);
        alert('Payment error. Please try again.');
    }
}
```

### 5.2 Purchase Button HTML
Add this to your ACIMguide website:

```html
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

<style>
.course-purchase-section {
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    text-align: center;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.price {
    margin: 1rem 0;
}

.amount {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2196F3;
}

.period {
    color: #666;
    margin-left: 0.5rem;
}

.purchase-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 8px;
    cursor: pointer;
    margin: 1rem 0;
    transition: background 0.3s;
}

.purchase-btn:hover {
    background: #1976D2;
}

.guarantee {
    font-size: 0.9rem;
    color: #666;
}
</style>
```

---

## Step 6: Test Your Payment System

### 6.1 Test with Stripe Test Cards
Use these test card numbers:
- **Success**: `4242424242424242`
- **Decline**: `4000000000000002`
- **Requires Auth**: `4000002500003155`

**Use any future date for expiry and any 3-digit CVC**

### 6.2 Test the Complete Flow
1. Click your purchase button
2. Complete checkout with test card
3. Verify customer is created in Firestore
4. Check Stripe dashboard for successful payment

---

## Step 7: Set Up Course Delivery

### 7.1 Create Course Access Page
```html
<!-- /course-access page -->
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to Your ACIM Course!</title>
</head>
<body>
    <h1>🎉 Welcome to Your Transformation Journey!</h1>
    <p>Thank you for purchasing the 14-Day ACIM Course.</p>
    
    <div id="course-content">
        <!-- Course content will load here -->
    </div>
    
    <script>
    // Check if user has purchased course
    firebase.auth().onAuthStateChanged(async (user) => {
        if (user) {
            const customerDoc = await firebase.firestore()
                .collection('customers')
                .doc(user.uid)
                .get();
            
            if (customerDoc.exists && customerDoc.data().hasCourseAccess) {
                loadCourseContent();
            } else {
                showPurchaseRequired();
            }
        }
    });
    
    function loadCourseContent() {
        // Load the 14-day course content
        document.getElementById('course-content').innerHTML = `
            <h2>Day 1: Your Greatest Fear</h2>
            <p>The greatest fear that I want to let go of is ___________.</p>
            <p>Please help me see where I am still mistaken. I want peace instead.</p>
            <button onclick="askCourseGPT()">Get Personalized Guidance</button>
        `;
    }
    </script>
</body>
</html>
```

---

## Step 8: Deploy and Go Live!

### 8.1 Deploy Your Changes
```bash
cd /home/am/TestAlex

# Deploy functions with new Stripe integration
firebase deploy --only functions

# Deploy updated website
firebase deploy --only hosting
```

### 8.2 Switch to Live Mode (When Ready)
1. Update Stripe extension with live API key
2. Update frontend with live price ID
3. Test with small real purchase (€1)
4. Go live! 🚀

---

## 📊 Tracking Your Success

### Revenue Metrics to Watch:
- **Checkout conversion rate**: visitors → purchases
- **Monthly recurring revenue**: €7 × purchases
- **Customer lifetime value**: track repeat customers

### Use Your Business RAG to Track Progress:
```bash
cd /home/am/TestAlex/agentic-rag-system
python business_intelligence_rag.py

# Ask: "How many course sales do I need to reach €1000/month?"
# Answer: 143 courses (€7 × 143 = €1,001)
```

---

## 🚨 Important Security Notes

1. **Never expose secret keys** in frontend code
2. **Use test mode** until you're ready for real payments
3. **Set up webhook verification** for production (we'll do this next week)
4. **Monitor for suspicious activity** in Stripe dashboard

---

## 🎯 Success Milestones

- [ ] **Today**: Stripe account created and verified
- [ ] **Tomorrow**: Test purchase flow working  
- [ ] **This Week**: First real €7 sale
- [ ] **Next Week**: 10+ course sales (€70+ revenue)
- [ ] **Month 1**: 100+ sales (€700+ revenue)

---

## ❓ Need Help?

Your Business Intelligence RAG can help:
```bash
python business_intelligence_rag.py
```

Ask questions like:
- "How do I test Stripe payments?"
- "What should my course content include?"
- "How do I increase conversion rates?"

---

**🚀 Ready to make your first sale? Let's get Stripe configured!**
