# De döda som går igen – resultat

Fördjupning 8 i serien Fornnordiska väsen. Låst plan: `analysplaner/2026-11-23-de-doda-som-gar-igen.md` (sha256
93b258fa…, commit d6a533a). Skript: `utdata/de_doda/analys.py`. Siffror: `matt.json`. Blind kontroll: `kontroll_resultat.json`.
Texterna och klassningen med utdrag ligger utanför git (`data/cache/de_doda/`).

## Träffarna och klassningen
- **383 träffar:**
  - mönster A (den gående döde): 72;
  - mönster B (högen): 311;
  - per textgrupp: islänningasagornas prosa 149, fornaldarsagornas prosa 127, övriga 107.
- **Alla klassade för hand** med Anthropics språkmodell Claude (Claude Opus):

  | Klass | Antal |
  |---|---|
  | högbo | 133 |
  | grav | 125 |
  | plats | 43 |
  | gengångare | 38 |
  | annan betydelse | 32 |
  | annat | 12 |

- **Blind kontroll:** 40 träffar, stratifierade efter mönster × textgrupp, klassades av en separat instans av samma modell
  utan att se den första klassningen. **39 av 40 lika (97,5 %).** Kravet var ≥ 85 %. Den enda oenigheten gällde "arnar flaug
  of hauga" i Hávarðr haltes vers i Skáldskaparmál: vi klassade det som *plats*, kontrollen som *annan betydelse*
  (omskrivning).
- **Gränsfall vi valde själva:**
  - *reimt/reimleikar* räknas som gengångare bara när den döde är utpekad. Sandhaugar-spöket i Grettis saga (troll) och
    Ketils saga blev *annat*.
  - Sigmundr och Sinfjötli, som murades in levande i en hög i Völsunga saga, blev *grav*.
- **Utgåvan:** en träff i Heiðarvíga saga är en utgivarnot i utgåvan (hänvisning till Eyrbyggjas dyradom), inte
  sagatext. Den står kvar som gengångare enligt klassningen och påverkar inte T1, eftersom Heiðarvíga saga har den enda
  träffen.

## V1 – klasserna per grupp
| Grupp | gengångare | högbo | grav | plats | annan betydelse | annat |
|---|---|---|---|---|---|---|
| Islänningasagornas prosa (149) | 36 | 42 | 48 | 6 | 12 | 5 |
| Fornaldarsagornas prosa (127) | 1 | 53 | 48 | 16 | 5 | 4 |
| Övriga (107) | 1 | 38 | 29 | 21 | 15 | 3 |

**Täthet för verksamma döda** (gengångare + högbo) per 10 000 ord:

| Text | Täthet |
|---|---|
| Fornaldarsagornas vers | 6,8 |
| Eddadikterna | 4,6 |
| Islänningasagornas vers | 2,1 |
| Fornaldarsagornas prosa | 1,6 |
| Islänningasagornas prosa | 0,9 |
| Heimskringla | 0,08 |
| Snorres Edda | 0 |
| Samtidssagorna | 0 |

## V2 – var de döda finns
- **Flest verksamma döda:**

  | Text | Verksamma döda | Den döde |
  |---|---|---|
  | Göngu-Hrólfs saga | 24 | Hreggviðr |
  | Hrómundar saga | 19 | Þráinn |
  | Grettis saga | 19 | Glámr och Kárr |
  | Hervararkviða | 15 | Angantýr |
  | Harðar saga | 15 | Sóti |
  | Bárðar saga | 12 | Raknarr |
  | Eyrbyggja saga | 8 | Þórólfr bægifótr, Fróðá |

- **Handläsningen, beskrivande och inte prövad:** islänningasagornas 42 högbor finns i fem sagor. 37 av dem bor utomlands:
  - Kárr på Háramarsey i Norge;
  - Sóti i Norge;
  - Agnarr i Norge;
  - Raknarr i Helluland.

  Den enda högbon på Island är Gunnar på Hlíðarendi, som sjunger glad i sin hög (5). Gengångarna går igen hemma:
  - på Island (Glámr, Þórólfr bægifótr, Fróðá, Hrappr, Klaufi);
  - på Grönland (Eiríks saga rauða, Flóamanna saga);
  - på Färöarna (Færeyinga saga);
  - en gång i Norge (Bjarnes far i Flóamanna saga).

## T1 – hemma eller i högen (låst): **håller**
Andelen *högbo* bland de verksamma döda:

| | Fornaldarsagorna | Islänningasagorna | Skillnad | 95 % intervall | p |
|---|---|---|---|---|---|
| **Huvud** | 53/54 = 98,1 % (9 sagor) | 42/78 = 53,8 % (14 sagor) | 44,3 pe | 17,7 till 76,6 | 0,004 |
| Bara mönster A | 5 i 2 sagor | 38 i 12 sagor | – | – | obestämt (för få) |
| En per saga | 9 | 17 | – | – | obestämt (fornaldarsagorna < 10) |

- **I fornaldarsagorna möter man de döda i högen.** Den enda gengångaren där är när de döda reser sig på slagfältet i
  Hrólfs saga kraka.
- **I islänningasagorna** är hälften av de verksamma döda gengångare som kommer hem till gården.
- **Båda känslighetsproven blev obestämda:** underlaget räcker inte för dem enligt planens krav. Huvudprovet vilar på
  träffarna i högarna.

## V3 – runstenarna
- **Mönstret** `\bhaug\w*|\bhôg\w*` var för brett: det fångar *hôggva* (hugga) 60 gånger.
- **Vid handläsning nämner tre stenar en hög:**
  - U 135 ("brú þessa gerðu ok haug þenna");
  - U 269 ("lét reisa steina ok haug gera eptir Bjôrn");
  - Öl 1, Karlevistenen ("Þrúðar draugr í þessu haugi").
- **På Karlevistenen** är *draugr* en del av en skaldisk omskrivning för en krigare ("Þrúðs träd"), inte en gengångare.
  Det är den enda runsten med substantivet *draugr* (en sökning på `draug` i hela Rundata ger också Sö 126, där *draug* är verbet *draga*: "hann draug orrostu").
- **Runstenarna** talar aldrig om döda som går igen.

## Vad det betyder och inte betyder
- Ett ord i en text är inte en tro. Sagorna skrevs på 1200- och 1300-talen.
- Skillnaden visar två sätt att berätta: fornaldarsagornas äventyr i högen och islänningasagornas oro hemma på gården.
  Det säger inte hur människor på vikingatiden trodde att de döda betedde sig.
