from pathlib import Path
import json
ROOT=Path(r'C:\geonet_beregning')
data=json.loads((ROOT/'tmp/pdfs/codex-diagram-kontrol/checked-readings.json').read_text())
def fmt(x):return f'{x:.1f}'.replace('.',',')
def low(z):return min(z['png'],z['pdf'])<=2.0
counts=[sum(len(p) for p in d.values()) for d in data]
lows=[sum(low(z) for p in d.values() for z in p) for d in data]
text=f'''# Kontrol af diagramaflæsninger

Dato: 24. september 2026.

## Resultat og afgrænsning

**Alle {sum(counts)} markerede kurvepunkter kan identificeres i de seks PNG-billeder. Ingen markører er ulæselige.** Bærelagstykkelsen kan fastlægges ud fra gitteret for samtlige punkter. Bundmodulet kan aflæses omtrentligt. {sum(counts)-sum(lows)} punkter er almindeligt aflæselige; {sum(lows)} punkter tæt på nul er særskilt markeret med **†**, fordi usikkerheden udgør en stor del af deres lave værdi.

Alle 176 punkter er også sammenholdt med de tilsvarende markører i designmanualens **PDF-side 10, trykt side 10**. Der er overensstemmelse i kurveidentitet, antal punkter og tykkelsespositioner. De beregnede forskelle mellem markørernes grafiske Eᵤ-positioner er højst ca. **0,21 MN/m²**, hvilket ligger inden for den praktiske aflæsningsusikkerhed. Det er et krydstjek af to gengivelser af diagrammerne, ikke en uafhængig validering af deres dimensioneringsgrundlag.

Dette trin dokumenterer kildernes markerede punkter. Det omfatter ikke sammenligning med eksisterende regneark/programdata eller valg af interpolation mellem punkterne.

## Kilder og læsevejledning

- Primære kilder: `Diagram 1.png` til `Diagram 6.png` i denne mappe.
- Krydstjek: [brochure-tensar-designmanual-sept-2024-1.pdf](../Dokumenter%20og%20data/datablade%20og%20designmanualer/brochure-tensar-designmanual-sept-2024-1.pdf), side 10. Alle seks diagrammer er her angivet som baseret på TriAx TX160.
- Vandret akse: bærelagstykkelse **h i cm**. Hvert lodret gittertrin svarer til 10 cm, også hvor kun hvert andet trin har et tal.
- Lodret akse: bundmodul **Eᵤ i MN/m²**. Gittertrinene er 5 MN/m² i diagram 1 og 10 MN/m² i diagram 2-6.
- E₀ i diagramoverskriften er den pågældende belastningsklasses modul på oversiden af bærelaget; tabellernes kurveværdier er Eᵤ.
- Hver udfyldt celle viser **PNG / PDF**. Eksempel: `11,4 / 11,4` betyder omtrent 11,4 MN/m² i begge gengivelser. Skråstregen betyder ikke division eller et interval.
- **Alle Eᵤ-tal er omtrentlige**, også hvor der står `30,0` eller `10,0`. Én decimal gør små forskelle mellem gengivelserne synlige; den dokumenterer ikke en sikkerhed på 0,1 MN/m² eller originale numeriske grunddata.
- Som praktisk aflæsningsmargin bør regnes med omkring **±0,5 MN/m²**. Dette er et skøn ud fra gitter, stregtykkelse og markørstørrelse, ikke en statistisk beregnet usikkerhed. Den lille forskel mellem PNG og PDF ophæver ikke denne begrænsning.
- **†**: mindst én af de to aflæsninger er ≤ 2,0 MN/m² før afrunding. Punktet kan identificeres, men talværdien kræver særlig omtanke. Se bemærkningerne efter hvert diagram.
- **—**: ingen markeret værdi for den pågældende kurve ved denne tykkelse. Det betyder ikke nul.

### Fremgangsmåde

Alle seks billeder og manualsiden er gennemgået visuelt. Markørernes centre i PNG-billederne er derefter målt i forhold til de tilstødende vandrette gitterlinjer. Gitterlinjernes faktiske billedpositioner er brugt for at begrænse fejl fra skalering og afrunding til pixels. PDF-krydstjekket bruger markørernes grafiske vektorpositioner og PDF'ens egne gitterlinjer. Det er stadig en aflæsning af den tegnede grafik, ikke udtræk af en bagvedliggende datatabel. Forstørrede udsnit af diagram 1, 3 og 6 er desuden kontrolleret ved de lave værdier.

### Oversigt over markører

| Diagram | E₀ (MN/m²) | Uarmeret | 1 lag armering | 2 lag / Flere lag | I alt | Heraf † |
|---|---:|---:|---:|---:|---:|---:|
'''
E=[30,45,60,80,120,150]
for i,d in enumerate(data):
    text+=f"| {i+1} | {E[i]} | {len(d['purple' if i==0 else 'yellow'])} | {len(d['blue'])} | {'—' if i==0 else len(d['purple'])} | {counts[i]} | {lows[i]} |\n"
