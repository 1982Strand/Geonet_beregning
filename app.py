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
import hashlib
import os

from core.data import (
    BELASTNINGSKLASSER,
    GEONET_NAVNE,
    GEONET_DB,
    GEONET_NOTER,
    MATERIAL_DB,
    EU_MIN, EU_MAX,
    K_PHI,
    PHI_BASIS,
    find_geonet,
    cv_til_eu,
    CV_TIL_EU,
    eo_til_klasse,
    T_BASIS_TABLE,
    DESIGNDIAGRAM_RAW_TABLES,
    EO_KOLONNER,
    TRAFIKKOBLING_NOTE,
    format_trafikkobling,
    format_klasse_interval,
)
from core.calculator import (
    beregn,
    beregn_alle_produkter,
    grupper_produkter,
)
from core.validators import valider_input
from core.placement import check_geonet_placement, placement_requirements

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
MIN_LAGTYKKELSE_MM = 200

INFO_VISUALISERING_MD = """**Sådan læses søjlerne**

**Indtastet opbygning** viser brugerens egne tykkelser.

**Ustabiliseret basistykkelse (φ-korrigeret)** er den ustabiliserede *kravtykkelse* fra
designdiagrammet — bestemt af Eu og Eo og korrigeret for den vægtede
friktionsvinkel via formlen
*T_krav = T_basis × (1 + K_PHI·(φ−37))*.
Materialeforholdet fra det indtastede bevares, og krav-tykkelsen fordeles
proportionalt på lagene. Tallene kan derfor være større end de indtastede
— differencen svarer til "Mangler X mm" der vises under søjlen.

**1 lag / 2 lag geonet** viser det stabiliserede krav med samme proportionale
lagfordeling. Det øverste geonet ved 2 lag placeres ved den reducerede
materialegrænse.
"""


INFO_DESIGNDIAGRAM_MD = """**Sådan dannes diagrammet**

Kurverne kommer fra designdiagram-tabellen for det valgte **Eo**: tabellen
giver basis-bærelagstykkelsen (cm) for hver Eu-række og lag-mode
(ustabiliseret / 1 lag / 2 lag).

Basis-tykkelsen ganges med en samlet faktor:

*T = T_basis × (1 + φ-korrektion + net-korrektion)*

- **φ-korrektion** = −0,02 × (φ − 37°) — fra dine materialelag.
- **net-korrektion** — fra det valgte geonet (0 % for reference,
  negativt for stærkere net).

For interval-produkter (fx NX750/NX850) tegnes både den konservative og
optimale kurve med et tonet bånd imellem.

**Prikker på diagrammet**:

- Rød "Din opbygning"-prik sidder ved (indtastet bærelagstykkelse, dit Eu).
- 1-/2-lag-prikkerne viser krævet tykkelse ved netop dit Eu for det valgte
  geonet — fyldt = konservativ, hul cirkel = optimal (kun interval-produkter).
"""


def _vis_billede_med_info(
    png: bytes,
    info_md: str,
    *,
    caption: str | None = None,
    use_container_width: bool = False,
) -> None:
    """Vis PNG med et ℹ️-popover ved siden af.

    Falder tilbage til st.expander hvis st.popover ikke er tilgængelig i
    den installerede Streamlit-version.
    """
    col_img, col_info = st.columns([0.95, 0.05])
    with col_img:
        kwargs = {"width": "stretch" if use_container_width else "content"}
        if caption:
            st.image(png, caption=caption, **kwargs)
        else:
            st.image(png, **kwargs)
    with col_info:
        popover = getattr(st, "popover", None)
        if callable(popover):
            with popover("ℹ️", width="stretch"):
                st.markdown(info_md)
        else:
            with st.expander("ℹ️", expanded=False):
                st.markdown(info_md)


def _vis_opbygning_med_info(png: bytes, *, caption: str | None = None) -> None:
    """Vis opbygnings-PNG med et ℹ️-popover (INFO_VISUALISERING_MD)."""
    _vis_billede_med_info(png, INFO_VISUALISERING_MD, caption=caption)


def _vis_designdiagram_med_info(
    png: bytes,
    *,
    caption: str | None = None,
    use_container_width: bool = False,
) -> None:
    """Vis designdiagram-PNG med et ℹ️-popover (INFO_DESIGNDIAGRAM_MD)."""
    _vis_billede_med_info(
        png, INFO_DESIGNDIAGRAM_MD,
        caption=caption, use_container_width=use_container_width,
    )


