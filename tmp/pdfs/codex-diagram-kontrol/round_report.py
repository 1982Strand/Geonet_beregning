from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import re

root=Path(r'C:\geonet_beregning')
target=root/'diagrambilleder/codex-diagram-kontrol.md'
original=target.read_text(encoding='utf-8')
sections=re.split(r'^## Diagram (\d+) - ',original,flags=re.M)
assert len(sections)==13,'Expected the six original diagram sections.'
diagrams=[]
for n in range(1,13,2):
    number=int(sections[n])
    rows=[]
    for line in sections[n+1].splitlines():
        if not re.match(r'^\| \d+ \|',line):continue
        cells=[c.strip() for c in line.strip('|').split('|')]
        if not any(' / ' in c for c in cells[1:]):continue
        h=int(cells[0]); vals=[]
        for cell in cells[1:]:
            if cell=='—': vals.append(None);continue
            m=re.fullmatch(r'(\d+,\d+) / (\d+,\d+)( †)?',cell)
            assert m,cell
            png=Decimal(m[1].replace(',','.'))
            pdf=Decimal(m[2].replace(',','.'))
            rounded=(png*2).quantize(Decimal('1'),rounding=ROUND_HALF_UP)/2
            vals.append({'eu':rounded,'low':bool(m[3]),'png':png,'pdf':pdf})
        rows.append((h,vals))
    diagrams.append(rows)

def fmt(v):
    d=Decimal(v)
    return str(int(d)) if d==int(d) else str(d.normalize()).replace('.',',')

counts=[sum(v is not None for _,row in rows for v in row) for rows in diagrams]
assert counts==[20,28,30,31,33,34]
assert sum(v['low'] for rows in diagrams for _,row in rows for v in row if v)==22
assert all(abs(v['png']-v['pdf'])<=Decimal('0.5') for rows in diagrams for _,row in rows for v in row if v)
assert [(h,fmt(vals[0]['eu'])) for h,vals in diagrams[0] if h in [0,20,40,80]]==[(0,'30'),(20,'21'),(40,'14,5'),(80,'6')]

e0=[30,45,60,80,120,150]
notes=[
    'Ustabiliseret har lilla firkanter, og 1 lag net har blå ruder. Der er ingen kurve for 2 lag net. Sidste ustabiliserede punkt er ved 110 cm. Ved 1 lag net og h = 90 cm afrundes den lave aflæsning til **0 MPa †**. Det er en afrunding af en markør næsten på nulaksen og dokumenterer ikke et eksakt fysisk nulpunkt.',
    '2 lag net har fem markører, fra h = 50 til 90 cm. Sidste punkt for 1 lag net er ved 100 cm, og sidste ustabiliserede punkt er ved 130 cm.',
    'X-aksen starter ved 10 cm. 1 lag net starter ved 20 cm; 2 lag net starter ved 50 cm. De lave punkter ved 1 lag net, h = 100 og 110 cm, og 2 lag net, h = 90 og 100 cm, er markeret med †. Sidste ustabiliserede punkt er ved 140 cm.',
    'X-aksen starter ved 20 cm. 2 lag net går fra h = 60 til 110 cm. Sidste punkt for 1 lag net er ved 120 cm, og sidste ustabiliserede punkt er ved 150 cm.',
    'X-aksen starter ved 30 cm. Diagrammets lilla kurve hedder **Flere lag** og kan ikke ud fra signaturforklaringen alene betegnes som præcis 2 lag. Den går fra h = 50 til 120 cm. Sidste ustabiliserede punkt er ved 160 cm.',
    'X-aksen starter ved 40 cm. Diagrammets lilla kurve hedder **Flere lag** og går fra h = 50 til 130 cm. Sidste punkt på denne kurve afrundes til **0,5 MPa †** og ligger meget tæt på nul. Sidste ustabiliserede punkt er ved 170 cm.'
]
def labels(i):
    return ['Ustabiliseret','1 lag net']+([] if i==0 else ['2 lag net' if i<4 else 'Flere lag net'])

