const admin = require('firebase-admin');

// Initialize Firebase Admin
const serviceAccount = require('./acim-guide-test-firebase-adminsdk-t27k8-da4e4b5c6e.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: 'acim-guide-test'
});

const db = admin.firestore();

async function setupStripeProduct() {
  try {
    console.log('Creating Stripe product in Firestore...');
    
    // Create the product document
    const productRef = db.collection('products').doc('acim-premium-guide');
    await productRef.set({
      name: 'A Course in Miracles - Premium Guide',
      description: 'Unlock the profound teachings of A Course in Miracles with our comprehensive premium guide. Transform your understanding and experience inner peace through practical insights and exercises.',
      active: true,
      role: 'premium', // Custom claim that will be added to user
      images: ['https://acim-guide-test.web.app/acim-guide-image.jpg'], // Add your product image URL here
      metadata: {
        course_type: 'premium',
        access_duration: 'lifetime'
      },
      tax_code: 'txcd_10000000' // Digital goods tax code
    });

    console.log('Product created successfully!');

    // Create the price document (one-time payment)
    const priceRef = productRef.collection('prices').doc('premium-guide-7eur');
    await priceRef.set({
      active: true,
      currency: 'eur',
      unit_amount: 700, // €7.00 in cents
      type: 'one_time',
      metadata: {
        course: 'acim-premium-guide'
      }
    });

    console.log('Price created successfully!');
    
    // Wait a moment for Stripe sync
    console.log('Waiting for Stripe sync...');
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Read back the created price to get the Stripe price ID
    const priceDoc = await priceRef.get();
    const priceData = priceDoc.data();
    
    if (priceData && priceData.id) {
      console.log(`✅ Stripe Price ID: ${priceData.id}`);
      console.log('Update your payment.html file with this price ID!');
    } else {
      console.log('⏳ Stripe sync is still in progress. Check Firestore in a few minutes for the price ID.');
    }
    
    console.log('\n🎉 Setup complete!');
    console.log('Next steps:');
    console.log('1. Update the price ID in payment.html');
    console.log('2. Deploy your site: firebase deploy');
    console.log('3. Test the payment flow!');
    
  } catch (error) {
    console.error('Error setting up product:', error);
  }
  
  process.exit(0);
}

setupStripeProduct();
