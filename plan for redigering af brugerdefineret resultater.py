# Plan — Brugerdefineret: beregning og visning af resultater (sektion D + Resultat)

## Context

Brugeren vil have rettet "Brugerdefineret"-tilstanden i Geonet-app'en så
visningen af resultater matcher Excel-arkets struktur (`2. Dimensionering`,
sektion F) og giver mere overblik over forskellen mellem uarmeret/armeret
samt korrektionsfaktorernes effekt på tykkelsen.

**Forskel fra Excel:** i appen vælger brugeren ikke "1 lag" / "2 lag"
(Excel sektion E) — begge resultater vises samtidig så brugeren kan
sammenligne.

**Excel sektion H ("Reduktionsstrategi") udskydes** — implementeres først
efter at denne plan er gennemført og afstemt.

## Brugerens afklaringer (fra AskUserQuestion)

- Hovedproblem: "Der mangler information i appen, som der er i excel-arket.
  Der skal skabes yderligere overblik over sammenligningen mellem uarmeret
  og armeret, samt korrektionsfaktorerne og hvordan de påvirker beregningerne."
- Visning-radio i sektion D bevares: både "Vis alle produkter (oversigt)"
  og "Vælg specifikt produkt" skal forblive valgbare i Brugerdefineret.
- Resultat-layout: to kolonner side om side, med eksplicit mm-reduktion.
- Breakdown: både visuel boks under resultat **og** udvidet "Sådan beregnes det".
- I oversigt-mode: breakdown for bedste produkt + note om variation pr. produkt.

## Ændringer

### 1. Resultat-kort — tilføj eksplicit mm-reduktion

I [app.py](app.py) — `_render_gruppe_kort()` (linje 242–289):

Tilføj linje med ↓ {reduktion_mm} mm under hovedtallet, ved siden af eller
i stedet for `(X% reduktion)`-parentesen. Eksisterende `t_armeret_mm` og
`t_uarmeret_mm` findes allerede på produkter inde i gruppen — beregn
`reduktion_mm = t_uarmeret_mm − t_armeret_mm` (afrundet).

Layout (jf. brugerens valg):

```
1 LAG GEONET
440 mm
↓ 260 mm (37 %)
eksakt: 437 mm (36,8 % reduktion)
GS-GRID: SX160
```

Gælder begge tilstande (Standard + Brugerdefineret) for konsistens, og
begge modes i Brugerdefineret (oversigt + specifikt).

### 2. Ny "Beregnings-breakdown"-boks — under Resultat, før expandere

Ny funktion i [app.py](app.py), kaldes fra `render_brugerdefineret()`
mellem resultatkortene og `_render_oversigt_expanders()`:

```python
def _vis_beregnings_breakdown(
    eu, eo, phi, valgt_klasse,
    bedste_1, bedste_2,
    geonet=None, geonet_navn=None,
    materialer=None,
) -> None
```

Boksen viser visuelt for hver lag-mode:

```
Beregnings-breakdown

Uarmeret bærelagstykkelse
  T_basis (opslag/interpoleret)        700 mm
  (ingen φ- eller net-korrektion)
  = 700 mm

Med 1 lag geonet (GS-GRID SX160)
  T_basis_armeret                       500 mm
  φ-korrektion  φ=40,0°  (−0,10)        −50 mm
  Net-korrektion  (±0,00)                ±0 mm
  = 450 mm   ↓ 250 mm fra uarmeret (36 %)

Med 2 lag geonet (GS-GRID SX160)
  T_basis_armeret                       430 mm
  φ-korrektion  φ=40,0°  (−0,10)        −43 mm
  Net-korrektion  (±0,00)                ±0 mm
  = 387 mm   ↓ 313 mm fra uarmeret (45 %)
```

Genbruger eksisterende:

- [core/calculator.py](core/calculator.py) `beregn()` — returnerer allerede
  `t_basis_uarm_mm`, `t_basis_arm_mm`, `phi_korrektion`, `samlet_faktor`,
  `t_armeret_mm`, `t_uarmeret_mm`. Ingen nye kerneberegninger nødvendige.
- mm-effekt pr. korrektion = `t_basis_arm_mm × phi_korrektion`
  og `t_basis_arm_mm × net_korrektion` (samme princip som
  `_vis_phi_opsummeringsboks` ved [app.py:887](app.py:887) allerede gør).
- `_dk_num` [app.py:823](app.py:823) til dansk talformatering.

**Oversigt-mode**: brug `bedste_1["produkter"][0]["korrektion"]` og navn
til at vise net-korrektion for det bedste produkt i hver lag-mode + en
note: *"Net-korrektionen vist her gælder det bedst reducerende produkt
({navn}). Andre produkter har andre korrektioner — se kolonnerne ovenfor."*

**Specifikt-mode**: brug det valgte `geonet`-objekts korrektion direkte.

**Fejl-håndtering**: hvis `bedste_1` (eller `bedste_2`) er `None` for en
given lag-mode, skip den sektion i boksen i stedet for at vise en fejl —
boksen er sekundær til selve resultatkortene som allerede håndterer
manglende værdier.

### 3. Udvidet "Sådan beregnes det"-expander

[app.py:600-740](app.py:600) — `_render_oversigt_expanders()` har allerede
en grundig 7-trins visning. Mindre udvidelser:

- **Trin 6 (φ-korrektion)**: tilføj mm-effekt-linje pr. lag-mode:
  *"Effekt: 1 lag = T_basis × φ-kor = X mm, 2 lag = Y mm"*
  (allerede til stede i `_vis_phi_opsummeringsboks` — genbrug formen).
- **Trin 7 (Net-korrektion)**: tilsvarende mm-effekt-linje pr. lag-mode.
- **Samlet eksempel-linje for hver lag-mode**:
  *"1 lag: 500 mm × 0,90 = 450 mm"* (med faktiske tal indsat).

Disse tilføjelser er små og krydsrefererer Excel-arkets fane "3. Sådan
beregnes det". Genbruger `beregn()`-output (allerede kaldt for `ref_1` og
`ref_2` i samme funktion).

### 4. Sektion D — uændret

Visning-radioen i [app.py:1071-1082](app.py:1071) bevares som er.
Produktvælger + manuel korrektion bevares som er. Intet at ændre her.

## Filer der røres ved

- [app.py](app.py) — alle UI-ændringer
- [core/calculator.py](core/calculator.py) — **ingen ændringer**
  (alle nødvendige mellemregninger returneres allerede af `beregn()`)
- [core/data.py](core/data.py) — **ingen ændringer**
- [core/validators.py](core/validators.py) — **ingen ændringer**

## Verifikation

Manuel test via Streamlit:

1. Start app: `streamlit run app.py`
2. Skift til "Brugerdefineret"-tilstand
3. **Specifikt-mode test**: Eu=10, klasse 5, materialelag (SG II 0-32 350 mm
   + Bundsand 650 mm = φ ca. 36,5°), produkt = GS-GRID SX160
   - Sammenlign de viste tal med Excel-arket (samme inputs i fane
     "2. Dimensionering"): T_uarmeret, T_armeret (1 lag), T_armeret (2 lag),
     reduktion mm, reduktion %, φ-kor mm-effekt, net-kor mm-effekt.
4. **Oversigt-mode test**: samme inputs uden produktvalg
   - Tjek at breakdown-boksen viser bedste produkts net-korrektion + note
   - Tjek at "Sådan beregnes det" er konsistent
5. **Kant-tilfælde**: Eu=20, klasse 6 — typisk hvor 2-lag ikke er gyldigt
   - Tjek at breakdown-boksen kun viser 1-lag sektionen, uden fejl
6. **Standard-tilstand**: tjek at den nye mm-reduktion også vises der
   (uden at det forstyrrer den nuværende oversigt)
