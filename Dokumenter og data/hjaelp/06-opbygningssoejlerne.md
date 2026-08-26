---
titel: Sådan læses resultaterne
resume: Hvordan den indtastede opbygning sammenholdes med de beregnede krav, hvordan geonetplaceringen vises, og hvordan statuslinjen angiver forskellen mellem krav og indtastet tykkelse.
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
stedet proportionalt efter de indtastede lagtykkelser. Søjlerne viser dermed
den samlede beregning fordelt på en mulig lagopbygning.

Hvis φᵥ overskrives manuelt, anvendes den manuelt indtastede værdi i stedet
for den tykkelsesvægtede værdi.

De røde linjer markerer geonettets placering. Ved to lag placeres det øverste
net ved den reducerede materialegrænse. Ved beregning efter trafikklasse kan
søjlens grundlag være VejDims ubundne tykkelse, jf. kapitel 2, afsnit 3.

Har det valgte produkt et korrektionsinterval, angives den optimale ende med
en grøn, prikket linje. Mellemregningen bag værdien vises ved markøren.

## 2 Statuslinjen

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
