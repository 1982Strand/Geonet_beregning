---
titel: Designdiagrammerne
resume: De tre kurver i hvert af de seks diagrammer, hvordan der interpoleres i de aflæste punkter, og hvad der sker uden for diagrammets område.
---

## 1 De tre kurver

Hvert af de seks designdiagrammer viser bærelagstykkelsen som funktion af
underbundens E-modul for tre opbygninger: ustabiliseret, med 1 lag geonet og
med 2 lag geonet. Diagrammerne er leverandørernes egne, ét pr.
belastningsklasse, og er optegnet for referencenettet.

Kurverne vises på siden Designdiagrammer, både som designmanualens egen
scanning og som en optegning af de aflæste værdier. Optegningen anvender
gennemgående de samme farver som værktøjets øvrige diagrammer: sort for
ustabiliseret, blåt for 1 lag og lilla for 2 lag.

:::figur Uddrag af diagram 4, belastningsklasse 4. Værdien ved 95 MPa er interpoleret.
| Eo [MPa] | Ustab. [cm] | 1 lag [cm] |
| --- | --- | --- |
| 90 | 95,9 | 64,7 |
| 95 | 92,9 | 62,3 |
| 100 | 90,0 | 60,0 |
:::

## 2 Aflæsning og interpolation

Der slås ikke op i kurverne selv, men i de aflæste datapunkter, som ligger i
tabellen ved hvert diagram. Interpolationen mellem diagrammernes værdier er
foretaget på forhånd, og beregningen anvender tabellen direkte som opslag.

Ved dimensionering efter belastningsklasse rammer opslaget en af diagrammernes
egne søjler — 30, 45, 60, 80, 120 og 150 MPa — og værdien aflæses uændret.

Rammes en søjle ikke, bestemmes værdien ved lineær interpolation mellem de to
nærmeste søjler. Dette er tilfældet ved dimensionering efter trafikklasse, hvor
Eo er den tilbageberegnede ækvivalente Eo, jf. kapitel 1, afsnit 4.

:::formel
t  =  t_lav  +  f × (t_høj − t_lav)
--
f            er interpolationsfaktoren, jf. kapitel 1, afsnit 3
t_lav, t_høj er de aflæste lagtykkelser ved de to nærmeste søjler [cm]
:::

Interpolationen udføres særskilt for hver af de tre kurver med samme f.

## 3 Uden for diagrammets område

Diagrammerne er ikke optegnet for hele Eu-området. Den ustabiliserede
opbygning er ikke dimensioneret under Eu = 3 MN/m², og de armerede kurver
ophører ved hver sin øvre grænse; 2 lag geonet forekommer slet ikke i
diagram 1.

Ligger opslagspunktet uden for det aflæste spænd, angives værdien med en
tankestreg i tabellen, og beregningen kan ikke gennemføres for den
kombination. Forholdet svarer til zonerne under og over, jf. kapitel 2.

De aflæste værdier kan redigeres på siden Designdiagrammer. Ændres en værdi,
dannes opslagstabellen på ny, og både dimensioneringen og
Eo_ækv-matricen følger med.
