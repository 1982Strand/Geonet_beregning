# Kontrol af diagramaflæsninger

Dato: 24. september 2026.

## Resultat og afrunding

Alle **176 markerede kurvepunkter** er identificeret og aflæst i de seks diagrambilleder samt krydstjekket mod designmanualens side 10. Ingen markører er ulæselige. **22 lave punkter** er markeret med **†**, fordi aflæsningsusikkerheden er stor i forhold til deres værdi.

Der vises nu **ét Eᵤ-tal pr. kurve og bærelagstykkelse**, afrundet til nærmeste **0,5 MPa**. Afrundingen tager udgangspunkt i PNG-aflæsningen fra den første kontrol. PDF'en er brugt som krydstjek. Hele værdier skrives uden decimal, fx 30, 21 og 6; halve værdier skrives fx 14,5. Bærelagstykkelserne er uændrede.

**Krydstjek:** Ingen store afvigelser mellem billeder og PDF. Ingen af de kontrollerede forskelle overstiger 0,5 MPa før afrunding. Små forskelle omkring en afrundingsgrænse ændrer ikke valget af PNG-aflæsningen som grundlag.

## Kilder og læsevejledning

- Primære kilder: `Diagram 1.png` til `Diagram 6.png` i denne mappe.
- Krydstjek: [brochure-tensar-designmanual-sept-2024-1.pdf](<../Dokumenter%20og%20data/datablade%20og%20designmanualer/brochure-tensar-designmanual-sept-2024-1.pdf>), PDF-side 10, trykt side 10. Diagrammerne er her angivet som baseret på TriAx TX160.
- **h** er bærelagstykkelse i **cm**. **Eᵤ** er bundmodul i **MPa**, hvor **1 MPa = 1 MN/m²**. E₀ i overskrifterne er modulet på oversiden af bærelaget.
- **Ustabiliseret** svarer til kurven **Uarmeret** i kilderne. **1 lag net**, **2 lag net** og **Flere lag net** følger diagrammernes kurver. Flere lag i diagram 5 og 6 betyder ikke nødvendigvis præcis to lag.
- Alle Eᵤ-værdier er omtrentlige. Afrunding til 0,5 MPa ændrer ikke den praktiske aflæsningsmargin på omkring **±0,5 MPa** og dokumenterer ikke de eksakte oprindelige grundtal.
- **†** markerer de lave punkter fra første kontrol, hvor mindst én kildeaflæsning var højst 2 MPa før afrunding. Markeringen er bevaret efter afrunding.
- **—** i de første seks tabeller betyder, at der ikke er en markeret værdi for kurven ved den pågældende tykkelse. Det betyder ikke nul.

### Fremgangsmåde

Alle seks billeder og manualsiden er gennemgået visuelt. Markørernes centre er aflæst i forhold til de tilstødende gitterlinjer. PDF-krydstjekket anvender PDF'ens grafiske markørpositioner og egne gitterlinjer. De aflæste PNG-værdier fra første kontrol er herefter afrundet til nærmeste 0,5 MPa. Afsnittet »Tabeller med Eᵤ fra 1 til 45 MPa« omstiller alene disse afrundede punkter fra h → Eᵤ til Eᵤ → h uden mellemværdier. Det efterfølgende afsnit »Interpolerede tabeller med hele Eᵤ-trin« tilføjer de beregnede mellemværdier.

### Oversigt over markører

| Diagram          | E₀ (MPa) | Ustabiliseret |    1 lag net | 2 lag / Flere lag net |         I alt |     Heraf † |
| ---------------- | --------: | ------------: | -----------: | --------------------: | ------------: | -----------: |
| 1                |        30 |            12 |            8 |                    — |            20 |            2 |
| 2                |        45 |            14 |            9 |                     5 |            28 |            4 |
| 3                |        60 |            14 |           10 |                     6 |            30 |            4 |
| 4                |        80 |            14 |           11 |                     6 |            31 |            4 |
| 5                |       120 |            14 |           11 |                     8 |            33 |            4 |
| 6                |       150 |            14 |           11 |                     9 |            34 |            4 |
| **Samlet** |           |  **82** | **60** |          **34** | **176** | **22** |

## Diagram 1 - E₀ = 30 MPa, belastningsklasse 1

Kilde: [Diagram 1.png](<Diagram%201.png>). **20 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net |
| -----: | ------------: | --------: |
|      0 |            30 |        — |
|     10 |            25 |        — |
|     20 |            21 |        15 |
|     30 |            18 |      11,5 |
|     40 |          14,5 |         9 |
|     50 |            12 |       6,5 |
|     60 |            10 |         5 |
|     70 |             8 |         3 |
|     80 |             6 |      2 † |
|     90 |             5 |      0 † |
|    100 |           3,5 |        — |
|    110 |             3 |        — |

