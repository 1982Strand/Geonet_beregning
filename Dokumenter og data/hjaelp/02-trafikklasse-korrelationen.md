---
titel: Trafikklasse-korrelationen
resume: Hvad Eₒ-matricen på korrelationssiden viser, hvad zonerne under og over betyder, hvordan der kan dimensioneres uden for diagrammernes område, og hvad der sker, når en kørsel rettes.
---

## 1 Hvad tabellen viser

Korrelationssidens Eₒ,ækv-matrix omsætter hver af de 48 VejDim-kørsler til den
designdiagram-kurve, hvis ustabiliserede lagtykkelse svarer til kørslens krav.
Ved dimensionering efter trafikklasse er det denne matrix, der slås op i - ikke
kørslerne direkte.

Matricen anvendes alene ved dimensionering efter trafikklasse. Vælges
belastningsklasse, henviser klassen direkte til sit designdiagram, og
korrelationen indgår ikke, jf. kapitel 1, afsnit 2.

Matricen er afledt: den genberegnes af kørslerne og af det aktive
designdiagram. Ændres et af de to grundlag, kan celler skifte værdi eller zone.

:::figur Ækvivalent Eₒ for T4 ved tre Eᵤ-værdier. Begge rækker interpoleres uafhængigt.
| T4 ved | t_ubundet | Eₒ,ækv |
| --- | --- | --- |
| 5 MPa | 1.184 | 90 |
| 8 MPa | 1.038 | 95 |
| 10 MPa | 969 | 99 |
:::

## 2 Zonerne under og over

Designdiagrammerne omfatter alene kurverne Eₒ = 30–150 MPa. Der foretages ikke
ekstrapolation. Fire udfald er mulige for en given celle:

- **et tal** — krydsningspunktet ligger inden for diagrammernes spænd, og
  Eₒ,ækv bestemmes ved lineær interpolation mellem de to nærmeste kurver.
- **under** — Den krævede tykkelse af de ubundne lag bestemt i VejDim er tyndere end designdiagrammets tyndeste kurve
  (Diagram 1, Eₒ = 30 MPa). Eksempelvis kræver T1 ved Eᵤ = 5 MPa 560 mm, mens kurven for
  Eₒ = 30 MPa ligger på 900 mm.
- **over** — Den krævede tykkelse af de ubundne lag bestemt i VejDim er tykkere end diagrammets tykkeste kurve
  (Diagram 6, Eₒ = 150 MPa). Eksempelvis kræver T6 ved Eᵤ = 10 MPa 1.146 mm, mens kurven
  for Eₒ = 150 MPa slutter ved 1.100 mm.

Vælges en celle i zonen under eller over ved dimensioneringen, vises den
tilsvarende advarsel i stedet for resultater, medmindre dimensionering på
VejDims tal er tilvalgt, jf. afsnit 3.

Sammenkædningen er gyldig i kernezonen, som omfatter 30 af
tabellens 48 celler — typisk T2–T4 ved middel underbund og de lave
trafikklasser ved stiv underbund. I kernezonen ligger reduktionerne på 25–47 %
med en middelværdi på 30 %, hvilket svarer til niveauet ved dimensionering
efter belastningsklasse.

## 3 Dimensionering uden for diagrammernes område

Uden for diagrammernes tykkelsesområde kan dimensioneringen gennemføres på
VejDims tal. Tilvalget sættes med afkrydsningsfeltet **Anvend VejDims tal
uden for diagrammet**, som står både i dimensioneringens trin 1 og på
korrelationssiden. De to felter er ét og samme tilvalg. Feltet er fravalgt ved
opstart, og indstillingen gendannes ikke ved næste opstart.

Fremgangsmåden er, at den ubundne tykkelse fastlægges af VejDims krav, mens
reduktionen aflæses på diagrammets nærmeste randkurve. Opslaget sker dermed på
randkurven, skaleret til VejDims tykkelse:

:::formel
t_armeret = t_VejDim × (1 − r_rand) × (1 + k_φ + k_net)
--
t_VejDim  er VejDims krævede ubundne tykkelse, SG + BL
r_rand    er reduktionen aflæst på randkurven ved samme Eᵤ
k_φ       er korrektionen for friktionsvinklen
k_net     er korrektionen for det valgte geonet
:::

Skaleringen rammer den armerede og den ustabiliserede tykkelse ens.
Reduktionsprocenten er derfor randkurvens egen og påvirkes ikke af tilvalget.

Inden for diagrammernes område er skalaen 1,0, idet Eₒ,ækv per definition er
den kurve, hvis ustabiliserede tykkelse svarer til VejDims krav. Tilvalget har
dermed ingen virkning i kernezonen; de 30 celler giver samme resultat, hvad
enten det er sat eller ej. Uden for området ligger skalaen mellem 0,562 og
1,262 for standardkørslerne og angives sammen med resultatet.

Opmærksomheden henledes på, at reduktionen i disse celler er aflæst på
randkurven og dermed ekstrapoleret. Den er ikke bestemt i driftspunktet, og
afvigelsen fra randkurven bør derfor indgå i vurderingen af resultatet.

Tilvalget udvider dækningen fra 26 til 40 af de 48 celler ved ét lag geonet og
fra 11 til 15 celler ved to lag. De øvrige celler kan ikke beregnes, uanset
tilvalget: diagrammets armerede kurver ophører ved lavere Eᵤ end de
ustabiliserede, og ved Eᵤ = 40 MPa findes ingen armeret kurve ved nogen Eₒ.

:::figur Højeste Eᵤ med data for ét lag geonet, pr. Eₒ-kurve.
| Eₒ-kurve | 1 lag findes til og med |
| --- | --- |
| 30 MPa | Eᵤ = 15 |
| 45 MPa | Eᵤ = 20 |
| 60 MPa | Eᵤ = 27 |
| 80 MPa | Eᵤ = 33 |
| 120 MPa | Eᵤ = 33 |
| 150 MPa | Eᵤ = 32 |
:::

I matricen mærkes cellerne uden for diagrammernes område med `*`, når
tilvalget er sat. En celle, der viser `—`, mangler armeret kurve og kan ikke
beregnes.

## 4 Redigering af kørslerne

Kørslerne kan overskrives, hvis VejDim-kørslerne ønskes justeret manuelt. Ændres en kørsel, genberegnes Eₒ,ækv-matricen og anvendes med det
samme i dimensioneringen.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eₒ,ækv bestemmes ud fra; Samlet
højde er inklusive de bundne lag øverst.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
