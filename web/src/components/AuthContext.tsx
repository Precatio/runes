"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { onAuthStateChanged, User, signInWithPopup, signOut, GoogleAuthProvider } from "firebase/auth";
import { auth, googleProvider } from "@/firebase/config";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  googleToken: string | null;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [googleToken, setGoogleToken] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
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
      const result = await signInWithPopup(auth, googleProvider);
      const credential = GoogleAuthProvider.credentialFromResult(result);
      if (credential?.accessToken) {
        setGoogleToken(credential.accessToken);
        localStorage.setItem('google_oauth_token', credential.accessToken);
      }
    } catch (error) {
      console.error("Failed to login with Google:", error);
      throw error;
    }
  };

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
    <AuthContext.Provider value={{ user, loading, googleToken, loginWithGoogle, logout }}>
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
