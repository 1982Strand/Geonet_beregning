# Kontrol af designdiagrammerne — aflæsning af de markerede punkter

Kontrolfil, udarbejdet 24.09.2026. Formålet er at fastlægge de punkter, der er markeret på kurverne i designdiagram 1–6, før opslagstabellerne i `geonet_interpolerede_diagrammer.xlsx` og `core/data.py` kontrolleres.

## 1 Sammenfatning

- Alle 176 markerede punkter i de seks diagrammer kan aflæses. Intet punkt er uaflæseligt.
- 161 markører er fuldt synlige i billederne. 15 markører for 1 lag armering er delvist dækket af markøren for 2 lag/flere lag og er rekonstrueret, jf. afsnit 4.2.
- Diagramsiden findes som vektorgrafik på side 10 i begge designmanualer (`brochure-tensar-designmanual-sept-2024-1.pdf` og `dk-brochure-gs-grid-designmanual.pdf`). Kurverne er tegnet som rette linjestykker mellem datapunkterne, og punkterne kan derfor aflæses direkte af linjestykkernes endepunkter. De to manualer har identiske diagramdata.
- Aflæsningen af billederne afviger højst 0,13 MPa fra vektorgrafikken (middel 0,02 MPa, spredning 0,04 MPa).
- Alle datapunkter i vektorgrafikken ligger på et fast raster på 0,23 MPa (diagram 1) og 0,30–0,33 MPa (diagram 2–6). Manualens tegning er dermed afrundet, og de oprindelige værdier kan ikke bestemmes nærmere end ca. ±0,15 MPa, jf. afsnit 4.3.
- Tykkelserne ligger i alle tilfælde på de hele 10 cm.
- Værdierne i afsnit 3 og 6 er aflæst af vektorgrafikken og afrundet til nærmeste 0,5 MPa. I 2 punkter giver billedaflæsningen en anden afrundet værdi; de er noteret under de pågældende tabeller.
- Afsnit 6 stiller de aflæste punkter op efter Eᵤ, som i `geonet_interpolerede_diagrammer.xlsx`.
- Afsnit 7 angiver lagtykkelsen ved hele Eᵤ, bestemt ved lineær interpolation mellem de afrundede punkter. Standardtabellerne i appen (`core/data.py`) er rettet til afsnit 7 den 24.09.2026, og de værdier, der ligger i et aflæst punkt, står med fed på siden Designdiagrammer.
- Ét punkt er ved gennemsyn fastsat til en anden værdi end aflæsningen: diagram 1, ustabiliseret, t = 100 cm, Eᵤ = 4 MPa, jf. afsnit 3.
- Afsnit 8 sammenholder afsnit 7 med den hidtidige opslagstabel i `geonet_interpolerede_diagrammer.xlsx`. De udfyldte rækker er de samme. Af 458 værdier afviger 44 med 1 cm eller mere, heraf 18 med 2 cm eller mere. Den største afvigelse er 5,5 cm (diagram 4, ustabiliseret, Eᵤ = 5 MPa).
- Enkelte forhold bør afklares, før der arbejdes videre, jf. afsnit 5.

## 2 Fremgangsmåde

**Billederne.** De seks filer `Diagram 1.png` … `Diagram 6.png` er aflæst ved pixelanalyse. Akserne kalibreres på diagrammernes gitterlinjer (lineær tilpasning; restafvigelse højst 0,24 cm og 0,13 MPa). Markørerne findes på deres farve, og markørens midtpunkt tages som datapunkt. For trekanterne anvendes midten af den omskrevne boks og ikke tyngdepunktet, da trekantens tyngdepunkt ligger under datapunktet.

**Vektorgrafikken.** Datapunkterne er udtrukket af kurvernes linjestykker på side 10 i manualerne. Akserne kalibreres på de sorte gitterlinjer i hvert plotområde. Markørernes midtpunkter i vektorgrafikken falder sammen med linjestykkernes endepunkter.

Markørerne har ikke samme betydning i alle diagrammer:

| Diagram | Ustabiliseret | 1 lag armering | 2 lag / flere lag |
| --- | --- | --- | --- |
| 1 | lilla firkant | blå rombe | — (ingen kurve) |
| 2–4 | gul trekant | blå rombe | lilla firkant, »2 lag armering« |
| 5–6 | gul trekant | blå rombe | lilla firkant, »Flere lag« |

*Figur 1 Markørernes betydning. I Tensar-manualen er diagrammerne angivet som baseret på TriAx TX160; GS-GRID-manualen har samme diagramdata uden denne angivelse.*

| Diagram | Eₒ [MPa] | Klasse | Tykkelse [cm] | Eᵤ-akse [MPa] | Billede [px/MPa] | Raster [MPa] | Punkter |
| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | 30 | 1 | 0–110 | 0–35 | 8,3 | 0,23 | 20 |
| 2 | 45 | 2 | 0–130 | 0–50 | 5,7 | 0,33 | 28 |
| 3 | 60 | 3 | 10–140 | 0–50 | 5,8 | 0,31 | 30 |
| 4 | 80 | 4 | 20–150 | 0–50 | 5,9 | 0,32 | 31 |
| 5 | 120 | 5 | 30–160 | 0–50 | 5,8 | 0,30 | 33 |
| 6 | 150 | 6 | 40–170 | 0–50 | 5,8 | 0,32 | 34 |

*Figur 2 Akser, opløsning og antal punkter pr. diagram. Rasteret er afrundingstrinnet i manualens vektorgrafik, jf. afsnit 4.3.*

## 3 Aflæste punkter

Værdierne er Eᵤ i MPa ved den anførte bærelagstykkelse. De er aflæst af vektorgrafikken og afrundet til nærmeste 0,5 MPa. En tankestreg betyder, at kurven ikke har et punkt ved tykkelsen.

Billedaflæsningen afviger højst 0,13 MPa fra vektorgrafikken, jf. afsnit 4.1. Hvor de to aflæsninger alligevel giver forskellig afrundet værdi, er værdien mærket med ¹ og forholdet noteret under tabellen.

Værdier mærket med ² er ved gennemsyn fastsat til en anden værdi end aflæsningen; forholdet er noteret under tabellen.

Der gøres opmærksom på, at afrundingen ikke er entydig, når den aflæste værdi ligger inden for ca. 0,15 MPa af et afrundingsskel (x,25 eller x,75), jf. afsnit 4.3.

### Diagram 1 — Eₒ = 30 MPa, belastningsklasse 1

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] |
| ---: | ---: | ---: |
| 0 | 30 | — |
| 10 | 25 | — |
| 20 | 21 | 15 |
| 30 | 18 | 11,5 |
| 40 | 14,5 | 9 |
| 50 | 12 | 6,5 |
| 60 | 9,5 | 5 |
| 70 | 8 | 3 |
| 80 | 6 | 2 |
| 90 | 5 | 0,5 |
| 100 | 4 ² | — |
| 110 | 3 | — |

*Figur 3 Diagram 1: ustabiliseret 12 punkter, 1 lag 8 punkter.*