out='''# Kontrol af diagramaflæsninger

Dato: 24. september 2026.

## Resultat og afrunding

Alle **176 markerede kurvepunkter** er identificeret og aflæst i de seks diagrambilleder samt krydstjekket mod designmanualens side 10. Ingen markører er ulæselige. **22 lave punkter** er markeret med **†**, fordi aflæsningsusikkerheden er stor i forhold til deres værdi.

Der vises nu **ét Eᵤ-tal pr. kurve og bærelagstykkelse**, afrundet til nærmeste **0,5 MPa**. Afrundingen tager udgangspunkt i PNG-aflæsningen fra den første kontrol. PDF'en er brugt som krydstjek. Hele værdier skrives uden decimal, fx 30, 21 og 6; halve værdier skrives fx 14,5. Bærelagstykkelserne er uændrede.

**Krydstjek:** Ingen store afvigelser mellem billeder og PDF. Ingen af de kontrollerede forskelle overstiger 0,5 MPa før afrunding. Små forskelle omkring en afrundingsgrænse ændrer ikke valget af PNG-aflæsningen som grundlag.

## Kilder og læsevejledning

- Primære kilder: `Diagram 1.png` til `Diagram 6.png` i denne mappe.
- Krydstjek: [brochure-tensar-designmanual-sept-2024-1.pdf](../Dokumenter%20og%20data/datablade%20og%20designmanualer/brochure-tensar-designmanual-sept-2024-1.pdf), PDF-side 10, trykt side 10. Diagrammerne er her angivet som baseret på TriAx TX160.
- **h** er bærelagstykkelse i **cm**. **Eᵤ** er bundmodul i **MPa**, hvor **1 MPa = 1 MN/m²**. E₀ i overskrifterne er modulet på oversiden af bærelaget.
- **Ustabiliseret** svarer til kurven **Uarmeret** i kilderne. **1 lag net**, **2 lag net** og **Flere lag net** følger diagrammernes kurver. Flere lag i diagram 5 og 6 betyder ikke nødvendigvis præcis to lag.
- Alle Eᵤ-værdier er omtrentlige. Afrunding til 0,5 MPa ændrer ikke den praktiske aflæsningsmargin på omkring **±0,5 MPa** og dokumenterer ikke de eksakte oprindelige grundtal.
- **†** markerer de lave punkter fra første kontrol, hvor mindst én kildeaflæsning var højst 2 MPa før afrunding. Markeringen er bevaret efter afrunding.
- **—** i de første seks tabeller betyder, at der ikke er en markeret værdi for kurven ved den pågældende tykkelse. Det betyder ikke nul.

### Fremgangsmåde

Alle seks billeder og manualsiden er gennemgået visuelt. Markørernes centre er aflæst i forhold til de tilstødende gitterlinjer. PDF-krydstjekket anvender PDF'ens grafiske markørpositioner og egne gitterlinjer. De aflæste PNG-værdier fra første kontrol er herefter afrundet til nærmeste 0,5 MPa. Tabellerne nederst omstiller alene disse afrundede punkter fra h → Eᵤ til Eᵤ → h; der er ikke beregnet mellemværdier.

### Oversigt over markører

| Diagram | E₀ (MPa) | Ustabiliseret | 1 lag net | 2 lag / Flere lag net | I alt | Heraf † |
|---|---:|---:|---:|---:|---:|---:|
'''
for i,rows in enumerate(diagrams):
    nc=len(rows[0][1])
    nums=[sum(row[k] is not None for _,row in rows) for k in range(nc)]
    low=sum(v['low'] for _,row in rows for v in row if v)
    out+=f'| {i+1} | {e0[i]} | {nums[0]} | {nums[1]} | {nums[2] if nc>2 else "—"} | {counts[i]} | {low} |\n'
out+='| **Samlet** | | **82** | **60** | **34** | **176** | **22** |\n'

