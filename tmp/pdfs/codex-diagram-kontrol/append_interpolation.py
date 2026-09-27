from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import re

path = Path(r'C:\geonet_beregning\diagrambilleder\codex-diagram-kontrol.md')
original = path.read_text(encoding='utf-8')
heading = '## Interpolerede tabeller med hele Eᵤ-trin'
assert heading not in original, 'Interpolation section already exists.'
parts = re.split(r'^## Diagram (\d+) - ', original, flags=re.M)
assert len(parts) == 13
diagrams = []
for pos in range(1, 13, 2):
    number = int(parts[pos])
    section = parts[pos + 1].split('\n## ', 1)[0]
    table_header = next(line for line in section.splitlines() if line.startswith('| h (cm) |'))
    names = [v.strip() for v in table_header.strip('|').split('|')][1:]
    curves = [[] for _ in names]
    for line in section.splitlines():
        if not re.match(r'^\| \d+ \|', line):
            continue
        cells = [v.strip() for v in line.strip('|').split('|')]
        assert len(cells) == len(names) + 1
        h = Decimal(cells[0])
        for k, cell in enumerate(cells[1:]):
            if cell == '—':
                continue
            match = re.fullmatch(r'(\d+(?:,5)?)( †)?', cell)
            assert match, cell
            eu = Decimal(match[1].replace(',', '.'))
            curves[k].append((eu, h, bool(match[2])))
    for curve in curves:
        curve.sort()
        assert all(a[0] < b[0] and a[1] > b[1] for a, b in zip(curve, curve[1:]))
    diagrams.append((number, names, curves))

assert [sum(map(len, curves)) for _, _, curves in diagrams] == [20, 28, 30, 31, 33, 34]

def interpolate(curve, eu):
    if eu < curve[0][0] or eu > curve[-1][0]:
        return None
    for source_eu, h, low in curve:
        if source_eu == eu:
            return h, low, True
    for (e1, h1, low1), (e2, h2, low2) in zip(curve, curve[1:]):
        if e1 < eu < e2:
            h = h1 + (h2 - h1) * (eu - e1) / (e2 - e1)
            assert h2 < h < h1
            return h, low1 or low2, False
    raise AssertionError('Missing bracketing points')

def display(h):
    return format(h.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP), '.1f').replace('.', ',')

append = '''

## Interpolerede tabeller med hele Eᵤ-trin

Dette afsnit indeholder de beregnede tykkelser for **Eᵤ = 1–30 MPa i diagram 1** og **Eᵤ = 1–45 MPa i diagram 2–6**, i trin på **1 MPa**. Alle tykkelser h angives i **cm med præcis én decimal**.

### Beregningsgrundlag

- Grundlaget er de 176 markerede punkter i de første seks tabeller, hvor Eᵤ er afrundet til nærmeste 0,5 MPa. De halve Eᵤ-værdier indgår som støttepunkter i beregningen.
- Hver kurve behandles særskilt. Ved et eksisterende støttepunkt bruges dets tykkelse direkte. Mellem to tilstødende støttepunkter anvendes **stykkevis lineær interpolation**.
- For støttepunkterne (Eᵤ₁, h₁) og (Eᵤ₂, h₂) beregnes: **h = h₁ + (h₂ − h₁) × (Eᵤ − Eᵤ₁) / (Eᵤ₂ − Eᵤ₁)**.
- Der afrundes først til én decimal efter beregningen. Der ekstrapoleres ikke. En tom celle betyder, at Eᵤ ligger uden for den pågældende kurves aflæste område; den betyder ikke nul tykkelse.
- **†** betyder, at resultatet enten kommer direkte fra et usikkert støttepunkt eller er interpoleret med mindst ét usikkert støttepunkt. Markeringen vedrører grundlagets Eᵤ-aflæsning, ikke en særskilt måling af tykkelsen.
- Én decimal er beregningens visningspræcision. Den giver ikke diagramaflæsningen en større nøjagtighed.

**Eksempel:** I diagram 1 ligger ustabiliseret mellem h = 100 cm ved Eᵤ = 3,5 MPa og h = 90 cm ved Eᵤ = 5 MPa. Ved Eᵤ = 4 MPa bliver tykkelsen **96,7 cm**.

**Særligt om diagram 1:** Ved Eᵤ = 1 MPa bliver tykkelsen for 1 lag net **85,0 cm †**. Beregningen bruger støttepunktet ved h = 90 cm, som er afrundet til Eᵤ = 0 MPa, samt punktet ved h = 80 cm og Eᵤ = 2 MPa. Resultatet afhænger derfor af det usikre endepunkt og er ikke en selvstændig sikker aflæsning.
'''

