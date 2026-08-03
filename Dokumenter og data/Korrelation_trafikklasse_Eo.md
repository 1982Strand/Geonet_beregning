# Korrelation: VejDims trafikklasser → geonet-appens designdiagrammer

**Status:** dokumentationsgrundlag for trafikklasse-indgangen i appen (implementeret).
**Grundlag:** 36 VejDim-kørsler med standard E-værdier, udført af DST, juli 2026.
**Aktuelle tal:** dette notat indeholder bevidst **ingen talttabeller** — de ville
blive forældede, hver gang datagrundlaget rettes. Kørslerne ligger i appens
sektion **🚦 Trafikklasse-korrelation**, hvor de kan ses og redigeres direkte, og
hvor de afledte tal (ækvivalent Eo, reduktioner, zoner) altid vises aktuelt.

---

## 1. Hovedresultat

Der kan etableres en dokumenterbar bro fra Vejdirektoratets trafikklasser til
appens designdiagrammer — **ikke ved at gætte, men ved at lade to uafhængige,
empiriske kilder mødes:**

1. **VejDim-kørslerne** (vejreglens metode) fastlægger, hvor tykt et ubundet lag
   (SG+BL) en given trafikklasse kræver ved en given underbund Eu.
2. **Geonet-designdiagrammerne** (GS-GRID/Tensar-feltforsøg) fastlægger, hvor
   meget et geonet kan reducere netop den tykkelse.

Broens eneste led er at **finde det driftspunkt (Eu, tykkelse) i diagrammet, som
svarer til VejDims krav** — derefter er reduktionen diagrammets egen,
feltdokumenterede værdi. Der indgår ingen teoretisk omregning mellem de to
metoder.

**Broen holder i en veldefineret kernezone.** Med det oprindelige datagrundlag
(juli 2026) var det 21 af 36 celler — typisk trafikklasse T2–T4 ved middel
underbund og de lave klasser ved stiv underbund — med reduktioner på
**26–47 % (middel 31 %)**, altså samme niveau som appens
belastningsklasse-beregning. Uden for kernezonen falder driftspunktet uden for
diagrammernes gyldighedsområde, og appen afviser med besked frem for at
ekstrapolere. Det præcise antal celler afhænger af det aktuelle datagrundlag og
ses i appen.

## 2. Datagrundlag

36 kørsler = T1–T6 × Eu {5, 10, 15, 20, 30, 40 MPa}, alle med:

- Belastningsmodel Æ10 tvillingehjul (standard), 60–80 km/t, afvanding "Nej".
- Underbund "Frostsikker" med **manuelt overskrevet E = celle-Eu** — fjerner
  koblingshøjdekravet, så kørslen bliver ren bæreevne (dokumenteret forudsætning).
- Levetidsmål 20 år; alle lag ≥ 20 år; SG II (E=300) over BL II U≤3 (E=100),
  justeret af VejDim.
- **Standard asfalt-E** (ikke overskrevet — modsat en tidligere, forkastet serie
  med manuelt E=1500, som var systematisk konservativ).

Fast asfaltpakke pr. klasse (bundet lag låst hvor muligt, ellers VejDim-beregnet).
De faktiske materialer og tykkelser ses i appens kørselstabel og opsummeres
under *Datagrundlag og forudsætninger*. En vigtig erfaring undervejs: BSM- og
højklasse-GAB-lags tykkelser er programstyrede i VejDim (kan ikke låses) — de er
derfor VejDims egne kanoniske værdier.

## 3. Metoden (hvorfor det ikke er et gæt)

For hver celle:

1. Ubundet total fra VejDim: `t_ubundet = t_SG + t_BL`.
2. **Driftspunkt:** find den Eo i appens diagram (`T_BASIS_TABLE`, uarmeret),
   hvis tykkelse ved samme Eu netop er lig `t_ubundet` (lineær interpolation
   mellem Eo-kolonnerne). Dette giver den ækvivalente Eo, `Eo_ækv(T, Eu)` — kun
   en indeksværdi, ikke en fysisk påstand.
3. **Reduktion:** aflæs den armerede tykkelse (1 net, referenceprodukt) ved
   (Eo_ækv, Eu). Da Eo_ækv per konstruktion giver `uarmeret = t_ubundet`, er
   reduktionen **identisk med diagrammets egen reduktion** i det punkt:
   `reduktion = (t_ubundet − armeret) / t_ubundet`.

Pointen: VejDim-kørslen bruges *kun* til at placere driftspunktet. Selve
reduktionen er 100 % geonet-diagrammets feltdokumenterede tal. De to metoders
kriterier blandes aldrig.

## 4. Konsistenschecks

