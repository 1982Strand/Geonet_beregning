# Plan: automatisk opdeling i stabilgrus og bundsikring

**Dato:** 27. september 2026  
**Status:** Implementeret 27. september 2026; afventer gennemsyn i browseren.

## Formål

I Standard-beregningen vises den dimensionerede ubundne tykkelse som en
opbygning af stabilgrus og bundsikring. Standard skal desuden kunne danne en
rapport med opdelingen. Brugerdefinerets beregningsgang bevares, bortset fra
de fælles valg, der er nævnt under Afklaringer.

Opdelingen er en indstilling, så Standard fortsat kan vises som ét samlet
ubundet lag, når automatisk opdeling er slået fra.

## Aftalte regler

- Automatisk opdeling er slået til som standard.
- Stabilgruslaget sættes til minimumstykkelsen for belastningsklassen i
  indstillingernes afsnit **3. Øverste bærelag**. Tabellen dér er eneste kilde
  til værdierne; de må ikke kopieres til en ny tabel. Tabellen bruges altid af
  Standard, uanset hvilken fordeling der er valgt i afsnit 3.
- Minimumstykkelsen **oprundes** til det gældende oprundingstrin; der rundes
  aldrig ned.
- Bundsikringen udgør resten af den samlede dimensionerede tykkelse.
- Tynde underliggende lag behandles efter valget i afsnit **4. Underliggende
  lag**, som gælder både Standard og Brugerdefineret. Valget »VD's mindste
  lagtykkelse« svarer til et bundsikringsminimum; standardværdien er 200 mm.
- Et eventuelt tillæg indgår i beregningens tykkelsesresultat og reduktion,
  ikke kun i den viste figur.
- Standard regnes fortsat med referencematerialet φᵥ = 37°. Opdelingen
  indfører ingen vægtet friktionsvinkel.

## Afklaringer (27. september 2026)

### 1 Rapport fra Standard

Standard skal kunne danne en rapport. Rapportsiden kræver i dag en
dimensionering i Brugerdefineret med et valgt geonet. Standard skal gemme sit
resultat, og rapporten skal kunne vise Standard-opbygningen med den
automatiske opdeling. Rapportens tekster, dimensioneringsgrundlag og figur
skal tilpasses, så der ikke forudsættes indtastede materialelag.

### 2 Samlet minimum fjernet

Fluebenet »Den samlede bærelagstykkelse sættes mindst til minimumstykkelsen«
bevares. Er det fjernet, kan en opbygning blive tyndere end
stabilgrusminimum. For det tilfælde indføres et valg med tre opførsler:

| Valg | Virkning ved 200 mm og minimum 250 mm |
| --- | --- |
| Ét lag stabilgrus (standard) | 200 mm stabilgrus, intet løft |
| Opdelingen løfter altid | 250 mm stabilgrus |
| Ét samlet ubundet lag | 200 mm vist som én ubunden opbygning |

Valget forklares i appen med et regneeksempel, fx belastningsklasse 4,
Eᵤ = 33 MPa, 1 lag: ustabiliseret 350 mm, med geonet beregnet 200 mm. Det
anføres, at situationen er et ydertilfælde ved stiv underbund og sjældent
forekommer, idet geonet typisk anvendes ved lave E-moduler i planum.

### 3 Bundsikringsminimum

- **3a** Afsnit 4 styrer også Standard. Planens oprindelige særskilte
  til/fra-valg for bundsikringsminimum udgår. Feltet for bundsikringens
  mindste lagtykkelse genbruges uden kopi.
- **3b** Under valget »VD's mindste lagtykkelse« indføres fluebenet »Kræv
  altid et bundsikringslag«. Det gælder begge tilstande og er **slået fra**
  som standard.
  - Slået fra: en opbygning, der netop svarer til stabilgrusminimum, godtages
    som rent stabilgrus.
  - Slået til: opbygningen øges til stabilgrusminimum + bundsikringsminimum.

  Opmærksomheden henledes på, at reglen uden fluebenet giver et spring i
  reduktionen ved stiv underbund. Eksempel, belastningsklasse 4, 1 lag:
  Eᵤ = 28 giver 450/450 mm og reduktion 0; Eᵤ = 30 giver 450/250 mm og
  reduktion 200 mm. Med fluebenet er begge 450/450 mm.

