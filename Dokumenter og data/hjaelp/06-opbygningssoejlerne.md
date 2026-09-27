---
titel: Sådan læses resultaterne
resume: Hvordan den indtastede opbygning sammenholdes med de beregnede krav, hvordan tykkelsen fordeles på materialelagene med minimumstykkelse for det øverste lag og regler for tynde underliggende lag, hvilken friktionsvinkel opbygningerne regnes med, hvordan Standard-beregningen opdeler opbygningen, hvordan geonetplaceringen vises, og hvordan statuslinjen angiver forskellen mellem krav og indtastet tykkelse.
---

## 1 Opbygningssøjler og sammenligning

Resultatvisualiseringen sammenholder den indtastede opbygning med de
beregnede krav for en ustabiliseret opbygning og for opbygninger med ét eller
to lag geonet. Den stiplede grå linje markerer den indtastede opbygnings
samlede tykkelse og fungerer som reference for vurderingen. En beregnet søjle,
der slutter på eller under linjen, opfylder tykkelseskravet; en søjle over
linjen viser, at opbygningen mangler tykkelse.

Søjlerne viser hver sin opbygning:

- **Indtastet opbygning** gengiver de indtastede lagtykkelser.
- **Ustabiliseret basistykkelse** er lagtykkelsen fra designdiagrammet,
  bestemt ud fra Eᵤ og Eₒ og korrigeret for den vægtede friktionsvinkel.
- **1 lag og 2 lag geonet** viser de tilsvarende stabiliserede lagtykkelser
  efter reduktionen for geonet.

Det er den samlede ubundne bærelagstykkelse, der sammenlignes – ikke
geonettets tykkelse. Når opbygningen består af flere materialelag, beregner
værktøjet først én samlet, tykkelsesvægtet friktionsvinkel, φᵥ, for hele
opbygningen. Denne værdi anvendes som fælles friktionsvinkel i korrektionen af
den samlede bærelagstykkelse. Lagene korrigeres derfor ikke hver for sig ud
fra deres individuelle friktionsvinkler. Den beregnede tykkelse fordeles i
stedet på materialelagene efter den fordeling, der er valgt under
Indstillinger, jf. afsnit 2, og afrundes lagvis til det valgte
indbygningstrin, så hvert lag kan indbygges i den viste tykkelse, og lagene
tilsammen giver den oprundede lagtykkelse, jf. kapitel 1, afsnit 7.
Søjlerne viser dermed den samlede beregning fordelt på en mulig lagopbygning.

Hvis φᵥ overskrives manuelt, anvendes den manuelt indtastede værdi i stedet
for den tykkelsesvægtede værdi.

De røde linjer markerer geonettets placering. Ved to lag placeres det øverste
net ved den reducerede materialegrænse. Nettets navn står ud for hver linje,
lige til venstre for søjlen; under Indstillinger kan påskriften fravælges, så
navnet alene fremgår af signaturen under figuren. Ved beregning efter
trafikklasse kan søjlens grundlag være VejDims ubundne tykkelse, jf. kapitel
2, afsnit 3.

Den samlede tykkelse målsættes til højre for hver søjle med en
målsætningsstreg fra underbundens overkant til opbygningens top og målet ved
siden af. Både stregen og målet kan fravælges under Indstillinger.

Har det valgte produkt et korrektionsinterval, angives den optimale ende med
en grøn, prikket linje. Mellemregningen bag værdien vises ved markøren.

## 2 Fordeling på materialelag og minimumstykkelse

Designdiagrammerne giver én samlet ubunden lagtykkelse og indeholder ingen
oplysning om, hvordan tykkelsen fordeles på de enkelte materialelag.
Fordelingen indgår derfor ikke i diagramopslaget. Den samlede lagtykkelse
og reduktionen kan dog ændres af reglerne i afsnit 3 og 4. Fordelingen
fastlægges under Indstillinger, afsnittet Øverste bærelag, og gælder både
opbygningerne på dimensioneringssiden og rapportens figur.

Der kan vælges mellem tre fordelinger:

- **Proportionalt.** Alle lag reduceres i samme forhold som den samlede
  lagtykkelse. Lagforholdet er dermed det indtastede i alle beregnede
  opbygninger.
