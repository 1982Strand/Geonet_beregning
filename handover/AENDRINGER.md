# Designgennemgang — Geonet-beregning v0.3 → v0.4

Branch: **`feature/ui-redesign-v04`**

Valgt flow: **B — input i venstre kolonne, resultat fast i højre.**
Se `Designgennemgang.dc.html`, option 1b (princip) og 1d (gennemarbejdet skærm).

```bash
rtk git checkout -b feature/ui-redesign-v04
```

Filerne i denne mappe lægges i repoet som:

| Fra | Til |
|---|---|
| `handover/config.toml` | `.streamlit/config.toml` |
| `handover/byggros_theme.css` | `assets/byggros_theme.css` |
| `handover/ui.py` | `ui.py` (repo-roden, ved siden af `app.py`) |

Logoet skal ligge som `static/byggros_logo.png` med gennemsigtig baggrund, og
`[server] enableStaticServing = true` skal være sat, for at topbjælken kan hente
det. Alternativt indlæses det som base64 i `ui.topbjaelke()`.

Der ændres ikke i `core/calculator.py`, `core/data.py` eller `core/placement.py`.
Gennemgangen er rent præsentation — ingen beregningslogik røres.

---

## 1 Grundopsætning

`config.toml` sætter tema, farver og skrifter. `ui.py` indeholder
præsentationslaget — ingen beregningslogik — og erstatter de håndskrevne
`st.markdown`-blokke i `app.py`. Første linjer i `app.py`:

```python
import ui

ui.opsaet_side()          # sætter page_config og indlæser stylesheetet
ui.topbjaelke(version="v0.4")
```

Der gøres opmærksom på, at `ui.opsaet_side()` selv kalder
`st.set_page_config()` og derfor skal stå som allerførste Streamlit-kald.

### Hvad `ui.py` dækker

| Funktion | Erstatter |
|---|---|
| `mm() mpa() grader() procent() fortegn()` | al ad hoc-formatering, herunder `95.2858` |
| `topbjaelke()` | `st.title("🏗️ Dimensionering")` |
| `etiket()` | emoji-overskrifter og `st.subheader` |
| `resultatkort()` | resultat-metric + den brede resultattabel |
| `snit()` | matplotlib-figuren med opbygningssøjlerne |
| `produkttabel()` | produktoversigten i begge tilstande |
| `besked()` | `st.info` / `st.warning` / `st.success` |

`snit()` tager samme datastruktur i begge tilstande: i Brugerdefineret sendes
fire kolonner og `reference_mm=700`, i Standard tre kolonner og
`reference_mm=None`. Skalaen udregnes af den højeste søjle, så alle snit kan
sammenlignes direkte.

---

## 2 Ændringer i `app.py`, sektion for sektion

### 2.1 Sidebar — navigation

Menupunkterne grupperes i to blokke, og emoji erstattes af Material Symbols,
som Streamlit understøtter direkte i `st.page_link`, `st.button` og
`st.selectbox`-etiketter.

```python
with st.sidebar:
    st.image("assets/byggros_logo.jpeg", width=150)
    st.caption("BEREGNING")
    valg = st.radio(..., options=["Dimensionering", "Rapport"], label_visibility="collapsed")
    st.caption("OPSLAG")
    opslag = st.radio(..., options=["Materialer", "Geonet-database",
                                    "Designdiagrammer", "Trafikklasse-korrelation"],
                      label_visibility="collapsed")
```

Ikoner: `:material/straighten:` (Dimensionering), `:material/description:`
(Rapport), `:material/layers:` (Materialer), `:material/grid_on:`
(Geonet-database), `:material/show_chart:` (Designdiagrammer),
`:material/table_chart:` (Trafikklasse-korrelation).

### 2.2 Sidehoved

Titlen `🏗️ Dimensionering` erstattes af en `st.html`-bjælke med logo,
værktøjsnavn, versionsmærke, `Vis mellemregninger`-kontakt og
`Generér rapport`. Bjælken gentages på alle sider, så konteksten er den samme
hele vejen igennem.

