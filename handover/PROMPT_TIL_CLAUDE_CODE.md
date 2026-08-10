# Opgave til Claude Code — visuel omlægning af Geonet-beregning

Denne fil er selve opgavebeskrivelsen. Læs den hele igennem, før du ændrer noget.

---

## Til dig der giver filen videre (menneske, læs kun dette afsnit)

1. Hent mappen `handover/` fra chatten (download-kortet) og læg den i roden af
   `Geonet_beregning`, så du har:

   ```
   Geonet_beregning/
     app.py
     core/
     handover/
       AENDRINGER.md
       byggros_theme.css
       config.toml
       ui.py
       PROMPT_TIL_CLAUDE_CODE.md   ← denne fil
   ```

2. Åbn en terminal i mappen og start Claude Code.
3. Skriv: **»Læs `handover/PROMPT_TIL_CLAUDE_CODE.md` og udfør opgaven.«**
4. Når den er færdig: kør `streamlit run app.py` og se på det. Er noget galt,
   sig det til Claude Code — arbejdet ligger på en separat branch, så `main` er
   uberørt hele vejen.

Resten af filen er til Claude Code.

---

## 0 Rammer

- Alt arbejde foregår på en ny branch: `feature/ui-redesign-v04`.
- **Ingen beregningslogik må ændres.** `core/calculator.py`, `core/data.py`,
  `core/placement.py` og `core/validators.py` røres ikke. Ændrer et tal sig på
  skærmen, er det en fejl — undtagen talformatering (decimalkomma, afrunding).
- `core/backup 17.06.26/` er en gammel kopi. Ignorer den fuldstændigt.
- Al brugervendt tekst følger skrivestilen i `CLAUDE.md` (Vejdirektoratets
  håndbogssprog: passiv, konstaterende, ingen direkte tiltale).
- Commit efter hvert trin med en kort besked. Små commits, ikke én stor.
- Går et trin i vasken, så stop og spørg frem for at improvisere.

Start med:

```bash
git checkout -b feature/ui-redesign-v04
```

---

## 1 Læg filerne på plads

```bash
mkdir -p .streamlit assets static
git mv handover/config.toml .streamlit/config.toml
git mv handover/byggros_theme.css assets/byggros_theme.css
git mv handover/ui.py ui.py
```

Behold `handover/AENDRINGER.md` og denne fil i `handover/` som dokumentation.

Tilføj til `requirements.txt`:

```
plotly>=5.22
```

Tilføj til `.streamlit/config.toml`:

```toml
[server]
enableStaticServing = true
```

**Logo:** `assets/byggros_logo.jpeg` har hvid baggrund og kan ikke ligge på den
mørke topbjælke. Kopier den til `static/byggros_logo.png`. Har du ikke en version
med gennemsigtig baggrund, så lad `ui.topbjaelke()` beholde den hvide brik bag
logoet — den er designet til netop det tilfælde og ser rigtig ud.

Commit: `chore: tema, ui-modul og statiske filer på plads`

---

## 2 Kobl temaet på

`ui.py` er et præsentationslag uden beregningslogik. Læs det først — det
indeholder alle byggeklodserne, du skal bruge nedenfor.

I `app.py` står `st.set_page_config()` som allerførste Streamlit-kald omkring
linje 12. Erstat blokken med:

```python
import ui

ui.opsaet_side()
ui.topbjaelke(version="v0.4")
```

`ui.opsaet_side()` kalder selv `st.set_page_config()` og indlæser stylesheetet,
så den **skal** stå før alle andre `st`-kald. Importér `ui` før `streamlit`
bruges, men efter `import streamlit as st`.

Der findes en eksisterende CSS-blok i `app.py` omkring linje 714–880
(`st.markdown` med `<style>`). Gennemgå den: alt der handler om farver,
skrifter, knapper, tabeller og bredde er nu dækket af `assets/byggros_theme.css`
og skal slettes. Er der regler, som løser noget stylesheetet ikke dækker
(specifikke tabel-ombrydninger, enkelte `nth-child`-hacks), så flyt dem ned i
bunden af `assets/byggros_theme.css` under en kommentar
`/* ---- 14. Flyttet fra app.py ---- */`.