² Ustabiliseret, t = 100 cm: Punktet ved t = 100 cm er ved gennemsyn fastsat til Eᵤ = 4 MPa. Vektorgrafikken giver 3,42 MPa, der afrundes til 3,5 MPa; billedet giver 3,44 MPa.

### Diagram 2 — Eₒ = 45 MPa, belastningsklasse 2

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] | 2 lag Eᵤ [MPa] |
| ---: | ---: | ---: | ---: |
| 0 | 45 ¹ | — | — |
| 10 | 36 | — | — |
| 20 | 29 | 20 | — |
| 30 | 23 | 16 | — |
| 40 | 18,5 | 12 | — |
| 50 | 15 | 9 | 6,5 |
| 60 | 12 | 6 | 4,5 |
| 70 | 10 | 4,5 | 3 |
| 80 | 8 | 3 | 2 |
| 90 | 6 | 2 | 1 |
| 100 | 5 | 1 | — |
| 110 | 3,5 | — | — |
| 120 | 3 | — | — |
| 130 | 2,5 | — | — |

*Figur 4 Diagram 2: ustabiliseret 14 punkter, 1 lag 9 punkter, 2 lag 5 punkter.*

¹ Ustabiliseret, t = 0 cm: PDF 45,17 MPa afrundes til 45 MPa, billede 45,26 MPa afrundes til 45,5 MPa. Afvigelsen er 0,09 MPa.

### Diagram 3 — Eₒ = 60 MPa, belastningsklasse 3

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] | 2 lag Eᵤ [MPa] |
| ---: | ---: | ---: | ---: |
| 10 | 45 | — | — |
| 20 | 36 | 27 | — |
| 30 | 29 | 20 | — |
| 40 | 23 | 16 | — |
| 50 | 18,5 | 12 | 9 |
| 60 | 15 | 9 | 6,5 |
| 70 | 12 | 6,5 | 4,5 |
| 80 | 10 | 4,5 | 2,5 |
| 90 | 8 | 3 | 1,5 |
| 100 | 6 | 1,5 | 1 |
| 110 | 5 | 1 | — |
| 120 | 3,5 | — | — |
| 130 | 3 | — | — |
| 140 | 2,5 | — | — |

*Figur 5 Diagram 3: ustabiliseret 14 punkter, 1 lag 10 punkter, 2 lag 6 punkter.*

### Diagram 4 — Eₒ = 80 MPa, belastningsklasse 4

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] | 2 lag Eᵤ [MPa] |
| ---: | ---: | ---: | ---: |
| 20 | 45 | 33 | — |
| 30 | 36 | 26 | — |
| 40 | 29 | 20 | — |
| 50 | 23 | 14 | — |
| 60 | 18,5 | 10,5 | 8 |
| 70 | 15 | 7,5 | 6 |
| 80 | 12 | 5,5 | 4 |
| 90 | 10 | 4 | 3 |
| 100 | 8 | 3 | 2 |
| 110 | 6 | 2 | 1 |
| 120 | 5 | 1 | — |
| 130 | 3,5 | — | — |
| 140 | 3 | — | — |
| 150 | 2,5 | — | — |

*Figur 6 Diagram 4: ustabiliseret 14 punkter, 1 lag 11 punkter, 2 lag 6 punkter.*

### Diagram 5 — Eₒ = 120 MPa, belastningsklasse 5

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] | Flere lag Eᵤ [MPa] |
| ---: | ---: | ---: | ---: |
| 30 | 45 | 33 | — |
| 40 | 36 | 25 | — |
| 50 | 29 | 19 | 14 |
| 60 | 23 | 13,5 | 10 |
| 70 | 18,5 | 9,5 | 8 |
| 80 | 15 | 8 | 6 |
| 90 | 12 | 6 | 4,5 |
| 100 | 10 | 4,5 | 3 |
| 110 | 8 | 2,5 | 2 |
| 120 | 6 | 2 | 1 |
| 130 | 5 | 1 | — |
| 140 | 3,5 | — | — |
| 150 | 3 | — | — |
| 160 | 2,5 | — | — |

*Figur 7 Diagram 5: ustabiliseret 14 punkter, 1 lag 11 punkter, flere lag 8 punkter.*

### Diagram 6 — Eₒ = 150 MPa, belastningsklasse 6

| t [cm] | Ustabiliseret Eᵤ [MPa] | 1 lag Eᵤ [MPa] | Flere lag Eᵤ [MPa] |
| ---: | ---: | ---: | ---: |
| 40 | 45 | 32 | — |
| 50 | 36 | 24 | 18 |
| 60 | 29 | 17 | 12 |
| 70 | 23 | 12 | 9 |
| 80 | 18,5 | 8,5 | 6,5 |
| 90 | 15 | 6 | 4,5 |
| 100 | 12 | 4,5 | 3 |
| 110 | 10 | 3,5 | 2,5 ¹ |
| 120 | 8 | 2,5 | 1,5 |
| 130 | 6 | 1,5 | 0,5 |
| 140 | 5 | 1 | — |
| 150 | 3,5 | — | — |
| 160 | 3 | — | — |
| 170 | 2,5 | — | — |

*Figur 8 Diagram 6: ustabiliseret 14 punkter, 1 lag 11 punkter, flere lag 9 punkter.*

¹ Flere lag, t = 110 cm: PDF 2,26 MPa afrundes til 2,5 MPa, billede 2,18 MPa afrundes til 2 MPa. Afvigelsen er 0,07 MPa.

## 4 Kontrol af aflæsningen

### 4.1 Billede mod vektorgrafik

| Diagram | Punkter | Middel [MPa] | Spredning [MPa] | Største [MPa] | Største, dækkede markører [MPa] |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 20 | 0,00 | 0,03 | 0,07 | — |
| 2 | 28 | 0,03 | 0,06 | 0,13 | 0,04 |
| 3 | 30 | 0,02 | 0,03 | 0,09 | 0,03 |
| 4 | 31 | 0,02 | 0,04 | 0,08 | 0,07 |
| 5 | 33 | 0,03 | 0,04 | 0,10 | 0,02 |
| 6 | 34 | 0,03 | 0,04 | 0,12 | 0,03 |

*Figur 9 Afvigelse = billede − PDF.*

Billedaflæsningen gengiver vektorgrafikken inden for ca. en pixel. Den systematiske afvigelse på +0,02 til +0,03 MPa i diagram 2–6 skyldes formentlig kalibreringen af billedet og er uden praktisk betydning.

### 4.2 Delvist dækkede markører

Markøren for 2 lag/flere lag er tegnet oven på markøren for 1 lag. Hvor de to kurver ligger tæt, er den blå rombe derfor kun delvist synlig i billedet. Rombens midtpunkt er bestemt på to uafhængige måder:

- **A:** rombens synlige øverste spids plus en halv rombehøjde, målt på de fuldt synlige romber i samme diagram.
- **B:** den blå linjes forløb på hver side af markøren, forlænget til gitterlinjen. Linjestykkerne går gennem datapunkterne.