- **Proportionalt, dog mindst minimumstykkelsen.** Det øverste lag fordeles
  proportionalt, men gøres ikke tyndere end minimumstykkelsen for
  belastningsklassen. Resten af lagtykkelsen fordeles proportionalt på de
  underliggende lag.
- **Øverste lag fastholdt.** Det øverste lag har den indtastede tykkelse i
  alle beregnede opbygninger, dog mindst minimumstykkelsen. De underliggende lag optager
  både forøgelsen til den ustabiliserede lagtykkelse og reduktionen for
  geonet.

:::formel
t_1  =  min( T ;  max( t_1,prop ;  t_min ) )     proportionalt, dog mindst minimumstykkelsen
t_1  =  min( T ;  max( t_1,ind ;  t_min ) )      øverste lag fastholdt
--
t_1       er tykkelsen af det øverste lag [mm]
T         er den samlede, oprundede lagtykkelse [mm]
t_1,prop  er det øverste lags tykkelse ved proportional fordeling [mm]
t_1,ind   er det indtastede øverste lags tykkelse, oprundet til indbygningstrin [mm]
t_min     er minimumstykkelsen for klassen, oprundet til indbygningstrin [mm]
:::

Resten, T − t_1, fordeles proportionalt på de underliggende lag. Det øverste
lag kan ikke blive tykkere end den samlede lagtykkelse; er der ingen rest,
udgør det øverste lag hele opbygningen. Alle beregnede opbygninger, også
den ustabiliserede, fordeles efter samme regel.

Er materialelagene angivet i procent, findes der ingen indtastet tykkelse.
Ved fordelingen »Øverste lag fastholdt« anvendes da det øverste lags
tykkelse i den ustabiliserede opbygning i stedet for t_1,ind.

Figur 6.1 viser standardværdierne for minimumstykkelsen. Værdierne kan
redigeres under Indstillinger. Minimumstykkelsen oprundes til
indbygningstrinnet; ved standardtrinnet på 50 mm anvendes 275 mm således som
300 mm.

:::figur Minimumstykkelser for det øverste lag. Standardværdier, der kan redigeres under Indstillinger.
| Belastningsklasse | Minimumstykkelse [mm] |
| --- | ---: |
| 1–3 | 200 |
| 4 | 250 |
| 5 | 275 |
| 6 | 300 |
:::

Ved dimensionering efter trafikklasse anvendes minimumstykkelsen for den
højeste af de to belastningsklasser, som opslagspunktet Eₒ,ækv ligger
imellem, jf. kapitel 1, afsnit 4. Ved Eₒ,ækv = 95,3 MPa anvendes således
minimumstykkelsen for belastningsklasse 5.

Figur 6.2 viser de tre fordelinger for en indtastet opbygning af 300 mm
stabilgrus over 400 mm bundsikringssand ved belastningsklasse 4 og
Eᵤ = 16 MPa. Den ustabiliserede opbygning er 700 mm, og opbygningen med 1 lag
geonet er 500 mm.

:::figur Fordeling af 500 mm ved 1 lag geonet. Belastningsklasse 4, Eᵤ = 16 MPa, minimumstykkelse 250 mm.
| Fordeling | Øverste lag [mm] | Underliggende lag [mm] |
| --- | ---: | ---: |
| Proportionalt | 200 | 300 |
| Mindst minimumstykkelsen | 250 | 250 |
| Øverste lag fastholdt | 300 | 200 |
:::

Figur 6.3 viser samme indtastede opbygning ved Eᵤ = 8 MPa. Designdiagrammet
kræver her 1.000 mm uden geonet, altså mere end de indtastede 700 mm. Ved
proportional fordeling øges begge lag i det indtastede forhold, og
stabilgruset bliver 450 mm i den ustabiliserede opbygning. Fastholdes det
øverste lag, forbliver stabilgruset 300 mm, og forøgelsen tages i
bundsikringslaget.

