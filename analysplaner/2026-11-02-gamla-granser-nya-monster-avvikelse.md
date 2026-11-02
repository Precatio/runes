# Avvikelse 1 från planen 2026-11-02-gamla-granser-nya-monster (sha 054c87d5)

Skriven 2026-11-02 innan något resultat har setts (inget χ² har räknats ut; slumpindelningen fastnade i en oändlig loop).

**Problem:** grannregeln i steg 1 (ISOF-socknarnas punkter inom 10 km) lämnar härader utan grannar: Värmdö skeppslag och
Våla härad i Uppland; Aspelands, Handbörds och Norra Tjusts härader i Småland. Med isolerade enheter kan inga
sammanhängande slumpindelningar byggas, så planen går inte att genomföra som skriven.

**Ändring:** två härader är grannar om deras närmaste ISOF-socknar ligger inom **20 km**; en härad som ändå saknar grannar
får sin närmaste härad (minsta avstånd mellan socknarna) som granne. Allt annat är oförändrat. Övriga steg påverkas inte.

**Dessutom (bara teknik):** hjälpfunktionerna kopieras in i stället för att importeras ur folkland.py, eftersom importen
körde om hela folklandsanalysen; NPART kan sänkas med en miljövariabel för tidsprov, huvudkörningen använder 999.
