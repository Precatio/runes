// Korpus → Ristarna i appen: sidan (components/Ristare.tsx) med datan från analysmotorn, som bygger den i korpusjobbet
import Ristare from "@/components/Ristare";
import { API_URL } from "@/lib/api";
import "../../ristarna/ristare.css";

export default function RistarePage() {
  return <Ristare src={`${API_URL}/api/r/ristare`} />;
}