:::figur Fordeling i de tre beregnede opbygninger, øverste lag / underliggende lag [mm]. Belastningsklasse 4, Eᵤ = 8 MPa, minimumstykkelse 250 mm.
| Fordeling | Ustabiliseret 1.000 mm | 1 lag geonet 700 mm | 2 lag geonet 600 mm |
| --- | ---: | ---: | ---: |
| Proportionalt | 450 / 550 | 300 / 400 | 250 / 350 |
| Mindst minimumstykkelsen | 450 / 550 | 300 / 400 | 250 / 350 |
| Øverste lag fastholdt | 300 / 700 | 300 / 400 | 300 / 300 |
:::

Under Indstillinger kan det desuden tilvælges, at den samlede
bærelagstykkelse sættes mindst til minimumstykkelsen. Valget gælder både
Standard- og Brugerdefineret-tilstanden. Er den beregnede og oprundede
lagtykkelse mindre end minimumstykkelsen, angives minimumstykkelsen, og
reduktionen mindskes tilsvarende. Tillægget står som eget led i
mellemregningerne efter oprundingen, jf. kapitel 1, afsnit 7.

Opmærksomheden henledes på, at designdiagrammerne alene dokumenterer den
samlede reduktion og ikke, hvor i opbygningen den tages. Minimumstykkelsen og
fastholdelsen af det øverste lag er således konstruktive regler, der lægges
oven på beregningen.

Der gøres endvidere opmærksom på, at lagforholdet i de beregnede
opbygninger ændres, når det øverste lag holdes på minimumstykkelsen eller
fastholdes. Hvilken φᵥ opbygningerne da regnes med, er beskrevet i
afsnit 4.

## 3 Underliggende lag

Holdes det øverste lag på minimumstykkelsen, eller fastholdes det, bliver
der mindre tilbage til de underliggende lag. Bundsikringslaget kan derved
blive tyndere, end det kan indbygges. Under Indstillinger, afsnittet
Underliggende lag, fastlægges, hvordan et tyndt underliggende lag behandles:

- **Lagene vises som fordelt.** Lagene angives, som fordelingen efter
  afsnit 2 giver dem.
- **Et lag tyndere end grænsen lægges til laget ovenover.** Et
  underliggende lag, der er tyndere end den valgte grænse, indgår i laget
  ovenover — ved to lag således i det øverste lag. Standardgrænsen er
  100 mm. Den samlede lagtykkelse og reduktionen er uændrede.
- **Lagene gøres mindst så tykke som VD's mindste lagtykkelse.** Hvert
  underliggende lag skal mindst have den mindste lagtykkelse for sin
  lagtype. Den samlede lagtykkelse øges i hele indbygningstrin, til
  fordelingen efter afsnit 2 opfylder kravet, og reduktionen mindskes
  tilsvarende.

Lagtypen fremgår af materialetabellen. Standardværdierne for den mindste
lagtykkelse fremgår af Figur 6.4. De følger håndbogens Figur 6.5 og kan
redigeres under Indstillinger.

:::figur Mindste lagtykkelse for underliggende lag, jf. Vejdirektoratets håndbog, Figur 6.5.
| Lagtype | Mindste lagtykkelse [mm] | Materialer i Figur 6.5 |
| --- | ---: | --- |
| Bærelag | 100 | SG I, SG II, KB, KBT, KAS, KBA, FS I |
| Bundsikring | 200 | BL I og BL II |
:::

Ved den sidste regel bestemmes den samlede lagtykkelse som den mindste
tykkelse fra den oprundede og eventuelt til minimumstykkelsen øgede
lagtykkelse og opefter, hvor alle underliggende lag kan indbygges.

:::formel
T_ind  =  min { T ≥ T_min,  T = n × t :  t_i ≥ t_i,min  for alle underliggende lag med t_i > 0 }
--
T_ind    er den angivne samlede lagtykkelse [mm]
T_min    er den oprundede lagtykkelse, eventuelt øget til minimumstykkelsen [mm]
t        er oprundingstrinnet [mm]
t_i      er tykkelsen af det underliggende lag i ved fordelingen efter afsnit 2 [mm]
t_i,min  er den mindste lagtykkelse for lagets lagtype [mm]
:::

