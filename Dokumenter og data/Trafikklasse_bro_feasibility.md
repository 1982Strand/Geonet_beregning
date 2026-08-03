# Feasibility-analyse: Bro fra VejDims trafikklasser til geonet-appens dimensionering

**Dato:** 2. juli 2026 · **Status:** analysegrundlag til beslutning — ingen app-ændringer foretaget

---

## 1. Formål

Visionen: En rådgiver dimensionerer sin vej i VejDim, taster de fundne ubundne lagtykkelser ind i appen sammen med trafikklassen og underbundens E-modul, og appen viser, hvor meget de ubundne lag kan reduceres med geonet (MSL). Dette dokument undersøger, om der kan bygges en fagligt holdbar bro fra VejDims trafikklasser (T1–T7) til appens dimensioneringsgrundlag, for underbund med Eu = 5, 10, 15, 20, 30 og 40 MPa.

**Konklusion på forhånd:** Ja, broen er mulig i et stort, praktisk relevant område af T×Eu-matricen (typisk reduktioner på 26–38 %), men den har tre veldefinerede grænser, som en app-integration skal håndtere eksplicit (afsnit 8).

---

## 2. Metodeforskellen

| | Appen (GS-GRID/Tensar MSL) | VejDim (vejreglen) |
|---|---|---|
| Kriterium | Krav om **overflademodul Eo** på toppen af bærelaget (stivhedsmetode) | Tilladelig **trykspænding pr. lag**, faldende med antal gentagelser (udmattelsesmetode) |
| Trafik | Belastningsklasse 1–6 = **lastens størrelse** (akseltryk ≤6/8/12/15 t) | Trafikklasse T0–T7 = **lastens gentagelser** (NÆ10 over dimensioneringsperioden) |
| Model | Empiriske designdiagrammer (feltforsøg): (Eu, Eo) → tykkelse, uarmeret/1 net/2 net | Elastisk lagmodel + analytisk-empiriske kriterier |
| Omfang | Ét ubundet lag (MSL); ingen asfalt, ingen frost | Hele befæstelsen: asfalt + SG + BL + frostkrav |

Klasserne koder altså **forskellige fysiske størrelser** — en direkte klasse→klasse-oversættelse er umulig, og appens eksisterende `TRAFIKKOBLING` (core/data.py) er korrekt markeret som ekspertvurdering.

## 3. Broens princip

Trafikklassen erstatter belastningsklassen som indgang, og Eo bliver en intern, afledt størrelse:

1. Rådgiveren dimensionerer i VejDim → uarmeret ubundet tykkelse (SG + BL) for (trafikklasse, Eu).
2. Tykkelsen tastes ind i appen sammen med T-klasse og Eu.
3. Appen finder den **ækvivalente Eo** ved baglæns-opslag i sin egen diagramtabel: "hvilken Eo-kurve giver netop denne uarmerede tykkelse ved denne Eu?" (interpolation mellem Eo-kolonnerne 30–150).
4. Den armerede tykkelse aflæses ved samme ækvivalente Eo — præcis som appens nuværende beregning, blot med interpoleret Eo.

Logikken: diagrammernes reduktion udtrykker "samme præstation med tyndere lag" langs en Eo-kurve. Ved at gå ind på kurven dér, hvor den uarmerede tykkelse matcher VejDims krav, overføres reduktionen til VejDim-referencen uden at blande de to metoders kriterier sammen.

## 4. Beregningsgrundlag og validering

Til at estimere VejDims krav pr. (T, Eu)-celle er brugt den manuelle mekanistisk-empiriske metode (Odemark/Boussinesq) fra Bolet & Busch: *Vejbefæstelsers dimensionering* (AAU 2016, kap. 7), parret med de **gældende** kriterier fra håndbogen (jan. 2022, rev. aug. 2025):

- σz,till = 0,086 MPa · (E/160)^1,06 · (NÆ10/10⁶)^−0,25 (top af hvert ubundet lag + underbund)
- εh,till = 250 µstrain · (NÆ10/10⁶)^−0,191 (underside af samlet asfaltpakke)

Responsmodellen (punktlast 60 kN = 5 t enkelthjul + 20 % stødtillæg; ækvivalent dybde med kubikrodsvægtning; f = 1+0,6(a/h)² ved første snit, 0,85 dybere; σz = 3P/(2πR²)) er **valideret mod lærebogens gennemregnede eksempel** (Figur 43/Eksempel Q):

| Respons | Beregnet | Lærebogens facit |
|---|---|---|
| ε underside asfalt | 121,3 µstr | 121 µstr |
| σz top SIM | 0,186 MPa | 0,190 MPa |
| σz top BL | 0,028 MPa | 0,028 MPa |
| h_e snit 1 / snit 2 | 353 / 1187 mm | 353 / 1187 mm |

Bro-opslagene bruger appens **live** diagramtabel (`T_BASIS_TABLE`, genopbygget fra `DESIGNDIAGRAM_RAW_TABLES`) og er krydstjekket mod appens egen `beregn()` ved eksakte kolonner (fx Eu=10/Eo=60: uarmeret 800 mm, 1 net 564 mm — identisk i begge).

