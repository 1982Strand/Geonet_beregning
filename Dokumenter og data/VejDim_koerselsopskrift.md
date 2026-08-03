# VejDim-kørselsopskrift: standardiseret referencematrix til trafikklasse-korrelationen

**Formål:** 36 VejDim-kørsler (T1–T6 × Eu = 5, 10, 15, 20, 30, 40 MPa) med **standard E-værdier**, som dokumenteret grundlag for korrelationen mellem trafikklasser og appens designdiagrammer (ækvivalent Eo). Resultaterne indtastes i `VejDim_koersler_skema.csv`.

**Forskel fra de første 36 kørsler:** asfaltens E-værdi må **ikke** overskrives manuelt (ikke 1500) — VejDims egne standard-/vægtede værdier skal bruges, så kørslerne svarer til, hvad en rådgiver ville få. Alt andet er som du gjorde det (opsætningen var rigtig tænkt).

---

## Fælles indstillinger (alle 36 kørsler)

| Indstilling | Værdi | Bemærkning |
|---|---|---|
| Belastningsmodel | **Æ10 Tvillingehjul (standard)** | dropdown øverst til højre |
| Hastighed | **60 / 80 km/t** (min/maks) | ingen E-reduktion |
| Afvandingsforhold etableret | **Nej** | irrelevant ved frostsikker — bare konsistent |
| Underbund | **Frostsikker** + E-værdi **manuelt sat til cellens Eu** (5/10/15/20/30/40) | frostsikker fjerner koblingshøjdekravet → kørslen bliver ren bæreevne. Dokumenteret forudsætning, ikke et trick |
| Dimensioneringsperiode / levetidsmål | **20 år** | alle lags levetid ≥ 20 år |
| Asfaltens E-værdier | **VejDims standard** (rør ikke de gule felter) | notér den viste E i skemaet |
| Ubundne lag | **SG II** (E=300) over **BL II U≤3** (E=100) | standard E-værdier |

## Fast asfaltpakke pr. trafikklasse (lås tykkelserne — kun SG og BL justeres)

| T-klasse | Slidlag | Bindelag | Bundet bærelag | Bundet lag: låst eller frit? |
|---|---|---|---|---|
| T1 | 40 mm AB 1000 | — | — (slet laget) | intet låg |
| T2 | 40 mm AB 1000 | 40 mm GAB 0 2000 | 40 mm GAB 0 2000 | **låst** (bindelag + bærelag min. 40 hver) |
| T3 | 40 mm AB 1000 | — | 100 mm GAB 0 2000 | **låst** (intet bindelag nødvendigt) |
| T4 | 40 mm AB 2000 | — | GAB 0 2000, **frit** | **frit** — VejDim beregner; notér tykkelsen |
| T5 | 40 mm AB 2000 | — | GAB I 3000, frit (~130 mm) | frit — færdig i runde 1 |
| T6 | 40 mm SMA 3000 | — | GAB II 3000, frit (~140 mm) | frit — færdig i runde 1 |

**Hvorfor låst vs. frit:** ved T4–T6 er trafikken så høj (lav tilladelig tøjning), at det bundne lags tykkelse er stramt bundet af asfaltkriteriet — låser man en anden værdi, kan asfaltlagets levetid ikke reddes ved at justere de ubundne lag → fejlmeddelelse "a solution … could not be found". Lad derfor feltet stå frit ved T4 (og notér den tykkelse, VejDim beregner). T5/T6 er allerede kørt frit i runde 1 og genbruges. Ved T2/T3 er trafikken lav nok til, at et låst låg går op.

**T2-note:** VejDim kræver et bindelag, når man vælger GAB-bundet bærelag. Vælg GAB 0 2000 til begge og sæt begge på minimum (40 mm hver) → samlet bundet = 40 slid + 40 binde + 40 bærelag = **120 mm**.

**VIGTIGT (erfaring fra runde 1):** GAB-tykkelser skal **skrives ind i feltet** for at være låst — frie felter løses af VejDim selv. **BSM-tykkelsen kan ikke låses** (programstyret; kun E kan overskrives — lad den stå på standard 800): notér den tykkelse, VejDim vælger, i skemaet; cellerne normaliseres bagefter til referencelåget med ækvivalente tykkelsers metode. Kun SG og BL må stå frie.

Noter:
- **T2–T4 bruger BSM 800**, fordi VejDim ikke tilbyder GAB-materialer som bundet bærelag ved disse klasser (materialelisten filtreres efter trafikklasse; GAB I/II er tilgængelige ved T5–T6). Det er acceptabelt: BSM'ens E-værdi skal stå på **standard 800** (ikke overskrives), dens eget kriterium er massivt ikke-styrende (levetid ~32.000 år ved Eu=5), og det ubundne behov styres uændret af σ-kriterierne. Dokumentationsmæssigt noteres: "bundet bærelag = VejDims tilbudte standardmateriale for klassen".
- De låste BSM-tykkelser (125/180/215) svarer til VejDims minimum ved T2 hhv. VejDims egne løsninger ved Eu=40 for T3/T4 i runde 1 — faste, repræsentative værdier pr. klasse.
- **Generelt ved materialevalg:** tilbyder VejDim ikke det foreskrevne materiale ved en klasse, så brug VejDims tilbudte alternativ med standardværdier, lås tykkelsen hele rækken igennem, og notér det i bemærkningsfeltet.