def _standard_materialer() -> list[dict]:
    """Returner standardmaterialer i samme format som editoren gemmer."""
    return [
        {
            "navn": str(m.get("navn", "")).strip(),
            "lagtype": m.get("lagtype") or "Bærelag",
            "phi": int(m.get("phi") or PHI_BASIS),
            "max_korn": int(m["max_korn"]) if m.get("max_korn") else None,
            "krav_maskestoerrelse_mm": (
                int(m["krav_maskestoerrelse_mm"])
                if m.get("krav_maskestoerrelse_mm")
                else None
            ),
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
        phi = int(PHI_BASIS)
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

    krav_raw = raw.get("krav_maskestoerrelse_mm")
    if _er_tom_vaerdi(krav_raw):
        krav_maske = None
    else:
        try:
            krav_maske = int(round(float(krav_raw)))
        except (TypeError, ValueError):
            krav_maske = None
        if krav_maske is not None:
            krav_maske = min(max(krav_maske, 0), 500) or None

    return {
        "navn": navn,
        "lagtype": lagtype,
        "phi": phi,
        "max_korn": max_korn,
        "krav_maskestoerrelse_mm": krav_maske,
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


def _backfill_fra_standard(materialer: list[dict]) -> list[dict]:
    """Fyld manglende felter fra MATERIAL_DB når materialets navn matcher.

    Bruges til at migrere gamle gemte JSON-filer der ikke har nye felter
    (fx krav_maskestoerrelse_mm). Eksisterende værdier overskrives ikke.
    """
    standard_by_navn = {m["navn"]: m for m in MATERIAL_DB}
    for materiale in materialer:
        std = standard_by_navn.get(materiale.get("navn"))
        if std is None:
            continue
        if materiale.get("krav_maskestoerrelse_mm") is None:
            std_krav = std.get("krav_maskestoerrelse_mm")
            if std_krav is not None:
                materiale["krav_maskestoerrelse_mm"] = int(std_krav)
    return materialer


def indlaes_materialer() -> list[dict]:
    """Indlæs brugerdefinerede materialer. Fallback til MATERIAL_DB."""
    if os.path.exists(MATERIALER_JSON):
        try:
            with open(MATERIALER_JSON, "r", encoding="utf-8") as f:
                materialer = _normaliser_materialer(json.load(f))
            if materialer and not _duplikerede_materialenavne(materialer):
                return _backfill_fra_standard(materialer)
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
        t_uarmeret = _diagramtal(row.get("t_uarmeret_cm", row.get("Ustabiliseret tykkelse (cm)")))
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
  /* Parentes-sekundærtekst: bruges ved interval-produkter til at vise
     den optimale (best-case) værdi som mindre/gråtone supplerende info. */
  .parentes {{ font-size:0.85em; color:#666; font-weight:400; }}
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
  .bd-basis {{
    font-size:0.82rem; font-weight:500; color:#555;
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

  /* Resultat-tabel (Standard-tilstand) */
  .rt-tabel {{ margin:0.2rem 0 0.3rem; }}
  .rt-head, .rt-sum, .rt-detalje {{
    display:grid;
    grid-template-columns:1.5fr 0.8fr 1.2fr 1.2fr 0.9fr 0.9fr;
    gap:0.5rem;
  }}
  .rt-head, .rt-sum {{ align-items:center; }}
  .rt-head {{
    font-size:0.72rem; color:#666; text-transform:uppercase;
    letter-spacing:0.03em; padding:0 0.6rem 0.35rem;
    border-bottom:2px solid {GRØN};
  }}
  .rt-head .num {{ text-align:right; }}
  .rt-raekke {{ border-bottom:0.5px solid #EEE; }}
  .rt-sum {{
    cursor:pointer; padding:0.5rem 0.6rem; font-size:0.92rem;
    list-style:none;
  }}
  .rt-sum::-webkit-details-marker {{ display:none; }}
  .rt-sum::marker {{ content:""; }}
  .rt-sum .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .rt-tom {{ color:{GRÅ}; }}
  /* Optimal-tooltip for interval-produkter (NX750/NX850) */
  .rt-tip {{ position:relative; cursor:help;
             border-bottom:1px dotted {GRØN}; }}
  .rt-tip-mark {{ font-size:0.6rem; color:{GRØN}; vertical-align:super;
                  margin-left:2px; font-weight:500; letter-spacing:0.02em; }}
  .rt-tip-box {{ display:none; position:absolute; right:0; top:1.6em;
                 width:300px; background:#fff; border:0.5px solid #CCC;
                 border-radius:6px; box-shadow:0 4px 14px rgba(0,0,0,0.13);
                 padding:0.5rem 0.7rem; z-index:60; text-align:left;
                 font-weight:400; white-space:normal; }}
  .rt-tip:hover .rt-tip-box {{ display:block; }}
  .rt-tip-box .rt-dlinje {{ font-size:0.8rem; }}
  .rt-tip-titel {{ display:block; font-size:0.7rem; color:{GRØN};
                   text-transform:uppercase; letter-spacing:0.04em;
                   font-weight:500; margin-bottom:0.25rem; }}
  .rt-tip-resultat {{ border-top:0.5px solid #C0DD97; margin-top:0.15rem;
                      padding-top:0.2rem; font-weight:500; color:#173404; }}
  .rt-chev {{ display:inline-block; width:0.9em; color:{GRÅ};
              transition:transform 0.12s; }}
  details[open] > .rt-sum .rt-chev {{ transform:rotate(90deg); }}
  .rt-navn {{ font-weight:500; }}
  .rt-ref {{ background:#F5F5F5; }}
  .rt-ref .rt-navn {{ font-style:italic; color:#555; font-weight:400; }}
  .rt-bedste {{ background:{LYS_GR}; border-left:3px solid {GRØN}; }}
  .rt-bedste .rt-navn {{ color:#173404; }}
  .rt-badge {{ font-size:0.78rem; padding:1px 9px; border-radius:12px;
               white-space:nowrap; }}
  .rt-badge-ok {{ background:{LYS_GR}; color:#173404; }}
  .rt-badge-advarsel {{ background:#FBE9E7; color:#BF360C; }}
  .rt-detalje {{ align-items:start; padding:0.3rem 0.6rem 0.7rem; }}
  .rt-d-krav {{ grid-column:1 / 3; min-width:0; }}
  .rt-d-krav .rt-dlinje {{ grid-template-columns:230px auto; }}
  .rt-d-krav .rt-dlinje .val {{ text-align:left; padding-left:0; }}
  .rt-d-bd {{ min-width:0; }}
  .rt-d-bd1 {{ grid-column:3 / 4; }}
  .rt-d-bd2 {{ grid-column:4 / 5; }}
  .rt-d-bd .rt-dlinje {{ font-size:0.8rem; }}
  /* 2-lag-kolonnen viser kun værdier — labels står ved 1-lag-kolonnen */
  .rt-d-bd2 .rt-dlinje > span:first-child {{ display:none; }}
  .rt-bd-tom {{ color:{GRÅ}; font-size:0.85rem; text-align:right; }}
  .rt-detalje-tom {{ color:#666; font-size:0.85rem;
                     padding:0.3rem 0.6rem 0.7rem; }}
  .rt-dlinje {{ display:grid; grid-template-columns:1fr auto;
                font-size:0.85rem; padding:0.12rem 0; }}
  .rt-dlinje .val {{ text-align:right; font-variant-numeric:tabular-nums;
                     padding-left:0.75rem; }}
  .rt-graa {{ color:#666; }}
  .rt-spar {{ color:{GRØN}; }}
  .rt-pen {{ color:#BF360C; }}
  .rt-samlet {{ border-top:0.5px solid #C0DD97; margin-top:0.15rem;
                padding-top:0.2rem; font-weight:500; }}
  .rt-krav-titel {{ font-size:0.7rem; color:#888; text-transform:uppercase;
                    letter-spacing:0.04em; margin-bottom:0.15rem; }}
  .rt-caption {{ font-size:0.78rem; color:#666; margin-top:0.5rem; }}

  .cv-eu-wrap {{ margin-top:-10.6rem; }}
  .st-key-kl_diagram_wrap {{ margin-top:-4rem; margin-left:10rem; }}
  .cv-eu-tabel {{ width:100%; max-width:360px; border-collapse:collapse;
                  font-size:0.85rem; margin-top:0.3rem; }}
  .cv-eu-tabel th {{ text-align:left; font-size:0.72rem; color:{GRÅ};
                     text-transform:uppercase; letter-spacing:0.03em;
                     padding:0.25rem 0.5rem; border-bottom:1px solid #DDD; }}
  .cv-eu-tabel td {{ padding:0.25rem 0.5rem; border-bottom:1px solid #EEE; }}
  .cv-row-aktiv td {{ background:{LYS_GR}; font-weight:600; color:#173404; }}
  .cv-eu-note {{ font-size:0.78rem; color:#666; margin-top:0.4rem; }}

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
    """Render Underbund (Eu eller Cv → Eu). Returnerer Eu i MPa."""
    st.subheader("Underbund")
    st.caption(
        "Vælg om underbundens E-modul (Eu) angives direkte, eller udledes ud fra "
        "en korrelation med vingestyrken Cv."
    )

    eu_mode = st.radio(
        "Input-form",
        ["Eu - E-modul (MPa)", "Cv - vingestyrke (kN/m²)"],
        horizontal=True,
        key=f"{key_prefix}_eu_mode",
        label_visibility="collapsed",
    )

    slider_kol, tabel_kol = st.columns([1, 1])

    if eu_mode.startswith("Eu"):
        with slider_kol:
            eu = float(st.slider(
                "Eu (MPa)", min_value=int(EU_MIN), max_value=int(EU_MAX),
                value=10, step=1, key=f"{key_prefix}_eu_slider",
                help="Angiv E-modul for underbunden. Oftest målt ved belastningsforsøg i marken, eller skønnet.",
            ))
        st.caption(f"Valgt **Eu = {eu:.0f} MPa**")
        return eu

    with slider_kol:
        cv = st.slider(
            "Cv (kN/m²)", min_value=0, max_value=180,
            value=60, step=5, key=f"{key_prefix}_cv_slider",
            help="Ukorrigeret vingerstyrke fra feltmåling/markjournal.",
        )
        eu_opslag = cv_til_eu(float(cv))
        if eu_opslag is None:
            st.error("Cv er uden for tabelområdet (0–180 kN/m²).")
            return 10.0
        st.caption(f"Cv = {cv} kN/m²  →  **Eu = {eu_opslag:.0f} MPa**")
    with tabel_kol:
        rækker = []
        for cv_min, cv_max, eu_trin in CV_TIL_EU:
            interval = f"0 – {cv_max}" if cv_min == 0 else f"{cv_min + 1} – {cv_max}"
            css = "cv-row-aktiv" if eu_trin == eu_opslag else ""
            rækker.append(
                f'<tr class="{css}"><td>{eu_trin:.0f} MN/m²</td>'
                f'<td>{interval} kN/m²</td></tr>'
            )
        st.markdown(
            '<div class="cv-eu-wrap">'
            '<table class="cv-eu-tabel">'
            '<thead><tr><th>E-modul på planum Eu</th>'
            '<th>Tilhørende vingestyrke Cv</th></tr></thead>'
            f'<tbody>{"".join(rækker)}</tbody></table>'
            '<p class="cv-eu-note">Relationen mellem E-modul og vingestyrke som '
            'typisk findes for moræneler, gytje og lignende.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    return eu_opslag


def input_belastning(key_prefix: str) -> tuple[int, dict, float]:
    """Render Belastningsklasse som 6 klasse-knapper. Returnerer (klasse, info, eo)."""
    st.subheader("Belastningsklasse")

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
        st.caption(
            f"VD's trafikklassificering (vejledende): {format_trafikkobling(valgt)}"
        )
        with st.expander("Vejdirektoratets trafikklassificering"):
            st.write(TRAFIKKOBLING_NOTE)
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
            with st.container(key="kl_diagram_wrap"):
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
    """Komprimér klasseliste til intervaller (delt helper i core.data)."""
    return format_klasse_interval(klasser)


def _produkt_label(navn: str) -> str:
    """Dropdown-label: produktnavn + anbefalede klasser, fx
    'GS-GRID SX170 (Klasse 4-6)'.

    Bemærk: Streamlit-dropdownen kan ikke farve en del af teksten, så
    klasse-delen vises i samme farve som navnet (kun captionen nedenunder
    kan vises nedtonet).
    """
    g = find_geonet(navn)
    kl = g.get("klasser") if g else None
    if kl:
        return f"{navn} (Klasse {_format_klasse_liste(kl)})"
    return navn


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


def _bd_reduktion_opdeling_html(
    basis_uarm: float | None,
    t_basis: float | None,
    phi: float,
    produkter: list[dict],
    interval_p: dict | None,
) -> str:
    """Brugerdefineret: opdel reduktionen i basis-, φ- og net-bidrag.

    Returnerer HTML med op til tre linjer:
      Basisreduktion: xx mm
      φ-korrektion for φ = xx,x°: xx mm (xx %)
      Net-korrektion (xx %): xx mm ift reference
    Net-linjen vises som interval (xx %/xx % opt.) for interax-produkter.
    Retning angives via farve (blå = reduktion, rød = forøgelse).
    """
    if not t_basis or t_basis <= 0:
        return ""
    linjer: list[str] = []

    # Basisreduktion — ren diagram-forskel uden korrektioner.
    if basis_uarm:
        basis_red = round(basis_uarm - t_basis)
        linjer.append(
            f'<div class="bd-basis">Basisreduktion: {basis_red} mm</div>'
        )

    # φ-korrektion — kun hvis φ afviger fra basis.
    if abs(phi - PHI_BASIS) > 0.05:
        phi_kor = K_PHI * (phi - PHI_BASIS)
        phi_mm = round(t_basis * phi_kor)
        phi_pct = round(phi_kor * 100)
        phi_str = f"{phi:.1f}".replace(".", ",")
        css = "net-kor-spar" if phi_mm <= 0 else "net-kor-pen"
        linjer.append(
            f'<div class="{css}">'
            f'φ-korrektion for φ = {phi_str}°: '
            f'{phi_mm:+d} mm ({phi_pct:+d}%)'
            f'</div>'
        )

    # Net-korrektion — interval (interax) eller enkelt værdi.
    if interval_p is not None and interval_p.get("korrektion_min") is not None:
        kor_opt = interval_p["korrektion_min"]    # største reduktion (optimal)
        kor_kons = interval_p["korrektion_max"]   # mindste reduktion (konservativ)
        mm_kons = round(t_basis * kor_kons)
        mm_opt = round(t_basis * kor_opt)
        pct_kons = round(kor_kons * 100)
        pct_opt = round(kor_opt * 100)
        linjer.append(
            f'<div class="net-kor-spar">'
            f'Net-korrektion ({pct_kons:+d}%/{pct_opt:+d}% opt.) ift. reference: '
            f'{mm_kons:+d} mm /{mm_opt:+d} mm (opt.)'
            f'</div>'
        )
    else:
        kor = produkter[0].get("korrektion", 0.0) if produkter else 0.0
        if abs(kor) < 0.005:
            linjer.append(
                '<div class="net-kor-ref">referenceprodukt (0 % korrektion)</div>'
            )
        else:
            net_mm = round(t_basis * kor)
            net_pct = round(kor * 100)
            css = "net-kor-spar" if net_mm <= 0 else "net-kor-pen"
            linjer.append(
                f'<div class="{css}">'
                f'Net-korrektion ({net_pct:+d}%) ift. reference: '
                f'{net_mm:+d} mm'
                f'</div>'
            )

    return "".join(linjer)


def _render_gruppe_kort(
    gruppe: dict,
    primaer: bool,
    phi: float = PHI_BASIS,
    valgt_klasse: int | None = None,
    brugerdefineret: bool = False,
) -> None:
    """
    Render én tykkelses-gruppe som kort.
    primaer=True ⇒ fremhævet grønt kort (bedste). False ⇒ dæmpet grå variant.
    brugerdefineret=True ⇒ vis 3-linje reduktionsopdeling (basis/φ/net) i
    stedet for de simple φ-/net-korrektionslinjer.
    """
    t_vis   = gruppe["t_armeret_mm"]
    red_pct = gruppe["reduktion_pct"]

    # Basis-ustabiliseret tykkelse (rå tabelopslag uden korrektioner). Alle
    # produkter i gruppen deler samme eu/eo/lag_mode og dermed samme basis.
    # Reduktionen i headline vises ift. denne basistykkelse i begge tilstande.
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
            # Konservativ (større tykkelse) som hovedværdi, optimal i parentes
            tal_html = (
                f'{t_high_vis:.0f} mm'
                f'<span class="parentes" style="margin-left:8px">'
                f'({t_low_vis:.0f} mm)</span>'
            )
    else:
        t_low_vis = None
        t_high_vis = round(t_vis)
        tal_html = f'{t_vis:.0f} mm'

    # ↓ mm-reduktionslinje. Format: "Reduceres ↓ {kons} mm → {pct}% (↓ {best} mm → {pct}%)"
    # Konservativ ende (mindst reduktion) er hovedværdi, best-case i parentes.
    if interval_p is not None and t_uarm_prod is not None and t_low_vis is not None:
        red_mm_best = round(t_uarm_prod - t_low_vis)    # største reduktion (best case)
        red_mm_kons = round(t_uarm_prod - t_high_vis)   # mindste reduktion (konservativ)
        red_pct_best = red_mm_best / t_uarm_prod if t_uarm_prod > 0 else 0
        red_pct_kons = red_mm_kons / t_uarm_prod if t_uarm_prod > 0 else 0
        if t_low_vis == t_high_vis:
            red_linje = (
                f'<div class="gruppe-red-linje">'
                f'Reduceret i alt {red_mm_best} mm → {red_pct_best:.0%}'
                f'</div>'
            )
        else:
            red_linje = (
                f'<div class="gruppe-red-linje">'
                f'Reduceret i alt {red_mm_kons} mm → {red_pct_kons:.0%} '
                f'<span class="parentes">'
                f'({red_mm_best} mm → {red_pct_best:.0%})'
                f'</span>'
                f'</div>'
            )
    elif t_uarm_prod:
        red_mm = round(t_uarm_prod - t_vis)
        red_pct_val = red_mm / t_uarm_prod if t_uarm_prod > 0 else 0
        red_linje = (
            f'<div class="gruppe-red-linje">Reduceret i alt {red_mm} mm → {red_pct_val:.0%}</div>'
        )
    else:
        red_linje = ""

    # Brugerdefineret: opdel reduktionen i basis-, φ- og net-bidrag.
    breakdown_html = (
        _bd_reduktion_opdeling_html(
            t_uarm_prod, gruppe.get("t_basis_arm_mm"), phi,
            gruppe.get("produkter") or [], interval_p,
        )
        if brugerdefineret else ""
    )

    # φ-korrektionslinje — vises kun hvis phi ≠ 37°
    phi_kor_html = ""
    t_basis = gruppe.get("t_basis_arm_mm")
    if t_basis and t_basis > 0 and abs(phi - PHI_BASIS) > 0.05:
        phi_kor = -0.02 * (phi - PHI_BASIS)
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
                # Laveste effektindeks (konservativ, mindst reduktion) først;
                # højeste effektindeks (best-case, mest reduktion) i parentes.
                tekst = (
                    f'net-kor: {d_hi:+d} mm ({pct_hi:+d}%) '
                    f'<span class="parentes">'
                    f'({d_lo:+d} mm / {pct_lo:+d}%)</span>'
                    f', ift. reference'
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
        f'{breakdown_html if brugerdefineret else phi_kor_html + net_kor_html}'
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
    # Reduktion sammenlignes mod den φ-korrigerede uarmerede reference,
    # så begge sider af regnestykket er konsistent korrigeret for materiale.
    t_uarm_ref = res.get("t_uarmeret_phi_kor_mm") or t_uarm
    red_eks = (t_uarm_ref - t_eks) / t_uarm_ref if t_uarm_ref else None

    produkt = {
        "navn":           geonet["navn"],
        "serie":          geonet["serie"],
        "korrektion":     geonet["korrektion"],
        "t_armeret_mm":   t_eks,
        "t_uarmeret_mm":  t_uarm,
        "t_uarmeret_phi_kor_mm": res.get("t_uarmeret_phi_kor_mm"),
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "reduktion_mm":   t_uarm_ref - t_eks if t_uarm_ref is not None else None,
        "reduktion_pct":  red_eks,
        "klasse_ok":      valgt_klasse in geonet["klasser"],
        "klasser":        geonet["klasser"],
        "min_daklag":     geonet["min_daklag"],
        "max_korn":       geonet["max_korn"],
        "fejl":           None,
    }
    for key in (
        "placering_ok", "geonet_placeringer_mm_fra_top", "geonet_y_fracs",
        "topdaeklag_mm", "afstande_mellem_geonet_mm", "placeringsadvarsler",
        "t_min_placering_mm", "t_dimensionerende_mm", "min_top_cover_mm",
        "min_spacing_mm", "max_spacing_mm", "placeringsbasis",
    ):
        if key in res:
            produkt[key] = res[key]
    return {
        "t_armeret_mm":         round(t_eks, 0),
        "t_armeret_eksakt_mm":  round(t_eks, 0),
        "reduktion_pct":        round(red_eks, 4) if red_eks is not None else None,
        "reduktion_pct_eksakt": round(red_eks, 4) if red_eks is not None else None,
        "t_basis_arm_mm":       res.get("t_basis_arm_mm"),
        "produkter":            [produkt],
        "placering_ok":         produkt.get("placering_ok", True),
        "har_fejl":             False,
        "fejl_besked":          None,
    }


def _reference_resultat_til_gruppe(res: dict, valgt_klasse: int) -> dict | None:
    """Pak neutral referenceberegning som en gruppe til referencevisning."""
    if res.get("fejl") or res.get("t_armeret_mm") is None:
        return None
    if "placering_ok" not in res:
        res = {
            **res,
            **check_geonet_placement(
                lag_mode=res.get("lag_mode"),
                total_mm=res.get("t_armeret_mm"),
                geonet=None,
            ),
        }

    t_ref = res["t_armeret_mm"]
    t_uarm = res["t_uarmeret_mm"]
    # Reduktion mod φ-korrigeret reference (se _resultat_til_gruppe).
    t_uarm_ref = res.get("t_uarmeret_phi_kor_mm") or t_uarm
    red_ref = (t_uarm_ref - t_ref) / t_uarm_ref if t_uarm_ref else None
    produkt = {
        "navn": REFERENCE_NAVN,
        "serie": "Reference",
        "korrektion": 0.0,
        "t_armeret_mm": t_ref,
        "t_uarmeret_mm": t_uarm,
        "t_uarmeret_phi_kor_mm": res.get("t_uarmeret_phi_kor_mm"),
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "reduktion_mm": t_uarm_ref - t_ref if t_uarm_ref is not None else None,
        "reduktion_pct": red_ref,
        "klasse_ok": valgt_klasse in REFERENCE_KLASSER,
        "klasser": REFERENCE_KLASSER,
        "min_daklag": None,
        "max_korn": None,
        "fejl": None,
    }
    for key in (
        "placering_ok", "geonet_placeringer_mm_fra_top", "geonet_y_fracs",
        "topdaeklag_mm", "afstande_mellem_geonet_mm", "placeringsadvarsler",
        "t_min_placering_mm", "t_dimensionerende_mm", "min_top_cover_mm",
        "min_spacing_mm", "max_spacing_mm", "placeringsbasis",
    ):
        if key in res:
            produkt[key] = res[key]
    return {
        "t_armeret_mm": round(t_ref, 0),
        "t_armeret_eksakt_mm": round(t_ref, 0),
        "reduktion_pct": round(red_ref, 4) if red_ref is not None else None,
        "reduktion_pct_eksakt": round(red_ref, 4) if red_ref is not None else None,
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "produkter": [produkt],
        "placering_ok": produkt.get("placering_ok", True),
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
    phi: float = PHI_BASIS,
    brugerdefineret: bool = False,
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
            _render_gruppe_kort(ref_1, primaer=True, phi=phi, valgt_klasse=valgt_klasse,
                                brugerdefineret=brugerdefineret)
        else:
            st.info(fejl_1 or "Ingen gyldigt 1-lag-resultat for referencenettet.")
    with col_2:
        st.markdown('<div class="kol-titel">2 LAG REFERENCENET</div>', unsafe_allow_html=True)
        if ref_2 is not None:
            _render_gruppe_kort(ref_2, primaer=True, phi=phi, valgt_klasse=valgt_klasse,
                                brugerdefineret=brugerdefineret)
        else:
            st.info(fejl_2 or "Ingen gyldigt 2-lag-resultat for referencenettet.")


def _render_uarmeret_mangler_besked(eu: float, eo: float) -> None:
    st.warning(
        "Der er ikke defineret nogen ustabiliseret bærelagstykkelse for "
        f"det valgte Eu/Eo ({eu:.0f} MPa / {eo:.0f} MPa). "
        "Stabiliserede resultater vises stadig, hvor designdiagrammet har data."
    )


def _render_lag_kolonne(
    titel: str,
    grupper: list[dict],
    valgt_klasse: int,
    lag_mode: str,
    tom_besked: str | None = None,
    phi: float = PHI_BASIS,
    brugerdefineret: bool = False,
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

    st.markdown('<div class="bedste-label">Stabiliseret bærelagstykkelse</div>',
                unsafe_allow_html=True)
    _render_gruppe_kort(bedste, primaer=True, phi=phi, valgt_klasse=valgt_klasse,
                        brugerdefineret=brugerdefineret)

    if rest:
        label = (
            f"Vis {len(rest)} flere mulighed"
            f"{'er' if len(rest) > 1 else ''}"
        )
        with st.expander(label, expanded=False):
            for g in rest:
                _render_gruppe_kort(g, primaer=False, phi=phi, valgt_klasse=valgt_klasse,
                                    brugerdefineret=brugerdefineret)


# ---------------------------------------------------------------------------
# Standard-tilstand: produkt-tabel (én række pr. produkt, foldbar)
# ---------------------------------------------------------------------------

# Referencerækkens label i tabellen — fulde produktnavne (≠ REFERENCE_NAVN,
# der bruges til produkt-matchning andre steder).
REFERENCE_NAVN_TABEL = "Referencenet (SX160 / T6 / TriAx TX160)"


def _rt_gyldig(p: dict | None) -> bool:
    """True hvis produkt-dict'en har et gyldigt beregningsresultat."""
    return bool(
        p and p.get("fejl") is None and p.get("t_armeret_mm") is not None
    )


def _rt_reduktion_linjer(
    p: dict | None,
    is_ref: bool,
    *,
    kor: float | None = None,
    t_arm: float | None = None,
) -> str:
    """Reduktions-opdeling for ÉT lag (basis/net/samlet) som fortegns-deltaer.

    De tre linjer summer: basisreduktion (grå, negativ) + net-korrektion
    (grøn hvis sparer, rød hvis koster) = samlet reduktion (grå, overstreg).
    Returnerer en dæmpet '—' hvis laget ikke har et gyldigt resultat.

    kor/t_arm kan overskrives (fx til interval-produkternes optimale værdier);
    default er produktets konservative korrektion/tykkelse. Basisreduktionen er
    uafhængig af korrektionen (ren diagram-forskel). Linjerne udskrives med
    <span>-wrappers, så de også er gyldige inde i et tooltip-<span>.
    """
    if not _rt_gyldig(p):
        return '<span class="rt-bd-tom">—</span>'

    t_uarm = p.get("t_uarmeret_mm")
    t_basis = p.get("t_basis_arm_mm")
    if kor is None:
        kor = p.get("korrektion") or 0.0
    if t_arm is None:
        t_arm = p["t_armeret_mm"]
    linjer: list[str] = []

    if t_uarm is not None and t_basis is not None:
        basis_delta = -round(t_uarm - t_basis)
        linjer.append(
            '<span class="rt-dlinje rt-graa">'
            '<span>Basisreduktion</span>'
            f'<span class="val">{basis_delta:+d} mm</span></span>'
        )

    if t_basis is not None:
        if abs(kor) < 0.005 and is_ref:
            linjer.append(
                '<span class="rt-dlinje rt-graa">'
                '<span>Net-korrektion ift. reference</span>'
                '<span class="val">referenceprodukt (0 %)</span></span>'
            )
        elif abs(kor) < 0.005:
            linjer.append(
                '<span class="rt-dlinje rt-graa">'
                '<span>Net-korrektion (0 %) ift. reference</span>'
                '<span class="val">0 mm</span></span>'
            )
        else:
            net_mm = round(t_basis * kor)
            net_pct = round(kor * 100)
            css = "rt-spar" if net_mm <= 0 else "rt-pen"
            linjer.append(
                f'<span class="rt-dlinje {css}">'
                f'<span>Net-korrektion ({net_pct:+d} %) ift. reference</span>'
                f'<span class="val">{net_mm:+d} mm</span></span>'
            )

    if t_uarm is not None:
        samlet_delta = -round(t_uarm - t_arm)
        linjer.append(
            '<span class="rt-dlinje rt-graa rt-samlet">'
            '<span>Samlet reduktion</span>'
            f'<span class="val">{samlet_delta:+d} mm</span></span>'
        )

    return "".join(linjer)


def _rt_optimal_tip_html(p: dict | None) -> str:
    """Tooltip-indhold: optimal opdeling for et interval-produkt (ét lag).

    Returnerer "" hvis produktet ikke er et interval-produkt (intet
    t_armeret_mm_min). Genbruger _rt_reduktion_linjer med de optimale værdier.
    """
    if not _rt_gyldig(p) or p.get("t_armeret_mm_min") is None:
        return ""
    kor_opt = p.get("korrektion_min")
    t_opt = p["t_armeret_mm_min"]
    pct_opt = p.get("reduktion_pct_max")
    linjer = _rt_reduktion_linjer(p, False, kor=kor_opt, t_arm=t_opt)
    pct_txt = f" (↓ {pct_opt:.0%})" if pct_opt is not None else ""
    return (
        '<span class="rt-tip-box">'
        '<span class="rt-tip-titel">Under optimale forhold</span>'
        f'{linjer}'
        '<span class="rt-dlinje rt-tip-resultat">'
        '<span>Optimal bærelagstykkelse</span>'
        f'<span class="val">{int(round(t_opt))} mm{pct_txt}</span></span>'
        '</span>'
    )


def _rt_tk_celle(p: dict | None, valid: bool, t_txt: str, cls: str) -> str:
    """Tykkelse-celle. For interval-produkter pakkes værdien i et hover-tooltip
    med den optimale beregning; ellers vises bare værdien."""
    if valid and p is not None and p.get("t_armeret_mm_min") is not None:
        tip = _rt_optimal_tip_html(p)
        return (
            f'<span class="{cls}">'
            f'<span class="rt-tip">{t_txt}'
            f'<span class="rt-tip-mark">opt.</span>'
            f'{tip}</span></span>'
        )
    return f'<span class="{cls}">{t_txt}</span>'


def _rt_detalje_html(
    navn: str,
    p1: dict | None,
    p2: dict | None,
    is_ref: bool = False,
) -> str:
    """Foldbar detalje justeret efter tabellens kolonner.

    Layout (samme grid som tabellen): 'Krav til nettet' til venstre (under
    Produkt/klasse), 1-lags reduktions-opdeling under '...1 lag geonet' og
    2-lags under '...2 lag geonet'.
    """
    if not (_rt_gyldig(p1) or _rt_gyldig(p2)):
        return (
            '<div class="rt-detalje-tom">'
            'Ingen gyldig beregning for denne kombination.</div>'
        )

    # Krav til nettet — uafhængig af lag.
    geonet = None if is_ref else find_geonet(navn)
    krav = placement_requirements(geonet)
    tilslag = (geonet or {}).get("anbefalet_tilslag") or "—"
    krav_html = (
        '<div class="rt-d-krav">'
        '<div class="rt-krav-titel">Krav til nettet</div>'
        '<div class="rt-dlinje rt-graa"><span>Minimum dæklag over geonet</span>'
        f'<span class="val">{krav["min_top_cover_mm"]:.0f} mm</span></div>'
        '<div class="rt-dlinje rt-graa"><span>Anbefalet afstand imellem geonetlag</span>'
        f'<span class="val">{krav["min_spacing_mm"]:.0f}–{krav["max_spacing_mm"]:.0f} mm</span></div>'
        '<div class="rt-dlinje rt-graa"><span>Anbefalet tilslagsstørrelse</span>'
        f'<span class="val">{tilslag}</span></div>'
        '</div>'
    )

    bd1 = _rt_reduktion_linjer(p1, is_ref)
    bd2 = _rt_reduktion_linjer(p2, is_ref)

    return (
        '<div class="rt-detalje">'
        f'{krav_html}'
        f'<div class="rt-d-bd rt-d-bd1">{bd1}</div>'
        f'<div class="rt-d-bd rt-d-bd2">{bd2}</div>'
        '</div>'
    )


def _rt_red_txt(p: dict | None) -> str:
    """Reduktionstekst for ét lag: '{mm} mm ({pct})' eller '—'."""
    if not _rt_gyldig(p):
        return "—"
    pct = p.get("reduktion_pct")
    mm = p.get("reduktion_mm")
    if pct is not None and mm is not None:
        return f'{int(round(mm))} mm ({pct:.0%})'
    if pct is not None:
        return f'{pct:.0%}'
    return "—"


def _rt_raekke_html(
    navn: str,
    p1: dict | None,
    p2: dict | None,
    *,
    is_ref: bool = False,
    is_bedste: bool = False,
) -> str:
    """Byg én foldbar tabelrække (<details>) for et produkt/referencenet."""
    v1 = _rt_gyldig(p1)
    v2 = _rt_gyldig(p2)
    chosen = p1 if v1 else (p2 if v2 else (p1 or p2 or {}))

    klasser = chosen.get("klasser") or []
    klasse_ok = chosen.get("klasse_ok", True)
    kl_txt = _format_klasse_liste(klasser) if klasser else "—"
    badge_css = "rt-badge-ok" if klasse_ok else "rt-badge-advarsel"
    badge_pre = "" if klasse_ok else "⚠️ "

    t1 = f'{int(round(p1["t_armeret_mm"]))}' if v1 else "—"
    t2 = f'{int(round(p2["t_armeret_mm"]))}' if v2 else "—"
    t1_cls = "num" if v1 else "num rt-tom"
    t2_cls = "num" if v2 else "num rt-tom"

    red1_txt = _rt_red_txt(p1)
    red2_txt = _rt_red_txt(p2)
    red1_cls = "num" if v1 else "num rt-tom"
    red2_cls = "num" if v2 else "num rt-tom"

    raekke_css = "rt-raekke"
    if is_ref:
        raekke_css += " rt-ref"
    elif is_bedste:
        raekke_css += " rt-bedste"

    return (
        f'<details class="{raekke_css}">'
        f'<summary class="rt-sum">'
        f'<span class="rt-navn"><span class="rt-chev">▸</span> {navn}</span>'
        f'<span><span class="rt-badge {badge_css}">{badge_pre}{kl_txt}</span></span>'
        f'{_rt_tk_celle(p1, v1, t1, t1_cls)}'
        f'{_rt_tk_celle(p2, v2, t2, t2_cls)}'
        f'<span class="{red1_cls}">{red1_txt}</span>'
        f'<span class="{red2_cls}">{red2_txt}</span>'
        f'</summary>'
        f'{_rt_detalje_html(navn, p1, p2, is_ref)}'
        f'</details>'
    )


def _render_produkt_tabel(
    ref_1: dict | None,
    ref_2: dict | None,
    ref_fejl_1: str | None,
    ref_fejl_2: str | None,
    prod_1lag: list[dict],
    prod_2lag: list[dict],
    valgt_klasse: int,
) -> None:
    """Standard-tilstandens resultattabel: én foldbar række pr. produkt.

    Referencenettet øverst som basis, derefter produkter med tyndeste
    1-lag-bærelag først (tyndeste gyldige fremhævet grønt). 1-lag og 2-lag
    vises som kolonner; detaljer (reduktions-opdeling) skjules i fold-ud.
    """
    refp1 = ref_1["produkter"][0] if ref_1 and ref_1.get("produkter") else None
    refp2 = ref_2["produkter"][0] if ref_2 and ref_2.get("produkter") else None

    p1_by = {p["navn"]: p for p in prod_1lag}
    p2_by = {p["navn"]: p for p in prod_2lag}
    navne = list(p1_by.keys())
    for n in p2_by:
        if n not in p1_by:
            navne.append(n)

    # Bedste = tyndeste gyldige 1-lag (prod_1lag er sorteret tyndeste først);
    # ellers tyndeste gyldige 2-lag.
    bedste_navn = next((n for n in navne if _rt_gyldig(p1_by.get(n))), None)
    if bedste_navn is None:
        bedste_navn = next((n for n in navne if _rt_gyldig(p2_by.get(n))), None)

    dele = ['<div class="rt-tabel">']
    dele.append(
        '<div class="rt-head">'
        '<span>Produkt</span>'
        '<span>Anbefalet belastningsklasse</span>'
        '<span class="num">Bærelagstykkelse, 1 lag geonet</span>'
        '<span class="num">Bærelagstykkelse, 2 lag geonet</span>'
        '<span class="num">Reduktion i alt, 1 lag</span>'
        '<span class="num">Reduktion i alt, 2 lag</span>'
        '</div>'
    )
    dele.append(_rt_raekke_html(REFERENCE_NAVN_TABEL, refp1, refp2, is_ref=True))
    for n in navne:
        p1 = p1_by.get(n)
        p2 = p2_by.get(n)
        if not (_rt_gyldig(p1) or _rt_gyldig(p2)):
            continue
        dele.append(_rt_raekke_html(n, p1, p2, is_bedste=(n == bedste_navn)))
    dele.append('</div>')
    dele.append(
        '<div class="rt-caption">Referencenet vises øverst, derefter de mest '
        'effektive produkter først. Klik på hver række for flere detaljer</div>'
    )
    st.markdown("".join(dele), unsafe_allow_html=True)


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
    if (
        "dæklag" in advarsel
        or "minimumsdæklag" in advarsel
        or "under oversiden" in advarsel
    ):
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


def _krav_for_gruppe(gruppe: dict) -> tuple[str, str, str, str]:
    """
    Returner (navne, min_dæklag_str, max_korn_str) for visning af
    udførelseskrav for produkterne i en bedste-gruppe.

    Hvis alle produkter har samme værdi vises kun det ene tal.
    Hvis de varierer vises et interval med en lille forklaring.
    """
    produkter = gruppe["produkter"]
    navne = ", ".join(p["navn"] for p in produkter)

    # min_daklag er i cm i GEONET_DB → konvertér til mm
    dk_unik = sorted({
        p.get("min_top_cover_mm")
        if p.get("min_top_cover_mm") is not None
        else max(200, p["min_daklag"] * 10)
        for p in produkter
    })
    if len(dk_unik) == 1:
        dk_str = f"{dk_unik[0]:.0f} mm"
    else:
        dk_str = f"{dk_unik[0]:.0f}–{dk_unik[-1]:.0f} mm (varierer pr. produkt)"

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

    min_afst = sorted({p.get("min_spacing_mm", 200) for p in produkter})
    max_afst = sorted({p.get("max_spacing_mm", 400) for p in produkter})
    if len(min_afst) == 1 and len(max_afst) == 1:
        afstand_str = f"{min_afst[0]:.0f}–{max_afst[0]:.0f} mm"
    else:
        afstand_str = (
            f"{min(min_afst):.0f}–{max(max_afst):.0f} mm "
            "(varierer pr. produkt)"
        )

    return navne, dk_str, korn_str, afstand_str


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


def _sub_lag_skaleret_fra_materialer(
    materialer: list[dict] | None, total_mm: float | None
) -> list[dict]:
    """Returnér materialer skaleret så summen = total_mm.

    Bruger mm-mode (m["tykkelse_mm"]) hvis nogen lag har det sat,
    ellers pct-mode (m["pct"]). Lag med 0/None bidrag filtreres væk.
    """
    if not materialer or not total_mm:
        return []
    in_mm_mode = any((m.get("tykkelse_mm") or 0) > 0 for m in materialer)
    if in_mm_mode:
        sum_t = sum((m.get("tykkelse_mm") or 0) for m in materialer)
        if sum_t <= 0:
            return []
        return [
            {
                "navn": m.get("navn", "Lag"),
                "tykkelse_mm": (m.get("tykkelse_mm") or 0) * total_mm / sum_t,
            }
            for m in materialer if (m.get("tykkelse_mm") or 0) > 0
        ]
    sum_p = sum((m.get("pct") or 0) for m in materialer)
    if sum_p <= 0:
        return []
    return [
        {
            "navn": m.get("navn", "Lag"),
            "tykkelse_mm": (m.get("pct") or 0) / sum_p * total_mm,
        }
        for m in materialer if (m.get("pct") or 0) > 0
    ]


def _sub_lag_uarmeret_fra_materialer(
    materialer: list[dict] | None, t_uarm: float | None
) -> tuple[float | None, list[dict]]:
    """Uarmeret-snittet: brug brugerens dimensionerede tykkelser (mm-mode).
    I pct-mode (eller uden materialer) falder vi tilbage på t_uarm-beregningen.
    """
    materialer = materialer or []
    in_mm_mode = any((m.get("tykkelse_mm") or 0) > 0 for m in materialer)
    if in_mm_mode:
        lag = [
            {
                "navn": m.get("navn", "Lag"),
                "tykkelse_mm": float(m.get("tykkelse_mm") or 0),
            }
            for m in materialer if (m.get("tykkelse_mm") or 0) > 0
        ]
        total = sum(l["tykkelse_mm"] for l in lag)
        return (total if total > 0 else None, lag)
    return (
        t_uarm,
        _sub_lag_skaleret_fra_materialer(materialer, t_uarm) if t_uarm else [],
    )


def _berig_resultat_med_placering(
    res: dict,
    geonet: dict | None,
    materialer: list[dict] | None,
) -> dict:
    # Koncept A: placement evalueres i krav-tykkelsen (uden brugerens
    # lagfordeling). sub_lag=None tvinger min_daklag-reglen — det er den
    # korrekte fortolkning, da diagrammets krav ikke har en lagstruktur.
    # `materialer` bevares som parameter for bagudkompatibilitet.
    del materialer
    if res.get("fejl") or res.get("t_armeret_mm") is None:
        return res
    return {
        **res,
        **check_geonet_placement(
            lag_mode=res.get("lag_mode"),
            total_mm=res.get("t_armeret_mm"),
            geonet=geonet,
            sub_lag=None,
        ),
    }


def _berig_produkter_med_placering(
    produkter: list[dict],
    lag_mode: str,
    materialer: list[dict] | None,
) -> list[dict]:
    # Koncept A: se _berig_resultat_med_placering.
    del materialer
    berigede: list[dict] = []
    for produkt in produkter:
        if produkt.get("fejl") or produkt.get("t_armeret_mm") is None:
            berigede.append(produkt)
            continue
        geonet = find_geonet(produkt["navn"])
        opdateret = {
            **produkt,
            **check_geonet_placement(
                lag_mode=lag_mode,
                total_mm=produkt.get("t_armeret_mm"),
                geonet=geonet,
                sub_lag=None,
            ),
        }
        if produkt.get("t_armeret_mm_min") is not None:
            opdateret["placering_best"] = check_geonet_placement(
                lag_mode=lag_mode,
                total_mm=produkt.get("t_armeret_mm_min"),
                geonet=geonet,
                sub_lag=None,
            )
        berigede.append(opdateret)
    return berigede


def _geonet_fracs_for_snit(
    lag_mode: str,
    total_mm: float | None,
    geonet: dict | None,
    sub_lag: list[dict] | None,
) -> tuple[list[float], dict | None]:
    if total_mm is None:
        return [], None
    placement = check_geonet_placement(
        lag_mode=lag_mode,
        total_mm=total_mm,
        geonet=geonet,
        sub_lag=sub_lag,
    )
    return placement.get("geonet_y_fracs", []), placement


def _geonet_fracs_kravsoejle(
    lag_mode: str,
    total_mm: float | None,
    geonet: dict | None,
    sub_lag: list[dict] | None = None,
) -> tuple[list[float], dict | None]:
    """Geonet-placering i en krav-søjle (Koncept A).

    Hvis sub_lag er givet (brugerdefineret-tilstand med ≥2 materialelag,
    proportionalt skaleret til den reducerede totaltykkelse), placeres
    øverste geonet ved materialegrænsen mellem lag 0 og lag 1. Ellers
    bruges produktets min_daklag som top-position. Bunden af bærelaget
    får altid det nederste geonet.
    """
    if total_mm is None or total_mm <= 0:
        return [], None
    placement = check_geonet_placement(
        lag_mode=lag_mode,
        total_mm=total_mm,
        geonet=geonet,
        sub_lag=sub_lag,
    )
    return placement.get("geonet_y_fracs", []), placement


def _status_for_krav(
    t_indtastet: float | None,
    t_krav: float | None,
    t_krav_best: float | None = None,
) -> tuple[str | None, str | None]:
    """Returnér (status_tekst, status_farve) for sammenligning af indtastet vs krav.

    Format (interval-produkter): konservativ værdi som hovedlinje + optimal
    værdi i parentes som anden linje (adskilt med \\n). Render-funktionen
    håndterer linjeskiftet visuelt.
    """
    if t_indtastet is None or t_krav is None:
        return None, None
    diff_kons = t_indtastet - t_krav  # negativ = mangler, positiv = besparelse
    diff_best = (
        t_indtastet - t_krav_best
        if t_krav_best is not None and t_krav_best < t_krav
        else None
    )

    # Hvis konservativ er tilstrækkelig → grøn (besparelse)
    if diff_kons >= 0:
        if diff_best is not None and diff_best > diff_kons:
            return (
                f"✓ Besparelse {diff_kons:.0f} mm\n({diff_best:.0f} mm)",
                "success",
            )
        return f"✓ Besparelse {diff_kons:.0f} mm", "success"

    # Hvis best-case er tilstrækkelig men konservativ ikke → orange (interval)
    if diff_best is not None and diff_best >= 0:
        return (
            f"Mangler {-diff_kons:.0f} mm (best: ✓ +{diff_best:.0f} mm)",
            "warning",
        )

    # Begge mangler → rød. Konservativ stor (størst mangler), optimal i parentes.
    if diff_best is not None:
        return (
            f"Mangler {-diff_kons:.0f} mm\n({-diff_best:.0f} mm)",
            "danger",
        )
    return f"Mangler {-diff_kons:.0f} mm", "danger"


def _render_opbygningsvisualisering(
    eu: float,
    ref_1: dict | None,
    ref_2: dict | None,
    prod_1lag: list[dict] | None = None,
    prod_2lag: list[dict] | None = None,
    materialer: list[dict] | None = None,
    phi: float = PHI_BASIS,
    tvunget_produkt: str | None = None,
) -> None:
    """Tre eller fire opbygnings-snit side om side (Koncept A).

    I Brugerdefineret-tilstand (materialer != []) vises fire søjler:
    "Indtastet opbygning" + tre krav-søjler (Uarmeret/1 lag/2 lag).
    I Standard-tilstand vises de tre krav-søjler alene.

    Hvis prod_1lag/prod_2lag er givet OG tvunget_produkt er None, vises en
    dropdown der lader brugeren skifte til et hvilket som helst gyldigt
    produkt fra resultatlisten. Hvis tvunget_produkt er sat (Brugerdefineret
    → 'Vælg specifikt produkt'), bruges det navn direkte uden dropdown.

    Renderes via samme matplotlib-funktion (rapport.render_opbygning_png)
    som bruges i rapportgenereringen — så preview i dim. og rapport er ens.
    """
    from core import rapport as rapport_mod
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
    if tvunget_produkt is not None:
        # Brugerdefineret 'Vælg specifikt produkt': dropdown skjules, det
        # valgte produkt bruges direkte. Hvis produktet ikke er i listen
        # (fx kun gyldigt i én lag-mode) bruges det alligevel.
        valg = tvunget_produkt
        st.caption(f"Viser opbygning for: **{tvunget_produkt}**")
    elif navne_sorteret:
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
        valgt_geonet = None
        geonet_label = "Tensar TriAx 160 / GS-GRID SX160 / E'GRID T6"
    else:
        t_1 = _produkt_t(prod_1lag, valg)
        t_2 = _produkt_t(prod_2lag, valg)
        t_1_best = _produkt_t_best(prod_1lag, valg)
        t_2_best = _produkt_t_best(prod_2lag, valg)
        produkt_navn_vis = valg
        valgt_geonet = find_geonet(valg)
        geonet_label = valg

    # ── Skalering: brug t_uarm hvis defineret, ellers største armerede ─
    kandidater = [t for t in (t_uarm, t_1, t_2) if t is not None]
    if not kandidater:
        st.caption("Ingen gyldige beregninger at visualisere.")
        return

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

    # ── Byg snit-listen (Koncept A) ────────────────────────────────────
    # I Brugerdefineret-tilstand (materialer != []): 4 søjler — Indtastet
    # opbygning + 3 krav-søjler. I Standard-tilstand: 3 krav-søjler.
    snit_liste: list[rapport_mod.Snit] = []

    har_indtastet = bool(materialer) and any(
        (m.get("tykkelse_mm") or 0) > 0 for m in materialer
    )

    # phi-korrigeret uarmeret-krav: t_uarm × (1 + K_PHI × (phi - 37))
    t_uarm_krav: float | None = None
    if t_uarm is not None:
        phi_kor = K_PHI * (phi - PHI_BASIS) if har_indtastet else 0.0
        t_uarm_krav = round(t_uarm * (1 + phi_kor))

    # Indtastet opbygning som total (sum af brugerens lag)
    indtastet_total, indtastet_sub = _sub_lag_uarmeret_fra_materialer(
        materialer, t_uarm
    )
    # I Standard-tilstand giver _sub_lag_uarmeret_fra_materialer
    # (None, []) tilbage hvis ingen materialer i mm-mode — så har_indtastet
    # styrer om vi tegner søjle 1.
    t_indtastet_for_linje = indtastet_total if har_indtastet else None

    if har_indtastet:
        snit_liste.append(rapport_mod.Snit(
            titel="Indtastet opbygning",
            t_baerelag_mm=indtastet_total,
            geonet_y_fracs=[],
            sub_lag=indtastet_sub,
            ikke_defineret_tekst=None,
            t_indtastet_mm=t_indtastet_for_linje,
        ))

    # Søjle 2: Uarmeret basistykkelse (φ-korrigeret)
    if t_uarm_krav is not None:
        status_tekst_uarm, status_farve_uarm = _status_for_krav(
            t_indtastet_for_linje, t_uarm_krav, t_krav_best=None,
        )
        sub_red_u = _sub_lag_skaleret_fra_materialer(materialer, t_uarm_krav)
        brug_sub_u = len(sub_red_u) >= 2
        snit_liste.append(rapport_mod.Snit(
            titel="Ustabiliseret basistykkelse (φ-korrigeret)" if har_indtastet
                  else "Ustabiliseret basistykkelse",
            t_baerelag_mm=t_uarm_krav,
            geonet_y_fracs=[],
            sub_lag=sub_red_u if brug_sub_u else None,
            ikke_defineret_tekst=None,
            er_krav_soejle=not brug_sub_u,
            t_indtastet_mm=t_indtastet_for_linje,
            status_tekst=status_tekst_uarm,
            status_farve=status_farve_uarm,
            phi_vaegtet=har_indtastet,
        ))
    else:
        snit_liste.append(rapport_mod.Snit(
            titel="Ustabiliseret basistykkelse",
            t_baerelag_mm=None,
            geonet_y_fracs=[],
            sub_lag=None,
            ikke_defineret_tekst=(
                f"Ustabiliseret bærelag ikke defineret for Eu = {eu:g} MPa"
            ),
            er_krav_soejle=True,
            t_indtastet_mm=t_indtastet_for_linje,
            phi_vaegtet=har_indtastet,
        ))

    # Søjle 3+4: byg reducerede sub_lag når brugeren har angivet ≥2 materialer.
    # Reduktionen fordeles proportionalt — matematisk identisk med den vægtede
    # φ-tilgang (lineær formel, se core/data.py:K_PHI). Når der er færre end 2
    # lag falder vi tilbage til den neutrale "φ-vægtet bærelag"-blok.
    sub_red_1 = _sub_lag_skaleret_fra_materialer(materialer, t_1)
    sub_red_2 = _sub_lag_skaleret_fra_materialer(materialer, t_2)
    brug_sub_1 = len(sub_red_1) >= 2
    brug_sub_2 = len(sub_red_2) >= 2

    # Søjle 3: 1 lag geonet
    fracs_1, placement_1 = _geonet_fracs_kravsoejle(
        "1_lag", t_1, valgt_geonet,
        sub_lag=sub_red_1 if brug_sub_1 else None,
    )
    status_tekst_1, status_farve_1 = _status_for_krav(
        t_indtastet_for_linje, t_1, t_krav_best=t_1_best,
    )
    snit_liste.append(rapport_mod.Snit(
        titel="1 lag geonet",
        t_baerelag_mm=t_1,
        geonet_y_fracs=fracs_1,
        sub_lag=sub_red_1 if brug_sub_1 else None,
        ikke_defineret_tekst=(
            None if t_1 is not None else "Ikke gyldigt for denne kombination"
        ),
        best_case_mm=t_1_best,
        placement=placement_1,
        er_krav_soejle=not brug_sub_1,
        t_indtastet_mm=t_indtastet_for_linje,
        status_tekst=status_tekst_1,
        status_farve=status_farve_1,
        phi_vaegtet=har_indtastet,
    ))

    # Søjle 4: 2 lag geonet
    fracs_2, placement_2 = _geonet_fracs_kravsoejle(
        "2_lag", t_2, valgt_geonet,
        sub_lag=sub_red_2 if brug_sub_2 else None,
    )
    status_tekst_2, status_farve_2 = _status_for_krav(
        t_indtastet_for_linje, t_2, t_krav_best=t_2_best,
    )
    snit_liste.append(rapport_mod.Snit(
        titel="2 lag geonet",
        t_baerelag_mm=t_2,
        geonet_y_fracs=fracs_2,
        sub_lag=sub_red_2 if brug_sub_2 else None,
        ikke_defineret_tekst=(
            None if t_2 is not None else "Ikke gyldigt for denne kombination"
        ),
        best_case_mm=t_2_best,
        placement=placement_2,
        er_krav_soejle=not brug_sub_2,
        t_indtastet_mm=t_indtastet_for_linje,
        status_tekst=status_tekst_2,
        status_farve=status_farve_2,
        phi_vaegtet=har_indtastet,
    ))

    png = rapport_mod.render_opbygning_png(
        eu=eu, snit_liste=snit_liste, geonet_label=geonet_label,
    )
    _vis_opbygning_med_info(png)


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
    phi: float = PHI_BASIS,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
    materialer: list[dict] | None = None,
    t_basis_table: dict | None = None,
) -> None:
    """De 3 informations-expandere under resultaterne.

    Bruges af både Standard (phi=37, geonet=None, materialer=None)
    og Brugerdefineret (egne phi/geonet/materialer-værdier).

    bedste_1 / bedste_2: bedste (mindste t_armeret) gruppe i hver lag-mode,
    eller None hvis ingen er gyldige. I "Vælg specifikt produkt"-mode er
    bedste-gruppen den enkelte produkts resultat pakket via
    _resultat_til_gruppe().
    """
    materialer = materialer or []

    # --- Opbygningsvisualisering (referencenet eller valgt produkt) -----
    if ref_1 is not None or ref_2 is not None:
        st.markdown("#### 🧱 Opbygning")
        _render_opbygningsvisualisering(
            eu, ref_1, ref_2,
            prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            materialer=materialer,
            phi=phi,
            tvunget_produkt=geonet_navn,
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
    valgt_opbygning = st.session_state.get("opbygning_geonet_valg", _REF_VALG)

    def _placeringsadvarsler_for_valgt_opbygning(lag_mode: str) -> list[tuple[str, str]]:
        # Koncept A: placement evalueres i krav-tykkelsen uden brugerens
        # lagfordeling (sub_lag=None → min_daklag-regel). Det fjerner falske
        # advarsler der opstod fra proportional skalering.
        if valgt_opbygning == _REF_VALG:
            ref = ref_1 if lag_mode == "1_lag" else ref_2
            if ref is None or ref.get("t_armeret_mm") is None:
                return []
            t_ref = ref["t_armeret_mm"]
            placement = check_geonet_placement(
                lag_mode=lag_mode,
                total_mm=t_ref,
                geonet=None,
                sub_lag=None,
            )
            return [
                (f"{_REF_VALG}: {a}", lag_mode)
                for a in placement.get("placeringsadvarsler", [])
            ]

        produkter = prod_1lag if lag_mode == "1_lag" else prod_2lag
        if not produkter:
            return []
        for produkt in produkter:
            if produkt.get("navn") != valgt_opbygning or produkt.get("fejl"):
                continue
            t = produkt.get("t_armeret_mm")
            if t is None:
                return []
            valgt_geonet = find_geonet(valgt_opbygning)
            placement = check_geonet_placement(
                lag_mode=lag_mode,
                total_mm=t,
                geonet=valgt_geonet,
                sub_lag=None,
            )
            return [
                (f"{valgt_opbygning}: {a}", lag_mode)
                for a in placement.get("placeringsadvarsler", [])
            ]
        return []

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
        for a, a_lm in _placeringsadvarsler_for_valgt_opbygning(lm):
            advarsler_pr_lag.append((a, a_lm))
            lag_by_advarsel.setdefault(a, set()).add(a_lm)

    for a, lm in advarsler_pr_lag:
        if len(lag_by_advarsel[a]) == 1:
            a = _advarsel_med_lagtekst(a, lm)
        if a not in seen_a:
            seen_a.add(a)
            advarsler_unik.append(a)

    # --- Samlet opbygning vs. minimumtykkelse (1 lag / 2 lag) -----------
    # Én samlet advarsel der sammenligner brugerens samlede materialetykkelse
    # mod den mindst mulige krævede tykkelse i hver lag-mode (erstatter den
    # tidligere per-lag-advarsel, så 1-lag- og 2-lag-tilfældet samles).
    total_opbygning = sum(
        m["tykkelse_mm"] for m in materialer
        if m.get("tykkelse_mm") is not None
    )
    t_min_1 = bedste_1["t_armeret_mm"] if bedste_1 is not None else None
    t_min_2 = bedste_2["t_armeret_mm"] if bedste_2 is not None else None
    under_1 = t_min_1 is not None and total_opbygning < t_min_1
    under_2 = t_min_2 is not None and total_opbygning < t_min_2
    if materialer and total_opbygning > 0 and (under_1 or under_2):
        if t_min_2 is not None and under_1 and not under_2:
            # 1 lag utilstrækkeligt, men 2 lag er nok → foreslå 2 lag
            opbyg_adv = (
                f"Den samlede foreslåede opbygning ({total_opbygning:.0f} mm) er "
                f"mindre end minimumtykkelsen ved 1 lag geonet ({t_min_1:.0f} mm), "
                f"men tilstrækkelig ved 2 lag geonet ({t_min_2:.0f} mm). "
                f"Anvend 2 lag geonet for denne opbygning."
            )
        elif t_min_1 is not None and t_min_2 is not None:
            # Utilstrækkelig ved både 1 og 2 lag
            opbyg_adv = (
                f"Den samlede foreslåede opbygning ({total_opbygning:.0f} mm) er "
                f"mindre end den beregnede minimumtykkelse ved både 1 lag "
                f"({t_min_1:.0f} mm) og 2 lag geonet ({t_min_2:.0f} mm). "
                f"Øg den samlede materialetykkelse, eller anvend materialer med "
                f"højere friktionsvinkel."
            )
        else:
            # Kun ét lag-mode er gyldigt for kombinationen
            t_kendt = t_min_1 if t_min_1 is not None else t_min_2
            lag_txt = "1 lag" if t_min_1 is not None else "2 lag"
            opbyg_adv = (
                f"Den samlede foreslåede opbygning ({total_opbygning:.0f} mm) er "
                f"mindre end minimumtykkelsen ved {lag_txt} geonet "
                f"({t_kendt:.0f} mm). Øg den samlede materialetykkelse, eller "
                f"anvend materialer med højere friktionsvinkel."
            )
        if opbyg_adv not in seen_a:
            seen_a.add(opbyg_adv)
            advarsler_unik.insert(0, opbyg_adv)

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
            krav = placement_requirements(geonet)
            min_dk_mm = krav["min_top_cover_mm"]
            afstand_str = (
                f"{krav['min_spacing_mm']:.0f}–"
                f"{krav['max_spacing_mm']:.0f} mm"
            )
            if geonet["max_korn"] is not None:
                korn_str = f"**{geonet['max_korn']} mm**"
            else:
                korn_str = "**ikke specificeret** — kontakt leverandør"
            st.markdown(
                f"**Krav for {navn_vis}:**\n"
                f"- Minimum dæklag over geonet: **{min_dk_mm} mm**\n"
                f"- Afstand mellem geonetlag: **{afstand_str}**\n"
                f"- Max kornstørrelse i kontakt med geonet: {korn_str}"
            )
        else:
            # Oversigt: produkt-specifikke krav for bedste 1-lag og 2-lag.
            # Hvis samme sæt produkter er bedste i begge lag-modes,
            # vises kravene kun én gang.
            def _vis_krav_blok(overskrift: str, gruppe: dict) -> None:
                navne, dk_str, korn_str, afstand_str = _krav_for_gruppe(gruppe)
                st.markdown(
                    f"**{overskrift}** ({navne})\n"
                    f"- Minimum dæklag over geonet: **{dk_str}**\n"
                    f"- Afstand mellem geonetlag: **{afstand_str}**\n"
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
Den beregnede bærelagstykkelse korrigeres for friktionsvinkler forskellig fra φ = 37° samt effektindeks af forskellige geonet.

1. **Bundmodulet Eu** vælges eller beregnes via sammenhæng med Cv
2. **Krav til overflademodulet Eo** vælges alt efter belastningsklasse
3. **Opslag i designdiagrammerne** foretages på baggrund af valg af bund- og overflademodul, hvor bærelagstykkelsen bestemmes - ustabiliseret og stabiliseret med 1–2 lag geonet.
   Der er lavet forudgående interpolation imellem designdiagrammerns tabelværdier, for at danne en komplet tabel for hvert designdiagram. 
4. **På baggrund af opslaget bestemmes basistykkelsen T_basis:**
   - Ustabiliseret: *xx mm*
   - 1 lag armering (referencenet): *xx mm*
   - 2 lag armering (referencenet): *xx mm*
5. **Korrektionsfaktorer for friktionsvinkel og effektivitet af geonet**

   **Friktionsvinkel:**
   Friktionsvinkel-korrektionen justerer basistykkelsen fra opslagstabellen, som er baseret på et standardmateriale med φ ≈ 37°. For hver grad over 37° reduceres tykkelsen med 2 %, og for φ under 37° øges tykkelsen tilsvarende.

   I standardberegningen sættes bærelagets friktionsvinkel φ = 37°.

   I den brugerdefinerede beregning beregnes en vægtet friktionsvinkel ud fra den angivne procentvægtning eller lagtykkelser af lagene, som er prædefinerede materialer med forskellige friktionsvinkler.

   *Eksempel på beregning i brugerdefineret tilstand, ud fra lagtykkelser:*

   | Lag | Materiale | Tykkelse | φ (°) | Vægtet bidrag |
   |-----|-----------|----------|------:|-------------:|
   | 1   | SG I 0-32 | 300 mm   | 40,0  | 12 000        |
   | 2   | Bundsand  | 450 mm   | 37,0  | 16 650        |

   Vægtet φ = Σ(tᵢ × φᵢ) / Σ(tᵢ) = 28 650 / 750 = **38,20°**

   φ-korrektion = −0,02 × (φ − 37°) = −0,02 × (38,20 − 37) = **−0,0240**
   *(dvs. tykkelsen reduceres med 2,40 % af T_basis)*

   **Net-korrektion:**
   Designdiagrammerne bruger GS-GRID SX160, E'GRID T6 eller Tensar TriAx TX160 som referencenet (effektindeks 100). Hvis der er valgt en anden armering, skaleres tykkelsen op eller ned med op til 20 % alt efter produkt.
   En positiv korrektionsfaktor = tykkere bærelag (mindre effektiv armering), negativ = tyndere bærelag (mere effektiv armering).

6. **Den endelige bærelagstykkelse beregnes som:**

   **T_stabiliseret = T_basis × (1 + φ-kor + net-kor)**

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
                f'Reduceres ↓ {red_mm:.0f} mm fra ustabiliseret ({pct_str})'
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
        reduktion_txt = f" (Reduceres ↓ {red_mm} mm fra ustabiliseret, {red_pct:.0%})"
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
    phi_kor = K_PHI * (phi - PHI_BASIS)

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

    # Reduktion sammenlignes mod φ-korrigeret uarmeret reference, så net-effekten
    # alene afspejles i procentdelen (se calculator.beregn() for begrundelse).
    t_uarm_final = (
        ref_uarm.get("t_uarmeret_phi_kor_mm") or ref_uarm.get("t_uarmeret_mm")
        if not ref_uarm.get("fejl") else None
    )

    with st.container(border=True):
        st.markdown("**📊 Beregnings-breakdown**")

        # ── Uarmeret ──────────────────────────────────────────────────
        st.markdown("**Ustabiliseret bærelagstykkelse**")
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
                    ("T_basis_stabiliseret (opslag)", f"{t_b_1:.0f} mm", ""),
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
                    ("T_basis_stabiliseret (opslag)", f"{t_b_2:.0f} mm", ""),
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

    Lodret stablet layout: Underbund → Belastningsklasse →
    Resultater (uarmeret + 1/2-lag-kolonner) → informations-expandere.
    """

    # --- Underbund + Belastningsklasse ----------------------------
    eu = input_underbund(key_prefix="std")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="std")
    st.caption(
        "ℹ️ I resultatoversigten vises hvilke belastningsklasser produkterne anbefales til. Der vises en advarsel, hvis et produkt ikke anbefales anvendt til den valgte klasse."
    )

    # --- Beregn alt -----------------------------------------------------
    t_basis_table = _aktiv_t_basis_table()
    ref_1, ref_2, ref_fejl_1, ref_fejl_2 = _beregn_referencegrupper(
        eu, eo, PHI_BASIS, valgt_klasse, t_basis_table
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
                f'<div class="uarm-banner-label">Ustabiliseret bærelagstykkelse</div>'
                f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            _render_uarmeret_mangler_besked(eu, eo)

        _render_produkt_tabel(
            ref_1, ref_2, ref_fejl_1, ref_fejl_2,
            prod_1lag, prod_2lag, valgt_klasse,
        )

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
        phi_weighted   — total_bidrag / total_v (eller 37 ved tom input)
        lag_mode_pct   — True hvis andele i %, ellers tykkelser i mm
        symbol         — 'p' eller 't' (til formelvisning)
        enhed          — '%' eller 'mm'
    """
    if not materialer:
        return {
            "tabel_md": "", "total_v": 0.0, "total_bidrag": 0.0,
            "phi_weighted": PHI_BASIS, "lag_mode_pct": False,
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
    phi_weighted = total_bidrag / total_v if total_v > 0 else PHI_BASIS

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

    phi_kor = -0.02 * (phi_final - PHI_BASIS)
    phi_kor_str = _dk_num(phi_kor, "+.4f")
    phi_kor_pct_str = _dk_num(phi_kor * 100, "+.2f")

    boks_kol, _ = st.columns([1, 1])
    with boks_kol, st.container(border=True):
        st.markdown("**📐 φ-beregning fra materialelagene**")
        st.markdown(data["tabel_md"])
        st.markdown(
            f"**Vægtet φ** = Σ({data['symbol']}ᵢ × φᵢ) / Σ({data['symbol']}ᵢ) = "
            f"{bidrag_str} / {v_str} = **{phi_w_str}°**"
        )

        if overskrevet:
            st.markdown(
                f"⚠️ φ overskrevet manuelt → bruger **{phi_f_str}°** "
                f"i resten af beregningen (vægtet værdi {phi_w_str}° ignoreres)."
            )

        st.markdown(
            f"**φ-korrektion** = −0,02 × (φ − 37°) = "
            f"−0,02 × ({phi_f_str} − 37) = **{phi_kor_str}** "
            f"({phi_kor_pct_str} % af basistykkelsen)"
        )

        ref_1 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="1_lag",
                       t_basis_table=t_basis_table)
        ref_2 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="2_lag",
                       t_basis_table=t_basis_table)




def _lag_label(idx: int, antal_lag: int) -> str:
    """UI-navn på lag-expanderen i Materialelag.

    2 lag → Øverste/Nederste. 3 lag → Øverste/Midterste/Nederste.
    1 lag har ingen indbyrdes position, så vi falder tilbage på 'Lag 1'.
    """
    if antal_lag == 2:
        return "Øverste lag" if idx == 0 else "Nederste lag"
    if antal_lag == 3:
        return ("Øverste lag", "Midterste lag", "Nederste lag")[idx]
    return f"Lag {idx + 1}"


def _input_materialelag(eu: float, eo: float) -> tuple[list[dict], float]:
    """
    Materialelag — render input-sektionen og returnér
    (materialer-liste, beregnet/overskrevet φ).
    """
    st.subheader("Materialelag")

    antal_lag_kol, _ = st.columns([1, 7])
    with antal_lag_kol:
        antal_lag = st.number_input(
            "Antal lag", min_value=1, max_value=3, value=2, step=1,
            key="bd_antal_lag",
        )
    st.caption(f"Mindste lagtykkelse der kan indtastes er {MIN_LAGTYKKELSE_MM} mm.")

    # Default-opbygning ved første besøg på siden: Stabilgrus SGII 0-32
    # (øverst, 300 mm) + Bundsikringssand (nederst, 400 mm). Sat via
    # setdefault så brugerens egne ændringer bevares ved rerun.
    _DEFAULT_LAG = [
        ("Stabilgrus SGII 0-32", 300),
        ("Bundsikringssand", 400),
    ]
    for _idx, (_navn, _t) in enumerate(_DEFAULT_LAG):
        st.session_state.setdefault(f"bd_mat_{_idx}", _navn)
        st.session_state.setdefault(f"bd_t_{_idx}", _t)

    materialer: list[dict] = []
    phi_vaerdier: list[float] = []

    for i in range(int(antal_lag)):
        lag_kol, _ = st.columns([1, 1])
        with lag_kol, st.expander(_lag_label(i, int(antal_lag)), expanded=True):
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
                    "φ (°)", 20.0, 60.0, PHI_BASIS, 0.5, key=f"bd_phi_m_{i}"
                )
                korn_i = st.number_input(
                    "Max kornstørrelse (mm)", 0, 500, 32, key=f"bd_korn_m_{i}"
                )
                ltype_i = st.selectbox(
                    "Lagtype", ["Bærelag", "Bundsikring"], key=f"bd_lt_m_{i}"
                )
                krav_maske_i = None
            else:
                phi_i = float(md["phi"])
                korn_i = md["max_korn"]
                ltype_i = md["lagtype"]
                krav_maske_i = md.get("krav_maskestoerrelse_mm")
                krav_txt = (
                    f" · krav til geonet maskestørrelse = {krav_maske_i} mm"
                    if krav_maske_i is not None
                    else ""
                )
                st.caption(
                    f"φ = {phi_i}° · max korn = {korn_i} mm · {ltype_i}{krav_txt}"
                )

            phi_vaerdier.append(phi_i)

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
                step=50,
                key=t_key,
            )
            materialer.append({
                "navn": lag_navn, "phi": phi_i, "max_korn": korn_i,
                "lagtype": ltype_i, "tykkelse_mm": float(t_i),
                "pct": None,
                "krav_maskestoerrelse_mm": krav_maske_i,
            })

    total_t = sum(m["tykkelse_mm"] for m in materialer)
    st.markdown(f"**Samlet tykkelse af opbygning:** {total_t:.0f} mm")

    phi_weighted = (
        sum(m["phi"] * m["tykkelse_mm"] for m in materialer) / total_t
        if total_t > 0
        else (sum(phi_vaerdier) / len(phi_vaerdier) if phi_vaerdier else PHI_BASIS)
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


def _render_uarm_banner_bd(t_uarm: float, phi: float = PHI_BASIS) -> None:
    """Render ustabiliseret-banner i brugerdefineret tilstand (én basis-boks).

    phi bevares i signaturen for kald-kompatibilitet, men bruges ikke længere —
    den φ-korrigerede boks er fjernet, og reduktionen (incl. φ-bidraget) vises
    nu i de enkelte resultatkort.
    """
    st.markdown(
        f'<div class="uarm-banner">'
        f'<div class="uarm-banner-label">Ustabiliseret bærelagstykkelse</div>'
        f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_brugerdefineret() -> None:
    """Brugerdefineret-tilstand: input + resultater + expandere.

    Lodret stablet layout som i Standard-tilstand. Sektion Geonet lader brugeren
    vælge mellem 'Vis alle produkter' (oversigt med custom φ) og 'Vælg
    specifikt produkt' (detaljeret resultat for ét produkt). Begge modes
    viser 1-lag og 2-lag side om side — ingen separat lag-mode-radio.
    """

    # --- Underbund + Belastningsklasse + Materialelag --------------------------------------------------------
    t_basis_table = _aktiv_t_basis_table()
    eu = input_underbund(key_prefix="bd")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="bd")
    materialer, phi = _input_materialelag(eu, eo)

    # --- Geonet --------------------------------------------------------
    st.subheader("Geonet")

    visning = st.radio(
        "Visning",
        ["Vis alle produkter (oversigt)", "Vælg specifikt produkt"],
        horizontal=True,
        key="bd_visning",
        help=(
            "**Vis alle produkter:** samme oversigt som Standard-beregningen, men med "
            "din vægtede friktionsvinkel φ fra materialelagene.  \n"
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
            format_func=_produkt_label,
        )
        geonet = find_geonet(geonet_navn)

        if geonet:
            korn_txt = f"{geonet['max_korn']} mm" if geonet["max_korn"] else "—"
            kl_txt = _format_klasse_liste(geonet["klasser"])
            kor_txt = f"{geonet['korrektion']:+.0%}"
            rude_txt = geonet.get("rudeaabning") or "—"
            db_maske = geonet.get("maskestoerrelse_datablad_mm")
            if db_maske:
                rude_txt += f" (datablad: {db_maske} mm)"
            st.caption(
                f"Serie: **{geonet['serie']}** · Korrektion: {kor_txt} · "
                f"Max korn: {korn_txt} · Rudeåbning/maskestørrelse: {rude_txt} · "
                f"Belastningsklasser: {kl_txt} · "
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
    prod_1lag = _berig_produkter_med_placering(prod_1lag, "1_lag", materialer)
    prod_2lag = _berig_produkter_med_placering(prod_2lag, "2_lag", materialer)

    if not specifikt_mode:
        # OVERSIGT-MODE — som Standard, men med custom phi
        # Rapport kræver et specifikt valgt produkt — ryd evt. tidligere stash.
        st.session_state.pop("sidste_dim", None)

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
                brugerdefineret=True,
            )
            st.markdown("")
            kol_1, kol_2 = st.columns(2, gap="large")
            with kol_1:
                _render_lag_kolonne("1 LAG GEONET", grupper_1, valgt_klasse, "1_lag",
                                    phi=phi, brugerdefineret=True)
            with kol_2:
                _render_lag_kolonne("2 LAG GEONET", grupper_2, valgt_klasse, "2_lag",
                                    phi=phi, brugerdefineret=True)

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
        res_1 = _berig_resultat_med_placering(res_1, geonet, materialer)
        res_2 = _berig_resultat_med_placering(res_2, geonet, materialer)

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
                res_best = _berig_resultat_med_placering(
                    res_best, geonet, materialer
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
                produkt["placering_best"] = {
                    k: res_best.get(k)
                    for k in (
                        "placering_ok", "geonet_placeringer_mm_fra_top",
                        "geonet_y_fracs", "topdaeklag_mm",
                        "afstande_mellem_geonet_mm", "placeringsadvarsler",
                        "t_min_placering_mm", "t_dimensionerende_mm",
                        "min_top_cover_mm", "min_spacing_mm", "max_spacing_mm",
                        "placeringsbasis",
                    )
                    if k in res_best
                }

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
            st.session_state.pop("sidste_dim", None)
        else:
            # Stash til Rapport-siden
            st.session_state["sidste_dim"] = {
                "eu": eu, "eo": eo, "valgt_klasse": valgt_klasse,
                "phi": phi, "materialer": materialer,
                "geonet": geonet, "geonet_navn": geonet_navn,
                "res_1": res_1, "res_2": res_2,
                "t_uarmeret_mm": t_uarm,
                "t_1_lag_best_mm": (
                    bedste_1["produkter"][0].get("t_armeret_mm_min")
                    if bedste_1 and bedste_1.get("produkter") else None
                ),
                "t_2_lag_best_mm": (
                    bedste_2["produkter"][0].get("t_armeret_mm_min")
                    if bedste_2 and bedste_2.get("produkter") else None
                ),
            }
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
                    tom_besked=tom_1, phi=phi, brugerdefineret=True,
                )
            with kol_2:
                _render_lag_kolonne(
                    "2 LAG GEONET", grupper_2, valgt_klasse, "2_lag",
                    tom_besked=tom_2, phi=phi, brugerdefineret=True,
                )

            if geonet and geonet.get("navn"):
                from core import rapport as rapport_mod
                t_indtastet_total = sum(
                    float(m.get("tykkelse_mm") or 0) for m in materialer
                ) or None
                produkt_1 = (
                    bedste_1["produkter"][0]
                    if bedste_1 and bedste_1.get("produkter") else None
                )
                produkt_2 = (
                    bedste_2["produkter"][0]
                    if bedste_2 and bedste_2.get("produkter") else None
                )

                st.markdown("")
                kol_chk, _kol_gap, kol_dd, _kol_spacer = st.columns(
                    [2, 0.5, 4, 1], gap="small", vertical_alignment="center",
                )
                with kol_chk:
                    vis_din_prik = st.checkbox(
                        "Vis 'Indtastet opbygning'",
                        value=True,
                        key="bd_dd_vis_din_prik",
                        disabled=t_indtastet_total is None,
                    )
                    vis_lag_prikker = st.checkbox(
                        "Vis endepunkter for 1/2 lag geonet",
                        value=True,
                        key="bd_dd_vis_lag_prikker",
                    )

                with kol_dd:
                    try:
                        designdiagram_png = rapport_mod.render_personligt_designdiagram_png(
                            eu=float(eu),
                            eo=float(eo),
                            klasse=valgt_klasse,
                            phi=float(phi),
                            geonet=geonet,
                            t_indtastet_mm=t_indtastet_total if vis_din_prik else None,
                            t_basis_table=t_basis_table,
                            t_1_lag_mm=(
                                produkt_1.get("t_armeret_mm")
                                if produkt_1 and vis_lag_prikker else None
                            ),
                            t_2_lag_mm=(
                                produkt_2.get("t_armeret_mm")
                                if produkt_2 and vis_lag_prikker else None
                            ),
                            t_1_lag_best_mm=(
                                produkt_1.get("t_armeret_mm_min")
                                if produkt_1 and vis_lag_prikker else None
                            ),
                            t_2_lag_best_mm=(
                                produkt_2.get("t_armeret_mm_min")
                                if produkt_2 and vis_lag_prikker else None
                            ),
                        )
                        _vis_designdiagram_med_info(
                            designdiagram_png,
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.warning(f"Kunne ikke generere designdiagram: {e}")

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
    ("📄", "Rapport",            "rapport"),
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
            "BK":                    _format_klasse_liste(g["klasser"]),
            "Min. dæklag\n(cm)":     g["min_daklag"],
            "Maks. korn\n(datablad mm)": f"{g['max_korn']}" if g["max_korn"] else "—",
            "Anb. tilslag\n(designmanual)": g.get("anbefalet_tilslag") or "—",
            "Maskestørrelse\n(datablad mm)":        f"{g['maskestoerrelse_datablad_mm']} mm" if g.get("maskestoerrelse_datablad_mm") else "—",
            "Rudeåbning/maskestørrelse\n(designmanual)": g.get("rudeaabning") or "—",
            "Radial stivhed\n(kN/m @ 0,5%)": f"{g['radial_stivhed']}" if g.get("radial_stivhed") else "—",
            "GWP A1–A3\n(kg CO₂/m²)": (
                " / ".join(f"{v:.2f} ({b:g}m)" for b, v in g["gwp_bredder"].items())
                if g.get("gwp_bredder")
                else (f"{g['gwp']:.2f}" if g.get("gwp") else "—")
            ),
            "Min. levetid":          g.get("min_levetid") or "—",
            "Min. trækstyrke\n(kN/m)":      g.get("min_traekstyrke") or "—",
            "Trækstyrke 2%\n(kN/m)":       g.get("traekstyrke_2pct") or "—",
            "Trækstyrke 5%\n(kN/m)":       g.get("traekstyrke_5pct") or "—",
            "Maks. def.\n(%)":              f"≤{g['max_deformation_pct']}" if g.get("max_deformation_pct") else "—",
            "Knudepunkt\neffektivitet":     g.get("knudepunkt_effektivitet") or "—",
            "Maskestabilitet\n(N.mm/grad)": f"{g['maskestabilitet_Nmm_grad']}" if g.get("maskestabilitet_Nmm_grad") else "—",
            "Ribbetykkelse\n(mm)":          g.get("ribbetykkelse") or "—",
            "Stivhedsforhold":              f"{g['stivhedsforhold']}" if g.get("stivhedsforhold") is not None else "—",
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
                "Ustabiliseret tykkelse (cm)": row["t_uarmeret_cm"],
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
                    "Ustabiliseret tykkelse (cm)": st.column_config.NumberColumn(
                        "Ustabiliseret tykkelse (cm)",
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
                "phi": int(PHI_BASIS),
                "max_korn": 32,
                "krav_maskestoerrelse_mm": None,
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
        columns=[
            "navn", "lagtype", "phi", "max_korn",
            "krav_maskestoerrelse_mm", "anvendelse",
        ],
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
            "krav_maskestoerrelse_mm": st.column_config.NumberColumn(
                "Krav til geonet — maskestørrelse (mm)",
                help=(
                    "Minimum kvadratisk maskestørrelse i mm som materialet "
                    "kræver af et biaksialt geonet. Sammenlignes kun med "
                    "biaksiale net i Brugerdefineret-tilstand."
                ),
                min_value=0,
                max_value=500,
                step=5,
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


def render_rapport() -> None:
    """Rapport-side — generér Word/PDF ud fra den seneste dimensionering."""
    from datetime import date as _date

    from core import rapport as rapport_mod

    st.title("📄 Rapport")
    st.caption(
        "Generér en notat-rapport (Word og PDF) baseret på den seneste "
        "dimensionering. Standardtekster kan redigeres pr. rapport."
    )
    st.divider()

    sd = st.session_state.get("sidste_dim")
    if not sd or not sd.get("geonet"):
        st.info(
            "Du skal først foretage en dimensionering med et specifikt valgt "
            "geonet, før rapporten kan genereres.\n\n"
            "Gå til **Dimensionering → Brugerdefineret**, vælg "
            "**Vælg specifikt produkt**, og udfyld inputtene."
        )
        if st.button("Gå til Dimensionering", type="primary"):
            st.session_state.aktiv_side = "dimensionering"
            st.rerun()
        return

    # Opsummering af det aktuelle beregningsgrundlag
    st.success(
        f"**Rapport baseret på:**  Eu = {sd['eu']:g} MPa  ·  "
        f"Klasse {sd['valgt_klasse']} (Eo = {sd['eo']:g} MPa)  ·  "
        f"Produkt: **{sd['geonet_navn']}**  ·  φ = {sd['phi']:.1f}°"
    )

    # --- A. Metadata --------------------------------------------------------
    st.subheader("A. Projekt-oplysninger")
    md_state = st.session_state.setdefault("rapport_metadata", {
        "projekt": "", "beskrivelse": "", "omfang": "",
        "udfoeres_for": "", "sagsbehandler": "", "sagsbehandler_mail": "",
        "dato": _date.today().isoformat(),
    })
    # Migrér gamle session-states der ikke har sagsbehandler_mail
    md_state.setdefault("sagsbehandler_mail", "")

    col_a, col_b = st.columns(2)
    with col_a:
        md_state["projekt"] = st.text_input(
            "Projekt", value=md_state.get("projekt", ""), key="rap_projekt",
        )
        md_state["omfang"] = st.text_input(
            "Omfang", value=md_state.get("omfang", ""), key="rap_omfang",
        )
        md_state["sagsbehandler"] = st.text_input(
            "Sagsbehandler", value=md_state.get("sagsbehandler", ""),
            key="rap_sagsbehandler",
        )
        md_state["sagsbehandler_mail"] = st.text_input(
            "Sagsbehandler-mail",
            value=md_state.get("sagsbehandler_mail", ""),
            key="rap_sagsbehandler_mail",
        )
    with col_b:
        md_state["beskrivelse"] = st.text_area(
            "Beskrivelse", value=md_state.get("beskrivelse", ""),
            key="rap_beskrivelse", height=80,
        )
        md_state["udfoeres_for"] = st.text_input(
            "Udføres for", value=md_state.get("udfoeres_for", ""),
            key="rap_udfoeres_for",
        )
        valgt_dato = st.date_input(
            "Dato",
            value=_date.fromisoformat(md_state.get("dato")) if md_state.get("dato") else _date.today(),
            key="rap_dato",
            format="DD/MM/YYYY",
        )
        md_state["dato"] = valgt_dato.isoformat() if hasattr(valgt_dato, "isoformat") else str(valgt_dato)

    st.divider()

    # --- B. Redigerbare skabelon-sektioner ---------------------------------
    st.subheader("B. Skabelon-tekster")
    st.caption(
        "Standardteksterne fra BG Byggros eksempelrapport er forudfyldt. "
        "Du kan redigere dem pr. rapport — eller nulstille til standard."
    )
    tekster_state = st.session_state.setdefault("rapport_tekster", {})
    # Versionsnummer pr. sektion — bumpes når Nulstil klikkes, så text_area
    # får en ny widget-key og dermed glemmer det brugeren skrev.
    reset_v = st.session_state.setdefault("rapport_reset_v", {})

    for nøgle in rapport_mod.SECTION_KEYS:
        titel = rapport_mod.SECTION_TITLER[nøgle]
        std = rapport_mod.STANDARD_TEKSTER[nøgle]
        nuvaerende = tekster_state.get(nøgle, std)
        v = reset_v.get(nøgle, 0)
        widget_key = f"rap_tekst_{nøgle}_v{v}"
        with st.expander(titel, expanded=False):
            kol_l, kol_r = st.columns([5, 1])
            with kol_r:
                if st.button("🔄 Nulstil", key=f"rap_reset_{nøgle}",
                             width="stretch"):
                    tekster_state[nøgle] = std
                    # Bump versionen — det giver text_area en ny key, så
                    # Streamlit re-initialiserer widget'en med std-tekst.
                    reset_v[nøgle] = v + 1
                    st.rerun()
            ny_tekst = st.text_area(
                "Tekst", value=nuvaerende, height=220,
                key=widget_key, label_visibility="collapsed",
            )
            tekster_state[nøgle] = ny_tekst

    st.divider()

    # --- C. Visualiseringsvalg + preview -----------------------------------
    st.subheader("C. Visualisering")

    res_1 = sd.get("res_1") or {}
    res_2 = sd.get("res_2") or {}
    t_1 = res_1.get("t_armeret_mm") if not res_1.get("fejl") else None
    t_2 = res_2.get("t_armeret_mm") if not res_2.get("fejl") else None
    t_uarm = sd.get("t_uarmeret_mm")

    uarm_muligt = t_uarm is not None
    to_lag_muligt = t_1 is not None and t_1 >= 500.0

    # Materialelag fra brugerens dimensionering — bruges til at vise
    # 'Indtastet opbygning'-søjlen og sammenligningslinjen på krav-søjlerne.
    materialer_dim = sd.get("materialer") or []
    in_mm_mode = any(m.get("tykkelse_mm") for m in materialer_dim)
    indtastet_muligt = in_mm_mode and bool(materialer_dim)

    kol_v0, kol_v1, kol_v2, kol_v3 = st.columns(4)
    with kol_v0:
        vis_indtastet = st.checkbox(
            "Indtastet opbygning",
            value=indtastet_muligt,
            disabled=not indtastet_muligt,
            key="rap_vis_indtastet",
            help=(
                None if indtastet_muligt
                else "Ingen brugerindtastede lagtykkelser at vise."
            ),
        )
    with kol_v1:
        vis_uarm = st.checkbox(
            "Ustabiliseret opbygning",
            value=uarm_muligt,
            disabled=not uarm_muligt,
            key="rap_vis_uarm",
            help=(
                None if uarm_muligt
                else "Ustabiliseret tykkelse er ikke defineret for denne "
                     "Eu/Eo-kombination."
            ),
        )
    with kol_v2:
        vis_1lag = st.checkbox(
            "1 lag geonet",
            value=t_1 is not None,
            disabled=t_1 is None,
            key="rap_vis_1lag",
        )
    with kol_v3:
        vis_2lag = st.checkbox(
            "2 lag geonet",
            value=to_lag_muligt,
            disabled=not to_lag_muligt,
            key="rap_vis_2lag",
            help=(
                None if to_lag_muligt
                else "2 lag geonet anvendes kun ved opbygninger ≥ 500 mm "
                     "(beregnet 1-lag tykkelse) — derfor ikke relevant her."
            ),
        )

    geonet = sd.get("geonet") or {}
    geonet_label = geonet.get("navn", "Geonet")

    # --- Ekstra: Personligt designdiagram ---------------------------------
    designdiagram_muligt = bool(geonet.get("navn"))
    vis_designdiagram = st.checkbox(
        "Personligt designdiagram",
        value=designdiagram_muligt,
        disabled=not designdiagram_muligt,
        key="rap_vis_designdiagram",
        help=(
            "Tegner designkurverne (ustabiliseret, 1 lag, 2 lag) tilpasset dine "
            "materialer og valgte geonet, med din opbygning og Eu som "
            "referencer. Ligner de originale designdiagrammer."
            if designdiagram_muligt
            else "Vælg et specifikt geonet under Dimensionering for at få "
                 "kurverne med produktets net-korrektion."
        ),
    )
    kol_dd1, kol_dd2 = st.columns(2)
    with kol_dd1:
        vis_dd_din_prik = st.checkbox(
            "Vis 'Din opbygning'-prik i designdiagram",
            value=True,
            key="rap_dd_vis_din_prik",
            disabled=not (vis_designdiagram and designdiagram_muligt),
        )
    with kol_dd2:
        vis_dd_lag_prikker = st.checkbox(
            "Vis endepunkter for 1/2 lag i designdiagram",
            value=True,
            key="rap_dd_vis_lag_prikker",
            disabled=not (vis_designdiagram and designdiagram_muligt),
        )

    # --- Ekstra: VD-trafikkobling i grundlagstabellen --------------------
    vis_trafikkobling = st.checkbox(
        "VD-trafikkobling i grundlagstabellen",
        value=False,
        key="rap_vis_trafikkobling",
        help=(
            "Tilføjer en linje i Dimensioneringsgrundlag med vejledende "
            "T-klasse, NÆ10/år og tunge køretøjer/døgn for den valgte "
            "belastningsklasse. Bygger på anvendelsesbeskrivelsen — ikke en "
            "normfastlagt konvertering."
        ),
    )

    def _sub_lag_skaleret(total_mm: float | None) -> list[dict]:
        """Returnér brugerens materialer skaleret så summen = total_mm.
        For mm-mode: forhold = tykkelse_mm / sum. For pct-mode: forhold = pct / sum.
        """
        if not materialer_dim or not total_mm:
            return []
        if in_mm_mode:
            sum_t = sum((m.get("tykkelse_mm") or 0) for m in materialer_dim)
            if sum_t <= 0:
                return []
            return [
                {
                    "navn": m.get("navn", "Lag"),
                    "tykkelse_mm": (m.get("tykkelse_mm") or 0) * total_mm / sum_t,
                }
                for m in materialer_dim if (m.get("tykkelse_mm") or 0) > 0
            ]
        # pct-mode
        sum_p = sum((m.get("pct") or 0) for m in materialer_dim)
        if sum_p <= 0:
            return []
        return [
            {
                "navn": m.get("navn", "Lag"),
                "tykkelse_mm": (m.get("pct") or 0) / sum_p * total_mm,
            }
            for m in materialer_dim if (m.get("pct") or 0) > 0
        ]

    def _sub_lag_uarmeret() -> tuple[float | None, list[dict]]:
        """For uarmeret-snittet: brug brugerens dimensionerede tykkelser
        (mm-mode). I pct-mode falder vi tilbage på t_uarm-beregningen."""
        if in_mm_mode and materialer_dim:
            lag = [
                {
                    "navn": m.get("navn", "Lag"),
                    "tykkelse_mm": float(m.get("tykkelse_mm") or 0),
                }
                for m in materialer_dim if (m.get("tykkelse_mm") or 0) > 0
            ]
            total = sum(l["tykkelse_mm"] for l in lag)
            return (total if total > 0 else None, lag)
        # pct-mode fallback
        return (t_uarm, _sub_lag_skaleret(t_uarm) if t_uarm else [])

    # Koncept A: Indtastet opbygning + neutrale krav-søjler. φ fra
    # dimensioneringen (sd["phi"]) styrer φ-korrektionen på uarmeret-kravet.
    phi_dim = float(sd.get("phi", PHI_BASIS))
    phi_kor_dim = K_PHI * (phi_dim - PHI_BASIS)
    har_indtastet_rap = in_mm_mode and bool(materialer_dim)
    indtastet_total_rap: float | None = None
    if har_indtastet_rap:
        indtastet_total_rap = sum(
            float(m.get("tykkelse_mm") or 0) for m in materialer_dim
        ) or None
    t_uarm_krav_rap = (
        round(t_uarm * (1 + phi_kor_dim)) if t_uarm is not None else None
    )

    # Når 'Indtastet opbygning' er fravalgt, slukkes både søjlen OG
    # sammenligningslinjen — t_indtastet_for_snit styrer linjen via Snit-feltet.
    vis_indtastet_aktiv = (
        vis_indtastet and har_indtastet_rap and bool(indtastet_total_rap)
    )
    t_indtastet_for_snit = indtastet_total_rap if vis_indtastet_aktiv else None
    # Status-tekst (Mangler / Besparelse) giver kun mening sammen med linjen.
    status_indtastet_ref = (
        indtastet_total_rap if vis_indtastet_aktiv else None
    )

    snit_liste: list[rapport_mod.Snit] = []

    # Søjle 1: Indtastet opbygning (styres af checkbox)
    if vis_indtastet_aktiv:
        _, indtastet_sub = _sub_lag_uarmeret()
        snit_liste.append(rapport_mod.Snit(
            titel="Indtastet opbygning",
            t_baerelag_mm=indtastet_total_rap,
            geonet_y_fracs=[], sub_lag=indtastet_sub,
            t_indtastet_mm=t_indtastet_for_snit,
        ))

    if vis_uarm and uarm_muligt and t_uarm_krav_rap is not None:
        status_tekst_u, status_farve_u = _status_for_krav(
            status_indtastet_ref, t_uarm_krav_rap, None,
        )
        sub_red_u = _sub_lag_skaleret_fra_materialer(
            materialer_dim, t_uarm_krav_rap
        )
        brug_sub_u = len(sub_red_u) >= 2
        snit_liste.append(rapport_mod.Snit(
            titel="Ustabiliseret basistykkelse (φ-korrigeret)"
                  if har_indtastet_rap else "Ustabiliseret basistykkelse",
            t_baerelag_mm=t_uarm_krav_rap,
            geonet_y_fracs=[],
            sub_lag=sub_red_u if brug_sub_u else None,
            er_krav_soejle=not brug_sub_u,
            t_indtastet_mm=t_indtastet_for_snit,
            status_tekst=status_tekst_u,
            status_farve=status_farve_u,
            phi_vaegtet=har_indtastet_rap,
        ))
    if vis_1lag and t_1 is not None:
        sub_red_1 = _sub_lag_skaleret_fra_materialer(materialer_dim, t_1)
        brug_sub_1 = len(sub_red_1) >= 2
        fracs_1, placement_1 = _geonet_fracs_kravsoejle(
            "1_lag", t_1, geonet,
            sub_lag=sub_red_1 if brug_sub_1 else None,
        )
        status_tekst_1, status_farve_1 = _status_for_krav(
            status_indtastet_ref, t_1, None,
        )
        snit_liste.append(rapport_mod.Snit(
            titel="1 lag geonet", t_baerelag_mm=t_1,
            geonet_y_fracs=fracs_1,
            sub_lag=sub_red_1 if brug_sub_1 else None,
            placement=placement_1,
            er_krav_soejle=not brug_sub_1,
            t_indtastet_mm=t_indtastet_for_snit,
            status_tekst=status_tekst_1,
            status_farve=status_farve_1,
            phi_vaegtet=har_indtastet_rap,
        ))
    if vis_2lag and t_2 is not None and to_lag_muligt:
        sub_red_2 = _sub_lag_skaleret_fra_materialer(materialer_dim, t_2)
        brug_sub_2 = len(sub_red_2) >= 2
        fracs_2, placement_2 = _geonet_fracs_kravsoejle(
            "2_lag", t_2, geonet,
            sub_lag=sub_red_2 if brug_sub_2 else None,
        )
        status_tekst_2, status_farve_2 = _status_for_krav(
            status_indtastet_ref, t_2, None,
        )
        snit_liste.append(rapport_mod.Snit(
            titel="2 lag geonet", t_baerelag_mm=t_2,
            geonet_y_fracs=fracs_2,
            sub_lag=sub_red_2 if brug_sub_2 else None,
            placement=placement_2,
            er_krav_soejle=not brug_sub_2,
            t_indtastet_mm=t_indtastet_for_snit,
            status_tekst=status_tekst_2,
            status_farve=status_farve_2,
            phi_vaegtet=har_indtastet_rap,
        ))

    if not snit_liste:
        st.warning(
            "Vælg mindst ét snit (ustabiliseret / 1 lag / 2 lag) for at kunne "
            "generere rapporten."
        )
        visu_png: bytes | None = None
    else:
        visu_png = rapport_mod.render_opbygning_png(
            eu=sd["eu"], snit_liste=snit_liste, geonet_label=geonet_label,
        )
        _vis_opbygning_med_info(
            visu_png, caption="Preview af opbygnings-visualisering"
        )

    # --- Personligt designdiagram (preview + rapport-PNG) ----------------
    designdiagram_png: bytes | None = None
    if vis_designdiagram and designdiagram_muligt:
        try:
            designdiagram_png = rapport_mod.render_personligt_designdiagram_png(
                eu=float(sd["eu"]),
                eo=float(sd["eo"]),
                klasse=sd.get("valgt_klasse"),
                phi=float(sd.get("phi", PHI_BASIS)),
                geonet=geonet,
                t_indtastet_mm=(
                    indtastet_total_rap
                    if har_indtastet_rap and vis_dd_din_prik else None
                ),
                t_basis_table=_aktiv_t_basis_table(),
                t_1_lag_mm=t_1 if vis_dd_lag_prikker else None,
                t_2_lag_mm=t_2 if vis_dd_lag_prikker else None,
                t_1_lag_best_mm=(
                    sd.get("t_1_lag_best_mm") if vis_dd_lag_prikker else None
                ),
                t_2_lag_best_mm=(
                    sd.get("t_2_lag_best_mm") if vis_dd_lag_prikker else None
                ),
            )
            _vis_designdiagram_med_info(
                designdiagram_png,
                caption="Preview af personligt designdiagram",
            )
        except Exception as e:
            st.warning(f"Kunne ikke generere designdiagram: {e}")
            designdiagram_png = None

    st.divider()

    # --- D. Generér rapport -----------------------------------------------
    st.subheader("D. Generér rapport")

    rapport_data = {
        "metadata": dict(md_state),
        "dim": sd,
        "tekster": dict(tekster_state),
        "visualisering_png": visu_png,
        "designdiagram_png": designdiagram_png,
        "valg": {
            "trafikkobling": vis_trafikkobling,
        },
    }

    filnavn_base = (
        md_state.get("projekt") or "MSL-rapport"
    ).strip().replace("/", "-").replace("\\", "-")[:60] or "MSL-rapport"
    dato_kort = md_state.get("dato", "")
    filnavn_base = f"Dimensionering - {filnavn_base} - {dato_kort}".rstrip(" -")

    klar = snit_liste is not None and len(snit_liste) > 0

    visu_hash = (
        hashlib.sha256(visu_png).hexdigest()
        if isinstance(visu_png, bytes)
        else None
    )
    designdiagram_hash = (
        hashlib.sha256(designdiagram_png).hexdigest()
        if isinstance(designdiagram_png, bytes)
        else None
    )
    rapport_fingerprint = hashlib.sha256(json.dumps(
        {
            "metadata": rapport_data["metadata"],
            "dim": rapport_data["dim"],
            "tekster": rapport_data["tekster"],
            "valg": rapport_data["valg"],
            "visualisering_sha256": visu_hash,
            "designdiagram_sha256": designdiagram_hash,
            "filnavn_base": filnavn_base,
        },
        sort_keys=True,
        default=str,
    ).encode("utf-8")).hexdigest()

    if st.button(
        "📄 Generér rapport",
        type="primary",
        disabled=not klar,
        width="stretch",
    ):
        with st.spinner("Genererer rapport..."):
            try:
                docx_bytes = rapport_mod.byg_rapport_docx(rapport_data)
            except Exception as exc:
                st.session_state.pop("rapport_genereret", None)
                st.error(f"Rapportens Word-fil kunne ikke genereres: {exc}")
            else:
                pdf_bytes = None
                pdf_error = None

                try:
                    pdf_bytes = rapport_mod.konverter_docx_til_pdf(docx_bytes)
                except Exception as exc:
                    pdf_error = str(exc)

                st.session_state["rapport_genereret"] = {
                    "fingerprint": rapport_fingerprint,
                    "filnavn_base": filnavn_base,
                    "docx_bytes": docx_bytes,
                    "pdf_bytes": pdf_bytes,
                    "pdf_error": pdf_error,
                }

                if pdf_error:
                    st.warning(
                        "Word-rapporten er genereret, men PDF-konverteringen "
                        f"fejlede: {pdf_error}"
                    )
                else:
                    st.success("Rapporten er genereret.")

    if not klar:
        st.caption("Vælg mindst ét snit for at kunne generere rapporten.")

    genereret = st.session_state.get("rapport_genereret")
    rapport_er_aktuel = (
        genereret
        and genereret.get("fingerprint") == rapport_fingerprint
    )

    if genereret and not rapport_er_aktuel:
        st.info(
            "Rapportinput er ændret siden sidste generering. Klik "
            "**Generér rapport** igen for at hente opdaterede filer."
        )

    if rapport_er_aktuel:
        if genereret.get("pdf_error"):
            st.warning(
                "PDF kunne ikke oprettes automatisk:\n\n"
                f"`{genereret['pdf_error']}`\n\n"
                "Du kan altid hente Word-filen herunder og bruge 'Gem som "
                "PDF' i Word."
            )

        if genereret.get("pdf_bytes"):
            kol_d1, kol_d2 = st.columns(2)
        else:
            kol_d1 = st.container()
            kol_d2 = None

        with kol_d1:
            st.download_button(
                "📄 Hent som Word (.docx)",
                data=genereret["docx_bytes"],
                file_name=f"{genereret['filnavn_base']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width="stretch",
            )
        if kol_d2 is not None:
            with kol_d2:
                st.download_button(
                    "📄 Hent som PDF (.pdf)",
                    data=genereret["pdf_bytes"],
                    file_name=f"{genereret['filnavn_base']}.pdf",
                    mime="application/pdf",
                    width="stretch",
                )


# ===========================================================================
# Top-level layout — sidebar + routing
# ===========================================================================

aktiv_side = render_sidebar()

if aktiv_side == "dimensionering":
    st.title("🏗️ Dimensionering")
    st.caption(
        "Beregning af bærelagstykkelse med og uden geonetarmering "
        "· Baseret på BG Byggros designmanualer til Tensar og GS-GRID, samt interne forsøgsdata"
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

    if tilstand == "Standard":
        st.caption(
            "I standardberegningen forudsættes 1 homogent bærelag med en forudsat "
            "friktionsvinkel på φ = 37°."
        )
    else:
        st.caption(
            "I brugerdefineret tilstand kan du selv sammensætte op til "
            "3 materialelag, med forskellige friktionsvinkler og egenskaber."
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

elif aktiv_side == "rapport":
    render_rapport()