**Forudsætninger for matricen** (holdt statiske): 20 års dimensioneringsperiode, 0 % trafikvækst (NÆ10 = årsværdi fra håndbogens Fig. 4.1 × 20; T7 sat til 2×T6 som illustration, da klassen er åben opad); hastighed ≥ 60 km/t; asfalt = 40 mm AB 2000 + GAB I 2000/3000 (dimensioneret pr. celle efter ε-kriteriet); SG II (E=300) over BL (E=100); ν = 0,35; **ingen** min/maks-tykkelser og **intet** frost-gulv (ren bæreevne).

## 5. VejDim-referencematrix (rå bæreevne, mm)

| T | NÆ10 [mio.] | Eu=5 | Eu=10 | Eu=15 | Eu=20 | Eu=30 | Eu=40 |
|---|---|---|---|---|---|---|---|
| **T1** ubundet (SG+BL) | 0,002 | 390 (80+310) | 301 | 255 | 224 | 183 | 156 |
| **T2** ubundet | 0,146 | 733 (184+549) | 576 | 493 | 438 | 366 | 319 |
| **T3** ubundet | 0,366 | 826 (209+617) | 649 | 557 | 495 | 414 | 361 |
| **T4** ubundet | 1,46 | 965 (232+733) | 755 | 645 | 572 | 476 | 412 |
| **T5** ubundet | 3,6 | 1072 (252+820) | 837 | 714 | 632 | 525 | 453 |
| **T6** ubundet | 6,0 | 1141 (266+875) | 890 | 759 | 672 | 557 | 481 |
| **T7*** ubundet | 12,0 | 1239 (285+954) | 966 | 822 | 727 | 602 | 520 |

Asfaltpakken (fast pr. række): T1 100 · T2 148 · T3 163 · T4 199 · T5 225 · T6 240 · T7 263 mm. SG-delen er konstant hen over Eu (den beskytter toppen af BL, E=100); kun BL vokser med blødere bund. *T7 er en illustrativ antagelse (2×T6).

**Frost-gulve til sammenligning** (mindste koblingshøjde for hele befæstelsen, Fig. 5.3; frostsikker har intet gulv): T1: 400/500 mm · T2: 500/700 · T3: 600/800 · T4–T7: 700/900 (frosttvivlsom/frostfarlig). Ved fx T4/Eu=40 er rå total 611 mm < 700 → frost styrer dér i praksis (stemmer med at det udgåede katalogs T4-opbygninger summede til netop 700 mm).

## 6. Bro-tabellen: ækvivalent Eo og reduktionspotentiale (1 net, referenceprodukt)

| T | Eu=5 | Eu=10 | Eu=15 | Eu=20 | Eu=30 | Eu=40 |
|---|---|---|---|---|---|---|
| **T1** | ÷ under | ÷ under | ÷ under | ÷ under | Eo≈45 (net uden dækning) | Eo≈61 (net uden dækning) |
| **T2** | ÷ under | ÷ under | Eo≈44 → **−38 %** | Eo≈56 → **−37 %** | Eo≈76 (net uden dækning) | Eo≈107 (net uden dækning) |
| **T3** | ÷ under | Eo≈37 → **−37 %** | Eo≈54 → **−32 %** | Eo≈66 → **−33 %** | Eo≈92 → **−35 %** | Eo≈123 (net uden dækning) |
| **T4** | Eo≈40 → **−34 %** | Eo≈53 → **−31 %** | Eo≈69 → **−30 %** | Eo≈83 → **−29 %** | Eo≈116 → **−32 %** | Eo≈138 (net uden dækning) |
| **T5** | Eo≈56 → **−31 %** | Eo≈67 → **−30 %** | Eo≈86 → **−31 %** | Eo≈107 → **−28 %** | Eo≈132 → **−30 %** | ÷ over |
| **T6** | Eo≈78 → **−26 %** | Eo≈78 → **−31 %** | Eo≈104 → **−30 %** | Eo≈122 → **−27 %** | Eo≈142 → **−29 %** | ÷ over |
| **T7*** | Eo≈104 → **−26 %** | Eo≈106 → **−30 %** | Eo≈127 → **−29 %** | Eo≈139 → **−27 %** | ÷ over | ÷ over |

Signaturer: **÷ under** = VejDim-kravet ligger under diagrammets Eo=30-kurve (diagrammet er mere konservativt end VejDim — broen er ikke relevant/nødvendig). **÷ over** = kravet overstiger Eo=150-kurven (uden for diagramdækning). **"net uden dækning"** = ækvivalent Eo findes, men 1-net-kurven har ingen data dér (typisk stiv bund + lav Eo, hvor nettet giver begrænset effekt).

## 7. Læsning: tre zoner

