# Admin på webben – publicering utan Viktors dator

Från och med november 2026 kan Vitki publicera artiklar och posta Bluesky-kön utan att den lokala appen är igång. Det
finns också en första webbadmin, `/redaktion`, som fungerar från vilken dator eller mobil som helst. Allt är byggt så
att det är **avstängt tills du har gjort stegen nedan**. Innan dess gör arbetsflödena ingenting, och `/redaktion` säger
"inte aktiverad än".

## Vad som körs var

| Vad | Var | När |
|---|---|---|
| Webbplatsen vitkirunor.se | GitHub Pages, `.github/workflows/site.yml` | Vid push till `web/**`, och när `publicera.yml` startar den |
| Export av artiklarna ur Firestore | GitHub Actions, `.github/workflows/publicera.yml` → `scripts/ci_publicera.py` → `src/site_export.py` | Var 30:e minut (:07 och :37) och för hand |
| Bluesky-förfrågningar från /redaktion in i kön | Samma körning: `scripts/ci_publicera.py` läser `bluesky_forfragningar` och lägger nya i `data/bluesky/ko.json` (`src/bluesky_queue.py`) | Var 30:e minut, med exporten |
| Veckoplanen till Firestore | `scripts/publiceringsschema_sync.py` på datorn | När du har ändrat `data/publiceringsschema.json` |
| Bluesky-kön (`data/bluesky/ko.json`) | GitHub Actions, `.github/workflows/bluesky.yml` → `scripts/ci_bluesky.py` → `scripts/bluesky_post.py`, **eller** den lokala appens tråd i `api/main.py` | Från kl. 18 svensk tid. Filen `data/bluesky/postning.json` avgör vem som postar |
| Webbadmin `/redaktion` | Den statiska webbplatsen. Google-inloggning (Firebase Auth) och Firestore direkt från webbläsaren, skyddat av `web/firestore.rules` | När du vill |
| Skriva och ändra text, R-figurer, ta bort, veckans artikel, redigera Bluesky-kön | Den lokala appen, som förut | – |

**Exporten i CI** gör samma sak som den lokala appen och använder samma kontroller. Den stoppar om många artiklar skulle
försvinna på en gång eller om figurer saknas. Den committar bara när något har ändrats. Sidvisningarna ("mest lästa")
läses en gång om dygnet, kl. 05:07.

**/redaktion** visar:

- **Översikt**: vad som är schemalagt de närmaste fyra veckorna, antal utkast, det senast publicerade och de senaste
  körningarna i GitHub Actions.
- **Veckan**: *Veckans publiceringar (vecka N)*, samma som i den lokala Admin. Se måndagsrutinen nedan.
- **Innehåll**: sök och filter (Utkast, Schemalagda, Publicerade, Rapporter). På varje rad finns Förhandsgranska,
  Schemalägg (svensk tid), Publicera nu och Avpublicera.

Sidan ändrar bara fälten `published`, `publishedAt`, `month`, `updatedAt` och `by`, med samma betydelse som när den
lokala appen sparar. Den redigerar aldrig text och tar aldrig bort något, och reglerna tillåter inget annat. Den enda
andra skrivningen är en Bluesky-förfrågan när du godkänner veckan. Den kan bara skapas, aldrig ändras eller tas bort. En ändring
syns på webbplatsen inom ungefär en halvtimme, eller direkt om den lokala appen är igång.

## Måndagsrutinen på webben

Allt går från mobilen, och datorn behöver inte vara igång.

1. Öppna https://vitkirunor.se/redaktion/, logga in och välj fliken **Veckan**. Den visar den kommande veckan (på en
   måndag den vecka som börjar i dag). Med pilarna byter du vecka.
2. Varje rad visar veckodag, datum och tid, rubrik, spår och lägeschips. Chipsen säger om raden är utkast, schemalagd
   eller publicerad, om den är godkänd, om engelskan finns, om etiketterna är rätt och hur långt Bluesky-inlägget är.
   Tryck på *Bluesky-inlägget* för att läsa det. En rad som inte kan godkännas har ingen bock och säger varför: den
   saknas, är redan live eller schemalagd, tiden har passerat, etiketterna är fel eller Bluesky-texten är för lång.
