---
titel: Trafikklasse-korrelationen
resume: Hvad Eₒ-matricen på korrelationssiden viser, hvad zonerne under og over betyder, hvordan de kan dimensioneres på VejDims tal, og hvad der sker, når en kørsel rettes.
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

Designdiagrammerne omfatter kurverne Eₒ = 30–150 MPa. Falder VejDims krav uden
for det spænd, findes der intet driftspunkt at aflæse i, og cellen bærer en
zonebetegnelse frem for et tal:

- **under** — kravet er tyndere end diagrammernes tyndeste kurve (Diagram 1,
  Eₒ = 30 MPa). T1 ved Eᵤ = 5 MPa kræver 560 mm, hvor kurven ligger på 900 mm.
  Zonen omfatter 5 celler: de laveste trafikklasser på blød underbund.
- **over** — kravet er tykkere end den tykkeste kurve (Diagram 6,
  Eₒ = 150 MPa). T6 ved Eᵤ = 10 MPa kræver 1.146 mm, hvor kurven slutter ved
  1.100 mm. Zonen omfatter 13 celler: de høje trafikklasser på stiv underbund.
- **mangler** — cellen har ingen kørselsdata, idet den ubundne tykkelse er
  angivet til nul.

De øvrige 30 celler udgør kernezonen, hvor reduktionen aflæses i selve
driftspunktet. Her ligger den ved ét lag geonet på 25–47 % med en middelværdi
på 30 %, hvilket svarer til niveauet ved dimensionering efter
belastningsklasse.

Vælges en celle i zonen under eller over, vises zonebeskeden i stedet for
resultater. Dimensioneringen kan dog gennemføres på VejDims tal, jf. afsnit 3.

## 3 Dimensionering på VejDims tal

Uden for diagrammernes område kan dimensioneringen henlægges til den nærmeste
randkurve med afkrydsningsfeltet **Anvend VejDims tal uden for diagrammet**,
som står både i dimensioneringens trin 1 og på korrelationssiden. De to felter
er ét og samme tilvalg. Feltet er fravalgt ved opstart og gendannes ikke ved
næste opstart.

Fremgangsmåden er, at den ubundne tykkelse fastholdes som VejDims krav, mens
reduktionsprocenten aflæses på randkurven ved samme Eᵤ:

:::formel
t_armeret = t_VejDim × (1 − r_rand) × (1 + k_φ + k_net)
--
t_VejDim  er VejDims krævede ubundne tykkelse, SG + BL
r_rand    er reduktionen aflæst på randkurven ved samme Eᵤ
k_φ       er korrektionen for friktionsvinklen
k_net     er korrektionen for det valgte geonet
:::

Aflæsningen sker altså på randkurven, skaleret med forholdet
`t_VejDim / t_rand`. Skaleringen rammer den armerede og den ustabiliserede
tykkelse ens, hvorved reduktionsprocenten forbliver randkurvens egen.
Arbejdsdelingen fra kapitel 1 er dermed uændret: VejDim fastlægger alene
lagtykkelsen, og reduktionen er designdiagrammets feltdokumenterede værdi.

:::figur Trafikklasse T1 ved Eᵤ = 8 MPa, ét lag geonet. Cellen ligger i zonen under.
| Trin | Værdi |
| --- | --- |
| VejDims krav, interpoleret | 489 mm |
| Diagram 1 ved Eᵤ = 8, ustabiliseret | 700 mm |
| Diagram 1 ved Eᵤ = 8, 1 lag | 437 mm |
| Reduktion på randkurven | 37,6 % |
| Skala 489 / 700 | 0,699 |
| Resultat 489 × (1 − 0,376) | 306 mm |
:::

Figuren viser regnegangen for en celle i zonen under. VejDims krav ligger her
under diagrammernes tyndeste kurve, og reduktionen hentes derfor på Diagram 1
og anvendes på VejDims tykkelse.

Inden for diagrammernes område er skalaen 1,0, idet Eₒ,ækv per definition er
den kurve, hvis ustabiliserede tykkelse svarer til VejDims krav. Tilvalget har
derfor ingen virkning i kernezonen. Uden for området ligger skalaen mellem
0,562 og 1,262 for standardkørslerne og angives sammen med resultatet.

Opmærksomheden henledes på, at reduktionen i disse celler er aflæst uden for
driftspunktet og dermed er ekstrapoleret, jf. kapitel 7, afsnit 2. I matricen
mærkes cellerne med `*`, når tilvalget er sat.

## 4 Redigering af kørslerne

Kørslerne kan overskrives, hvis VejDim-kørslerne ønskes justeret manuelt. Ændres en kørsel, genberegnes Eₒ,ækv-matricen og anvendes med det
samme i dimensioneringen.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eₒ,ækv bestemmes ud fra; Samlet
højde er inklusive de bundne lag øverst.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