| Diagram | t [cm] | Synlig højde [px] | A [MPa] | B [MPa] | Billede [MPa] | PDF [MPa] |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 80 | 8 af ca. 9 | 3,26 | 3,21 | 3,24 | 3,21 |
| 2 | 90 | 5 af ca. 9 | 1,86 | 1,86 | 1,86 | 1,91 |
| 3 | 100 | 4 af ca. 9 | 1,52 | 1,52 | 1,52 | 1,49 |
| 4 | 80 | 8 af ca. 9 | 5,55 | 5,43 | 5,49 | 5,45 |
| 4 | 90 | 7 af ca. 9 | 4,19 | 4,18 | 4,18 | 4,18 |
| 4 | 100 | 6 af ca. 9 | 3,00 | 2,95 | 2,97 | 2,91 |
| 4 | 110 | 5 af ca. 9 | 1,98 | 2,02 | 2,00 | 1,95 |
| 5 | 70 | 8 af ca. 9 | 9,61 | 9,74 | 9,67 | 9,67 |
| 5 | 100 | 7 af ca. 9 | 4,26 | 4,28 | 4,27 | 4,25 |
| 5 | 110 | 5 af ca. 9 | 2,70 | 2,77 | 2,74 | 2,75 |
| 5 | 120 | 5 af ca. 9 | 1,84 | 1,85 | 1,84 | 1,85 |
| 6 | 100 | 8 af ca. 9 | 4,60 | 4,50 | 4,55 | 4,52 |
| 6 | 110 | 7 af ca. 9 | 3,57 | 3,56 | 3,56 | 3,55 |
| 6 | 120 | 7 af ca. 9 | 2,53 | 2,59 | 2,56 | 2,58 |
| 6 | 130 | 6 af ca. 9 | 1,66 | 1,60 | 1,63 | 1,61 |

*Figur 10 Rekonstruerede markører for 1 lag armering. Billede = middel af A og B.*

Metoderne A og B stemmer overens, og alle rekonstruerede værdier ligger inden for 0,07 MPa af vektorgrafikken. De dækkede markører betragtes derfor som aflæst.

### 4.3 Afrundingsraster i manualens tegning

Samtlige datapunkter og gitterlinjer i vektorgrafikken ligger på et heltalsraster (afvigelse under 0,001 rasterenhed). Diagrammerne er dermed gemt med afrundede koordinater, formentlig ved eksport fra regneark til et vektorformat med heltalskoordinater. Den tegnede placering af et punkt kan afvige op til en halv rasterenhed fra den værdi, der lå til grund for tegningen:

| Diagram | Rasterenhed [MPa] | Mulig afrunding [MPa] |
| ---: | ---: | ---: |
| 1 | 0,23 | ±0,11 |
| 2 | 0,33 | ±0,16 |
| 3 | 0,31 | ±0,15 |
| 4 | 0,32 | ±0,16 |
| 5 | 0,30 | ±0,15 |
| 6 | 0,32 | ±0,16 |

*Figur 11 Afrundingsraster pr. diagram.*

Der gøres opmærksom på, at usikkerheden relativt set er størst for de små værdier. Ved Eᵤ ≈ 1 MPa svarer ±0,16 MPa til ca. ±16 %.

### 4.4 Ustabiliseret kurve i diagram 2–6

Den ustabiliserede kurve i diagram 2–6 har samme forløb i alle fem diagrammer, forskudt 10 cm pr. diagram. Punkt nr. i ligger ved tykkelsen t₀ + 10·(i − 1) cm, hvor t₀ = 0, 10, 20, 30 og 40 cm for diagram 2–6.

| Punkt | D2 | D3 | D4 | D5 | D6 | Middel | Spænd |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 45,17 | 45,13 | 44,87 | 44,84 | 44,84 | 44,97 | 0,33 |
| 2 | 36,06 | 35,91 | 35,97 | 36,13 | 36,13 | 36,04 | 0,22 |
| 3 | 28,90 | 29,15 | 28,97 | 28,91 | 29,03 | 28,99 | 0,25 |
| 4 | 23,05 | 23,00 | 22,93 | 22,90 | 22,90 | 22,96 | 0,15 |
| 5 | 18,49 | 18,39 | 18,48 | 18,38 | 18,39 | 18,43 | 0,11 |
| 6 | 14,92 | 15,01 | 14,99 | 15,08 | 14,84 | 14,97 | 0,24 |
| 7 | 11,99 | 11,94 | 12,13 | 12,07 | 11,94 | 12,01 | 0,19 |
| 8 | 10,04 | 10,10 | 9,90 | 9,97 | 10,00 | 10,00 | 0,20 |
| 9 | 8,09 | 7,95 | 7,99 | 8,16 | 8,06 | 8,05 | 0,22 |
| 10 | 5,81 | 6,10 | 6,09 | 6,06 | 6,13 | 6,04 | 0,32 |
| 11 | 4,83 | 4,87 | 5,13 | 5,15 | 4,84 | 4,97 | 0,32 |
| 12 | 3,53 | 3,34 | 3,54 | 3,65 | 3,55 | 3,52 | 0,31 |
| 13 | 2,88 | 3,03 | 2,91 | 3,05 | 2,90 | 2,95 | 0,17 |
| 14 | 2,56 | 2,41 | 2,59 | 2,45 | 2,58 | 2,52 | 0,17 |

*Figur 12 Ustabiliseret kurve, PDF-værdier [MPa].*

Spændet er i alle punkter højst ca. én rasterenhed (0,30–0,33 MPa). Forskellene mellem diagrammerne kan derfor alene tilskrives afrundingen, og kurven må antages at være den samme dataserie. Middelværdierne ligger tæt på 45 – 36 – 29 – 23 – 18,5 – 15 – 12 – 10 – 8 – 6 – 5 – 3,5 – 3 – 2,5 MPa, hvilket tyder på, at dataserien er angivet med hele og halve MPa. Afrundes hvert diagram for sig til nærmeste 0,5 MPa, fås netop denne serie i alle fem diagrammer. Det understøtter afrundingen i afsnit 3 og 6.

## 5 Forhold der bør afklares

