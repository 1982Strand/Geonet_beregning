---
titel: Trafikklasse-korrelationen
resume: Hvad Eo-matricen på korrelationssiden viser, hvad zonerne under og over betyder, og hvad der sker, når en kørsel rettes.
---

## 1 Hvad tabellen viser

Korrelationssidens Eo_ækv-matrix omsætter hver af de 48 VejDim-kørsler til den
designdiagram-kurve, hvis ustabiliserede lagtykkelse svarer til kørslens krav.
Ved dimensionering efter trafikklasse er det denne matrix, der slås op i — ikke
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

## 2 Zonerne under, over og mangler

Designdiagrammerne omfatter alene kurverne Eo = 30–150 MPa. Der foretages ikke
ekstrapolation. Fire udfald er mulige for en given celle:

- **et tal** — krydsningspunktet ligger inden for diagrammernes spænd, og
  Eo_ækv bestemmes ved lineær interpolation mellem de to nærmeste kurver.
- **under** — kørslens krav er tyndere end diagrammets tyndeste kurve
  (Eo = 30 MPa). Eksempelvis kræver T1 ved Eu = 5 MPa 560 mm, mens kurven for
  Eo = 30 MPa ligger på 900 mm. Reduktionen kan ikke bestemmes, og
  belastningsklassegrundlaget bør anvendes. I praksis er frostkravet ofte
  styrende for totalhøjden i disse tilfælde.
- **over** — kørslens krav er tykkere end diagrammets tykkeste kurve
  (Eo = 150 MPa). Eksempelvis kræver T6 ved Eu = 10 MPa 1.146 mm, mens kurven
  for Eo = 150 MPa slutter ved 1.100 mm. Kurverne forlænges ikke ud over
  feltforsøgenes gyldighedsområde, og der henvises til en konkret
  VejDim-beregning.
- **mangler** — cellen indeholder endnu ingen VejDim-kørsel, idet den ubundne
  lagtykkelse er 0. Cellen indgår hverken i opslaget eller i interpolationen,
  før den udfyldes.

Vælges en celle i zonen under eller over ved dimensioneringen, vises den
tilsvarende meddelelse i stedet for resultater.

Sammenkædningen er gyldig i en veldefineret kernezone, som omfatter 30 af
tabellens 48 celler — typisk T2–T4 ved middel underbund og de lave
trafikklasser ved stiv underbund. I kernezonen ligger reduktionerne på 25–47 %
med en middelværdi på 30 %, hvilket svarer til niveauet ved dimensionering
efter belastningsklasse.

## 3 Redigering af kørslerne

Kørslerne kan overskrives, hvis en konkret VejDim-beregning findes for
projektet. Ændres en kørsel, genberegnes Eo_ækv-matricen og anvendes med det
samme i dimensioneringen; der er ingen særskilt gem-og-genindlæs-handling.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eo_ækv bestemmes ud fra; Samlet
højde er asfaltpakken hertil og er relevant for frostkontrollen.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