**Kontrolpunkt:** kør appen. Den skal nu være i IBM Plex Sans med grøn accent og
uden Streamlits standardmenu. Alle tal skal stå uændret.

Commit: `feat: byggros-tema og topbjælke`

---

## 3 Fjern emoji

Søg efter emoji i hele `app.py` (og i rapportskabelonerne i `core/rapport.py`).
Alle skal væk — de renderer forskelligt på Windows, Mac og i PDF'en.

- Sektionsoverskrifter: `st.subheader("📐 Underbund")` →
  `ui.etiket("UNDERBUND")` efterfulgt af indholdet, eller
  `st.subheader("Underbund")` hvor en rigtig overskrift er på sin plads.
- Navigation: brug Streamlits indbyggede Material Symbols i stedet:
  `:material/straighten:` Dimensionering, `:material/description:` Rapport,
  `:material/layers:` Materialer, `:material/grid_on:` Geonet-database,
  `:material/show_chart:` Designdiagrammer, `:material/table_chart:`
  Trafikklasse-korrelation.
- `st.info` / `st.warning` / `st.success`: fjern emoji i teksten. Streamlit
  tegner selv et ikon. Ønskes ensartet udseende, brug `ui.besked(tekst, slags)`.

Commit: `refactor: emoji erstattet af material symbols`

---

## 4 Ensartet talformatering

Erstat al ad hoc-formatering med hjælpefunktionerne i `ui.py`:
`ui.mm()`, `ui.mpa()`, `ui.grader()`, `ui.procent()`, `ui.fortegn()`.

Reglerne er:

| Størrelse | Format | Eksempel |
|---|---|---|
| Tykkelser | hele mm, tusindtalspunktum | `1.038 mm` |
| E-moduler | hele MPa | `95 MPa` |
| Friktionsvinkler | én decimal, decimalkomma | `38,3°` |
| Procent | hele tal | `34 %` |
| Differencer | typografisk minus | `−245 mm` |

Særligt: diagramtitlen `Designdiagram for Eo = 95.2858 MN/m²` skal blive
`95 MN/m²`. Fire decimaler signalerer en præcision, beregningen ikke har.

Gælder også rapporten i `core/rapport.py`.

**Kontrolpunkt:** søg efter `.4f`, `:.2f` og rå `f"{...}"` med tal, og bekræft at
alle går gennem `ui.`-funktionerne.

Commit: `refactor: ensartet talformatering`

---

## 5 To-kolonne-layout (flow B)

Dette er den strukturelle ændring. Se `Designgennemgang.dc.html` option 1b og 1d
for det færdige resultat, hvis du har adgang til filen.

Hele `Dimensionering`-siden lægges i to kolonner:

```python
input_col, resultat_col = st.columns([328, 1000], gap="large")
```

- **`input_col`:** Tilstand (Standard / Brugerdefineret), Underbund,
  Dimensioneringsgrundlag med trafikklasse, Opbygning med materialelag, Geonet.
- **`resultat_col`:** Resultat, Opbygning (snit), Designdiagram, Produktvalg og
  de sammenfoldede afsnit.

Input-kolonnen skal blive stående, når man scroller i resultatet — tilføj i
bunden af `assets/byggros_theme.css`:

```css
[data-testid="column"]:first-child{
  position:sticky; top:0; align-self:flex-start;
  max-height:100vh; overflow-y:auto;
  scrollbar-width:thin;
}
```

Streamlit gentegner hele siden ved hver ændring. Læg beregningen i
`@st.cache_data` med input-værdierne som nøgle, så resultatet ikke blinker, når
brugeren trækker i Eu-slideren. Cachen skal have en klar nøgle — undgå at cache
funktioner, der læser `st.session_state` direkte.

