// Firebase configuration
// ⚠️ Tạo file .env trong project root với các biến VITE_FIREBASE_*
// Hoặc vào Firebase Console → Project Settings → Web App → Copy config vào đây

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'YOUR_API_KEY',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'YOUR_PROJECT.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'YOUR_PROJECT_ID',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'YOUR_PROJECT.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || 'YOUR_SENDER_ID',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || 'YOUR_APP_ID',
};

let app = null;
let db = null;

try {
  const { initializeApp } = await import('firebase/app');
  const { getFirestore } = await import('firebase/firestore');
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  console.log('✅ Firebase initialized:', firebaseConfig.projectId);
} catch (e) {
  console.warn('⚠️ Firebase init skipped (running without backend):', e.message);
}

export { app, db };
