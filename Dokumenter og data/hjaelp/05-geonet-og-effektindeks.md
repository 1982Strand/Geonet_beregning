---
titel: Geonet og effektindeks
resume: Referencenettet bag diagrammerne, hvordan effektindekset omsættes til en korrektion af lagtykkelsen, og hvorfor to lag ikke giver den dobbelte reduktion.
---

## 1 Referencenettet

Designdiagrammerne er optegnet for tre referencenet — Tensar TriAx TX160,
GS-GRID SX160 og E'GRID T6 — som alle har effektindeks 100. Øvrige produkter i
geonet-databasen er indekseret i forhold til disse.

Vælges et referencenet, anvendes diagrammernes værdier uændret, og k_net er 0.
Enkelte øvrige produkter er tilkendt samme effektindeks og giver dermed samme
lagtykkelse, uden at de indgår i diagrammernes optegning.

## 2 Effektindekset

Effektindekset angiver produktets effektivitet i forhold til referencenettet.
Et produkt med indeks under 100 giver en mindre reduktion end referencenettet;
et indeks over 100 giver en større. Indekset er fastlagt ved sammenligning af
produkternes trækstyrke- og stivhedsegenskaber i BG Byggros' interne forsøg og
leverandørernes egne datablade.

Indekset omsættes til en korrektion af den armerede lagtykkelse:

:::formel
k_net  =  (100 − indeks) / 100
--
indeks   er produktets effektindeks; referencenettet har 100
:::

Fortegnet følger konventionen i resten af værktøjet: en positiv k_net giver et
tykkere bærelag (mindre effektivt net), en negativ et tyndere. Et produkt med
indeks 90 giver således k_net = +0,10, og et med indeks 115 giver k_net = −0,15.

Enkelte produkter er tabuleret med et effektindeks i to ender, eksempelvis
Tensar InterAx NX750 med 110–120 og NX850 med 115–130. Beregningerne tager
udgangspunkt i den nedre, konservative ende; den optimale ende opgøres
særskilt og vises i detaljeboksen, i opbygningssnittene og i designdiagrammet,
hvor den tegnes som en prikket kurve med et tonet bånd op til den
konservative.

:::figur Bærelagstykkelse i mm ved Eᵤ = 8 MPa, T4, 1 lag geonet.
| Produkt | Indeks | 1 lag |
| --- | --- | --- |
| TX160 (ref.) | 100 | 738 |
| TX150 | 90 | 812 |
| NX850 | 115 | 627 |
:::

## 3 To lag geonet

Ved to lag anvendes som standard samme produkt i begge lag. Reduktionen for
2 lag er ikke den dobbelte af 1 lag — den aflæses som sin egen kurve i
designdiagrammet, idet samspillet mellem to armeringslag ikke er lineært.

Placeringen af nettene kontrolleres mod produktets krav til mindste dæklag og
mod afstanden mellem lagene. Kan kravene ikke overholdes ved den beregnede
lagtykkelse, gives en placeringsadvarsel ved opbygningssnittet.