### 2.3 Layout — input og resultat

Hele `Dimensionering`-siden lægges i to kolonner:

```python
input_col, result_col = st.columns([328, 1000], gap="large")
```

`input_col` indeholder Underbund, Dimensioneringsgrundlag, Opbygning og Geonet.
`result_col` indeholder Resultat, Opbygning, Designdiagram, Produktvalg og de
sammenfoldede afsnit. Ved skærmbredder under 1180 px falder kolonnerne under
hinanden — det håndteres i stylesheetets afsnit 13.

Input-kolonnen skal kunne scrolles uafhængigt, så resultatet bliver stående ved
justering af φ, lagtykkelser eller trafikklasse:

```css
/* tilføjes til assets/byggros_theme.css */
[data-testid="column"]:first-child{
  position:sticky; top:0; align-self:flex-start;
  max-height:100vh; overflow-y:auto;
}
```

Der gøres opmærksom på, at Streamlit gentegner hele siden ved hver ændring.
For at undgå at resultatet blinker, lægges beregningen i
`@st.cache_data` med input-værdierne som nøgle.

### 2.4 Resultatafsnittet

```python
ui.resultatkort([
    {"etiket": "Nødvendig uden geonet", "vaerdi": "1038",
     "note": "Ustabiliseret opbygning, interpoleret · φ-korrigeret"},
    {"etiket": "1 lag geonet", "vaerdi": "793",
     "delta": "−245 mm", "delta_note": "24 % tyndere"},
    {"etiket": "2 lag geonet", "vaerdi": "686", "anbefalet": True,
     "delta": "−352 mm", "delta_note": "34 % tyndere · holder ved 700 mm"},
])
```

Rækken erstatter både `st.metric` og den brede resultattabel. Anvendes
`st.metric` alligevel, skal `delta_color="inverse"` sættes, fordi en reduktion i
tykkelse er en gevinst, ikke et fald.

Den brede produkttabel flyttes ned under diagrammet og reduceres til
Produkt · 1 lag · 2 lag med differencerne som undertekst. Kolonnerne
`Basisreduktion`, `Net-korrektion` og `φ-korrektion` vises kun, når
`Vis mellemregninger` er slået til.

### 2.5 Opbygnings-visualiseringen

Matplotlib-figuren erstattes af `ui.snit()`:

```python
ui.snit(
    kolonner=[
        {"titel": "Indtastet opbygning",
         "lag": [("Stabilgrus", 300, "baerelag"), ("Bundsikring", 400, "bundsikring")],
         "total_mm": 700, "underbund_tekst": "UNDERBUND · Eu 8 MPa",
         "status": ("Reference", "neutral")},
        {"titel": "Uden geonet",
         "lag": [("Stabilgrus", 433, "baerelag"), ("Bundsikring", 578, "bundsikring")],
         "total_mm": 1011, "status": ("311 mm for lidt", "kritisk")},
        {"titel": "1 lag geonet",
         "lag": [("Stabilgrus", 340, "baerelag"), ("Bundsikring", 453, "bundsikring")],
         "geonet_mm": [0], "total_mm": 793, "status": ("93 mm for lidt", "kritisk")},
        {"titel": "2 lag geonet",
         "lag": [("Stabilgrus", 294, "baerelag"), ("Bundsikring", 392, "bundsikring")],
         "geonet_mm": [0, 392], "total_mm": 686, "status": ("14 mm i overskud", "gron")},
    ],
    reference_mm=700,
)
```

Ændringer i selve tegningen:

- Fælles stiplet referencelinje i alle snit ved den indtastede tykkelse.
- Lagetiketten skjules automatisk, når laget bliver for tyndt til at rumme den.
- Målsætning til højre for søjlen med samme talformat som resultatkortene.
- Statuslinjen formuleres som en konstatering: `311 mm for lidt` frem for
  `Mangler 311 mm`.