3. Tryck på **Godkänn veckans publiceringar** och läs listan. Tryck sedan på **Ja, schemalägg**. Sidan kontrollerar
   varje rad på nytt mot Firestore. Därefter schemaläggs artikeln till sin tid i svensk tid, på samma sätt som
   *Schemalägg*. Om artikeln har en engelsk utgåva skapas en Bluesky-förfrågan. Under knappen står resultatet för
   varje rad.
4. GitHub Actions lägger förfrågan i `data/bluesky/ko.json` vid nästa körning av "Publicera artiklarna", alltså inom
   ungefär en halvtimme. Inlägget hamnar före köns andra inlägg samma dag och postas kl. 18 på publiceringsdagen.
   Commiten heter "Bluesky-kön: inlägg från /redaktion" eller ingår i exportens commit.

"Godkänd" betyder att artikeln är schemalagd eller publicerad. Det läses ur artikeln själv. Om du avpublicerar en
artikel är den alltså inte godkänd längre. En redan skickad Bluesky-förfrågan ligger dock kvar (se nedan).

**Planen.** Veckoplanen redigerar du som förut i `data/publiceringsschema.json`. /redaktion läser en kopia i Firestore
(samlingen `publiceringsschema`), så efter varje ändring kör du:

```
.venv/bin/python scripts/publiceringsschema_sync.py            # visar vad som skulle skrivas
.venv/bin/python scripts/publiceringsschema_sync.py --skriv    # skriver och läser tillbaka
```

Skriptet lägger till och uppdaterar rader, men tar aldrig bort något utan `--rensa`. Med `--rensa` tar det bara bort
rader som inte står i filen och vars artikel inte är schemalagd eller publicerad. Den lokala Admin läser filen
direkt, som förut. Fältet `godkand` fylls bara i av den lokala Admin.

**Bluesky-förfrågningarna.** En förfrågan finns per artikeladress (`bluesky_forfragningar/<adress>`). När den
hanterats står utfallet i `data/bluesky/webbforfragningar.json`, och den läggs aldrig in igen, inte heller om du
stryker inlägget ur `ko.json`. Om du vill att en förfrågan prövas på nytt tar du bort dess rad i den filen. Om
adressen redan står i kön, postad eller väntande, läggs den inte in en gång till. Det gäller också när du har godkänt
veckan i den lokala Admin. En förfrågan för en artikel som inte är schemalagd eller publicerad väntar, till exempel om
du avpublicerade artikeln innan exporten hann köras. Den läggs in om artikeln schemaläggs igen.

## Det här behöver du göra (i ordning)

Varje steg går att testa för sig. Du kan sluta efter vilket steg som helst.

### 1. Tjänstekonto för exporten → GitHub-hemligheten `FIREBASE_SERVICE_ACCOUNT`

1. Öppna Google Cloud Console för projektet **runes-1656b** och gå till IAM och admin → Tjänstekonton → Skapa
   tjänstekonto. Kalla det `vitki-publicera`.
2. Ge kontot rollen **Cloud Datastore Viewer** (`roles/datastore.viewer`). Exporten behöver bara läsa.
3. Öppna kontot, gå till Nycklar → Lägg till nyckel → JSON. En fil laddas ned.
4. Gå till GitHub → Precatio/runes → Settings → Secrets and variables → Actions → New repository secret.
   Namnet ska vara `FIREBASE_SERVICE_ACCOUNT`, och värdet hela innehållet i JSON-filen.
5. Radera den nedladdade filen.

**Testa:** gå till Actions → "Publicera artiklarna" → Run workflow. Körningen ska bli grön och visa "Inget nytt att
publicera". Om något hade ändrats i Firestore blir det i stället en commit, och "Webbplatsen" byggs.

