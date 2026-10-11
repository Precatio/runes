"use client";

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";
import { onAuthStateChanged, User, signInWithPopup, signOut, GoogleAuthProvider } from "firebase/auth";
import { auth, googleProvider } from "@/firebase/config";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [googleToken, setGoogleToken] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [accountNotice, setAccountNotice] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
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
      // Attempt to load token from localStorage if user is logged in
      if (currentUser) {
        const savedToken = localStorage.getItem('google_oauth_token');
        if (savedToken) setGoogleToken(savedToken);
      } else {
        setGoogleToken(null);
        localStorage.removeItem('google_oauth_token');
      }
    });

    return () => unsubscribe();
  }, []);

  const loginWithGoogle = async () => {
    try {
      setAccountNotice(null);
      const result = await signInWithPopup(auth, googleProvider);
      const credential = GoogleAuthProvider.credentialFromResult(result);
      if (credential?.accessToken) {
        setGoogleToken(credential.accessToken);
        localStorage.setItem('google_oauth_token', credential.accessToken);
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
    const token = await auth.currentUser?.getIdToken().catch(() => null);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, []);

  const logout = async () => {
    try {
      await signOut(auth);
      setGoogleToken(null);
      localStorage.removeItem('google_oauth_token');
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