1. **»Flere lag« i diagram 5 og 6.** Signaturforklaringen i diagram 5 og 6 angiver den lilla kurve som *Flere lag*, mens diagram 2–4 angiver *2 lag armering*. Værktøjet behandler kurven som 2 lag i alle diagrammer (`t_2_lag_cm`). Kildefilen `geonet_interpolerede_diagrammer.xlsx` har derimod kolonnen *Flere Lag Tykkelse (cm)* ved siden af *2 Lag Tykkelse (cm)*. Det bør afklares, om kurven i diagram 5 og 6 gælder for netop 2 lag.
2. **Nøjagtighed.** Manualens tegning er afrundet med op til ±0,15 MPa, jf. afsnit 4.3, og værdierne i afsnit 3 og 6 er yderligere afrundet til nærmeste 0,5 MPa (op til ±0,25 MPa). Ved kontrol af opslagstabellerne bør der tages hensyn til dette, fx ved at anvende en tilsvarende tolerance på tykkelsen ved kurvens aktuelle hældning. Hvis de oprindelige regnearksdata bag diagrammerne findes, bør de anvendes i stedet.
3. **2-lagskurvens forløb.** I alle fem diagrammer med 2 lag/flere lag falder 2–5 af punkterne på samme rasterpunkt som 1-lagskurvens punkt 10 cm længere til højre (diagram 2: 60, 80, 90 cm; diagram 3: 50, 70, 90, 100 cm; diagram 4: 80–110 cm; diagram 5: 70, 80, 90, 110, 120 cm; diagram 6: 60, 90 cm). Det kan tyde på, at 2-lagskurven i manualen delvist er fastlagt som 1-lagskurven forskudt 10 cm. For de små værdier kan sammenfaldet dog også skyldes afrundingen. Forholdet ændrer ikke aflæsningen, men bør kendes ved den videre kontrol.

## 6 Aflæste punkter opstillet efter Eᵤ

Tabellerne er opstillet som arkene i `geonet_interpolerede_diagrammer.xlsx`, med Eᵤ i første kolonne og bærelagstykkelsen i cm for hver kurve. Kun de rækker, hvor kurven har et aflæst punkt, er udfyldt; øvrige celler er tomme. Eᵤ-værdierne er afrundet som i afsnit 3.

Rækkerne dækker Eᵤ = 1–45 MPa i alle diagrammer, også hvor diagrammets akse eller kurver ikke når så langt. Hvor et aflæst punkt ligger på en halv værdi (fx 14,5 MPa), er der indsat en ekstra række, så punktet ikke går tabt. Rækker med halve værdier er markeret med *kursiv*.

### Diagram 1 — Eₒ = 30 MPa, belastningsklasse 1

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] |
| ---: | ---: | ---: |
| *0,5* |  | 90 |
| 1 |  |  |
| 2 |  | 80 |
| 3 | 110 | 70 |
| 4 | 100 |  |
| 5 | 90 | 60 |
| 6 | 80 |  |
| *6,5* |  | 50 |
| 7 |  |  |
| 8 | 70 |  |
| 9 |  | 40 |
| *9,5* | 60 |  |
| 10 |  |  |
| 11 |  |  |
| *11,5* |  | 30 |
| 12 | 50 |  |
| 13 |  |  |
| 14 |  |  |
| *14,5* | 40 |  |
| 15 |  | 20 |
| 16 |  |  |
| 17 |  |  |
| 18 | 30 |  |
| 19 |  |  |
| 20 |  |  |
| 21 | 20 |  |
| 22 |  |  |
| 23 |  |  |
| 24 |  |  |
| 25 | 10 |  |
| 26 |  |  |
| 27 |  |  |
| 28 |  |  |
| 29 |  |  |
| 30 | 0 |  |
| 31 |  |  |
| 32 |  |  |
| 33 |  |  |
| 34 |  |  |
| 35 |  |  |
| 36 |  |  |
| 37 |  |  |
| 38 |  |  |
| 39 |  |  |
| 40 |  |  |
| 41 |  |  |
| 42 |  |  |
| 43 |  |  |
| 44 |  |  |
| 45 |  |  |

*Figur 13 Diagram 1, aflæste punkter efter Eᵤ.*

### Diagram 2 — Eₒ = 45 MPa, belastningsklasse 2

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 |  | 100 | 90 |
| 2 |  | 90 | 80 |
| *2,5* | 130 |  |  |
| 3 | 120 | 80 | 70 |
| *3,5* | 110 |  |  |
| 4 |  |  |  |
| *4,5* |  | 70 | 60 |
| 5 | 100 |  |  |
| 6 | 90 | 60 |  |
| *6,5* |  |  | 50 |
| 7 |  |  |  |
| 8 | 80 |  |  |
| 9 |  | 50 |  |
| 10 | 70 |  |  |
| 11 |  |  |  |
| 12 | 60 | 40 |  |
| 13 |  |  |  |
| 14 |  |  |  |
| 15 | 50 |  |  |
| 16 |  | 30 |  |
| 17 |  |  |  |
| 18 |  |  |  |
| *18,5* | 40 |  |  |
| 19 |  |  |  |
| 20 |  | 20 |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 | 30 |  |  |
| 24 |  |  |  |
| 25 |  |  |  |
| 26 |  |  |  |
| 27 |  |  |  |
| 28 |  |  |  |
| 29 | 20 |  |  |
| 30 |  |  |  |
| 31 |  |  |  |
| 32 |  |  |  |
| 33 |  |  |  |
| 34 |  |  |  |
| 35 |  |  |  |
| 36 | 10 |  |  |
| 37 |  |  |  |
| 38 |  |  |  |
| 39 |  |  |  |
| 40 |  |  |  |
| 41 |  |  |  |
| 42 |  |  |  |
| 43 |  |  |  |
| 44 |  |  |  |
| 45 | 0 |  |  |

*Figur 14 Diagram 2, aflæste punkter efter Eᵤ.*

### Diagram 3 — Eₒ = 60 MPa, belastningsklasse 3

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 |  | 110 | 100 |
| *1,5* |  | 100 | 90 |
| 2 |  |  |  |
| *2,5* | 140 |  | 80 |
| 3 | 130 | 90 |  |
| *3,5* | 120 |  |  |
| 4 |  |  |  |
| *4,5* |  | 80 | 70 |
| 5 | 110 |  |  |
| 6 | 100 |  |  |
| *6,5* |  | 70 | 60 |
| 7 |  |  |  |
| 8 | 90 |  |  |
| 9 |  | 60 | 50 |
| 10 | 80 |  |  |
| 11 |  |  |  |
| 12 | 70 | 50 |  |
| 13 |  |  |  |
| 14 |  |  |  |
| 15 | 60 |  |  |
| 16 |  | 40 |  |
| 17 |  |  |  |
| 18 |  |  |  |
| *18,5* | 50 |  |  |
| 19 |  |  |  |
| 20 |  | 30 |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 | 40 |  |  |
| 24 |  |  |  |
| 25 |  |  |  |
| 26 |  |  |  |
| 27 |  | 20 |  |
| 28 |  |  |  |
| 29 | 30 |  |  |
| 30 |  |  |  |
| 31 |  |  |  |
| 32 |  |  |  |
| 33 |  |  |  |
| 34 |  |  |  |
| 35 |  |  |  |
| 36 | 20 |  |  |
| 37 |  |  |  |
| 38 |  |  |  |
| 39 |  |  |  |
| 40 |  |  |  |
| 41 |  |  |  |
| 42 |  |  |  |
| 43 |  |  |  |
| 44 |  |  |  |
| 45 | 10 |  |  |

*Figur 15 Diagram 3, aflæste punkter efter Eᵤ.*