### 2. Bluesky → GitHub-hemligheterna `BLUESKY_HANDLE` och `BLUESKY_APP_PASSWORD`

1. Skapa ett nytt applösenord i Bluesky under Inställningar → Integritet och säkerhet → Applösenord. Kalla det
   "GitHub Actions". Använd ett eget lösenord, så att det kan återkallas utan att den lokala appen påverkas.
2. Lägg till två repository secrets i GitHub: `BLUESKY_HANDLE` = `vitkirunor.bsky.social` och
   `BLUESKY_APP_PASSWORD` = applösenordet.

**Testa:** gå till Actions → "Bluesky-kön" → Run workflow. Notisen ska säga "…den lokala appen postar kön; GitHub Actions
gör ingenting". Det betyder att hemligheterna finns och att brytaren fortfarande står på lokal.

### 3. Låt GitHub Actions posta Bluesky-kön

Gör det här på datorn, före kl. 18 eller efter att dagens inlägg har gått ut:

```
git pull --rebase
# ändra "postar": "lokal" till "postar": "ci" i data/bluesky/postning.json
git commit -m "Bluesky-kön postas av GitHub Actions" data/bluesky/postning.json
git push
```

Den lokala appens tråd läser filen före varje försök och slutar posta direkt. Om du vill stänga av den lokala tråden
helt, oberoende av filen, lägger du till `BLUESKY_LOCAL=0` i `.env`.

**Testa:** dagen efter, efter kl. 18:10 svensk tid, ska det finnas en grön körning av
"Bluesky-kön" och ett nytt inlägg på Bluesky. `ko.json` på GitHub ska då ha fått `posted` och `posted_at`. Kör
`git pull` innan du lägger till nya inlägg i kön, eftersom GitHub Actions committar den.

### 4. Inloggning på /redaktion → repository-variablerna `FIREBASE_WEB_API_KEY` och `FIREBASE_WEB_APP_ID`

1. Gå till GitHub → Settings → Secrets and variables → Actions → fliken **Variables** → New repository variable.
2. Skapa `FIREBASE_WEB_API_KEY` med samma värde som `NEXT_PUBLIC_FIREBASE_API_KEY` i `web/.env.local`.
3. Skapa `FIREBASE_WEB_APP_ID` med samma värde som `NEXT_PUBLIC_FIREBASE_APP_ID` i `web/.env.local`.

Värdena är Firebase-webbappens publika konfiguration. De hamnar i sidans kod, så de är variabler och inte hemligheter.

Om API-nyckeln har webbplatsbegränsningar (Google Cloud Console → API:er och tjänster → Inloggningsuppgifter) måste du
lägga till `https://vitkirunor.se/*`.

**Testa:** gå till Actions → "Webbplatsen" → Run workflow och öppna sedan https://vitkirunor.se/redaktion/. Knappen
"Logga in med Google" ska synas i stället för "inte aktiverad".

### 5. Godkänn domänen i Firebase Auth

Gå till Firebase Console → runes-1656b → Authentication → Settings → Authorized domains → Add domain och lägg till
`vitkirunor.se`.

**Testa:** logga in på /redaktion. Inloggningsfönstret ska öppnas och stängas. Sidan säger då "Redaktionen är inte
aktiverad än – Firestore nekade åtkomst". Det är väntat tills steg 6 är gjort.

### 6. Driftsätt säkerhetsreglerna

Reglerna ligger i `web/firestore.rules`. Ditt konto (uid i `ADMIN_UIDS`) får läsa artiklarna och ändra deras
publiceringsfält. Det är driftsatt sedan november 2026. Fliken **Veckan** behöver två regler till, som tillkom
2026-11-11 och ännu inte är driftsatta:

- **`publiceringsschema`**: ditt konto får läsa planen. Ingen får skriva i den från en webbläsare, och bara
  synkskriptet skriver.
