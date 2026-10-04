export type Language = "sv" | "en";

export interface Translations {
  sidebar: {
    title: string;
    subtitle: string;
    ai_runologist: string;
    threed_analysis: string;
    nlp_analysis: string;
    twod_analysis: string;
    synthesis: string;
    phonetics: string;
    knowledge_base: string;
    documentation: string;
    inscriptions: string;
    map: string;
    styles: string;
    corpus: string;
    compare: string;
    rti: string;
    group_analysis: string;
    group_research: string;
    group_resources: string;
    settings: string;
    built_by: string;
    optimized_for: string;
  };
  chat: {
    title: string;
    description: string;
    placeholder: string;
  };
  threed: {
    title: string;
    description: string;
    use_mock: string;
    upload_mesh: string;
    vectors: string;
    origin: string;
    direction: string;
    up_vector: string;
    analyze_btn: string;
    calculating: string;
    v_angle: string;
    asymmetry: string;
    groove_depth: string;
    graph_title: string;
    graph_empty: string;
    extracting: string;
  };
  nlp: {
    title: string;
    description: string;
    under_construction: string;
    under_construction_desc: string;
  };
}

export const translations: Record<Language, Translations> = {
  sv: {
    sidebar: {
      title: "Vitki AI",
      subtitle: "Analysplattform",
      ai_runologist: "Vitki AI",
      threed_analysis: "3D-Huggspårsanalys",
      twod_analysis: "2D-Bildanalys (Paleografi)",
      synthesis: "Syntes & Attribuering",
      phonetics: "Språk & Fonetik",
      nlp_analysis: "Lingvistisk Analys",
      knowledge_base: "Runologiskt Arkiv",
      documentation: "Dokumentation & Om",
      inscriptions: "Inskrifter (Rundata)",
      map: "Karta",
      styles: "Stilgrupper",
      corpus: "Mätkorpus",
      compare: "Jämför stenar",
      rti: "RTI-visare",
      group_analysis: "Analys",
      group_research: "Forskning",
      group_resources: "Resurser",
      settings: "Inställningar & API",
      built_by: "Utvecklad av",
      optimized_for: "Optimerad för epigrafisk forskning",
    },
    chat: {
      title: "Epigrafisk AI-Assistent",
      description: "Interagera med en specialiserad AI-modell tränad för runologisk och epigrafisk vetenskaplig diskurs. Assistenten kan assistera med datatolkning och metodologiska frågeställningar.",
      placeholder: "Formulera din forskningsfråga...",
    },
    threed: {
      title: "3D-Huggspårsanalys (Fotogrammetri)",
      description: "Ladda upp fotogrammetriska 3D-modeller (mesh) av runstenar. Definiera snittvektorer för att extrahera profilgeometri och kvantifiera ristningsspårens vinkel och djup.",
      use_mock: "Använd referensdata (Mock)",
      upload_mesh: "Ladda upp 3D-mesh (.stl, .obj)",
      vectors: "Snittvektorer (X, Y, Z)",
      origin: "Origo (Startpunkt)",
      direction: "Riktning (Vektor)",
      up_vector: "Uppvektor (Normal)",
      analyze_btn: "Exekvera Snittanalys",
      calculating: "Beräknar topologiskt snitt...",
      v_angle: "Korsningsvinkel",
      asymmetry: "Asymmetriindex",
      groove_depth: "Maximalt Spårdjup",
      graph_title: "Topografisk Spårprofil",
      graph_empty: "Initiera analys för att rendera topografisk profil",
      extracting: "Extraherar ytdatapunktmoln...",
    },
    nlp: {
      title: "Kvantitativ Lingvistik & NLP",
      description: "Modul för storskalig korpusanalys och Natural Language Processing (NLP) av runtexter, med fokus på syntax, semantik och formelartade mönster.",
      under_construction: "Modul Under Utveckling",
      under_construction_desc: "Arkitekturen för att stödja semantisk klustring och morfologisk jämförelse av historiska inskriptioner implementeras för närvarande.",
    },
  },
  en: {
    sidebar: {
      title: "Vitki AI",
      subtitle: "Analysis Platform",
      ai_runologist: "Vitki AI",
      threed_analysis: "3D Groove Analysis",
      twod_analysis: "2D Image Analysis (Paleography)",
      synthesis: "Synthesis & Attribution",
      phonetics: "Language & Phonetics",
      nlp_analysis: "Linguistic Analysis",
      knowledge_base: "Runological Archive",
      documentation: "Documentation & About",
      inscriptions: "Inscriptions (Rundata)",
      map: "Map",
      styles: "Style groups",
      corpus: "Measurement corpus",
      compare: "Compare stones",
      rti: "RTI viewer",
      group_analysis: "Analysis",
      group_research: "Research",
      group_resources: "Resources",
      settings: "Settings & API",
      built_by: "Developed by",
      optimized_for: "Optimized for epigraphic research",
    },
    chat: {
      title: "Epigraphic AI Assistant",
      description: "Engage with a specialized AI model trained for runological and epigraphic scientific discourse. The assistant can aid in data interpretation and methodological inquiries.",
      placeholder: "Formulate your research inquiry...",
    },
    threed: {
      title: "3D Carving Groove Analysis",
      description: "Upload photogrammetric 3D models (mesh) of runestones. Define intersection vectors to extract profile geometry and quantify carving groove angles and depths.",
      use_mock: "Use Reference Data (Mock)",
      upload_mesh: "Upload 3D Mesh (.stl, .obj)",
      vectors: "Intersection Vectors (X, Y, Z)",
      origin: "Origin (Starting point)",
      direction: "Direction (Vector)",
      up_vector: "Up Vector (Normal)",
      analyze_btn: "Execute Profile Analysis",
      calculating: "Computing topological intersection...",
      v_angle: "Intersection Angle",
      asymmetry: "Asymmetry Index",
      groove_depth: "Maximum Groove Depth",
      graph_title: "Topographic Groove Profile",
      graph_empty: "Initiate analysis to render topographic profile",
      extracting: "Extracting surface point cloud...",
    },
    nlp: {
      title: "Quantitative Linguistics & NLP",
      description: "Module for large-scale corpus analysis and Natural Language Processing (NLP) of runic texts, focusing on syntax, semantics, and formulaic patterns.",
      under_construction: "Module Under Development",
      under_construction_desc: "The architecture to support semantic clustering and morphological comparison of historical inscriptions is currently being implemented.",
    },
  },
};
