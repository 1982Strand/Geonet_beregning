# Plan: over/under-håndtering i trafikklasse-korrelationen

**Dato:** 27. september 2026  
**Status:** Implementeret 27. september 2026; afventer gennemsyn i browseren.

## Formål

Ved dimensionering efter trafikklasse placeres VejDims ubundne tykkelse
mellem designdiagrammets ustabiliserede kurver. Ligger den uden for kurverne
— under den laveste eller over den højeste — skal appen håndtere det efter
regler, der kan indstilles, i stedet for enten at afvise eller at følge
VejDim frit i begge retninger.

## Nuværende håndtering

- Inden for kurverne interpoleres der, og der regnes normalt.
- Uden for kurverne afvises beregningen, medmindre fluebenet »Anvend VejDims
  tal uden for diagrammet« i trin 1 er sat.
- Med fluebenet anvendes VejDims tykkelse som ustabiliseret tykkelse, og
  geonettets procentvise reduktion hentes fra randkurven. Det sker i begge
  retninger; ved »under« følges VejDim dermed nedad.

## Målte afvigelser

18 af de 48 standardkørsler ligger uden for kurverne (afvigelse fra
randkurven, u = under, o = over):

| | Eᵤ 3 | Eᵤ 4 | Eᵤ 5 | Eᵤ 10 | Eᵤ 15 | Eᵤ 20 | Eᵤ 30 | Eᵤ 40 |
|---|---|---|---|---|---|---|---|---|
| T1 | u 43,8 | u 41,0 | u 37,8 | u 21,4 | – | – | – | – |
| T2 | u 4,9 | u 2,3 | – | – | – | – | – | – |
| T4 | – | – | – | – | – | – | o 6,1 | o 16,4 |
| T5 | – | – | – | – | o 4,3 | o 9,5 | o 19,3 | o 31,6 |
| T6 | – | o 0,8 | – | o 4,2 | o 10,3 | o 15,9 | o 25,9 | o 38,2 |

T3 ligger inden for kurverne ved alle Eᵤ. Afvigelserne under er enten små
(T2) eller store (T1); afvigelserne over vokser jævnt med Eᵤ.

## Afklaringer

| Punkt | Beslutning |
| --- | --- |
| 1 Over, inden for tolerancen | Den ustabiliserede reference løftes til VejDims tykkelse; de armerede tykkelser skaleres med samme faktor, så reduktionen i procent er randkurvens. Fast regel. |
| 2 Under, inden for tolerancen | Valg: »Behold diagrammets laveste kurve« (standard) eller »Følg VejDim ned«. |
| 3 Tolerance | Separat for over og under, begge 5 % som standard, redigerbare. |
| 4 Over, uden for tolerancen | Valg: »Afvis« (standard) eller »Løft til VejDims tykkelse med advarsel«. |
| 5 Under, uden for tolerancen | Valg: »Afvis« (standard), »Behold diagrammets laveste kurve« eller »Følg VejDim ned med advarsel«. |
| 6 Fluebenet i trin 1 | Fjernes, også fra siden Trafikklasse-korrelation. Indstillingerne styrer alene. Trin 1 viser en kort linje om håndteringen med henvisning til Indstillinger. |
| 7a Besked | Inden for tolerancen: diskret, grå note med afvigelsen og den anvendte reference. Uden for tolerancen: gul advarsel eller afvisning. |
| 7b Korrelationstabel | Celler inden for tolerancen viser den Eₒ, der regnes med, mærket som godtaget inden for tolerancen, med forklaring under tabellen. |
| 7c Rapport | Linjen »Uden for diagrammets område« angiver afvigelsen, om den er inden for tolerancen, og den anvendte reference. Et flueben på rapportsiden afgør, om linjen kommer med; slået til som standard. |

Eksempler brugt ved afklaringen:

- Over, inden (T5, Eᵤ = 15): VejDim 939 mm mod 900 mm (4,3 %). Løft giver
  ustabiliseret 939, 1 lag 668, 2 lag 574 mm.
- Under, inden (T2, Eᵤ = 3): VejDim 1.046 mm mod 1.100 mm (4,9 %). Laveste
  kurve giver ustabiliseret 1.100, 1 lag 700 mm; VejDim giver 1.046 og 666 mm.
- Over, uden (T6, Eᵤ = 20): VejDim 889 mm mod 767 mm (15,9 %).
- Under, uden (T1, Eᵤ = 5): VejDim 560 mm mod 900 mm (37,8 %). Laveste kurve
  giver 900 og 600 mm; VejDim giver 560 og 373 mm.

## Implementering

### 1. Indstillinger

- Nyt afsnit »Trafikklasse uden for diagrammet« med de to tolerancer og
  valgene i punkt 2, 4 og 5. Standardværdierne er som ovenfor; ældre
  indstillingsfiler normaliseres.
- Afsnittet angiver med »Gælder:«, at det gælder både Standard og
  Brugerdefineret ved dimensionering efter trafikklasse.
- Tooltips markerer standardvalget, og en note angiver, hvordan appens
  hidtidige opførsel med og uden fluebenet genskabes.
- Klassisk standardberegning omfatter ikke denne håndtering; reglerne
  gælder begge tilstande.

### 2. Beregningsgrundlag

- Opslaget af Eₒ,ækv (core.data) returnerer zone, afvigelse og skala efter
  reglerne: inden for kurverne som i dag; uden for kurverne randkurvens Eₒ og
  en skala, der svarer til den valgte reference (VejDims tykkelse eller
  randkurven), eller intet driftspunkt, når der afvises.
- Tolerancen sammenholdes med afvigelsen fra randkurven:
  (VejDim − randkurve)/randkurve for over og (randkurve − VejDim)/randkurve
  for under. Grænsen er inklusiv.
- Parametret brug_vejdim og sessionsnøglen for fluebenet udgår og erstattes
  af indstillingen.
- Klassen bag minimumstykkelsen og den øvrige beregning bruger fortsat
  randkurvens Eₒ.

### 3. Visning

- Trin 1: diskret note inden for tolerancen, advarsel ved ekstrapolation
  uden for tolerancen, afvisning med forklaring og henvisning til
  Indstillinger ved »Afvis«.
- Siden Trafikklasse-korrelation: fluebenet fjernes; Eₒ-matricen følger
  indstillingerne og markerer celler inden for tolerancen.
- Mellemregningerne i »Sådan er resultatet beregnet« angiver den anvendte
  reference og afvigelsen.

### 4. Rapport og dokumentation

- Rapportens linje tilpasses efter punkt 7c, med flueben på rapportsiden.
- Hjælpekapitel 2, afsnit 3, og kapitel 1, afsnit 4, beskriver
  tolerancerne, reglerne og de målte afvigelser.

## Kontrolpunkter

- Standardindstillingerne giver: T6/4, T6/10 og T5/15 løftet til VejDim;
  T2/3 og T2/4 regnet på laveste kurve; alle øvrige celler uden for kurverne
  afvist.
- Tolerancerne 5, 8 og 10 % giver de forventede celler, jf. tabellen ovenfor.
- »Følg VejDim« i punkt 2, 4 og 5 samtidig giver samme resultat som det
  hidtidige flueben.
- Mellemliggende Eᵤ behandles efter samme regler.
- Resultatkort, søjler, mellemregning, korrelationstabel og rapport viser
  samme reference.
- Belastningsklasse-beregninger er uændrede.