### Diagram 4 — Eₒ = 80 MPa, belastningsklasse 4

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 |  | 120 | 110 |
| 2 |  | 110 | 100 |
| *2,5* | 150 |  |  |
| 3 | 140 | 100 | 90 |
| *3,5* | 130 |  |  |
| 4 |  | 90 | 80 |
| 5 | 120 |  |  |
| *5,5* |  | 80 |  |
| 6 | 110 |  | 70 |
| 7 |  |  |  |
| *7,5* |  | 70 |  |
| 8 | 100 |  | 60 |
| 9 |  |  |  |
| 10 | 90 |  |  |
| *10,5* |  | 60 |  |
| 11 |  |  |  |
| 12 | 80 |  |  |
| 13 |  |  |  |
| 14 |  | 50 |  |
| 15 | 70 |  |  |
| 16 |  |  |  |
| 17 |  |  |  |
| 18 |  |  |  |
| *18,5* | 60 |  |  |
| 19 |  |  |  |
| 20 |  | 40 |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 | 50 |  |  |
| 24 |  |  |  |
| 25 |  |  |  |
| 26 |  | 30 |  |
| 27 |  |  |  |
| 28 |  |  |  |
| 29 | 40 |  |  |
| 30 |  |  |  |
| 31 |  |  |  |
| 32 |  |  |  |
| 33 |  | 20 |  |
| 34 |  |  |  |
| 35 |  |  |  |
| 36 | 30 |  |  |
| 37 |  |  |  |
| 38 |  |  |  |
| 39 |  |  |  |
| 40 |  |  |  |
| 41 |  |  |  |
| 42 |  |  |  |
| 43 |  |  |  |
| 44 |  |  |  |
| 45 | 20 |  |  |

*Figur 16 Diagram 4, aflæste punkter efter Eᵤ.*

### Diagram 5 — Eₒ = 120 MPa, belastningsklasse 5

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | Flere lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 |  | 130 | 120 |
| 2 |  | 120 | 110 |
| *2,5* | 160 | 110 |  |
| 3 | 150 |  | 100 |
| *3,5* | 140 |  |  |
| 4 |  |  |  |
| *4,5* |  | 100 | 90 |
| 5 | 130 |  |  |
| 6 | 120 | 90 | 80 |
| 7 |  |  |  |
| 8 | 110 | 80 | 70 |
| 9 |  |  |  |
| *9,5* |  | 70 |  |
| 10 | 100 |  | 60 |
| 11 |  |  |  |
| 12 | 90 |  |  |
| 13 |  |  |  |
| *13,5* |  | 60 |  |
| 14 |  |  | 50 |
| 15 | 80 |  |  |
| 16 |  |  |  |
| 17 |  |  |  |
| 18 |  |  |  |
| *18,5* | 70 |  |  |
| 19 |  | 50 |  |
| 20 |  |  |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 | 60 |  |  |
| 24 |  |  |  |
| 25 |  | 40 |  |
| 26 |  |  |  |
| 27 |  |  |  |
| 28 |  |  |  |
| 29 | 50 |  |  |
| 30 |  |  |  |
| 31 |  |  |  |
| 32 |  |  |  |
| 33 |  | 30 |  |
| 34 |  |  |  |
| 35 |  |  |  |
| 36 | 40 |  |  |
| 37 |  |  |  |
| 38 |  |  |  |
| 39 |  |  |  |
| 40 |  |  |  |
| 41 |  |  |  |
| 42 |  |  |  |
| 43 |  |  |  |
| 44 |  |  |  |
| 45 | 30 |  |  |

*Figur 17 Diagram 5, aflæste punkter efter Eᵤ.*

### Diagram 6 — Eₒ = 150 MPa, belastningsklasse 6

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | Flere lag t [cm] |
| ---: | ---: | ---: | ---: |
| *0,5* |  |  | 130 |
| 1 |  | 140 |  |
| *1,5* |  | 130 | 120 |
| 2 |  |  |  |
| *2,5* | 170 | 120 | 110 |
| 3 | 160 |  | 100 |
| *3,5* | 150 | 110 |  |
| 4 |  |  |  |
| *4,5* |  | 100 | 90 |
| 5 | 140 |  |  |
| 6 | 130 | 90 |  |
| *6,5* |  |  | 80 |
| 7 |  |  |  |
| 8 | 120 |  |  |
| *8,5* |  | 80 |  |
| 9 |  |  | 70 |
| 10 | 110 |  |  |
| 11 |  |  |  |
| 12 | 100 | 70 | 60 |
| 13 |  |  |  |
| 14 |  |  |  |
| 15 | 90 |  |  |
| 16 |  |  |  |
| 17 |  | 60 |  |
| 18 |  |  | 50 |
| *18,5* | 80 |  |  |
| 19 |  |  |  |
| 20 |  |  |  |
| 21 |  |  |  |
| 22 |  |  |  |
| 23 | 70 |  |  |
| 24 |  | 50 |  |
| 25 |  |  |  |
| 26 |  |  |  |
| 27 |  |  |  |
| 28 |  |  |  |
| 29 | 60 |  |  |
| 30 |  |  |  |
| 31 |  |  |  |
| 32 |  | 40 |  |
| 33 |  |  |  |
| 34 |  |  |  |
| 35 |  |  |  |
| 36 | 50 |  |  |
| 37 |  |  |  |
| 38 |  |  |  |
| 39 |  |  |  |
| 40 |  |  |  |
| 41 |  |  |  |
| 42 |  |  |  |
| 43 |  |  |  |
| 44 |  |  |  |
| 45 | 40 |  |  |

*Figur 18 Diagram 6, aflæste punkter efter Eᵤ.*

## 7 Interpolerede lagtykkelser ved hele Eᵤ

Lagtykkelsen ved hele værdier af Eᵤ bestemmes ud fra de aflæste punkter i afsnit 3, afrundet til nærmeste 0,5 MPa. Mellem to nabopunkter på samme kurve interpoleres lineært. Kurverne er i manualens vektorgrafik tegnet som rette linjestykker mellem punkterne, og interpolationen gengiver derfor den tegnede kurve.

```
t  =  t₁ + (Eᵤ − Eᵤ,₁) / (Eᵤ,₂ − Eᵤ,₁) × (t₂ − t₁)
```

hvor:

- `t` er bærelagstykkelsen ved den aktuelle Eᵤ [cm]
- `Eᵤ` er underbundens E-modul, 1, 2, 3 … MPa
- `Eᵤ,₁`, `Eᵤ,₂` er Eᵤ i de to nabopunkter, der omslutter Eᵤ [MPa]
- `t₁`, `t₂` er bærelagstykkelsen i de to nabopunkter [cm]

Tykkelsen afrundes til én decimal. Der ekstrapoleres ikke: ligger Eᵤ uden for kurvens første eller sidste aflæste punkt, angives en tankestreg. Diagram 1 opstilles for Eᵤ = 1–30 MPa og diagram 2–6 for Eᵤ = 1–45 MPa, svarende til arkene i `geonet_interpolerede_diagrammer.xlsx`.

Værdier med **fed** skrift ligger i et aflæst punkt og er dermed ikke interpoleret.