**Bemærkninger:** Ustabiliseret har lilla firkanter, og 1 lag net har blå ruder. Der er ingen kurve for 2 lag net. Sidste ustabiliserede punkt er ved 110 cm. Ved 1 lag net og h = 90 cm afrundes den lave aflæsning til **0 MPa †**. Det er en afrunding af en markør næsten på nulaksen og dokumenterer ikke et eksakt fysisk nulpunkt.

## Diagram 2 - E₀ = 45 MPa, belastningsklasse 2

Kilde: [Diagram 2.png](<Diagram%202.png>). **28 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net | 2 lag net |
| -----: | ------------: | --------: | --------: |
|      0 |            45 |        — |        — |
|     10 |            36 |        — |        — |
|     20 |            29 |        20 |        — |
|     30 |            23 |      15,5 |        — |
|     40 |          18,5 |        12 |        — |
|     50 |            15 |         9 |       6,5 |
|     60 |            12 |         6 |       4,5 |
|     70 |            10 |       4,5 |         3 |
|     80 |             8 |         3 |      2 † |
|     90 |             6 |      2 † |      1 † |
|    100 |             5 |      1 † |        — |
|    110 |           3,5 |        — |        — |
|    120 |             3 |        — |        — |
|    130 |           2,5 |        — |        — |

**Bemærkninger:** 2 lag net har fem markører, fra h = 50 til 90 cm. Sidste punkt for 1 lag net er ved 100 cm, og sidste ustabiliserede punkt er ved 130 cm.

## Diagram 3 - E₀ = 60 MPa, belastningsklasse 3

Kilde: [Diagram 3.png](<Diagram%203.png>). **30 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net | 2 lag net |
| -----: | ------------: | --------: | --------: |
|     10 |            45 |        — |        — |
|     20 |            36 |        27 |        — |
|     30 |            29 |        20 |        — |
|     40 |            23 |        16 |        — |
|     50 |          18,5 |        12 |         9 |
|     60 |            15 |         9 |       6,5 |
|     70 |            12 |       6,5 |       4,5 |
|     80 |            10 |       4,5 |       2,5 |
|     90 |             8 |         3 |    1,5 † |
|    100 |             6 |    1,5 † |      1 † |
|    110 |             5 |      1 † |        — |
|    120 |           3,5 |        — |        — |
|    130 |             3 |        — |        — |
|    140 |           2,5 |        — |        — |

**Bemærkninger:** X-aksen starter ved 10 cm. 1 lag net starter ved 20 cm; 2 lag net starter ved 50 cm. De lave punkter ved 1 lag net, h = 100 og 110 cm, og 2 lag net, h = 90 og 100 cm, er markeret med †. Sidste ustabiliserede punkt er ved 140 cm.

## Diagram 4 - E₀ = 80 MPa, belastningsklasse 4

Kilde: [Diagram 4.png](<Diagram%204.png>). **31 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net | 2 lag net |
| -----: | ------------: | --------: | --------: |
|     20 |            45 |        33 |        — |
|     30 |            36 |        26 |        — |
|     40 |            29 |        20 |        — |
|     50 |            23 |        14 |        — |
|     60 |          18,5 |      10,5 |         8 |
|     70 |            15 |       7,5 |       5,5 |
|     80 |            12 |       5,5 |         4 |
|     90 |            10 |         4 |         3 |
|    100 |             8 |         3 |      2 † |
|    110 |             6 |      2 † |      1 † |
|    120 |             5 |      1 † |        — |
|    130 |           3,5 |        — |        — |
|    140 |             3 |        — |        — |
|    150 |           2,5 |        — |        — |

**Bemærkninger:** X-aksen starter ved 20 cm. 2 lag net går fra h = 60 til 110 cm. Sidste punkt for 1 lag net er ved 120 cm, og sidste ustabiliserede punkt er ved 150 cm.

## Diagram 5 - E₀ = 120 MPa, belastningsklasse 5

Kilde: [Diagram 5.png](<Diagram%205.png>). **33 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net | Flere lag net |
| -----: | ------------: | --------: | ------------: |
|     30 |            45 |        33 |            — |
|     40 |            36 |        25 |            — |
|     50 |            29 |        19 |            14 |
|     60 |            23 |      13,5 |            10 |
|     70 |          18,5 |       9,5 |             8 |
|     80 |            15 |         8 |             6 |
|     90 |            12 |       5,5 |             4 |
|    100 |            10 |         4 |             3 |
|    110 |           8,5 |       2,5 |          2 † |
|    120 |             6 |      2 † |          1 † |
|    130 |             5 |      1 † |            — |
|    140 |           3,5 |        — |            — |
|    150 |             3 |        — |            — |
|    160 |           2,5 |        — |            — |

**Bemærkninger:** X-aksen starter ved 30 cm. Diagrammets lilla kurve hedder **Flere lag** og kan ikke ud fra signaturforklaringen alene betegnes som præcis 2 lag. Den går fra h = 50 til 120 cm. Sidste ustabiliserede punkt er ved 160 cm.

## Diagram 6 - E₀ = 150 MPa, belastningsklasse 6

