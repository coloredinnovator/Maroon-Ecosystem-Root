// ---------------------------------------------------------------------------
// Maroon Technologies — Firebase Zero-Trust Configuration
// ---------------------------------------------------------------------------
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getAuth, connectAuthEmulator } from "firebase/auth";

// If the founder has provided standard credentials via env, use them.
// Otherwise, we fallback to a local emulator suite for sovereign, offline development.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "demo-api-key",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "demo-project.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "demo-project",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "demo-project.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "000000000000",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:000000000000:web:0000000000000000000000"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);

// Connect to emulators if we are in sovereign dev mode
if (import.meta.env.DEV && !import.meta.env.VITE_FIREBASE_PROJECT_ID) {
    console.log("🔥 [Maroon Firebase] Connecting to Sovereign Local Emulators.");
    try {
      connectFirestoreEmulator(db, 'localhost', 8080);
      connectAuthEmulator(auth, 'http://localhost:9099');
    } catch(e) {
      console.warn("Emulators already initialized or failed.", e);
    }
}
