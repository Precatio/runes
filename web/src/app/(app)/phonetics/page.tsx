"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Språk & Fonetik was removed 2026-10-20: the AI reading could not be told apart from recalled formulas, and everything
// computed (the comparison with Rundata, the probability model's reading) lives on the stone pages. Old links go to the
// 3D page, where the images from the scan are.
export default function PhoneticsRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/3d"); }, [router]);
  return null;
}
