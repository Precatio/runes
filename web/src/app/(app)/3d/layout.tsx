// The 3D tools (measuring grooves, RTI raking light, images and rune forms) are built for a computer: measuring needs a
// mouse with Shift-click and room for the model beside the controls. On a phone a short note says so above the page,
// instead of letting someone try; the page itself is unchanged and still opens.
export default function ThreeDLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div role="note" className="md:hidden mx-4 mt-4 mb-2 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <strong>Huggspårsanalysen kräver en dator.</strong> Att mäta spåren görs med mus och Shift-klick och behöver en
        större skärm, så på en telefon går verktyget inte att använda fullt ut.
      </div>
      {children}
    </>
  );
}
