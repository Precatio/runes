/* eslint-disable @next/next/no-img-element -- ImageResponse draws <img> into the picture itself */
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";

// The picture shown when a link to Vitki is shared (Open Graph, also used for Twitter/X and LinkedIn), at
// /delningsbild.png – a file with its extension, which also the static public website serves as a picture
export const dynamic = "force-static";
const size = { width: 1200, height: 630 };

export async function GET() {
  const logo = `data:image/png;base64,${(await readFile(join(process.cwd(), "public", "vitki_logo.png"))).toString("base64")}`;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center",
                    padding: "80px", background: "#f6f4f1", color: "#0f172a", position: "relative" }}>
        <img src={logo} alt="" width={206} height={171} style={{ position: "absolute", right: 110, top: 220, borderRadius: 28 }} />
        <div style={{ fontSize: 30, fontWeight: 700, color: "#b7410e", letterSpacing: 4 }}>VITKI</div>
        <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1.05, marginTop: 20, maxWidth: 900 }}>
          Runstenar och runinskrifter
        </div>
        <div style={{ fontSize: 34, color: "#475569", marginTop: 28, maxWidth: 900, lineHeight: 1.3 }}>
          Mönsterkarta, ristare, stilgrupper och statistik över Sveriges 2 321 vikingatida runstenar – öppen och fri.
        </div>
        <div style={{ fontSize: 24, color: "#64748b", marginTop: 40 }}>vitkirunor.se</div>
      </div>
    ),
    { ...size },
  );
}
