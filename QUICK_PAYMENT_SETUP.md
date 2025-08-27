# 🚀 Quick Payment Setup - Get €7 Sales Working in 20 Minutes

## ✅ What You Can Test RIGHT NOW:

**Your test page is live:** https://acim-guide-test.web.app/test-payment.html

Go there now and click the test buttons to see what the payment flow will look like!

---

## 🔧 To Make Real Payments Work (20 minutes):

### Step 1: Get Your Stripe Keys (5 minutes)
1. Go to **https://stripe.com/** (if you haven't signed up)
2. **Developers** → **API Keys**  
3. Copy both keys:
   - **Publishable key** (pk_test_xxx)
   - **Secret key** (sk_test_xxx)

### Step 2: Install Stripe Extension (5 minutes)
```bash
cd /home/am/TestAlex
firebase ext:install stripe/firestore-stripe-payments
```

**When prompted:**
- **Products collection:** `products`
- **Customers collection:** `customers`  
- **Stripe API key:** *paste your SECRET key (sk_test_xxx)*
- **Sync users:** `Sync`
- All other settings: use defaults

### Step 3: Create €7 Course Product (5 minutes)
1. **Stripe Dashboard** → **Products** → **Add product**
2. **Name:** `14-Day ACIM Transformation Course`
3. **Price:** `€7.00 EUR` (one-time)
4. **Save** → Copy the **Price ID** (price_xxxxx)

### Step 4: Add Purchase Button (3 minutes)
Add this to your `public/index.html` (after the quick-actions div):

```html
<!-- Course Purchase Section -->
<div class="course-premium-section" id="coursePremiumSection">
    <h3>🌟 14-Day ACIM Transformation Course</h3>
    <p>Daily guided spiritual prompts for deep healing</p>
    <div class="price">€7 <span>one-time</span></div>
    <button onclick="purchaseACIMCourse()" class="purchase-btn">
        Start Your Journey ✨
    </button>
</div>

<script>
async function purchaseACIMCourse() {
    try {
        const createCheckoutSession = firebase.functions().httpsCallable('ext-firestore-stripe-payments-createCheckoutSession');
        
        const {data} = await createCheckoutSession({
            price: 'price_YOUR_PRICE_ID_HERE', // Replace with your actual price ID
            success_url: window.location.origin + '/success',
            cancel_url: window.location.origin
        });
        
        window.location.href = data.url;
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
</script>

<style>
.course-premium-section {
    background: #f0f8ff;
    border: 2px solid #2196F3;
    border-radius: 12px;
    padding: 2rem;
    margin: 2rem;
    text-align: center;
}
.price { font-size: 2rem; color: #2196F3; margin: 1rem 0; }
.purchase-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 8px;
    cursor: pointer;
}
</style>
```

### Step 5: Deploy & Test (2 minutes)
```bash
firebase deploy
```

Then test with card: **4242424242424242** (any expiry/CVC)

---

## 🧪 How To Test:

1. **Go to your live site:** https://acim-guide-test.web.app
2. **Click the purchase button**
3. **Use test card:** 4242424242424242
4. **Any expiry date:** 12/25
5. **Any CVC:** 123

**What should happen:**
✅ Redirects to Stripe checkout  
✅ Test payment processes  
✅ Customer created in Firebase  
✅ Success page shows  

---

## 🎯 Once Working:

**Switch to Live Mode:**
1. Get live Stripe keys (pk_live_xxx, sk_live_xxx)
2. Update Firebase extension with live key
3. Update website with live price ID
4. **Start making real money!** 💰

---

## 🚀 Your Revenue Path:

**Goal:** €10,000/month  
**Course Price:** €7  
**Sales Needed:** 1,429/month (≈ 48/day)

**Week 1:** 1 sale (prove it works)  
**Month 1:** 143 sales (€1,000/month)  
**Month 6:** 1,429 sales (€10,000/month) 🎉

---

## ❓ Need Help?

**Ask your Business RAG:**
```bash
cd /home/am/TestAlex/agentic-rag-system
python business_intelligence_rag.py
```

**Questions to ask:**
- "Help me complete Stripe setup"
- "How do I test payments?"
- "What should I do after my first sale?"

---

**Ready to make your first €7 sale? Let's go! 🚀**