Der gøres opmærksom på, at kurverne er flade ved små værdier af Eᵤ. Her giver en ændring af de aflæste værdier på få tiendedele MPa en ændring af tykkelsen på flere cm. Interpoleres der i de uafrundede PDF-værdier i stedet for de afrundede, ændres tykkelsen op til 2,3 cm, jf. afsnit 4.3.

### Diagram 1 — Eₒ = 30 MPa, belastningsklasse 1

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] |
| ---: | ---: | ---: |
| 1 | — | 86,7 |
| 2 | — | **80,0** |
| 3 | **110,0** | **70,0** |
| 4 | **100,0** | 65,0 |
| 5 | **90,0** | **60,0** |
| 6 | **80,0** | 53,3 |
| 7 | 75,0 | 48,0 |
| 8 | **70,0** | 44,0 |
| 9 | 63,3 | **40,0** |
| 10 | 58,0 | 36,0 |
| 11 | 54,0 | 32,0 |
| 12 | **50,0** | 28,6 |
| 13 | 46,0 | 25,7 |
| 14 | 42,0 | 22,9 |
| 15 | 38,6 | **20,0** |
| 16 | 35,7 | — |
| 17 | 32,9 | — |
| 18 | **30,0** | — |
| 19 | 26,7 | — |
| 20 | 23,3 | — |
| 21 | **20,0** | — |
| 22 | 17,5 | — |
| 23 | 15,0 | — |
| 24 | 12,5 | — |
| 25 | **10,0** | — |
| 26 | 8,0 | — |
| 27 | 6,0 | — |
| 28 | 4,0 | — |
| 29 | 2,0 | — |
| 30 | **0,0** | — |

*Figur 19 Diagram 1, interpolerede lagtykkelser ved hele Eᵤ.*

### Diagram 2 — Eₒ = 45 MPa, belastningsklasse 2

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 | — | **100,0** | **90,0** |
| 2 | — | **90,0** | **80,0** |
| 3 | **120,0** | **80,0** | **70,0** |
| 4 | 106,7 | 73,3 | 63,3 |
| 5 | **100,0** | 66,7 | 57,5 |
| 6 | **90,0** | **60,0** | 52,5 |
| 7 | 85,0 | 56,7 | — |
| 8 | **80,0** | 53,3 | — |
| 9 | 75,0 | **50,0** | — |
| 10 | **70,0** | 46,7 | — |
| 11 | 65,0 | 43,3 | — |
| 12 | **60,0** | **40,0** | — |
| 13 | 56,7 | 37,5 | — |
| 14 | 53,3 | 35,0 | — |
| 15 | **50,0** | 32,5 | — |
| 16 | 47,1 | **30,0** | — |
| 17 | 44,3 | 27,5 | — |
| 18 | 41,4 | 25,0 | — |
| 19 | 38,9 | 22,5 | — |
| 20 | 36,7 | **20,0** | — |
| 21 | 34,4 | — | — |
| 22 | 32,2 | — | — |
| 23 | **30,0** | — | — |
| 24 | 28,3 | — | — |
| 25 | 26,7 | — | — |
| 26 | 25,0 | — | — |
| 27 | 23,3 | — | — |
| 28 | 21,7 | — | — |
| 29 | **20,0** | — | — |
| 30 | 18,6 | — | — |
| 31 | 17,1 | — | — |
| 32 | 15,7 | — | — |
| 33 | 14,3 | — | — |
| 34 | 12,9 | — | — |
| 35 | 11,4 | — | — |
| 36 | **10,0** | — | — |
| 37 | 8,9 | — | — |
| 38 | 7,8 | — | — |
| 39 | 6,7 | — | — |
| 40 | 5,6 | — | — |
| 41 | 4,4 | — | — |
| 42 | 3,3 | — | — |
| 43 | 2,2 | — | — |
| 44 | 1,1 | — | — |
| 45 | **0,0** | — | — |

*Figur 20 Diagram 2, interpolerede lagtykkelser ved hele Eᵤ.*

### Diagram 3 — Eₒ = 60 MPa, belastningsklasse 3

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 | — | **110,0** | **100,0** |
| 2 | — | 96,7 | 85,0 |
| 3 | **130,0** | **90,0** | 77,5 |
| 4 | 116,7 | 83,3 | 72,5 |
| 5 | **110,0** | 77,5 | 67,5 |
| 6 | **100,0** | 72,5 | 62,5 |
| 7 | 95,0 | 68,0 | 58,0 |
| 8 | **90,0** | 64,0 | 54,0 |
| 9 | 85,0 | **60,0** | **50,0** |
| 10 | **80,0** | 56,7 | — |
| 11 | 75,0 | 53,3 | — |
| 12 | **70,0** | **50,0** | — |
| 13 | 66,7 | 47,5 | — |
| 14 | 63,3 | 45,0 | — |
| 15 | **60,0** | 42,5 | — |
| 16 | 57,1 | **40,0** | — |
| 17 | 54,3 | 37,5 | — |
| 18 | 51,4 | 35,0 | — |
| 19 | 48,9 | 32,5 | — |
| 20 | 46,7 | **30,0** | — |
| 21 | 44,4 | 28,6 | — |
| 22 | 42,2 | 27,1 | — |
| 23 | **40,0** | 25,7 | — |
| 24 | 38,3 | 24,3 | — |
| 25 | 36,7 | 22,9 | — |
| 26 | 35,0 | 21,4 | — |
| 27 | 33,3 | **20,0** | — |
| 28 | 31,7 | — | — |
| 29 | **30,0** | — | — |
| 30 | 28,6 | — | — |
| 31 | 27,1 | — | — |
| 32 | 25,7 | — | — |
| 33 | 24,3 | — | — |
| 34 | 22,9 | — | — |
| 35 | 21,4 | — | — |
| 36 | **20,0** | — | — |
| 37 | 18,9 | — | — |
| 38 | 17,8 | — | — |
| 39 | 16,7 | — | — |
| 40 | 15,6 | — | — |
| 41 | 14,4 | — | — |
| 42 | 13,3 | — | — |
| 43 | 12,2 | — | — |
| 44 | 11,1 | — | — |
| 45 | **10,0** | — | — |

*Figur 21 Diagram 3, interpolerede lagtykkelser ved hele Eᵤ.*

