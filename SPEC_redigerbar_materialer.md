# SPEC: Redigerbar materialeliste

## Kontekst
Appen er et Streamlit-baseret geonet-dimensioneringsværktøj (BG Byggros).
Relevante filer: `app.py`, `data.py` (samt `core/data.py` og `core/calculator.py` i modulstruktur).

---

## Mål
Menupunktet **🪨 Materialer** skal gøres redigerbart via `st.data_editor`.
Brugernes ændringer skal:
1. Persistere på tværs af sessioner (JSON-fil)
2. Slå igennem i selve beregningen (Brugerdefineret-tilstand → C. Materialelag)

---

## 1. Persistens-lag: JSON-fil

Opret `materialer_brugerdefineret.json` ved siden af `app.py`.

**Format:**
```json
[
  {
    "navn": "Bundsand",
    "lagtype": "Bundsikring",
    "phi": 35,
    "max_korn": 8,
    "anvendelse": "Bundlag, friktionsmateriale"
  },
  ...
]
```

**Hjælpefunktioner (tilføjes i `app.py` eller ny `core/storage.py`):**
```python
import json, os

MATERIALER_JSON = os.path.join(os.path.dirname(__file__), "materialer_brugerdefineret.json")

def indlæs_materialer() -> list[dict]:
    """Indlæs fra JSON. Fallback til MATERIAL_DB hvis filen ikke findes."""
    if os.path.exists(MATERIALER_JSON):
        with open(MATERIALER_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "navn": m["navn"],
            "lagtype": m["lagtype"],
            "phi": int(m["phi"]),
            "max_korn": int(m["max_korn"]) if m["max_korn"] else 0,
            "anvendelse": m["anvendelse"],
        }
        for m in MATERIAL_DB
    ]

def gem_materialer(materialer: list[dict]) -> None:
    with open(MATERIALER_JSON, "w", encoding="utf-8") as f:
        json.dump(materialer, f, ensure_ascii=False, indent=2)

def slet_json_og_nulstil() -> None:
    if os.path.exists(MATERIALER_JSON):
        os.remove(MATERIALER_JSON)
```

---

## 2. Session state — initialisering

Tilføj dette **én gang ved opstart** (øverst i `app.py`, efter imports):

```python
if "materialer" not in st.session_state:
    st.session_state["materialer"] = indlæs_materialer()
```

---

## 3. `render_materialer()` — ny implementation

Erstat den eksisterende funktion med:

```python
def render_materialer() -> None:
    import pandas as pd

    st.title("🪨 Materialer")
    st.caption("Redigér materialebasen. Ændringer gemmes automatisk og slår igennem i beregningen.")
    st.divider()

    # Knapper øverst
    kol_a, kol_b, kol_c = st.columns([1, 1, 4])
    with kol_a:
        if st.button("➕ Tilføj materiale", use_container_width=True):
            st.session_state["materialer"].append({
                "navn": "Nyt materiale",
                "lagtype": "Bærelag",
                "phi": 35,
                "max_korn": 32,
                "anvendelse": "",
            })
            gem_materialer(st.session_state["materialer"])
            st.rerun()

    with kol_b:
        if st.button("🔄 Nulstil til standard", use_container_width=True, type="secondary"):
            slet_json_og_nulstil()
            st.session_state["materialer"] = indlæs_materialer()
            st.rerun()

    # Data editor
    df = pd.DataFrame(st.session_state["materialer"])

    redigeret = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",          # tillader sletning via ×-knap
        column_config={
            "navn": st.column_config.TextColumn(
                "Materiale",
                required=True,
            ),
            "lagtype": st.column_config.SelectboxColumn(
                "Lagtype",
                options=["Bærelag", "Bundsikring"],
                required=True,
            ),
            "phi": st.column_config.NumberColumn(
                "φ (°)",
                min_value=20,
                max_value=60,
                step=1,
                format="%d",
                required=True,
            ),
            "max_korn": st.column_config.NumberColumn(
                "Max korn (mm)",
                min_value=0,
                max_value=500,
                step=1,
                format="%d",
                required=False,
            ),
            "anvendelse": st.column_config.TextColumn(
                "Anvendelse",
            ),
        },
        key="mat_editor",
    )

    # Gem ved ændringer
    ny_liste = redigeret.to_dict("records")
    # Sørg for at phi og max_korn er int
    for m in ny_liste:
        m["phi"] = int(m["phi"]) if m.get("phi") is not None else 35
        m["max_korn"] = int(m["max_korn"]) if m.get("max_korn") else None

    if ny_liste != st.session_state["materialer"]:
        st.session_state["materialer"] = ny_liste
        gem_materialer(ny_liste)
```

---

## 4. `find_materiale()` — opdatér opslag

Den eksisterende funktion i `data.py` bruger `MATERIAL_DB` (hardcoded).
I `app.py` skal den erstattes med en session-state baseret version:

```python
def _find_materiale_session(navn: str) -> dict | None:
    """Slår op i session_state['materialer'] i stedet for hardcoded MATERIAL_DB."""
    for m in st.session_state.get("materialer", []):
        if m["navn"] == navn:
            return m
    return None
```

Alle steder i `app.py` hvor `find_materiale(mat_navn)` kaldes (i `_input_materialelag()`),
erstattes med `_find_materiale_session(mat_navn)`.

---

## 5. `_input_materialelag()` — opdatér dropdown

Erstat:
```python
mat_navn = st.selectbox("Materiale", MATERIAL_NAVNE, key=f"bd_mat_{i}")
```

Med:
```python
dynamiske_navne = [m["navn"] for m in st.session_state.get("materialer", [])] + ["Manuel indtastning"]
mat_navn = st.selectbox("Materiale", dynamiske_navne, key=f"bd_mat_{i}")
```

Og erstat `find_materiale(mat_navn)` med `_find_materiale_session(mat_navn)`.

---

## 6. Graceful fallback

Hvis et gemt valg i en beregning ikke længere findes i den opdaterede liste
(fordi brugeren har slettet det), håndteres det i `_input_materialelag()`:

```python
md = _find_materiale_session(mat_navn)
if md is None:
    # Materiale er slettet — fald tilbage til manuel indtastning
    mat_navn = "Manuel indtastning"
    st.warning(f"Materialet '{mat_navn}' findes ikke længere i databasen. Skift til manuel.")
```

---

## 7. Hvad der IKKE skal ændres

- `data.py` / `MATERIAL_DB` forbliver uændret — bruges kun som fallback ved nulstilling
- `core/calculator.py` og `core/validators.py` behøver ingen ændringer
- `MATERIAL_NAVNE` i `data.py` bruges ikke længere direkte i UI (erstattes af dynamisk liste),
  men kan beholdes som reference

---

## Rækkefølge for implementering

1. Tilføj `indlæs_materialer()`, `gem_materialer()`, `slet_json_og_nulstil()` til `app.py`
2. Tilføj session state initialisering øverst i `app.py` (efter imports, før sidebar)
3. Tilføj `_find_materiale_session()` til `app.py`
4. Erstat `render_materialer()` med ny version
5. Opdatér `_input_materialelag()` — dropdown + opslag
6. Test: tilføj materiale → brug i beregning → nulstil → kontrollér fallback