- **`bluesky_forfragningar`**: ditt konto får läsa och skapa förfrågningar. Skapandet kontrolleras: exakt fälten
  `slug`, `datum`, `text`, `tags`, `en`, `created` och `by`, där dokumentets id är adressen. Texten får vara högst 400
  tecken och taggarna högst 8. `datum` är en datumsträng, `en` är true, `created` är serverns tid och `by` är ditt uid.
  Ingen får ändra eller ta bort en förfrågan.

Allt annat är oförändrat, och emulatortestet visar det. Innan reglerna är driftsatta säger fliken Veckan
"Publiceringsschemat kunde inte läsas … Firestore nekade åtkomst". Resten av /redaktion fungerar som förut.

```
cd tests/firestore_rules && npm ci && npm test        # 60 kontroller i emulatorn (kräver Java 21)
cd ../../web && npx firebase-tools@14 login            # om du inte redan är inloggad
# OBS: "--only firestore:rules" hoppar tyst över databasen vitki (säger ändå Deploy complete) – använd "--only firestore"
npx firebase-tools@14 deploy --only firestore --project runes-1656b
```

**Testa:**

1. Ladda om /redaktion. Översikten ska visa utkast, det schemalagda och det senast publicerade.
2. Skapa ett testutkast i den lokala appen.
3. På /redaktion: Schemalägg testutkastet till en tid långt fram. Kontrollera att den lokala Admin visar det som
   schemalagt. Avpublicera det sedan.
4. Ta bort testutkastet i den lokala appen.
5. Öppna fliken **Veckan**. Vecka 47 ska visa Freja (tis 17 nov) och De gamla landen: Skåne (fre 20 nov) som utkast med
   bock, och med pilen ska vecka 48 visa lerkanten och Fyra stenar för två barn. Godkänn inget som ett test. Det
   schemalägger artiklarna på riktigt och skickar Bluesky-förfrågan, och förfrågan kan inte tas bort från webben. Gör
   det först på måndagen, när veckan ska ut.

## Rulla tillbaka

- **Exporten i CI:** ta bort hemligheten `FIREBASE_SERVICE_ACCOUNT`, så skriver jobbet bara en notis. Du kan också
  stänga av arbetsflödet under Actions → "Publicera artiklarna" → ⋯ → Disable workflow. Nyckeln återkallar du under
  Google Cloud Console → tjänstekontot → Nycklar → ta bort.
- **En felaktig export på webbplatsen:** rätta artikeln i Firestore (i den lokala appen eller på /redaktion) först.
  Nästa körning exporterar då om den. `git revert <commit>` hjälper bara tills nästa körning.
- **Bluesky:** sätt `"postar": "lokal"` i `data/bluesky/postning.json`, committa och pusha. Då postar den lokala appen
  igen. Du kan också ta bort hemligheterna eller återkalla applösenordet i Bluesky.
- **Säkerhetsreglerna:** återställ den föregående versionen under Firebase Console → Firestore → databasen vitki → Rules
  → historiken. Det går också från terminalen:
  `git show 5502d71:web/firestore.rules > web/firestore.rules && cd web && npx firebase-tools@14 deploy --only firestore --project runes-1656b`.
  Utan de nya reglerna visar /redaktion "inte aktiverad", och allt annat fungerar som förut.
- **Veckan på /redaktion:** schemaläggningen gör du om på /redaktion (Avpublicera) eller i den lokala appen. Bluesky-
  inlägget stryker du ur `data/bluesky/ko.json` (committa och pusha). Det kommer inte tillbaka, eftersom förfrågan
  står som hanterad i `data/bluesky/webbforfragningar.json`. Om exporten inte har hunnit hantera förfrågan än tar du
  bort dokumentet i Firebase Console → Firestore → vitki → `bluesky_forfragningar`.
- **/redaktion:** ta bort variablerna `FIREBASE_WEB_API_KEY` och `FIREBASE_WEB_APP_ID` och bygg om webbplatsen. Då
  säger sidan "inte aktiverad".