Kilde: [Diagram 6.png](<Diagram%206.png>). **34 markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.

| h (cm) | Ustabiliseret | 1 lag net | Flere lag net |
| -----: | ------------: | --------: | ------------: |
|     40 |            45 |        32 |            — |
|     50 |            36 |        24 |            18 |
|     60 |            29 |        17 |            12 |
|     70 |            23 |        12 |             9 |
|     80 |          18,5 |       8,5 |           6,5 |
|     90 |            15 |         6 |           4,5 |
|    100 |            12 |       4,5 |             3 |
|    110 |            10 |       3,5 |           2,5 |
|    120 |             8 |       2,5 |        1,5 † |
|    130 |             6 |    1,5 † |        0,5 † |
|    140 |             5 |      1 † |            — |
|    150 |           3,5 |        — |            — |
|    160 |             3 |        — |            — |
|    170 |           2,5 |        — |            — |

**Bemærkninger:** X-aksen starter ved 40 cm. Diagrammets lilla kurve hedder **Flere lag** og går fra h = 50 til 130 cm. Sidste punkt på denne kurve afrundes til **0,5 MPa †** og ligger meget tæt på nul. Sidste ustabiliserede punkt er ved 170 cm.

## Tabeller med Eᵤ fra 1 til 45 MPa

Første kolonne viser **Eᵤ = 1, 2, 3, …, 45 MPa**, ligesom opstillingen med hele Eᵤ-trin i [geonet_interpolerede_diagrammer.xlsx](geonet_interpolerede_diagrammer.xlsx). Alle seks tabeller har samtlige 45 rækker, også hvor diagrammets kurver ikke når den pågældende værdi.

De øvrige kolonner viser **bærelagstykkelse h i cm**. En celle er kun udfyldt, hvis et afrundet, markeret punkt i tabellerne ovenfor har netop den pågældende hele Eᵤ-værdi. Øvrige celler er tomme. Der er ikke interpoleret, ekstrapoleret eller kopieret tykkelsesværdier fra Excel-filen.

Punkter med halve Eᵤ-værdier, fx 14,5 MPa, står fortsat i tabellerne ovenfor. De er ikke flyttet til en hel Eᵤ-række. Det samme gælder punkter under 1 MPa, som ligger uden for dette afsnits interval. **†** følger punktet og angiver usikkerheden i Eᵤ-aflæsningen, selv om cellen her viser h.

### Diagram 1 - E₀ = 30 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) |
| --------: | ---------------------: | -----------------: |
|         1 |                        |                    |
|         2 |                        |              80 † |
|         3 |                    110 |                 70 |
|         4 |                        |                    |
|         5 |                     90 |                 60 |
|         6 |                     80 |                    |
|         7 |                        |                    |
|         8 |                     70 |                    |
|         9 |                        |                 40 |
|        10 |                     60 |                    |
|        11 |                        |                    |
|        12 |                     50 |                    |
|        13 |                        |                    |
|        14 |                        |                    |
|        15 |                        |                 20 |
|        16 |                        |                    |
|        17 |                        |                    |
|        18 |                     30 |                    |
|        19 |                        |                    |
|        20 |                        |                    |
|        21 |                     20 |                    |
|        22 |                        |                    |
|        23 |                        |                    |
|        24 |                        |                    |
|        25 |                     10 |                    |
|        26 |                        |                    |
|        27 |                        |                    |
|        28 |                        |                    |
|        29 |                        |                    |
|        30 |                      0 |                    |
|        31 |                        |                    |
|        32 |                        |                    |
|        33 |                        |                    |
|        34 |                        |                    |
|        35 |                        |                    |
|        36 |                        |                    |
|        37 |                        |                    |
|        38 |                        |                    |
|        39 |                        |                    |
|        40 |                        |                    |
|        41 |                        |                    |
|        42 |                        |                    |
|        43 |                        |                    |
|        44 |                        |                    |
|        45 |                        |                    |

### Diagram 2 - E₀ = 45 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |             100 † |              90 † |
|         2 |                        |              90 † |              80 † |
|         3 |                    120 |                 80 |                 70 |
|         4 |                        |                    |                    |
|         5 |                    100 |                    |                    |
|         6 |                     90 |                 60 |                    |
|         7 |                        |                    |                    |
|         8 |                     80 |                    |                    |
|         9 |                        |                 50 |                    |
|        10 |                     70 |                    |                    |
|        11 |                        |                    |                    |
|        12 |                     60 |                 40 |                    |
|        13 |                        |                    |                    |
|        14 |                        |                    |                    |
|        15 |                     50 |                    |                    |
|        16 |                        |                    |                    |
|        17 |                        |                    |                    |
|        18 |                        |                    |                    |
|        19 |                        |                    |                    |
|        20 |                        |                 20 |                    |
|        21 |                        |                    |                    |
|        22 |                        |                    |                    |
|        23 |                     30 |                    |                    |
|        24 |                        |                    |                    |
|        25 |                        |                    |                    |
|        26 |                        |                    |                    |
|        27 |                        |                    |                    |
|        28 |                        |                    |                    |
|        29 |                     20 |                    |                    |
|        30 |                        |                    |                    |
|        31 |                        |                    |                    |
|        32 |                        |                    |                    |
|        33 |                        |                    |                    |
|        34 |                        |                    |                    |
|        35 |                        |                    |                    |
|        36 |                     10 |                    |                    |
|        37 |                        |                    |                    |
|        38 |                        |                    |                    |
|        39 |                        |                    |                    |
|        40 |                        |                    |                    |
|        41 |                        |                    |                    |
|        42 |                        |                    |                    |
|        43 |                        |                    |                    |
|        44 |                        |                    |                    |
|        45 |                      0 |                    |                    |

