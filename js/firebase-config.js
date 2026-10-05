/**
 * BCComputers First-Reply Website — Firebase Configuration
 * Firebase JS SDK v10.12.2 (loaded as ES modules)
 * 
 * Replace the placeholder values below with your Firebase Web App configuration from:
 * https://console.firebase.google.com/ -> Project Settings -> General -> Your apps -> Web app
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

// Active Firebase Web App configuration for bccomputers-firstreply
export const firebaseConfig = {
  apiKey: "AIzaSyC2GT6L7xuZvZCSU-WKhS5kePPIarsKxvQ",
  authDomain: "bccomputers-firstreply.firebaseapp.com",
  projectId: "bccomputers-firstreply",
  storageBucket: "bccomputers-firstreply.firebasestorage.app",
  messagingSenderId: "664625813938",
  appId: "1:664625813938:web:1693ca617c6ea107142cab"
};

// Check if Firebase credentials have been configured
export const isFirebaseConfigured = () => {
  return (
    firebaseConfig.apiKey &&
    firebaseConfig.apiKey !== "YOUR_FIREBASE_API_KEY" &&
    firebaseConfig.projectId &&
    firebaseConfig.projectId !== "YOUR_PROJECT_ID"
  );
};

let app = null;
let db = null;

if (isFirebaseConfigured()) {
  try {
    app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    console.log("Firebase & Firestore initialised successfully.");
  } catch (error) {
    console.warn("Firebase initialisation error:", error);
  }
} else {
  console.info("Firebase running in demo mode (using placeholder config). Submissions will provide graceful WhatsApp fallback.");
}

export { app, db };
