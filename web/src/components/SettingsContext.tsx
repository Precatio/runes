"use client";

import React, { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { useAuth } from "./AuthContext";
import { db as firestore } from "@/firebase/config";
import { doc, getDoc, setDoc, updateDoc, deleteField } from "firebase/firestore";

export type AIProvider = "claude" | "gemini";

interface SettingsContextType {
  aiProvider: AIProvider;
  anthropicKey: string;
  setAiProvider: (p: AIProvider) => void;
  setAnthropicKey: (key: string) => void;
  // Headers for every AI call: chosen model and the user's own keys (kept only in this browser)
  aiHeaders: Record<string, string>;
  geminiKey: string;
  openaiKey: string;
  userName: string;
  userInstitution: string;
  setGeminiKey: (key: string) => void;
  setOpenaiKey: (key: string) => void;
  setUserName: (name: string) => void;
  setUserInstitution: (inst: string) => void;
  isModalOpen: boolean;
  setIsModalOpen: (open: boolean) => void;
  totalTokensUsed: number;
  tokenHistory: Record<string, number>;
  addUsedTokens: (count: number) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [geminiKey, setGeminiState] = useState("");
  const [anthropicKey, setAnthropicState] = useState("");
  const [aiProvider, setProviderState] = useState<AIProvider>("claude");
  const [openaiKey, setOpenaiState] = useState("");
  const [userName, setUserNameState] = useState("Viktor Kvant");
  const [userInstitution, setUserInstState] = useState("Bifrost");
  const [totalTokensUsed, setTotalTokensUsed] = useState(0);
  const [tokenHistory, setTokenHistory] = useState<Record<string, number>>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const { user } = useAuth();

  useEffect(() => {
    const loadSettings = async () => {
      let savedGemini = localStorage.getItem("vitki_gemini_key");
      let savedOpenai = localStorage.getItem("vitki_openai_key");
      let savedName = localStorage.getItem("vitki_user_name");
      let savedInst = localStorage.getItem("vitki_user_inst");
      let savedTokens = parseInt(localStorage.getItem("vitki_tokens_used") || "0", 10);
      let savedHistory = {};
      try {
        savedHistory = JSON.parse(localStorage.getItem("vitki_token_history") || "{}");
      } catch {}
      
      if (user) {
        try {
          const docRef = doc(firestore, `users/${user.uid}/settings`, "profile");
          const snap = await getDoc(docRef);
          if (snap.exists()) {
            const data = snap.data();
            // API keys are local-only. Migrate keys that older versions synced to
            // Firestore into localStorage, then remove them from the cloud.
            if (data.geminiKey || data.openaiKey) {
              if (data.geminiKey && !savedGemini) {
                savedGemini = data.geminiKey;
                localStorage.setItem("vitki_gemini_key", data.geminiKey);
              }
              if (data.openaiKey && !savedOpenai) {
                savedOpenai = data.openaiKey;
                localStorage.setItem("vitki_openai_key", data.openaiKey);
              }
              updateDoc(docRef, { geminiKey: deleteField(), openaiKey: deleteField() })
                .catch(e => console.error("Failed to remove API keys from Firestore:", e));
            }
            savedName = data.userName || savedName;
            savedInst = data.userInstitution || savedInst;
            savedTokens = data.totalTokensUsed || savedTokens;
            savedHistory = data.tokenHistory || savedHistory;
          }
        } catch (e) {
          console.error("Failed to fetch settings from Firestore:", e);
        }
      }

      if (savedGemini) setGeminiState(savedGemini);
      const savedAnthropic = localStorage.getItem("vitki_anthropic_key");
      if (savedAnthropic) setAnthropicState(savedAnthropic);
      const savedProvider = localStorage.getItem("vitki_ai_provider");
      if (savedProvider === "claude" || savedProvider === "gemini") setProviderState(savedProvider);
      if (savedOpenai) setOpenaiState(savedOpenai);
      if (savedName) setUserNameState(savedName);
      // The app was earlier called Aagaard Research; saved settings get the new name Bifrost
      if (savedInst === "Aagaard Research") {
        savedInst = "Bifrost";
        localStorage.setItem("vitki_user_inst", savedInst);
        if (user) {
          setDoc(doc(firestore, `users/${user.uid}/settings`, "profile"), { userInstitution: savedInst }, { merge: true })
            .catch(e => console.error("Failed to save setting to Firestore:", e));
        }
      }
      if (savedInst) setUserInstState(savedInst);
      if (savedTokens) setTotalTokensUsed(savedTokens);
      if (Object.keys(savedHistory).length > 0) setTokenHistory(savedHistory);
    };
    loadSettings();
  }, [user]);
  
  const saveToFirestore = async (key: string, value: string) => {
    if (user) {
       try {
         const docRef = doc(firestore, `users/${user.uid}/settings`, "profile");
         await setDoc(docRef, { [key]: value }, { merge: true });
       } catch (e) {
         console.error("Failed to save setting to Firestore:", e);
       }
    }
  };

  const addUsedTokens = (count: number) => {
    if (!count) return;
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    
    // Calculate new values outside to avoid StrictMode double-invocation bugs
    const newTotal = totalTokensUsed + count;
    const newHistory = { ...tokenHistory };
    newHistory[today] = (newHistory[today] || 0) + count;
    
    // Update local state
    setTotalTokensUsed(newTotal);
    setTokenHistory(newHistory);
    
    // Update storage
    localStorage.setItem("vitki_tokens_used", newTotal.toString());
    localStorage.setItem("vitki_token_history", JSON.stringify(newHistory));
    
    if (user) {
       try {
         const docRef = doc(firestore, `users/${user.uid}/settings`, "profile");
         setDoc(docRef, { 
           totalTokensUsed: newTotal,
           tokenHistory: newHistory 
         }, { merge: true });
       } catch (e) {
         console.error("Failed to save tokens to Firestore:", e);
       }
    }
  };

  const setGeminiKey = (key: string) => {
    setGeminiState(key);
    localStorage.setItem("vitki_gemini_key", key);
  };

  const setAnthropicKey = (key: string) => {
    setAnthropicState(key);
    localStorage.setItem("vitki_anthropic_key", key);
  };

  const setAiProvider = (p: AIProvider) => {
    setProviderState(p);
    localStorage.setItem("vitki_ai_provider", p);
  };

  const aiHeaders = useMemo(() => {
    const h: Record<string, string> = { "X-AI-Provider": aiProvider };
    if (anthropicKey) h["X-Anthropic-Api-Key"] = anthropicKey;
    if (geminiKey) h["X-Gemini-Api-Key"] = geminiKey;
    return h;
  }, [aiProvider, anthropicKey, geminiKey]);

  const setOpenaiKey = (key: string) => {
    setOpenaiState(key);
    localStorage.setItem("vitki_openai_key", key);
  };

  const setUserName = (name: string) => {
    setUserNameState(name);
    localStorage.setItem("vitki_user_name", name);
    saveToFirestore("userName", name);
  };

  const setUserInstitution = (inst: string) => {
    setUserInstState(inst);
    localStorage.setItem("vitki_user_inst", inst);
    saveToFirestore("userInstitution", inst);
  };

  return (
    <SettingsContext.Provider value={{ 
      aiProvider, anthropicKey, setAiProvider, setAnthropicKey, aiHeaders,
      geminiKey, openaiKey, userName, userInstitution,
      setGeminiKey, setOpenaiKey, setUserName, setUserInstitution,
      isModalOpen, setIsModalOpen,
      totalTokensUsed, tokenHistory, addUsedTokens
    }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
