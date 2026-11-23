// Korpus → Ristarna i appen: sidan (components/Ristare.tsx) med datan från analysmotorn, som bygger den i korpusjobbet,
// och under den stenarna som kan ha samma hand (components/HandGroups.tsx, GET /api/r/handgrupper)
import HandGroups from "@/components/HandGroups";
import Ristare from "@/components/Ristare";
import { API_URL } from "@/lib/api";
import "@/components/ristare.css";

export default function RistarePage() {
  return (
    <>
      <Ristare src={`${API_URL}/api/r/ristare`} />
      <HandGroups src={`${API_URL}/api/r/handgrupper`} />
    </>
  );
}
