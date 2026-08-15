---
titel: Beregningsmetoden
resume: De to dimensioneringsgrundlag og vejen fra hver af dem til den færdige lagtykkelse. Belastningsklassen aflæses direkte i designdiagrammet; trafikklassen føres derind gennem en VejDim-kørsel og en ækvivalent Eo.
---

## 1 De to dimensioneringsgrundlag

Værktøjet dimensionerer med basis i BG Byggros' designmanualer, som er
udarbejdet på baggrund af en række danske feltforsøg siden 1997.
Den primære empiriske kilde er designdiagrammerne.
Der findes seks diagrammer, ét pr. belastningsklasse, og hvert diagram viser
bærelagstykkelsen som funktion af underbundens E-modul for tre opbygninger:
ustabiliseret, med 1 lag geonet og med 2 lag geonet.

Værktøjet tilbyder to indgange til disse diagrammer:

- **Belastningsklasse** er designmanualernes egen skala. Klassen vælges ud fra
  den forventede belastning og henviser direkte til ét af de seks diagrammer.
- **Trafikklasse** er Vejdirektoratets skala T1–T6. Der findes ingen
  designdiagrammer for trafikklasser. Trafikklassen føres ind i diagrammerne
  gennem en VejDim-kørsel, som fastlægger den ubundne lagtykkelse, og derfra
  til det punkt i diagrammerne, hvor den ustabiliserede kurve giver samme
  tykkelse.

VejDim-kørslerne knytter sig alene til trafikklasserne.
Kørslerne er udført for at kunne henføre en trafikklasse til
et opslagspunkt i designdiagrammerne og indgår ikke ved dimensionering efter
belastningsklasse.

De to fremgangsmåder adskiller sig alene i, hvordan opslagspunktet findes. Fra
det punkt, hvor lagtykkelserne er aflæst, er beregningen den samme, jf.
afsnit 5 og 6.

Koblingen er nærmere beskrevet under **Trafikklasse-korrelation** i menuen.

:::gaatil trafikklasse_korrelation
Gå til Trafikklasse-korrelation
:::

## 2 Dimensionering efter belastningsklasse

Belastningsklassen henviser direkte til sit designdiagram. Diagrammet aflæses
ved underbundens E-modul, og de tre kurver giver den ustabiliserede
lagtykkelse samt lagtykkelsen ved 1 og 2 lag geonet.

Hvert diagram er optegnet for ét overflademodul, og dette Eo er en forventet
størrelse: det overflademodul, opbygningen forudsættes at give på oversiden af
de ubundne lag.

:::figur Belastningsklassernes diagrammer og deres overflademodul.
| Klasse | Diagram | Eo [MPa] |
| --- | --- | --- |
| 1 | 1 | 30 |
| 2 | 2 | 45 |
| 3 | 3 | 60 |
| 4 | 4 | 80 |
| 5 | 5 | 120 |
| 6 | 6 | 150 |
:::

Opslaget sker i det valgte diagram alene, og der interpoleres ikke mellem
diagrammerne. Vælges belastningsklasse 5 ved Eu = 8 MN/m², aflæses de tre
lagtykkelser i diagram 5, og Eo er 120 MPa.

## 3 Ubunden lagtykkelse ved trafikklasse

For hver kombination af trafikklasse og underbunds-E-værdi er der udført en
VejDim-kørsel. Kørslerne fremgår af tabellen i **Trafikklasse-korrelation**.
Den ubundne lagtykkelse fastlægges som summen af de to ubundne lag, typisk
stabilgruslaget og bundsikringslaget.

:::formel
t_ubundet  =  t_SG  +  t_BL
--
t_SG   er tykkelsen af stabilgruslaget [mm]
t_BL   er tykkelsen af bundsikringslaget [mm]
:::

Kørslen giver alene den lagtykkelse, trafikklassen kræver ved det valgte
E-modul for underbunden. Der fremkommer ikke noget overflademodul, og
lagtykkelsen kan derfor ikke uden videre henføres til et af designdiagrammerne,
som hører til belastningsklasserne. Omsætningen sker i afsnit 4.

Kørslerne er udført ved Eu = 3, 4, 5, 10, 15, 20, 30 og 40 MPa. For
mellemliggende E-værdier bestemmes lagtykkelsen ved lineær interpolation i
log(Eu), idet lagtykkelsen aftager tilnærmelsesvis retlinet med log(Eu).

:::formel
f          =  (ln Eu − ln Eu_1) / (ln Eu_2 − ln Eu_1)
t_ubundet  =  t_1  +  f × (t_2 − t_1)
--
Eu_1, Eu_2   er de nærmeste kørte E-værdier
t_1, t_2     er de tilhørende lagtykkelser [mm]
:::

Ved en udeladelsestest er middelafvigelsen på den ækvivalente Eo bestemt til 2,9 MPa ved logaritmisk interpolation mod 5,5 MPa ved lineær interpolation.

:::figur Ubunden lagtykkelse i mm for T4. Værdien ved 8 MPa er interpoleret, f = 0,678.
| T4 ved | t_ubundet |
| --- | --- |
| 5 MPa | 1.184 |
| 8 MPa | 1.038 |
| 10 MPa | 969 |
:::

## 4 Ækvivalent Eo

Ved den ækvivalente Eo forstås den Eo-værdi, hvis ustabiliserede lagtykkelse
ved samme Eu svarer til den lagtykkelse, der er fastlagt efter afsnit 3.
Værdien bestemmes ved lineær interpolation mellem de to nærmeste Eo-kurver i
designdiagrammet og giver den kobling, der fører trafikklassen ind i
designmanualernes grundlag.