### Diagram 3 - E₀ = 60 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |             110 † |             100 † |
|         2 |                        |                    |                    |
|         3 |                    130 |                 90 |                    |
|         4 |                        |                    |                    |
|         5 |                    110 |                    |                    |
|         6 |                    100 |                    |                    |
|         7 |                        |                    |                    |
|         8 |                     90 |                    |                    |
|         9 |                        |                 60 |                 50 |
|        10 |                     80 |                    |                    |
|        11 |                        |                    |                    |
|        12 |                     70 |                 50 |                    |
|        13 |                        |                    |                    |
|        14 |                        |                    |                    |
|        15 |                     60 |                    |                    |
|        16 |                        |                 40 |                    |
|        17 |                        |                    |                    |
|        18 |                        |                    |                    |
|        19 |                        |                    |                    |
|        20 |                        |                 30 |                    |
|        21 |                        |                    |                    |
|        22 |                        |                    |                    |
|        23 |                     40 |                    |                    |
|        24 |                        |                    |                    |
|        25 |                        |                    |                    |
|        26 |                        |                    |                    |
|        27 |                        |                 20 |                    |
|        28 |                        |                    |                    |
|        29 |                     30 |                    |                    |
|        30 |                        |                    |                    |
|        31 |                        |                    |                    |
|        32 |                        |                    |                    |
|        33 |                        |                    |                    |
|        34 |                        |                    |                    |
|        35 |                        |                    |                    |
|        36 |                     20 |                    |                    |
|        37 |                        |                    |                    |
|        38 |                        |                    |                    |
|        39 |                        |                    |                    |
|        40 |                        |                    |                    |
|        41 |                        |                    |                    |
|        42 |                        |                    |                    |
|        43 |                        |                    |                    |
|        44 |                        |                    |                    |
|        45 |                     10 |                    |                    |

### Diagram 4 - E₀ = 80 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |             120 † |             110 † |
|         2 |                        |             110 † |             100 † |
|         3 |                    140 |                100 |                 90 |
|         4 |                        |                 90 |                 80 |
|         5 |                    120 |                    |                    |
|         6 |                    110 |                    |                    |
|         7 |                        |                    |                    |
|         8 |                    100 |                    |                 60 |
|         9 |                        |                    |                    |
|        10 |                     90 |                    |                    |
|        11 |                        |                    |                    |
|        12 |                     80 |                    |                    |
|        13 |                        |                    |                    |
|        14 |                        |                 50 |                    |
|        15 |                     70 |                    |                    |
|        16 |                        |                    |                    |
|        17 |                        |                    |                    |
|        18 |                        |                    |                    |
|        19 |                        |                    |                    |
|        20 |                        |                 40 |                    |
|        21 |                        |                    |                    |
|        22 |                        |                    |                    |
|        23 |                     50 |                    |                    |
|        24 |                        |                    |                    |
|        25 |                        |                    |                    |
|        26 |                        |                 30 |                    |
|        27 |                        |                    |                    |
|        28 |                        |                    |                    |
|        29 |                     40 |                    |                    |
|        30 |                        |                    |                    |
|        31 |                        |                    |                    |
|        32 |                        |                    |                    |
|        33 |                        |                 20 |                    |
|        34 |                        |                    |                    |
|        35 |                        |                    |                    |
|        36 |                     30 |                    |                    |
|        37 |                        |                    |                    |
|        38 |                        |                    |                    |
|        39 |                        |                    |                    |
|        40 |                        |                    |                    |
|        41 |                        |                    |                    |
|        42 |                        |                    |                    |
|        43 |                        |                    |                    |
|        44 |                        |                    |                    |
|        45 |                     20 |                    |                    |

