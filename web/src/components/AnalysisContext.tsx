"use client";
import React, { createContext, useContext, useState } from "react";
import { TwoDResultData, LinguisticResultData, ThreeDAnalysisResult, TwoDSource } from "@/lib/db";
import type { StoneReportInput } from "@/lib/stoneReport";

export interface MetaData {
  stone: string;
  weathering: string;
  text: string;
  ornamentation: string;
  period: string;
  carver: string;
  location: string;
}

interface AnalysisContextType {
  latest3DResults: ThreeDAnalysisResult | null;
  setLatest3DResults: (data: ThreeDAnalysisResult | null) => void;
  latest3DFile: File | null;
  setLatest3DFile: (data: File | null) => void;
  latest3DMeta: MetaData;
  setLatest3DMeta: (data: MetaData) => void;
  latestLinguisticResults: LinguisticResultData | null;
  setLatestLinguisticResults: (data: LinguisticResultData | null) => void;
  latest2DResults: TwoDResultData | null;
  setLatest2DResults: (data: TwoDResultData | null) => void;
  latest2DImage: string | null;
  setLatest2DImage: (data: string | null) => void;
  latest2DFile: File | null;
  setLatest2DFile: (data: File | null) => void;
  latest2DSource: TwoDSource | null;
  setLatest2DSource: (data: TwoDSource | null) => void;
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
  stoneReportInput: StoneReportInput | null;
  setStoneReportInput: (data: StoneReportInput | null) => void;
  // Images handed to Språk & Fonetik (relief from the 3D view, a view from the RTI viewer)
  phoneticsImage: PhoneticsImage | null;
  setPhoneticsImage: (data: PhoneticsImage | null) => void;
}

export interface PhoneticsImage {
  source: string;
  images: Record<string, string>; // label -> data URL; the first is shown first
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [latest3DResults, setLatest3DResults] = useState<ThreeDAnalysisResult | null>(null);
  const [latest3DFile, setLatest3DFile] = useState<File | null>(null);
  const [latest3DMeta, setLatest3DMeta] = useState<MetaData>({
    stone: "Granit", weathering: "Låg", text: "", ornamentation: "", period: "", carver: "", location: ""
  });
  const [latestLinguisticResults, setLatestLinguisticResults] = useState<LinguisticResultData | null>(null);
  const [latest2DResults, setLatest2DResults] = useState<TwoDResultData | null>(null);
  const [latest2DImage, setLatest2DImage] = useState<string | null>(null);
  const [latest2DFile, setLatest2DFile] = useState<File | null>(null);
  const [latest2DSource, setLatest2DSource] = useState<TwoDSource | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [stoneReportInput, setStoneReportInput] = useState<StoneReportInput | null>(null);
  const [phoneticsImage, setPhoneticsImage] = useState<PhoneticsImage | null>(null);

  return (
    <AnalysisContext.Provider value={{
      latest3DResults, setLatest3DResults,
      latest3DFile, setLatest3DFile,
      latest3DMeta, setLatest3DMeta,
      latestLinguisticResults, setLatestLinguisticResults,
      latest2DResults, setLatest2DResults,
      latest2DImage, setLatest2DImage,
      latest2DFile, setLatest2DFile,
      latest2DSource, setLatest2DSource,
      activeProjectId, setActiveProjectId,
      stoneReportInput, setStoneReportInput,
      phoneticsImage, setPhoneticsImage,
    }}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return context;
}
