---
titel: Trafikklasse-korrelationen
resume: Hvad Eₒ-matricen på korrelationssiden viser, hvad zonerne under og over betyder, hvordan de behandles efter tolerancer og regler, og hvad der sker, når en kørsel rettes.
---

## 1 Hvad tabellen viser

Korrelationssidens Eₒ,ækv-matrix omsætter hver af de 48 VejDim-kørsler til et
opslagspunkt i designdiagrammerne. Hvis den ubundne lagtykkelse ligger uden
for diagramområdet, angiver matricen i stedet en zonebetegnelse.
Ved dimensionering efter trafikklasse er det denne matrix, der slås op i - ikke
kørslerne direkte.

Matricen anvendes alene ved dimensionering efter trafikklasse. Vælges
belastningsklasse, henviser klassen direkte til sit designdiagram, og
korrelationen indgår ikke, jf. kapitel 1, afsnit 2.

Matricen er afledt: den genberegnes af kørslerne og af det aktive
designdiagram. Ændres et af de to grundlag, kan celler skifte værdi eller zone.

Figur 2.1 viser sammenhængen for T4: Først bestemmes den ubundne lagtykkelse
ved det aktuelle Eᵤ, og derefter findes det tilsvarende Eₒ,ækv-opslagspunkt.

:::figur Eksempel på korrelation for T4. Først bestemmes den ubundne lagtykkelse, hvorefter Eₒ,ækv findes ud fra de ustabiliserede kurver.
| Eᵤ [MPa] | t_ubundet [mm] | Eₒ,ækv [MPa] |
| ---: | ---: | ---: |
| 5 | 1.184 | 77 |
| 8 | 1.038 | 95,3 |
| 10 | 969 | 108 |
:::

## 2 Zonerne under og over

Designdiagrammerne omfatter kurverne Eₒ = 30–150 MPa. Falder VejDims krav uden
for det spænd, findes der intet driftspunkt at aflæse i, og cellen bærer en
zonebetegnelse frem for et tal:

- **under** — kravet er tyndere end diagrammernes tyndeste kurve (Diagram 1,
  Eₒ = 30 MPa). T1 ved Eᵤ = 5 MPa kræver 560 mm, hvor kurven ligger på 900 mm.
  Zonen omfatter 6 celler: de laveste trafikklasser på blød underbund.
- **over** — kravet er tykkere end den tykkeste kurve (Diagram 6,
  Eₒ = 150 MPa). T6 ved Eᵤ = 10 MPa kræver 1.146 mm, hvor kurven slutter ved
  1.100 mm. Zonen omfatter 12 celler: de høje trafikklasser på stiv underbund.

Med det aktuelle standardgrundlag består matricen af 48 celler: 30 i
kernezonen, 6 i zonen under og 12 i zonen over. I kernezonen aflæses
reduktionen i selve driftspunktet. Her ligger den ved ét lag geonet på 26–47 %
med en middelværdi
på 31 %, hvilket svarer til niveauet ved dimensionering efter
belastningsklasse. Antallet af celler i de tre zoner følger det aktive
kørsels- og diagramgrundlag og kan derfor ændre sig, hvis dataene ændres.

Hvordan en celle i zonen under eller over behandles, fastlægges af
tolerancerne og reglerne i afsnit 3.

## 3 Opslag uden for diagrammets kurver

Opslaget i designdiagrammerne sker i de ustabiliserede tykkelser: ved
underbundens E-modul giver de seks diagrammer hver sin tykkelse, og VejDims
krav henføres til det sted, hvor tykkelsen passer, jf. kapitel 1, afsnit 4.
I kernezonen aflæses reduktionen derefter i det samme opslagspunkt. Eₒ er
alene betegnelsen for opslagspunktet og indgår ikke som en fysisk størrelse.

Figur 2.2 sammenholder VejDims krav med de seks ustabiliserede diagramkurver
ved samme Eᵤ og viser, hvorfor T1 ligger uden for diagramområdet i eksemplet.

:::figur De seks diagrammer ved Eᵤ = 8 MPa. T1 kræver 489 mm og falder uden for.
| Diagram | Uden geonet | 1 lag | Reduktion |
| --- | --- | --- | --- |
| 1 | 700 mm | 440 mm | 37,1 % |
| 2 | 800 mm | 533 mm | 33,4 % |
| 3 | 900 mm | 640 mm | 28,9 % |
| 4 | 1.000 mm | 683 mm | 31,7 % |
| 5 | 1.100 mm | 800 mm | 27,3 % |
| 6 | 1.200 mm | 820 mm | 31,7 % |
:::

Falder VejDims krav uden for de seks tykkelser, findes der intet opslagssted i
diagrammerne. Afvigelsen fra den nærmeste kurve, randkurven, måles da i
procent af randkurvens tykkelse og holdes op mod en tolerance for hver
retning. Tolerancerne og håndteringen fastlægges under Indstillinger,
afsnittet Trafikklasse uden for diagrammet, og gælder både Standard og
Brugerdefineret.

:::formel
a_over   =  (t_VejDim − t_rand) / t_rand
a_under  =  (t_rand − t_VejDim) / t_rand
--
t_VejDim  er VejDims krævede ubundne tykkelse, SG + BL [mm]
t_rand    er randkurvens ustabiliserede tykkelse ved samme Eᵤ [mm]
:::

Der er tre måder at behandle et opslag uden for kurverne på:

- **VejDims tykkelse.** VejDims ubundne lagtykkelse anvendes som den
  ustabiliserede reference. Randkurvens tykkelser skaleres med
  t_VejDim / t_rand, så geonettets reduktion i procent er randkurvens.
