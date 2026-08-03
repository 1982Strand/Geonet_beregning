# Overlevering: Trafikklasse-projektet (kontekst til ny chat)

**Formål med dette dokument:** samle hele konteksten fra samtaleforløbet, så arbejdet kan fortsættes i en ny chat / på en anden konto. Alle nævnte filer ligger i repoet og følger med. Læs dette først, åbn derefter de nævnte filer.

---

## 1. Kort om projektet

`geonet_beregning` er en Streamlit-app (Byggros) der dimensionerer **MSL-opbygninger** (mekanisk stabiliseret bærelag med geonet). I dag dimensioneres ud fra **belastningsklasser** (1–6), der hver svarer til et krav om overflademodul Eo (30–150 MPa). Beregningen er opslag i GS-GRID/Tensar-**designdiagrammer**: `(Eu, Eo) → bærelagstykkelse` for uarmeret / 1 net / 2 net, plus φ- og netkorrektioner.

**Målet med forløbet:** gøre det muligt at dimensionere ud fra **Vejdirektoratets trafikklasser** (T1–T7) *ved siden af* belastningsklasserne — så en rådgiver kan dimensionere i VejDim, indtaste de fundne ubundne lagtykkelser i appen og se geonet-reduktionen. Kravet fra brugeren: koblingen må **ikke være et gæt**, den skal kunne dokumenteres med beregning/tilbageberegning.

**Status:** Fase A (VejDim-kørsler) og Fase B (korrelation + dokumentation) er **færdige**. Fase C (app-integration) er **ikke påbegyndt** — afventer brugerens godkendelse af korrelationstabellen.

---

## 2. Hvad vi lærte om VejDim's metode (baggrund)

