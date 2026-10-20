"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// The 2D analysis became the tab "Bilder och runformer" on the 3D page (2026-10-20); old links land there
export default function TwoDRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/3d?verktyg=2d"); }, [router]);
  return null;
}
