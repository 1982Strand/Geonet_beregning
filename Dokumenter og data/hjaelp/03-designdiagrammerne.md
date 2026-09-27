---
titel: Designdiagrammerne
resume: De tre kurver i hvert af de seks diagrammer, hvordan tabellerne er dannet af de aflæste punkter, og hvad der sker uden for diagrammets område.
---

## 1 De tre kurver

Hvert af de seks designdiagrammer viser bærelagstykkelsen som funktion af
underbundens E-modul for tre opbygninger: ustabiliseret, med ét lag geonet og
med to lag geonet. Diagrammerne er vores (Byggros) egne, ét pr.
belastningsklasse, og er optegnet for referencenettet.

Kurverne vises på siden Designdiagrammer, både som designmanualens egen
scanning og som en optegning af de aflæste værdier. Optegningen anvender
gennemgående de samme farver som værktøjets øvrige diagrammer: sort for
ustabiliseret, blåt for 1 lag og lilla for 2 lag.

Figur 3.1 viser et udsnit af de aflæste datapunkter for et diagram, hvor alle
tre opbygninger er tilgængelige.

:::figur Uddrag af diagram 4, belastningsklasse 4, hvor alle tre opbygninger har aflæste værdier.
| Eᵤ [MPa] | Ustabiliseret [mm] | 1 lag [mm] | 2 lag [mm] |
| ---: | ---: | ---: | ---: |
| 3 | 1.400 | 1.000 | 900 |
| 4 | 1.267 | 900 | 800 |
| 5 | 1.200 | 833 | 750 |
:::

## 2 Aflæsning og interpolation

Der slås ikke op i kurverne som grafiske objekter, men i en tabel ved hvert
diagram, som angiver lagtykkelsen for hele værdier af Eᵤ. Tabellen er dannet af
de punkter, der er markeret på kurverne i designmanualens diagrammer, og
beregningen anvender tabellen direkte som opslag.

Punkterne er aflæst af designmanualens vektorgrafik. Hvert punkt ligger ved en
bærelagstykkelse på et helt antal gange 10 cm, og Eᵤ er afrundet til nærmeste
0,5 MPa. Mellem to nabopunkter på samme kurve bestemmes lagtykkelsen ved
lineær interpolation. Kurverne er i manualen tegnet som rette linjestykker
mellem punkterne, og interpolationen gengiver dermed den tegnede kurve.

:::formel
t  =  t_1  +  (Eᵤ − Eᵤ,1) / (Eᵤ,2 − Eᵤ,1) × (t_2 − t_1)
--
Eᵤ,1, Eᵤ,2   er Eᵤ i de to aflæste punkter, der omslutter Eᵤ [MPa]
t_1, t_2     er lagtykkelserne i de to punkter [cm]
:::

Lagtykkelsen afrundes til 0,1 cm. Der ekstrapoleres ikke: ligger Eᵤ uden for
kurvens første eller sidste punkt, har kurven ikke data i rækken, jf. afsnit 3.
På siden Designdiagrammer står de værdier, der ligger i et aflæst punkt, med
fed skrift.

Der gøres opmærksom på, at manualens tegning er afrundet til et fast raster på
0,2–0,3 MPa, og at kurverne er flade ved små værdier af Eᵤ. En usikkerhed på få
tiendedele MPa svarer her til flere cm lagtykkelse.

Ved dimensionering efter belastningsklasse svarer opslaget til en af
diagrammernes egne Eₒ-kolonner — 30, 45, 60, 80, 120 eller 150 MPa — og
lagtykkelsen aflæses direkte.

Ved dimensionering efter trafikklasse ligger opslagspunktet derimod normalt
mellem to af disse Eₒ-kolonner. Punktet beskrives med den tilbageberegnede værdi
Eₒ,ækv, og lagtykkelsen bestemmes derfor ved lineær interpolation mellem de to
nærmeste kolonner, jf. kapitel 1, afsnit 4. Hvis Eₒ,ækv falder præcist på en
kolonne, aflæses værdien direkte.

:::formel
t  =  t_lav  +  f × (t_høj − t_lav)
--
f            er interpolationsfaktoren, jf. kapitel 1, afsnit 4
t_lav, t_høj er de aflæste lagtykkelser ved de to nærmeste kolonner [mm]
:::

Interpolationen udføres særskilt for hver af de tre kurver med samme f. Det
forudsætter, at den pågældende kurve har data i begge de Eₒ-kolonner, der
afgrænser opslagspunktet. Hvis kurven mangler i én af kolonnerne, kan der ikke
interpoleres for den pågældende opbygning.

## 3 Uden for diagrammets område

Designdiagrammerne dækker ikke alle kombinationer af underbundens E-modul og
Eₒ. Den ustabiliserede kurve er defineret fra og med Eᵤ = 3 MPa, mens de
armerede kurver har et mere begrænset gyldighedsområde. Den øvre grænse
afhænger både af Eₒ og af, om opbygningen indeholder ét eller to lag geonet.
Tabellerne nedenfor gælder de præcise Eₒ-kolonner i designdiagrammerne. Ved et
mellemliggende Eₒ skal begge omkringliggende kurver have data, før der kan
interpoleres.

Figur 3.2 og Figur 3.3 viser de øvre Eᵤ-grænser for henholdsvis ét og to lag
geonet.

:::figur Øvre Eᵤ-grænse for kurver med 1 lag geonet.
| Eₒ [MPa] | Kurven findes til og med Eᵤ [MPa] |
| --- | --- |
| 30 | 15 |
| 45 | 20 |
| 60 | 27 |
| 80 | 33 |
| 120 | 33 |
| 150 | 32 |
:::

:::figur Øvre Eᵤ-grænse for kurver med 2 lag geonet.
| Eₒ [MPa] | Kurven findes til og med Eᵤ [MPa] |
| --- | --- |
| 30 | — |
| 45 | 6 |
| 60 | 9 |
| 80 | 8 |
| 120 | 14 |
| 150 | 18 |
:::

Ved Eᵤ = 40 MPa findes der ingen armeret kurve for nogen af Eₒ-værdierne. I
diagram 1 findes der slet ingen kurve for to lag geonet.

En tankestreg betyder, at den pågældende kurve ikke har data i punktet.
Beregningen kan derfor ikke gennemføres for den konkrete kombination af Eᵤ, Eₒ
og antal geonetlag. Andre kurver i samme punkt kan dog stadig være tilgængelige.

Forholdet bør ikke forveksles med zonerne under og over, jf. kapitel 2,
afsnit 2. En zonebetegnelse betyder derimod, at de nødvendige diagramkurver
findes, men at VejDims krævede samlede tykkelse af de ubundne lag ligger uden
for diagrammets tykkelsesinterval. Ved trafikklasse kan der i dette tilfælde,
hvis tilvalget er aktiveret, dimensioneres på VejDims tykkelse. Reduktionen
aflæses da på den nærmeste randkurve og er derfor ekstrapoleret, jf. kapitel 2,
afsnit 3.

De aflæste værdier kan redigeres på siden Designdiagrammer. Ændres en værdi,
dannes opslagstabellen på ny, og både dimensioneringen og
Eₒ,ækv-matricen følger med.