### Diagram 5 - E₀ = 120 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | Flere lag net - h (cm) |
| --------: | ---------------------: | -----------------: | ---------------------: |
|         1 |                        |             130 † |                 120 † |
|         2 |                        |             120 † |                 110 † |
|         3 |                    150 |                    |                    100 |
|         4 |                        |                100 |                     90 |
|         5 |                    130 |                    |                        |
|         6 |                    120 |                    |                     80 |
|         7 |                        |                    |                        |
|         8 |                        |                 80 |                     70 |
|         9 |                        |                    |                        |
|        10 |                    100 |                    |                     60 |
|        11 |                        |                    |                        |
|        12 |                     90 |                    |                        |
|        13 |                        |                    |                        |
|        14 |                        |                    |                     50 |
|        15 |                     80 |                    |                        |
|        16 |                        |                    |                        |
|        17 |                        |                    |                        |
|        18 |                        |                    |                        |
|        19 |                        |                 50 |                        |
|        20 |                        |                    |                        |
|        21 |                        |                    |                        |
|        22 |                        |                    |                        |
|        23 |                     60 |                    |                        |
|        24 |                        |                    |                        |
|        25 |                        |                 40 |                        |
|        26 |                        |                    |                        |
|        27 |                        |                    |                        |
|        28 |                        |                    |                        |
|        29 |                     50 |                    |                        |
|        30 |                        |                    |                        |
|        31 |                        |                    |                        |
|        32 |                        |                    |                        |
|        33 |                        |                 30 |                        |
|        34 |                        |                    |                        |
|        35 |                        |                    |                        |
|        36 |                     40 |                    |                        |
|        37 |                        |                    |                        |
|        38 |                        |                    |                        |
|        39 |                        |                    |                        |
|        40 |                        |                    |                        |
|        41 |                        |                    |                        |
|        42 |                        |                    |                        |
|        43 |                        |                    |                        |
|        44 |                        |                    |                        |
|        45 |                     30 |                    |                        |

### Diagram 6 - E₀ = 150 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | Flere lag net - h (cm) |
| --------: | ---------------------: | -----------------: | ---------------------: |
|         1 |                        |             140 † |                        |
|         2 |                        |                    |                        |
|         3 |                    160 |                    |                    100 |
|         4 |                        |                    |                        |
|         5 |                    140 |                    |                        |
|         6 |                    130 |                 90 |                        |
|         7 |                        |                    |                        |
|         8 |                    120 |                    |                        |
|         9 |                        |                    |                     70 |
|        10 |                    110 |                    |                        |
|        11 |                        |                    |                        |
|        12 |                    100 |                 70 |                     60 |
|        13 |                        |                    |                        |
|        14 |                        |                    |                        |
|        15 |                     90 |                    |                        |
|        16 |                        |                    |                        |
|        17 |                        |                 60 |                        |
|        18 |                        |                    |                     50 |
|        19 |                        |                    |                        |
|        20 |                        |                    |                        |
|        21 |                        |                    |                        |
|        22 |                        |                    |                        |
|        23 |                     70 |                    |                        |
|        24 |                        |                 50 |                        |
|        25 |                        |                    |                        |
|        26 |                        |                    |                        |
|        27 |                        |                    |                        |
|        28 |                        |                    |                        |
|        29 |                     60 |                    |                        |
|        30 |                        |                    |                        |
|        31 |                        |                    |                        |
|        32 |                        |                 40 |                        |
|        33 |                        |                    |                        |
|        34 |                        |                    |                        |
|        35 |                        |                    |                        |
|        36 |                     50 |                    |                        |
|        37 |                        |                    |                        |
|        38 |                        |                    |                        |
|        39 |                        |                    |                        |
|        40 |                        |                    |                        |
|        41 |                        |                    |                        |
|        42 |                        |                    |                        |
|        43 |                        |                    |                        |
|        44 |                        |                    |                        |
|        45 |                     40 |                    |                        |

## Interpolerede tabeller med hele Eᵤ-trin

Dette afsnit indeholder de beregnede tykkelser for **Eᵤ = 1–30 MPa i diagram 1** og **Eᵤ = 1–45 MPa i diagram 2–6**, i trin på **1 MPa**. Alle tykkelser h angives i **cm med præcis én decimal**.

### Beregningsgrundlag

- Grundlaget er de 176 markerede punkter i de første seks tabeller, hvor Eᵤ er afrundet til nærmeste 0,5 MPa. De halve Eᵤ-værdier indgår som støttepunkter i beregningen.
- Hver kurve behandles særskilt. Ved et eksisterende støttepunkt bruges dets tykkelse direkte. Mellem to tilstødende støttepunkter anvendes **stykkevis lineær interpolation**.
- For støttepunkterne (Eᵤ₁, h₁) og (Eᵤ₂, h₂) beregnes: **h = h₁ + (h₂ − h₁) × (Eᵤ − Eᵤ₁) / (Eᵤ₂ − Eᵤ₁)**.
- Der afrundes først til én decimal efter beregningen. Der ekstrapoleres ikke. En tom celle betyder, at Eᵤ ligger uden for den pågældende kurves aflæste område; den betyder ikke nul tykkelse.
- **†** betyder, at resultatet enten kommer direkte fra et usikkert støttepunkt eller er interpoleret med mindst ét usikkert støttepunkt. Markeringen vedrører grundlagets Eᵤ-aflæsning, ikke en særskilt måling af tykkelsen.
- Én decimal er beregningens visningspræcision. Den giver ikke diagramaflæsningen en større nøjagtighed.

