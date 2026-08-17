---
titel: Materialer og friktionsvinkel
resume: Hvordan den vægtede friktionsvinkel dannes af materialelagene, hvordan φ-korrektionen virker på lagtykkelsen, og hvornår kornstørrelsen udelukker et materiale.
---

## 1 Vægtet friktionsvinkel

Opbygningens friktionsvinkel φ bestemmes som et tykkelsevægtet gennemsnit af de
indtastede materialelags friktionsvinkler. Designmanualerne forudsætter
φ = 37°; afviger den vægtede værdi herfra, korrigeres basistykkelsen.

:::formel
φ  =  Σ (t_i × φ_i) / Σ t_i
--
t_i   er tykkelsen af lag i [mm]
φ_i   er lagets friktionsvinkel [°]
:::

I Standard-tilstand forudsættes ét samlet ubundet bærelag med φ = 37°, og der
sammensættes ikke materialelag. Den vægtede friktionsvinkel forekommer derfor
alene i Brugerdefineret-tilstand.

:::figur Eksemplet fra dimensioneringssiden. Den vægtede vinkel giver kᵩ = −0,0257.
| Lag | mm | φ |
| --- | --- | --- |
| Stabilgrus | 300 | 40,0° |
| Bundsikring | 400 | 37,0° |
| Vægtet | 700 | 38,3° |
:::

## 2 φ-korrektionen

Korrektionsfaktoren kᵩ er lineær omkring φ = 37°. En positiv afvigelse giver
en negativ kᵩ, det vil sige en tyndere opbygning.

:::formel
kᵩ  =  −0,02 × (φ − 37°)
--
φ   er den vægtede friktionsvinkel [°]
:::

Korrektionen anvendes på samtlige tre kurver, jf. kapitel 1, afsnit 5.

Der gøres opmærksom på, at korrektionen ikke er begrænset opadtil eller
nedadtil. Ligger den vægtede vinkel under 37° eller over 50°, gives en advarsel
i dimensioneringen, idet materialevalget da ligger uden for det område,
designmanualerne dækker.

## 3 Kornstørrelse mod maskestørrelse

Et materiale kan ikke vælges til et lag, der ligger direkte mod geonettet, hvis
materialets maksimale kornstørrelse overstiger nettets maskestørrelse. Kornene
vil da falde igennem i stedet for at blive låst af nettet.

Materialeoversigten og geonet-databasen markerer disse kombinationer. Der gøres
opmærksom på, at databladets maksimale kornstørrelse og designmanualens
anbefalede tilslag kan afvige for det samme produkt; begge er angivet i
databasen.