1. **Reduktionsniveauet matcher appen selv.** De fundne reduktioner ligger i
   samme bånd som appens direkte belastningsklasse-dimensionering — det er den
   samme fysiske geonet-effekt, blot indekseret via trafikklasse.
2. **Zonegrænserne matcher en uafhængig beregning.** "under"/"over"-mønstret er
   praktisk talt identisk med en teoretisk beregnet MET-bromatrix (Odemark/
   Boussinesq-håndmetode, se §6), selvom de to er fremkommet helt uafhængigt
   (empiriske VejDim-kørsler vs. håndberegning).
3. **Mekanisk plausibilitet.** En uafhængig to-lags overflademodul-tilbage-
   beregning (Odemark/Boussinesq) af VejDim-stakken (SG 300 / BL 100 /
   underbund Eu) giver i kernezonen en surface-modulus i samme størrelsesorden
   som Eo_ækv (middelforhold ~1,1). Koblingen lander altså i et fysisk fornuftigt
   leje. Den er dog **ikke** en stram mekanisk identitet (stort spænd i
   yderpunkterne) — hvilket netop understreger, at reduktionen hviler på
   diagrammets tykkelsesrelation, ikke på en Eo-lighed.

## 5. Zoner — og hvad appen gør

- **Kernezone:** dimensionér som beskrevet — vis reduktion pr. produkt via
  Eo_ækv. Det kommercielt relevante område (middel-tung trafik på blød–middel
  bund).
- **Zone "under" (blød bund × lave klasser):** VejDim kræver mindre end
  diagrammets mest konservative kurve (Eo=30). Appen henviser til
  belastningsklasse-flowet. (I praksis vil frost-gulvet ofte styre disse celler.)
- **Zone "over" (stiv bund × høje klasser):** VejDims ubundne krav overstiger
  diagrammernes tykkelsesområde (Eo=150). Appen afviser med besked frem for at
  ekstrapolere; reduktionspotentialet er her lavest, og en konkret
  VejDim-beregning er nødvendig.

## 6. Forbehold

1. **VejDim kender ikke geonet.** Reduktionen kan aldrig begrundes inden for
   vejreglen — den hviler på GS-GRID/Tensar-feltforsøgene. Rapportteksten skal
   gøre dette eksplicit.
2. **MSL erstatter SG+BL samlet.** Diagrammets tykkelse er ét mekanisk
   stabiliseret lag; VejDim-referencen er SG+BL. Sammenligningen sker på total
   ubundet tykkelse. Materialekravet til MSL-laget (SG-kvalitet) er strengere end
   BL, hvilket er konservativt.
3. **Frost/koblingshøjde ligger uden for korrelationen.** Kørslerne er lavet
   frostsikkert (ren bæreevne). En geonet-reduceret opbygning må ikke bringe den
   samlede højde under koblingshøjden for frosttvivlsom/frostfarlig bund
   (håndbogens Fig. 5.3) — separat kontrol. Vejledende gulve for hele
   befæstelsen (frosttvivlsom/frostfarlig): T1 400/500 · T2 500/700 ·
   T3 600/800 · T4–T7 700/900 mm. **Verificér mod Fig. 5.3 før normativ brug.**
4. **1-net-huller i kernezonen.** Nogle celler i kernezonen mangler 1-net-data i
   diagrammet ved den ækvivalente Eo (1-lags-kolonnen er tom ved høj Eo / tynd
   opbygning) — reduktionen kan ikke aflæses der.
5. **T7 ikke medtaget** (åben klasse) — appen henviser til konkret
   VejDim-beregning.
6. **Følsomhed for asfaltpakken.** Eo_ækv afhænger let af den valgte (faste)
   asfaltpakke pr. klasse. Pakkerne er VejDims kanoniske valg; væsentligt
   anderledes pakker ville flytte de ubundne krav og dermed Eo_ækv. En
   dokumenteret forudsætning, ikke en fejlkilde.

## 7. Hvor funktionen bor i appen

- `core/data.py` — indeholder de 36 standardkørsler
  (`VEJDIM_KOERSLER_STANDARD_RAEKKER`), tilbageberegner Eo_ækv
  (`back_beregn_eo_aekv` / `korrelation_fra_koersler`) og slår op med
  Eu-interpolation (`trafik_eo_aekv`).
- `core/calculator.py` — `_slaa_op_interp` interpolerer mellem Eo-kolonnerne
  (identisk med eksakt opslag ved en præcis kolonne).
- `app.py` — valg af dimensioneringsgrundlag i begge tilstande samt sektionen
  **🚦 Trafikklasse-korrelation** med metode, forudsætninger, zoner, redigerbare
  kørsler og den afledte Eo_ækv-tabel.