**Særligt om diagram 1:** Ved Eᵤ = 1 MPa bliver tykkelsen for 1 lag net **85,0 cm †**. Beregningen bruger støttepunktet ved h = 90 cm, som er afrundet til Eᵤ = 0 MPa, samt punktet ved h = 80 cm og Eᵤ = 2 MPa. Resultatet afhænger derfor af det usikre endepunkt og er ikke en selvstændig sikker aflæsning.

### Interpoleret diagram 1 - E₀ = 30 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) |
| --------: | ---------------------: | -----------------: |
|         1 |                        |            85,0 † |
|         2 |                        |            80,0 † |
|         3 |                  110,0 |               70,0 |
|         4 |                    100 |               65,0 |
|         5 |                   90,0 |               60,0 |
|         6 |                   80,0 |               53,3 |
|         7 |                   75,0 |               48,0 |
|         8 |                   70,0 |               44,0 |
|         9 |                   65,0 |               40,0 |
|        10 |                   60,0 |               36,0 |
|        11 |                   55,0 |               32,0 |
|        12 |                   50,0 |               28,6 |
|        13 |                   46,0 |               25,7 |
|        14 |                   42,0 |               22,9 |
|        15 |                   38,6 |               20,0 |
|        16 |                   35,7 |                    |
|        17 |                   32,9 |                    |
|        18 |                   30,0 |                    |
|        19 |                   26,7 |                    |
|        20 |                   23,3 |                    |
|        21 |                   20,0 |                    |
|        22 |                   17,5 |                    |
|        23 |                   15,0 |                    |
|        24 |                   12,5 |                    |
|        25 |                   10,0 |                    |
|        26 |                    8,0 |                    |
|        27 |                    6,0 |                    |
|        28 |                    4,0 |                    |
|        29 |                    2,0 |                    |
|        30 |                    0,0 |                    |

### Interpoleret diagram 2 - E₀ = 45 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |           100,0 † |            90,0 † |
|         2 |                        |            90,0 † |            80,0 † |
|         3 |                  120,0 |               80,0 |               70,0 |
|         4 |                  106,7 |               73,3 |               63,3 |
|         5 |                  100,0 |               66,7 |               57,5 |
|         6 |                   90,0 |               60,0 |               52,5 |
|         7 |                   85,0 |               56,7 |                    |
|         8 |                   80,0 |               53,3 |                    |
|         9 |                   75,0 |               50,0 |                    |
|        10 |                   70,0 |               46,7 |                    |
|        11 |                   65,0 |               43,3 |                    |
|        12 |                   60,0 |               40,0 |                    |
|        13 |                   56,7 |               37,1 |                    |
|        14 |                   53,3 |               34,3 |                    |
|        15 |                   50,0 |               31,4 |                    |
|        16 |                   47,1 |               28,9 |                    |
|        17 |                   44,3 |               26,7 |                    |
|        18 |                   41,4 |               24,4 |                    |
|        19 |                   38,9 |               22,2 |                    |
|        20 |                   36,7 |               20,0 |                    |
|        21 |                   34,4 |                    |                    |
|        22 |                   32,2 |                    |                    |
|        23 |                   30,0 |                    |                    |
|        24 |                   28,3 |                    |                    |
|        25 |                   26,7 |                    |                    |
|        26 |                   25,0 |                    |                    |
|        27 |                   23,3 |                    |                    |
|        28 |                   21,7 |                    |                    |
|        29 |                   20,0 |                    |                    |
|        30 |                   18,6 |                    |                    |
|        31 |                   17,1 |                    |                    |
|        32 |                   15,7 |                    |                    |
|        33 |                   14,3 |                    |                    |
|        34 |                   12,9 |                    |                    |
|        35 |                   11,4 |                    |                    |
|        36 |                   10,0 |                    |                    |
|        37 |                    8,9 |                    |                    |
|        38 |                    7,8 |                    |                    |
|        39 |                    6,7 |                    |                    |
|        40 |                    5,6 |                    |                    |
|        41 |                    4,4 |                    |                    |
|        42 |                    3,3 |                    |                    |
|        43 |                    2,2 |                    |                    |
|        44 |                    1,1 |                    |                    |
|        45 |                    0,0 |                    |                    |