### 4 Placering af øverste geonet ved 2 lag

Placeringen bliver et valg under Indstillinger, som gælder både Standard og
Brugerdefineret:

- Ved laggrænsen mellem stabilgrus og bundsikring (standard; som
  Brugerdefineret i dag). Net med større dæklagskrav end stabilgruslaget giver
  placeringsadvarsel.
- Ved nettets mindste dæklag (som Standard i dag).
- Ved laggrænsen, dog mindst nettets mindste dæklag.

### 5 Minimumstabellen

- **5a** Standard bruger altid tabellen, uanset fordelingsvalget i afsnit 3.
  Fordelingsvalget gælder kun Brugerdefinerets materialelag.
- **5b** Tabellen tillader ikke 0. Mindsteværdien er 100 mm, VD's mindste
  lagtykkelse for stabilgrus (Figur 6.5).

### 6 Oprunding

Stabilgrusminimum oprundes altid til oprundingstrinnet. Står der en værdi i
tabellen, som ikke går op i det valgte trin, vises en advarsel på
indstillingssiden med de berørte klasser.

### 7 φᵥ og lagnavne

Standard regnes med φᵥ = 37°. Lagene benævnes »Stabilgrus« og
»Bundsikring«. En note ved figuren og hjælpeteksten forklarer, at opdelingen
viser en typisk opbygning, at beregningen er ført med referencematerialet
φ = 37°, og at en materialespecifik beregning foretages i Brugerdefineret.
Eksempel, belastningsklasse 4, Eᵤ = 10, 1 lag: Standard 617 → 650 mm;
Brugerdefineret med 250 mm stabilgrus over 650 mm skærver 0-120 giver
535 → 550 mm.

### 8 Mellemregning

Forklaringen til leddet »Tillæg for mindste lagtykkelse« viser lagene og
tallene, fx »Stabilgrus 250 mm + bundsikring 200 mm = 450 mm. Bundsikringen er
øget fra 50 mm til VD's mindste lagtykkelse«. Det gælder musteksten i kortet
»Detaljer« og den grå note i »Sådan er resultatet beregnet«, i begge
tilstande.

### 9 Klassisk standardberegning

Standards indstillingsgruppe får en hovedafbryder, »Klassisk
standardberegning«, som er **slået fra** som standard. Er den slået til,
regnes og vises Standard direkte efter designdiagrammerne:

- den samlede tykkelse oprundes alene til indbygningstrin,
- der anvendes ingen minimumstykkelse, heller ikke når fluebenet for samlet
  minimum i afsnit 3 er sat,
- opbygningen vises som ét samlet ubundet lag uden opdeling og uden regler
  for underliggende lag,
- det øverste geonet ved 2 lag placeres ved nettets mindste dæklag.

Brugerdefinerets indstillinger og beregning berøres ikke af afbryderen.
Teksten ved afbryderen beskriver virkningen, ikke appens historik, så den kan
forstås af en ny bruger.

## Implementering

### 1. Indstillinger

- Tilføj en normaliseret indstillingsgruppe til automatisk opdeling i
  Standard. Manglende værdier i ældre indstillingsfiler får de aftalte
  standardværdier.
- Tilføj hovedafbryderen »Klassisk standardberegning« (afklaring 9). Når den
  er slået til, deaktiveres Standards øvrige valg i gruppen, og det fremgår,
  at samlet minimum, opdeling, lagregler og netplacering ikke gælder
  Standard.
- Tilføj valget for opførslen, når samlet minimum er fjernet (afklaring 2),
  med regneeksempel og note om ydertilfældet.
- Tilføj fluebenet »Kræv altid et bundsikringslag« under VD-valget i afsnit 4
  (afklaring 3b).
- Tilføj valget for placering af øverste geonet ved 2 lag (afklaring 4).
- Sæt minimumstabellens mindsteværdi til 100 mm, og vis advarslen om trin
  (afklaring 5b og 6).