Tillægget står som eget led i mellemregningerne efter oprundingen og
tillægget til minimumstykkelsen. Forklaringen til leddet angiver lagene før
og efter tillægget. Den ustabiliserede opbygning behandles efter samme
regel. I Standard gælder reglen for opdelingen i stabilgrus og bundsikring,
jf. afsnit 5.

Uden yderligere valg godtages en opbygning, hvor det øverste lag udgør hele
tykkelsen, idet der da ikke er noget underliggende lag at vurdere. Under
valget »VD's mindste lagtykkelse« kan det tilvælges, at der altid kræves et
bundsikringslag. Opbygningen øges da, til også bundsikringen har sin mindste
tykkelse. Uden dette tilvalg kan reduktionen springe ved stiv underbund, som
vist i Figur 6.5.

:::figur Stabilgrus mindst 250 mm, bundsikring mindst 200 mm. Belastningsklasse 4, 1 lag geonet. Ustabiliseret / med geonet [mm], reduktion [mm].
| Eᵤ | Bundsikringslag ikke krævet | Bundsikringslag krævet |
| ---: | --- | --- |
| 28 | 450 / 450, reduktion 0 | 450 / 450, reduktion 0 |
| 30 | 450 / 250, reduktion 200 | 450 / 450, reduktion 0 |
| 33 | 450 / 250, reduktion 200 | 450 / 450, reduktion 0 |
:::

Ved Eᵤ = 30 og 33 MPa er opbygningen med geonet præcis stabilgrusminimum og
har ingen bundsikring. Uden tilvalget godtages den, mens den ustabiliserede
opbygning øges til 450 mm. Reduktionen springer derved fra 0 til 200 mm, selv
om underbunden kun er lidt stivere.

Figur 6.6 viser de tre regler for en indtastet opbygning af 300 mm
stabilgrus over 400 mm bundsikringssand ved belastningsklasse 4 og
Eᵤ = 27 MPa. Opbygningen med 1 lag geonet er beregnet til 279 mm og
oprundet til 300 mm. Minimumstykkelsen er 250 mm, og den ustabiliserede
opbygning er 450 mm.

:::figur Behandling af et tyndt bundsikringslag. Belastningsklasse 4, Eᵤ = 27 MPa, 1 lag geonet.
| Regel | Stabilgrus [mm] | Bundsikring [mm] | Samlet [mm] | Reduktion [mm] |
| --- | ---: | ---: | ---: | ---: |
| Vises som fordelt | 250 | 50 | 300 | 150 |
| Lægges til laget ovenover | 300 | — | 300 | 150 |
| VD's mindste lagtykkelse | 250 | 200 | 450 | 0 |
:::

Opmærksomheden henledes på, at den sidste regel i eksemplet fjerner hele
reduktionen. Geonettet giver her ikke en tyndere opbygning, der kan
indbygges med de valgte materialer.

## 4 Friktionsvinkel i opbygningerne

Den vægtede friktionsvinkel φᵥ bestemmes af den indtastede opbygning, jf.
kapitel 1, afsnit 6. Ved proportional fordeling har alle beregnede
opbygninger det indtastede lagforhold, og φᵥ svarer til deres materialer.
Holdes det øverste lag på minimumstykkelsen, eller fastholdes det, jf.
afsnit 2, indeholder de stabiliserede opbygninger relativt mere af det
øverste lags materiale, og opbygningens egen φᵥ afviger fra den indtastede
opbygnings.

Under Indstillinger, afsnittet Friktionsvinkel i opbygningerne, fastlægges,
hvilken φᵥ hver beregnet opbygning regnes med:

- **φᵥ for den indtastede opbygning.** Samme φᵥ anvendes i alle beregnede
  opbygninger. Reduktionen afspejler alene geonettet.
- **Den laveste af de to.** Hver opbygning regnes med den laveste af φᵥ for
  den indtastede opbygning og φᵥ for opbygningens egne lag. Ingen opbygning
  regnes dermed med en højere φᵥ, end dens egne lag giver.
- **φᵥ for opbygningens egne lag.** Hver opbygning regnes med φᵥ for sine
  egne lag, også når det giver en tyndere opbygning.

:::formel
φᵥ,opb  =  Σ(tᵢ × φᵢ) / Σ tᵢ
--
tᵢ  er tykkelsen af lag i i opbygningen efter fordelingen og oprundingen til hele trin [mm]
φᵢ  er lagets friktionsvinkel [°]
:::