for i,rows in enumerate(diagrams):
    names=labels(i)
    out+=f'\n## Diagram {i+1} - E₀ = {e0[i]} MPa, belastningsklasse {i+1}\n\n'
    out+=f'Kilde: [Diagram {i+1}.png](Diagram%20{i+1}.png). **{counts[i]} markører**. Kurveværdierne er Eᵤ i **MPa**, afrundet til nærmeste 0,5.\n\n'
    out+='| h (cm) | '+' | '.join(names)+' |\n|---:|'+'---:|'*len(names)+'\n'
    for h,row in rows:
        cells=['—' if v is None else fmt(v['eu'])+(' †' if v['low'] else '') for v in row]
        out+=f'| {h} | '+' | '.join(cells)+' |\n'
    out+='\n**Bemærkninger:** '+notes[i]+'\n'

out+='''
## Tabeller med Eᵤ fra 1 til 45 MPa

Første kolonne viser **Eᵤ = 1, 2, 3, …, 45 MPa**, ligesom opstillingen med hele Eᵤ-trin i [geonet_interpolerede_diagrammer.xlsx](geonet_interpolerede_diagrammer.xlsx). Alle seks tabeller har samtlige 45 rækker, også hvor diagrammets kurver ikke når den pågældende værdi.

De øvrige kolonner viser **bærelagstykkelse h i cm**. En celle er kun udfyldt, hvis et afrundet, markeret punkt i tabellerne ovenfor har netop den pågældende hele Eᵤ-værdi. Øvrige celler er tomme. Der er ikke interpoleret, ekstrapoleret eller kopieret tykkelsesværdier fra Excel-filen.

Punkter med halve Eᵤ-værdier, fx 14,5 MPa, står fortsat i tabellerne ovenfor. De er ikke flyttet til en hel Eᵤ-række. Det samme gælder punkter under 1 MPa, som ligger uden for dette afsnits interval. **†** følger punktet og angiver usikkerheden i Eᵤ-aflæsningen, selv om cellen her viser h.
'''
inverted=[]
for i,rows in enumerate(diagrams):
    names=labels(i)
    mapping={eu:[None]*len(names) for eu in range(1,46)}
    for h,row in rows:
        for k,v in enumerate(row):
            if v is None:continue
            eu=v['eu']
            if eu==int(eu) and 1<=eu<=45:
                assert mapping[int(eu)][k] is None,('Rounding collision',i+1,k,eu)
                mapping[int(eu)][k]=(h,v['low'])
    inverted.append(mapping)
    out+=f'\n### Diagram {i+1} - E₀ = {e0[i]} MPa\n\n'
    out+='| Eᵤ (MPa) | '+' | '.join(name+' - h (cm)' for name in names)+' |\n'
    out+='|---:|'+'---:|'*len(names)+'\n'
    for eu,vals in mapping.items():
        cells=['' if v is None else str(v[0])+(' †' if v[1] else '') for v in vals]
        out+=f'| {eu} | '+' | '.join(cells)+' |\n'

# Check coverage and reverse mappings directly against the source-point records.
assert len(inverted)==6 and all(list(d)==list(range(1,46)) for d in inverted)
for rows,mapping in zip(diagrams,inverted):
    expected={(int(v['eu']),k,h) for h,row in rows for k,v in enumerate(row) if v and v['eu']==int(v['eu']) and 1<=v['eu']<=45}
    actual={(eu,k,v[0]) for eu,row in mapping.items() for k,v in enumerate(row) if v}
    assert actual==expected
assert 'PNG / PDF' not in out
target.write_text(out,encoding='utf-8')
saved=target.read_text(encoding='utf-8')
assert saved==out
print('Updated:',target)
print('Marker counts:',counts,'Total:',sum(counts))
print('45-row tables:',len(inverted))
print('Populated inverted cells:',[sum(v is not None for row in d.values() for v in row) for d in inverted])
print('User examples and all inverse mappings verified.')
