"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { db, ProjectData, type AnalysisProvenance } from "@/lib/db";
import { useAnalysis } from "@/components/AnalysisContext";
import { useAuth } from "@/components/AuthContext";
import { useSettings } from "@/components/SettingsContext";
import { exportToGoogleDocs } from "@/lib/drive";
import DOMPurify from "dompurify";
import { API_URL } from "@/lib/api";

// A saved project, the current unsaved session, or a stored report (title only)
type ReportSource = Omit<Partial<ProjectData>, "slices"> & {
  stoneType?: string;
  weathering?: string;
  slices?: unknown[];
  provenance?: AnalysisProvenance;
};

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [project, setProject] = useState<ReportSource | null>(null);
  const { latest3DMeta, latest3DResults } = useAnalysis();
  const { googleToken, loginWithGoogle } = useAuth();
  const { aiHeaders, userName, userInstitution } = useSettings();
  const [reportHtml, setReportHtml] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isExportingGoogle, setIsExportingGoogle] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {

    const loadProj = async () => {
      let proj: ReportSource | null = null;
      if (id === "current") {
        proj = {
          name: "Aktuell Analys",
          metaText: latest3DMeta?.text || "Aktuell analys",
          stoneType: latest3DMeta?.stone || "Okänd",
          weathering: latest3DMeta?.weathering || "Okänt",
          attributedCarver: latest3DMeta?.carver || "Ingen hypotes",
          location: latest3DMeta?.location || "Okänd plats",
          metaOrnamentation: latest3DMeta?.ornamentation || "Okänd",
          metaPeriod: latest3DMeta?.period || "Okänd",
          provenance: latest3DResults?.provenance,
          // Backend expects the same per-slice fields as saved project slices
          slices: (latest3DResults?.slices ?? []).map(sl => ({
            angle: sl.apex_vinkel_deg,
            asymmetry: sl.asymmetri_deg,
            depth: sl.spårdjup_mm,
            width: sl.spårbredd_mm,
            djup_bredd_kvot: sl.djup_bredd_kvot,
            bottenradie: sl.bottenradie_mm,
            ytrahet: sl.ytråhet_mm,
            tool: latest3DResults?.results.troligt_verktyg,
          }))
        };
      } else {
        proj = await db.getProject(id);
      }
      
      if (!proj) {
        alert("Projektet hittades inte eller ingen data finns tillgänglig.");
        router.push("/synthesis");
        return;
      }
      setProject(proj);
      generateReport(proj);
    };
    
    const generateReport = async (proj: ReportSource) => {
      try {
        // 1. First run synthesis
        const synthRes = await fetch(`${API_URL}/api/synthesis/analyze`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            ...aiHeaders
          },
          body: JSON.stringify({
            signum: proj.metaText || "Okänt",
            stoneType: proj.metaStone || proj.stoneType || "Okänd",
            weathering: proj.metaWeathering || proj.weathering || "Okänt",
            attributed_carver: proj.attributedCarver || "Ingen hypotes",
            location: proj.location || "Okänd plats",
            ornamentation: proj.metaOrnamentation || "Okänd",
            period: proj.metaPeriod || "Okänd",
            slices: proj.slices
          })
        });
        const synthData = await synthRes.json();
        
        // 2. Now run report generator
        const reportRes = await fetch(`${API_URL}/api/synthesis/report`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            ...aiHeaders
          },
          body: JSON.stringify({
            signum: proj.metaText || "Okänt",
            stoneType: proj.metaStone || proj.stoneType || "Okänd",
            weathering: proj.metaWeathering || proj.weathering || "Okänt",
            attributed_carver: proj.attributedCarver || "Ingen hypotes",
            location: proj.location || "Okänd plats",
            ornamentation: proj.metaOrnamentation || "Okänd",
            period: proj.metaPeriod || "Okänd",
            slices: proj.slices,
            geology_analysis: synthData.geology_analysis,
            theory_analysis: synthData.theory_analysis,
            dating_analysis: synthData.dating_analysis,
            summary: synthData.summary,
            candidates: synthData.candidates,
            evidence: synthData.evidence,
            sources: synthData.sources,
            provenance: proj.provenance ?? proj.grooveAnalyses?.at(-1)?.provenance,
          })
        });
        const reportData = await reportRes.json();
        
        // Append images into HTML so they are editable
        let fullHtml = reportData.html_report;
        if (proj.threeImage || proj.plotImage || proj.twoDImage) {
          fullHtml += `
            <div style="margin-top: 40px; page-break-before: always;">
              <h2 style="border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">Bilagor: Visuell Analys</h2>
          `;
          
          if (proj.threeImage) {
            fullHtml += `
              <div style="margin-bottom: 20px;">
                <p style="font-weight: bold; color: #64748b; text-transform: uppercase; font-size: 12px; margin-bottom: 8px;">Figur: 3D-Modell och Snitt</p>
                <img src="${proj.threeImage}" style="max-width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;" />
              </div>
            `;
          }
          if (proj.plotImage) {
             fullHtml += `
              <div style="margin-bottom: 20px;">
                <p style="font-weight: bold; color: #64748b; text-transform: uppercase; font-size: 12px; margin-bottom: 8px;">Figur: Huggspårsprofil</p>
                <img src="${proj.plotImage}" style="max-width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;" />
              </div>
            `;
          }
          if (proj.twoDImage) {
             fullHtml += `
              <div style="margin-bottom: 20px;">
                <p style="font-weight: bold; color: #64748b; text-transform: uppercase; font-size: 12px; margin-bottom: 8px;">Figur: 2D Referens</p>
                <img src="${proj.twoDImage}" style="max-width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;" />
              </div>
            `;
          }
          
          fullHtml += `</div>`;
        }
        
        // AI-generated HTML: sanitize before it reaches the DOM
        setReportHtml(DOMPurify.sanitize(fullHtml));
        
      } catch (err) {
        console.error(err);
        alert("Kunde inte generera rapporten.");
      } finally {
        setLoading(false);
      }
    };
    
    // Check if it's an existing report vs a synthesis project
    const loadReportOrProj = async () => {
      if (id.startsWith("rep_")) {
         const reports = await db.getReports();
         const rep = reports.find(r => r.id === id);
         if (rep) {
           setProject({ name: rep.title, metaText: rep.title });
           setReportHtml(DOMPurify.sanitize(rep.htmlContent));
           setLoading(false);
         } else {
           alert("Hittade inte rapporten.");
           router.push("/account");
         }
      } else {
         loadProj();
      }
    };
    
    loadReportOrProj();
  }, [id, router, aiHeaders, latest3DMeta, latest3DResults]);

  // Compress base64 images inside HTML string before saving
  const compressImagesInHtml = async (html: string): Promise<string> => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const imgs = doc.querySelectorAll("img");
    
    for (const img of Array.from(imgs)) {
      if (img.src.startsWith("data:image")) {
        try {
          const compressed = await compressImage(img.src);
          img.src = compressed;
        } catch (e) {
          console.error("Failed to compress image", e);
        }
      }
    }
    return doc.body.innerHTML;
  };

  const compressImage = (base64: string): Promise<string> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const MAX_WIDTH = 800;
        const scaleSize = MAX_WIDTH / img.width;
        canvas.width = MAX_WIDTH;
        canvas.height = img.height * scaleSize;
        const ctx = canvas.getContext("2d");
        if (!ctx) return resolve(base64);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        // High compression to ensure we bypass 1MB limit for multiple images
        resolve(canvas.toDataURL("image/jpeg", 0.5)); 
      };
      img.onerror = reject;
      img.src = base64;
    });
  };

  const handleSaveReport = async () => {
    if (!editorRef.current || !project) return;
    setIsSaving(true);
    
    try {
      const currentHtml = editorRef.current.innerHTML;
      const compressedHtml = await compressImagesInHtml(currentHtml);
      
      await db.saveReport({
        id: id.startsWith("rep_") ? id : undefined,
        title: project.metaText || project.name || "Rapport",
        htmlContent: compressedHtml
      });
      
      alert("Rapporten sparades till ditt konto!");
      if (!id.startsWith("rep_")) {
        router.push("/account");
      }
    } catch (e) {
      console.error(e);
      alert("Kunde inte spara rapporten.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportGoogleDocs = async () => {
    if (!editorRef.current || !project) return;
    
    // Check if user has token
    if (!googleToken) {
      const confirmLogin = confirm("Du måste logga in med Google för att spara till Google Drive. Vill du logga in nu?");
      if (confirmLogin) {
        try {
          await loginWithGoogle();
          alert("Inloggad! Klicka på export-knappen igen för att spara.");
        } catch {
          alert("Inloggningen avbröts.");
        }
      }
      return;
    }

    setIsExportingGoogle(true);
    try {
      // Vi bygger ihop en komplett HTML-sträng som Google Drive kan konvertera till ett Docs-dokument
      const currentHtml = editorRef.current.innerHTML;
      
      // Lägg till header och lite enklare CSS för Google Docs-export
      const fullDocumentHtml = `
        <html>
          <head>
            <style>
              body { font-family: Arial, sans-serif; }
              h1 { font-size: 24pt; color: #000000; border-bottom: 2pt solid #000000; padding-bottom: 6pt; }
              h2 { font-size: 18pt; color: #333333; margin-top: 18pt; }
              p { font-size: 11pt; line-height: 1.5; }
              .header-meta { font-size: 10pt; color: #666666; margin-bottom: 24pt; }
            </style>
          </head>
          <body>
            <h1>Vitki Akademisk Rapport: ${project.metaText || project.name}</h1>
            <div class="header-meta">
              Datum: ${new Date().toLocaleDateString('sv-SE')}<br/>
              Skapad av: ${userName}<br/>
              ${userInstitution ? `Institution: ${userInstitution}` : ''}
            </div>
            ${currentHtml}
          </body>
        </html>
      `;

      // Export using lib
      const docsLink = await exportToGoogleDocs(
        fullDocumentHtml, 
        `Vitki_Rapport_${project.metaText || "Analys"}`, 
        googleToken
      );
      
      alert("Sparad till Google Drive! Du kan nu öppna och redigera den där.");
      window.open(docsLink, "_blank"); // Open the new doc in a new tab

    } catch (e) {
      console.error(e);
      alert("Kunde inte spara till Google Docs. Din inloggnings-session kan ha gått ut.");
    } finally {
      setIsExportingGoogle(false);
    }
  };

  if (loading || !project) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-slate-200 border-t-[#b7410e] rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-slate-800">Genererar akademisk rapport...</h2>
          <p className="text-slate-500 mt-2">Detta kan ta upp till en minut.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="print:hidden bg-slate-100 border-b border-slate-200 p-4 flex justify-between items-center sticky top-0 z-50">
        <div>
          <h1 className="font-bold text-slate-800 text-lg">Granska Rapport</h1>
          <p className="text-xs text-slate-500">Skriv ut eller spara som PDF för bästa resultat.</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleExportGoogleDocs}
            disabled={isExportingGoogle}
            className="px-4 py-2 text-sm font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            {isExportingGoogle ? (
              <div className="w-4 h-4 border-2 border-slate-400 border-t-slate-700 rounded-full animate-spin"></div>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" className="w-4 h-4">
                <path fill="#4CAF50" d="M11 44h26c2.2 0 4-1.8 4-4V16L29 4H11c-2.2 0-4 1.8-4 4v32c0 2.2 1.8 4 4 4z"></path>
                <path fill="#E8F5E9" d="M29 4v12h12L29 4z"></path>
                <path fill="#2E7D32" d="M21 23h12v4H21zm0 8h12v4H21zM15 23h4v4h-4zm0 8h4v4h-4z"></path>
              </svg>
            )}
            Exportera till Google Docs
          </button>
          
          <button 
            onClick={handleSaveReport}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            {isSaving ? "Sparar..." : "Spara till Mitt Konto"}
          </button>
          <button 
            onClick={() => window.print()}
            className="px-4 py-2 text-sm font-bold text-white bg-[#b7410e] hover:bg-[#9a350b] rounded-lg shadow-sm transition-colors flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0 1 10.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0 .229 2.523a1.125 1.125 0 0 1-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0 0 21 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 0 0-1.913-.247M6.34 18H5.25A2.25 2.25 0 0 1 3 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 0 1 1.913-.247m10.5 0a48.536 48.536 0 0 0-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5Zm-3 0h.008v.008H15V10.5Z" />
            </svg>
            Spara som PDF
          </button>
        </div>
      </div>

      <div className="report-content max-w-[21cm] mx-auto p-8 md:p-16 print:p-0 print:pt-4 text-slate-900 bg-white">
        <div className="mb-12 border-b-2 border-slate-900 pb-6 flex justify-between items-end">
          <div>
            <div className="text-sm font-bold uppercase tracking-widest text-[#b7410e] mb-2">Vitki Akademisk Rapport</div>
            <h1 className="text-4xl font-serif font-bold text-slate-900">{project.metaText || project.name}</h1>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-slate-600">Datum: {new Date().toLocaleDateString('sv-SE')}</p>
            <p className="text-sm font-semibold text-slate-600">Skapad av: {userName}</p>
            {userInstitution && <p className="text-xs font-semibold text-slate-500">{userInstitution}</p>}
          </div>
        </div>

        <div 
          className="prose prose-slate prose-lg max-w-none prose-headings:font-serif prose-h1:text-3xl prose-h2:text-2xl prose-h2:mt-10 prose-h2:border-b prose-h2:border-slate-200 prose-h2:pb-2 prose-a:text-[#b7410e] outline-none"
          contentEditable
          suppressContentEditableWarning
          ref={editorRef}
          dangerouslySetInnerHTML={{ __html: reportHtml }} 
        />
      </div>
    </div>
  );
}
