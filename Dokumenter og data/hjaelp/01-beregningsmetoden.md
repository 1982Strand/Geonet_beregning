---
titel: Beregningsmetoden
resume: De to dimensioneringsgrundlag og vejen fra hver af dem til den færdige lagtykkelse. Belastningsklassen aflæses direkte i designdiagrammet; trafikklassen kobles til diagrammerne gennem VejDim-beregninger og et ækvivalent opslagspunkt.
---

## 1 Beregningsgrundlag og to dimensioneringsindgange

Værktøjet bygger på BG Byggros' designmanualer, som er udarbejdet på baggrund
af feltforsøg gennemført siden 1997. Den primære empiriske kilde er seks
designdiagrammer, ét for hver belastningsklasse. Hvert diagram viser
bærelagstykkelsen som funktion af underbundens E-modul for tre opbygninger:
ustabiliseret, med ét lag geonet og med to lag geonet.

Dimensioneringen kan tage udgangspunkt i to forskellige klassesystemer:

- **Belastningsklasse** er designmanualernes egen skala. Den valgte klasse
  henviser direkte til det tilsvarende designdiagram.
- **Trafikklasse** følger Vejdirektoratets skala T1–T6. Der findes ikke
  særskilte designdiagrammer for trafikklasserne. Sammenhængen er derfor
  etableret gennem VejDim-beregninger: For hver trafikklasse holdes klassen
  fast, mens underbundens E-modul varieres. Ved hver beregning fastlægger
  VejDim den nødvendige samlede tykkelse af de ubundne lag.

Den VejDim-bestemte tykkelse placeres derefter i belastningsklassernes
designdiagrammer ved det samme underbunds-E-modul. Det opslagspunkt, hvor den
ustabiliserede kurve giver samme tykkelse, fastlægger trafikklassens placering
mellem diagrammernes Eₒ-værdier.

VejDim-beregningerne anvendes dermed alene til at etablere korrelationen mellem
trafikklasserne og designdiagrammernes belastningsklasser. De indgår ikke i
dimensioneringen efter belastningsklasse.

De to fremgangsmåder adskiller sig alene i, hvordan opslagspunktet findes. Fra
det punkt, hvor lagtykkelserne er aflæst, er beregningen den samme, jf.
afsnit 5 og 6.

Koblingen er nærmere beskrevet under **Trafikklasse-korrelation** i menuen.

:::gaatil trafikklasse_korrelation
Gå til Trafikklasse-korrelation
:::

## 2 Direkte opslag ved belastningsklasse

Ved dimensionering efter belastningsklasse vælges det designdiagram, som
klassen henviser til. Diagrammet aflæses ved underbundens E-modul, og de tre
kurver giver den ustabiliserede lagtykkelse samt lagtykkelsen ved ét og to lag
geonet.

Hvert diagram er optegnet for én fast Eₒ-værdi. Eₒ betegner her det forventede
overflademodul på oversiden af de ubundne lag og skal således ikke forstås
som en garanteret værdi.

Figur 1.1 viser de seks belastningsklasser og den Eₒ-værdi, som hører til hvert
designdiagram.

:::figur Belastningsklassernes designdiagrammer og deres forudsatte Eₒ-værdier.
| Belastningsklasse | Eₒ [MPa] |
| --- | ---: |
| 1 | 30 |
| 2 | 45 |
| 3 | 60 |
| 4 | 80 |
| 5 | 120 |
| 6 | 150 |
:::

Opslaget sker i det valgte diagram alene, og der interpoleres ikke mellem
diagrammerne. Vælges belastningsklasse 5 ved Eᵤ = 8 MPa, aflæses de tre
lagtykkelser i diagram 5, og Eₒ er 120 MPa.

## 3 Trafikklasse: VejDims ubundne lagtykkelse

Korrelationen bygger på 48 VejDim-kørsler: én for hver kombination af de seks
trafikklasser og de valgte underbunds-E-værdier. For hver trafikklasse holdes
trafikklassen fast, mens underbundens E-modul varieres. Kørslerne fremgår af
tabellen i **Trafikklasse-korrelation**. Den ubundne lagtykkelse fastlægges som
summen af de to ubundne lag, typisk stabilgruslaget og bundsikringslaget.

:::formel
t_ubundet  =  t_SG  +  t_BL
--
t_SG   er tykkelsen af stabilgruslaget [mm]
t_BL   er tykkelsen af bundsikringslaget [mm]
:::

VejDim-kørslen giver dermed den lagtykkelse, trafikklassen kræver ved det
valgte underbunds-E-modul. Kørslen fastlægger ikke en Eₒ-værdi. Lagtykkelsen
skal derfor først sammenholdes med belastningsklassernes ustabiliserede kurver,
før trafikklassen kan kobles til designdiagrammerne. Det sker i afsnit 4.

