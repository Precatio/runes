// Firebase is loaded when it is needed, not with every page: the SDK is about 640 kB, and most visits (the start page,
// the blog, Rundata, the map and the statistics) do not need it at once. Auth is loaded after the page has rendered, to
// know whether someone is signed in (components/AuthContext.tsx); Firestore only when a signed-in user's data is read or
// written (lib/db.ts, lib/corpus.ts, SettingsContext, Messages).
import type { Auth, GoogleAuthProvider, User } from "firebase/auth";
import type { Firestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSy_dummy",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "vitki-ai.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "vitki-ai",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "vitki-ai.firebasestorage.app",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "123456789",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:123:web:456",
};

// Initialize Firebase only once (important for Next.js, which may evaluate the module again)
async function app() {
  const { initializeApp, getApps, getApp } = await import("firebase/app");
  return getApps().length ? getApp() : initializeApp(firebaseConfig);
}

type AuthLib = typeof import("firebase/auth");
let authLoading: Promise<{ auth: Auth; googleProvider: GoogleAuthProvider; lib: AuthLib }> | null = null;

/** Firebase Auth, the Google provider and the auth functions (signInWithPopup, onAuthStateChanged …). */
export function firebaseAuth() {
  authLoading ??= (async () => {
    const [a, lib] = await Promise.all([app(), import("firebase/auth")]);
    const googleProvider = new lib.GoogleAuthProvider();
    googleProvider.addScope("https://www.googleapis.com/auth/drive.file");
    return { auth: lib.getAuth(a), googleProvider, lib };
  })();
  return authLoading;
}

/** The signed-in user once Firebase has restored the session, or null when nobody is signed in. */
export async function currentUser(): Promise<User | null> {
  const { auth } = await firebaseAuth();
  await auth.authStateReady();
  return auth.currentUser;
}

type FirestoreLib = typeof import("firebase/firestore");
let firestoreLoading: Promise<FirestoreLib & { db: Firestore }> | null = null;

/** The Firestore functions (doc, getDocs, setDoc …) and the app's database ("vitki"). */
export function firestoreLib() {
  firestoreLoading ??= (async () => {
    const [a, lib] = await Promise.all([app(), import("firebase/firestore")]);
    return { ...lib, db: lib.getFirestore(a, "vitki") };
  })();
  return firestoreLoading;
}