### Diagram 4 — Eₒ = 80 MPa, belastningsklasse 4

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | 2 lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 | — | **120,0** | **110,0** |
| 2 | — | **110,0** | **100,0** |
| 3 | **140,0** | **100,0** | **90,0** |
| 4 | 126,7 | **90,0** | **80,0** |
| 5 | **120,0** | 83,3 | 75,0 |
| 6 | **110,0** | 77,5 | **70,0** |
| 7 | 105,0 | 72,5 | 65,0 |
| 8 | **100,0** | 68,3 | **60,0** |
| 9 | 95,0 | 65,0 | — |
| 10 | **90,0** | 61,7 | — |
| 11 | 85,0 | 58,6 | — |
| 12 | **80,0** | 55,7 | — |
| 13 | 76,7 | 52,9 | — |
| 14 | 73,3 | **50,0** | — |
| 15 | **70,0** | 48,3 | — |
| 16 | 67,1 | 46,7 | — |
| 17 | 64,3 | 45,0 | — |
| 18 | 61,4 | 43,3 | — |
| 19 | 58,9 | 41,7 | — |
| 20 | 56,7 | **40,0** | — |
| 21 | 54,4 | 38,3 | — |
| 22 | 52,2 | 36,7 | — |
| 23 | **50,0** | 35,0 | — |
| 24 | 48,3 | 33,3 | — |
| 25 | 46,7 | 31,7 | — |
| 26 | 45,0 | **30,0** | — |
| 27 | 43,3 | 28,6 | — |
| 28 | 41,7 | 27,1 | — |
| 29 | **40,0** | 25,7 | — |
| 30 | 38,6 | 24,3 | — |
| 31 | 37,1 | 22,9 | — |
| 32 | 35,7 | 21,4 | — |
| 33 | 34,3 | **20,0** | — |
| 34 | 32,9 | — | — |
| 35 | 31,4 | — | — |
| 36 | **30,0** | — | — |
| 37 | 28,9 | — | — |
| 38 | 27,8 | — | — |
| 39 | 26,7 | — | — |
| 40 | 25,6 | — | — |
| 41 | 24,4 | — | — |
| 42 | 23,3 | — | — |
| 43 | 22,2 | — | — |
| 44 | 21,1 | — | — |
| 45 | **20,0** | — | — |

*Figur 22 Diagram 4, interpolerede lagtykkelser ved hele Eᵤ.*

### Diagram 5 — Eₒ = 120 MPa, belastningsklasse 5

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | Flere lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 | — | **130,0** | **120,0** |
| 2 | — | **120,0** | **110,0** |
| 3 | **150,0** | 107,5 | **100,0** |
| 4 | 136,7 | 102,5 | 93,3 |
| 5 | **130,0** | 96,7 | 86,7 |
| 6 | **120,0** | **90,0** | **80,0** |
| 7 | 115,0 | 85,0 | 75,0 |
| 8 | **110,0** | **80,0** | **70,0** |
| 9 | 105,0 | 73,3 | 65,0 |
| 10 | **100,0** | 68,8 | **60,0** |
| 11 | 95,0 | 66,3 | 57,5 |
| 12 | **90,0** | 63,8 | 55,0 |
| 13 | 86,7 | 61,3 | 52,5 |
| 14 | 83,3 | 59,1 | **50,0** |
| 15 | **80,0** | 57,3 | — |
| 16 | 77,1 | 55,5 | — |
| 17 | 74,3 | 53,6 | — |
| 18 | 71,4 | 51,8 | — |
| 19 | 68,9 | **50,0** | — |
| 20 | 66,7 | 48,3 | — |
| 21 | 64,4 | 46,7 | — |
| 22 | 62,2 | 45,0 | — |
| 23 | **60,0** | 43,3 | — |
| 24 | 58,3 | 41,7 | — |
| 25 | 56,7 | **40,0** | — |
| 26 | 55,0 | 38,8 | — |
| 27 | 53,3 | 37,5 | — |
| 28 | 51,7 | 36,3 | — |
| 29 | **50,0** | 35,0 | — |
| 30 | 48,6 | 33,8 | — |
| 31 | 47,1 | 32,5 | — |
| 32 | 45,7 | 31,3 | — |
| 33 | 44,3 | **30,0** | — |
| 34 | 42,9 | — | — |
| 35 | 41,4 | — | — |
| 36 | **40,0** | — | — |
| 37 | 38,9 | — | — |
| 38 | 37,8 | — | — |
| 39 | 36,7 | — | — |
| 40 | 35,6 | — | — |
| 41 | 34,4 | — | — |
| 42 | 33,3 | — | — |
| 43 | 32,2 | — | — |
| 44 | 31,1 | — | — |
| 45 | **30,0** | — | — |

*Figur 23 Diagram 5, interpolerede lagtykkelser ved hele Eᵤ.*

### Diagram 6 — Eₒ = 150 MPa, belastningsklasse 6

| Eᵤ [MPa] | Ustabiliseret t [cm] | 1 lag t [cm] | Flere lag t [cm] |
| ---: | ---: | ---: | ---: |
| 1 | — | **140,0** | 125,0 |
| 2 | — | 125,0 | 115,0 |
| 3 | **160,0** | 115,0 | **100,0** |
| 4 | 146,7 | 105,0 | 93,3 |
| 5 | **140,0** | 96,7 | 87,5 |
| 6 | **130,0** | **90,0** | 82,5 |
| 7 | 125,0 | 86,0 | 78,0 |
| 8 | **120,0** | 82,0 | 74,0 |
| 9 | 115,0 | 78,6 | **70,0** |
| 10 | **110,0** | 75,7 | 66,7 |
| 11 | 105,0 | 72,9 | 63,3 |
| 12 | **100,0** | **70,0** | **60,0** |
| 13 | 96,7 | 68,0 | 58,3 |
| 14 | 93,3 | 66,0 | 56,7 |
| 15 | **90,0** | 64,0 | 55,0 |
| 16 | 87,1 | 62,0 | 53,3 |
| 17 | 84,3 | **60,0** | 51,7 |
| 18 | 81,4 | 58,6 | **50,0** |
| 19 | 78,9 | 57,1 | — |
| 20 | 76,7 | 55,7 | — |
| 21 | 74,4 | 54,3 | — |
| 22 | 72,2 | 52,9 | — |
| 23 | **70,0** | 51,4 | — |
| 24 | 68,3 | **50,0** | — |
| 25 | 66,7 | 48,8 | — |
| 26 | 65,0 | 47,5 | — |
| 27 | 63,3 | 46,3 | — |
| 28 | 61,7 | 45,0 | — |
| 29 | **60,0** | 43,8 | — |
| 30 | 58,6 | 42,5 | — |
| 31 | 57,1 | 41,3 | — |
| 32 | 55,7 | **40,0** | — |
| 33 | 54,3 | — | — |
| 34 | 52,9 | — | — |
| 35 | 51,4 | — | — |
| 36 | **50,0** | — | — |
| 37 | 48,9 | — | — |
| 38 | 47,8 | — | — |
| 39 | 46,7 | — | — |
| 40 | 45,6 | — | — |
| 41 | 44,4 | — | — |
| 42 | 43,3 | — | — |
| 43 | 42,2 | — | — |
| 44 | 41,1 | — | — |
| 45 | **40,0** | — | — |

*Figur 24 Diagram 6, interpolerede lagtykkelser ved hele Eᵤ.*

## 8 Sammenligning med den hidtidige opslagstabel

Lagtykkelserne i afsnit 7 er sammenholdt med `geonet_interpolerede_diagrammer.xlsx`, som indtil 24.09.2026 indeholdt de samme værdier som standardtabellerne i `core/data.py`. Standardtabellerne er herefter rettet til afsnit 7, og regnearket gengiver dermed den hidtidige opslagstabel.

