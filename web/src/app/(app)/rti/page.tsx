import { redirect } from "next/navigation";

// RTI-visaren bor sedan 2026-10-18 som ett verktyg på 3D-sidan; gamla adressen pekas dit
export default function RTIRedirect() {
  redirect("/3d?verktyg=rti");
}