Opbygningens lag afhænger af dens tykkelse, som igen afhænger af φᵥ.
Beregningen gentages derfor, til φᵥ er uændret. Skifter φᵥ mellem to
værdier uden at blive stabil, anvendes den laveste, hvilket giver den
tykkeste opbygning. φᵥ gælder ved det aktuelle Eᵤ; designdiagrammets kurver
tegnes med hver opbygnings φᵥ, så aflæsningen ligger på kurven. Ved de to
sidste regler omfatter reduktionen også forskellen i materialer mellem den
ustabiliserede og den stabiliserede opbygning.

Reglen gælder Brugerdefineret med mindst to materialelag. Er φᵥ overskrevet
manuelt, anvendes den manuelle værdi i alle opbygninger.

Figur 6.7 og Figur 6.8 viser betydningen for to indtastede opbygninger med
300 mm stabilgrus, φ = 40°, over 400 mm af et andet materiale ved
belastningsklasse 5 og 1 lag geonet. Det øverste lag holdes på
minimumstykkelsen, 275 mm oprundet til 300 mm.

:::figur Stabilgrus over bundsikringssand, φ = 37°. Eᵤ = 20 MPa, 1 lag geonet.
| Regel | Stabilgrus / bundsikring [mm] | φᵥ | Beregnet [mm] | Angivet [mm] |
| --- | ---: | ---: | ---: | ---: |
| Indtastet opbygning | 300 / 200 | 38,29° | 471 | 500 |
| Den laveste af de to | 300 / 200 | 38,29° | 471 | 500 |
| Opbygningens egne lag | 300 / 200 | 38,80° | 466 | 500 |
:::

:::figur Stabilgrus over skærver 0-120, φ = 45°. Eᵤ = 22 MPa, 1 lag geonet.
| Regel | Stabilgrus / skærver [mm] | φᵥ | Beregnet [mm] | Angivet [mm] |
| --- | ---: | ---: | ---: | ---: |
| Indtastet opbygning | 300 / 100 | 42,86° | 397 | 400 |
| Den laveste af de to | 300 / 150 | 41,67° | 408 | 450 |
| Opbygningens egne lag | 300 / 150 | 41,67° | 408 | 450 |
:::

Ved stabilgrus over bundsikringssand har det øverste lag den højeste
friktionsvinkel. Opbygningens egen φᵥ er højere end den indtastede opbygnings,
og regnet med den indtastede φᵥ ligger beregningen på den sikre side. Ved
stabilgrus over skærver er forholdet det modsatte. Regnet med den indtastede
φᵥ angives 400 mm, mens opbygningens egne lag kræver 450 mm.

## 5 Standard-beregning

I Standard regnes med designdiagrammernes referencemateriale, φᵥ = 37°, og
den samlede tykkelse fastlægges af designdiagrammet. Under Indstillinger,
afsnittet Standard-beregning, fastlægges, hvordan resultatet vises.

**Opdeling i stabilgrus og bundsikring.** Opbygningen vises som stabilgrus
over bundsikring. Stabilgruset sættes til minimumstykkelsen for klassen i
tabellen fra afsnit 2, oprundet til indbygningstrin, og bundsikringen udgør
resten. Tabellen anvendes uanset fordelingsvalget i afsnit 2, som alene
gælder Brugerdefineret. Tynde bundsikringslag behandles efter afsnit 3.

:::formel
t_SG  =  min( T ;  ⌈t_min / t⌉ × t )
t_BL  =  T − t_SG
--
t_SG   er tykkelsen af stabilgruslaget [mm]
t_BL   er tykkelsen af bundsikringslaget [mm]
T      er den samlede, oprundede lagtykkelse [mm]
t_min  er minimumstykkelsen for klassen [mm]
t      er oprundingstrinnet [mm]
:::