### Interpoleret diagram 3 - E₀ = 60 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |           110,0 † |           100,0 † |
|         2 |                        |            96,7 † |            85,0 † |
|         3 |                  130,0 |               90,0 |               77,5 |
|         4 |                  116,7 |               83,3 |               72,5 |
|         5 |                  110,0 |               77,5 |               67,5 |
|         6 |                  100,0 |               72,5 |               62,5 |
|         7 |                   95,0 |               68,0 |               58,0 |
|         8 |                   90,0 |               64,0 |               54,0 |
|         9 |                   85,0 |               60,0 |               50,0 |
|        10 |                   80,0 |               56,7 |                    |
|        11 |                   75,0 |               53,3 |                    |
|        12 |                   70,0 |               50,0 |                    |
|        13 |                   66,7 |               47,5 |                    |
|        14 |                   63,3 |               45,0 |                    |
|        15 |                   60,0 |               42,5 |                    |
|        16 |                   57,1 |               40,0 |                    |
|        17 |                   54,3 |               37,5 |                    |
|        18 |                   51,4 |               35,0 |                    |
|        19 |                   48,9 |               32,5 |                    |
|        20 |                   46,7 |               30,0 |                    |
|        21 |                   44,4 |               28,6 |                    |
|        22 |                   42,2 |               27,1 |                    |
|        23 |                   40,0 |               25,7 |                    |
|        24 |                   38,3 |               24,3 |                    |
|        25 |                   36,7 |               22,9 |                    |
|        26 |                   35,0 |               21,4 |                    |
|        27 |                   33,3 |               20,0 |                    |
|        28 |                   31,7 |                    |                    |
|        29 |                   30,0 |                    |                    |
|        30 |                   28,6 |                    |                    |
|        31 |                   27,1 |                    |                    |
|        32 |                   25,7 |                    |                    |
|        33 |                   24,3 |                    |                    |
|        34 |                   22,9 |                    |                    |
|        35 |                   21,4 |                    |                    |
|        36 |                   20,0 |                    |                    |
|        37 |                   18,9 |                    |                    |
|        38 |                   17,8 |                    |                    |
|        39 |                   16,7 |                    |                    |
|        40 |                   15,6 |                    |                    |
|        41 |                   14,4 |                    |                    |
|        42 |                   13,3 |                    |                    |
|        43 |                   12,2 |                    |                    |
|        44 |                   11,1 |                    |                    |
|        45 |                   10,0 |                    |                    |

### Interpoleret diagram 4 - E₀ = 80 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | 2 lag net - h (cm) |
| --------: | ---------------------: | -----------------: | -----------------: |
|         1 |                        |           120,0 † |           110,0 † |
|         2 |                        |           110,0 † |           100,0 † |
|         3 |                  140,0 |              100,0 |               90,0 |
|         4 |                  126,7 |               90,0 |               80,0 |
|         5 |                  120,0 |               83,3 |               73,3 |
|         6 |                  110,0 |               77,5 |               68,0 |
|         7 |                  105,0 |               72,5 |               64,0 |
|         8 |                  100,0 |               68,3 |               60,0 |
|         9 |                   95,0 |               65,0 |                    |
|        10 |                   90,0 |               61,7 |                    |
|        11 |                   85,0 |               58,6 |                    |
|        12 |                   80,0 |               55,7 |                    |
|        13 |                   76,7 |               52,9 |                    |
|        14 |                   73,3 |               50,0 |                    |
|        15 |                   70,0 |               48,3 |                    |
|        16 |                   67,1 |               46,7 |                    |
|        17 |                   64,3 |               45,0 |                    |
|        18 |                   61,4 |               43,3 |                    |
|        19 |                   58,9 |               41,7 |                    |
|        20 |                   56,7 |               40,0 |                    |
|        21 |                   54,4 |               38,3 |                    |
|        22 |                   52,2 |               36,7 |                    |
|        23 |                   50,0 |               35,0 |                    |
|        24 |                   48,3 |               33,3 |                    |
|        25 |                   46,7 |               31,7 |                    |
|        26 |                   45,0 |               30,0 |                    |
|        27 |                   43,3 |               28,6 |                    |
|        28 |                   41,7 |               27,1 |                    |
|        29 |                   40,0 |               25,7 |                    |
|        30 |                   38,6 |               24,3 |                    |
|        31 |                   37,1 |               22,9 |                    |
|        32 |                   35,7 |               21,4 |                    |
|        33 |                   34,3 |               20,0 |                    |
|        34 |                   32,9 |                    |                    |
|        35 |                   31,4 |                    |                    |
|        36 |                   30,0 |                    |                    |
|        37 |                   28,9 |                    |                    |
|        38 |                   27,8 |                    |                    |
|        39 |                   26,7 |                    |                    |
|        40 |                   25,6 |                    |                    |
|        41 |                   24,4 |                    |                    |
|        42 |                   23,3 |                    |                    |
|        43 |                   22,2 |                    |                    |
|        44 |                   21,1 |                    |                    |
|        45 |                   20,0 |                    |                    |