1. **Kernezonen (broen holder):** T3–T7 × Eu 5–30 (samt T2 ved Eu 15–20). Ækvivalent Eo lander pænt inde i diagramområdet, og reduktionerne (26–38 %) er helt på linje med appens nuværende resultater. Det er samtidig præcis dér, geonet-løsninger er kommercielt relevante: middel-tung trafik på blød–middel bund.
2. **Nedre venstre (let trafik / blød bund):** VejDims rå krav er *mindre* end diagrammets svageste kurve (Eo=30). Diagrammerne stiller et stivhedskrav, VejDim ikke stiller. Her bør appen melde "VejDim-kravet er under diagramområdet — brug klassisk belastningsklasse-dimensionering i stedet" (og i praksis styrer frost-gulvet alligevel T1–T2).
3. **Øvre højre (tung trafik / stiv bund):** VejDims krav overstiger Eo=150-kurven (T5–T7 × Eu 40, T7 × Eu 30), eller nettet mangler dækning i diagrammet. Her er reduktionspotentialet alligevel lavest, og frost-gulvet (700–900 mm) er ofte det reelt styrende. Appen bør afvise med klar besked frem for at ekstrapolere.

## 8. Forbehold

1. **VejDim kender ikke geonet.** Reduktionen kan aldrig begrundes inden for vejreglens kriterier — den hviler på GS-GRID/Tensar-feltforsøgsdokumentationen. Rapportteksten skal (som i dag) gøre dette eksplicit.
2. **Frost-gulvet skal respekteres.** En geonet-reduceret opbygning må ikke bringe den samlede befæstelseshøjde under koblingshøjden (Fig. 5.3). Broen kræver derfor frostklasse som input og skal begrænse reduktionen til frost-gulvet (eller kræve frostsikker bund/kompenserende tiltag). Bemærk at MSL-dokumentationens udjævnende effekt på frosthævninger er et fagligt argument, men ikke vejregel-hjemmel.
3. **MSL erstatter SG+BL samlet.** Diagramtykkelsen er ét mekanisk stabiliseret lag; VejDim-referencen er SG+BL. Sammenligningen sker på total ubundet tykkelse — materialekravene til MSL-laget (typisk SG-kvalitet) er strengere end BL, hvilket er konservativt for bæreevnen men skal fremgå af rapporten.
4. **Matricens tal er en MET-tilnærmelse.** Referencematricen er beregnet med håndmetoden (valideret mod lærebogens eksempel, ±få %), ikke med VejDim selv. Det er acceptabelt her, fordi den endelige bro bruger **rådgiverens indtastede VejDim-tal** som reference — matricen tjener kun til at afgrænse dækningen og validere princippet. Skal matricen bruges normativt (fx som indbygget kontrol), bør den kalibreres mod 10–30 VejDim-referencekørsler.
5. **Realisme ved Eu ≤ 10:** VejDim regner med faste E-værdier (SG=300 selv på 5 MPa bund); i praksis begrænses opnåelig lagstivhed af underlaget. Det taler yderligere *for* MSL-løsningen (dokumenteret på blød bund), men betyder at VejDim-referencen ved Eu=5–10 er teoretisk i begge metoder.
6. **T7 er åben opad** — matricens T7-række er en illustration (2×T6); reelle T7-projekter skal altid regnes konkret i VejDim.

## 9. Anbefaling til app-integration (næste fase)

1. **Ny tilstand "VejDim-reference":** input = trafikklasse (T1–T7), Eu (5–40 MPa), frostklasse, og rådgiverens uarmerede SG+BL-tykkelse fra VejDim (+ evt. asfalttykkelse til frost-kontrollen).
2. **Beregning:** ækvivalent Eo ved interpolation i `T_BASIS_TABLE`-rækken (genbrug `opslag`-mønstret fra `core/calculator.py`; kræver en interpolerende variant af `_slaa_op`), derefter armeret tykkelse pr. produkt som i dag (φ- og netkorrektioner uændrede).
3. **Valideringer:** (a) indtastet tykkelse inden for diagramdækning (ellers zone 2/3-besked); (b) plausibilitetstjek mod referencematricen (±30 % advarsel); (c) frost-gulvskontrol på reduceret total; (d) eksisterende min. dæklag/kornstørrelses-tjek genbruges.
4. **Rapport:** ny standardtekst der beskriver referencens oprindelse (VejDim/vejreglen) og reduktionens dokumentationsgrundlag (feltforsøg), inkl. frost-forbeholdet.
5. **Kalibrering (valgfri men anbefalet):** 10–30 VejDim-kørsler spredt over kernezonen til at efterprøve referencematricen og stramme plausibilitetstjekket.

---

*Kilder: Håndbog "Dimensionering af befæstelser og forstærkningsbelægninger" (VD, jan. 2022/rev. aug. 2025); MMOPP Brugervejledning (Vejregelrådet, 2007); Bolet & Busch: "Vejbefæstelsers dimensionering" (AAU DCE Lecture Notes 52, 2016) kap. 7; appens `core/data.py`/`core/calculator.py`. Beregningsscript: scratchpad `bro_matrix.py` (session-arbejdsfil, ikke del af appen).*