Afvigelsen er angivet som Δ = afsnit 7 − regneark. En positiv Δ betyder, at den hidtidige tabel angiver en mindre tykkelse end afsnit 7.

| Diagram | Kurve | Rækker | Samme rækker udfyldt | Middel Δ [cm] | Største \|Δ\| [cm] | \|Δ\| ≥ 1 cm | \|Δ\| ≥ 2 cm |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Ustabiliseret | 28 | ja | 0,1 | 4,1 | 3 | 2 |
| 1 | 1 lag | 15 | ja | 0,2 | 0,6 | 0 | 0 |
| 2 | Ustabiliseret | 43 | ja | 0,3 | 1,4 | 4 | 0 |
| 2 | 1 lag | 20 | ja | 0,1 | 3,5 | 6 | 1 |
| 2 | 2 lag | 6 | ja | 0,1 | 0,3 | 0 | 0 |
| 3 | Ustabiliseret | 43 | ja | 0,3 | 2,3 | 3 | 2 |
| 3 | 1 lag | 27 | ja | 0,3 | 1,0 | 2 | 0 |
| 3 | 2 lag | 9 | ja | 0,2 | 5,4 | 3 | 2 |
| 4 | Ustabiliseret | 43 | ja | 0,4 | 5,5 | 4 | 3 |
| 4 | 1 lag | 33 | ja | −0,1 | 3,5 | 4 | 1 |
| 4 | 2 lag | 8 | ja | 0,1 | 0,5 | 0 | 0 |
| 5 | Ustabiliseret | 43 | ja | 0,2 | 0,8 | 0 | 0 |
| 5 | 1 lag | 33 | ja | 0,0 | 2,5 | 3 | 1 |
| 5 | Flere lag | 14 | ja | 1,3 | 4,1 | 7 | 4 |
| 6 | Ustabiliseret | 43 | ja | 0,2 | 0,8 | 0 | 0 |
| 6 | 1 lag | 32 | ja | 0,2 | 0,6 | 0 | 0 |
| 6 | Flere lag | 18 | ja | 1,0 | 5,0 | 5 | 2 |

*Figur 25 Afvigelser pr. diagram og kurve.*

Rækker med en afvigelse på 1 cm eller mere er vist nedenfor. Kolonnen *Aflæst punkt* angiver, om Eᵤ falder i et aflæst punkt, så værdien i afsnit 7 ikke er interpoleret. Opmærksomheden henledes på, at et aflæst punkt her er bestemt med afrundet Eᵤ, jf. afsnit 3; også disse værdier er derfor behæftet med usikkerheden i kurvernes flade ende.

| Diagram | Kurve | Eᵤ [MPa] | Afsnit 7 t [cm] | Regneark t [cm] | Δ [cm] | Aflæst punkt |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Ustabiliseret | 4 | 100,0 | 95,9 | +4,1 | ja |
| 1 | Ustabiliseret | 9 | 63,3 | 65,0 | −1,7 |  |
| 1 | Ustabiliseret | 10 | 58,0 | 60,0 | −2,0 |  |
| 2 | Ustabiliseret | 17 | 44,3 | 43,0 | +1,3 |  |
| 2 | Ustabiliseret | 18 | 41,4 | 40,0 | +1,4 |  |
| 2 | Ustabiliseret | 19 | 38,9 | 37,6 | +1,3 |  |
| 2 | Ustabiliseret | 20 | 36,7 | 35,5 | +1,2 |  |
| 2 | 1 lag | 3 | 80,0 | 83,5 | −3,5 | ja |
| 2 | 1 lag | 4 | 73,3 | 75,0 | −1,7 |  |
| 2 | 1 lag | 14 | 35,0 | 34,0 | +1,0 |  |
| 2 | 1 lag | 15 | 32,5 | 31,3 | +1,2 |  |
| 2 | 1 lag | 16 | 30,0 | 28,8 | +1,2 | ja |
| 2 | 1 lag | 17 | 27,5 | 26,4 | +1,1 |  |
| 3 | Ustabiliseret | 7 | 95,0 | 92,8 | +2,2 |  |
| 3 | Ustabiliseret | 8 | 90,0 | 87,7 | +2,3 | ja |
| 3 | Ustabiliseret | 9 | 85,0 | 83,9 | +1,1 |  |
| 3 | 1 lag | 2 | 96,7 | 95,7 | +1,0 |  |
| 3 | 1 lag | 24 | 24,3 | 23,3 | +1,0 |  |
| 3 | 2 lag | 1 | 100,0 | 94,6 | +5,4 | ja |
| 3 | 2 lag | 2 | 85,0 | 86,3 | −1,3 |  |
| 3 | 2 lag | 3 | 77,5 | 80,0 | −2,5 |  |
| 4 | Ustabiliseret | 4 | 126,7 | 124,5 | +2,2 |  |
| 4 | Ustabiliseret | 5 | 120,0 | 114,5 | +5,5 | ja |
| 4 | Ustabiliseret | 6 | 110,0 | 107,4 | +2,6 | ja |
| 4 | Ustabiliseret | 7 | 105,0 | 103,7 | +1,3 |  |
| 4 | 1 lag | 4 | 90,0 | 93,5 | −3,5 | ja |
| 4 | 1 lag | 5 | 83,3 | 84,7 | −1,4 |  |
| 4 | 1 lag | 7 | 72,5 | 73,5 | −1,0 |  |
| 4 | 1 lag | 8 | 68,3 | 70,0 | −1,7 |  |
| 5 | 1 lag | 3 | 107,5 | 110,0 | −2,5 |  |
| 5 | 1 lag | 9 | 73,3 | 74,7 | −1,4 |  |
| 5 | 1 lag | 10 | 68,8 | 70,0 | −1,2 |  |
| 5 | Flere lag | 2 | 110,0 | 105,9 | +4,1 | ja |
| 5 | Flere lag | 4 | 93,3 | 90,0 | +3,3 |  |
| 5 | Flere lag | 5 | 86,7 | 82,8 | +3,9 |  |
| 5 | Flere lag | 6 | 80,0 | 77,7 | +2,3 | ja |
| 5 | Flere lag | 7 | 75,0 | 73,9 | +1,1 |  |
| 5 | Flere lag | 12 | 55,0 | 53,7 | +1,3 |  |
| 5 | Flere lag | 13 | 52,5 | 51,4 | +1,1 |  |
| 6 | Flere lag | 1 | 125,0 | 120,0 | +5,0 |  |
| 6 | Flere lag | 2 | 115,0 | 110,0 | +5,0 |  |
| 6 | Flere lag | 14 | 56,7 | 55,6 | +1,1 |  |
| 6 | Flere lag | 15 | 55,0 | 53,7 | +1,3 |  |
| 6 | Flere lag | 16 | 53,3 | 52,1 | +1,2 |  |

*Figur 26 Rækker med |Δ| ≥ 1 cm.*