e0s = [30, 45, 60, 80, 120, 150]
all_results = []
for number, names, curves in diagrams:
    limit = 30 if number == 1 else 45
    rows = []
    append += f'\n### Interpoleret diagram {number} - E₀ = {e0s[number-1]} MPa\n\n'
    append += '| Eᵤ (MPa) | ' + ' | '.join(name + ' - h (cm)' for name in names) + ' |\n'
    append += '|---:|' + '---:|' * len(names) + '\n'
    for eu in range(1, limit + 1):
        results = [interpolate(curve, Decimal(eu)) for curve in curves]
        rows.append(results)
        cells = ['' if result is None else display(result[0]) + (' †' if result[1] else '') for result in results]
        append += f'| {eu} | ' + ' | '.join(cells) + ' |\n'
    all_results.append(rows)

# Check the agreed example, uncertain endpoint, blank boundaries and direct anchors.
assert display(all_results[0][3][0][0]) == '96,7'
assert display(all_results[0][0][1][0]) == '85,0' and all_results[0][0][1][1]
assert all_results[0][0][0] is None and all_results[0][1][0] is None
assert all_results[0][15][1] is None
assert display(all_results[0][29][0][0]) == '0,0'
assert display(all_results[1][44][0][0]) == '0,0'
assert [len(rows) for rows in all_results] == [30, 45, 45, 45, 45, 45]
for (_, names, curves), rows in zip(diagrams, all_results):
    for k, curve in enumerate(curves):
        values = [row[k][0] for row in rows if row[k] is not None]
        assert all(a >= b for a, b in zip(values, values[1:]))
        for eu, h, low in curve:
            if eu == int(eu) and 1 <= eu <= len(rows):
                assert rows[int(eu)-1][k] == (h, low, True)
        for eu, row in enumerate(rows, 1):
            assert (row[k] is None) == (eu < curve[0][0] or eu > curve[-1][0])

# Clarify the scope of the old method statement after adding a later section.
old = 'Tabellerne nederst omstiller alene disse afrundede punkter fra h → Eᵤ til Eᵤ → h; der er ikke beregnet mellemværdier.'
new = 'Afsnittet »Tabeller med Eᵤ fra 1 til 45 MPa« omstiller alene disse afrundede punkter fra h → Eᵤ til Eᵤ → h uden mellemværdier. Det efterfølgende afsnit »Interpolerede tabeller med hele Eᵤ-trin« tilføjer de beregnede mellemværdier.'
assert original.count(old) == 1
updated = original.replace(old, new).rstrip() + append
path.write_text(updated, encoding='utf-8')

# Verify the written tables, including decimal format, numeric values and markers.
saved = path.read_text(encoding='utf-8')
assert saved == updated
assert saved.split(heading)[0].rstrip() == original.replace(old, new).rstrip()
saved_sections = re.split(r'^### Interpoleret diagram \d+ - ', saved.split(heading, 1)[1], flags=re.M)[1:]
assert len(saved_sections) == 6
for section, rows in zip(saved_sections, all_results):
    lines = [line for line in section.splitlines() if re.match(r'^\| \d+ \|', line)]
    assert len(lines) == len(rows)
    for eu, (line, expected) in enumerate(zip(lines, rows), 1):
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        assert cells[0] == str(eu)
        for cell, result in zip(cells[1:], expected):
            if result is None:
                assert cell == ''
            else:
                assert re.fullmatch(r'\d+,\d(?: †)?', cell)
                assert cell == display(result[0]) + (' †' if result[1] else '')

print('Updated:', path)
print('Rows per diagram:', [len(rows) for rows in all_results])
print('Filled cells per diagram:', [sum(v is not None for row in rows for v in row) for rows in all_results])
print('Verified: source anchors, interpolation example, boundaries, uncertainty markers, monotonicity, one-decimal output and preserved prior tables.')