- Beskriv i afsnit 4, at valget også gælder Standard.
- Markér ved hvert afsnit eller valg på indstillingssiden, hvilken tilstand
  det gælder: Standard, Brugerdefineret eller begge. Markeringen følger
  hovedafbryderen, så det fremgår, når et valg ikke gælder Standard, fordi
  klassisk standardberegning er slået til.

### 2. Beregningsgrundlag

- Brug den eksisterende klassebestemmelse og opslaget i tabellen fra afsnit 3.
  For trafikklasser anvendes samme belastningsklasse som ved de øvrige
  minimumsregler.
- Dan Standard-opdelingen med den eksisterende lagfordeling
  (core.lagfordeling), med stabilgrus fastholdt på det oprundede minimum og
  bundsikring som resten. Lagene må ikke sendes ind som materialelag, idet
  appen så viser en »Indtastet opbygning«-søjle og statuslinjer.
- Før tillæg for bundsikringsminimum ind via den eksisterende mekanisme i
  core.afrunding, før resultater og reduktioner beregnes.
- Bevar Standard-beregningens friktionsvinkel og øvrige diagramopslag.

### 3. Resultatopbygning

- Når automatisk opdeling er aktiv, vises hvert Standard-resultat med
  stabilgrus øverst og bundsikring nedenunder.
- En lagtykkelse på nul vises ikke som et fysisk lag.
- Når automatisk opdeling er slået fra, bevares den nuværende visning som ét
  ubundet lag.
- Placeringen af geonet og placeringsadvarslerne følger valget i afklaring 4.
- Lagdelingen må alene beskrive Standard-resultatet. Den må ikke sendes ind i
  Brugerdefinerets materialekorrektioner, materialevalidering eller
  geonetberegning.

### 4. Rapport og dokumentation

- Standard gemmer sit resultat til rapporten, og rapporten viser samme
  lagfordeling som Standard-visningen (afklaring 1).
- Opdatér hjælpeteksterne om beregningsmetoden og opbygningssøjlerne:
  diagrammet fastlægger fortsat den samlede tykkelse, mens indstillingerne
  fordeler resultatet og eventuelt øger det for mindste lagtykkelser.
  Forklar φᵥ = 37° i Standard (afklaring 7).

## Kontrolpunkter ved implementering

- Hver belastningsklasse henter stabilgrusminimum fra indstillingstabellen,
  også når tabellen er redigeret, og også når afsnit 3 står på
  »Proportionalt«.
- Et oprundingstrin, der ikke går op i stabilgrusminimum, giver en samlet
  opbygning uden underskridelse og en advarsel under Indstillinger.
- Tabellen afviser værdier under 100 mm.
- Med afsnit 4 på »Vises som fordelt« bliver bundsikringen resten af den
  beregnede tykkelse.
- Med »VD's mindste lagtykkelse« øges tykkelsen, til bundsikringen er mindst
  200 mm, og reduktionen afspejler tillægget. Med fluebenet »Kræv altid et
  bundsikringslag« gælder det også, når der ingen rest er.
- Med samlet minimum fjernet følger resultatet valget i afklaring 2.
- Placeringen af geonet ved 2 lag følger valget i afklaring 4 i begge
  tilstande.
- Trafikklasse, også uden for diagrammets område, henter klassen som de
  øvrige minimumsregler.
- Standard-resultatkort, opbygningsfigur, mellemregning og rapport viser samme
  lagtykkelser.
- Når opdelingen slås fra, vises ét ubundet lag.
- Med »Klassisk standardberegning« slået til giver Standard samme tykkelser,
  reduktioner, figur og netplacering som en beregning uden minimumstykkelse,
  opdeling og lagregler, uanset fluebenet for samlet minimum. Brugerdefineret
  påvirkes ikke.
- Brugerdefinerede beregninger er uændrede med standardværdierne for de nye
  valg.

## Afgrænsning

Opdelingen ændrer ikke de faglige diagramopslag eller beregner en
friktionsvinkel for de to lag. Den vurderer heller ikke frostforhold. Sådanne
krav skal fortsat håndteres særskilt, hvis de skal indgå i dimensioneringen.