- **Diagrammets laveste kurve.** Anvendes alene under. Der regnes med
  kurven Eₒ = 30 MPa uændret. Den er tykkere end VejDims krav, og resultatet
  er konservativt.
- **Afvis.** Der er intet driftspunkt, og opbygningen kræver en konkret
  vurdering. Der kan i stedet dimensioneres efter belastningsklasse.

:::figur Reglerne uden for diagrammets kurver. Standardtolerancen er 5 % i begge retninger.
| Situation | Standard | Kan i stedet vælges |
| --- | --- | --- |
| Over, inden for tolerancen | VejDims tykkelse | – |
| Over, uden for tolerancen | Afvis | VejDims tykkelse |
| Under, inden for tolerancen | Laveste kurve | VejDims tykkelse |
| Under, uden for tolerancen | Afvis | Laveste kurve eller VejDims tykkelse |
:::

Reglen er ikke symmetrisk. Over følges VejDims krav opad, idet det er
konservativt at regne fra den tykkere opbygning. T5 ved Eᵤ = 15 MPa kræver
939 mm, 4,3 % over randkurvens 900 mm, og den ustabiliserede tykkelse løftes
til 939 mm. Under følges VejDim som udgangspunkt ikke nedad, idet VejDim ved
lave E-moduler giver markant tyndere opbygninger end diagrammerne. T2 ved
Eᵤ = 3 MPa kræver 1.046 mm, 4,9 % under randkurvens 1.100 mm, og der regnes
med 1.100 mm.

Figur 2.4 viser afvigelserne for de 18 standardkørsler uden for kurverne.

:::figur Afvigelse fra randkurven for standardkørslerne uden for diagrammets kurver. Eᵤ i MPa i parentes.
| Trafikklasse | Under [%] | Over [%] |
| --- | --- | --- |
| T1 | 43,8 (3) · 41,0 (4) · 37,8 (5) · 21,4 (10) | – |
| T2 | 4,9 (3) · 2,3 (4) | – |
| T3 | – | – |
| T4 | – | 6,1 (30) · 16,4 (40) |
| T5 | – | 4,3 (15) · 9,5 (20) · 19,3 (30) · 31,6 (40) |
| T6 | – | 0,8 (4) · 4,2 (10) · 10,3 (15) · 15,9 (20) · 25,9 (30) · 38,2 (40) |
:::

Afvigelserne under er enten små (T2) eller store (T1), mens afvigelserne over
vokser jævnt med Eᵤ. Med standardtolerancen regnes T6 ved Eᵤ = 4 og 10 MPa og
T5 ved Eᵤ = 15 MPa med VejDims tykkelse, og T2 ved Eᵤ = 3 og 4 MPa med
diagrammets laveste kurve. De øvrige 13 kørsler afvises. Under Indstillinger
vises de aktuelle afvigelser og den håndtering, de gældende regler giver, og
under hvert valg anføres antallet af kørte punkter, valget omfatter, med
spændet i afvigelserne.

Opmærksomheden henledes på, at geonettets reduktion ved VejDims tykkelse
bygger på antagelsen om, at geonettet giver samme procentvise reduktion som
ved randkurven ved samme underbunds-E-modul. Lagtykkelsen fastlægges af
VejDim, og reduktionsprocenten er en aflæst værdi fra feltforsøgene, men
aflæst ved randkurven og ikke i driftspunktet. Uden for tolerancen må
resultatet derfor forventes at være behæftet med større usikkerhed, og der
vises en advarsel.

Figur 2.5 viser beregningen med VejDims tykkelse for T1 ved Eᵤ = 8 MPa.

:::formel
t_armeret = t_VejDim × (1 − r_rand) × (1 + k_φ + k_net)
--
t_VejDim  er VejDims krævede ubundne tykkelse, SG + BL
r_rand    er reduktionen aflæst på randkurven ved samme Eᵤ
k_φ       er korrektionen for friktionsvinklen
k_net     er korrektionen for det valgte geonet
:::

:::figur Trafikklasse T1 ved Eᵤ = 8 MPa, beregnet med VejDims tykkelse. Afvigelsen er 30,1 % under randkurven; med standardreglerne afvises beregningen.
| Trin | Værdi |
| --- | --- |
| VejDims krav, interpoleret | 489 mm |
| Diagram 1 ved Eᵤ = 8, ustabiliseret | 700 mm |
| Diagram 1 ved Eᵤ = 8, 1 lag | 440 mm |
| Reduktion på randkurven | 37,1 % |
| Skala 489 / 700 | 0,699 |
| Resultat 489 × (1 − 0,371) | 308 mm |
:::

I matricen mærkes celler, der ligger uden for kurverne, men regnes inden for
tolerancen, med `*`, og celler, der regnes uden for tolerancen, med `†`.
Afviste celler bærer zonebetegnelsen. Uden for kurverne anføres afvigelsen fra
randkurven i parentes, med + over og − under, fx `150† (+15,9 %)` for T6 ved
Eᵤ = 20 MPa. Inden for kurverne har reglerne ingen betydning.

Forbeholdet ved fremgangsmåden er beskrevet i kapitel 7, afsnit 2.

## 4 Redigering af kørslerne

Kørslerne kan overskrives, hvis VejDim-kørslerne ønskes justeret manuelt. Ændres en kørsel, genberegnes Eₒ,ækv-matricen og anvendes med det
samme i dimensioneringen.

Kolonnerne Ubundet og Samlet højde beregnes af de øvrige kolonner og kan ikke
redigeres. Ubundet er summen t_SG + t_BL, som Eₒ,ækv bestemmes ud fra; Samlet
højde er inklusive de bundne lag øverst.

De oprindelige 48 kørsler gendannes med Nulstil kørsler.
