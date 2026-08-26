---
titel: Materialer og friktionsvinkel
resume: Hvordan den vægtede friktionsvinkel dannes af materialelagene, hvordan φᵥ-korrektionen virker på lagtykkelsen, og hvornår kornstørrelsen udelukker et materiale.
---

## 1 Vægtet friktionsvinkel

Opbygningens vægtede friktionsvinkel φᵥ bestemmes som et tykkelsevægtet gennemsnit af de
indtastede materialelags friktionsvinkler. Designmanualerne forudsætter
φᵥ = 37°; afviger den vægtede værdi herfra, korrigeres basistykkelsen.

:::formel
φᵥ =  Σ (t_i × φ_i) / Σ t_i
--
t_i   er tykkelsen af lag i [mm]
φ_i   er lagets friktionsvinkel [°]
:::

I Standard-tilstand forudsættes ét samlet ubundet bærelag med φᵥ = 37°, og der
sammensættes ikke materialelag. Den vægtede friktionsvinkel forekommer derfor
alene i Brugerdefineret-tilstand.

Figur 4.1 viser, hvordan materialelagenes individuelle friktionsvinkler indgår
i beregningen af den vægtede værdi φᵥ.

:::figur Eksemplet fra dimensioneringssiden. Den vægtede vinkel giver k_φ = −0,0257.
| Lag | mm | Friktionsvinkel |
| --- | --- | --- |
| Stabilgrus | 300 | 40,0° |
| Bundsikring | 400 | 37,0° |
| Vægtet (φᵥ) | 700 | 38,3° |
:::

## 2 φᵥ-korrektionen

Korrektionsfaktoren k_φ er lineær omkring φᵥ = 37°. Beregningsforudsætningen er,
at lagtykkelsen reduceres med 2 % for hver grad, den vægtede friktionsvinkel
ligger over 37°. Omvendt øges lagtykkelsen med 2 % for hver grad under 37°.
De 2 % skrives som decimalen 0,02 i formlen. Derfor giver en positiv afvigelse
fra 37° en negativ k_φ og dermed en tyndere opbygning.

:::formel
k_φ =  −0,02 × (φᵥ − 37°)
--
φᵥ  er den vægtede friktionsvinkel [°]
:::

Korrektionen anvendes på samtlige tre kurver, jf. kapitel 1, afsnit 6.

Der gøres opmærksom på, at korrektionen ikke er begrænset opadtil eller
nedadtil. Ligger den vægtede vinkel under 37° eller over 50°, gives en advarsel
i dimensioneringen, idet materialevalget da ligger uden for det område,
designmanualerne dækker.

## 3 Materiale- og geonetkompatibilitet

Værktøjet udfører to separate kompatibilitetskontroller, når der er valgt både
materialelag og geonet i Brugerdefineret-tilstand. Kontrollerne må ikke
forveksles:

- Materialets maksimale kornstørrelse sammenholdes med geonettets angivne
  maksimale kornstørrelse. Hvis materialets værdi er større, gives en advarsel,
  fordi materialet kan være uforeneligt med det valgte net.
- For biaksiale geonet sammenholdes materialets minimumskrav til maskestørrelse
  med geonettets faktiske maskestørrelse. Hvis materialets krav
  er større end nettets maskestørrelse, gives der en advarsel. Denne kontrol
  udføres ikke for triaksiale eller hexagonale net.

Hvis en af de nødvendige værdier mangler, kan den pågældende kontrol ikke
gennemføres automatisk. Materialeoversigten og geonetdatabasen viser de værdier,
der ligger til grund for kontrollerne. Databladets maksimale kornstørrelse og
designmanualens anbefalede tilslag kan afvige for det samme produkt; begge dele
er derfor angivet særskilt i databasen.