### Interpoleret diagram 5 - E₀ = 120 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | Flere lag net - h (cm) |
| --------: | ---------------------: | -----------------: | ---------------------: |
|         1 |                        |           130,0 † |               120,0 † |
|         2 |                        |           120,0 † |               110,0 † |
|         3 |                  150,0 |              106,7 |                  100,0 |
|         4 |                  136,7 |              100,0 |                   90,0 |
|         5 |                  130,0 |               93,3 |                   85,0 |
|         6 |                  120,0 |               88,0 |                   80,0 |
|         7 |                  116,0 |               84,0 |                   75,0 |
|         8 |                  112,0 |               80,0 |                   70,0 |
|         9 |                  106,7 |               73,3 |                   65,0 |
|        10 |                  100,0 |               68,8 |                   60,0 |
|        11 |                   95,0 |               66,3 |                   57,5 |
|        12 |                   90,0 |               63,8 |                   55,0 |
|        13 |                   86,7 |               61,3 |                   52,5 |
|        14 |                   83,3 |               59,1 |                   50,0 |
|        15 |                   80,0 |               57,3 |                        |
|        16 |                   77,1 |               55,5 |                        |
|        17 |                   74,3 |               53,6 |                        |
|        18 |                   71,4 |               51,8 |                        |
|        19 |                   68,9 |               50,0 |                        |
|        20 |                   66,7 |               48,3 |                        |
|        21 |                   64,4 |               46,7 |                        |
|        22 |                   62,2 |               45,0 |                        |
|        23 |                   60,0 |               43,3 |                        |
|        24 |                   58,3 |               41,7 |                        |
|        25 |                   56,7 |               40,0 |                        |
|        26 |                   55,0 |               38,8 |                        |
|        27 |                   53,3 |               37,5 |                        |
|        28 |                   51,7 |               36,3 |                        |
|        29 |                   50,0 |               35,0 |                        |
|        30 |                   48,6 |               33,8 |                        |
|        31 |                   47,1 |               32,5 |                        |
|        32 |                   45,7 |               31,3 |                        |
|        33 |                   44,3 |               30,0 |                        |
|        34 |                   42,9 |                    |                        |
|        35 |                   41,4 |                    |                        |
|        36 |                   40,0 |                    |                        |
|        37 |                   38,9 |                    |                        |
|        38 |                   37,8 |                    |                        |
|        39 |                   36,7 |                    |                        |
|        40 |                   35,6 |                    |                        |
|        41 |                   34,4 |                    |                        |
|        42 |                   33,3 |                    |                        |
|        43 |                   32,2 |                    |                        |
|        44 |                   31,1 |                    |                        |
|        45 |                   30,0 |                    |                        |

### Interpoleret diagram 6 - E₀ = 150 MPa

| Eᵤ (MPa) | Ustabiliseret - h (cm) | 1 lag net - h (cm) | Flere lag net - h (cm) |
| --------: | ---------------------: | -----------------: | ---------------------: |
|         1 |                        |           140,0 † |               125,0 † |
|         2 |                        |           125,0 † |               115,0 † |
|         3 |                  160,0 |              115,0 |                  100,0 |
|         4 |                  146,7 |              105,0 |                   93,3 |
|         5 |                  140,0 |               96,7 |                   87,5 |
|         6 |                  130,0 |               90,0 |                   82,5 |
|         7 |                  125,0 |               86,0 |                   78,0 |
|         8 |                  120,0 |               82,0 |                   74,0 |
|         9 |                  115,0 |               78,6 |                   70,0 |
|        10 |                  110,0 |               75,7 |                   66,7 |
|        11 |                  105,0 |               72,9 |                   63,3 |
|        12 |                  100,0 |               70,0 |                   60,0 |
|        13 |                   96,7 |               68,0 |                   58,3 |
|        14 |                   93,3 |               66,0 |                   56,7 |
|        15 |                   90,0 |               64,0 |                   55,0 |
|        16 |                   87,1 |               62,0 |                   53,3 |
|        17 |                   84,3 |               60,0 |                   51,7 |
|        18 |                   81,4 |               58,6 |                   50,0 |
|        19 |                   78,9 |               57,1 |                        |
|        20 |                   76,7 |               55,7 |                        |
|        21 |                   74,4 |               54,3 |                        |
|        22 |                   72,2 |               52,9 |                        |
|        23 |                   70,0 |               51,4 |                        |
|        24 |                   68,3 |               50,0 |                        |
|        25 |                   66,7 |               48,8 |                        |
|        26 |                   65,0 |               47,5 |                        |
|        27 |                   63,3 |               46,3 |                        |
|        28 |                   61,7 |               45,0 |                        |
|        29 |                   60,0 |               43,8 |                        |
|        30 |                   58,6 |               42,5 |                        |
|        31 |                   57,1 |               41,3 |                        |
|        32 |                   55,7 |               40,0 |                        |
|        33 |                   54,3 |                    |                        |
|        34 |                   52,9 |                    |                        |
|        35 |                   51,4 |                    |                        |
|        36 |                   50,0 |                    |                        |
|        37 |                   48,9 |                    |                        |
|        38 |                   47,8 |                    |                        |
|        39 |                   46,7 |                    |                        |
|        40 |                   45,6 |                    |                        |
|        41 |                   44,4 |                    |                        |
|        42 |                   43,3 |                    |                        |
|        43 |                   42,2 |                    |                        |
|        44 |                   41,1 |                    |                        |
|        45 |                   40,0 |                    |                        |
