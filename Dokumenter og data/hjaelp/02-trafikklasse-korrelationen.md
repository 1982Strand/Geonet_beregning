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
| 10 MPa | 969 | 108 |
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

De øvrige 30 celler udgør kernezonen, hvor reduktionen aflæses i selve
driftspunktet. Her ligger den ved ét lag geonet på 25–47 % med en middelværdi
på 30 %, hvilket svarer til niveauet ved dimensionering efter
belastningsklasse.

Vælges en celle i zonen under eller over, vises zonebeskeden i stedet for
resultater. Dimensioneringen kan dog gennemføres på VejDims tal, jf. afsnit 3.

## 3 Dimensionering på VejDims tal

Opslaget i designdiagrammerne sker i de ustabiliserede tykkelser: ved
underbundens E-modul giver de seks diagrammer hver sin tykkelse, og VejDims
krav henføres til det sted, hvor tykkelsen passer, jf. kapitel 1, afsnit 4.
Reduktionen aflæses derefter samme sted. Eₒ er alene betegnelsen for
opslagsstedet og indgår ikke som en fysisk størrelse.

:::figur De seks diagrammer ved Eᵤ = 8 MPa. T1 kræver 489 mm og falder uden for.
| Diagram | Uden geonet | 1 lag | Reduktion |
| --- | --- | --- | --- |
| 1 | 700 mm | 437 mm | 37,6 % |
| 2 | 800 mm | 530 mm | 33,8 % |
| 3 | 877 mm | 638 mm | 27,3 % |
| 4 | 1.000 mm | 700 mm | 30,0 % |
| 5 | 1.100 mm | 800 mm | 27,3 % |
| 6 | 1.200 mm | 817 mm | 31,9 % |
:::

Falder VejDims krav uden for de seks tykkelser, findes der intet opslagssted.
Diagrammerne dækker ikke en så tynd henholdsvis tyk opbygning ved den
pågældende underbund. Med tilvalget **Anvend VejDims tal uden for diagrammet**
hentes reduktionsprocenten da ved den nærmeste af de seks kurver og anvendes
på VejDims krav. Feltet står både i dimensioneringens trin 1 og på
korrelationssiden; de to felter er ét og samme tilvalg, og det er fravalgt ved
opstart.

Fremgangsmåden hviler på én forudsætning. Lagtykkelsen fastlægges uændret af
VejDim og er dermed lige så veldokumenteret som i de øvrige celler, og
reduktionsprocenten er ligeledes en aflæst værdi fra feltforsøgene — blot
aflæst ved randkurven og ikke i driftspunktet. Det forudsættes alene, at
reduktionsprocenten holder, når opbygningen bliver tyndere henholdsvis tykkere
end den, diagrammet dækker.

:::formel
t_armeret = t_VejDim × (1 − r_rand) × (1 + k_φ + k_net)
--
t_VejDim  er VejDims krævede ubundne tykkelse, SG + BL
r_rand    er reduktionen aflæst på randkurven ved samme Eᵤ
k_φ       er korrektionen for friktionsvinklen
k_net     er korrektionen for det valgte geonet
:::

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

Inden for diagrammernes område er randkurven og opslagsstedet det samme, og
tilvalget ændrer derfor intet i kernezonens 30 celler. Uden for området
angives forholdet mellem VejDims krav og randkurvens tykkelse sammen med
resultatet. For de celler, der kan beregnes, ligger det mellem 0,562 og 1,262.
I matricen mærkes cellerne med `*`.

Forbeholdet ved fremgangsmåden er beskrevet i kapitel 7, afsnit 2.

## 4 Redigering af kørslerne

Kørslerne kan overskrives, hvis VejDim-kørslerne ønskes justeret manuelt. Ændres en kørsel, genberegnes Eₒ,ækv-matricen og anvendes med det
samme i dimensioneringen.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eₒ,ækv bestemmes ud fra; Samlet
højde er inklusive de bundne lag øverst.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
