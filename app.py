"""
Geonet Dimensioneringsværktøj — Streamlit entrypoint.

Start med: streamlit run app.py
"""

# ---------------------------------------------------------------------------
# set_page_config SKAL stå som allerførste Streamlit-kald
# ---------------------------------------------------------------------------
import streamlit as st

st.set_page_config(
    page_title="Geonet Dimensionering",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports — efter set_page_config
# ---------------------------------------------------------------------------
import json
import os

from core.data import (
    BELASTNINGSKLASSER,
    GEONET_NAVNE,
    GEONET_DB,
    GEONET_NOTER,
    MATERIAL_DB,
    EU_MIN, EU_MAX,
    K_PHI,
    find_geonet,
    cv_til_eu,
    eo_til_klasse,
    T_BASIS_TABLE,
    DESIGNDIAGRAM_RAW_TABLES,
    EO_KOLONNER,
)
from core.calculator import (
    beregn,
    beregn_alle_produkter,
    grupper_produkter,
)
from core.validators import valider_input

# ---------------------------------------------------------------------------
# Redigerbare materialer
# ---------------------------------------------------------------------------
MATERIALER_JSON = os.path.join(
    os.path.dirname(__file__),
    "materialer_brugerdefineret.json",
)
DESIGNDIAGRAMMER_JSON = os.path.join(
    os.path.dirname(__file__),
    "designdiagrammer_brugerdefineret.json",
)
MIN_LAGTYKKELSE_MM = 100
MIN_TOTAL_OPBYGNING_MM = 200


def _standard_materialer() -> list[dict]:
    """Returner standardmaterialer i samme format som editoren gemmer."""
    return [
        {
            "navn": str(m.get("navn", "")).strip(),
            "lagtype": m.get("lagtype") or "Bærelag",
            "phi": int(m.get("phi") or 35),
            "max_korn": int(m["max_korn"]) if m.get("max_korn") else None,
            "anvendelse": str(m.get("anvendelse") or ""),
        }
        for m in MATERIAL_DB
    ]


def _er_tom_vaerdi(value) -> bool:
    if value is None:
        return True
    try:
        if value == "":
            return True
    except TypeError:
        pass
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return False


def _normaliser_materiale(raw: dict) -> dict | None:
    """Saniter en editor-række. Tomme navne droppes."""
    navn = str(raw.get("navn") or "").strip()
    if not navn:
        return None

    lagtype = raw.get("lagtype")
    if lagtype not in ("Bærelag", "Bundsikring"):
        lagtype = "Bærelag"

    try:
        phi = int(round(float(raw.get("phi"))))
    except (TypeError, ValueError):
        phi = 35
    phi = min(max(phi, 20), 60)

    max_korn_raw = raw.get("max_korn")
    if _er_tom_vaerdi(max_korn_raw):
        max_korn = None
    else:
        try:
            max_korn = int(round(float(max_korn_raw)))
        except (TypeError, ValueError):
            max_korn = None
        if max_korn is not None:
            max_korn = min(max(max_korn, 0), 500) or None

    return {
        "navn": navn,
        "lagtype": lagtype,
        "phi": phi,
        "max_korn": max_korn,
        "anvendelse": str(raw.get("anvendelse") or "").strip(),
    }


def _normaliser_materialer(materialer: list[dict]) -> list[dict]:
    resultat = []
    for materiale in materialer:
        normaliseret = _normaliser_materiale(materiale)
        if normaliseret is not None:
            resultat.append(normaliseret)
    return resultat


def _duplikerede_materialenavne(materialer: list[dict]) -> list[str]:
    set_navne: set[str] = set()
    duplikater: list[str] = []
    for materiale in materialer:
        navn = materiale["navn"]
        key = navn.casefold()
        if key in set_navne and navn not in duplikater:
            duplikater.append(navn)
        set_navne.add(key)
    return duplikater


def indlaes_materialer() -> list[dict]:
    """Indlæs brugerdefinerede materialer. Fallback til MATERIAL_DB."""
    if os.path.exists(MATERIALER_JSON):
        try:
            with open(MATERIALER_JSON, "r", encoding="utf-8") as f:
                materialer = _normaliser_materialer(json.load(f))
            if materialer and not _duplikerede_materialenavne(materialer):
                return materialer
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return _standard_materialer()


def gem_materialer(materialer: list[dict]) -> None:
    with open(MATERIALER_JSON, "w", encoding="utf-8") as f:
        json.dump(materialer, f, ensure_ascii=False, indent=2)


def slet_json_og_nulstil() -> None:
    if os.path.exists(MATERIALER_JSON):
        os.remove(MATERIALER_JSON)


def _standard_designdiagrammer() -> list[dict]:
    """Returner en frisk kopi af standard-diagramdata."""
    return json.loads(json.dumps(DESIGNDIAGRAM_RAW_TABLES))


def _diagramtal(value) -> float | None:
    if _er_tom_vaerdi(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normaliser_diagram_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    normaliserede: list[dict] = []
    fejl: list[str] = []
    eu_vaerdier: set[float] = set()

    for idx, row in enumerate(rows, start=1):
        eu = _diagramtal(row.get("eu", row.get("Eu (MPa)")))
        t_uarmeret = _diagramtal(row.get("t_uarmeret_cm", row.get("Uarmeret tykkelse (cm)")))
        t_1_lag = _diagramtal(row.get("t_1_lag_cm", row.get("1 lag tykkelse (cm)")))
        t_2_lag = _diagramtal(row.get("t_2_lag_cm", row.get("2 lag tykkelse (cm)")))

        if (
            eu is None
            and t_uarmeret is None
            and t_1_lag is None
            and t_2_lag is None
        ):
            continue

        if eu is None:
            fejl.append(f"Række {idx} mangler Eu.")
            continue

        if eu in eu_vaerdier:
            fejl.append(f"Eu {eu:g} MPa findes flere gange.")
            continue
        eu_vaerdier.add(eu)

        normaliserede.append({
            "eu": eu,
            "t_uarmeret_cm": t_uarmeret,
            "t_1_lag_cm": t_1_lag,
            "t_2_lag_cm": t_2_lag,
        })

    normaliserede.sort(key=lambda row: row["eu"])
    return normaliserede, fejl


def _normaliser_designdiagrammer(diagrammer: list[dict]) -> tuple[list[dict], list[str]]:
    standard_by_nr = {d["diagram_nr"]: d for d in DESIGNDIAGRAM_RAW_TABLES}
    normaliserede: list[dict] = []
    alle_fejl: list[str] = []

    for standard in DESIGNDIAGRAM_RAW_TABLES:
        nr = standard["diagram_nr"]
        raw = next((d for d in diagrammer if d.get("diagram_nr") == nr), standard)
        rows, fejl = _normaliser_diagram_rows(raw.get("rows", []))
        if fejl:
            alle_fejl.extend([f"Diagram {nr}: {tekst}" for tekst in fejl])
        normaliserede.append({
            "diagram_nr": nr,
            "eo": standard_by_nr[nr]["eo"],
            "klasse": standard_by_nr[nr]["klasse"],
            "image_name": standard_by_nr[nr]["image_name"],
            "rows": rows,
        })

    return normaliserede, alle_fejl


def indlaes_designdiagrammer() -> list[dict]:
    """Indlæs brugerredigerede diagramdata. Fallback til standarddata."""
    if os.path.exists(DESIGNDIAGRAMMER_JSON):
        try:
            with open(DESIGNDIAGRAMMER_JSON, "r", encoding="utf-8") as f:
                diagrammer, fejl = _normaliser_designdiagrammer(json.load(f))
            if not fejl:
                return diagrammer
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return _standard_designdiagrammer()


def gem_designdiagrammer(diagrammer: list[dict]) -> None:
    with open(DESIGNDIAGRAMMER_JSON, "w", encoding="utf-8") as f:
        json.dump(diagrammer, f, ensure_ascii=False, indent=2)


def slet_designdiagrammer_json_og_nulstil() -> None:
    if os.path.exists(DESIGNDIAGRAMMER_JSON):
        os.remove(DESIGNDIAGRAMMER_JSON)


def generer_t_basis_table_fra_diagrammer(diagrammer: list[dict]) -> dict:
    """Byg T_BASIS_TABLE-kompatibel tabel direkte fra diagramdata."""
    table: dict = {}
    tom = {"uarmeret": None, "1_lag": None, "2_lag": None}

    for diagram in diagrammer:
        eo = diagram["eo"]
        for row in diagram.get("rows", []):
            eu = row["eu"]
            table.setdefault(eu, {})
            table[eu][eo] = {
                "uarmeret": row.get("t_uarmeret_cm"),
                "1_lag": row.get("t_1_lag_cm"),
                "2_lag": row.get("t_2_lag_cm"),
            }

    for eu_data in table.values():
        for eo in EO_KOLONNER:
            eu_data.setdefault(eo, tom.copy())

    return {eu: table[eu] for eu in sorted(table)}


def _opdater_aktiv_t_basis_table() -> None:
    st.session_state["aktiv_t_basis_table"] = generer_t_basis_table_fra_diagrammer(
        st.session_state["designdiagrammer"]
    )


def _aktiv_t_basis_table() -> dict:
    return st.session_state.get("aktiv_t_basis_table", T_BASIS_TABLE)


def _diagrammer_har_aktuel_schema(diagrammer: list[dict]) -> bool:
    return all(
        all("eu" in row for row in diagram.get("rows", []))
        for diagram in diagrammer
    )


def _find_materiale_session(navn: str) -> dict | None:
    """Slå materiale op i den redigerbare session-liste."""
    for materiale in st.session_state.get("materialer", []):
        if materiale["navn"] == navn:
            return materiale
    return None


if "materialer" not in st.session_state:
    st.session_state["materialer"] = indlaes_materialer()
diagrammer_genindlaest = False
if (
    "designdiagrammer" not in st.session_state
    or not _diagrammer_har_aktuel_schema(st.session_state["designdiagrammer"])
):
    st.session_state["designdiagrammer"] = indlaes_designdiagrammer()
    diagrammer_genindlaest = True
if "aktiv_t_basis_table" not in st.session_state or diagrammer_genindlaest:
    _opdater_aktiv_t_basis_table()

# ---------------------------------------------------------------------------
# Farvepalette
# ---------------------------------------------------------------------------
GRØN   = "#2E7D32"
GUL    = "#F9A825"
RØD    = "#C62828"
GRÅ    = "#9E9E9E"
LYS_GR = "#E8F5E9"

# ---------------------------------------------------------------------------
# Serie-sortering til standard-oversigten
# ---------------------------------------------------------------------------
SERIE_ORDER = {"Reference": 0, "Tensar": 1, "GS-GRID": 2, "E'GRID": 3, "Manuel": 4}
REFERENCE_NAVN = "Referencenet (SX160 / T6 / TX160)"
REFERENCE_KLASSER = [3, 4, 5, 6]

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

  .res-kort {{
    background: {LYS_GR};
    border-left: 5px solid {GRØN};
    border-radius: 6px;
    padding: 1rem 1.25rem 0.75rem;
    margin-bottom: 0.5rem;
  }}
  .res-tal   {{ font-size: 2.2rem; font-weight: 700; color: {GRØN}; line-height: 1.1; }}
  .res-label {{ font-size: 0.78rem; color: #555; text-transform: uppercase;
                letter-spacing: 0.06em; margin-bottom: 0.15rem; }}
  .uarm-tal  {{ font-size: 1.5rem; font-weight: 600; color: {GRÅ}; }}

  .boks-fejl  {{ background:#FFEBEE; border-left:4px solid {RØD};
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}
  .boks-adv   {{ background:#FFF8E1; border-left:4px solid {GUL};
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}
  .boks-tip   {{ background:#E3F2FD; border-left:4px solid #1565C0;
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}

  .uarm-banner {{
    background:#F5F5F5; border-left:5px solid {GRÅ};
    border-radius:6px; padding:0.75rem 1.25rem; margin-bottom:1rem;
  }}
  .uarm-banner-label {{ font-size:0.78rem; color:#555; text-transform:uppercase;
                        letter-spacing:0.06em; }}
  .uarm-banner-tal   {{ font-size:1.8rem; font-weight:700; color:{GRÅ};
                        line-height:1.1; }}

  .gruppe-kort {{
    background:{LYS_GR}; border-left:5px solid {GRØN};
    border-radius:6px; padding:0.75rem 1rem; margin:0.4rem 0 0.6rem 0;
  }}
  .gruppe-kort-rest {{
    background:#FAFAFA; border-left:4px solid {GRÅ};
    border-radius:6px; padding:0.6rem 0.9rem; margin:0.3rem 0;
  }}
  .gruppe-tal {{ font-size:1.6rem; font-weight:700; color:{GRØN}; line-height:1.1; }}
  .gruppe-tal-rest {{ font-size:1.15rem; font-weight:600; color:#444; line-height:1.1; }}
  .gruppe-red {{ font-size:0.9rem; color:#555; margin-left:0.5rem; }}
  .gruppe-red-linje {{ font-size:0.95rem; font-weight:600; color:{GRØN};
                       margin-top:0.05rem; margin-bottom:0.1rem; }}
  .gruppe-serie {{ font-size:0.88rem; margin-top:0.35rem; }}
  .gruppe-serie b {{ color:#333; }}

  /* Net-korrektionslinjer i gruppe-kort */
  .net-kor-spar {{
    font-size:0.82rem; font-weight:500; color:#1565C0;
    margin:0.1rem 0 0.05rem;
  }}
  .net-kor-pen {{
    font-size:0.82rem; font-weight:500; color:#BF360C;
    margin:0.1rem 0 0.05rem;
  }}
  .net-kor-ref {{
    font-size:0.80rem; color:{GRÅ}; font-style:italic;
    margin:0.1rem 0 0.05rem;
  }}
  .klasse-ok {{
    font-size:0.80rem; color:#555;
    margin:0.25rem 0 0.05rem;
  }}
  .klasse-advarsel {{
    font-size:0.80rem; font-weight:500; color:#BF360C;
    margin:0.25rem 0 0.05rem;
  }}
  .bedste-label {{
    font-size:0.7rem; color:{GRØN}; text-transform:uppercase;
    letter-spacing:0.08em; font-weight:600; margin:0.1rem 0 0.1rem 0;
  }}
  .kol-titel {{
    font-size:0.95rem; font-weight:700; color:#333;
    border-bottom:2px solid {GRØN}; padding-bottom:0.25rem;
    margin-bottom:0.4rem;
  }}

  .diagram-række-afstand {{
    height: 1.8rem;
  }}

  hr {{ margin: 0.75rem 0; }}

  /* ─── Sidebar ─────────────────────────────────────────── */
  [data-testid="stSidebar"] {{
    background: #FFFFFF;
    border-right: 1px solid #E0E0E0;
  }}
  [data-testid="stSidebarContent"] > div:first-child {{
    padding-top: 0 !important;
  }}

  .sb-header {{
    padding: 1.4rem 1.1rem 1.1rem;
    border-bottom: 1px solid #EEEEEE;
    margin-bottom: 0.6rem;
  }}
  .sb-logo {{
    font-size: 1.6rem;
    line-height: 1;
    margin-bottom: 0.3rem;
  }}
  .sb-title {{
    font-size: 0.78rem;
    font-weight: 700;
    color: #222;
    text-transform: uppercase;
    letter-spacing: 0.09em;
  }}
  .sb-sub {{
    font-size: 0.7rem;
    color: #AAA;
    margin-top: 0.15rem;
  }}

  [data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #555 !important;
    padding: 0.6rem 1.1rem !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    letter-spacing: 0.01em;
  }}
  [data-testid="stSidebar"] .stButton > button:hover {{
    background: #F5F5F5 !important;
    color: {GRØN} !important;
    border-left-color: #C8E6C9 !important;
  }}
  [data-testid="stSidebar"] .stButton > button[kind="primaryFormSubmit"],
  [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: {LYS_GR} !important;
    color: {GRØN} !important;
    border-left: 3px solid {GRØN} !important;
    font-weight: 700 !important;
  }}

  .sb-divider {{
    border: none;
    border-top: 1px solid #EEEEEE;
    margin: 0.5rem 0;
  }}

  .sb-footer {{
    padding: 0 1.1rem;
    font-size: 0.7rem;
    color: #BBB;
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
  }}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hjælpefunktioner til bokse
# ---------------------------------------------------------------------------

def _boks(css_klasse: str, ikon: str, tekst: str):
    st.markdown(
        f'<div class="{css_klasse}">{ikon} {tekst}</div>',
        unsafe_allow_html=True,
    )

def vis_fejl(tekst: str):        _boks("boks-fejl", "⛔", tekst)
def vis_advarsel(tekst: str):    _boks("boks-adv",  "⚠️", tekst)
def vis_anbefaling(tekst: str):  _boks("boks-tip",  "💡", tekst)

# ---------------------------------------------------------------------------
# Belastningsklasse-ikoner
# ---------------------------------------------------------------------------
KLASSE_IKON = {1: "🚲", 2: "🚜", 3: "🚗", 4: "🚛", 5: "🏗️", 6: "✈️"}


# ===========================================================================
# Fælles input-widgets (genbruges på tværs af tilstande)
# ===========================================================================

def input_underbund(key_prefix: str) -> float:
    """Render A. Underbund (Eu eller Cv → Eu). Returnerer Eu i MPa."""
    st.subheader("A. Underbund")

    eu_mode = st.radio(
        "Input-form",
        ["Eu — E-modul (MPa)", "Cv — vingestyrke (kN/m²)"],
        horizontal=True,
        key=f"{key_prefix}_eu_mode",
        label_visibility="collapsed",
    )

    if eu_mode.startswith("Eu"):
        eu = float(st.slider(
            "Eu (MPa)", min_value=int(EU_MIN), max_value=int(EU_MAX),
            value=10, step=1, key=f"{key_prefix}_eu_slider",
            help="Underbundens E-modul. Lavere Eu = blødere bund = tykkere bærelag.",
        ))
        st.caption(f"Valgt **Eu = {eu:.0f} MPa**")
        return eu

    cv = st.slider(
        "Cv (kN/m²)", min_value=0, max_value=180,
        value=60, step=5, key=f"{key_prefix}_cv_slider",
        help="Ukorrigeret vingerstyrke fra feltmåling (tabel 7.4).",
    )
    eu_opslag = cv_til_eu(float(cv))
    if eu_opslag is None:
        st.error("Cv er uden for tabelområdet (0–180 kN/m²).")
        return 10.0
    st.caption(f"Cv = {cv} kN/m²  →  **Eu = {eu_opslag:.0f} MPa**")
    return eu_opslag


def input_belastning(key_prefix: str) -> tuple[int, dict, float]:
    """Render B. Belastningsklasse som 6 klasse-knapper. Returnerer (klasse, info, eo)."""
    st.subheader("B. Belastningsklasse")

    state_key = f"{key_prefix}_valgt_klasse"
    if state_key not in st.session_state:
        st.session_state[state_key] = 4

    kol_knapper, kol_diagram, _kol_luft = st.columns([1.1, 0.95, 0.45], gap="large")
    with kol_knapper:
        kl_cols = st.columns(2)
        for kl_nr, kl_data in BELASTNINGSKLASSER.items():
            with kl_cols[(kl_nr - 1) % 2]:
                aktiv = st.session_state[state_key] == kl_nr
                if st.button(
                    f"{KLASSE_IKON[kl_nr]}\n**{kl_nr}**",
                    key=f"{key_prefix}_kl_{kl_nr}",
                    type="primary" if aktiv else "secondary",
                    width="stretch",
                    help=f"Klasse {kl_nr}: {kl_data['anvendelse']}",
                ):
                    st.session_state[state_key] = kl_nr
                    st.rerun()

    valgt = st.session_state[state_key]
    info  = BELASTNINGSKLASSER[valgt]
    eo    = float(info["eo"])
    with kol_knapper:
        st.caption(
            f"**Klasse {valgt}** · {info['belastning']} · "
            f"Eo = {eo:.0f} MPa · _{info['anvendelse']}_"
        )
    with kol_diagram:
        diagram = next(
            (
                d for d in st.session_state.get("designdiagrammer", [])
                if d["klasse"] == valgt
            ),
            None,
        )
        if diagram:
            image_path = os.path.join(
                os.path.dirname(__file__),
                "diagrambilleder",
                diagram["image_name"],
            )
            st.image(image_path, width="stretch")
    return valgt, info, eo


# ===========================================================================
# STANDARD-TILSTAND — produktoversigt
# ===========================================================================

def _sort_produkter(produkter: list[dict]) -> list[dict]:
    """Sortér produkter inden for en gruppe: serie først, derefter navn."""
    return sorted(
        produkter,
        key=lambda p: (SERIE_ORDER.get(p["serie"], 99), p["navn"]),
    )


def _filter_klasse_anbefalede(grupper: list[dict]) -> list[dict]:
    """
    Returnér kun gyldige grupper (har_fejl=False) hvor klasse-anbefalede
    produkter er beholdt. Manuel-produktet og produkter uden for valgt
    klasse fjernes helt. Grupper der ender tomme droppes.
    """
    resultat: list[dict] = []
    for g in grupper:
        if g["har_fejl"]:
            continue
        beholdt = [
            p for p in g["produkter"]
            if p["klasse_ok"] and p["navn"] != "Anden armering (manuel)"
        ]
        if beholdt:
            resultat.append({**g, "produkter": beholdt})
    return resultat


def _gyldige_grupper(grupper: list[dict]) -> list[dict]:
    """Behold kun grupper med gyldig beregning, uden klassefiltrering."""
    return [g for g in grupper if not g.get("har_fejl")]


def _format_klasse_liste(klasser: list[int]) -> str:
    return ", ".join(str(k) for k in sorted(klasser))


def _klasse_linjer_html(produkter: list[dict], valgt_klasse: int | None) -> str:
    if valgt_klasse is None:
        return ""

    linjer: list[str] = []
    for p in _sort_produkter(produkter):
        klasser = p.get("klasser") or []
        kl_txt = _format_klasse_liste(klasser)
        css = "klasse-ok" if p.get("klasse_ok") else "klasse-advarsel"
        prefix = "Anbefalet" if p.get("klasse_ok") else "Ikke anbefalet til valgt klasse"
        linjer.append(
            f'<div class="{css}">{p["navn"]}: {prefix} · klasser {kl_txt}</div>'
        )
    return "".join(linjer)


def _render_gruppe_kort(
    gruppe: dict,
    primaer: bool,
    phi: float = 35.0,
    valgt_klasse: int | None = None,
) -> None:
    """
    Render én tykkelses-gruppe som kort.
    primaer=True ⇒ fremhævet grønt kort (bedste). False ⇒ dæmpet grå variant.
    """
    t_vis   = gruppe["t_armeret_mm"]
    red_pct = gruppe["reduktion_pct"]

    # Hent t_uarmeret fra første produkt (alle i gruppen har samme uarmerede tykkelse)
    t_uarm_prod = (
        gruppe["produkter"][0].get("t_uarmeret_mm")
        if gruppe.get("produkter") else None
    )

    # Interval-produkter (fx NX750/NX850): vises i egen gruppe med spænd.
    # Efter grupper_produkter() er en interval-gruppe altid mono-produkt, så
    # vi læser tallene direkte fra det ene produkt.
    interval_p = (
        gruppe["produkter"][0]
        if gruppe.get("produkter")
        and gruppe["produkter"][0].get("t_armeret_mm_min") is not None
        else None
    )
    if interval_p is not None:
        t_low_vis = round(interval_p["t_armeret_mm_min"])
        t_high_vis = round(interval_p["t_armeret_mm_max"])
        if t_low_vis == t_high_vis:
            tal_html = f'{t_high_vis:.0f} mm'
        else:
            tal_html = (
                f'{t_low_vis:.0f}–{t_high_vis:.0f} mm'
                f'<span style="font-size:0.55em;font-weight:400;color:#555;'
                f'margin-left:8px">(største–laveste effektindeks)</span>'
            )
    else:
        t_low_vis = None
        t_high_vis = round(t_vis)
        tal_html = f'{t_vis:.0f} mm'

    # ↓ mm-reduktionslinje
    if interval_p is not None and t_uarm_prod is not None and t_low_vis is not None:
        red_mm_best = round(t_uarm_prod - t_low_vis)    # største reduktion (best case)
        red_mm_kons = round(t_uarm_prod - t_high_vis)   # mindste reduktion (konservativ)
        red_pct_best = red_mm_best / t_uarm_prod if t_uarm_prod > 0 else 0
        red_pct_kons = red_mm_kons / t_uarm_prod if t_uarm_prod > 0 else 0
        if t_low_vis == t_high_vis:
            red_linje = (
                f'<div class="gruppe-red-linje">'
                f'Reduceres ↓ {red_mm_best} mm ({red_pct_best:.0%})'
                f'</div>'
            )
        else:
            red_linje = (
                f'<div class="gruppe-red-linje">'
                f'Reduceres ↓ {red_mm_best} mm ({red_pct_best:.0%}) '
                f'/ {red_mm_kons} mm ({red_pct_kons:.0%})'
                f'</div>'
            )
    elif t_uarm_prod is not None and red_pct is not None:
        red_mm = round(t_uarm_prod - t_vis)
        red_pct_str = f"{red_pct:.0%}"
        red_linje = (
            f'<div class="gruppe-red-linje">Reduceres ↓ {red_mm} mm ({red_pct_str})</div>'
        )
    else:
        red_linje = ""

    # φ-korrektionslinje — vises kun hvis phi ≠ 35°
    phi_kor_html = ""
    t_basis = gruppe.get("t_basis_arm_mm")
    if t_basis and t_basis > 0 and abs(phi - 35.0) > 0.05:
        phi_kor = -0.02 * (phi - 35.0)
        phi_kor_mm = round(t_basis * phi_kor)
        abs_mm = abs(phi_kor_mm)
        pct = abs(round(phi_kor * 100))
        phi_str = f"{phi:.1f}".replace(".", ",")
        if phi_kor < 0:
            phi_kor_html = (
                f'<div class="net-kor-spar">'
                f'φ-kor: \u2212{abs_mm} mm (\u2212{pct}\u00a0%) · φ = {phi_str}°'
                f'</div>'
            )
        else:
            phi_kor_html = (
                f'<div class="net-kor-pen">'
                f'φ-kor: +{abs_mm} mm (+{pct}\u00a0%) · φ = {phi_str}°'
                f'</div>'
            )

    # ↕ net-korrektionslinje — viser delta ift. referenceprodukt (kor=0)
    # t_basis er fælles for alle produkter i gruppen (samme eu/eo/lag_mode)
    net_kor_html = ""
    t_basis = gruppe.get("t_basis_arm_mm")
    if t_basis and t_basis > 0 and gruppe.get("produkter"):
        kor_vaerdier: set[float] = set()
        for p in gruppe["produkter"]:
            if p.get("korrektion_min") is not None:
                kor_vaerdier.add(p["korrektion_min"])
                kor_vaerdier.add(p["korrektion_max"])
            else:
                kor_vaerdier.add(p["korrektion"])
        korrektioner = sorted(kor_vaerdier)
        kor_min = korrektioner[0]
        kor_max = korrektioner[-1]
        # Skelnetegn: interval-produkter bruger "/", andre blandede grupper bruger "til"
        interval_separator = (
            interval_p is not None and t_low_vis is not None and t_low_vis != t_high_vis
        )
        delta_min = round(t_basis * kor_min)  # mm; negativ = sparer, positiv = koster mere
        delta_max = round(t_basis * kor_max)

        if abs(kor_min) < 0.005 and abs(kor_max) < 0.005:
            # Referenceprodukt(er)
            net_kor_html = '<div class="net-kor-ref">referenceprodukt (0 % korrektion)</div>'
        elif abs(kor_min - kor_max) < 0.005:
            # Alle produkter i gruppen har samme korrektion
            delta = delta_min
            pct = int(round(abs(kor_min) * 100))
            abs_delta = abs(delta)
            if kor_min < 0:
                net_kor_html = (
                    f'<div class="net-kor-spar">'
                    f'net-kor: −{abs_delta} mm (−{pct} %) ift. reference'
                    f'</div>'
                )
            else:
                net_kor_html = (
                    f'<div class="net-kor-pen">'
                    f'net-kor: +{abs_delta} mm (+{pct} %) ift. reference'
                    f'</div>'
                )
        else:
            # Blandet gruppe — vis interval. Interval-produkter bruger
            # "best-case / konservativ, ift. reference"; andre blandede
            # grupper bruger den klassiske "{d_lo} til {d_hi}"-syntaks.
            d_lo, d_hi = delta_min, delta_max
            if d_hi <= 0:
                css = "net-kor-spar"
            elif d_lo >= 0:
                css = "net-kor-pen"
            else:
                css = "net-kor-ref"
            if interval_separator:
                pct_lo = int(round(kor_min * 100))
                pct_hi = int(round(kor_max * 100))
                tekst = (
                    f'net-kor: {d_lo:+d} mm ({pct_lo:+d}%) / '
                    f'{d_hi:+d} mm ({pct_hi:+d}%), ift. reference'
                )
            elif d_lo >= 0:
                tekst = f'net-kor: +{d_lo} til +{d_hi} mm ift. reference'
            else:
                tekst = f'net-kor: {d_lo:+d} til {d_hi:+d} mm ift. reference'
            net_kor_html = f'<div class="{css}">{tekst}</div>'

    pr_serie: dict[str, list[dict]] = {}
    for p in _sort_produkter(gruppe["produkter"]):
        pr_serie.setdefault(p["serie"], []).append(p)

    serie_linjer: list[str] = []
    for serie in sorted(pr_serie.keys(), key=lambda s: SERIE_ORDER.get(s, 99)):
        navne = [p["navn"].replace(f"{serie} ", "", 1) for p in pr_serie[serie]]
        serie_linjer.append(
            f'<div class="gruppe-serie"><b>{serie}:</b> {", ".join(navne)}</div>'
        )
    klasse_linjer = _klasse_linjer_html(gruppe.get("produkter", []), valgt_klasse)

    kort_css = "gruppe-kort" if primaer else "gruppe-kort-rest"
    tal_css  = "gruppe-tal"  if primaer else "gruppe-tal-rest"

    st.markdown(
        f'<div class="{kort_css}">'
        f'<span class="{tal_css}">{tal_html}</span>'
        f'{red_linje}'
        f'{phi_kor_html}'
        f'{net_kor_html}'
        f'{"".join(serie_linjer)}'
        f'{klasse_linjer}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _resultat_til_gruppe(
    res: dict, geonet: dict, valgt_klasse: int
) -> dict | None:
    """
    Pak et enkelt beregn()-resultat ind i samme dict-struktur som
    grupper_produkter()-output, så det kan vises med _render_gruppe_kort.

    Returnerer None hvis beregningen fejlede.
    """
    if res.get("fejl") or res.get("t_armeret_mm") is None:
        return None

    t_eks = res["t_armeret_mm"]
    t_uarm = res["t_uarmeret_mm"]
    red_eks = (t_uarm - t_eks) / t_uarm if t_uarm else None

    produkt = {
        "navn":           geonet["navn"],
        "serie":          geonet["serie"],
        "korrektion":     geonet["korrektion"],
        "t_armeret_mm":   t_eks,
        "t_uarmeret_mm":  t_uarm,
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "reduktion_mm":   t_uarm - t_eks if t_uarm is not None else None,
        "reduktion_pct":  red_eks,
        "klasse_ok":      valgt_klasse in geonet["klasser"],
        "klasser":        geonet["klasser"],
        "min_daklag":     geonet["min_daklag"],
        "max_korn":       geonet["max_korn"],
        "fejl":           None,
    }
    return {
        "t_armeret_mm":         round(t_eks, 0),
        "t_armeret_eksakt_mm":  round(t_eks, 0),
        "reduktion_pct":        round(red_eks, 4) if red_eks is not None else None,
        "reduktion_pct_eksakt": round(red_eks, 4) if red_eks is not None else None,
        "t_basis_arm_mm":       res.get("t_basis_arm_mm"),
        "produkter":            [produkt],
        "har_fejl":             False,
        "fejl_besked":          None,
    }


def _reference_resultat_til_gruppe(res: dict, valgt_klasse: int) -> dict | None:
    """Pak neutral referenceberegning som en gruppe til referencevisning."""
    if res.get("fejl") or res.get("t_armeret_mm") is None:
        return None

    t_ref = res["t_armeret_mm"]
    t_uarm = res["t_uarmeret_mm"]
    red_ref = (t_uarm - t_ref) / t_uarm if t_uarm else None
    produkt = {
        "navn": REFERENCE_NAVN,
        "serie": "Reference",
        "korrektion": 0.0,
        "t_armeret_mm": t_ref,
        "t_uarmeret_mm": t_uarm,
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "reduktion_mm": t_uarm - t_ref if t_uarm is not None else None,
        "reduktion_pct": red_ref,
        "klasse_ok": valgt_klasse in REFERENCE_KLASSER,
        "klasser": REFERENCE_KLASSER,
        "min_daklag": None,
        "max_korn": None,
        "fejl": None,
    }
    return {
        "t_armeret_mm": round(t_ref, 0),
        "t_armeret_eksakt_mm": round(t_ref, 0),
        "reduktion_pct": round(red_ref, 4) if red_ref is not None else None,
        "reduktion_pct_eksakt": round(red_ref, 4) if red_ref is not None else None,
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "produkter": [produkt],
        "har_fejl": False,
        "fejl_besked": None,
    }


def _beregn_referencegrupper(
    eu: float,
    eo: float,
    phi: float,
    valgt_klasse: int,
    t_basis_table: dict | None,
) -> tuple[dict | None, dict | None, str | None, str | None]:
    res_1 = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=0.0,
        lag_mode="1_lag", t_basis_table=t_basis_table,
    )
    res_2 = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=0.0,
        lag_mode="2_lag", t_basis_table=t_basis_table,
    )
    return (
        _reference_resultat_til_gruppe(res_1, valgt_klasse),
        _reference_resultat_til_gruppe(res_2, valgt_klasse),
        res_1.get("fejl"),
        res_2.get("fejl"),
    )


def _render_referenceblok(
    ref_1: dict | None,
    ref_2: dict | None,
    fejl_1: str | None,
    fejl_2: str | None,
    valgt_klasse: int,
    phi: float = 35.0,
) -> None:
    st.markdown("**Referencenet (SX160 / T6 / TX160)**")
    if valgt_klasse not in REFERENCE_KLASSER:
        st.warning(
            "Referencenettet er ikke anbefalet til den valgte belastningsklasse. "
            f"Referenceprodukterne er anbefalet til klasse {_format_klasse_liste(REFERENCE_KLASSER)}."
        )

    col_1, col_2 = st.columns(2, gap="large")
    with col_1:
        st.markdown('<div class="kol-titel">1 LAG REFERENCENET</div>', unsafe_allow_html=True)
        if ref_1 is not None:
            _render_gruppe_kort(ref_1, primaer=True, phi=phi, valgt_klasse=valgt_klasse)
        else:
            st.info(fejl_1 or "Ingen gyldigt 1-lag-resultat for referencenettet.")
    with col_2:
        st.markdown('<div class="kol-titel">2 LAG REFERENCENET</div>', unsafe_allow_html=True)
        if ref_2 is not None:
            _render_gruppe_kort(ref_2, primaer=True, phi=phi, valgt_klasse=valgt_klasse)
        else:
            st.info(fejl_2 or "Ingen gyldigt 2-lag-resultat for referencenettet.")


def _render_uarmeret_mangler_besked(eu: float, eo: float) -> None:
    st.warning(
        "Der er ikke defineret nogen uarmeret bærelagstykkelse for "
        f"det valgte Eu/Eo ({eu:.0f} MPa / {eo:.0f} MPa). "
        "Armerede resultater vises stadig, hvor designdiagrammet har data."
    )


def _render_lag_kolonne(
    titel: str,
    grupper: list[dict],
    valgt_klasse: int,
    lag_mode: str,
    tom_besked: str | None = None,
    phi: float = 35.0,
) -> None:
    """
    Render én kolonne (1-lag eller 2-lag): bedste gruppe øverst,
    øvrige skjult i en expander nedenunder.

    tom_besked: tilpasset besked når grupper er tomme (overstyrer default).
    """
    st.markdown(f'<div class="kol-titel">{titel}</div>', unsafe_allow_html=True)

    if not grupper:
        if tom_besked is not None:
            st.info(tom_besked)
        elif lag_mode == "2_lag":
            st.info(
                f"Designdiagrammet definerer ikke 2-lag-værdier for "
                f"kombinationen af det valgte Eu og klasse {valgt_klasse}. "
            )
        else:
            st.info(
                f"Ingen produkter giver et gyldigt 1-lag-resultat for "
                f"kombinationen af det valgte Eu og klasse {valgt_klasse}. "
                f"Prøv en anden belastningsklasse eller justér Eu."
            )
        return

    grupper_sorteret = sorted(grupper, key=lambda g: g["t_armeret_eksakt_mm"])
    bedste = grupper_sorteret[0]
    rest   = grupper_sorteret[1:]

    st.markdown('<div class="bedste-label">Armeret bærelagstykkelse</div>',
                unsafe_allow_html=True)
    _render_gruppe_kort(bedste, primaer=True, phi=phi, valgt_klasse=valgt_klasse)

    if rest:
        label = (
            f"Vis {len(rest)} flere mulighed"
            f"{'er' if len(rest) > 1 else ''}"
        )
        with st.expander(label, expanded=False):
            for g in rest:
                _render_gruppe_kort(g, primaer=False, phi=phi, valgt_klasse=valgt_klasse)


def _navne_kort(gruppe: dict) -> str:
    """Format produktnavne i en bedste-gruppe: '<navn>' eller '<navn> m.fl.'"""
    navne = [p["navn"] for p in gruppe["produkter"]]
    if len(navne) == 1:
        return navne[0]
    return f"{navne[0]} m.fl."


def _advarsel_med_lagtekst(advarsel: str, lag_mode: str) -> str:
    """Tilføj lag-kontekst til advarsler der kun gælder én lag-mode."""
    lagtekst = "ved 1 lag geonet" if lag_mode == "1_lag" else "ved 2 lag geonet"
    if lagtekst in advarsel or "1 lag geonet" in advarsel or "2 lag geonet" in advarsel:
        return advarsel
    if "minimumtykkelse" in advarsel and " mm). " in advarsel:
        return advarsel.replace(" mm). ", f" mm) {lagtekst}. ", 1)
    if advarsel.endswith("."):
        return f"{advarsel[:-1]} {lagtekst}."
    return f"{advarsel} {lagtekst}"


def _samme_produkter(g1: dict | None, g2: dict | None) -> bool:
    """True hvis to grupper indeholder præcis det samme sæt produktnavne."""
    if g1 is None or g2 is None:
        return False
    n1 = {p["navn"] for p in g1["produkter"]}
    n2 = {p["navn"] for p in g2["produkter"]}
    return n1 == n2


def _krav_for_gruppe(gruppe: dict) -> tuple[str, str, str]:
    """
    Returner (navne, min_dæklag_str, max_korn_str) for visning af
    udførelseskrav for produkterne i en bedste-gruppe.

    Hvis alle produkter har samme værdi vises kun det ene tal.
    Hvis de varierer vises et interval med en lille forklaring.
    """
    produkter = gruppe["produkter"]
    navne = ", ".join(p["navn"] for p in produkter)

    # min_daklag er i cm i GEONET_DB → konvertér til mm
    dk_unik = sorted({p["min_daklag"] * 10 for p in produkter})
    if len(dk_unik) == 1:
        dk_str = f"{dk_unik[0]} mm"
    else:
        dk_str = f"{dk_unik[0]}–{dk_unik[-1]} mm (varierer pr. produkt)"

    korn_alle = [p["max_korn"] for p in produkter]
    korn_unik = sorted({k for k in korn_alle if k is not None})
    har_none = any(k is None for k in korn_alle)

    if not korn_unik:
        korn_str = "ikke specificeret (kontakt leverandør)"
    elif len(korn_unik) == 1 and not har_none:
        korn_str = f"{korn_unik[0]} mm"
    else:
        rng = (
            f"{korn_unik[0]}–{korn_unik[-1]}"
            if len(korn_unik) > 1 else f"{korn_unik[0]}"
        )
        if har_none:
            korn_str = f"{rng} mm (visse produkter ikke specificeret)"
        else:
            korn_str = f"{rng} mm (varierer pr. produkt)"

    return navne, dk_str, korn_str


def _opbygnings_snit_svg(
    titel: str,
    t_baerelag_mm: float | None,
    mm_per_px: float,
    eu: float,
    geonet_y_fracs: list[float],
    *,
    geonet_label: str = "Tensar TriAx 160 / GS-GRID SX160 / E'GRID T6",
    ikke_defineret: str | None = None,
    max_baerelag_px: int = 220,
    best_case_mm: float | None = None,
) -> str:
    """Render et enkelt opbygnings-snit som inline SVG.

    Alle snit har samme total-højde (TITEL_H + max_baerelag_px + UNDERBUND_H
    + BUND_MARGIN), så underbundens bund ligger på samme y-koordinat
    i alle kolonner — bund-justeret layout.

    geonet_y_fracs er liste af y-positioner (0.0 = top af bærelag,
    1.0 = bund af bærelag) hvor geonet-linjer skal tegnes.

    ikke_defineret: hvis sat, vises i stedet for et faktisk snit
    (fx når uarmeret er udenfor tabelområdet).
    """
    BOX_X1, BOX_X2 = 78, 252
    BOX_W = BOX_X2 - BOX_X1
    TITEL_H = 26
    UNDERBUND_H = 56
    BUND_MARGIN = 26

    # Fælles total-højde og underbund-position på tværs af alle snit.
    h_total = TITEL_H + max_baerelag_px + UNDERBUND_H + BUND_MARGIN
    underbund_y1 = TITEL_H + max_baerelag_px
    underbund_y2 = underbund_y1 + UNDERBUND_H

    titel_html = (
        f'<text x="{(BOX_X1 + BOX_X2) / 2}" y="16" '
        f'font-family="system-ui, sans-serif" font-size="13" '
        f'font-weight="600" fill="#333" text-anchor="middle">{titel}</text>'
    )

    if ikke_defineret is not None or t_baerelag_mm is None:
        # Stiplet placeholder fylder hele bærelags-området så den
        # alligevel bund-justeres med de andre snit.
        besked = ikke_defineret or "Ikke defineret"
        return (
            f'<svg viewBox="0 0 360 {h_total}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto;max-height:{h_total}px">'
            f'{titel_html}'
            f'<rect x="{BOX_X1}" y="{TITEL_H}" width="{BOX_W}" '
            f'height="{max_baerelag_px}" '
            f'fill="#F5F5F5" stroke="#BDBDBD" stroke-width="1" '
            f'stroke-dasharray="4 3"/>'
            f'<text x="{(BOX_X1 + BOX_X2) / 2}" '
            f'y="{TITEL_H + max_baerelag_px / 2 + 4}" '
            f'font-family="system-ui, sans-serif" font-size="12" '
            f'fill="#888" text-anchor="middle" font-style="italic">{besked}</text>'
            f'</svg>'
        )

    baerelag_px = max(40, round(t_baerelag_mm / mm_per_px))
    baerelag_y2 = underbund_y1
    baerelag_y1 = baerelag_y2 - baerelag_px

    # ↕ mm-label i venstre side, centreret på bærelagsblokken
    mm_label_y = (baerelag_y1 + baerelag_y2) / 2
    mm_label_parts = [
        f'<text x="38" y="{mm_label_y - 4}" '
        f'font-family="system-ui, sans-serif" font-size="11" '
        f'fill="#444" text-anchor="middle">↕</text>',
        f'<text x="38" y="{mm_label_y + 10}" '
        f'font-family="system-ui, sans-serif" font-size="12" '
        f'font-weight="600" fill="#333" text-anchor="middle">'
        f'{t_baerelag_mm:.0f} mm</text>',
    ]
    # Interval-produkter (NX750/NX850): vis best-case under hovedtallet.
    if best_case_mm is not None and round(best_case_mm) < round(t_baerelag_mm):
        mm_label_parts.append(
            f'<text x="38" y="{mm_label_y + 24}" '
            f'font-family="system-ui, sans-serif" font-size="9" '
            f'fill="#555" text-anchor="middle">'
            f'↓ {best_case_mm:.0f} mm</text>'
            f'<text x="38" y="{mm_label_y + 34}" '
            f'font-family="system-ui, sans-serif" font-size="8" '
            f'fill="#777" text-anchor="middle" font-style="italic">'
            f'under optimale</text>'
            f'<text x="38" y="{mm_label_y + 43}" '
            f'font-family="system-ui, sans-serif" font-size="8" '
            f'fill="#777" text-anchor="middle" font-style="italic">'
            f'forhold</text>'
        )
    mm_label = "".join(mm_label_parts)

    # Geonet-linjer (stiplet, rød) — label vises ved hver linje,
    # opdelt i flere linjer (splittet på " / ") for læselighed.
    label_linjer = [s.strip() for s in geonet_label.split("/")]
    n_linjer = len(label_linjer)
    linje_h = 11  # px mellem baselines
    geonet_elems: list[str] = []
    for frac in geonet_y_fracs:
        y = baerelag_y1 + frac * baerelag_px
        geonet_elems.append(
            f'<line x1="{BOX_X1 - 4}" x2="{BOX_X2 + 4}" '
            f'y1="{y}" y2="{y}" stroke="{RØD}" stroke-width="2" '
            f'stroke-dasharray="6 3"/>'
        )
        # Centrér label-blokken vertikalt om y (geonet-linjen).
        første_baseline = y - (n_linjer - 1) * linje_h / 2 + 3
        tspans = "".join(
            f'<tspan x="{BOX_X2 + 8}" '
            f'dy="{0 if i == 0 else linje_h}">{linje}</tspan>'
            for i, linje in enumerate(label_linjer)
        )
        geonet_elems.append(
            f'<text x="{BOX_X2 + 8}" y="{første_baseline}" '
            f'font-family="system-ui, sans-serif" font-size="9.5" '
            f'fill="{RØD}">{tspans}</text>'
        )

    # Placér "Bærelag"-teksten i den øverste rene strækning af bærelaget
    # — fra toppen ned til den øverste geonet-linje (eller bunden hvis
    # der ikke er nogen). Det undgår at teksten overlapper en geonet-linje
    # i fx 2-lags-snittet, hvor øverste lag står midt i bærelaget.
    geonet_y_abs = [baerelag_y1 + f * baerelag_px for f in geonet_y_fracs]
    øverste_geonet_y = min(geonet_y_abs) if geonet_y_abs else baerelag_y2
    baerelag_tekst_y = (baerelag_y1 + øverste_geonet_y) / 2 + 4
    underbund_tekst_y = (underbund_y1 + underbund_y2) / 2 + 4

    return (
        f'<svg viewBox="0 0 360 {h_total}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;max-height:{h_total}px">'
        f'<defs>'
        # Bærelag: lys grå med små prikker
        f'<pattern id="pat_baerelag" patternUnits="userSpaceOnUse" '
        f'width="8" height="8">'
        f'<rect width="8" height="8" fill="#E8E8E8"/>'
        f'<circle cx="2" cy="2" r="0.9" fill="#9E9E9E"/>'
        f'<circle cx="6" cy="6" r="0.9" fill="#9E9E9E"/>'
        f'</pattern>'
        # Underbund: oliven/brun med diagonale streger
        f'<pattern id="pat_underbund" patternUnits="userSpaceOnUse" '
        f'width="9" height="9" patternTransform="rotate(45)">'
        f'<rect width="9" height="9" fill="#A89377"/>'
        f'<line x1="0" y1="0" x2="0" y2="9" stroke="#6E5B40" stroke-width="1.2"/>'
        f'</pattern>'
        f'</defs>'
        f'{titel_html}'
        # Bærelag
        f'<rect x="{BOX_X1}" y="{baerelag_y1}" width="{BOX_W}" '
        f'height="{baerelag_px}" fill="url(#pat_baerelag)" '
        f'stroke="#666" stroke-width="1"/>'
        f'<text x="{(BOX_X1 + BOX_X2) / 2}" y="{baerelag_tekst_y}" '
        f'font-family="system-ui, sans-serif" font-size="12" '
        f'font-weight="600" fill="#333" text-anchor="middle">'
        f'Bærelag</text>'
        # Underbund
        f'<rect x="{BOX_X1}" y="{underbund_y1}" width="{BOX_W}" '
        f'height="{UNDERBUND_H}" fill="url(#pat_underbund)" '
        f'stroke="#5C4A33" stroke-width="1"/>'
        f'<text x="{(BOX_X1 + BOX_X2) / 2}" y="{underbund_tekst_y - 6}" '
        f'font-family="system-ui, sans-serif" font-size="11" '
        f'font-weight="600" fill="#fff" text-anchor="middle">'
        f'Underbund</text>'
        f'<text x="{(BOX_X1 + BOX_X2) / 2}" y="{underbund_tekst_y + 9}" '
        f'font-family="system-ui, sans-serif" font-size="10.5" '
        f'fill="#fff" text-anchor="middle">'
        f'Eu = {eu:g} MPa</text>'
        # mm-label på venstre side
        f'{mm_label}'
        # Geonet-linjer ovenpå
        f'{"".join(geonet_elems)}'
        f'</svg>'
    )


_REF_VALG = "Referencenet (TX160 / SX160 / T6)"


def _produkt_t(produkter: list[dict] | None, navn: str) -> float | None:
    """Slå t_armeret_mm op for et produkt i en liste fra beregn_alle_produkter."""
    if not produkter:
        return None
    for p in produkter:
        if p["navn"] == navn and p.get("fejl") is None:
            return p.get("t_armeret_mm")
    return None


def _produkt_t_best(produkter: list[dict] | None, navn: str) -> float | None:
    """Best-case-tykkelse for interval-produkter (None hvis ikke interval)."""
    if not produkter:
        return None
    for p in produkter:
        if p["navn"] == navn and p.get("fejl") is None:
            return p.get("t_armeret_mm_min")
    return None


def _render_opbygningsvisualisering(
    eu: float,
    ref_1: dict | None,
    ref_2: dict | None,
    prod_1lag: list[dict] | None = None,
    prod_2lag: list[dict] | None = None,
) -> None:
    """Tre opbygnings-snit side om side. Default: referencenettet.

    Hvis prod_1lag/prod_2lag er givet, vises en dropdown der lader brugeren
    skifte til et hvilket som helst gyldigt produkt fra resultatlisten.
    """
    # ── Find uarmeret-tykkelse (uafhængig af produktvalg) ──────────────
    t_uarm = None
    for r in (ref_1, ref_2):
        if r is not None and r.get("produkter"):
            t_uarm_kandidat = r["produkter"][0].get("t_uarmeret_mm")
            if t_uarm_kandidat is not None:
                t_uarm = t_uarm_kandidat
                break

    # ── Dropdown med valgmuligheder ────────────────────────────────────
    # Saml gyldige produktnavne på tværs af 1-lag og 2-lag, sorteret efter
    # bedste (mindste) 1-lags-tykkelse — dem uden 1-lag bagest.
    navne_sorteret: list[str] = []
    if prod_1lag is not None or prod_2lag is not None:
        navne_set: dict[str, tuple[float, float, float]] = {}
        for p in (prod_1lag or []) + (prod_2lag or []):
            if p["navn"] == "Anden armering (manuel)":
                continue
            if p.get("fejl") is not None:
                continue
            if p["navn"] in navne_set:
                continue
            t1 = _produkt_t(prod_1lag, p["navn"])
            t2 = _produkt_t(prod_2lag, p["navn"])
            if t1 is None and t2 is None:
                continue
            sort_t1 = t1 if t1 is not None else 1e9
            navne_set[p["navn"]] = (sort_t1, t1 or 1e9, t2 or 1e9)
        navne_sorteret = sorted(navne_set.keys(), key=lambda n: navne_set[n])

    valg = _REF_VALG
    if navne_sorteret:
        def _format_valg(navn: str) -> str:
            if navn == _REF_VALG:
                return navn
            t1 = _produkt_t(prod_1lag, navn)
            t2 = _produkt_t(prod_2lag, navn)
            t1_str = f"{t1:.0f} mm" if t1 is not None else "—"
            t2_str = f"{t2:.0f} mm" if t2 is not None else "—"
            return f"{navn}  ·  1 lag: {t1_str}  ·  2 lag: {t2_str}"

        valg = st.selectbox(
            "Vis opbygning for:",
            [_REF_VALG] + navne_sorteret,
            index=0,
            format_func=_format_valg,
            key="opbygning_geonet_valg",
        )

    # ── Bestem snittenes tykkelser ud fra valget ───────────────────────
    if valg == _REF_VALG:
        t_1 = ref_1["t_armeret_mm"] if ref_1 is not None else None
        t_2 = ref_2["t_armeret_mm"] if ref_2 is not None else None
        t_1_best = None
        t_2_best = None
        produkt_navn_vis = None
        geonet_label = "Tensar TriAx 160 / GS-GRID SX160 / E'GRID T6"
    else:
        t_1 = _produkt_t(prod_1lag, valg)
        t_2 = _produkt_t(prod_2lag, valg)
        t_1_best = _produkt_t_best(prod_1lag, valg)
        t_2_best = _produkt_t_best(prod_2lag, valg)
        produkt_navn_vis = valg
        geonet_label = valg

    # ── Skalering: brug t_uarm hvis defineret, ellers største armerede ─
    kandidater = [t for t in (t_uarm, t_1, t_2) if t is not None]
    if not kandidater:
        st.caption("Ingen gyldige beregninger at visualisere.")
        return
    t_max = max(kandidater)
    mm_per_px = t_max / 220.0

    # ── Caption (dynamisk efter valg) ──────────────────────────────────
    if valg == _REF_VALG:
        st.caption(
            "Snittene viser opbygninger med **referencenettet** "
            "(Tensar TriAx TX160 / GS-GRID SX160 / E'GRID T6). "
            "Højderne er proportionale, så besparelsen ved armering er aflæselig."
        )
    else:
        st.caption(
            f"Snittene viser opbygninger med **{produkt_navn_vis}**. "
            f"Højderne er proportionale, så besparelsen ved armering er aflæselig."
        )

    # ── Byg de 3 SVG'er ────────────────────────────────────────────────
    svg_uarm = _opbygnings_snit_svg(
        "Uarmeret", t_uarm, mm_per_px, eu, geonet_y_fracs=[],
        ikke_defineret=(
            None if t_uarm is not None
            else f"Uarmeret bærelag ikke defineret for Eu = {eu:g} MPa"
        ),
    )
    svg_1 = _opbygnings_snit_svg(
        "1 lag geonet", t_1, mm_per_px, eu,
        geonet_y_fracs=[0.99] if t_1 is not None else [],
        ikke_defineret=(
            None if t_1 is not None
            else "Ikke gyldigt for denne kombination"
        ),
        geonet_label=geonet_label,
        best_case_mm=t_1_best,
    )
    svg_2 = _opbygnings_snit_svg(
        "2 lag geonet", t_2, mm_per_px, eu,
        geonet_y_fracs=[0.5, 0.99] if t_2 is not None else [],
        ikke_defineret=(
            None if t_2 is not None
            else "Ikke gyldigt for denne kombination"
        ),
        geonet_label=geonet_label,
        best_case_mm=t_2_best,
    )

    st.markdown(
        f'<div style="display:flex;gap:16px;justify-content:flex-start;'
        f'flex-wrap:wrap;max-width:100%">'
        f'<div style="flex:1 1 320px;max-width:440px">{svg_uarm}</div>'
        f'<div style="flex:1 1 320px;max-width:440px">{svg_1}</div>'
        f'<div style="flex:1 1 320px;max-width:440px">{svg_2}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_oversigt_expanders(
    eu: float,
    eo: float,
    valgt_klasse: int,
    bedste_1: dict | None,
    bedste_2: dict | None,
    *,
    ref_1: dict | None = None,
    ref_2: dict | None = None,
    prod_1lag: list[dict] | None = None,
    prod_2lag: list[dict] | None = None,
    phi: float = 35.0,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
    materialer: list[dict] | None = None,
    t_basis_table: dict | None = None,
) -> None:
    """De 3 informations-expandere under resultaterne.

    Bruges af både Standard (phi=35, geonet=None, materialer=None)
    og Brugerdefineret (egne phi/geonet/materialer-værdier).

    bedste_1 / bedste_2: bedste (mindste t_armeret) gruppe i hver lag-mode,
    eller None hvis ingen er gyldige. I "Vælg specifikt produkt"-mode er
    bedste-gruppen den enkelte produkts resultat pakket via
    _resultat_til_gruppe().
    """
    materialer = materialer or []

    # --- Opbygningsvisualisering (referencenet eller valgt produkt) -----
    if ref_1 is not None or ref_2 is not None:
        with st.expander("🧱 Opbygning", expanded=False):
            _render_opbygningsvisualisering(
                eu, ref_1, ref_2,
                prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            )

    # --- Advarsler -------------------------------------------------------
    # Validator-kørslen bruger den valgte phi/geonet/materialer-kontekst.
    # I "alle produkter"-mode er geonet=None, så produktspecifikke checks
    # springes over. Validator-anbefalinger (R1/R2) ignoreres altid — de
    # erstattes længere nede af tilpassede anbefalinger baseret på det
    # bedst reducerende net (gælder også specifikt produkt, da begge
    # lag-modes vises samtidig i den nye UI).
    advarsler_pr_lag: list[tuple[str, str]] = []
    lag_by_advarsel: dict[str, set[str]] = {}
    advarsler_unik: list[str] = []
    seen_a: set[str] = set()
    for lm in ("1_lag", "2_lag"):
        bedste = bedste_1 if lm == "1_lag" else bedste_2
        t_armeret_mm = bedste["t_armeret_mm"] if bedste is not None else None
        val = valider_input(
            eu=eu, eo=eo, phi=phi, lag_mode=lm,
            geonet=geonet, materialer=materialer,
            t_armeret_mm=t_armeret_mm,
            t_basis_table=t_basis_table,
        )
        for a in val.get("advarsler", []):
            advarsler_pr_lag.append((a, lm))
            lag_by_advarsel.setdefault(a, set()).add(lm)

    for a, lm in advarsler_pr_lag:
        if len(lag_by_advarsel[a]) == 1:
            a = _advarsel_med_lagtekst(a, lm)
        if a not in seen_a:
            seen_a.add(a)
            advarsler_unik.append(a)

    # --- Tilpassede anbefalinger baseret på bedste produkt --------------
    anbefalinger: list[str] = []

    # Anbefalinger bruger den afrundede (praktisk indbyggelige) tykkelse —
    # det er den værdi der konkret skal bygges, og som matcher kortenes
    # headline-tal.
    if bedste_1 is not None and bedste_1["t_armeret_mm"] > 500:
        # Best-case suffiks tilføjes for interval-produkter (NX750/NX850)
        interval_1 = next(
            (p for p in bedste_1.get("produkter", [])
             if p.get("t_armeret_mm_min") is not None),
            None,
        )
        t_1_str = f"<b>{bedste_1['t_armeret_mm']:.0f} mm</b>"
        if interval_1 is not None:
            t_1_best = round(interval_1["t_armeret_mm_min"])
            t_1_str = (
                f"{t_1_str}, og under optimale forhold "
                f"helt ned til <b>{t_1_best} mm</b>"
            )
        msg = (
            f"Mindst mulige bærelagstykkelse med 1 lag geonet er "
            f"{t_1_str} ({_navne_kort(bedste_1)}). "
            f"Ved opbygninger over 500 mm kan der med fordel anvendes "
            f"2 lag net for yderligere reduktion"
        )
        if bedste_2 is not None:
            interval_2 = next(
                (p for p in bedste_2.get("produkter", [])
                 if p.get("t_armeret_mm_min") is not None),
                None,
            )
            t_2_str = f"<b>{bedste_2['t_armeret_mm']:.0f} mm</b>"
            if interval_2 is not None:
                t_2_best = round(interval_2["t_armeret_mm_min"])
                t_2_str = (
                    f"{t_2_str}, og under optimale forhold "
                    f"<b>{t_2_best} mm</b>"
                )
            msg += f" — her: {t_2_str} ({_navne_kort(bedste_2)})."
        else:
            msg += " (ikke gyldigt for denne kombination)."
        anbefalinger.append(msg)

    if bedste_2 is not None and bedste_2["t_armeret_mm"] < 400:
        msg = (
            f"Mindst mulige tykkelse med 2 lag geonet er kun "
            f"<b>{bedste_2['t_armeret_mm']:.0f} mm</b>. "
            f"1 lag geonet er sandsynligvis tilstrækkeligt for denne belastning"
        )
        if bedste_1 is not None:
            msg += f" (1 lag giver <b>{bedste_1['t_armeret_mm']:.0f} mm</b>)."
        else:
            msg += "."
        anbefalinger.append(msg)

    antal = len(advarsler_unik) + len(anbefalinger)
    titel_adv = (
        f"⚠️ Advarsler og anbefalinger ({antal})"
        if antal else "⚠️ Advarsler og anbefalinger"
    )
    with st.expander(titel_adv, expanded=bool(advarsler_unik or anbefalinger)):
        if antal == 0:
            st.caption(
                "Ingen generelle advarsler for den valgte Eu og belastning."
            )
        for a in advarsler_unik:
            vis_advarsel(a)
        for r in anbefalinger:
            vis_anbefaling(r)

    # --- Udførelseskrav ---------------------------------------------------
    with st.expander("📋 Udførelseskrav"):
        st.markdown("**Generelle krav ved udførelse med geonet:**")
        st.markdown("""
- Underbund jævnes og planeres — ingen skarpe fremspring eller huller
- Komprimering i lag på maksimalt 200–300 mm
- Direkte kørsel på udlagt geonet er **ikke tilladt**
- Overlap ved skød: minimum **300 mm** (eller leverandørens anvisning)
- Geonettet udlægges stramt uden folder eller bølger
        """)

        if geonet is not None:
            # Specifikt produkt: vis konkrete værdier
            navn_vis = geonet_navn or geonet["navn"]
            min_dk_mm = geonet["min_daklag"] * 10
            if geonet["max_korn"] is not None:
                korn_str = f"**{geonet['max_korn']} mm**"
            else:
                korn_str = "**ikke specificeret** — kontakt leverandør"
            st.markdown(
                f"**Krav for {navn_vis}:**\n"
                f"- Minimum dæklag over geonet: **{min_dk_mm} mm**\n"
                f"- Max kornstørrelse i kontakt med geonet: {korn_str}"
            )
        else:
            # Oversigt: produkt-specifikke krav for bedste 1-lag og 2-lag.
            # Hvis samme sæt produkter er bedste i begge lag-modes,
            # vises kravene kun én gang.
            def _vis_krav_blok(overskrift: str, gruppe: dict) -> None:
                navne, dk_str, korn_str = _krav_for_gruppe(gruppe)
                st.markdown(
                    f"**{overskrift}** ({navne})\n"
                    f"- Minimum dæklag over geonet: **{dk_str}**\n"
                    f"- Max kornstørrelse i kontakt med geonet: **{korn_str}**"
                )

            samme = _samme_produkter(bedste_1, bedste_2)

            if samme and bedste_1 is not None:
                _vis_krav_blok("Krav for produkt", bedste_1)
            else:
                if bedste_1 is not None:
                    _vis_krav_blok("Krav for bedste 1-lag-produkt", bedste_1)
                if bedste_2 is not None:
                    _vis_krav_blok("Krav for bedste 2-lag-produkt", bedste_2)

            if bedste_1 is None and bedste_2 is None:
                st.caption(
                    "Ingen produkt-specifikke krav at vise — ingen gyldige "
                    "beregninger for den valgte kombination."
                )
            else:
                st.caption(
                    "Bemærk: kravene ovenfor gælder det bedst reducerende net. "
                    "Andre produkter kan have andre krav til dæklag og "
                    "kornstørrelse — se datablad eller skift til "
                    "'Vælg specifikt produkt' for individuelle værdier."
                )

    # --- Sådan beregnes det -----------------------------------------------
    with st.expander("🔢 Sådan beregnes det"):
        st.markdown("""
Trinvis beregning, baseret på designmanualer og intern forsøgsdata fra Byggros:

Der beregnes en bærelagstykkelse ud fra 1 eller 2 lag armering med udgangspunkt i et referencenet (Tensar TriAx TX160, GS-GRID SX160 eller E'GRID T6).
Den beregnede bærelagstykkelse korrigeres for friktionsvinkler forskellig fra φ = 35° samt effektindeks af forskellige geonet.

1. **Bundmodulet Eu** vælges eller beregnes via sammenhæng med Cv
2. **Krav til overflademodulet Eo** vælges alt efter belastningsklasse
3. **Opslag i designdiagrammerne** foretages på baggrund af valg af bund- og overflademodul, hvor bærelagstykkelsen bestemmes - uarmeret og armeret med 1–2 lag geonet.
   Der er lavet forudgående interpolation imellem designdiagrammerns tabelværdier, for at danne en komplet tabel for hvert designdiagram. 
4. **På baggrund af opslaget bestemmes basistykkelsen T_basis:**
   - Uarmeret: *xx mm*
   - 1 lag armering (referencenet): *xx mm*
   - 2 lag armering (referencenet): *xx mm*
5. **Korrektionsfaktorer for friktionsvinkel og effektivitet af geonet**

   **Friktionsvinkel:**
   Friktionsvinkel-korrektionen justerer basistykkelsen fra opslagstabellen, som er baseret på et standardmateriale med φ ≈ 35°. For hver grad over 35° reduceres tykkelsen med 2 %, og for φ under 35° øges tykkelsen tilsvarende.

   I standardberegningen sættes bærelagets friktionsvinkel φ = 35°.

   I den brugerdefinerede beregning beregnes en vægtet friktionsvinkel ud fra den angivne procentvægtning eller lagtykkelser af lagene, som er prædefinerede materialer med forskellige friktionsvinkler.

   *Eksempel på beregning i brugerdefineret tilstand, ud fra lagtykkelser:*

   | Lag | Materiale | Tykkelse | φ (°) | Vægtet bidrag |
   |-----|-----------|----------|------:|-------------:|
   | 1   | SG I 0-32 | 300 mm   | 40,0  | 12 000        |
   | 2   | Bundsand  | 450 mm   | 35,0  | 15 750        |

   Vægtet φ = Σ(tᵢ × φᵢ) / Σ(tᵢ) = 27 750 / 750 = **37,00°**

   φ-korrektion = −0,02 × (φ − 35°) = −0,02 × (37,00 − 35) = **−0,0400**
   *(dvs. tykkelsen reduceres med −4,00 % af T_basis)*

   **Net-korrektion:**
   Designdiagrammerne bruger GS-GRID SX160, E'GRID T6 eller Tensar TriAx TX160 som referencenet (effektindeks 100). Hvis der er valgt en anden armering, skaleres tykkelsen op eller ned med op til 20 % alt efter produkt.
   En positiv korrektionsfaktor = tykkere bærelag (mindre effektiv armering), negativ = tyndere bærelag (mere effektiv armering).

6. **Den endelige bærelagstykkelse beregnes som:**

   **T_armeret = T_basis × (1 + φ-kor + net-kor)**

        """)


def _render_breakdown_tabel(
    rows: list[tuple[str, str, str]],
    t_final: float | None,
    t_uarm: float | None = None,
    red_mm: float | None = None,
    red_pct: float | None = None,
) -> None:
    """
    Render en tabel-lignende breakdown med linjer og et slutresultat.
    rows: liste af (label, værditekst, notetekst). Hvis værditekst er tom
    vises kun label-teksten som en note-linje.
    """
    lines: list[str] = []
    for label, val, note in rows:
        if val:
            note_html = (
                f' <span style="color:#888;font-size:0.82em">{note}</span>'
                if note else ""
            )
            lines.append(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:2px 0;font-size:0.9rem">'
                f'<span style="color:#444">{label}{note_html}</span>'
                f'<span style="font-weight:600;font-variant-numeric:tabular-nums">'
                f'{val}</span>'
                f'</div>'
            )
        else:
            lines.append(
                f'<div style="font-size:0.83rem;color:#888;padding:2px 0">'
                f'{label}'
                f'</div>'
            )

    result_lines = "".join(lines)

    if t_final is not None:
        red_html = ""
        if red_mm is not None and red_pct is not None:
            pct_str = f"{red_pct:.0%}"
            red_html = (
                f'<span style="color:{GRØN};font-size:0.85em;margin-left:10px">'
                f'Reduceres ↓ {red_mm:.0f} mm fra uarmeret ({pct_str})'
                f'</span>'
            )
        result_html = (
            f'<div style="border-top:1px solid #C8E6C9;margin-top:6px;'
            f'padding-top:6px;display:flex;align-items:baseline;gap:6px">'
            f'<span style="font-size:1.25rem;font-weight:700;color:{GRØN}">'
            f'= {t_final:.0f} mm</span>'
            f'{red_html}'
            f'</div>'
        )
    else:
        result_html = ""

    st.markdown(
        f'<div style="background:#F8FFF8;border-radius:6px;'
        f'padding:0.75rem 1rem;border:1px solid #C8E6C9;margin-bottom:0.5rem">'
        f'{result_lines}'
        f'{result_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_breakdown_best_case(
    eu: float,
    eo: float,
    phi: float,
    lag_mode: str,
    kor_best: float,
    t_konservativ: float | None,
    t_uarm: float | None,
    t_basis_table: dict | None,
) -> None:
    """
    Vis en best-case-linje under breakdown-tabellen for interval-produkter
    (NX750/NX850). Tabellen ovenfor viser den konservative ende; her vises
    hvad samme beregning giver med best-case-korrektionen.
    """
    res = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=kor_best,
        lag_mode=lag_mode, t_basis_table=t_basis_table,
    )
    if res.get("fejl") is not None:
        return
    t_best = res.get("t_armeret_mm")
    if t_best is None or t_konservativ is None:
        return
    kor_pct = _dk_num(kor_best * 100, "+.0f")
    if t_uarm and t_uarm > 0:
        red_mm = round(t_uarm - t_best)
        red_pct = (t_uarm - t_best) / t_uarm
        reduktion_txt = f" (Reduceres ↓ {red_mm} mm fra uarmeret, {red_pct:.0%})"
    else:
        reduktion_txt = ""
    st.markdown(
        f'<div style="font-size:0.85rem;color:#444;'
        f'padding:4px 10px 0 10px;margin-top:-6px">'
        f'Best case (effektindeks i øvre ende, net-kor {kor_pct} %): '
        f'<b>{t_best:.0f} mm</b>{reduktion_txt} — '
        f'interval: <b>{t_best:.0f}–{t_konservativ:.0f} mm</b>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _vis_beregnings_breakdown(
    eu: float,
    eo: float,
    phi: float,
    valgt_klasse: int,
    bedste_1: dict | None,
    bedste_2: dict | None,
    *,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
    t_basis_table: dict | None = None,
) -> None:
    """
    Beregnings-breakdown boks under resultat (kun i Brugerdefineret).
    Viser trin-for-trin: uarmeret, 1 lag og 2 lag med korrektioner i mm.
    """
    phi_kor = -0.02 * (phi - 35.0)

    # Net-korrektioner og produktnavne per lag-mode
    if geonet is not None:
        # Specifikt-mode: samme korrektion begge lag-modes
        net_kor_1 = geonet["korrektion"]
        net_kor_2 = geonet["korrektion"]
        net_navn_1 = geonet_navn or geonet["navn"]
        net_navn_2 = net_navn_1
        note = None
        interval = geonet.get("korrektion_interval")
    else:
        # Oversigt-mode: brug bedste produkt per lag-mode
        if bedste_1 is not None and bedste_1.get("produkter"):
            net_kor_1 = bedste_1["produkter"][0]["korrektion"]
            net_navn_1 = bedste_1["produkter"][0]["navn"]
        else:
            net_kor_1 = 0.0
            net_navn_1 = "reference"
        if bedste_2 is not None and bedste_2.get("produkter"):
            net_kor_2 = bedste_2["produkter"][0]["korrektion"]
            net_navn_2 = bedste_2["produkter"][0]["navn"]
        else:
            net_kor_2 = 0.0
            net_navn_2 = "reference"
        note = (
            "Net-korrektionen vist her gælder det bedst reducerende produkt. "
            "Andre produkter har andre korrektioner — se kolonnerne ovenfor."
        )
        interval = None

    # Kald beregn() med de relevante net-korrektioner
    ref_uarm = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=0.0,
        lag_mode="1_lag", t_basis_table=t_basis_table,
    )
    ref_1 = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=net_kor_1,
        lag_mode="1_lag", t_basis_table=t_basis_table,
    )
    ref_2 = beregn(
        eu=eu, eo=eo, phi=phi, net_korrektion=net_kor_2,
        lag_mode="2_lag", t_basis_table=t_basis_table,
    )

    t_uarm_final = ref_uarm.get("t_uarmeret_mm") if not ref_uarm.get("fejl") else None

    with st.container(border=True):
        st.markdown("**📊 Beregnings-breakdown**")

        # ── Uarmeret ──────────────────────────────────────────────────
        st.markdown("**Uarmeret bærelagstykkelse**")
        if not ref_uarm.get("fejl") and ref_uarm.get("t_basis_uarm_mm") is not None:
            t_b_u = ref_uarm["t_basis_uarm_mm"]
            phi_kor_mm_u = t_b_u * phi_kor
            rows_u: list[tuple[str, str, str]] = [
                ("T_basis (opslag)", f"{t_b_u:.0f} mm", ""),
            ]
            if abs(phi_kor_mm_u) > 0.5:
                rows_u.append((
                    "φ-korrektion",
                    f"{_dk_num(phi_kor_mm_u, '+.0f')} mm",
                    f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                ))
            else:
                rows_u.append(("(ingen φ- eller net-korrektion)", "", ""))
            _render_breakdown_tabel(rows_u, t_uarm_final)
        else:
            st.caption("Kan ikke beregnes for denne Eu/Eo-kombination.")

        st.markdown("---")

        # ── 1 lag ─────────────────────────────────────────────────────
        if bedste_1 is not None:
            st.markdown(f"**Med 1 lag geonet** ({net_navn_1})")
            if not ref_1.get("fejl") and ref_1.get("t_basis_arm_mm") is not None:
                t_b_1     = ref_1["t_basis_arm_mm"]
                t_1_final = ref_1.get("t_armeret_mm")
                phi_kor_mm_1 = t_b_1 * phi_kor
                net_kor_mm_1 = t_b_1 * net_kor_1
                rows_1: list[tuple[str, str, str]] = [
                    ("T_basis_armeret (opslag)", f"{t_b_1:.0f} mm", ""),
                    (
                        "φ-korrektion",
                        f"{_dk_num(phi_kor_mm_1, '+.0f')} mm",
                        f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                    ),
                    (
                        "Net-korrektion",
                        f"{_dk_num(net_kor_mm_1, '+.0f')} mm",
                        f"({_dk_num(net_kor_1, '+.2f')})",
                    ),
                ]
                red_mm_1  = (t_uarm_final - t_1_final) if (t_uarm_final and t_1_final) else None
                red_pct_1 = (red_mm_1 / t_uarm_final)  if (red_mm_1 and t_uarm_final)  else None
                _render_breakdown_tabel(rows_1, t_1_final, t_uarm_final, red_mm_1, red_pct_1)
                if interval is not None:
                    _render_breakdown_best_case(
                        eu, eo, phi, "1_lag", interval[0],
                        t_1_final, t_uarm_final, t_basis_table,
                    )
            else:
                st.caption("Ingen gyldigt 1-lag resultat for denne kombination.")

        # ── 2 lag ─────────────────────────────────────────────────────
        if bedste_2 is not None:
            st.markdown("---")
            st.markdown(f"**Med 2 lag geonet** ({net_navn_2})")
            if not ref_2.get("fejl") and ref_2.get("t_basis_arm_mm") is not None:
                t_b_2     = ref_2["t_basis_arm_mm"]
                t_2_final = ref_2.get("t_armeret_mm")
                phi_kor_mm_2 = t_b_2 * phi_kor
                net_kor_mm_2 = t_b_2 * net_kor_2
                rows_2: list[tuple[str, str, str]] = [
                    ("T_basis_armeret (opslag)", f"{t_b_2:.0f} mm", ""),
                    (
                        "φ-korrektion",
                        f"{_dk_num(phi_kor_mm_2, '+.0f')} mm",
                        f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                    ),
                    (
                        "Net-korrektion",
                        f"{_dk_num(net_kor_mm_2, '+.0f')} mm",
                        f"({_dk_num(net_kor_2, '+.2f')})",
                    ),
                ]
                red_mm_2  = (t_uarm_final - t_2_final) if (t_uarm_final and t_2_final) else None
                red_pct_2 = (red_mm_2 / t_uarm_final)  if (red_mm_2 and t_uarm_final)  else None
                _render_breakdown_tabel(rows_2, t_2_final, t_uarm_final, red_mm_2, red_pct_2)
                if interval is not None:
                    _render_breakdown_best_case(
                        eu, eo, phi, "2_lag", interval[0],
                        t_2_final, t_uarm_final, t_basis_table,
                    )
            else:
                st.caption("Ingen gyldigt 2-lag resultat for denne kombination.")

        if note:
            st.caption(f"ℹ️ {note}")


def render_standard() -> None:
    """Standard-tilstand: produktoversigt for alle geonet på én gang.

    Lodret stablet layout: A. Underbund → B. Belastningsklasse →
    Resultater (uarmeret + 1/2-lag-kolonner) → informations-expandere.
    """

    # --- A. Underbund + B. Belastningsklasse ----------------------------
    eu = input_underbund(key_prefix="std")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="std")
    st.caption(
        "ℹ️ I resultatoversigten vises hvilke belastningsklasser produkterne anbefales til. Der vises en advarsel, hvis et produkt ikke anbefales anvendt til den valgte klasse."
    )

    # --- Beregn alt -----------------------------------------------------
    t_basis_table = _aktiv_t_basis_table()
    ref_1, ref_2, ref_fejl_1, ref_fejl_2 = _beregn_referencegrupper(
        eu, eo, 35.0, valgt_klasse, t_basis_table
    )
    prod_1lag = beregn_alle_produkter(eu, eo, "1_lag", t_basis_table=t_basis_table)
    prod_2lag = beregn_alle_produkter(eu, eo, "2_lag", t_basis_table=t_basis_table)

    alle_fejler_1 = all(p["fejl"] for p in prod_1lag)
    alle_fejler_2 = all(p["fejl"] for p in prod_2lag)
    haard_fejl: str | None = None
    if alle_fejler_1 and alle_fejler_2:
        for p in prod_1lag:
            if p["fejl"]:
                haard_fejl = p["fejl"]
                break

    t_uarm = None
    for p in prod_1lag + prod_2lag:
        if p["t_uarmeret_mm"] is not None:
            t_uarm = p["t_uarmeret_mm"]
            break

    grupper_1 = _gyldige_grupper(grupper_produkter(prod_1lag, tolerance_mm=5.0))
    grupper_2 = _gyldige_grupper(grupper_produkter(prod_2lag, tolerance_mm=5.0))

    bedste_1 = (
        sorted(grupper_1, key=lambda g: g["t_armeret_eksakt_mm"])[0]
        if grupper_1 else None
    )
    bedste_2 = (
        sorted(grupper_2, key=lambda g: g["t_armeret_eksakt_mm"])[0]
        if grupper_2 else None
    )

    # --- Resultater -----------------------------------------------------
    st.divider()
    st.subheader("Resultater")

    if haard_fejl:
        vis_fejl(haard_fejl)
    else:
        if t_uarm is not None:
            st.markdown(
                f'<div class="uarm-banner">'
                f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse</div>'
                f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            _render_uarmeret_mangler_besked(eu, eo)

        _render_referenceblok(
            ref_1, ref_2, ref_fejl_1, ref_fejl_2,
            valgt_klasse=valgt_klasse,
        )
        st.markdown("")

        kol_1, kol_2 = st.columns(2, gap="large")
        with kol_1:
            _render_lag_kolonne("1 LAG GEONET", grupper_1, valgt_klasse, "1_lag")
        with kol_2:
            _render_lag_kolonne("2 LAG GEONET", grupper_2, valgt_klasse, "2_lag")

    # --- Informations-expandere ----------------------------------------
    st.divider()
    _render_oversigt_expanders(
        eu, eo, valgt_klasse, bedste_1, bedste_2,
        ref_1=ref_1, ref_2=ref_2,
        prod_1lag=prod_1lag, prod_2lag=prod_2lag,
        t_basis_table=t_basis_table,
    )


# ===========================================================================
# BRUGERDEFINERET-TILSTAND — målrettet beregning (uændret logik)
# ===========================================================================

def _dk_num(v: float, fmt: str) -> str:
    """Formattér tal med dansk decimal-komma og rigtigt minus-tegn."""
    s = format(v, fmt).replace(".", ",")
    if s.startswith("-"):
        s = "−" + s[1:]
    return s


def _phi_tabel_data(materialer: list[dict]) -> dict:
    """Byg data til φ-beregningstabel — genbruges af opsummeringsboks og trin 3.

    Returnerer dict med:
        tabel_md       — markdown-tabel (header + adskiller + rækker)
        total_v        — sum af tykkelser (mm) eller andele (%)
        total_bidrag   — Σ(vᵢ × φᵢ)
        phi_weighted   — total_bidrag / total_v (eller 35.0 ved tom input)
        lag_mode_pct   — True hvis andele i %, ellers tykkelser i mm
        symbol         — 'p' eller 't' (til formelvisning)
        enhed          — '%' eller 'mm'
    """
    if not materialer:
        return {
            "tabel_md": "", "total_v": 0.0, "total_bidrag": 0.0,
            "phi_weighted": 35.0, "lag_mode_pct": False,
            "symbol": "t", "enhed": "mm",
        }

    lag_mode_pct = any(m.get("pct") is not None for m in materialer)
    enhed = "%" if lag_mode_pct else "mm"
    symbol = "p" if lag_mode_pct else "t"
    feltnavn = "Andel" if lag_mode_pct else "Tykkelse"

    header = f"| Lag | Materiale | {feltnavn} | φ (°) | Vægtet bidrag |"
    sep = "|---|---|---:|---:|---:|"

    rows: list[str] = []
    total_v = 0.0
    total_bidrag = 0.0
    for i, m in enumerate(materialer):
        v = (m.get("pct") if lag_mode_pct else m.get("tykkelse_mm")) or 0.0
        bidrag = v * m["phi"]
        total_v += v
        total_bidrag += bidrag
        v_str = f"{v:.0f} {enhed}"
        phi_i_str = _dk_num(m["phi"], ".1f")
        bidrag_str = _dk_num(bidrag, ".0f")
        rows.append(
            f"| {i + 1} | {m['navn']} | {v_str} | {phi_i_str} | {bidrag_str} |"
        )

    tabel_md = "\n".join([header, sep] + rows)
    phi_weighted = total_bidrag / total_v if total_v > 0 else 35.0

    return {
        "tabel_md": tabel_md,
        "total_v": total_v,
        "total_bidrag": total_bidrag,
        "phi_weighted": phi_weighted,
        "lag_mode_pct": lag_mode_pct,
        "symbol": symbol,
        "enhed": enhed,
    }


def _vis_phi_opsummeringsboks(
    materialer: list[dict],
    phi_final: float,
    eu: float,
    eo: float,
    t_basis_table: dict | None = None,
) -> None:
    """Opsummeringsboks under lag-inputs: tabel, formel, φ-korrektion, mm-ækvivalent."""
    data = _phi_tabel_data(materialer)
    phi_weighted = data["phi_weighted"]
    overskrevet = abs(phi_final - phi_weighted) > 0.005

    phi_w_str = _dk_num(phi_weighted, ".2f")
    phi_f_str = _dk_num(phi_final, ".2f")
    bidrag_str = _dk_num(data["total_bidrag"], ".0f")
    v_str = _dk_num(data["total_v"], ".0f")

    phi_kor = -0.02 * (phi_final - 35.0)
    phi_kor_str = _dk_num(phi_kor, "+.4f")
    phi_kor_pct_str = _dk_num(phi_kor * 100, "+.2f")

    with st.container(border=True):
        st.markdown("**📐 φ-beregning fra materialelagene**")
        st.markdown(data["tabel_md"])
        st.markdown(
            f"φ = Σ({data['symbol']}ᵢ × φᵢ) / Σ({data['symbol']}ᵢ) = "
            f"{bidrag_str} / {v_str} = **{phi_w_str}°**"
        )

        if overskrevet:
            st.markdown(
                f"⚠️ φ overskrevet manuelt → bruger **{phi_f_str}°** "
                f"i resten af beregningen (vægtet værdi {phi_w_str}° ignoreres)."
            )

        st.markdown(
            f"**φ-korrektion** = −0,02 × (φ − 35°) = "
            f"−0,02 × ({phi_f_str} − 35) = **{phi_kor_str}** "
            f"({phi_kor_pct_str} % af T_basis)"
        )

        ref_1 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="1_lag",
                       t_basis_table=t_basis_table)
        ref_2 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="2_lag",
                       t_basis_table=t_basis_table)




def _input_materialelag(eu: float, eo: float) -> tuple[list[dict], float]:
    """
    C. Materialelag — render input-sektionen og returnér
    (materialer-liste, beregnet/overskrevet φ).
    """
    st.subheader("C. Materialelag")

    antal_lag = st.number_input(
        "Antal lag", min_value=1, max_value=3, value=2, step=1,
        key="bd_antal_lag",
    )
    lag_mode_mat = st.radio(
        "Angiv tykkelse som",
        ["mm (absolut)", "% (andele)"],
        horizontal=True,
        key="bd_lag_mode_mat",
    )
    if lag_mode_mat == "mm (absolut)":
        st.caption(
            f"Hvert lag skal være mindst {MIN_LAGTYKKELSE_MM} mm. "
            f"Den samlede opbygning skal være mindst {MIN_TOTAL_OPBYGNING_MM} mm."
        )

    materialer: list[dict] = []
    phi_vaerdier: list[float] = []
    total_pct = 0.0

    for i in range(int(antal_lag)):
        with st.expander(f"Lag {i + 1}", expanded=True):
            dynamiske_navne = [
                m["navn"] for m in st.session_state.get("materialer", [])
            ]
            materiale_options = dynamiske_navne + ["Manuel indtastning"]
            mat_key = f"bd_mat_{i}"
            slettet_materiale = None
            if (
                mat_key in st.session_state
                and st.session_state[mat_key] not in materiale_options
            ):
                slettet_materiale = st.session_state[mat_key]
                st.session_state[mat_key] = "Manuel indtastning"

            mat_navn = st.selectbox(
                "Materiale", materiale_options, key=mat_key,
            )

            md = (
                None
                if mat_navn == "Manuel indtastning"
                else _find_materiale_session(mat_navn)
            )
            if slettet_materiale is not None:
                st.warning(
                    f"Materialet '{slettet_materiale}' findes ikke længere i databasen. "
                    "Laget er skiftet til manuel indtastning."
                )
            elif mat_navn != "Manuel indtastning" and md is None:
                st.warning(
                    f"Materialet '{mat_navn}' findes ikke længere i databasen. "
                    "Laget behandles som manuel indtastning."
                )

            lag_navn = mat_navn if md is not None else "Manuel indtastning"

            if md is None:
                phi_i = st.number_input(
                    "φ (°)", 20.0, 60.0, 35.0, 0.5, key=f"bd_phi_m_{i}"
                )
                korn_i = st.number_input(
                    "Max kornstørrelse (mm)", 0, 500, 32, key=f"bd_korn_m_{i}"
                )
                ltype_i = st.selectbox(
                    "Lagtype", ["Bærelag", "Bundsikring"], key=f"bd_lt_m_{i}"
                )
            else:
                phi_i = float(md["phi"])
                korn_i = md["max_korn"]
                ltype_i = md["lagtype"]
                st.caption(
                    f"φ = {phi_i}° · max korn = {korn_i} mm · {ltype_i}"
                )

            phi_vaerdier.append(phi_i)

            if lag_mode_mat == "mm (absolut)":
                t_key = f"bd_t_{i}"
                if (
                    t_key in st.session_state
                    and st.session_state[t_key] < MIN_LAGTYKKELSE_MM
                ):
                    st.session_state[t_key] = MIN_LAGTYKKELSE_MM
                t_i = st.number_input(
                    "Tykkelse (mm)",
                    min_value=MIN_LAGTYKKELSE_MM,
                    max_value=2000,
                    value=300,
                    step=50,
                    key=t_key,
                )
                materialer.append({
                    "navn": lag_navn, "phi": phi_i, "max_korn": korn_i,
                    "lagtype": ltype_i, "tykkelse_mm": float(t_i),
                    "pct": None,
                })
            else:
                pct_default = round(100.0 / antal_lag, 1)
                p_i = st.number_input(
                    "Andel (%)", 0.0, 100.0, pct_default, 5.0,
                    key=f"bd_p_{i}",
                )
                total_pct += p_i
                materialer.append({
                    "navn": lag_navn, "phi": phi_i, "max_korn": korn_i,
                    "lagtype": ltype_i, "tykkelse_mm": None,
                    "pct": float(p_i),
                })

    if lag_mode_mat == "mm (absolut)":
        total_t = sum(m["tykkelse_mm"] for m in materialer)
        st.markdown(f"**Samlet tykkelse af opbygning:** {total_t:.0f} mm")

    if lag_mode_mat.startswith("%"):
        st.metric("Sum af andele", f"{total_pct:.1f} %")

    if lag_mode_mat == "mm (absolut)":
        if total_t < MIN_TOTAL_OPBYGNING_MM:
            st.error(
                f"Den samlede opbygning er {total_t:.0f} mm. "
                f"Den skal være mindst {MIN_TOTAL_OPBYGNING_MM} mm."
            )
            st.stop()
        phi_weighted = (
            sum(m["phi"] * m["tykkelse_mm"] for m in materialer) / total_t
            if total_t > 0
            else (sum(phi_vaerdier) / len(phi_vaerdier) if phi_vaerdier else 35.0)
        )
    else:
        total_p = sum(m["pct"] for m in materialer if m["pct"] is not None)
        phi_weighted = (
            sum(m["phi"] * m["pct"] for m in materialer) / total_p
            if total_p > 0
            else (sum(phi_vaerdier) / len(phi_vaerdier) if phi_vaerdier else 35.0)
        )

    if st.checkbox("Overskriv φ manuelt", key="bd_phi_override"):
        phi = st.number_input(
            "φ (°)", 20.0, 60.0, round(phi_weighted, 1), 0.5, key="bd_phi_man",
        )
    else:
        phi = phi_weighted

    _vis_phi_opsummeringsboks(
        materialer, phi, eu, eo,
        t_basis_table=_aktiv_t_basis_table(),
    )

    return materialer, phi


def _render_uarm_banner_bd(t_uarm: float, phi: float) -> None:
    """
    Render uarmeret-banner i brugerdefineret tilstand.

    Hvis phi == 35° (standard): én kolonne som i Standard-tilstanden.
    Hvis phi ≠ 35°: to kolonner — basis (ingen korrektioner) til venstre
    og φ-korrigeret tykkelse til højre med Δ-linje.
    """
    if abs(phi - 35.0) <= 0.05:
        st.markdown(
            f'<div class="uarm-banner">'
            f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse</div>'
            f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    phi_kor = K_PHI * (phi - 35.0)
    t_uarm_phi = round(t_uarm * (1 + phi_kor))
    delta_mm = abs(round(t_uarm - t_uarm_phi))
    phi_str = _dk_num(phi, ".1f")
    pil = "↓" if t_uarm_phi < t_uarm else "↑"

    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        st.markdown(
            f'<div class="uarm-banner">'
            f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse (basis)</div>'
            f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_r:
        st.markdown(
            f'<div class="uarm-banner">'
            f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse (φ-korrigeret)</div>'
            f'<div class="uarm-banner-tal">{t_uarm_phi:.0f} mm</div>'
            f'<div style="font-size:0.9rem;color:#555;margin-top:0.1rem">'
            f'{pil} {delta_mm} mm &nbsp;(φ = {phi_str}°)'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_brugerdefineret() -> None:
    """Brugerdefineret-tilstand: A–D input + resultater + expandere.

    Lodret stablet layout som i Standard-tilstand. Sektion D lader brugeren
    vælge mellem 'Vis alle produkter' (oversigt med custom φ) og 'Vælg
    specifikt produkt' (detaljeret resultat for ét produkt). Begge modes
    viser 1-lag og 2-lag side om side — ingen separat lag-mode-radio.
    """

    # --- A + B + C --------------------------------------------------------
    t_basis_table = _aktiv_t_basis_table()
    eu = input_underbund(key_prefix="bd")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="bd")
    materialer, phi = _input_materialelag(eu, eo)

    # --- D. Geonet --------------------------------------------------------
    st.subheader("D. Geonet")

    visning = st.radio(
        "Visning",
        ["Vis alle produkter (oversigt)", "Vælg specifikt produkt"],
        horizontal=True,
        key="bd_visning",
        help=(
            "**Vis alle produkter:** samme oversigt som Standard, men med "
            "din custom φ fra materialelagene.  \n"
            "**Vælg specifikt produkt:** detaljeret resultat for ét valgt "
            "produkt, herunder dets specifikke udførelseskrav."
        ),
    )
    specifikt_mode = visning == "Vælg specifikt produkt"

    geonet: dict | None = None
    geonet_navn: str | None = None
    if specifikt_mode:
        geonet_navn = st.selectbox(
            "Produkt",
            GEONET_NAVNE,
            index=GEONET_NAVNE.index("GS-GRID SX160"),
            key="bd_geonet",
        )
        geonet = find_geonet(geonet_navn)

        if geonet:
            korn_txt = f"{geonet['max_korn']} mm" if geonet["max_korn"] else "—"
            kl_txt = ", ".join(str(k) for k in geonet["klasser"])
            kor_txt = f"{geonet['korrektion']:+.0%}"
            st.caption(
                f"Serie: **{geonet['serie']}** · Korrektion: {kor_txt} · "
                f"Max korn: {korn_txt} · Klasser: {kl_txt} · "
                f"Min dæklag: {geonet['min_daklag']} cm"
            )
            if geonet["navn"] == "Anden armering (manuel)":
                kor_man = st.number_input(
                    "Korrektionsfaktor (−0.20 til +0.20)",
                    min_value=-0.20, max_value=0.20,
                    value=0.0, step=0.01, format="%.2f",
                    key="bd_kor_man",
                    help="0.00 = samme effektivitet som reference (TX160/SX160/T6).",
                )
                geonet = {**geonet, "korrektion": kor_man}

    # --- Resultat ---------------------------------------------------------
    st.divider()
    st.subheader("Resultater")

    bedste_1: dict | None = None
    bedste_2: dict | None = None

    # Reference- og produktberegninger bruges i begge modes — både til
    # at vise reference-banneret og til opbygnings-expanderens dropdown.
    ref_1, ref_2, ref_fejl_1, ref_fejl_2 = _beregn_referencegrupper(
        eu, eo, phi, valgt_klasse, t_basis_table
    )
    prod_1lag = beregn_alle_produkter(
        eu, eo, "1_lag", phi=phi, t_basis_table=t_basis_table
    )
    prod_2lag = beregn_alle_produkter(
        eu, eo, "2_lag", phi=phi, t_basis_table=t_basis_table
    )

    if not specifikt_mode:
        # OVERSIGT-MODE — som Standard, men med custom phi

        alle_fejler_1 = all(p["fejl"] for p in prod_1lag)
        alle_fejler_2 = all(p["fejl"] for p in prod_2lag)
        haard_fejl: str | None = None
        if alle_fejler_1 and alle_fejler_2:
            for p in prod_1lag:
                if p["fejl"]:
                    haard_fejl = p["fejl"]
                    break

        t_uarm = None
        for p in prod_1lag + prod_2lag:
            if p["t_uarmeret_mm"] is not None:
                t_uarm = p["t_uarmeret_mm"]
                break

        grupper_1 = _gyldige_grupper(grupper_produkter(prod_1lag, tolerance_mm=5.0))
        grupper_2 = _gyldige_grupper(grupper_produkter(prod_2lag, tolerance_mm=5.0))
        bedste_1 = (
            sorted(grupper_1, key=lambda g: g["t_armeret_eksakt_mm"])[0]
            if grupper_1 else None
        )
        bedste_2 = (
            sorted(grupper_2, key=lambda g: g["t_armeret_eksakt_mm"])[0]
            if grupper_2 else None
        )

        if haard_fejl:
            vis_fejl(haard_fejl)
        else:
            if t_uarm is not None:
                _render_uarm_banner_bd(t_uarm, phi)
            else:
                _render_uarmeret_mangler_besked(eu, eo)
            _render_referenceblok(
                ref_1, ref_2, ref_fejl_1, ref_fejl_2,
                valgt_klasse=valgt_klasse,
                phi=phi,
            )
            st.markdown("")
            kol_1, kol_2 = st.columns(2, gap="large")
            with kol_1:
                _render_lag_kolonne("1 LAG GEONET", grupper_1, valgt_klasse, "1_lag", phi=phi)
            with kol_2:
                _render_lag_kolonne("2 LAG GEONET", grupper_2, valgt_klasse, "2_lag", phi=phi)

    else:
        # SPECIFIKT PRODUKT-MODE
        net_kor = geonet["korrektion"] if geonet else 0.0
        res_1 = beregn(
            eu=eu, eo=eo, phi=phi, net_korrektion=net_kor,
            lag_mode="1_lag", t_basis_table=t_basis_table,
        )
        res_2 = beregn(
            eu=eu, eo=eo, phi=phi, net_korrektion=net_kor,
            lag_mode="2_lag", t_basis_table=t_basis_table,
        )

        bedste_1 = _resultat_til_gruppe(res_1, geonet, valgt_klasse)
        bedste_2 = _resultat_til_gruppe(res_2, geonet, valgt_klasse)

        # Interval-produkter (NX750/NX850): kør beregn() en ekstra gang med
        # best-case-korrektionen og berig produkt-dict'en med min/max-felter.
        interval = geonet.get("korrektion_interval") if geonet else None
        if interval is not None:
            kor_best, kor_kons = interval
            for gruppe, lag_mode in ((bedste_1, "1_lag"), (bedste_2, "2_lag")):
                if gruppe is None or not gruppe.get("produkter"):
                    continue
                res_best = beregn(
                    eu=eu, eo=eo, phi=phi, net_korrektion=kor_best,
                    lag_mode=lag_mode, t_basis_table=t_basis_table,
                )
                if res_best.get("fejl") is not None:
                    continue
                produkt = gruppe["produkter"][0]
                produkt["korrektion_min"] = kor_best
                produkt["korrektion_max"] = kor_kons
                produkt["t_armeret_mm_min"] = res_best.get("t_armeret_mm")
                produkt["t_armeret_mm_max"] = produkt["t_armeret_mm"]
                produkt["reduktion_mm_min"] = produkt.get("reduktion_mm")
                produkt["reduktion_mm_max"] = res_best.get("reduktion_mm")
                produkt["reduktion_pct_min"] = produkt.get("reduktion_pct")
                produkt["reduktion_pct_max"] = res_best.get("reduktion_pct")

        t_uarm = None
        for r in (res_1, res_2):
            if not r.get("fejl") and r.get("t_uarmeret_mm") is not None:
                t_uarm = r["t_uarmeret_mm"]
                break

        haard_fejl_specifikt: str | None = None
        if bedste_1 is None and bedste_2 is None:
            haard_fejl_specifikt = res_1.get("fejl") or res_2.get("fejl")

        if haard_fejl_specifikt:
            vis_fejl(haard_fejl_specifikt)
        else:
            if t_uarm is not None:
                _render_uarm_banner_bd(t_uarm, phi)
            else:
                _render_uarmeret_mangler_besked(eu, eo)

            grupper_1 = [bedste_1] if bedste_1 else []
            grupper_2 = [bedste_2] if bedste_2 else []

            tom_1 = (
                f"**{geonet_navn}** har ingen gyldigt 1-lag-resultat for "
                f"denne kombination.\n\n_{res_1.get('fejl', '')}_"
                if bedste_1 is None else None
            )
            tom_2 = (
                f"**{geonet_navn}** har ingen gyldigt 2-lag-resultat for "
                f"denne kombination.\n\n_{res_2.get('fejl', '')}_"
                if bedste_2 is None else None
            )

            kol_1, kol_2 = st.columns(2, gap="large")
            with kol_1:
                _render_lag_kolonne(
                    "1 LAG GEONET", grupper_1, valgt_klasse, "1_lag",
                    tom_besked=tom_1, phi=phi,
                )
            with kol_2:
                _render_lag_kolonne(
                    "2 LAG GEONET", grupper_2, valgt_klasse, "2_lag",
                    tom_besked=tom_2, phi=phi,
                )

    # --- Informations-expandere ------------------------------------------
    st.divider()
    _render_oversigt_expanders(
        eu, eo, valgt_klasse, bedste_1, bedste_2,
        ref_1=ref_1, ref_2=ref_2,
        prod_1lag=prod_1lag, prod_2lag=prod_2lag,
        phi=phi,
        geonet=geonet,
        geonet_navn=geonet_navn,
        materialer=materialer,
        t_basis_table=t_basis_table,
    )


# ===========================================================================
# Sidebar navigation
# ===========================================================================

_NAV_ITEMS = [
    ("📐", "Dimensionering",   "dimensionering"),
    ("🪨", "Materialer",        "materialer"),
    ("🕸️", "Geonet database",  "geonet_database"),
    ("📊", "Designdiagrammer",  "designdiagrammer"),
]


def render_sidebar() -> str:
    """Render venstre navigationsmenu. Returnerer nøglen for den aktive side."""
    if "aktiv_side" not in st.session_state:
        st.session_state.aktiv_side = "dimensionering"

    with st.sidebar:
        st.markdown(
            '<div class="sb-header">'
            '<div class="sb-logo">🏗️</div>'
            '<div class="sb-title">Beregningsværktøj</div>'
            '<div class="sb-sub">BG Byggros · v0.3</div>'
            '<div class="sb-sub">Udviklet af DST</div>'
            "</div>",
            unsafe_allow_html=True,
        )

        for ikon, navn, nøgle in _NAV_ITEMS:
            aktiv = st.session_state.aktiv_side == nøgle
            if st.button(
                f"{ikon}  {navn}",
                key=f"_nav_{nøgle}",
                width="stretch",
                type="primary" if aktiv else "secondary",
            ):
                st.session_state.aktiv_side = nøgle
                st.rerun()

        # Fyld-spacer + footer nederst
        st.markdown(
            '<hr class="sb-divider" style="margin-top:1.5rem">'
            '<div class="sb-footer">'
            "<span>© BG Byggros</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    return st.session_state.aktiv_side


# ===========================================================================
# Placeholder-sider (Materialer, Geonet database, Designdiagrammer)
# ===========================================================================

def render_geonet_database() -> None:
    st.title("🕸️ Geonet database")
    st.caption(
        "Oversigt over alle geonet-produkter med effektindeks, belastningsklasser og tekniske data. "
    )
    st.divider()

    import pandas as pd

    # ── Tabel ──────────────────────────────────────────────────────────────
    rækker = []
    for g in GEONET_DB:
        if g["navn"] == "Anden armering (manuel)":
            continue
        rækker.append({
            "Produkt":               g["navn"],
            "Serie":                 g["serie"],
            "Type":                  g.get("type", "—"),
            "Effektindeks":          g.get("effektindeks", "—"),
            "Korrektions-\nfaktor": (
                f"{g['korrektion_interval'][0]:+.0%} til {g['korrektion_interval'][1]:+.0%}"
                if g.get("korrektion_interval") is not None
                else f"{g['korrektion']:+.0%}"
            ),
            "BK":                    ", ".join(str(k) for k in g["klasser"]),
            "Min. dæklag\n(cm)":     g["min_daklag"],
            "Maks. korn\n(datablad mm)": f"{g['max_korn']}" if g["max_korn"] else "—",
            "Anb. tilslag\n(designmanual)": g.get("anbefalet_tilslag") or "—",
            "Rudeåbning/maskestørrelse":            g.get("rudeaabning") or "—",
            "Radial stivhed\n(kN/m @ 0,5%)": f"{g['radial_stivhed']}" if g.get("radial_stivhed") else "—",
            "GWP A1–A3\n(kg CO₂/m²)": f"{g['gwp']:.2f}" if g.get("gwp") else "—",
            "Min. levetid":          g.get("min_levetid") or "—",
            "Overlæg Eu ≥ 5\n(cm)": g.get("overlap_eu_ge5_cm", 30),
            "Overlæg Eu < 5\n(cm)": g.get("overlap_eu_lt5_cm", 40),
            "Bemærkning":            g.get("bemærkning", ""),
        })

    df = pd.DataFrame(rækker)

    # Beregn nødvendig højde så hele tabellen vises uden scroll
    row_height_px = 38
    header_px = 60
    tabel_hoejde = header_px + len(rækker) * row_height_px

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=tabel_hoejde,
    )

    # ── Kolonnebeskrivelser ────────────────────────────────────────────────
    with st.expander("📖 Kolonnebeskrivelser", expanded=False):
        st.markdown("""
| Kolonne | Forklaring |
|---|---|
| **Effektindeks** | Relativ effektivitet ift. referenceproduktet (= 100). Højere indeks = tyndere bærelag. |
| **Korrektionsfaktor** | Direkte korrektionsfaktor brugt i beregningen. Negativt = tykkelsen reduceres. |
| **BK** | Anbefalede belastningsklasser (1–6) iflg. designmanualerne. |
| **Min. dæklag** | Mindste lagtykkelse over geonet (cm) — under dette kan geonettets funktion ikke garanteres. |
| **Maks. korn (datablad)** | Maksimal kornstørrelse angivet i produktdatabladet (mm). |
| **Anb. tilslag (designmanual)** | Anbefalet tilslagsstørrelse iflg. dimensioneringsmanual. |
| **Rudeåbning** | Maskestørrelse/pitch fra designmanual. |
| **Radial stivhed** | Radial stivhed ved 0,5 % tøjning (kN/m) — kun tilgængeligt for hexagonale produkter. |
| **GWP A1–A3** | Klimaaftryk i produktionsfasen (kg CO₂-ækvivalent pr. m²). |
| **Min. levetid** | Teknisk minimumslevetid angivet i datablad. |
| **Overlæg Eu ≥ 5 / < 5** | Påkrævet overlæg i samlinger (cm) afhængig af underbundens E-modul. |
        """)

    # ── Vigtige noter ─────────────────────────────────────────────────────
    st.subheader("📝 Database-noter og kildehenvisninger")
    for note in GEONET_NOTER:
        with st.expander(f"ℹ️ {note['titel']}", expanded=False):
            st.markdown(note["tekst"])


def render_designdiagrammer() -> None:
    st.title("📊 Designdiagrammer")
    st.caption(
        "Designdiagrammer fra designmanualerne, samt redigerbare diagramdata. "
        "Beregningerne bruger tabellerne direkte som opslag, da der er lavet forudgående interpolation imellem værdier fra de originale designdiagrammer."
    )
    if st.button("Nulstil diagramdata til standard", type="secondary"):
        slet_designdiagrammer_json_og_nulstil()
        st.session_state["designdiagrammer"] = _standard_designdiagrammer()
        _opdater_aktiv_t_basis_table()
        st.rerun()

    st.divider()

    import pandas as pd

    def _raw_dataframe(diagram: dict) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "Eu (MPa)": row["eu"],
                "Uarmeret tykkelse (cm)": row["t_uarmeret_cm"],
                "1 lag tykkelse (cm)": row["t_1_lag_cm"],
                "2 lag tykkelse (cm)": row["t_2_lag_cm"],
            }
            for row in diagram["rows"]
        ])

    diagram_table_height = 490
    redigerede_diagrammer: list[dict] = []

    for diagram in st.session_state["designdiagrammer"]:
        kol_diagram, kol_tabel = st.columns([1.1, 1], gap="large")
        with kol_diagram:
            image_path = os.path.join(
                os.path.dirname(__file__),
                "diagrambilleder",
                diagram["image_name"],
            )
            st.image(image_path, width="stretch")
        with kol_tabel:
            st.markdown("**Aflæste diagramdata**")
            redigeret = st.data_editor(
                _raw_dataframe(diagram),
                width="stretch",
                height=diagram_table_height,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "Eu (MPa)": st.column_config.NumberColumn(
                        "Eu (MPa)",
                        min_value=0.0,
                        step=1.0,
                        format="%.0f",
                    ),
                    "Uarmeret tykkelse (cm)": st.column_config.NumberColumn(
                        "Uarmeret tykkelse (cm)",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                    ),
                    "1 lag tykkelse (cm)": st.column_config.NumberColumn(
                        "1 lag tykkelse (cm)",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                    ),
                    "2 lag tykkelse (cm)": st.column_config.NumberColumn(
                        "2 lag tykkelse (cm)",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                    ),
                },
                key=f"diagram_editor_{diagram['diagram_nr']}",
            )
            redigerede_diagrammer.append({
                **diagram,
                "rows": redigeret.to_dict("records"),
            })
        st.markdown('<div class="diagram-række-afstand"></div>', unsafe_allow_html=True)

    normaliserede_diagrammer, diagram_fejl = _normaliser_designdiagrammer(
        redigerede_diagrammer
    )
    if diagram_fejl:
        st.error(
            "Diagramdata er ikke gemt, fordi der er fejl: "
            + " ".join(diagram_fejl)
        )
    elif normaliserede_diagrammer != st.session_state["designdiagrammer"]:
        st.session_state["designdiagrammer"] = normaliserede_diagrammer
        gem_designdiagrammer(normaliserede_diagrammer)
        _opdater_aktiv_t_basis_table()