:::formel
f       =  (t_ubundet − t_lav) / (t_høj − t_lav)
Eo_ækv  =  Eo_lav  +  f × (Eo_høj − Eo_lav)
--
t_lav, t_høj     er de ustabiliserede lagtykkelser ved de to nærmeste kurver [mm]
Eo_lav, Eo_høj   er de tilhørende Eo-værdier [MPa]
:::

En lagtykkelse på 1.038 mm ligger mellem kurverne for Eo = 80 MPa og
Eo = 120 MPa, hvoraf fås f = 0,382 og Eo_ækv = 95,3 MPa.

Opmærksomheden henledes på, at den ækvivalente Eo ikke er et forventet
overflademodul. Ved dimensionering efter belastningsklasse er Eo diagrammets
egen, forudsatte værdi, jf. afsnit 2; ved dimensionering efter trafikklasse er
Eo_ækv alene en indeksværdi, der angiver opslagspunktet mellem to diagrammer.

Da opslagspunktet afhænger af både trafikklasse og underbundens E-værdi, kan en
trafikklasse ikke henføres til ét bestemt designdiagram.

:::figur Ækvivalent Eo for T4 ved fire underbunds-E-værdier. Trafikklassen henføres ikke til ét bestemt diagram.
| T4 ved | Eo_ækv | Nærmeste diagram |
| --- | --- | --- |
| 5 MPa | 90 | 4 |
| 10 MPa | 108 | mellem 4 og 5 |
| 15 MPa | 135 | 5 |
| 20 MPa | 148 | 6 |
:::

Forholdet skyldes, at de to klassesystemer beskriver forskellige størrelser:
belastningsklasserne beskriver lastens størrelse, mens trafikklasserne
beskriver antallet af belastningsgentagelser.

## 5 Geonet-reduktion

Fra opslagspunktet er beregningen den samme for de to grundlag. Ved
belastningsklasse aflæses de armerede kurver direkte i diagrammet. Ved
trafikklasse bestemmes de ved interpolation mellem de samme to Eo-kurver som i
afsnit 4 og med den samme interpolationsfaktor f.

:::formel
t_armeret  =  t_lav,armeret  +  f × (t_høj,armeret − t_lav,armeret)
--
f   er interpolationsfaktoren fra afsnit 4
:::

Reduktionen interpoleres ikke direkte, men følger af de interpolerede
lagtykkelser. For T4 ved Eu = 8 MPa, hvor f = 0,382, fås en reduktion på
28,9 % ved 1 lag og 38,5 % ved 2 lag. Værdien for 1 lag ligger følgelig mellem
de to nærmeste kurvers egne reduktioner på henholdsvis 30,0 % ved Eo = 80 MPa
og 27,3 % ved Eo = 120 MPa.

:::figur Lagtykkelser ved Eo_ækv = 95,3 MPa, bestemt ved interpolation mellem de to nærmeste kurver.
| Ved Eu = 8 MPa | 80 MPa | 120 MPa | Eo_ækv |
| --- | --- | --- | --- |
| Ustabiliseret | 1.000 | 1.100 | 1.038 |
| 1 lag geonet | 700 | 800 | 738 |
| 2 lag geonet | 600 | 700 | 638 |
:::

Da den ustabiliserede kurve indgår i begge interpolationer, er
interpolationsfaktoren den samme, uanset om den bestemmes ud fra lagtykkelsen
eller ud fra Eo-værdien. Den ækvivalente Eo kan derfor betragtes som en
angivelse af interpolationsfaktoren.

Der gøres opmærksom på, at designdiagrammerne ikke indeholder armerede kurver i
alle punkter. Ved Eu = 10 MPa findes eksempelvis ingen kurve for 2 lag geonet
ved Eo = 30, 45, 60 og 80 MPa. Falder opslagspunktet i dette område, kan
reduktionen for 2 lag ikke bestemmes, og resultatet udelades.

## 6 Korrektion for materialer og geonettype

De lagtykkelser, der bestemmes efter afsnit 5, er designdiagrammernes
basisværdier, som forudsætter en friktionsvinkel på φ = 37° og referencenettet
med effektindeks 100, som ses direkte anvendt i Standard-tilstanden.
I Standard-tilstanden korrigeres dermed kun for geonettenes forskellige
effektindeks.
I Brugerdefineret-tilstanden anvendes materialer med forskellige
friktionsvinkler. Der beregnes en vægtet friktionsvinkel til den videre
dimensionering, hvor der korrigeres med 2 % for hver grad over eller under
φ = 37°. I denne tilstand korrigeres der således for både friktionsvinklen og
geonettets effektindeks.

:::formel
T    =  T_basis × (1 + k_φ + k_net)
k_φ  =  −0,02 × (φ − 37°)
--
k_φ     er korrektionen for friktionsvinklen i de ubundne materialer
k_net   er korrektionen for det valgte geonet, jf. kapitel 5
T_basis er den aflæste eller interpolerede lagtykkelse fra afsnit 5 [mm]
:::

Korrektionen for friktionsvinklen anvendes på samtlige tre kurver. Korrektionen
for geonettype anvendes alene på de armerede kurver, idet den ustabiliserede
opbygning ikke indeholder geonet. Reduktionen opgøres derfor i forhold til den
korrigerede ustabiliserede lagtykkelse, således at begge lagtykkelser er
korrigeret på samme grundlag.

Grundlaget er rent bæreevnemæssigt. Kravene til frostsikring og koblingshøjde,
jf. Vejdirektoratets dimensioneringsvejledninger, er ikke omfattet.