Opmærksomheden henledes på, at opdelingen viser en typisk opbygning.
Beregningen er fortsat ført med referencematerialet φ = 37° og ikke med
materialernes egne friktionsvinkler. Indtastes samme opbygning i
Brugerdefineret, kan resultatet derfor blive tyndere. Ved belastningsklasse
4, Eᵤ = 10 MPa og 1 lag geonet giver Standard 617 mm, oprundet til 650 mm;
Brugerdefineret med 250 mm stabilgrus over 650 mm skærver 0-120 giver 535 mm,
oprundet til 550 mm.

**Opbygning tyndere end stabilgrusminimum.** Er fluebenet »Den samlede
bærelagstykkelse sættes mindst til minimumstykkelsen« fjernet, kan
opbygningen med geonet blive tyndere end stabilgrusminimum. For det tilfælde
vælges, om hele tykkelsen vises som stabilgrus, om tykkelsen øges til
stabilgrusminimum, eller om opbygningen vises som ét samlet ubundet lag.

:::figur Belastningsklasse 4, Eᵤ = 33 MPa, 1 lag geonet, fluebenet for samlet minimum fjernet. Den ustabiliserede opbygning er 350 mm = 250 mm stabilgrus + 100 mm bundsikring.
| Valg | Opbygning med geonet | Reduktion [mm] |
| --- | --- | ---: |
| Hele tykkelsen vises som stabilgrus | 200 mm stabilgrus | 150 |
| Tykkelsen øges til stabilgrusminimum | 250 mm stabilgrus | 100 |
| Ét samlet ubundet lag | 200 mm ubunden opbygning | 150 |
:::

Situationen er et ydertilfælde ved stiv underbund og forekommer sjældent,
idet geonet typisk anvendes ved lave E-moduler i planum.

**Klassisk standardberegning.** Er klassisk standardberegning valgt, regnes
Standard direkte efter designdiagrammerne. Den samlede tykkelse oprundes
alene til indbygningstrin; der anvendes ingen minimumstykkelse, heller ikke
når fluebenet for samlet minimum er sat, og opbygningen vises som ét samlet
ubundet lag. Det øverste geonet ved 2 lag placeres ved nettets mindste
dæklag. Valget gælder alene Standard.

## 6 Placering af geonet ved 2 lag

Ved 2 lag geonet ligger det nederste net i bunden af opbygningen. Består
opbygningen af flere lag, fastlægges det øverste nets placering under
Indstillinger, afsnittet Geonet ved 2 lag:

- **Ved laggrænsen.** Nettet ligger ved grænsen mellem det øverste og det
  næste lag. Er det øverste lag tyndere end nettets mindste dæklag, gives en
  placeringsadvarsel.
- **Ved nettets mindste dæklag.** Nettet ligger ved nettets mindste dæklag,
  uafhængigt af lagene.
- **Ved laggrænsen, dog mindst dæklaget.** Nettet ligger ved laggrænsen,
  eller dybere, når nettets mindste dæklag kræver det.

Uden lag, fx ved klassisk standardberegning, placeres nettet ved nettets
mindste dæklag. Valget gælder både Standard og Brugerdefineret.

:::figur Placering af øverste geonet i 600 mm = 250 mm stabilgrus + 350 mm bundsikring.
| Valg | Net med dæklag 200 mm | Net med dæklag 400 mm |
| --- | --- | --- |
| Ved laggrænsen | 250 mm | 250 mm, advarsel om dæklag |
| Ved nettets mindste dæklag | 200 mm | 400 mm |
| Ved laggrænsen, dog mindst dæklaget | 250 mm | 400 mm |
:::

## 7 Statuslinjen

Linjen under hver beregnede søjle angiver forskellen mellem det beregnede krav
og den indtastede tykkelse. »311 mm for lidt« betyder, at opbygningen kræver
311 mm mere for at være tilstrækkelig. »92 mm i overskud« betyder, at den
indtastede opbygning er 92 mm tykkere end nødvendigt. Den grønne farve
markerer, at kravet er opfyldt.

Står der en værdi i parentes med tilføjelsen »optimalt«, gælder den den
optimale ende af produktets korrektionsinterval, jf. kapitel 5, afsnit 2.

Forklaringen under visualiseringen angiver lagfladerne, geonettets linje, den
optimale korrektion og det indtastede niveau. Forklaringen følger med til
rapportens billede, så skærm og rapport viser samme visualisering.