## Runde 2 — de 18 celler der reelt mangler (T2 + T3 + T4)

Efter test i VejDim: GAB kan nu vælges (afløser BSM fra de tidlige kørsler), men **kun T2 og T3 kan få det bundne lag låst** — T4–T6 er stramt bundet af asfaltkriteriet og skal beregnes frit. Endelig arbejdsdeling (`VejDim_koersler_skema_runde2.csv`):

- **T2** (6 celler): GAB 0 2000 som bindelag (40) + bærelag (40), begge låst.
- **T3** (6 celler): GAB 0 2000 bærelag låst 100 mm, intet bindelag.
- **T4** (6 celler): GAB 0 2000 bærelag **frit** — notér den tykkelse, VejDim beregner.
- **Gyldige fra runde 1 (køres ikke igen):** T1 (intet bundet lag), T5 (GAB I 3000 frit ~130), T6 (GAB II 3000 frit ~140). Deres bundne lag er allerede VejDims kanoniske svar — et frit felt ville bare give det samme.

De tidlige BSM-kørsler for T2–T4 udgår (afløst af de rene GAB-kørsler ovenfor).
- Rødt udråbstegn ved tykkelse (maks pr. udlagt lag) er en **udførelses-note** — laget udlægges i praksis i flere lag; det påvirker ikke beregningen. Ignorér det i kørslerne.
- Hvis et lags **levetid** står langt over 20 år (fx slidlag ved T1), er det fint — pakken er bare ikke styrende.

## Fremgangsmåde pr. celle (36 gange)

VejDim justerer selv de lag, hvis tykkelse **ikke** er overskrevet — udnyt det:

1. Sæt trafikklassen til kolonnens T-klasse og underbundens E til rækkens Eu.
2. Indsæt den faste asfaltpakke fra tabellen ovenfor (tykkelserne overskrives/låses). Rør ikke E-felterne.
3. **Foretræk VejDims egen løsning:** lad både SG- og BL-tykkelsen stå frie (nulstil evt. overskrivning) og tryk Beregn. Udfylder VejDim selv begge felter, er cellen færdig — notér "VejDim-løst" i bemærkning.
4. **Løser VejDim kun det nederste frie lag:** sæt SG trinvist (hele 10 mm), lad BL være fri, og tryk Beregn pr. trin. Find den **mindste SG**, hvor beregningen lykkes og bundsikringslagets levetid er ≥ 20 år — BL-tykkelsen finder VejDim selv (underbundens levetid lander netop ≥ 20).
5. Kontrollér at **alle** lags levetid er ≥ 20 år. Er et lag i den faste pakke under 20 (burde ikke ske), notér det i bemærkningsfeltet i stedet for at ændre pakken.
6. Overfør til skemaet: t_SG, t_BL, den viste asfalt-E, styrende lag (levetid tættest på 20), koblingshøjden og evt. bemærkning.

Rækkefølgen (SG før BL) følger metodens kaskadeprincip: SG beskytter toppen af BL, BL beskytter underbunden.

## Kanttilfælde

- **"A solution that meets the lifetime criteria could not be found":** de låste øvre lag kan ikke beskytte snittet under dem — spændingen på toppen af et lag bestemmes kun af lagene ovenover, så intet nedre lag kan reparere det. Øg SG ét trin (eller løsn en overskrevet tykkelse) og beregn igen. Notér den mindste SG, der virker (eksempel: T1/Eu=5 fejler ved SG=100, virker ved SG=110).
- **BL-rækkens levetid ligger langt over 20** selv ved mindste SG: helt fint — kriterierne er potensfunktioner, så levetiden hopper stejlt. Kravet er kun ≥ 20.
- **Kan SG/BL ikke komme under en minimumsgrænse** VejDim håndhæver (fx SG ≥ 100 mm): notér den håndhævede værdi + "min-styret" i bemærkning.
- **Meget lange levetider** i BL-rækken selv ved tynd SG (typisk ved stiv underbund): vælg mindste tilladte SG og notér "BL ikke styrende".
- **T1 kræver mere end i første runde:** standardværdien for AB 1000 er E=1000 — *lavere* end de 1500, der var sat manuelt i de oprindelige kørsler — så T1-cellerne bliver tykkere nu. Omvendt bliver T3–T6 tyndere (standard 2000–3000 > 1500). Det er forventet og korrekt.
- **T7 køres ikke** — klassen er åben opad og indgår ikke i korrelationen (appen vil henvise til konkret VejDim-beregning).

## Dokumentationsspor

Gem gerne et skærmbillede pr. celle som i den oprindelige Excel — de bruges som bilag til korrelationsnotatet. Navngiv fx `T4_Eu10.png`.