text+=f'| **Samlet** | | **82** | **60** | **34** | **176** | **{sum(lows)}** |\n'
notes=[
'''- Den uarmerede kurve har **lilla firkanter**; den blå kurve har **ruder** og betyder 1 lag armering. Der er ingen kurve for flere lag.
- Ved **h = 20 cm** er de to værdier ca. **21** og **15 MN/m²**. De må ikke forveksles.
- † ved **1 lag, h = 80 og 90 cm**. Punktet ved 90 cm ligger næsten på nulaksen; den grafiske placering svarer til ca. **0,2 MN/m²**. Billedmaterialet kan ikke afgøre sikkert, om det oprindelige grundtal var 0, en lille positiv værdi eller en afrundet værdi. Det bør ikke fastlåses som et eksakt nulpunkt.
- Sidste uarmerede punkt er ved **110 cm**, selv om sidste tal på x-aksen er 100.''',
'''- Uarmeret: gule trekanter. 1 lag: blå ruder. **2 lag armering**: lilla firkanter.
- Tolagskurven starter først ved **50 cm** og slutter ved **90 cm**. Den indeholder fem markører.
- † ved **1 lag, h = 90 og 100 cm**, og **2 lag, h = 80 og 90 cm**. Ved 90 cm på étlagskurven ses en lille forskel mellem gengivelserne omkring Eᵤ = 2; det er ikke en sikker numerisk grænse.
- Sidste uarmerede punkt er ved **130 cm**, selv om sidste tal på x-aksen er 120.''',
'''- Uarmeret: gule trekanter. 1 lag: blå ruder. **2 lag armering**: lilla firkanter.
- X-aksen starter ved **10 cm**, ikke 0. Ét lag starter ved 20 cm; to lag starter ved 50 cm.
- † ved **1 lag, h = 100 og 110 cm**, og **2 lag, h = 90 og 100 cm**. Ved 100 cm på étlagskurven er aflæsningen ca. **1,7 / 1,5 MN/m²**; streg og markør ligger tæt, og værdien bør behandles som omtrent **1,5-2,0 MN/m²**.
- Ved 50 cm ligger kurverne for henholdsvis ét og to lag omkring **12** og **9 MN/m²**. Sidste uarmerede punkt er ved **140 cm**.''',
'''- Uarmeret: gule trekanter. 1 lag: blå ruder. **2 lag armering**: lilla firkanter.
- X-aksen starter ved **20 cm**. Tolagskurven starter først ved **60 cm** og slutter ved 110 cm.
- † ved **1 lag, h = 110 og 120 cm**, og **2 lag, h = 100 og 110 cm**. Punkterne omkring 2 MN/m² er identificerbare, men præcis placering på hver side af 2 kan ikke afgøres ud fra grafikken med tilsvarende sikkerhed.
- Sidste uarmerede punkt er ved **150 cm**, selv om sidste tal på x-aksen er 140.''',
'''- Uarmeret: gule trekanter. 1 lag: blå ruder. Lilla firkanter er betegnet **Flere lag**, ikke specifikt 2 lag.
- X-aksen starter ved **30 cm**. Kurven Flere lag starter ved **50 cm** og slutter ved **120 cm**.
- † ved **1 lag, h = 120 og 130 cm**, og **Flere lag, h = 110 og 120 cm**. Endepunkterne er omkring 1 MN/m²; forskellen mellem fx 0,8, 0,9 og 1,0 kan ikke opfattes som sikre grunddata.
- Sidste uarmerede punkt er ved **160 cm**, selv om sidste tal på x-aksen er 150.''',
'''- Uarmeret: gule trekanter. 1 lag: blå ruder. Lilla firkanter er betegnet **Flere lag**, ikke specifikt 2 lag.
- X-aksen starter ved **40 cm**. Kurven Flere lag starter ved **50 cm** og slutter ved **130 cm**.
- † ved **1 lag, h = 130 og 140 cm**, og **Flere lag, h = 120 og 130 cm**. Sidste punkt på Flere lag ligger meget tæt på nul: grafisk ca. **0,6 MN/m²**. Markøren kan ses, men decimalen er usikker og skal ikke behandles som et eksakt grundtal.
- Sidste uarmerede punkt er ved **170 cm**, selv om sidste tal på x-aksen er 160.'''
]
for i,d in enumerate(data):
    cols=[('Uarmeret','purple' if i==0 else 'yellow'),('1 lag armering','blue')]
    if i>0:cols.append(('2 lag armering' if i<4 else 'Flere lag','purple'))
    text+=f'\n## Diagram {i+1} - E₀ = {E[i]} MN/m², belastningsklasse {i+1}\n\n'
    text+=f'Kilde: [Diagram {i+1}.png](Diagram%20{i+1}.png). **{counts[i]} markører**. Alle Eᵤ-celler nedenfor er omtrentlige **PNG / PDF**, i MN/m².\n\n'
    text+='| h (cm) | '+' | '.join(label for label,_ in cols)+' |\n'
    text+='|---:|'+'---:|'*len(cols)+'\n'
    mapped={color:{z['h']:z for z in pts} for color,pts in d.items()}
    for h in sorted({z['h'] for pts in d.values() for z in pts}):
        cells=[]
        for label,color in cols:
            z=mapped[color].get(h)
            cells.append('—' if z is None else f"{fmt(z['png'])} / {fmt(z['pdf'])}"+(' †' if low(z) else ''))
        text+=f'| {h} | '+' | '.join(cells)+' |\n'
    text+='\n**Bemærkninger og tvivl:**\n\n'+notes[i]+'\n'
