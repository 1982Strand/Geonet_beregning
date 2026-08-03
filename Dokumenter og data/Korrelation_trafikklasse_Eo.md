# Korrelation: VejDims trafikklasser → geonet-appens designdiagrammer

**Dato:** 8. juli 2026 · **Status:** dokumentationsgrundlag for trafikklasse-indgang i appen · Fase B afsluttet
**Grundlag:** 36 VejDim-kørsler (standard E-værdier) udført af DST, juli 2026.

---

## 1. Hovedresultat

Der KAN etableres en dokumenterbar bro fra Vejdirektoratets trafikklasser til appens designdiagrammer — **ikke ved at gætte, men ved at lade to uafhængige, empiriske kilder mødes:**

1. **VejDim-kørslerne** (vejreglens metode) fastlægger, hvor tykt et ubundet lag (SG+BL) en given trafikklasse kræver ved en given underbund Eu.
2. **Geonet-designdiagrammerne** (GS-GRID/Tensar-feltforsøg) fastlægger, hvor meget et geonet kan reducere netop den tykkelse.

Broens eneste led er at **finde det driftspunkt (Eu, tykkelse) i diagrammet, som svarer til VejDims krav** — derefter er reduktionen diagrammets egen, feltdokumenterede værdi. Der indgår ingen teoretisk omregning imellem de to metoder.

**Broen holder i en veldefineret kernezone** (21 af 36 celler): typisk trafikklasse T2–T4 ved middel underbund og de lave trafikklasser ved stiv underbund. Her giver den reduktioner på **26–47 % (middel 31 %)** — samme niveau som appens nuværende belastningsklasse-beregning. Uden for kernezonen (meget blød eller meget stiv underbund kombineret med yderklasserne) falder driftspunktet uden for diagrammernes gyldighedsområde, og broen skal afvise med besked frem for at ekstrapolere.

## 2. Datagrundlag

36 kørsler = T1–T6 × Eu {5, 10, 15, 20, 30, 40 MPa}, alle med:
- Belastningsmodel Æ10 tvillingehjul (standard), 60–80 km/t, afvanding "Nej".
- Underbund "Frostsikker" med **manuelt overskrevet E = celle-Eu** — fjerner koblingshøjdekravet, så kørslen bliver ren bæreevne (dokumenteret forudsætning).
- Levetidsmål 20 år; alle lag ≥ 20 år; SG II (E=300) over BL II U≤3 (E=100), justeret af VejDim.
- **Standard asfalt-E** (ikke overskrevet — modsat en tidligere serie med manuelt E=1500).

Fast asfaltpakke pr. klasse (bundet lag låst hvor muligt, ellers VejDim-beregnet):

| Klasse | NÆ10 (20 år) | Slidlag + bundet bærelag | Bundet lag |
|---|---|---|---|
| T1 | ~0,002 mio. | 40 AB 1000 | intet |
| T2 | ~0,15 mio. | 40 AB 1000 + 40 GAB 0 bindelag + 40 GAB 0 bærelag | 120 mm (låst) |
| T3 | ~0,37 mio. | 40 AB 1000 + 100 GAB 0 2000 | 140 mm (låst) |
| T4 | ~1,46 mio. | 40 AB 2000 + ~118 GAB 0 2000 | VejDim-beregnet |
| T5 | ~3,6 mio. | 40 AB 2000 + ~130 GAB I 3000 | VejDim-beregnet |
| T6 | ~6,0 mio. | 40 SMA 3000 + ~140 GAB II 3000 | VejDim-beregnet |

Kilder: `VejDim_koersler_skema.csv` (T1/T5/T6) + `VejDim_koersler_skema_runde2.csv` (T2/T3/T4); opskrift i `VejDim_koerselsopskrift.md`. En vigtig erfaring undervejs: BSM- og højklasse-GAB-lags tykkelser er programstyrede i VejDim (kan ikke låses) — de er derfor VejDims egne kanoniske værdier.

## 3. Metoden (hvorfor det ikke er et gæt)