- **En ändring gjord på /redaktion:** gör om den åt andra hållet, på /redaktion eller i den lokala appen. Bara
  publiceringsfälten kan ha ändrats. Observera att den lokala appens säkerhetskopior (`data/backup/posts`) inte
  fångar ändringar som görs på webben.

## Bra att veta

- **Nya R-figurer** kan bara den lokala appen göra. CI-exporten räknar de WebP-filer som redan finns i
  `web/public/figurer` som befintliga. När en artikel med en ny figur går live stoppar kontrollen därför hela exporten
  ("Figurer saknas"), och körningen blir röd var 30:e minut tills figuren har kommit ut. Starta den lokala appen efter
  publiceringstiden, så exporterar och pushar den figuren. Det går också med
  `git pull --rebase && .venv/bin/python -m src.site_export --push`.
- **Två som pushar:** både GitHub Actions och den lokala appen committar till main. Kör `git pull --rebase` innan du
  pushar från datorn.
  - Om den lokala appens automatiska push nekas visar Admin "Committat men inte pushat". Kör då `git pull --rebase`.
  - Om det blir en konflikt i `web/content/articles.json` eller `web/public/artiklar-sok.json` kör du
    `git rebase --skip` på artikelcommitten. CI exporterar om från Firestore.
  - Kör därefter `.venv/bin/python -m src.site_export --push` om commiten innehöll nya figurer.
- **Tidsprecision:** GitHub kan försena schemalagda körningar med 5–30 minuter. En schemalagd artikel går därför ut
  inom ungefär en halvtimme till en timme efter sin tid. Vill du ha den på minuten kan du ha den lokala appen igång,
  eller köra "Publicera artiklarna" för hand.
- **Förstagångspublicering på /redaktion** sparar inte `snapshot`, det vill säga mönstrens läge som utkastet till
  månadens fynd jämförs med. Publicera en sådan artikel i den lokala appen om jämförelsen spelar roll.
- **Kostnad:** exporten läser cirka 70 artiklar var 30:e minut, alltså cirka 3 400 läsningar om dygnet, plus
  sidvisningarna en gång om dygnet. Dessutom läses alla Bluesky-förfrågningar i varje körning. Med två om veckan blir
  det cirka 100 om året, alltså upp till cirka 4 800 läsningar om dygnet efter ett år. Firestores gratiskvot är
  50 000 läsningar om dygnet.
- **Bluesky-kön och två som committar:** "Bluesky-kön" (kl. 18) och "Publicera artiklarna" kan båda ändra `ko.json`. Om
  en förfrågan läggs in i samma minut som kvällens inlägg markeras som postat kan Bluesky-jobbets `git pull --rebase`
  få en konflikt. Jobbet blir då rött med instruktionen att fylla i `posted` för hand. Det är osannolikt, eftersom
  exporten körs :07 och :37, men godkänn helst inte veckan precis kring kl. 18.
- **Om exportens kontroll stoppar** (till exempel "Figurer saknas") väntar också Bluesky-förfrågningarna, eftersom
  körningen avbryts före commiten. De läggs in vid nästa körning som går igenom.
- **Schemalagda arbetsflöden** stängs av av GitHub efter 60 dagar utan aktivitet i repot. Om det händer slår du på dem
  igen under Actions.
- **Tester:**
  - `tests/test_ci_publicera.py` testar exporten, Bluesky-logiken, att förfrågningarna från /redaktion slås in i kön
    (mot en falsk Firestore), synkskriptet och att `requirements-publicera.txt` är kopierad ur `requirements.lock`.
  - `tests/test_blog_week.py` testar den lokala Veckans publiceringar och samma insättning i kön.
  - `web/scripts/redaktion.test.mjs` testar fälten /redaktion skriver, svensk tid, veckans fönster och avvisningar
    (samma som `blog_week.py`), etiketterna, Bluesky-förfrågans fält och säkerhetspolicyn.
  - `tests/firestore_rules` testar reglerna i emulatorn.
  - Alla körs i `.github/workflows/ci.yml`.