text+='''
## Hvad kan fastslås nu?

| Kontrolpunkt | Status |
|---|---|
| Alle markerede punkters placering på x-aksen | Kan aflæses for alle 176 punkter. |
| Hvilken kurve hvert punkt tilhører | Kan identificeres for alle 176 punkter. |
| Omtrentlige Eᵤ-værdier | Kan aflæses for alle 176 punkter; se skemaerne og †-markeringerne. |
| Eksakte oprindelige Eᵤ-værdier | Kan ikke dokumenteres fra billederne eller PDF-grafikken alene. |
| Kurveværdier uden en markør | Ikke fastlagt i denne kontrol; tomme felter må ikke udfyldes med nul. |
| Om lilla kurve i diagram 5 og 6 er præcis 2 lag | Kan ikke afgøres ud fra diagrammernes signaturforklaring; den siger Flere lag. |
| Nulpunkt på étlagskurven i diagram 1 | Ikke sikkert fastlagt; sidste markør ligger næsten på nulaksen. |
| Uoverensstemmelser mellem PNG og PDF | Ingen væsentlige inden for den praktiske aflæsningsmargin. |

De små udsving som fx 29,9/30,0 eller 0,9/1,0 i en grafisk aflæsning skal ikke bruges til at udlede en større præcision end kilderne giver. Før værdierne eventuelt bliver faste beregningspunkter, skal der tages stilling til afrunding og håndtering af de lave endepunkter. Denne kontrol fastlægger ikke disse valg.
'''
# Verify complete coverage and each source-pair cell before writing.
assert sum(counts)==176
assert sum(len(d['purple' if i==0 else 'yellow']) for i,d in enumerate(data))==82
assert sum(len(d['blue']) for d in data)==60
assert sum(len(d['purple']) for d in data[1:])==34
assert text.count('## Diagram ')==6
out=ROOT/'diagrambilleder/codex-diagram-kontrol.md'
out.write_text(text,encoding='utf-8')
print('Skrevet:',out)
print('Markører:',counts,'I alt:',sum(counts),'Særligt markerede:',lows,'I alt:',sum(lows))
