---
titel: Trafikklasse-korrelationen
resume: Hvad Eo-matricen på korrelationssiden viser, hvad zonerne under og over betyder, og hvad der sker, når en kørsel rettes.
---

## 1 Hvad tabellen viser

Korrelationssidens Eo_ækv-matrix omsætter hver af de 48 VejDim-kørsler til den
designdiagram-kurve, hvis ustabiliserede lagtykkelse svarer til kørslens krav.
Ved dimensionering efter trafikklasse er det denne matrix, der slås op i - ikke
kørslerne direkte.

Matricen anvendes alene ved dimensionering efter trafikklasse. Vælges
belastningsklasse, henviser klassen direkte til sit designdiagram, og
korrelationen indgår ikke, jf. kapitel 1, afsnit 2.

Matricen er afledt: den genberegnes af kørslerne og af det aktive
designdiagram. Ændres et af de to grundlag, kan celler skifte værdi eller zone.

:::figur Ækvivalent Eo for T4 ved tre Eu-værdier. Begge rækker interpoleres uafhængigt.
| T4 ved | t_ubundet | Eo_ækv |
| --- | --- | --- |
| 5 MPa | 1.184 | 90 |
| 8 MPa | 1.038 | 95 |
| 10 MPa | 969 | 99 |
:::

## 2 Zonerne under og over

Designdiagrammerne omfatter alene kurverne Eo = 30–150 MPa. Der foretages ikke
ekstrapolation. Fire udfald er mulige for en given celle:

- **et tal** — krydsningspunktet ligger inden for diagrammernes spænd, og
  Eo_ækv bestemmes ved lineær interpolation mellem de to nærmeste kurver.
- **under** — Den krævede tykkelse af de ubundne lag bestemt i VejDim er tyndere end designdiagrammets tyndeste kurve
  (Diagram 1, Eo = 30 MPa). Eksempelvis kræver T1 ved Eu = 5 MPa 560 mm, mens kurven for
  Eo = 30 MPa ligger på 900 mm. I dette tilfælde anses dimensioneringen i Trafikklasse som ugyldig.
- **over** — Den krævede tykkelse af de ubundne lag bestemt i VejDim er tykkere end diagrammets tykkeste kurve
  (Diagram 6, Eo = 150 MPa). Eksempelvis kræver T6 ved Eu = 10 MPa 1.146 mm, mens kurven
  for Eo = 150 MPa slutter ved 1.100 mm. Her anses dimensioneringen i Trafikklasse også for ugyldig.

Vælges en celle i zonen under eller over ved dimensioneringen, vises den
tilsvarende advarsel i stedet for resultater.

Sammenkædningen er gyldig i kernezonen, som omfatter 30 af
tabellens 48 celler — typisk T2–T4 ved middel underbund og de lave
trafikklasser ved stiv underbund. I kernezonen ligger reduktionerne på 25–47 %
med en middelværdi på 30 %, hvilket svarer til niveauet ved dimensionering
efter belastningsklasse.

## 3 Redigering af kørslerne

Kørslerne kan overskrives, hvis VejDim-kørslerne ønskes justeret manuelt. Ændres en kørsel, genberegnes Eo_ækv-matricen og anvendes med det
samme i dimensioneringen.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eo_ækv bestemmes ud fra; Samlet
højde er inklusive de bundne lag øverst.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