For hver celle:
1. Ubundet total fra VejDim: `t_ubundet = t_SG + t_BL`.
2. **Driftspunkt:** find den Eo-kolonne i appens diagram (`T_BASIS_TABLE`, uarmeret), hvis tykkelse ved samme Eu netop er lig `t_ubundet` (lineær interpolation mellem kolonnerne). Dette giver den ækvivalente Eo, `Eo_ækv(T, Eu)` — kun en indeksværdi, ikke en fysisk påstand.
3. **Reduktion:** aflæs den armerede tykkelse (1 net, referenceprodukt) ved (Eo_ækv, Eu). Da Eo_ækv per konstruktion giver `uarmeret = t_ubundet`, er reduktionen **identisk med diagrammets egen reduktion** i det punkt:
   `reduktion = (t_ubundet − armeret) / t_ubundet = (uarmeret − armeret) / uarmeret`.

Pointen: VejDim-kørslen bruges *kun* til at placere driftspunktet. Selve reduktionen er 100 % geonet-diagrammets feltdokumenterede tal. De to metoders kriterier blandes aldrig.

## 4. Korrelationstabel: Eo_ækv(T, Eu)

Ækvivalent Eo (MPa) — indeks til diagrammet. "under" = VejDim kræver mindre end diagrammets Eo=30-kurve; "over" = mere end Eo=150-kurven.

| T \ Eu | 5 | 10 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| **T1** | under | under | 31 | 44 | 63 | 99 |
| **T2** | under | 46 | 67 | 86 | 120 | 138 |
| **T3** | under | 52 | 76 | 102 | 129 | 144 |
| **T4** | 90 | 108 | 135 | 149 | over | over |
| **T5** | 124 | 143 | over | over | over | over |
| **T6** | 149 | over | over | over | over | over |

Tabellen er **monoton og glat** i begge retninger (Eo_ækv stiger med både trafikklasse og Eu) — et tegn på at koblingen er velopført og ikke støj.

## 5. Reduktionstabel (appens kerneoutput, 1 net, referenceprodukt)

Reduktion af det ubundne lag (%). "—" = uden for kernezonen eller uden 1-net-data i diagrammet ved den ækvivalente Eo.

| T \ Eu | 5 | 10 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| **T1** | — | — | 47 | — | — | — |
| **T2** | — | 33 | 30 | 29 | 31 | — |
| **T3** | — | 31 | 31 | 28 | 30 | — |
| **T4** | 26 | 30 | 29 | 28 | — | — |
| **T5** | 26 | 31 | — | — | — | — |
| **T6** | 31 | — | — | — | — | — |

Middel 31 %, spænd 26–47 %, n=16 celler. Med 2 net vil reduktionen være større (aflæses tilsvarende i diagrammets 2-lags-kolonne).

## 6. Konsistenschecks

1. **Reduktionsniveauet matcher appen selv.** De 26–47 % ligger i samme bånd, som appens direkte belastningsklasse-dimensionering giver — det er den samme fysiske geonet-effekt, blot indekseret via trafikklasse i stedet for belastningsklasse.
2. **Zonegrænserne matcher den uafhængige beregning.** "under"/"over"-mønstret er praktisk talt identisk med den teoretisk beregnede MET-bromatrix i `Trafikklasse_bro_feasibility.md` (samme nedre-venstre og øvre-højre afskæring), selvom de to er fremkommet helt uafhængigt (empiriske VejDim-kørsler vs. håndberegnet Odemark-metode).
3. **Mekanisk plausibilitet.** En uafhængig to-lags overflademodul-tilbageberegning (Odemark/Boussinesq) af VejDim-stakken (SG 300 / BL 100 / underbund Eu) giver i kernezonen en surface-modulus i samme størrelsesorden som Eo_ækv (middelforhold ~1,1). Koblingen lander altså i et fysisk fornuftigt leje. Den er dog **ikke** en stram mekanisk identitet (stort spænd i yderpunkterne) — hvilket netop understreger, at reduktionen hviler på diagrammets tykkelsesrelation, ikke på en Eo-lighed.

## 7. Zoner — og hvad appen skal gøre

