import { Source_Serif_4 } from "next/font/google";

// The research reports' book face (components/ReportPaper.tsx, app/forskningsrapporter): Source Serif 4, made for long reading,
// self-hosted by next/font and loaded only on the pages that use it. Exposed as the CSS variable --font-paper.
export const paperFace = Source_Serif_4({ subsets: ["latin", "latin-ext"], style: ["normal", "italic"], display: "swap", variable: "--font-paper" });