**Kontrolpunkt:** ret Eu fra 8 til 12 MPa. Resultatet skal opdatere uden at
input-kolonnen hopper eller scroller væk.

Commit: `feat: to-kolonne-layout med fast resultatpanel`

---

## 6 Resultatafsnittet

Erstat den nuværende `st.metric` + brede resultattabel med:

```python
ui.resultatkort([
    {"etiket": "Nødvendig uden geonet", "vaerdi": ui.mm(basis).replace(" mm", ""),
     "note": "Ustabiliseret opbygning, interpoleret · φ-korrigeret"},
    {"etiket": "1 lag geonet", "vaerdi": f"{et_lag:.0f}",
     "delta": f"{ui.fortegn(et_lag - basis)} mm",
     "delta_note": f"{ui.procent(100 * (basis - et_lag) / basis)} tyndere"},
    {"etiket": "2 lag geonet", "vaerdi": f"{to_lag:.0f}", "anbefalet": anbefal_to_lag,
     "delta": f"{ui.fortegn(to_lag - basis)} mm",
     "delta_note": f"{ui.procent(100 * (basis - to_lag) / basis)} tyndere"},
])
```

`anbefalet` sættes på det tyndeste alternativ, der holder ved den indtastede
opbygning. Holder ingen af dem, sættes `anbefalet` på ingen af kortene, og
årsagen står i advarselsafsnittet.

De detaljerede kolonner — `Basisreduktion`, `Net-korrektion`, `φ-korrektion` —
flyttes ind bag `Vis mellemregninger` (se trin 8).

Commit: `feat: resultatkort med anbefaling`

---

## 7 Snit og designdiagram

### 7.1 Snittene

Erstat matplotlib-figuren med `ui.snit()`. Funktionen tager samme struktur i
begge tilstande:

```python
# Brugerdefineret: fire kolonner + referencelinje
ui.snit(kolonner, reference_mm=indtastet_total)

# Standard: tre kolonner, ingen referencelinje, ét ubundet lag pr. søjle
ui.snit(kolonner, reference_mm=None)
```

Datastrukturen er dokumenteret i funktionens docstring. Bemærk:

- Skalaen udregnes af den højeste søjle, så alle snit kan sammenlignes direkte.
- `geonet_mm` er koter målt fra underbundens overkant, ikke tykkelser.
- Statusteksten formuleres som en konstatering: `311 mm for lidt`, ikke
  `Mangler 311 mm`.
- `snit()` skal have hele bredden af resultatkolonnen. Læg den ikke i en
  under-kolonne ved siden af produkttabellen — søjlerne og målsætningen får
  ikke plads nok.

Den gamle matplotlib-kode til snittene slettes, når `ui.snit()` virker. Bevares
den til rapporten, så flyt den til `core/rapport.py` og lad skærmen bruge
`ui.snit()`.

### 7.2 Designdiagrammet

Skift fra matplotlib til Plotly:

```python
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
```

- Kurvefarver: uden geonet `#8B7355`, 1 lag `#15211A`, 2 lag `#1B6B34`.
- Den indtastede opbygning markeres med `#B42318` og en lodret stiplet
  hjælpelinje ned til x-aksen, så aflæsningen kan foretages direkte.
- `hovertemplate="%{x:.0f} cm · Eu %{y:.1f} MN/m²"`.
- Diagramtitlen udgår; forudsætningerne står i kortets sidehoved.
- Skrift: `IBM Plex Sans`, 11 px. Baggrund transparent, gitter `#EDEFED`.
- Aksetitler skal have plads: sæt `margin=dict(l=60, r=20, t=10, b=60)`.

Commit: `feat: snit i html og designdiagram i plotly`

---

## 8 »Vis mellemregninger«

Én global kontakt i topbjælken styrer al mellemregning:

```python
if "vis_mellemregninger" not in st.session_state:
    st.session_state.vis_mellemregninger = False
```

Når den er slået **fra** (standard), skjules:

- φ-beregningstabellen og φ-korrektionslinjen
- kolonnerne `Basisreduktion`, `Net-korrektion`, `φ-korrektion` i produkttabellen
- interpolationsdetaljer i resultatteksten

Når den er slået **til**, vises de, og `Sådan beregnes det` åbnes automatisk.

Kontakten skal virke på alle sider, ikke kun Dimensionering.

Commit: `feat: global kontakt for mellemregninger`

---

## 9 Sidebar

Gruppér de seks flade menupunkter i to blokke med versale gruppeoverskrifter:

```
BEREGNING     Dimensionering · Rapport
OPSLAG        Materialer · Geonet-database · Designdiagrammer · Trafikklasse-korrelation
```

Logoet øverst, `BG Byggros A/S / Beregningsværktøj v0.4` nederst.
Det aktive punkt markeres med en 2,5 px grøn kant i venstre side og grøn
baggrund — det er allerede i stylesheetet, hvis `st.page_link` bruges.

Commit: `feat: grupperet navigation`

---

## 10 Standard-tilstand

Standardtilstanden adskiller sig på tre punkter, som i dag ikke fremgår af
skærmen. Gør dem eksplicitte i input-kolonnen under `ui.etiket("FASTE
FORUDSÆTNINGER")`:

| Forudsætning | Værdi |
|---|---|
| Friktionsvinkel φ | 37,0° |
| φ-korrektion | ingen |
| Materialelag | indgår ikke |

Med en forklaring nedenunder: *»I standardberegningen sættes bærelagets
friktionsvinkel φ = 37°, svarende til designmanualernes forudsætning. Der
beregnes derfor ingen φ-korrektion.«*

Resultatet viser tre søjler uden referencelinje, og produkttabellen bliver
hovedindholdet — grupperet efter serie med effektindeks:

```python
ui.produkttabel(raekker, grupperet=True)
```

Rækkefølgen af serier findes i `SERIE_ORDER` i `app.py`.

Commit: `feat: standard-tilstand med eksplicitte forudsætninger`

---

## 11 Tablet

Appen bruges primært på desktop, men må ikke gå i stykker på tablet.
Stylesheetets afsnit 13 lægger kolonnerne under hinanden under 1180 px. Kontroller
ved 1024 px bredde at:

- input-kolonnen ikke længere er sticky (den fylder hele bredden)
- snittene stadig kan læses — falder de under fire kolonner, så tillad vandret
  scroll i stedet for at klemme dem sammen
- alle klikbare elementer er mindst 44 px høje

Commit: `fix: tablet-visning`

---

## 12 Afslut

```bash
git push -u origin feature/ui-redesign-v04
```

Skriv til sidst en kort opsummering i chatten:

- hvilke trin der er gennemført
- hvad du valgte anderledes, og hvorfor
- hvad der mangler, eller hvad du er i tvivl om
- om nogen tal på skærmen har flyttet sig (må de ikke — kun formatering)

---

## Hvad du **ikke** skal gøre

- Ikke ændre i `core/` bortset fra talformatering og rapportens skrift/farver.
- Ikke tilføje nye afhængigheder ud over `plotly`.
- Ikke omdøbe eller flytte `session_state`-nøgler.
- Ikke skrive nye CSS-klasser i `app.py` — al styling hører i
  `assets/byggros_theme.css`.
- Ikke opfinde nye farver. Paletten står i stylesheetets `:root` og i
  `ui.FARVE`.
- Ikke slette den gamle matplotlib-kode til rapporten, før rapporten er
  gennemgået.
- Ikke merge til `main`. Mennesket beslutter det.

## Referencer i repoet

| Fil | Indhold |
|---|---|
| `handover/AENDRINGER.md` | den fulde designgennemgang, sektion for sektion |
| `ui.py` | præsentationslaget, docstrings på hver funktion |
| `assets/byggros_theme.css` | paletten og alle regler, nummererede afsnit |
| `CLAUDE.md` | skrivestil for al brugervendt tekst |