VejDim er Vejdirektoratets analytisk-empiriske dimensioneringsprogram (afløser MMOPP's niveau 2). Nøglepunkter (fuldt uddybet i `vejdim_flow.html`):

- **Tre fejlmåder tjekkes:** asfalt-udmattelse (træktøjning), deformation af ubundne lag/underbund (trykspænding), og frosthævning (tabelopslag).
- **To tal pr. kriterium:** et *tilladeligt* (formel/opslag) og et *aktuelt* (beregnet i en lineærelastisk lagmodel). Lagtykkelser justeres til aktuel ≤ tilladelig.
- **Kaskadeprincip:** hvert lags tykkelse beskytter grænsefladen *under* det. Asfalt = tøjningskriterie; ubundne lag = bæreevnekriterie (σ_z,till på lagets top, med lagets eget E).
- **Kriterier (håndbog 2022/rev. 2025):** σz,till = 0,086·(E/160)^1,06·(NÆ10/10⁶)^−0,25 ; εh,till = 250·(NÆ10/10⁶)^−0,191 µstr.
- **Responsmodel:** fuld lagteori (WESDEF/Burmister) eller Odemark ækvivalente tykkelser; last = Æ10 tvillinghjul + 20 % stødtillæg (a ≈ 107–117 mm).
- **Praktisk erfaring fra kørslerne:** BSM-lags tykkelse er programstyret (kan ikke låses, kun E). Bundne lags tykkelse er programstyret ved T4–T6 (asfaltkriteriet binder den stramt — låser man en anden værdi fås "a solution … could not be found"). GAB kan låses ved T2/T3.

Kildedokumenter (i `Dokumenter og data/VD/`): håndbogen (`Dimensionering_befaestelser_og_forstaerkningsbelaegninger.md`), MMOPP Brugervejledning 2007 (PDF), Bolet & Busch "Vejbefæstelsers dimensionering" AAU 2016 (PDF, kap. 7 = den manuelle metode med regneeksempel).

---

## 3. Filer lavet i forløbet (alle i repoet)

| Fil | Formål | Status |
|---|---|---|
| `vejdim_flow.html` | Selvstændigt, redigerbart flowdiagram over VejDim-dimensionering + "under hjelmen"-forklaringer af hvert trin. Offline, ingen afhængigheder. | Færdig |
| `Dokumenter og data/Trafikklasse_bro_feasibility.md` | **Teoretisk** feasibility: MET/Odemark-beregnet T×Eu-matrix + bro-princip. Lavet før VejDim-kørslerne. | Færdig |
| `Dokumenter og data/VejDim_koerselsopskrift.md` | Præcis opskrift på VejDim-kørslerne (opsætning, faste asfaltpakker pr. klasse, låst-vs-frit-logik). | Færdig |
| `Dokumenter og data/VejDim_koersler_skema.csv` | Runde 1: 36 celler, standard-E. **Gyldige herfra: T1, T5, T6** (T2–T4 afløst af runde 2). | Udfyldt |
| `Dokumenter og data/VejDim_koersler_skema_runde2.csv` | Runde 2: 18 celler = **T2, T3, T4** (rene GAB-kørsler). | Udfyldt |
| `Dokumenter og data/Korrelation_trafikklasse_Eo.md` | **HOVEDLEVERANCEN (Fase B):** korrelationstabellen Eo_ækv(T,Eu), reduktionstabel, konsistenschecks, zoner, forbehold, køreplan for Fase C. | Færdig |
| `Dokumenter og data/korrelation_final.py` | Reproducerbart script bag Fase B (portabelt, repo-relative stier). | Færdig |

**Bemærk:** der lå tidligere en serie med manuelt overskrevet asfalt-E = 1500 MPa — den er **forkastet** (systematisk konservativ) og erstattet af standard-E-kørslerne. Nævnes kun for historik.

---

## 4. Korrelationsresultatet (kernen)

**Princip:** VejDim-kørslen placerer driftspunktet (Eu + krævet ubundet tykkelse SG+BL); geonet-diagrammet leverer reduktionen som sin *egen* feltdokumenterede værdi i det punkt. Ingen teoretisk omregning mellem metoderne — to empiriske ben, der mødes ved at matche ubundet tykkelse ved samme Eu. Ækvivalent Eo er kun en indeksværdi ind i diagrammet.

**Eo_ækv(T, Eu)** — MPa ("under"/"over" = uden for diagramdækning):

| T \ Eu | 5 | 10 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| T1 | under | under | 31 | 44 | 63 | 99 |
| T2 | under | 46 | 67 | 86 | 120 | 138 |
| T3 | under | 52 | 76 | 102 | 129 | 144 |
| T4 | 90 | 108 | 135 | 149 | over | over |
| T5 | 124 | 143 | over | over | over | over |
| T6 | 149 | over | over | over | over | over |

**Konklusion:** broen holder i en **kernezone (21/36 celler)** med reduktioner **26–47 % (middel 31 %)** — samme niveau som appens nuværende output. Tabellen er monoton og glat. Uden for kernezonen skal appen afvise: "under" (blød bund/lave klasser → brug belastningsklasse-flow); "over" (stiv bund/høje klasser → konkret VejDim-beregning).

**Tre konsistenschecks bestået:** (1) reduktionerne matcher appens eget bånd; (2) zonegrænserne matcher den uafhængige MET-matrix i feasibility-notatet; (3) mekanisk overflademodul-tilbageberegning giver samme størrelsesorden som Eo_ækv (~1,1).

---

## 5. Vigtige tekniske detaljer for den, der fortsætter

- **`T_BASIS_TABLE` genopbygges** fra `DESIGNDIAGRAM_RAW_TABLES` i `core/data.py:488` — den literale tabel øverst i filen (linje 23–168) er **død kode**. Brug altid den genopbyggede (det gør både appen og korrelations-scriptet).
- Relevante symboler i `core/data.py`: `T_BASIS_TABLE`, `EO_KOLONNER` (=[30,45,60,80,120,150]), `BELASTNINGSKLASSER` (1–6 → Eo), `TRAFIKKOBLING` (data.py:552 — gammel ekspertvurdering, **afløses** af korrelationen), `klasse_til_eo`/`eo_til_klasse`.
- Relevante symboler i `core/calculator.py`: `beregn()` (kerneopslag), `beregn_alle_produkter()`, `_slaa_op()` (skal generaliseres til interpoleret Eo i Fase C).
- Ingen af disse har testdækning ("no covering tests found") — vær forsigtig ved ændringer; lav regressionstjek af `beregn()` før/efter.
- Datasæt-split i korrelationen: **T1/T5/T6 fra runde 1-CSV, T2/T3/T4 fra runde 2-CSV** (håndteret i `korrelation_final.py`).
- Repoet er ret rodet (mange `backup 17.06.26/`-filer i `core/` — ignorér dem; de er stale kopier).

---

## 6. Næste skridt — Fase C (app-integration), ikke påbegyndt

Detaljeret køreplan i `Korrelation_trafikklasse_Eo.md` §9. Kort:
1. `core/data.py`: `KORRELATION_T_EO = {(T,eu): eo_ækv}` (fra tabel i §4) + zonemarkering + `TRAFIKKLASSER`-metadata.
2. `core/calculator.py`: interpolerende Eo-opslag + `beregn_alle_produkter_trafikklasse(t_klasse, eu, …)` der genbruger eksisterende flow.
3. `app.py`: ny indgang "Trafikklasse (Vejdirektoratet)" **ved siden af** belastningsklasse; viser Eo_ækv + zone-beskeder.
4. `core/validators.py` + `core/rapport.py`: validering mod gyldighedszone + ny rapporttekst (grundlag: vejregel + dette notat + feltforsøg; frost-forbehold).

**Beslutninger der udestår før Fase C:** (a) brugerens godkendelse af korrelationstabellen; (b) Eu-interpolation mellem de 6 værdier {5,10,15,20,30,40} eller lås til dem i v1; (c) hvordan frost-gulvet (uden for korrelationen) skal vises i UI/rapport.

---

## 7. Sådan genkører du korrelationen

```
cd C:\geonet_beregning
.venv\Scripts\python.exe "Dokumenter og data\korrelation_final.py"
```

Scriptet læser de to CSV'er + appens live diagramtabel og printer korrelations-/reduktionstabel + konsistenschecks. Retter du en celle i en CSV, afspejles det ved næste kørsel.

---

## 8. Brugerpræferencer (fra forløbet)

- Skriver og vil have leverancer på **dansk**.
- Tjekker selv i browser — jeg leverer koden, brugeren verificerer (gælder `vejdim_flow.html`).
- Vil have **dokumenterbare, ikke-gættede** sammenhænge; sætter pris på tydelige forbehold.
- App-kode skal ikke røres, før grundlaget er godkendt (vi arbejder i faser).