Kørslerne er udført ved Eᵤ = 3, 4, 5, 10, 15, 20, 30 og 40 MPa. For
mellemliggende E-værdier bestemmes lagtykkelsen ved lineær interpolation i
log(Eᵤ), idet lagtykkelsen aftager tilnærmelsesvis retlinet med log(Eᵤ).

:::formel
f          =  (ln Eᵤ − ln Eᵤ,1) / (ln Eᵤ,2 − ln Eᵤ,1)
t_ubundet  =  t_1  +  f × (t_2 − t_1)
--
Eᵤ,1, Eᵤ,2   er de nærmeste kørte E-værdier
t_1, t_2     er de tilhørende lagtykkelser [mm]
:::

Ved en udeladelsestest er middelafvigelsen på den ækvivalente Eₒ bestemt til 2,9 MPa ved logaritmisk interpolation mod 5,5 MPa ved lineær interpolation.

Figur 1.2 viser et eksempel på den ubundne lagtykkelse, som VejDim-kørslen
giver ved tre underbunds-E-værdier. Værdien ved Eᵤ = 8 MPa er bestemt ved
interpolation mellem de to nærmeste kørsler.

:::figur Eksempel på VejDim-bestemt ubunden lagtykkelse for T4. Værdien ved Eᵤ = 8 MPa er interpoleret.
| Eᵤ [MPa] | t_ubundet [mm] |
| ---: | ---: |
| 5 | 1.184 |
| 8 | 1.038 |
| 10 | 969 |
:::

## 4 Trafikklasse: bestemmelse af Eₒ,ækv

For trafikklassen findes opslagspunktet ved at sammenholde den VejDim-bestemte
lagtykkelse med de ustabiliserede kurver i designdiagrammerne ved samme Eᵤ.
Hvis tykkelsen ligger mellem to kurver, bestemmes placeringen ved lineær
interpolation. Den tilsvarende Eₒ-værdi betegnes Eₒ,ækv og bruges som en
entydig beskrivelse af opslagspunktet mellem de to kurver.

:::formel
f       =  (t_ubundet − t_lav) / (t_høj − t_lav)
Eₒ,ækv  =  Eₒ,lav  +  f × (Eₒ,høj − Eₒ,lav)
--
t_lav, t_høj     er de ustabiliserede lagtykkelser ved de to nærmeste kurver [mm]
Eₒ,lav, Eₒ,høj   er de tilhørende Eₒ-værdier [MPa]
:::

En lagtykkelse på 1.038 mm ligger mellem de ustabiliserede kurver for
Eₒ = 80 MPa og Eₒ = 120 MPa. Heraf fås f = 0,382 og Eₒ,ækv = 95,3 MPa.

Opmærksomheden henledes på, at den ækvivalente Eₒ ikke er et forventet
overflademodul. Ved dimensionering efter belastningsklasse er Eₒ diagrammets
egen, forudsatte værdi, jf. afsnit 2; ved dimensionering efter trafikklasse er
Eₒ,ækv alene en indeksværdi, der angiver opslagspunktet mellem to diagrammer.

Da opslagspunktet afhænger af både trafikklasse og underbundens E-værdi, kan en
trafikklasse ikke henføres til ét bestemt designdiagram.

Figur 1.3 illustrerer dette for T4: Den samme trafikklasse giver forskellige
Eₒ,ækv-værdier, når underbundens E-modul ændres.

Så længe lagtykkelsen ligger mellem diagrammernes yderste ustabiliserede
kurver, bestemmes Eₒ,ækv ved interpolation inden for diagramområdet. Ligger
lagtykkelsen uden for dette område, findes der ikke et egentligt opslagspunkt.
Hvis tilvalget **Anvend VejDims tal uden for diagrammet** er aktiveret, anvendes
VejDims tykkelse dog uændret, mens reduktionen hentes fra den nærmeste
randkurve. Reduktionen er dermed ikke bestemt i det faktiske driftspunkt. Denne
udvidelse er beskrevet nærmere i kapitel 2, afsnit 3.

:::figur Eₒ,ækv for T4 ved fire underbunds-E-værdier. Samme trafikklasse kan derfor ligge mellem forskellige diagramkurver.
| Eᵤ [MPa] | Eₒ,ækv [MPa] | Nærmeste Eₒ-kurver [MPa] |
| ---: | ---: | --- |
| 5 | 90 | 80 og 120 |
| 10 | 108 | 80 og 120 |
| 15 | 135 | 120 og 150 |
| 20 | 148 | 120 og 150 |
:::

Forholdet skyldes, at de to klassesystemer beskriver forskellige størrelser:
belastningsklasserne beskriver lastens størrelse, mens trafikklasserne
beskriver antallet af belastningsgentagelser.

## 5 Geonet-reduktion

Når opslagspunktet i designdiagrammet er fastlagt, bestemmes lagtykkelsen med
geonet på samme grundlag som den ustabiliserede lagtykkelse.

