---
titel: Datagrundlag og forbehold
resume: Forudsætningerne for de 48 standardkørsler, designmanualernes anvendelsesområde, korrelationens gyldighed og de forhold, der kræver særskilt kontrol eller beregning.
---

## 1 VejDim-kørslernes forudsætninger

Trafikklasse-korrelationen er baseret på 48 standardkørsler i VejDim.
Kørslerne dækker trafikklasserne T1–T6 ved Eᵤ = 3, 4, 5, 10, 15, 20, 30 og
40 MPa.

Kørslerne er udført med følgende forudsætninger:

- **Belastningsmodel:** Æ10 tvillingehjul, standard, ved 60–80 km/t.
- **Afvanding:** Nej.
- **Underbund:** Frostsikker, med E-modulet manuelt overskrevet til den
  aktuelle kørsels Eᵤ-værdi. Derved bortfalder kravet til koblingshøjde, og
  kørslen beskriver alene bæreevnen.
- **Levetidsmål:** 20 år for alle lag.
- **Ubundne lag:** SG II med E = 300 MPa over BL II U≤3 med E = 100 MPa.
- **Asfaltens E-modul:** VejDims standardværdier, uden manuel overskrivning.

Asfaltpakken er fastlagt pr. trafikklasse. Bundne bærelag er låst, hvor det er
muligt. Hvor VejDim selv beregner tykkelsen, anvendes VejDims værdi, og
tykkelsen kan derfor variere med Eᵤ.

Disse forudsætninger udgør datagrundlaget for korrelationen. Hvis de ændres
væsentligt, kan den beregnede ubundne tykkelse og dermed også Eₒ,ækv ændre sig.
Kørslerne er derfor ikke en generel erstatning for en projektspecifik
VejDim-beregning.

## 2 Anvendelsesområde og begrænsninger

Korrelationen bygger på to forskellige datagrundlag. VejDim fastlægger den
nødvendige samlede ubundne lagtykkelse, mens designmanualernes diagrammer
fastlægger geonettets reduktion. VejDim indeholder ikke geonet, og reduktionen
er derfor ikke en del af VejDims beregning.

**Designmanualernes anvendelsesområde.** Designmanualerne er udarbejdet til
vej- og pladsstabilisering, herunder blandt andet modvirkning af
differenssætninger og kompensationsopbygninger. De bør ikke anvendes direkte
til statisk belastede konstruktioner som forbelastede vejdæmninger eller
pæledæmninger. Sådanne konstruktioner kræver et særskilt design.

Diagrammerne og effektindeksene er knyttet til de produktfamilier og
produkter, som manualerne beskriver. Anvendelse af andre geonetprodukter
kræver særskilt dokumentation for en tilsvarende effekt under tilsvarende
forhold.

**Materialer og friktionsvinkel.** Diagrammerne forudsætter velgraderede
friktionsmaterialer som ubundne bærelag. I værktøjet behandles materialernes
egenskaber gennem den vægtede friktionsvinkel φᵥ, med 37° som
referenceværdi. Korrektionen for φᵥ ændrer beregningsresultatet, men den
erstatter ikke kravene til materialernes kvalitet, gradering eller egnethed
som ubundne bærelag.

Materialernes maksimale kornstørrelse, geonettets maskestørrelse og eventuelle
krav til materialetype skal derfor fortsat kontrolleres særskilt, jf. kapitel
4.

**Bestemmelse af underbundens E-modul.** Sammenhængen mellem Eᵤ og vingestyrke
er vejledende og gælder primært for typiske danske jordarter med højt
vandindhold. Vandindhold, jordtype og forsøgsmetode kan give afvigelser.
Pladebelastning er derfor en mere direkte metode til at kontrollere den
aktuelle bæreevne end en indirekte omregning fra vingestyrke.

**Udførelse på blød og vandholdig underbund.** På vandholdig, blød underbund
kan vibrationer under komprimering eller trafik på for tynde gruslag øge
porevandtrykket og midlertidigt reducere bæreevnen. Beregningen beskriver ikke
denne udførelsesfase og forudsætter, at komprimering, lagopbygning og
byggetrafik håndteres efter de relevante udførelseskrav.

