import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';

// Your Firebase config
const firebaseConfig = {
  apiKey: 'AIzaSyDc7XKEwrXn7W74tv9dEMH311ETEPh_trA',
  authDomain: 'acim-guide-production.firebaseapp.com',
  projectId: 'acim-guide-production',
  storageBucket: 'acim-guide-production.firebasestorage.app',
  messagingSenderId: '1002911619347',
  appId: '1:1002911619347:web:d497f100e932d40639a2e6'
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const firestore = getFirestore(app);
export const functions = getFunctions(app, 'europe-west3'); // Match your region

export default app;