Ved dimensionering efter belastningsklasse aflæses den relevante armerede kurve
direkte i det valgte designdiagram. Ved dimensionering efter trafikklasse ligger
opslagspunktet normalt mellem to Eₒ-kurver. Den armerede lagtykkelse bestemmes
derfor ved lineær interpolation mellem de samme to kurver, som blev anvendt ved
bestemmelsen af Eₒ,ækv i afsnit 4. Den samme interpolationsfaktor f anvendes for
den ustabiliserede kurve og for hver af de armerede kurver.

:::formel
t_armeret  =  t_lav,armeret  +  f × (t_høj,armeret − t_lav,armeret)
--
f                 er interpolationsfaktoren fra afsnit 4
t_lav,armeret,
t_høj,armeret     er lagtykkelserne ved de to nærmeste Eₒ-kurver [mm]
:::

Interpolationen forudsætter, at den pågældende armerede kurve har data i begge
de Eₒ-kolonner, der afgrænser opslagspunktet. Hvis en af kurverne mangler, kan
lagtykkelsen og reduktionen ikke bestemmes for den pågældende kombination.

Reduktionsprocenten bestemmes ikke ved direkte interpolation af kurvernes
reduktionsprocenter. Den beregnes efterfølgende ud fra den ustabiliserede og den
tilsvarende armerede, interpolerede lagtykkelse. For T4 ved Eᵤ = 8 MPa, hvor
f = 0,382, fås en reduktion på 28,9 % ved 1 lag geonet og 38,5 % ved 2 lag.
Reduktionen ved 1 lag ligger dermed mellem reduktionerne på de to nærmeste
kurver: 30,0 % ved Eₒ = 80 MPa og 27,3 % ved Eₒ = 120 MPa.

Figur 1.4 viser de tre lagtykkelser ved Eₒ,ækv = 95,3 MPa. Den samme
interpolationsfaktor, f = 0,382, anvendes på alle tre kurver og på hver kurves
egne lagtykkelser ved Eₒ = 80 MPa og Eₒ = 120 MPa.

:::figur Lagtykkelser ved Eₒ,ækv = 95,3 MPa, bestemt ved interpolation mellem de to nærmeste kurver. Her er f = 0,382. For den ustabiliserede kurve bliver beregningen: 1.000 + 0,382 × (1.100 − 1.000) = 1.038 mm.
| Ved Eᵤ = 8 MPa | 80 MPa | 120 MPa | Eₒ,ækv |
| --- | ---: | ---: | ---: |
| Ustabiliseret | 1.000 | 1.100 | 1.038 |
| 1 lag geonet | 700 | 800 | 738 |
| 2 lag geonet | 600 | 700 | 638 |
:::

Da den ustabiliserede kurve bruges til at fastlægge opslagspunktet, er
interpolationsfaktoren den samme ved aflæsningen af de armerede kurver.
Eₒ,ækv er dermed en angivelse af opslagspunktets placering mellem de to
nærmeste Eₒ-kurver.

Designdiagrammerne indeholder ikke armerede kurver i alle punkter. Hvis
opslagspunktet falder uden for en armeret kurves gyldighedsområde, kan den
pågældende geonetopbygning ikke beregnes, jf. kapitel 3, afsnit 3.

## 6 Korrektion for materialer og geonet

De lagtykkelser, der bestemmes efter afsnit 5, er designdiagrammernes
basisværdier. De svarer til en vægtet friktionsvinkel på φᵥ = 37° og et
referencenet med effektindeks 100. I Standard-tilstanden anvendes disse
forudsætninger direkte, og der korrigeres derfor kun for det valgte geonets
effektindeks.
I Brugerdefineret-tilstanden anvendes materialer med forskellige
friktionsvinkler. Der beregnes en vægtet friktionsvinkel φᵥ til den videre
dimensionering. For hver grad φᵥ ligger over 37°, reduceres lagtykkelsen med
2 %; ligger φᵥ under 37°, øges lagtykkelsen tilsvarende. De 2 % indgår som
decimalen 0,02 i korrektionsformlen. I denne tilstand korrigeres der således
for både friktionsvinklen og
geonettets effektindeks.

:::formel
T    =  T_basis × (1 + k_φ + k_net)
k_φ  =  −0,02 × (φᵥ − 37°)
--
k_φ      er korrektionen for friktionsvinklen i de ubundne materialer
k_net   er korrektionen for det valgte geonet, jf. kapitel 5
T_basis er den aflæste eller interpolerede lagtykkelse fra afsnit 5 [mm]
:::

Korrektionen for friktionsvinklen anvendes på samtlige tre kurver. Korrektionen
for geonet anvendes alene på de armerede kurver, idet den ustabiliserede
opbygning ikke indeholder geonet; her er k_net = 0. Reduktionen opgøres derfor
i forhold til den korrigerede ustabiliserede lagtykkelse, således at begge
lagtykkelser er korrigeret på samme grundlag.

Beregningen omfatter alene bæreevnen. Krav til frostsikring og koblingshøjde,
jf. Vejdirektoratets dimensioneringsvejledninger, er ikke omfattet.