**Geonetplacering og udførelse.** Den beregnede lagtykkelse forudsætter, at
geonettet indbygges med korrekt dæklag, afstand mellem flere geonetlag og
overlæg i samlingerne. Disse forhold er ikke fuldt ud kontrolleret af selve
tykkelsesberegningen. Krav til placering, dæklag og afstand mellem geonetlag
er beskrevet i kapitel 5 og skal kontrolleres særskilt ved udførelsen.

**Frost og koblingshøjde.** Kørslerne er udført med frostsikker underbund, så
frostforhold og koblingshøjde ikke indgår i korrelationen. Hvis underbunden er
frosttvivlsom eller frostfarlig, skal det kontrolleres særskilt, at den
samlede opbygning ikke bliver lavere end det relevante krav til koblingshøjde.

**Opslag uden for diagramområdet.** Med det aktuelle standarddatagrundlag
ligger 30 af 48 opslagspunkter inden for designdiagrammernes område. De øvrige
punkter ligger under eller over diagramområdet. Fordelingen afhænger af de
aktive VejDim-kørsler og designdiagrammer og kan derfor ændre sig.

Som udgangspunkt afviser værktøjet opslagspunkter uden for diagramområdet. Hvis
tilvalget **Anvend VejDims tal uden for diagrammet** aktiveres, anvendes
VejDims ubundne tykkelse uændret, mens reduktionen hentes fra den nærmeste
randkurve. Reduktionen er dermed ikke bestemt i det faktiske driftspunkt, men
er baseret på en ekstrapolation og må forventes at være behæftet med større
usikkerhed. Se også kapitel 2, afsnit 3.

**Manglende armerede kurver.** Nogle kombinationer af Eᵤ og Eₒ kan ikke
beregnes, fordi designdiagrammet ikke indeholder en armeret kurve i det
pågældende punkt. Hvor en armeret kurve mangler, kan geonettets reduktion ikke
bestemmes. Antallet af sådanne opslagspunkter afhænger af de aktive
designdiagrammer.

**Asfaltpakken og trafikklasse T7.** Eₒ,ækv afhænger af den asfaltpakke, der
ligger til grund for VejDim-kørslen. De anvendte asfaltpakker er VejDims
standardværdier pr. trafikklasse. T7 er ikke medtaget i korrelationen, fordi
klassen er åben. Dimensionering for T7 bør derfor foretages direkte i VejDim.

## 3 Hvornår en konkret beregning bør foretages

En projektspecifik VejDim-beregning eller en særskilt geoteknisk vurdering bør
foretages, når projektets forudsætninger afviger væsentligt fra
datagrundlaget, eller når opslaget ikke kan bestemmes med tilstrækkelig
sikkerhed. Det gælder blandt andet, når:

- projektet ligger uden for designmanualernes anvendelsesområde,
- der anvendes et produkt eller et materiale, som ikke er dækket af
  manualernes dokumentation,
- materialernes gradering, friktionsvinkel eller kornstørrelse afviger fra
  forudsætningerne,
- underbundens E-modul er usikkert eller bestemt ud fra en vejledende
  omregning, der ikke passer til jordtypen,
- afvandingsforholdene afviger fra kørslernes forudsætning,
- levetidsmålet afviger fra 20 år,
- underbunden ikke er frostsikker,
- udførelsen foregår på vandholdig, blød underbund under forhold, hvor
  porevandtryk eller byggetrafik kan blive dimensionsgivende,
- opslagspunktet ligger under eller over diagramområdet, og den ekstrapolerede
  reduktion ikke vurderes egnet,
- der mangler en armeret kurve for den ønskede kombination af Eᵤ og Eₒ,
- eller der dimensioneres for trafikklasse T7.

En projektspecifik VejDim-kørsel kan indtastes i kørselstabellen på
korrelationssiden. Herefter beregnes Eₒ,ækv-matricen og opslagene på ny. En ny
VejDim-kørsel ændrer dog ikke grundlaget for geonettets reduktion; den del
stammer fortsat fra designdiagrammernes empiriske dokumentation.