- `korrelation_final.py` — reproducerer analysen uden for appen ud fra
  standardkørslerne (dine egne redigeringer i appen indgår ikke).

---

## Appendiks A: VejDim-kørselsopskrift (til nye kørsler)

Retter du kørslerne i appen eller tilføjer nye, skal de udføres med samme
opsætning som grundlaget, ellers bliver rækkerne ikke sammenlignelige.

**Fælles indstillinger (alle celler)**

| Indstilling | Værdi |
|---|---|
| Belastningsmodel | Æ10 Tvillingehjul (standard) |
| Hastighed | 60 / 80 km/t |
| Afvandingsforhold etableret | Nej |
| Underbund | **Frostsikker** + E manuelt sat til cellens Eu |
| Dimensioneringsperiode | 20 år (alle lags levetid ≥ 20 år) |
| Asfaltens E-værdier | VejDims standard — må **ikke** overskrives |
| Ubundne lag | SG II (E=300) over BL II U≤3 (E=100) |

**Låst vs. frit bundet bærelag.** Ved T2/T3 er trafikken lav nok til, at et låst
bundet lag går op. Ved T4–T6 er laget stramt bundet af asfaltkriteriet — låser
man en anden værdi, fås *"a solution that meets the lifetime criteria could not
be found"*. Lad derfor feltet stå frit dér og notér den tykkelse, VejDim
beregner. BSM-tykkelser kan aldrig låses (programstyret; kun E kan overskrives).
Tilbyder VejDim ikke det ønskede materiale ved en klasse, så brug programmets
eget alternativ med standardværdier og notér det i bemærkningsfeltet.

**Fremgangsmåde pr. celle**

1. Sæt trafikklassen og underbundens E (= cellens Eu).
2. Indsæt den faste asfaltpakke for klassen; rør ikke E-felterne.
3. Lad både SG og BL stå frie og tryk Beregn. Udfylder VejDim selv begge, er
   cellen færdig.
4. Løser VejDim kun det nederste lag: sæt SG trinvist (10 mm ad gangen), lad BL
   være fri, og find den **mindste SG**, hvor beregningen lykkes med alle
   levetider ≥ 20 år.
5. Indtast rækken i appens kørselstabel (🚦 Trafikklasse-korrelation) — SG og BL
   samt asfaltpakken; totalerne beregnes automatisk.

Rækkefølgen SG før BL følger kaskadeprincippet: SG beskytter toppen af BL, BL
beskytter underbunden.

**Kanttilfælde**

- *"A solution … could not be found"*: de låste øvre lag kan ikke beskytte
  snittet under dem — spændingen på toppen af et lag bestemmes kun af lagene
  ovenover. Øg SG ét trin, eller løsn en overskrevet tykkelse.
- VejDim håndhæver minimumstykkelser (fx SG ≥ 100 mm) — notér "min-styret".
- Meget lange levetider i BL-rækken er fint; kravet er kun ≥ 20 år.
- Rødt udråbstegn ved tykkelse er en udførelses-note (laget udlægges i flere
  lag) og påvirker ikke beregningen.

## Appendiks B: Validering af den uafhængige håndberegning

Konsistenscheck 2 og 3 hviler på den manuelle mekanistisk-empiriske metode
(Odemark/Boussinesq) fra Bolet & Busch: *Vejbefæstelsers dimensionering*
(AAU 2016, kap. 7), med de gældende kriterier fra håndbogen (jan. 2022/rev.
aug. 2025):

- σz,till = 0,086 MPa · (E/160)^1,06 · (NÆ10/10⁶)^−0,25 (top af hvert ubundet lag)
- εh,till = 250 µstrain · (NÆ10/10⁶)^−0,191 (underside af samlet asfaltpakke)

Responsmodellen er valideret mod lærebogens gennemregnede eksempel
(Figur 43 / Eksempel Q):

| Respons | Beregnet | Lærebogens facit |
|---|---|---|
| ε underside asfalt | 121,3 µstr | 121 µstr |
| σz top SIM | 0,186 MPa | 0,190 MPa |
| σz top BL | 0,028 MPa | 0,028 MPa |
| h_e snit 1 / snit 2 | 353 / 1187 mm | 353 / 1187 mm |

---

*Kilder: VejDim (Vejdirektoratet); Håndbog "Dimensionering af befæstelser og
forstærkningsbelægninger" (jan. 2022/rev. aug. 2025); MMOPP Brugervejledning
(2007); Bolet & Busch: "Vejbefæstelsers dimensionering" (AAU 2016) kap. 7;
appens designdiagrammer i `core/data.py`. Datagrundlag: de 36 standardkørsler i
`core/data.py`, redigerbare i appen. Reproducerbart script:
`korrelation_final.py`.*
