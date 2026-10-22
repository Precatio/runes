"use client";

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import type { User } from "firebase/auth";
import { firebaseAuth } from "@/firebase/config";
import { PUBLIC_SITE } from "@/lib/site";
import { API_URL } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  googleToken: string | null;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  // The app's founder (set on the server with ADMIN_UIDS / ADMIN_EMAILS, never in the code)
  isAdmin: boolean;
  // Authorization header with the Firebase ID token, for calls the server checks (admin, founder-only reports)
  authHeaders: () => Promise<Record<string, string>>;
  // Set when the account has been suspended
  accountNotice: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// The Google access token (drive.file scope, for the Drive export) lives only for this tab's session, not in
// localStorage where it would outlive the visit; without it the export asks the user to sign in with Google again
const GOOGLE_TOKEN_KEY = 'google_oauth_token';
const readGoogleToken = (): string | null => {
  try { return sessionStorage.getItem(GOOGLE_TOKEN_KEY); } catch { return null; }
};
const storeGoogleToken = (token: string | null) => {
  try {
    if (token) sessionStorage.setItem(GOOGLE_TOKEN_KEY, token);
    else sessionStorage.removeItem(GOOGLE_TOKEN_KEY);
  } catch { /* storage blocked: the token stays in memory only */ }
  // Earlier versions kept the token in localStorage; never leave a copy there
  try { localStorage.removeItem(GOOGLE_TOKEN_KEY); } catch { /* ignore */ }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  // The public website (only the start page and the articles) has no sign-in, so Firebase is not loaded there
  const [loading, setLoading] = useState(!PUBLIC_SITE);
  const [googleToken, setGoogleToken] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [accountNotice, setAccountNotice] = useState<string | null>(null);

  useEffect(() => {
    if (PUBLIC_SITE) return;
    // Firebase Auth is loaded after the page has rendered (firebase/config.ts)
    let unsubscribe = () => {};
    let cancelled = false;
    firebaseAuth().then(({ auth, lib: { onAuthStateChanged, signOut } }) => {
      if (cancelled) return;
      unsubscribe = onAuthStateChanged(auth, (currentUser) => {
        setUser(currentUser);
        setLoading(false);
        setIsAdmin(false);
        if (currentUser) {
          // Ask the server for the account's role; a suspended account is signed out
          currentUser.getIdToken().then(token => fetch(`${API_URL}/api/me`, { headers: { Authorization: `Bearer ${token}` } }))
            .then(async r => {
              if (r.status === 403) {
                setAccountNotice((await r.json().catch(() => null))?.detail ?? "Kontot är avstängt.");
                await signOut(auth);
                return;
              }
              if (r.ok) setIsAdmin(!!(await r.json()).admin);
            })
            .catch(() => {});
        }
        // Restore this session's Google token if the user is signed in
        if (currentUser) {
          const savedToken = readGoogleToken();
          if (savedToken) setGoogleToken(savedToken);
          try { localStorage.removeItem(GOOGLE_TOKEN_KEY); } catch { /* ignore */ }
        } else {
          setGoogleToken(null);
          storeGoogleToken(null);
        }
      });
    }).catch(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; unsubscribe(); };
  }, []);

  const loginWithGoogle = async () => {
    try {
      setAccountNotice(null);
      const { auth, googleProvider, lib: { signInWithPopup, GoogleAuthProvider } } = await firebaseAuth();
      const result = await signInWithPopup(auth, googleProvider);
      const credential = GoogleAuthProvider.credentialFromResult(result);
      if (credential?.accessToken) {
        setGoogleToken(credential.accessToken);
        storeGoogleToken(credential.accessToken);
      }
    } catch (error) {
      if ((error as { code?: string })?.code === "auth/user-disabled") {
        setAccountNotice("Kontot är avstängt. Kontakta appens grundare om du tror att det är fel.");
        return;
      }
      console.error("Failed to login with Google:", error);
      throw error;
    }
  };

  const authHeaders = useCallback(async (): Promise<Record<string, string>> => {
    const { auth } = await firebaseAuth();
    const token = await auth.currentUser?.getIdToken().catch(() => null);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const logout = async () => {
    try {
      const { auth, lib: { signOut } } = await firebaseAuth();
      await signOut(auth);
      setGoogleToken(null);
      storeGoogleToken(null);
    } catch (error) {
      console.error("Failed to logout:", error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, googleToken, loginWithGoogle, logout, isAdmin, authHeaders, accountNotice }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