- Geonet-etiketten flyttes til signaturen; de røde linjer står uden tekst.

### 2.6 Designdiagrammet

Matplotlib erstattes af Plotly (`plotly>=5.22` tilføjes til
`requirements.txt`):

```python
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
```

- Kurvefarver: uden geonet `#8B7355`, 1 lag `#15211A`, 2 lag `#1B6B34`.
- Den indtastede opbygning markeres med `#B42318` og en lodret hjælpelinje ned
  til x-aksen, så aflæsningen kan foretages direkte.
- Titlen udgår; forudsætningerne står i kortets sidehoved.
- `hovertemplate="%{x:.0f} cm · Eu %{y:.1f} MN/m²"`.
- Talformat: `Eo = 95 MN/m²`, ikke `95.2858`.

### 2.7 Beskeder og sammenfoldede afsnit

`Advarsler og anbefalinger`, `Udførelseskrav` og `Sådan beregnes det` bevares
som `st.expander` nederst, lukket som standard. `Sådan beregnes det` åbnes
automatisk, når `Vis mellemregninger` er slået til.

Emoji i `st.info`, `st.warning` og `st.success` fjernes — Streamlit tegner
selv et ikon.

### 2.8 Talformatering

Der indføres én hjælpefunktion, som bruges alle steder:

```python
def mm(v):  return f"{v:,.0f} mm".replace(",", ".")
def mpa(v): return f"{v:,.0f} MPa".replace(",", ".")
def deg(v): return f"{v:.1f}°".replace(".", ",")
```

Decimalkomma og tusindtalspunktum i hele appen, også i rapporten.

### 2.9 Rapporten

PDF-rapporten er kundevendt og bør følge samme system: IBM Plex Sans,
logo i sidehovedet, resultattabellen med samme kolonner som skærmen, og snittet
indsat som vektor. Behandles som særskilt opgave efter skærmbilledet er
godkendt.

---

## 2.10 Standard-tilstand

Standardtilstanden adskiller sig på tre punkter, som i dag ikke fremgår af
skærmen. De gøres eksplicitte i input-kolonnen under overskriften
`FASTE FORUDSÆTNINGER`:

- φ = 37,0°, jf. designmanualernes forudsætning
- ingen φ-korrektion
- materialelag indgår ikke

Resultatet viser tre søjler i stedet for fire, uden referencelinje, og
produkttabellen bliver hovedindholdet — grupperet efter serie med effektindeks:

```python
ui.snit(kolonner, reference_mm=None)
ui.produkttabel(raekker, grupperet=True)
```

Se `Designgennemgang.dc.html`, option 4a.

---

## 3 Prioriteret liste til Claude Code

1. Læg `.streamlit/config.toml`, `assets/byggros_theme.css` og `ui.py` ind, og
   kald `ui.opsaet_side()` + `ui.topbjaelke()` øverst i `app.py`.
   *Halvdelen af det hjemmelavede indtryk forsvinder her.*
2. Fjern al emoji fra overskrifter, menupunkter, knapper og beskeder; erstat med
   `ui.etiket()` og Material Symbols i navigationen.
3. Erstat al talformatering med `ui.mm()`, `ui.mpa()`, `ui.grader()` — herunder
   `95.2858 MN/m²`.
4. Del `Dimensionering` i `input_col` / `resultat_col` med sticky inputkolonne.
5. Erstat resultatafsnittet med `ui.resultatkort()`.
6. Erstat produktoversigten med `ui.produkttabel()`; læg mellemregninger bag
   `Vis mellemregninger`.
7. Erstat matplotlib-søjlerne med `ui.snit()` i begge tilstande.
8. Skift designdiagrammet til Plotly med den angivne farvepalet.
9. Gruppér sidebaren i BEREGNING og OPSLAG.
10. Gennemgå rapportskabelonen med samme skrift og farver.

Punkt 1–3 kan udføres uden risiko for beregningerne og giver det største udslag.