- **Kernezone ("ok" i tabel 4, 21 celler):** dimensionér som beskrevet — vis reduktion pr. produkt via Eo_ækv. Dette er det kommercielt relevante område (middel-tung trafik på blød–middel bund).
- **Zone "under" (blød bund × lave klasser):** VejDim kræver mindre end diagrammets mest konservative kurve. Appen bør melde: *"VejDim giver allerede en tyndere opbygning end designdiagrammernes område — brug belastningsklasse-flowet."* (I praksis vil frost-gulvet ofte styre disse celler alligevel.)
- **Zone "over" (stiv bund × høje klasser):** VejDims ubundne krav overstiger diagrammernes tykkelsesområde ved høj Eu. Appen bør **afvise med besked** frem for at ekstrapolere. Reduktionspotentialet er her lavest, og en konkret VejDim-beregning er nødvendig.

## 8. Forbehold

1. **VejDim kender ikke geonet.** Reduktionen kan aldrig begrundes inden for vejreglen — den hviler på GS-GRID/Tensar-feltforsøgene. Rapporttekst skal (som i dag) gøre dette eksplicit.
2. **MSL erstatter SG+BL samlet.** Diagrammets tykkelse er ét mekanisk stabiliseret lag; VejDim-referencen er SG+BL. Sammenligningen sker på total ubundet tykkelse. Materialekravet til MSL-laget (SG-kvalitet) er strengere end BL, hvilket er konservativt.
3. **Frost/koblingshøjde ligger uden for korrelationen.** Kørslerne er lavet frostsikkert (ren bæreevne). En geonet-reduceret opbygning må ikke bringe den samlede højde under koblingshøjden for frosttvivlsom/frostfarlig bund (Fig. 5.3) — håndteres som separat kontrol/informationsnote i appen.
4. **1-net-huller i kernezonen.** Nogle "ok"-celler mangler 1-net-data ved den ækvivalente Eo (diagrammets 1-lags-kolonne er tom ved høj Eo / tynd opbygning) — reduktionen kan ikke aflæses der (markeret "—" i tabel 5).
5. **T7 ikke medtaget** (åben klasse) — appen henviser til konkret VejDim-beregning.
6. **Følsomhed for asfaltpakken.** Eo_ækv afhænger let af den valgte (faste) asfaltpakke pr. klasse. Pakkerne her er VejDims kanoniske valg; væsentligt anderledes pakker (fx tykkere bundet bærelag) ville flytte de ubundne krav og dermed Eo_ækv. Dette er en dokumenteret forudsætning, ikke en fejlkilde.

## 9. Anbefaling til app-integration (Fase C)

1. **core/data.py:** `KORRELATION_T_EO = {(T, eu): eo_ækv}` (fra tabel 4) + zonemarkering + kildehenvisning til dette notat; `TRAFIKKLASSER`-metadata (NÆ10/år). `TRAFIKKOBLING` markeres som afløst.
2. **core/calculator.py:** interpolerende Eo-opslag (generalisering af `_slaa_op`) + `beregn_alle_produkter_trafikklasse(t_klasse, eu, ...)` der slår Eo_ækv op og genbruger eksisterende flow (φ-/netkorrektioner, placering, gruppering uændret).
3. **app.py:** valgmulighed "Trafikklasse (Vejdirektoratet)" ved siden af belastningsklasse; viser Eo_ækv + dokumentationsreference; zone-beskeder ("under"/"over").
4. **core/validators.py:** valider (T, Eu) mod korrelationstabellens gyldighedszone.
5. **core/rapport.py:** ny standardtekst (grundlag: vejreglens kriterier + dette notat + feltforsøgsdokumentation; frost-forbehold).
6. Eu-interpolation mellem tabellens 6 værdier afklares under implementering (v1 kan låse til {5,10,15,20,30,40}).

---

*Kilder: VejDim (Vejdirektoratet); Håndbog "Dimensionering af befæstelser og forstærkningsbelægninger" (jan. 2022/rev. aug. 2025); Bolet & Busch: "Vejbefæstelsers dimensionering" (AAU 2016) kap. 7; appens `core/data.py` designdiagrammer. Beregningsscripts: scratchpad `korrelation_final.py`, `bro_matrix.py` (session-arbejdsfiler). Datasæt: `VejDim_koersler_skema.csv`, `VejDim_koersler_skema_runde2.csv`.*