def render_materialer() -> None:
    st.title("🪨 Materialer")
    st.caption(
        "Anvend standard materialerne til dimensioneringen, eller indtast egne materialer. Ændringer gemmes automatisk og anvendes ved beregninger "
        "i Brugerdefineret-tilstand."
    )
    st.divider()

    import pandas as pd

    kol_a, kol_b, kol_c = st.columns([1, 1, 4])
    with kol_a:
        if st.button("➕ Tilføj materiale", width="stretch"):
            eksisterende = {
                m["navn"].casefold()
                for m in st.session_state.get("materialer", [])
            }
            navn = "Nyt materiale"
            nr = 2
            while navn.casefold() in eksisterende:
                navn = f"Nyt materiale {nr}"
                nr += 1
            st.session_state["materialer"].append({
                "navn": navn,
                "lagtype": "Bærelag",
                "phi": 35,
                "max_korn": 32,
                "anvendelse": "",
            })
            gem_materialer(st.session_state["materialer"])
            st.rerun()

    with kol_b:
        if st.button("🔄 Nulstil til standard", width="stretch", type="secondary"):
            slet_json_og_nulstil()
            st.session_state["materialer"] = indlaes_materialer()
            st.rerun()

    df = pd.DataFrame(
        st.session_state.get("materialer", []),
        columns=["navn", "lagtype", "phi", "max_korn", "anvendelse"],
    )

    redigeret = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
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

    ny_liste = _normaliser_materialer(redigeret.to_dict("records"))
    duplikater = _duplikerede_materialenavne(ny_liste)

    if not ny_liste:
        st.error("Materialelisten skal indeholde mindst ét materiale.")
        st.stop()

    if duplikater:
        st.error(
            "Materialenavne skal være unikke. Ret duplikater: "
            + ", ".join(duplikater)
        )
        st.stop()

    if ny_liste != st.session_state["materialer"]:
        st.session_state["materialer"] = ny_liste
        gem_materialer(ny_liste)


