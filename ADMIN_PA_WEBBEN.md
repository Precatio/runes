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
| Bluesky-kön (`data/bluesky/ko.json`) | GitHub Actions, `.github/workflows/bluesky.yml` → `scripts/ci_bluesky.py` → `scripts/bluesky_post.py`, **eller** den lokala appens tråd i `api/main.py` | Från kl. 18 svensk tid. Filen `data/bluesky/postning.json` avgör vem som postar |
| Webbadmin `/redaktion` | Den statiska webbplatsen. Google-inloggning (Firebase Auth) och Firestore direkt från webbläsaren, skyddat av `web/firestore.rules` | När du vill |
| Skriva och ändra text, R-figurer, ta bort, veckans artikel, redigera Bluesky-kön | Den lokala appen, som förut | – |

**Exporten i CI** gör samma sak som den lokala appen och använder samma kontroller. Den stoppar om många artiklar skulle
försvinna på en gång eller om figurer saknas. Den committar bara när något har ändrats. Sidvisningarna ("mest lästa")
läses en gång om dygnet, kl. 05:07.

**/redaktion** visar:

- **Översikt**: vad som är schemalagt de närmaste fyra veckorna, antal utkast, det senast publicerade och de senaste
  körningarna i GitHub Actions.
- **Innehåll**: sök och filter (Utkast, Schemalagda, Publicerade, Rapporter). På varje rad finns Förhandsgranska,
  Schemalägg (svensk tid), Publicera nu och Avpublicera.

Sidan ändrar bara fälten `published`, `publishedAt`, `month`, `updatedAt` och `by`, med samma betydelse som när den
lokala appen sparar. Den redigerar aldrig text och tar aldrig bort något, och reglerna tillåter inget annat. En ändring
syns på webbplatsen inom ungefär en halvtimme, eller direkt om den lokala appen är igång.

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

Reglerna ligger i `web/firestore.rules`. Den driftsatta versionen (från 2026-10-22) är identisk med den committade före
den här ändringen. Det enda som är nytt är att ditt konto (uid i `ADMIN_UIDS`) får läsa artiklarna och ändra deras
publiceringsfält. Allt annat är oförändrat, och emulatortestet visar det.

```
cd tests/firestore_rules && npm ci && npm test        # 29 kontroller i emulatorn (kräver Java 21)
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
  sidvisningarna en gång om dygnet. Firestores gratiskvot är 50 000 läsningar om dygnet.
- **Schemalagda arbetsflöden** stängs av av GitHub efter 60 dagar utan aktivitet i repot. Om det händer slår du på dem
  igen under Actions.
- **Tester:**
  - `tests/test_ci_publicera.py` testar exporten, Bluesky-logiken och att `requirements-publicera.txt` är kopierad ur
    `requirements.lock`.
  - `web/scripts/redaktion.test.mjs` testar fälten /redaktion skriver, svensk tid och säkerhetspolicyn.
  - `tests/firestore_rules` testar reglerna i emulatorn.
  - Alla tre körs i `.github/workflows/ci.yml`.
