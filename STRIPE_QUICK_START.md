# 🚀 Stripe Quick Start Guide

## Your Immediate Next Steps (30 minutes to revenue)

### Step 1: Set Up Stripe Account (10 minutes)
1. **Go to**: https://stripe.com/
2. **Sign up** with your email 
3. **Business details**: "ACIMguide" or your name
4. **Complete verification** (bank details, address, etc.)

### Step 2: Get Your API Keys (2 minutes)  
1. **Stripe Dashboard** → **Developers** → **API Keys**
2. **Copy both keys**:
   - `Publishable key` (pk_test_xxx) 
   - `Secret key` (sk_test_xxx)

### Step 3: Install Stripe Extension (5 minutes)
```bash
cd /home/am/TestAlex

# Install the extension
firebase ext:install stripe/firestore-stripe-payments

# When prompted for API key, paste your SECRET key (sk_test_xxx)
```

**Extension Settings:**
- Products collection: `products`  
- Customers collection: `customers`
- Sync new users: `Sync`
- Auto delete: `Do not delete`

### Step 4: Create €7 Course Product (5 minutes)
1. **Stripe Dashboard** → **Products** → **Add product**
2. **Name**: "14-Day ACIM Transformation Course"
3. **Price**: €7.00 EUR (one-time)
4. **Save** and copy the **Price ID** (price_xxxxx)

### Step 5: Add Purchase Button (8 minutes)

**Add this to your ACIMguide website:**

```html
<div class="course-purchase">
    <h3>🌟 Start Your 14-Day ACIM Journey</h3>
    <p>Daily spiritual prompts for deep transformation</p>
    
    <div class="price">€7 <span>one-time</span></div>
    
    <button onclick="buyCourse()" class="buy-btn">
        Start Transformation ✨
    </button>
</div>

<script>
async function buyCourse() {
    try {
        const createCheckout = firebase.functions().httpsCallable('ext-firestore-stripe-payments-createCheckoutSession');
        
        const {data} = await createCheckout({
            price: 'price_YOUR_PRICE_ID_HERE', // Replace with your actual price ID
            success_url: window.location.origin + '/success',
            cancel_url: window.location.origin
        });
        
        window.location = data.url;
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
</script>

<style>
.course-purchase {
    max-width: 300px;
    margin: 2rem auto;
    padding: 2rem;
    border: 2px solid #ddd;
    border-radius: 10px;
    text-align: center;
}
.price { font-size: 2rem; color: #2196F3; margin: 1rem 0; }
.price span { font-size: 1rem; color: #666; }
.buy-btn {
    background: #2196F3;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 5px;
    cursor: pointer;
}
</style>
```

### Step 6: Test Everything (5 minutes)

**Test card**: `4242424242424242` (any expiry/CVC)

1. Click your purchase button
2. Complete checkout with test card
3. Check Stripe dashboard for payment
4. Check Firebase Console → Firestore → customers

---

## 🎉 That's It! You're Ready to Make Money

**What happens now:**
1. **Real customers** can buy your €7 course
2. **Money goes** to your bank account (via Stripe)
3. **Customer data** saved in Firebase automatically
4. **You deliver** the 14-day course content

**To go LIVE:**
1. Get your **live** Stripe keys (pk_live_xxx, sk_live_xxx)  
2. Update the Firebase extension with live API key
3. Update your website with live price ID
4. Start selling! 🚀

---

## 💰 Revenue Calculation

**Your Goal**: €10,000/month  
**Course Price**: €7  
**Courses Needed**: 1,429 sales/month (≈ 48 sales/day)

**Milestones:**
- **Week 1**: 1 sale (prove it works)
- **Week 2**: 10 sales (€70)  
- **Month 1**: 100 sales (€700)
- **Month 3**: 500 sales (€3,500)
- **Month 6**: 1,429 sales (€10,000/month) ✅

---

**🤖 Questions? Ask your Business RAG:**
```bash
cd /home/am/TestAlex/agentic-rag-system
python business_intelligence_rag.py
```