# ===========================================================================
# Top-level layout — sidebar + routing
# ===========================================================================

aktiv_side = render_sidebar()

if aktiv_side == "dimensionering":
    st.title("🏗️ Dimensionering")
    st.caption(
        "Beregning af bærelagstykkelse med og uden geonetarmering "
        "· Baseret på BG Byggros designmanualer for Tensar og GS-GRID, samt interne forsøgsdata"
    )

    tilstand = st.radio(
        "Tilstand",
        ["Standard", "Brugerdefineret"],
        horizontal=True,
        key="tilstand",
        help=(
            "**Standard:** Vælg Eu/Cv og belastningsklasse — få en oversigt over "
            "alle geonet-produkter med deres opnåelige bærelagstykkelse.  \n"
            "**Brugerdefineret:** Få en oversigt over alle produkter, eller vælg ét produkt med op til 3 materialelag, "
            "med beregning af vægtet friktionsvinkel"
        ),
    )

    st.caption(
        "I standardberegningen forudsættes 1 homogent bærelag med en forudsat "
        "friktionsvinkel på φ = 35°."
    )

    st.divider()

    if tilstand == "Standard":
        render_standard()
    else:
        render_brugerdefineret()

elif aktiv_side == "materialer":
    render_materialer()

elif aktiv_side == "geonet_database":
    render_geonet_database()

elif aktiv_side == "designdiagrammer":
    render_designdiagrammer()
