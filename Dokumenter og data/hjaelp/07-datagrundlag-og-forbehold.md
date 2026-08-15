---
titel: Datagrundlag og forbehold
resume: Forudsætningerne bag de 48 VejDim-kørsler, korrelationens gyldighedsområde, de seks forbehold og de tilfælde, hvor en konkret kørsel bør foretages.
---

## 1 Kørslernes forudsætninger

De 48 VejDim-kørsler omfatter T1–T6 ved Eu = 3, 4, 5, 10, 15, 20, 30 og
40 MPa. Samtlige kørsler er udført med:

- **Belastningsmodel:** Æ10 tvillingehjul, standard, ved 60–80 km/t.
- **Afvanding:** nej.
- **Underbund:** frostsikker, hvis E-modul er manuelt overskrevet til cellens
  Eu-værdi. Herved bortfalder koblingshøjdekravet, og kørslen bliver ren
  bæreevne.
- **Levetidsmål:** 20 år for alle lag.
- **Ubundne lag:** SG II med E = 300 over BL II U≤3 med E = 100, justeret af
  VejDim.
- **Asfalt-E:** standard, ikke overskrevet.

Asfaltpakken er fast pr. trafikklasse. Bundne bærelag er låst, hvor det er
muligt; hvor VejDim selv beregner tykkelsen, er programmets egne værdier
anvendt, og tykkelsen kan derfor variere med Eu.

## 2 Gyldighedsområde

Korrelationen er vejledende og gælder for opbygninger, der ligner kørslernes
forudsætninger. Afviger projektets underbund, trafikbelastning eller ønskede
levetid væsentligt, bør en konkret VejDim-beregning foretages frem for at
anvende korrelationstabellen.

Følgende forbehold gælder:

1. **VejDim omfatter ikke geonet.** Reduktionen hviler på feltforsøg fra
   GS-GRID og Tensar, ikke på vejreglen.
2. **MSL erstatter stabilgrus og bundsikring samlet.** Sammenligningen
   foretages på den samlede ubundne lagtykkelse. Materialekravet til MSL
   svarer til stabilgrus og er dermed strengere end kravet til bundsikring,
   hvilket er konservativt.
3. **Frostsikring og koblingshøjde er ikke omfattet.** Kørslerne er udført med
   frostsikker underbund. En geonet-reduceret opbygning bør ikke bringe
   totalhøjden under koblingshøjden for frostfarlig underbund, jf. håndbogens
   afsnit 5.3. Forholdet bør kontrolleres særskilt.
4. **Manglende armerede kurver i kernezonen.** I enkelte celler mangler
   diagrammet data for 1 lag geonet ved den ækvivalente Eo, idet kurven er tom
   ved høj Eo og tynd opbygning. Reduktionen kan da ikke bestemmes, selv om
   cellen ligger inden for kernezonen.
5. **Følsomhed over for asfaltpakken.** Den ækvivalente Eo afhænger af den
   faste asfaltpakke pr. trafikklasse. De anvendte pakker er VejDims egne
   værdier.
6. **Trafikklasse T7 er ikke medtaget**, idet klassen er åben. Der henvises til
   en konkret VejDim-beregning.

## 3 Hvornår en ny kørsel bør foretages

En konkret VejDim-beregning bør foretages, når mindst ét af følgende forhold
gør sig gældende:

- Afvanding er til stede eller udelukket i det konkrete projekt.
- Levetidsmålet afviger fra 20 år.
- Underbunden er ikke frostsikker.
- Trafikkens sammensætning afviger væsentligt fra Æ10-forudsætningen.
- Opslagspunktet falder i zonen under eller over, jf. kapitel 2, afsnit 2.

Foreligger en konkret kørsel, kan den indtastes i kørselstabellen på
korrelationssiden, hvorefter Eo_ækv-matricen og dimensioneringen følger med.
