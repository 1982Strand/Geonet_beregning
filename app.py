"""
Geonet Dimensioneringsværktøj — Streamlit entrypoint.

Start med: streamlit run app.py
"""

# ---------------------------------------------------------------------------
# Sideopsætningen SKAL stå som allerførste Streamlit-kald. ui.opsaet_side()
# kalder selv st.set_page_config() og indlæser assets/byggros_theme.css.
# ---------------------------------------------------------------------------
import streamlit as st

import ui

ui.opsaet_side()
ui.topbjaelke(version="v0.4")

# ---------------------------------------------------------------------------
# Imports — efter sideopsætningen
# ---------------------------------------------------------------------------
import base64
import contextlib
import json
import hashlib
import html
import math
import os
import re

from core.data import (
    BELASTNINGSKLASSER,
    GEONET_NAVNE,
    GEONET_DB,
    GEONET_NOTER,
    KILDEDOKUMENTER,
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
    format_klasse_interval,
    TRAFIKKLASSER,
    trafik_eo_aekv,
    trafik_eu_interval,
    trafik_ubundet_tykkelse,
    eo_til_naermeste_klasse,
    format_trafikklasse,
    format_trafikklasse_interval,
    trafikklasse_noegletal,
    trafikklasser_for_belastningsklasser,
    VEJDIM_KOERSLER_STANDARD_RAEKKER,
    UBUNDET_BAERELAG_STANDARD,
    BUNDSIKRING_STANDARD,
    berig_koersel_raekker,
    koersler_fra_raekker,
    korrelation_fra_koersler,
    TRAFIK_UNDER,
    TRAFIK_OVER,
    TRAFIK_EU_PUNKTER,
)
from core.calculator import (
    beregn,
    beregn_alle_produkter,
    grupper_produkter,
    _slaa_op_interp,
)
from core.validators import valider_input
from core.diagram import byg_designdiagram, byg_raadiagram, snit_til_kolonner
from core import hjaelp as hjaelp_mod
from core.placement import (
    check_geonet_placement,
    overlap_krav_mm,
    placement_requirements,
)

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
KORRELATION_JSON = os.path.join(
    os.path.dirname(__file__),
    "trafikklasse_korrelation_brugerdefineret.json",
)
RAPPORT_METADATA_JSON = os.path.join(
    os.path.dirname(__file__),
    "rapport_metadata_brugerdefineret.json",
)
MIN_LAGTYKKELSE_MM = 200

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


# ---------------------------------------------------------------------------
# Rapport-metadata (sektion A) — huskes til næste gang på disk
# ---------------------------------------------------------------------------
# Felter der gemmes på disk. "dato" gemmes bevidst IKKE — den skal som
# udgangspunkt være dags dato, ikke en gammel gemt dato.
_RAPPORT_METADATA_DISK_FELTER = (
    "projekt", "beskrivelse", "omfang", "udfoeres_for",
    "sagsbehandler", "sagsbehandler_mail", "kontrol",
)


def _standard_rapport_metadata() -> dict:
    """Tomme projekt-oplysninger med dags dato."""
    from datetime import date as _date
    return {
        "projekt": "", "beskrivelse": "", "omfang": "",
        "udfoeres_for": "", "sagsbehandler": "", "sagsbehandler_mail": "",
        "kontrol": "",
        "dato": _date.today().isoformat(),
    }


def indlaes_rapport_metadata() -> dict:
    """Indlæs gemte projekt-oplysninger fra disk. Fallback til tomme felter."""
    md = _standard_rapport_metadata()
    if os.path.exists(RAPPORT_METADATA_JSON):
        try:
            with open(RAPPORT_METADATA_JSON, "r", encoding="utf-8") as f:
                gemt = json.load(f)
            if isinstance(gemt, dict):
                for felt in _RAPPORT_METADATA_DISK_FELTER:
                    if isinstance(gemt.get(felt), str):
                        md[felt] = gemt[felt]
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return md


def gem_rapport_metadata(md: dict) -> None:
    """Gem projekt-oplysningerne (undtagen dato) på disk."""
    data = {felt: md.get(felt, "") for felt in _RAPPORT_METADATA_DISK_FELTER}
    try:
        with open(RAPPORT_METADATA_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def slet_rapport_metadata_json() -> None:
    if os.path.exists(RAPPORT_METADATA_JSON):
        try:
            os.remove(RAPPORT_METADATA_JSON)
        except OSError:
            pass


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
            fejl.append(f"Eu {ui.mpa(eu)} findes flere gange.")
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


# ---------------------------------------------------------------------------
# Trafikklasse-korrelation: redigerbare VejDim-kørsler
# ---------------------------------------------------------------------------

_KOERSEL_FELTER = (
    "T", "eu", "slidlag", "t_slid_mm", "bindelag", "t_bindelag_mm",
    "bundet_baerelag", "t_bundet_mm", "E_asf_vist_MPa",
    "ubundet_baerelag", "t_SG_mm", "bundsikring", "t_BL_mm",
    "levetid_styrende_aar", "bemaerkning",
)
_KOERSEL_TEKSTFELTER = (
    "T", "slidlag", "bindelag", "bundet_baerelag",
    "ubundet_baerelag", "bundsikring", "bemaerkning",
)
# Tekstfelter der er kommet til efter tabellen blev redigerbar. Mangler de helt
# i en gemt tabel, indsættes standardnavnet i stedet for en tom celle.
_KOERSEL_TEKST_STANDARD = {
    "ubundet_baerelag": UBUNDET_BAERELAG_STANDARD,
    "bundsikring": BUNDSIKRING_STANDARD,
}


def _standard_koersel_raekker() -> list[dict]:
    """Frisk kopi af de indbyggede standardkørsler (rådata uden totaler)."""
    return [dict(r) for r in VEJDIM_KOERSLER_STANDARD_RAEKKER]


def _normaliser_koersel_raekker(raekker) -> list[dict]:
    """Saniter en liste af kørselsrækker fra JSON eller editoren.

    Rækker uden trafikklasse/Eu eller uden gyldige ubundne tykkelser droppes.
    Er der intet brugbart tilbage, bruges standardrækkerne.
    """
    if not isinstance(raekker, list):
        return _standard_koersel_raekker()
    ud: list[dict] = []
    for r in raekker:
        if not isinstance(r, dict):
            continue
        t = str(r.get("T") or "").strip()
        try:
            eu = int(float(r.get("eu")))
            sg = float(r.get("t_SG_mm"))
            bl = float(r.get("t_BL_mm"))
        except (TypeError, ValueError):
            continue
        if not t or sg < 0 or bl < 0:
            continue
        ny = {"T": t, "eu": eu, "t_SG_mm": sg, "t_BL_mm": bl}
        for felt in _KOERSEL_FELTER:
            if felt in ny:
                continue
            vaerdi = r.get(felt)
            if felt in _KOERSEL_TEKSTFELTER:
                if felt not in r and felt in _KOERSEL_TEKST_STANDARD:
                    ny[felt] = _KOERSEL_TEKST_STANDARD[felt]
                else:
                    ny[felt] = str(vaerdi or "").strip()
            else:
                try:
                    ny[felt] = float(vaerdi)
                except (TypeError, ValueError):
                    ny[felt] = 0.0
        ud.append(ny)

    # Migrering: tilføj (T, Eu)-celler der findes i standarden, men mangler i
    # den gemte tabel — fx nye Eu-punkter. Uden dette ville en gemt tabel fra
    # før udvidelsen blokere for de nye rækker.
    if ud:
        kendte = {(r["T"], r["eu"]) for r in ud}
        for std_r in _standard_koersel_raekker():
            if (std_r["T"], std_r["eu"]) not in kendte:
                ud.append(std_r)

    ud.sort(key=lambda r: (r["T"], r["eu"]))
    return ud or _standard_koersel_raekker()


def indlaes_koersel_raekker() -> list[dict]:
    """Indlæs kørslerne: brugerens gemte tabel, ellers standardrækkerne."""
    if os.path.exists(KORRELATION_JSON):
        try:
            # utf-8-sig: tolerér BOM fra håndredigerede filer.
            with open(KORRELATION_JSON, "r", encoding="utf-8-sig") as f:
                return _normaliser_koersel_raekker(json.load(f))
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return _standard_koersel_raekker()


def gem_koersel_raekker(raekker: list[dict]) -> None:
    """Gem kørselstabellen. Er den identisk med standarden, fjernes filen."""
    if raekker == _standard_koersel_raekker():
        slet_koersler_json_og_nulstil()
        return
    with open(KORRELATION_JSON, "w", encoding="utf-8") as f:
        json.dump(raekker, f, ensure_ascii=False, indent=2)


def slet_koersler_json_og_nulstil() -> None:
    if os.path.exists(KORRELATION_JSON):
        os.remove(KORRELATION_JSON)


def _aktiv_koersel_raekker() -> list[dict]:
    """De aktive kørsler (rådata) — grundlaget for hele trafikklasse-flowet."""
    return st.session_state.get(
        "vejdim_koersel_raekker", VEJDIM_KOERSLER_STANDARD_RAEKKER
    )


def _aktiv_koersler() -> dict:
    """De aktive kørsler som {T: {Eu: {"sg", "bl"}}} — bruges til opslaget."""
    return koersler_fra_raekker(_aktiv_koersel_raekker())


def _aktiv_korrelation() -> dict:
    """Den aktive korrelationstabel (T → Eu → Eo_ækv/zone), tilbageberegnet fra
    de aktive kørsler mod det aktive designdiagram."""
    return korrelation_fra_koersler(
        koersler_fra_raekker(_aktiv_koersel_raekker()), _aktiv_t_basis_table()
    )


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
if "vejdim_koersel_raekker" not in st.session_state:
    st.session_state["vejdim_koersel_raekker"] = indlaes_koersel_raekker()

# ---------------------------------------------------------------------------
# Farvepalette
#
# Værdierne hentes fra ui.FARVE, så app.py, ui.py og assets/byggros_theme.css
# deler én palet. Navnene er bevaret, fordi de bruges i inline-opmærkning
# gennem hele filen.
# ---------------------------------------------------------------------------
GRØN   = ui.FARVE["gron"]
GUL    = ui.FARVE["advarsel"]
RØD    = ui.FARVE["kritisk"]
GRÅ    = ui.FARVE["ink_25"]
LYS_GR = ui.FARVE["gron_050"]

# ---------------------------------------------------------------------------
# Serie-sortering til standard-oversigten
# ---------------------------------------------------------------------------
SERIE_ORDER = {"Reference": 0, "Tensar": 1, "GS-GRID": 2, "E'GRID": 3, "Manuel": 4}
REFERENCE_NAVN = "Referencenet (SX160 / T6 / TX160)"
REFERENCE_KLASSER = [3, 4, 5, 6]

# De tre net, designdiagrammerne er opstillet for. Alle har netkorrektion 0
# og effektindeks 100, og de indgår derfor i geonet-vælgeren som produkter
# mærket som referencenet, jf. _produkt_label(). TX160 er standardvalget.
STANDARD_GEONET = "Tensar TriAx TX160"
REFERENCENET = (STANDARD_GEONET, "GS-GRID SX160", "E'GRID T6")

# ---------------------------------------------------------------------------
# CSS
#
# Farver, skrifter, knapper, tabeller og bredde fastlægges i
# assets/byggros_theme.css, som indlæses af ui.opsaet_side(). De regler,
# stylesheetet ikke dækker, står i dets afsnit 14.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hjælpefunktioner til bokse
# ---------------------------------------------------------------------------

def _noegletal_tabel_html(
    raekker: list[tuple[str, str]], *, dæmpet: bool = False
) -> str:
    """Tostrenget opstilling, hvor værdierne står lodret på linje.

    border:none og background:none sættes på alle elementer — ellers tegner
    Streamlits tabel-CSS rammer og stribede rækker. dæmpet=True giver mindre
    skrift og grå betegnelser, til brug uden for en farvet boks.
    """
    lille = "font-size:0.82rem;" if dæmpet else ""
    navn_farve = "color:#555;" if dæmpet else ""
    nul = "border:none;background:none;"
    return (
        f'<table style="border-collapse:collapse;width:100%;{nul}{lille}">'
        + "".join(
            f'<tr style="{nul}">'
            f'<td style="padding:2px 16px 2px 0;vertical-align:top;'
            f'{nul}{navn_farve}">{navn}:</td>'
            f'<td style="padding:2px 0;font-weight:700;vertical-align:top;'
            f'{nul}">{vaerdi}</td></tr>'
            for navn, vaerdi in raekker
        )
        + "</table>"
    )


def vis_fejl(tekst: str):        ui.besked(tekst, "kritisk")
def vis_advarsel(tekst: str):    ui.besked(tekst, "advarsel")
def vis_anbefaling(tekst: str):  ui.besked(tekst, "info")

# ---------------------------------------------------------------------------
# Belastningsklasse-ikoner
#
# Material Symbols frem for emoji: de tegnes af Streamlit selv og gengives ens
# på tværs af styresystemer.
# ---------------------------------------------------------------------------
KLASSE_IKON = {
    1: ":material/directions_bike:",
    2: ":material/agriculture:",
    3: ":material/directions_car:",
    4: ":material/local_shipping:",
    5: ":material/construction:",
    6: ":material/flight:",
}


# ===========================================================================
# Fælles input-widgets (genbruges på tværs af tilstande)
# ===========================================================================

def _cv_eu_tabel_html(eu_opslag: float | None) -> str:
    """Opslagstabellen mellem vingestyrke og E-modul, aktiv række markeret."""
    rækker = []
    for cv_min, cv_max, eu_trin in CV_TIL_EU:
        interval = f"0 – {cv_max}" if cv_min == 0 else f"{cv_min + 1} – {cv_max}"
        css = "cv-row-aktiv" if eu_trin == eu_opslag else ""
        rækker.append(
            f'<tr class="{css}"><td>{eu_trin:.0f} MN/m²</td>'
            f'<td>{interval} kN/m²</td></tr>'
        )
    return (
        '<table class="cv-eu-tabel">'
        '<thead><tr><th>E-modul på planum Eu</th>'
        '<th>Tilhørende vingestyrke Cv</th></tr></thead>'
        f'<tbody>{"".join(rækker)}</tbody></table>'
        '<p class="cv-eu-note">Relationen mellem E-modul og vingestyrke som '
        'typisk findes for moræneler, gytje og lignende.</p>'
    )


def _vis_cv_eu_korrelation(cv: int, eu_opslag: float) -> None:
    """Vis det aktuelle Cv→Eu-opslag med graf og den fulde opslagstabel."""
    import plotly.graph_objects as go

    interval = next(
        (
            (cv_min, cv_max)
            for cv_min, cv_max, eu in CV_TIL_EU
            if eu == eu_opslag and cv_min <= cv <= cv_max
        ),
        None,
    )
    if interval is None:
        interval_txt = "det valgte interval"
    else:
        cv_min, cv_max = interval
        interval_txt = (
            f"0–{cv_max} kN/m²" if cv_min == 0
            else f"{cv_min + 1}–{cv_max} kN/m²"
        )

    st.markdown("**Udledt E-modul**")
    st.markdown(f"## {ui.mpa(eu_opslag)}")
    st.code(
        f"Cv = {cv} kN/m² ligger i intervallet {interval_txt}\n"
        f"Eu = {ui.mpa(eu_opslag)}",
        language=None,
    )
    st.caption(
        "Eu er et tabelopslag fra den ukorrigerede vingestyrke Cv."
    )

    xs: list[float] = []
    ys: list[float] = []
    for cv_min, cv_max, eu in CV_TIL_EU:
        xs.extend([cv_min, cv_max])
        ys.extend([eu, eu])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", name="Cv–Eu-korrelation",
        line=dict(color="#15211A", width=2, shape="hv"),
        hovertemplate="Cv %{x:.0f} kN/m² · Eu %{y:.0f} MPa<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[cv], y=[eu_opslag], mode="markers", name="Valgt værdi",
        marker=dict(color="#1B6B34", size=10, line=dict(color="white", width=2)),
        hovertemplate=f"Cv {cv} kN/m² · Eu {ui.mpa(eu_opslag)}<extra></extra>",
    ))
    fig.update_layout(
        height=230,
        margin=dict(l=10, r=10, t=24, b=10),
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(title="Cv (kN/m²)", range=[0, 180], dtick=30, gridcolor="#E6EAE6"),
        yaxis=dict(title="Eu (MPa)", range=[0, 32], dtick=5, gridcolor="#E6EAE6"),
    )
    st.markdown("**Sammenhæng**")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown(_cv_eu_tabel_html(eu_opslag), unsafe_allow_html=True)


def input_underbund(
    key_prefix: str, kompakt: bool = False, uden_etiket: bool = False,
) -> float:
    """Render Underbund (Eu eller Cv → Eu). Returnerer Eu i MPa.

    kompakt=True anvendes i inputkolonnen, hvor bredden ikke rummer
    opslagstabellen ved siden af slideren; tabellen lægges da i et popover.
    """
    if uden_etiket:
        pass          # etiketten sættes af trin-kortets kolonne
    elif kompakt:
        ui.etiket("Underbund")
    else:
        st.subheader("Underbund")
    if not kompakt:
        st.caption(
            "Vælg om underbundens E-modul (Eu) angives direkte, eller udledes ud fra "
            "en korrelation med vingestyrken Cv."
        )

    eu_mode = st.segmented_control(
        "Input-form",
        ["Eu — E-modul", "Cv — vingestyrke"],
        default="Eu — E-modul",
        key=f"{key_prefix}_eu_mode",
        label_visibility="collapsed",
        width="stretch",
    ) or "Eu — E-modul"

    if eu_mode.startswith("Eu"):
        eu = float(st.slider(
            "Eu (MPa)", min_value=int(EU_MIN), max_value=int(EU_MAX),
            value=10, step=1, key=f"{key_prefix}_eu_slider",
            help="Angiv E-modul for underbunden. Oftest målt ved belastningsforsøg i marken, eller skønnet.",
        ))
        # Værdien aflæses på skyderen og gentages ikke nedenunder.
        return eu

    cv = st.slider(
        "Cv (kN/m²)", min_value=0, max_value=180,
        value=60, step=5, key=f"{key_prefix}_cv_slider",
        help="Ukorrigeret vingerstyrke fra feltmåling/markjournal.",
    )
    eu_opslag = cv_til_eu(float(cv))
    if eu_opslag is None:
        st.error("Cv er uden for tabelområdet (0–180 kN/m²).")
        return 10.0
    st.caption(f"Cv = {cv} kN/m²  →  **Eu = {ui.mpa(eu_opslag)}**")

    tabel_html = _cv_eu_tabel_html(eu_opslag)
    if kompakt:
        with st.popover("Se korrelationstabel", width="stretch"):
            _vis_cv_eu_korrelation(cv, eu_opslag)
    else:
        st.markdown(
            f'<div class="cv-eu-wrap">{tabel_html}</div>', unsafe_allow_html=True
        )
    return eu_opslag


def _klasse_diagram_sti(valgt: int) -> str | None:
    """Filsti til designdiagram-billedet for en belastningsklasse."""
    diagram = next(
        (
            d for d in st.session_state.get("designdiagrammer", [])
            if d["klasse"] == valgt
        ),
        None,
    )
    if not diagram:
        return None
    return os.path.join(
        os.path.dirname(__file__), "diagrambilleder", diagram["image_name"],
    )


def input_belastning(
    key_prefix: str, kompakt: bool = False, uden_etiket: bool = False,
) -> tuple[int, dict, float]:
    """Render Belastningsklasse som en vælger med de seks klasser.

    Returnerer (klasse, info, eo). kompakt=True lægger designdiagrammet i et
    popover, idet inputkolonnen ikke er bred nok til at vise det ved siden af.
    """
    if uden_etiket:
        pass          # etiketten sættes af trin-kortets kolonne
    elif kompakt:
        ui.etiket("Belastningsklasse")
    else:
        st.subheader("Belastningsklasse")

    state_key = f"{key_prefix}_valgt_klasse"
    if state_key not in st.session_state:
        st.session_state[state_key] = 4

    def _vis_klasse(nr: int) -> str:
        return f"{KLASSE_IKON[nr]} {nr}"

    valgt = st.segmented_control(
        "Belastningsklasse",
        list(BELASTNINGSKLASSER.keys()),
        format_func=_vis_klasse,
        key=state_key,
        label_visibility="collapsed",
        width="stretch",
    )
    # Segmented control tillader fravalg. Falder valget bort, fastholdes den
    # senest gyldige klasse, så beregningen ikke mister sit grundlag.
    if valgt is None:
        valgt = st.session_state.get(f"{key_prefix}_sidste_klasse", 4)
        st.session_state[state_key] = valgt
    st.session_state[f"{key_prefix}_sidste_klasse"] = valgt

    info = BELASTNINGSKLASSER[valgt]
    eo = float(info["eo"])

    sti = _klasse_diagram_sti(valgt)
    if sti:
        if kompakt:
            with st.popover("Se designdiagram", width="stretch"):
                st.image(sti, width="stretch")
        else:
            _, kol_diagram, _luft = st.columns([1.1, 0.95, 0.45], gap="large")
            with kol_diagram, st.container(key="kl_diagram_wrap"):
                st.image(sti, width="stretch")
    return valgt, info, eo


def _vis_korrelationstabel(
    korr: dict,
    *,
    valgt_t: str | None = None,
    eu: float | None = None,
    key_prefix: str = "",
    med_forklaring: bool = True,
) -> None:
    """Vis Eo_ækv-tabellen (T × Eu) med den aktuelle celle markeret.

    Bruges både i dimensioneringen (så man kan se hele korrelationen mens man
    vælger trafikklasse) og i Trafikklasse-sektionen. valgt_t/eu markerer den række og
    celle, dimensioneringen aktuelt slår op i.

    med_forklaring=False udelader overskrift og zoneforklaring. Anvendes på
    korrelationssiden, hvor trinnets hoved bærer overskriften, og hvor zonerne
    forklares samlet under tabellen.
    """
    import pandas as pd

    df = pd.DataFrame(_korrelation_pivot_rows(korr)).set_index("Trafikklasse")

    # Eu markeres kun, når det rammer et af de tabulerede punkter præcist.
    eu_kol = None
    if eu is not None:
        eu_rundet = int(round(eu))
        if abs(eu - eu_rundet) < 1e-9 and eu_rundet in TRAFIK_EU_PUNKTER:
            eu_kol = f"Eu {eu_rundet}"

    def _markering(data: pd.DataFrame) -> pd.DataFrame:
        stil = pd.DataFrame("", index=data.index, columns=data.columns)
        if valgt_t in data.index:
            stil.loc[valgt_t, :] = "background-color: #F5FAF1;"
            if eu_kol in data.columns:
                stil.loc[valgt_t, eu_kol] = (
                    f"background-color: {LYS_GR}; color: #173404; font-weight: 700;"
                )
        return stil

    if med_forklaring:
        st.markdown("**Ækvivalent Eo (MPa) — hele korrelationstabellen**")
    st.dataframe(df.style.apply(_markering, axis=None), width="content")
    if not med_forklaring:
        return
    if eu_kol is None and eu is not None:
        note = (
            f"Eu = {ui.mpa(eu)} ligger mellem tabellens punkter — Eo_ækv "
            f"interpoleres mellem nabokolonnerne."
        )
    else:
        note = "Den markerede celle er den, dimensioneringen slår op i."
    st.caption(
        f"{note} **under** = VejDim kræver en tyndere opbygning end "
        f"diagrammets område · **over** = tykkere end diagrammets område. "
        f"Se *Trafikklasse-korrelation* i menuen for metode og datagrundlag."
    )


def input_trafikklasse(
    key_prefix: str, eu: float, kompakt: bool = False,
    uden_etiket: bool = False,
) -> dict:
    """Render Trafikklasse-vælger (T1–T6) + udledt ækvivalent Eo og zone.

    Bruger korrelationen KORRELATION_T_EO (dokumenteret bro fra VejDim til
    designdiagrammerne). Returnerer en grundlag-dict — se input_grundlag().

    kompakt=True lægger korrelationstabellen i et popover, idet inputkolonnen
    ikke er bred nok til at vise den ved siden af vælgeren.
    """
    if uden_etiket:
        pass          # etiketten sættes af trin-kortets kolonne
    elif kompakt:
        ui.etiket("Trafikklasse")
    else:
        st.subheader("Trafikklasse (Vejdirektoratet)")

    state_key = f"{key_prefix}_valgt_tklasse"
    if state_key not in st.session_state:
        st.session_state[state_key] = "T4"

    valgt_t = st.segmented_control(
        "Trafikklasse",
        list(TRAFIKKLASSER.keys()),
        key=state_key,
        label_visibility="collapsed",
        width="stretch",
    )
    # Segmented control tillader fravalg. Falder valget bort, fastholdes den
    # senest gyldige klasse, så beregningen ikke mister sit grundlag.
    if valgt_t is None:
        valgt_t = st.session_state.get(f"{key_prefix}_sidste_tklasse", "T4")
        st.session_state[state_key] = valgt_t
    st.session_state[f"{key_prefix}_sidste_tklasse"] = valgt_t

    eo_aekv, zone = trafik_eo_aekv(
        valgt_t, eu,
        koersler=_aktiv_koersler(),
        t_basis_table=_aktiv_t_basis_table(),
    )
    naermeste = eo_til_naermeste_klasse(eo_aekv)

    if kompakt:
        with st.popover("Se korrelationstabel", width="stretch"):
            _vis_korrelationstabel(
                _aktiv_korrelation(), valgt_t=valgt_t, eu=eu, key_prefix=key_prefix
            )

    # Nøgletallene står i trin 1's tredje kolonne og gentages ikke her.
    # Falder driftspunktet uden for kernezonen, oplyses det derimod, da
    # der da ikke er noget grundlag at dimensionere efter.
    if zone == "under":
        ui.besked(
            f"<b>{valgt_t} · Eu = {ui.mpa(eu)} er uden for kernezonen "
            f"(under).</b> VejDim kræver en tyndere ubunden opbygning end "
            f"designdiagrammernes område. Dimensionér i stedet via "
            f"<b>Belastningsklasse</b>-grundlaget. "
            f"(Frost/koblingshøjde styrer ofte disse tilfælde.)",
            "advarsel",
        )
    elif zone == "over":
        ui.besked(
            f"<b>{valgt_t} · Eu = {ui.mpa(eu)} er uden for kernezonen "
            f"(over).</b> VejDims krav overstiger designdiagrammernes "
            f"tykkelsesområde. En konkret VejDim-beregning er nødvendig.",
            "advarsel",
        )
    elif zone != "ok":  # udenfor de kørte punkter
        interval = trafik_eu_interval(valgt_t, _aktiv_koersler())
        interval_txt = (
            f"{interval[0]}–{interval[1]} MPa" if interval
            else "ingen kørsler endnu"
        )
        ui.besked(
            f"<b>Eu = {ui.mpa(eu)} er uden for de kørte punkter for "
            f"{valgt_t} ({interval_txt}).</b> Vælg et Eu i intervallet, "
            f"udfyld kørslen under <b>Trafikklasse-korrelation</b>, eller "
            f"brug <b>Belastningsklasse</b>-grundlaget.",
            "advarsel",
        )
    if not kompakt:
        _vis_korrelationstabel(
            _aktiv_korrelation(), valgt_t=valgt_t, eu=eu, key_prefix=key_prefix
        )

    # Grundlaget for koblingen er beskrevet i Hjælp, kapitel 1 og 2.

    return {
        "type": "trafikklasse",
        "eo": eo_aekv,
        "valgt_klasse": naermeste,
        "t_klasse": valgt_t,
        "eo_aekv": eo_aekv,
        "zone": zone,
        "info": TRAFIKKLASSER[valgt_t],
    }


def input_grundlag(
    key_prefix: str, eu: float, kompakt: bool = False,
    uden_etiket: bool = False,
) -> dict:
    """Render valg af dimensioneringsgrundlag (belastningsklasse vs. trafikklasse)
    og dispatch til den relevante inputwidget.

    Returnerer en normaliseret grundlag-dict, som begge tilstande kan bruge:
        {
          "type":         "belastningsklasse" | "trafikklasse",
          "eo":           float | None,   # None hvis trafikklasse-zone blokerer
          "valgt_klasse": int | None,     # belastningsklasse til badges/reference
          "t_klasse":     str | None,     # kun trafikklasse
          "eo_aekv":      float | None,   # kun trafikklasse
          "zone":         str | None,     # kun trafikklasse: ok/under/over/udenfor
          "info":         dict,
        }
    """
    if kompakt and not uden_etiket:
        ui.etiket("Dimensioneringsgrundlag")

    grundlag_valg = st.segmented_control(
        "Dimensioneringsgrundlag",
        ["Belastningsklasse", "Trafikklasse"],
        default="Belastningsklasse",
        key=f"{key_prefix}_grundlag",
        label_visibility="collapsed" if kompakt else "visible",
        width="stretch",
        help=(
            "**Belastningsklasse:** dimensionér ud fra Tensar/GS-GRID-"
            "belastningsklasserne (1–6) som hidtil.  \n"
            "**Trafikklasse:** dimensionér ud fra Vejdirektoratets "
            "trafikklasser (T1–T6) via en dokumenteret korrelation til "
            "designdiagrammerne."
        ),
    ) or "Belastningsklasse"

    if grundlag_valg.startswith("Belastning"):
        valgt_klasse, info, eo = input_belastning(
            key_prefix, kompakt=kompakt, uden_etiket=uden_etiket,
        )
        return {
            "type": "belastningsklasse",
            "eo": eo,
            "valgt_klasse": valgt_klasse,
            "t_klasse": None,
            "eo_aekv": None,
            "zone": None,
            "info": info,
        }

    return input_trafikklasse(key_prefix, eu, kompakt=kompakt, uden_etiket=uden_etiket)


# ---------------------------------------------------------------------------
# Trafikklasse-kobling: forklaring (tykkelses-først)
# ---------------------------------------------------------------------------

def _trafik_kobling_tal(eu: float, eo_aekv: float, t_basis_table: dict) -> dict:
    """Nøgletal bag trafikklasse-forklaringen.

    Returnerer den krævede ubundne tykkelse (ustabiliseret opslag ved Eo_ækv)
    samt de to belastningsklasse-kurver som Eo_ækv ligger imellem, med deres
    tykkelser — så koblingen kan forklares konkret med tal. Felter kan være
    None hvis diagrammet ikke har uarmeret-data i punktet.
    """
    t_krav = _slaa_op_interp(eu, eo_aekv, "uarmeret", t_basis_table=t_basis_table)
    kols = sorted(EO_KOLONNER)
    lav_col = max((k for k in kols if k <= eo_aekv), default=kols[0])
    hoej_col = min((k for k in kols if k >= eo_aekv), default=kols[-1])
    t_lav = _slaa_op_interp(eu, lav_col, "uarmeret", t_basis_table=t_basis_table)
    t_hoej = _slaa_op_interp(eu, hoej_col, "uarmeret", t_basis_table=t_basis_table)
    return {
        "t_krav_mm": t_krav * 10 if t_krav is not None else None,
        "kl_lav": eo_til_klasse(lav_col),
        "kl_hoej": eo_til_klasse(hoej_col),
        "eo_lav": lav_col,
        "eo_hoej": hoej_col,
        "t_lav_mm": t_lav * 10 if t_lav is not None else None,
        "t_hoej_mm": t_hoej * 10 if t_hoej is not None else None,
    }


def _eo_aekv_trin_tal(t_klasse: str, eu: float, t_basis_table: dict) -> dict | None:
    """Mellemregningerne bag Eo_ækv, så regnestykket kan vises med tal.

    Trin 1 er VejDims krævede ubundne tykkelse ved dette Eu — enten et direkte
    opslag i en kørsel eller en interpolation i log(Eu) mellem to kørsler.
    Trin 2 er tilbageberegningen mellem de to Eo-kurver, tykkelsen falder
    imellem. Returnerer None, hvis grundlaget mangler i punktet.
    """
    koersler = _aktiv_koersler()
    rk = (koersler or {}).get(t_klasse) or {}

    def _total(v) -> float:
        if isinstance(v, dict):
            return float((v.get("sg") or 0) + (v.get("bl") or 0))
        return float(v or 0)

    kendte = sorted(p for p in rk if _total(rk[p]) > 0)
    ub = trafik_ubundet_tykkelse(t_klasse, eu, koersler)
    if ub is None or not kendte:
        return None

    # --- Trin 1: kørt punkt eller interpolation i log(Eu)? ---------------
    eu_rundet = int(round(eu))
    direkte = abs(eu - eu_rundet) < 1e-9 and eu_rundet in kendte
    trin1: dict = {"ubundet_mm": ub, "direkte": direkte, "kendte": kendte}
    if direkte:
        v = rk[eu_rundet]
        trin1["eu_punkt"] = eu_rundet
        trin1["sg"] = (v.get("sg") or 0) if isinstance(v, dict) else None
        trin1["bl"] = (v.get("bl") or 0) if isinstance(v, dict) else None
    else:
        lav = max((p for p in kendte if p <= eu), default=None)
        hoej = min((p for p in kendte if p >= eu), default=None)
        if lav is None or hoej is None or hoej == lav:
            return None
        trin1.update(
            lav=lav,
            hoej=hoej,
            t_lav=_total(rk[lav]),
            t_hoej=_total(rk[hoej]),
            frac=(math.log(eu) - math.log(lav)) / (math.log(hoej) - math.log(lav)),
        )

    # --- Trin 2: diagrammets uarmerede kurver ved dette Eu ---------------
    kurver = []
    for eo in sorted(EO_KOLONNER):
        t = _slaa_op_interp(eu, eo, "uarmeret", t_basis_table=t_basis_table)
        if t is not None:
            kurver.append((eo, t * 10.0))
    if not kurver:
        return None
    kurver.sort(key=lambda p: p[1])
    trin2: dict = {"kurver": kurver}
    for (e1, t1), (e2, t2) in zip(kurver, kurver[1:]):
        if t1 <= ub <= t2 and t2 > t1:
            frac = (ub - t1) / (t2 - t1)
            trin2.update(
                eo_lav=e1, eo_hoej=e2, t_lav=t1, t_hoej=t2,
                frac=frac, eo_aekv=e1 + frac * (e2 - e1),
            )
            break

    # --- Trin 3: de armerede kurver i de SAMME to nabokolonner ----------
    # Interpolationen i Eo er lineær, og uarmeret-rækken er lineær i tykkelse
    # mellem samme to kolonner — derfor er "hvor langt inde mellem klasserne"
    # det samme tal, uanset om det måles i Eo eller i tykkelse. Den ene vægt
    # bruges derfor på alle tre rækker.
    trin3: dict = {}
    if "eo_aekv" in trin2:
        for lag in ("1_lag", "2_lag"):
            a = _slaa_op_interp(eu, trin2["eo_lav"], lag, t_basis_table=t_basis_table)
            b = _slaa_op_interp(eu, trin2["eo_hoej"], lag, t_basis_table=t_basis_table)
            if a is None or b is None:
                continue
            a, b = a * 10.0, b * 10.0
            trin3[lag] = {
                "lav": a, "hoej": b, "basis": a + trin2["frac"] * (b - a),
            }
    return {"trin1": trin1, "trin2": trin2, "trin3": trin3}


# ===========================================================================
# Koblingssektionen »Sådan er tallene fremkommet«
# ===========================================================================
# Sporet fra trafikklasse til færdig bærelagstykkelse, opstillet som seks trin
# i beregningens egen rækkefølge: dimensioneringstrafikken, VejDims krav til
# de ubundne lag, driftspunktet i designdiagrammet, kurvens plads mellem to
# belastningsklasser, korrektionen for friktionsvinklen og reduktionen med
# geonet. Hvert trin viser sit eget regnestykke med brugerens tal.
#
# Trinnene står åbne, så kæden kan læses ovenfra og ned. Det tal, der bæres
# videre til næste trin, står som resultat i højre kant af sit eget trin.

# Figurernes tegneflade. Begge figurer har samme viewBox, så de står ens i
# hver sin spalte, og samme margener, så akserne flugter.
_KOB_SVG_B, _KOB_SVG_H = 400.0, 250.0
_KOB_X0, _KOB_X1 = 50.0, 380.0
_KOB_Y0, _KOB_Y1 = 36.0, 208.0

# Kurvefarver i trin 4. De to lag-farver følger designdiagrammets egne.
_KOB_FARVE_1LAG = "#2C5AA0"
_KOB_FARVE_2LAG = "#7B3F8C"


def _kob_tal(v: float | None, decimaler: int = 0) -> str:
    """Tal med dansk tusindtalsseparator og decimalkomma, uden enhed.

    ui.mm() og _dk_num() dækker hver sin halvdel — den ene sætter tusinder,
    den anden decimalkomma. Regnestykkerne har brug for begge dele på én gang.
    """
    if v is None:
        return "—"
    s = f"{v:,.{decimaler}f}"
    heltal, _, dec = s.partition(".")
    ud = heltal.replace(",", ".")
    if dec:
        ud = f"{ud},{dec}"
    return "−" + ud[1:] if ud.startswith("-") else ud


def _kob_esc(tekst) -> str:
    """Tekst klar til at indgå i sektionens HTML."""
    return html.escape(str(tekst))


def _kob_formel(*linjer: str) -> str:
    """Regnestykket i egen ramme, sat op som i φ-korrektionsboksen.

    Linjerne sættes med white-space:pre, jf. stylesheettets .kob-formel, så
    mellemrummene i opstillingen bevares og tallene står lodret på linje.
    """
    return '<div class="kob-formel">' + "\n".join(linjer) + "</div>"


def _kob_regnelinje(tekst: str, tal: str, bredde: int = 33, tal_bredde: int = 10) -> str:
    """En linje i et regnestykke: betegnelse til venstre, tallet højrestillet.

    Justeringen sker med mellemrum og forudsætter derfor, at hverken tekst
    eller tal indeholder opmærkning — den ville tælle med i bredden.
    """
    return f"{tekst:<{bredde}}{tal:>{tal_bredde}}"


def _kob_slutlinje(tekst: str, tal: str, bredde: int = 33, tal_bredde: int = 10) -> str:
    """Regnestykkets sidste linje: resultatet fremhævet i samme talkolonne.

    Opmærkningen sættes efter justeringen, så tallet står lodret under de
    øvrige linjers tal.
    """
    return (
        _kob_esc(f"{tekst:<{bredde}}")
        + f"<b>{_kob_esc(tal.rjust(tal_bredde))}</b>"
    )


def _kob_trin(
    nr: int,
    titel: str,
    kilde: str,
    krop: str,
    *,
    resultat: str = "",
    resultat_note: str = "",
    chip: str = "",
    groent_resultat: bool = False,
    mono_note: bool = False,
) -> str:
    """Ét trin: overskriftslinje med resultatet i højre kant og kroppen under."""
    chip_html = f'<span class="kob-chip">{chip}</span>' if chip else ""
    res_klasse = "kob-res-tal kob-groen" if groent_resultat else "kob-res-tal"
    note_klasse = "kob-res-note kob-groen" if mono_note else "kob-res-note"
    res_html = ""
    if resultat:
        res_html = (
            f'<div class="{res_klasse}">{resultat}</div>'
            + (f'<div class="{note_klasse}">{resultat_note}</div>'
               if resultat_note else "")
        )
    return (
        '<div class="kob-trin">'
        f'<div class="kob-nr">{nr}</div>'
        f'<div><span class="kob-titel">{titel}</span> '
        f'<span class="kob-kilde">— {kilde}</span>{chip_html}</div>'
        f'<div class="kob-res">{res_html}</div>'
        "</div>"
        f'<div class="kob-krop">{krop}</div>'
    )


def _kob_kol(venstre: str, figur: str) -> str:
    """Regnestykket til venstre, trinnets figur til højre.

    Venstre side pakkes i sit eget element: dens dele — kort, formel og note
    — ville ellers hver især blive placeret i en celle i gitteret og lægge
    sig ved siden af figuren i stedet for under hinanden.

    Uden figur fylder regnestykket hele bredden; en tom spalte ville blot
    forskyde teksten.
    """
    if not figur:
        return venstre
    return (
        '<div class="kob-kol">'
        f'<div class="kob-venstre">{venstre}</div>'
        f"{figur}</div>"
    )


# --- Figurerne -------------------------------------------------------------
# Begge figurer tegnes som SVG med brugerens egne tal. De hører til hvert sit
# trin og gentager ikke designdiagrammet længere oppe på siden: den første
# viser trafikklassens VejDim-kørsler, den anden de tre kurver, reduktionen
# aflæses på.

def _kob_skala(vaerdier: list[float], log: bool = False):
    """Afbildning fra dataområde til tegneflade, med lidt luft i hver ende."""
    lav, hoej = min(vaerdier), max(vaerdier)
    if hoej <= lav:
        hoej = lav + 1.0
    if log:
        lav, hoej = math.log(lav), math.log(hoej)
    spand = hoej - lav
    lav, hoej = lav - spand * 0.08, hoej + spand * 0.08
    return lav, hoej


def _kob_figur_koersler(t_klasse: str, eu: float, t1: dict) -> str:
    """Trafikklassens VejDim-kørsler med brugerens Eu markeret.

    Kørslerne står som punkter, og E-værdien er afsat i log-skala — det er
    den skala, tykkelsen aftager retlinet i, og dermed den, interpolationen
    foretages i, jf. trafik_ubundet_tykkelse().
    """
    rk = (_aktiv_koersler() or {}).get(t_klasse) or {}
    punkter: list[tuple[float, float]] = []
    for p in sorted(rk):
        v = rk[p]
        t = ((v.get("sg") or 0) + (v.get("bl") or 0)) if isinstance(v, dict) else float(v or 0)
        if t > 0:
            punkter.append((float(t), float(p)))
    if len(punkter) < 2:
        return ""

    ub = t1["ubundet_mm"]
    x_lav, x_hoej = _kob_skala([p[0] for p in punkter] + [ub])
    y_lav, y_hoej = _kob_skala([p[1] for p in punkter] + [float(eu)], log=True)

    def sx(v: float) -> float:
        return _KOB_X0 + (v - x_lav) / (x_hoej - x_lav) * (_KOB_X1 - _KOB_X0)

    def sy(v: float) -> float:
        return _KOB_Y1 - (math.log(v) - y_lav) / (y_hoej - y_lav) * (_KOB_Y1 - _KOB_Y0)

    dele: list[str] = []
    # Netlinjer ved de kørte E-værdier og ved fire tykkelser.
    x_ticks = _kob_akse_ticks(x_lav, x_hoej)
    dele.append('<g stroke="#EEF1EE" stroke-width="1">' + "".join(
        f'<line x1="{sx(v):.1f}" y1="{_KOB_Y0 - 2:.1f}" '
        f'x2="{sx(v):.1f}" y2="{_KOB_Y1:.1f}"></line>' for v in x_ticks
    ) + "".join(
        f'<line x1="{_KOB_X0:.1f}" y1="{sy(p):.1f}" '
        f'x2="{_KOB_X1:.1f}" y2="{sy(p):.1f}"></line>'
        for p in sorted({p[1] for p in punkter})
    ) + "</g>")
    dele.append(
        f'<g stroke="#C4CAC5" stroke-width="1">'
        f'<line x1="{_KOB_X0:.1f}" y1="{_KOB_Y0 - 4:.1f}" '
        f'x2="{_KOB_X0:.1f}" y2="{_KOB_Y1:.1f}"></line>'
        f'<line x1="{_KOB_X0:.1f}" y1="{_KOB_Y1:.1f}" '
        f'x2="{_KOB_X1 + 4:.1f}" y2="{_KOB_Y1:.1f}"></line></g>'
    )
    # Aksernes tal og benævnelser.
    dele.append(
        '<g fill="#9AA39C" font-size="9" text-anchor="end" '
        'font-family="IBM Plex Mono, monospace">' + "".join(
            f'<text x="{_KOB_X0 - 6:.1f}" y="{sy(p) + 3:.1f}">{p:.0f}</text>'
            for p in sorted({p[1] for p in punkter})
        ) + "</g>"
    )
    dele.append(
        '<g fill="#9AA39C" font-size="9" text-anchor="middle" '
        'font-family="IBM Plex Mono, monospace">' + "".join(
            f'<text x="{sx(v):.1f}" y="{_KOB_Y1 + 14:.1f}">{_kob_tal(v)}</text>'
            for v in x_ticks
        ) + "</g>"
    )
    dele.append(
        f'<text x="14" y="{(_KOB_Y0 + _KOB_Y1) / 2:.0f}" fill="#4A554E" '
        f'font-size="9" font-weight="600" text-anchor="middle" '
        f'transform="rotate(-90 14 {(_KOB_Y0 + _KOB_Y1) / 2:.0f})">'
        f'Underbund Eu [MPa]</text>'
        f'<text x="{(_KOB_X0 + _KOB_X1) / 2:.0f}" y="{_KOB_Y1 + 34:.0f}" '
        f'fill="#4A554E" font-size="9" font-weight="600" text-anchor="middle">'
        f'Ubunden lagtykkelse SG + BL [mm]</text>'
    )
    # Kørslerne som en linje med punkter.
    bane = " ".join(f"{sx(t):.1f},{sy(p):.1f}" for t, p in punkter)
    dele.append(
        f'<polyline points="{bane}" fill="none" stroke="#15211A" '
        f'stroke-width="1.6"></polyline>'
    )
    dele.append('<g fill="#15211A">' + "".join(
        f'<circle cx="{sx(t):.1f}" cy="{sy(p):.1f}" r="3.2"></circle>'
        for t, p in punkter
    ) + "</g>")
    # Brugerens punkt med hjælpelinjer ud til akserne.
    px, py = sx(ub), sy(float(eu))
    dele.append(
        f'<line x1="{_KOB_X0:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py:.1f}" '
        f'stroke="#1B6B34" stroke-width="1" stroke-dasharray="3 3"></line>'
        f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{_KOB_Y1:.1f}" '
        f'stroke="#1B6B34" stroke-width="1" stroke-dasharray="3 3"></line>'
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#1B6B34" '
        f'stroke="#fff" stroke-width="2"></circle>'
    )
    dele.append(
        f'<text x="{px + 9:.1f}" y="{py - 7:.1f}" fill="#12401F" font-size="10" '
        f'font-weight="600" font-family="IBM Plex Mono, monospace">'
        f'{_kob_tal(ub)} mm</text>'
    )
    return (
        f'<svg viewBox="0 0 {_KOB_SVG_B:.0f} {_KOB_SVG_H:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'font-family="IBM Plex Sans, sans-serif">{"".join(dele)}</svg>'
    )


def _kob_akse_ticks(lav: float, hoej: float, antal: int = 4) -> list[float]:
    """Fire runde værdier inden for aksens område."""
    spand = hoej - lav
    if spand <= 0:
        return [lav]
    raat = spand / antal
    trin = 10 ** math.floor(math.log10(raat))
    for m in (1, 2, 2.5, 5, 10):
        if trin * m >= raat:
            trin *= m
            break
    start = math.ceil(lav / trin) * trin
    ud: list[float] = []
    v = start
    while v <= hoej + 1e-9:
        ud.append(v)
        v += trin
    return ud


def _kob_figur_diagram(
    eu: float,
    eo_aekv: float,
    t2: dict,
    t_basis_table: dict,
    phi: float,
    net_kor: float,
    punkter: list[tuple[float, str, str]],
) -> str:
    """Designdiagrammets tre kurver i punktet, med nabokurverne stiplet.

    Kurverne bærer samme korrektion som beregningen — φ på den ustabiliserede
    og φ + net på de armerede — så de afsatte punkter ligger på deres egen
    kurve. Nabokurverne er de to belastningsklasser, Eo_ækv ligger imellem.
    """
    phi_kor = K_PHI * (phi - PHI_BASIS)
    eu_vals = sorted(t_basis_table.keys())

    def _kurve(eo: float, lag: str, faktor: float) -> list[tuple[float, float]]:
        ud: list[tuple[float, float]] = []
        for e in eu_vals:
            v = _slaa_op_interp(e, eo, lag, t_basis_table=t_basis_table)
            if v is not None:
                ud.append((v * 10.0 * faktor, float(e)))
        return ud

    hoved = _kurve(eo_aekv, "uarmeret", 1 + phi_kor)
    if len(hoved) < 2:
        return ""
    naboer = [
        (_kurve(t2["eo_lav"], "uarmeret", 1 + phi_kor), eo_til_klasse(t2["eo_lav"])),
        (_kurve(t2["eo_hoej"], "uarmeret", 1 + phi_kor), eo_til_klasse(t2["eo_hoej"])),
    ]
    armerede = [
        (_kurve(eo_aekv, "1_lag", 1 + phi_kor + net_kor), _KOB_FARVE_1LAG),
        (_kurve(eo_aekv, "2_lag", 1 + phi_kor + net_kor), _KOB_FARVE_2LAG),
    ]

    alle_x = [x for k, _ in naboer for x, _ in k] + [x for x, _ in hoved]
    alle_x += [x for k, _ in armerede for x, _ in k]
    alle_x += [p[0] for p in punkter]
    x_lav, x_hoej = _kob_skala(alle_x)
    y_lav, y_hoej = _kob_skala([float(e) for e in eu_vals] + [float(eu)])

    def sx(v: float) -> float:
        return _KOB_X0 + (v - x_lav) / (x_hoej - x_lav) * (_KOB_X1 - _KOB_X0)

    def sy(v: float) -> float:
        return _KOB_Y1 - (v - y_lav) / (y_hoej - y_lav) * (_KOB_Y1 - _KOB_Y0)

    def bane(k: list[tuple[float, float]]) -> str:
        return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in k)

    x_ticks = _kob_akse_ticks(x_lav, x_hoej)
    y_ticks = _kob_akse_ticks(y_lav, y_hoej)
    dele: list[str] = []
    dele.append('<g stroke="#EEF1EE" stroke-width="1">' + "".join(
        f'<line x1="{sx(v):.1f}" y1="{_KOB_Y0 - 2:.1f}" '
        f'x2="{sx(v):.1f}" y2="{_KOB_Y1:.1f}"></line>' for v in x_ticks
    ) + "".join(
        f'<line x1="{_KOB_X0:.1f}" y1="{sy(v):.1f}" '
        f'x2="{_KOB_X1:.1f}" y2="{sy(v):.1f}"></line>' for v in y_ticks
    ) + "</g>")
    dele.append(
        f'<g stroke="#C4CAC5" stroke-width="1">'
        f'<line x1="{_KOB_X0:.1f}" y1="{_KOB_Y0 - 4:.1f}" '
        f'x2="{_KOB_X0:.1f}" y2="{_KOB_Y1:.1f}"></line>'
        f'<line x1="{_KOB_X0:.1f}" y1="{_KOB_Y1:.1f}" '
        f'x2="{_KOB_X1 + 4:.1f}" y2="{_KOB_Y1:.1f}"></line></g>'
    )
    dele.append(
        '<g fill="#9AA39C" font-size="9" text-anchor="end" '
        'font-family="IBM Plex Mono, monospace">' + "".join(
            f'<text x="{_KOB_X0 - 6:.1f}" y="{sy(v) + 3:.1f}">{v:.0f}</text>'
            for v in y_ticks
        ) + "</g>"
    )
    dele.append(
        '<g fill="#9AA39C" font-size="9" text-anchor="middle" '
        'font-family="IBM Plex Mono, monospace">' + "".join(
            f'<text x="{sx(v):.1f}" y="{_KOB_Y1 + 14:.1f}">{_kob_tal(v)}</text>'
            for v in x_ticks
        ) + "</g>"
    )
    dele.append(
        f'<text x="14" y="{(_KOB_Y0 + _KOB_Y1) / 2:.0f}" fill="#4A554E" '
        f'font-size="9" font-weight="600" text-anchor="middle" '
        f'transform="rotate(-90 14 {(_KOB_Y0 + _KOB_Y1) / 2:.0f})">'
        f'Underbund Eu [MPa]</text>'
        f'<text x="{(_KOB_X0 + _KOB_X1) / 2:.0f}" y="{_KOB_Y1 + 34:.0f}" '
        f'fill="#4A554E" font-size="9" font-weight="600" text-anchor="middle">'
        f'Bærelagstykkelse [mm]</text>'
    )
    for kurve, klasse in naboer:
        if len(kurve) < 2:
            continue
        dele.append(
            f'<polyline points="{bane(kurve)}" fill="none" stroke="#C4CAC5" '
            f'stroke-width="1.2" stroke-dasharray="4 3"></polyline>'
        )
        x, y = kurve[len(kurve) // 3]
        dele.append(
            f'<text x="{sx(x) + 4:.1f}" y="{sy(y) - 4:.1f}" fill="#9AA39C" '
            f'font-size="8.5" font-family="IBM Plex Mono, monospace">'
            f'KL. {klasse}</text>'
        )
    for kurve, farve in armerede:
        if len(kurve) >= 2:
            dele.append(
                f'<polyline points="{bane(kurve)}" fill="none" stroke="{farve}" '
                f'stroke-width="1.6"></polyline>'
            )
    dele.append(
        f'<polyline points="{bane(hoved)}" fill="none" stroke="#15211A" '
        f'stroke-width="1.8"></polyline>'
    )
    # Brugerens E-værdi som vandret linje med trinnenes punkter afsat.
    py = sy(float(eu))
    dele.append(
        f'<line x1="{_KOB_X0:.1f}" y1="{py:.1f}" x2="{_KOB_X1:.1f}" y2="{py:.1f}" '
        f'stroke="#B9C1BA" stroke-width="1" stroke-dasharray="3 3"></line>'
        f'<text x="{_KOB_X0 + 4:.1f}" y="{py - 5:.1f}" fill="#7A857D" '
        f'font-size="9" font-family="IBM Plex Mono, monospace">'
        f'Eu {_kob_tal(eu)}</text>'
    )
    for x, farve, form in punkter:
        if form == "ring":
            dele.append(
                f'<circle cx="{sx(x):.1f}" cy="{py:.1f}" r="4.4" fill="#fff" '
                f'stroke="{farve}" stroke-width="1.6"></circle>'
            )
        else:
            dele.append(
                f'<circle cx="{sx(x):.1f}" cy="{py:.1f}" r="3.4" '
                f'fill="{farve}"></circle>'
            )
    return (
        f'<svg viewBox="0 0 {_KOB_SVG_B:.0f} {_KOB_SVG_H:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'font-family="IBM Plex Sans, sans-serif">{"".join(dele)}</svg>'
    )


def _kob_figurramme(svg: str, signatur: list[str], tekst: str) -> str:
    """Figuren med signatur og figurtekst under.

    Tegningen indsættes som et billede med figuren i adressen, ikke som
    inline SVG: Streamlit renser den HTML, st.html() modtager, og fjerner
    svg-elementet, hvorved rammen ville stå tom.
    """
    if not svg:
        return ""
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    sign = "".join(f"<div>{s}</div>" for s in signatur)
    return (
        '<div class="kob-figur">'
        f'<img alt="{_kob_esc(tekst)}" '
        f'src="data:image/svg+xml;base64,{data}">'
        f'<div class="kob-sign">{sign}</div>'
        f'<div class="kob-figur-tekst">{tekst}</div>'
        "</div>"
    )


# --- De seks trin ----------------------------------------------------------

def _kob_trin1(t_klasse: str, eu: float) -> str:
    """Dimensioneringstrafikken, som trafikklassen er defineret ved."""
    tk = TRAFIKKLASSER.get(t_klasse) or {}
    naae_aar = tk.get("naae10_aar") or "—"
    naae_20 = (tk.get("naae10_mio_20aar") or 0) * 1e6
    krop = _kob_formel(
        _kob_esc(
            f"{t_klasse} = {tk.get('tunge_koeretoejer', '—')} tunge køretøjer "
            f"pr. døgn, begge retninger"
        ),
        _kob_esc(f"    {tk.get('anvendelse', '')}"),
        "",
        _kob_esc(_kob_regnelinje("NÆ10 pr. år  (tabelværdi)", naae_aar)),
        _kob_slutlinje(f"NÆ10, 20 år = {naae_aar} × 20", _kob_tal(naae_20)),
    )
    krop += (
        '<div class="kob-note">Trafikklassen og '
        f"Eu = {_kob_esc(ui.mpa(eu))} er indtastet i trin 1. "
        "Alt herunder følger af dem.</div>"
    )
    return _kob_trin(
        1, "Dimensioneringstrafik", "trafikklassetabellen, "
        f"{t_klasse} {_kob_esc((tk.get('beskrivelse') or '').lower())}",
        krop,
        resultat=f"{_kob_tal(naae_20)} NÆ10",
        resultat_note="over 20 år",
    )


def _kob_trin2(t_klasse: str, eu: float, t1: dict) -> str:
    """VejDims krav til de ubundne lag — kørt punkt eller interpolation."""
    ub = t1["ubundet_mm"]
    ub_dec = 0 if abs(ub - round(ub)) < 0.05 else 1
    kendte = ", ".join(str(p) for p in t1.get("kendte", []))

    if t1["direkte"]:
        sg, bl = t1.get("sg"), t1.get("bl")
        linjer = [
            _kob_esc(f"kørsel {t_klasse} · Eu {t1['eu_punkt']} MPa"),
        ]
        if sg is not None:
            linjer += [
                _kob_esc(_kob_regnelinje("  stabilgrus SG", f"{_kob_tal(sg)} mm")),
                _kob_esc(_kob_regnelinje("  bundsikring BL", f"{_kob_tal(bl)} mm")),
            ]
        linjer.append(_kob_slutlinje("= ubundet i alt", f"{_kob_tal(ub)} mm"))
        krop = _kob_formel(*linjer)
        krop += (
            f'<div class="kob-note">Eu = {_kob_esc(ui.mpa(eu))} er et kørt '
            f"punkt, og lagtykkelsen aflæses direkte i kørselstabellen. "
            f"Kørslerne for {_kob_esc(t_klasse)} findes ved Eu = "
            f"{_kob_esc(kendte)} MPa.</div>"
        )
        chip = ""
    else:
        kort = (
            '<div class="kob-kort-par">'
            + "".join(
                '<div class="kob-kort">'
                f'<div class="kob-kort-hoved">NÆRMESTE KØRSEL {mærkat} · '
                f'EU {p} MPA</div>'
                f'<div class="kob-kort-linje">SG {_kob_tal(sg)} mm + '
                f'BL {_kob_tal(bl)} mm</div>'
                f'<div class="kob-kort-tal">= {_kob_tal(t)} mm</div></div>'
                for mærkat, p, sg, bl, t in (
                    ("UNDER", t1["lav"], *_kob_koersel_lag(t_klasse, t1["lav"]),
                     t1["t_lav"]),
                    ("OVER", t1["hoej"], *_kob_koersel_lag(t_klasse, t1["hoej"]),
                     t1["t_hoej"]),
                )
            )
            + "</div>"
        )
        f = t1["frac"]
        krop = kort + _kob_formel(
            _kob_esc(
                f"f = ln({_kob_tal(eu)} / {t1['lav']}) / "
                f"ln({t1['hoej']} / {t1['lav']}) = "
                f"{_kob_tal(math.log(eu / t1['lav']), 4)} / "
                f"{_kob_tal(math.log(t1['hoej'] / t1['lav']), 4)} = "
            ) + f"<b>{_kob_esc(_kob_tal(f, 3))}</b>",
            _kob_esc(
                f"t = {_kob_tal(t1['t_lav'])} − {_kob_tal(f, 3)} × "
                f"({_kob_tal(t1['t_lav'])} − {_kob_tal(t1['t_hoej'])}) = "
            ) + f"<b>{_kob_esc(_kob_tal(ub, ub_dec))} mm</b>",
        )
        krop += (
            '<div class="kob-note">Interpolationen foretages i log(Eu), ikke '
            "i Eu: lagtykkelsen aftager tilnærmelsesvis retlinet med log(Eu), "
            "og lineær interpolation ville give en for tynd opbygning. "
            f"Er E-værdien et kørt punkt ({_kob_esc(kendte)} MPa), aflæses "
            "kørslen direkte.</div>"
        )
        chip = f"Eu {_kob_esc(_kob_tal(eu))} er ikke kørt — interpoleres"

    figur = _kob_figurramme(
        _kob_figur_koersler(t_klasse, eu, t1),
        [
            '<div class="kob-prik"></div>kørte punkter',
            '<div class="kob-prik" style="background:#1B6B34"></div>'
            f"dit Eu = {_kob_esc(_kob_tal(eu))} MPa",
        ],
        f"{_kob_esc(t_klasse)}s VejDim-kørsler. E-værdien er afsat i "
        "log-skala — den skala, interpolationen foretages i.",
    )
    antal = sum(
        1
        for raekker in (_aktiv_koersler() or {}).values()
        for v in raekker.values()
        if (((v.get("sg") or 0) + (v.get("bl") or 0)) if isinstance(v, dict)
            else float(v or 0)) > 0
    )
    return _kob_trin(
        2, "VejDims ubundne krav",
        f"{antal} VejDim-kørsler, T1–T6 × Eu 3–40 MPa",
        _kob_kol(krop, figur),
        resultat=f"{_kob_tal(ub, ub_dec)} mm",
        resultat_note="ubundet i alt, SG + BL",
        chip=chip,
    )


def _kob_koersel_lag(t_klasse: str, eu_punkt: int) -> tuple[float, float]:
    """Kørslens stabilgrus og bundsikring ved et kørt punkt."""
    v = ((_aktiv_koersler() or {}).get(t_klasse) or {}).get(eu_punkt)
    if isinstance(v, dict):
        return float(v.get("sg") or 0), float(v.get("bl") or 0)
    return 0.0, 0.0


def _kob_trin3(eu: float, eo_aekv: float, t1: dict, t2: dict) -> str:
    """Driftspunktet: den Eo-kurve, VejDims krav svarer til ved samme Eu."""
    ub = t1["ubundet_mm"]
    ub_dec = 0 if abs(ub - round(ub)) < 0.05 else 1
    kl_lav, kl_hoej = eo_til_klasse(t2["eo_lav"]), eo_til_klasse(t2["eo_hoej"])
    krop = (
        '<div class="kob-brod">Kravet slås tilbage til den Eo-kurve i '
        "designdiagrammerne, der giver netop denne tykkelse uarmeret ved "
        "samme E-værdi. Opslaget foretages i diagrammets egen række for "
        f"Eu = {_kob_esc(ui.mpa(eu))} — ikke ved at interpolere nabokørslernes "
        "ækvivalente Eo. Værdien er en indeksværdi, der peger på en kurve, "
        "og ikke et krav til underbunden.</div>"
    )
    krop += _kob_formel(
        _kob_esc(f"uarmeret kurve ved Eu = {_kob_tal(eu)} MPa:"),
        _kob_esc(_kob_regnelinje(
            f"  Eo {t2['eo_lav']:>3} MPa  (klasse {kl_lav})",
            f"{_kob_tal(t2['t_lav'])} mm")),
        _kob_esc(_kob_regnelinje(
            f"  Eo {t2['eo_hoej']:>3} MPa  (klasse {kl_hoej})",
            f"{_kob_tal(t2['t_hoej'])} mm")),
        "",
        _kob_esc(
            f"f = ({_kob_tal(ub, ub_dec)} − {_kob_tal(t2['t_lav'])}) / "
            f"({_kob_tal(t2['t_hoej'])} − {_kob_tal(t2['t_lav'])}) = "
        ) + f"<b>{_kob_esc(_kob_tal(t2['frac'], 3))}</b>",
        _kob_esc(
            f"Eo,ækv = {t2['eo_lav']} + {_kob_tal(t2['frac'], 3)} × "
            f"({t2['eo_hoej']} − {t2['eo_lav']}) = "
            f"{_kob_tal(t2['eo_aekv'], 1)} → "
        ) + f"<b>{_kob_esc(_kob_tal(eo_aekv))} MPa</b>",
    )
    return _kob_trin(
        3, "Driftspunkt — ækvivalent Eo",
        "korrelationstabellen, tilbageberegnet i diagrammets række",
        krop,
        resultat=f"{_kob_tal(eo_aekv)} MPa",
        resultat_note="kurven beregningen læses på",
        groent_resultat=True,
    )


def _kob_trin4(
    eu: float,
    eo_aekv: float,
    t1: dict,
    t2: dict,
    t_basis_table: dict,
    phi: float,
    net_kor: float,
    punkter: list[tuple[float, str, str]],
    sign: list[str],
) -> str:
    """Kurvens plads mellem de to belastningsklasser, reduktionen aflæses på."""
    ub = t1["ubundet_mm"]
    ub_dec = 0 if abs(ub - round(ub)) < 0.05 else 1
    kl_lav, kl_hoej = eo_til_klasse(t2["eo_lav"]), eo_til_klasse(t2["eo_hoej"])
    naermeste = eo_til_naermeste_klasse(eo_aekv)
    klasser = (
        '<div class="kob-klasser">'
        f'<div class="kob-klasse"><div class="kob-klasse-hoved">'
        f'BELASTNINGSKLASSE {kl_lav}<br>Eo {t2["eo_lav"]} MPa</div>'
        f'<div class="kob-klasse-tal">{_kob_tal(t2["t_lav"])} mm</div></div>'
        f'<div class="kob-klasse kob-din"><div class="kob-klasse-hoved">'
        f'DIN KURVE<br>Eo,ækv {_kob_tal(eo_aekv)} MPa</div>'
        f'<div class="kob-klasse-tal">{_kob_tal(ub, ub_dec)} mm</div></div>'
        f'<div class="kob-klasse"><div class="kob-klasse-hoved">'
        f'BELASTNINGSKLASSE {kl_hoej}<br>Eo {t2["eo_hoej"]} MPa</div>'
        f'<div class="kob-klasse-tal">{_kob_tal(t2["t_hoej"])} mm</div></div>'
        "</div>"
    )
    venstre = klasser + _kob_formel(
        _kob_esc(f"uarmeret tykkelse ved Eu = {_kob_tal(eu)} MPa, aflæst i "
                 "diagrammerne"),
        _kob_esc(
            f"Eo,ækv ligger {_kob_tal(t2['frac'] * 100, 1)} % inde mellem "
            f"klasse {kl_lav} og {kl_hoej}"
        ),
        _kob_esc("reduktionen aflæses på samme to kurver med samme faktor"),
    )
    venstre += (
        '<div class="kob-note">Da Eo,ækv per konstruktion er valgt, så den '
        "uarmerede kurve rammer VejDims krav, er reduktionen i trin 6 "
        "designdiagrammets egen, feltdokumenterede værdi. VejDim omfatter "
        "ikke geonet, og de to metoders kriterier sammenblandes ikke.</div>"
    )
    figur = _kob_figurramme(
        _kob_figur_diagram(eu, eo_aekv, t2, t_basis_table, phi, net_kor, punkter),
        sign,
        f"De stiplede kurver er belastningsklasse {kl_lav} og {kl_hoej}; den "
        "fuldt optrukne er Eo,ækv. Punkterne på Eu-linjen er trin 5 og 6.",
    )
    return _kob_trin(
        4, "Hvor kurven ligger i designdiagrammet",
        f"designdiagram {kl_lav} og {kl_hoej}, GS-GRID/Tensar-feltforsøg",
        _kob_kol(venstre, figur),
        resultat=f"mellem klasse {kl_lav} og {kl_hoej}",
        resultat_note=f"nærmeste hele klasse: {naermeste}",
    )


def _kob_trin5(
    t_krav: float, t_uarm_kor: float | None, phi: float, materialer: list[dict],
) -> str:
    """Korrektionen for de valgte materialers friktionsvinkel."""
    # Uden afvigelse giver produktet −0,0; nulstilles, så fortegnet ikke
    # står tilbage i teksten.
    phi_kor = K_PHI * (phi - PHI_BASIS)
    phi_kor = 0.0 if abs(phi_kor) < 1e-12 else phi_kor
    linjer: list[str] = []
    kilde = "materialetabellen"
    if materialer:
        data = _phi_tabel_data(materialer)
        led = " + ".join(
            f"{_kob_tal((m.get('pct') if data['lag_mode_pct'] else m.get('tykkelse_mm')) or 0)}"
            f" × {_kob_tal(m['phi'], 1)}"
            for m in materialer
        )
        linjer += [
            _kob_esc(
                f"φ = Σ({data['symbol']}ᵢ × φᵢ) / Σ{data['symbol']}ᵢ = "
                f"({led}) / {_kob_tal(data['total_v'])}"
            ),
            _kob_esc(
                f"  = {_kob_tal(data['total_bidrag'])} / "
                f"{_kob_tal(data['total_v'])} = "
            ) + f"<b>{_kob_esc(_kob_tal(data['phi_weighted'], 2))}°</b>",
        ]
        navne = ", ".join(
            f"{m['navn']} {_kob_tal(m['phi'], 1)}°" for m in materialer
        )
        kilde = f"materialetabellen, {navne.lower()}"
    t_efter = t_uarm_kor if t_uarm_kor else t_krav
    linjer.append(
        _kob_esc(
            f"k_φ = {_kob_tal(K_PHI, 2)} × ({_kob_tal(phi, 2)} − "
            f"{_kob_tal(PHI_BASIS, 0)}) = {_kob_tal(phi_kor, 4)} = "
        ) + f"<b>{_kob_esc(_kob_tal(phi_kor * 100, 2))} %</b>"
    )
    if abs(phi_kor) >= 1e-9:
        linjer.append(
            _kob_esc(
                f"t = {_kob_tal(t_krav)} × (1 {'−' if phi_kor < 0 else '+'} "
                f"{_kob_tal(abs(phi_kor), 4)}) = "
            ) + f"<b>{_kob_esc(_kob_tal(t_efter))} mm</b>"
        )
    krop = _kob_formel(*linjer)
    if abs(phi_kor) >= 1e-9:
        note = (
            "Diagrammerne er tegnet for et referencemateriale med "
            f"φ = {_kob_esc(_kob_tal(PHI_BASIS, 0))}°. De valgte lag afviger "
            "herfra, og kurven forskydes tilsvarende; den korrigerede "
            "tykkelse er det punkt, materialerne faktisk ligger på."
        )
    else:
        note = (
            "Diagrammerne er tegnet for et referencemateriale med "
            f"φ = {_kob_esc(_kob_tal(PHI_BASIS, 0))}°, og beregningen føres "
            "med samme værdi. Korrektionen er dermed nul, og diagrammets "
            "værdi anvendes uændret. Vælges andre materialer under "
            "Brugerdefineret, slår korrektionen igennem her."
        )
    krop += f'<div class="kob-note">{note}</div>'
    return _kob_trin(
        5, "φ-korrektion for materialerne", kilde, krop,
        resultat=f"{_kob_tal(t_efter)} mm",
        resultat_note=(
            "ustabiliseret, korrigeret" if abs(phi_kor) >= 1e-9
            else "ustabiliseret, ukorrigeret"
        ),
    )


def _kob_trin6(
    t_krav: float,
    t_uarm_kor: float | None,
    t3: dict,
    phi: float,
    net_kor: float,
    net_navn: str,
    ref_1: dict | None,
    ref_2: dict | None,
) -> str:
    """Reduktionen med geonet, led for led fra VejDims krav."""
    phi_kor = K_PHI * (phi - PHI_BASIS)
    # Nettets afvigelse angives ved effektindekset, hvor det er kendt —
    # det er den størrelse, geonet-databasen ordner produkterne efter.
    indeks = (find_geonet(net_navn) or {}).get("effektindeks")
    net_maerkat = (
        f"indeks {indeks}" if indeks else f"{_kob_tal(net_kor * 100, 0)} %"
    )
    kolonner: list[str] = []
    resultater: list[str] = []
    pct_krav: list[str] = []
    for lag, navn, klasse, ref in (
        ("1_lag", "1 LAG GEONET", "kob-1lag", ref_1),
        ("2_lag", "2 LAG GEONET", "kob-2lag", ref_2),
    ):
        t_arm = (ref or {}).get("t_armeret_mm")
        if lag not in t3 or t_arm is None:
            continue
        basis = t3[lag]["basis"]
        linjer = [
            _kob_esc(_kob_regnelinje(
                "ustabiliseret bærelagstykkelse", f"{_kob_tal(t_krav)} mm")),
            _kob_esc(_kob_regnelinje(
                "− basisreduktion, referencenet",
                f"{_kob_tal(t_krav - basis)} mm")),
        ]
        if abs(net_kor) >= 0.005:
            linjer.append(_kob_esc(_kob_regnelinje(
                f"{'+' if net_kor > 0 else '−'} net-korrektion, {net_maerkat}",
                f"{_kob_tal(abs(basis * net_kor))} mm")))
        if abs(phi_kor) >= 1e-9:
            linjer.append(_kob_esc(_kob_regnelinje(
                f"{'+' if phi_kor > 0 else '−'} φ-korrektion, "
                f"{_kob_tal(phi_kor * 100, 1)} %",
                f"{_kob_tal(abs(basis * phi_kor))} mm")))
        red_krav = (t_krav - t_arm) / t_krav * 100 if t_krav else None
        red_kor = (ref or {}).get("reduktion_pct")
        hale = ""
        if red_krav is not None:
            hale = f"   (−{_kob_tal(red_krav)} % af {_kob_tal(t_krav)}"
            # Den anden reference nævnes kun, når φ-korrektionen flytter
            # udgangspunktet — ellers er de to procenter det samme tal.
            if red_kor is not None and t_uarm_kor and abs(t_uarm_kor - t_krav) >= 1:
                hale += f" · −{_kob_tal(red_kor * 100)} % af {_kob_tal(t_uarm_kor)}"
            hale += ")"
        linjer.append(
            "= " + f"<b>{_kob_esc(_kob_tal(t_arm))} mm</b>" + _kob_esc(hale)
        )
        kolonner.append(
            f'<div><div class="kob-lag-hoved {klasse}">{navn}</div>'
            + _kob_formel(*linjer) + "</div>"
        )
        resultater.append(_kob_tal(t_arm))
        if red_krav is not None:
            pct_krav.append(f"−{_kob_tal(red_krav)} %")

    if not kolonner:
        return ""
    krop = f'<div class="kob-lag">{"".join(kolonner)}</div>'
    krop += (
        '<div class="kob-note">Basisreduktionen gælder referencenettet i '
        "punktet, og net-korrektionen er det valgte nets afvigelse herfra. "
        "<b>To referencer for procenterne:</b> resultatkortet øverst regner "
        f"fra VejDims {_kob_esc(_kob_tal(t_krav))} mm, mens diagrammets "
        f"punkter ligger på de φ-korrigerede {_kob_esc(_kob_tal(t_uarm_kor))} "
        "mm. Begge er angivet, så de to sæt procenter ikke fremstår som en "
        "uoverensstemmelse.</div>"
        if t_uarm_kor and abs(t_uarm_kor - t_krav) >= 1 else
        '<div class="kob-note">Basisreduktionen gælder referencenettet i '
        "punktet, og net-korrektionen er det valgte nets afvigelse herfra."
        "</div>"
    )
    return _kob_trin(
        6, "Reduktion med geonet", f"geonet-databasen, {_kob_esc(net_navn)}",
        krop,
        resultat=f' <span class="kob-skraa">/</span> '.join(resultater) + " mm",
        resultat_note=" / ".join(pct_krav) + f" af {_kob_tal(t_krav)}",
        groent_resultat=True,
        mono_note=True,
    )


def _render_trafik_kobling_forklaring(
    t_klasse: str,
    eu: float,
    eo_aekv: float,
    phi: float,
    ref_1: dict | None,
    ref_2: dict | None,
    t_basis_table: dict,
    geonet: dict | None = None,
    materialer: list[dict] | None = None,
) -> None:
    """Sporet fra trafikklasse til bærelagstykkelse, trin for trin.

    Sektionen forklarer, hvordan de tal, resultatkortene viser, er fremkommet:
    hvert trin står med sin kilde, sit regnestykke og sit resultat, og de to
    figurer hører til hvert sit trin. Ekspanderen er lukket som udgangspunkt
    — forklaringen er baggrundsstof, der slås op efter behov — og alle seks
    trin står åbne, når den foldes ud.
    """
    tal = _eo_aekv_trin_tal(t_klasse, eu, t_basis_table)
    kobling = _trafik_kobling_tal(eu, eo_aekv, t_basis_table)
    t_krav = kobling["t_krav_mm"]
    if not tal or "eo_aekv" not in tal["trin2"] or t_krav is None:
        with st.expander("Sådan er tallene fremkommet", expanded=False):
            st.caption(
                "Designdiagrammet indeholder ingen ustabiliseret kurve i dette "
                "punkt, og sammenkædningen kan derfor ikke vises trinvist."
            )
        return

    t1, t2, t3 = tal["trin1"], tal["trin2"], tal["trin3"]
    materialer = materialer or []
    t_uarm_kor = (ref_1 or ref_2 or {}).get("t_uarmeret_phi_kor_mm")
    t_1lag = (ref_1 or {}).get("t_armeret_mm")
    t_2lag = (ref_2 or {}).get("t_armeret_mm")
    net_kor = float((geonet or {}).get("korrektion") or 0.0)
    net_navn = (geonet or {}).get("navn") or "referencenet"

    # Punkterne på Eu-linjen i trin 4's figur, med den signatur de hører til.
    punkter: list[tuple[float, str, str]] = [(t_krav, "#15211A", "ring")]
    sign = ['<div class="kob-prik-ring"></div>'
            f"{_kob_tal(t_krav)} mm krav"]
    if t_uarm_kor and abs(t_uarm_kor - t_krav) >= 1:
        punkter.append((t_uarm_kor, "#15211A", "fyldt"))
        sign.append('<div class="kob-prik"></div>'
                    f"{_kob_tal(t_uarm_kor)} mm φ-korrigeret")
    if t_1lag is not None:
        punkter.append((t_1lag, _KOB_FARVE_1LAG, "fyldt"))
        sign.append(f'<div class="kob-prik" style="background:{_KOB_FARVE_1LAG}">'
                    f"</div>{_kob_tal(t_1lag)} mm · 1 lag")
    if t_2lag is not None:
        punkter.append((t_2lag, _KOB_FARVE_2LAG, "fyldt"))
        sign.append(f'<div class="kob-prik" style="background:{_KOB_FARVE_2LAG}">'
                    f"</div>{_kob_tal(t_2lag)} mm · 2 lag")

    trin = [
        _kob_trin1(t_klasse, eu),
        _kob_trin2(t_klasse, eu, t1),
        _kob_trin3(eu, eo_aekv, t1, t2),
        _kob_trin4(eu, eo_aekv, t1, t2, t_basis_table, phi, net_kor,
                   punkter, sign),
        _kob_trin5(t_krav, t_uarm_kor, phi, materialer),
        _kob_trin6(t_krav, t_uarm_kor, t3, phi, net_kor, net_navn,
                   ref_1, ref_2),
    ]
    krop = '<div class="kob-skel"></div>'.join(t for t in trin if t)
    fod = (
        '<div class="kob-fod">VejDim omfatter ikke geonet. Kørslerne '
        "fastlægger alene driftspunktet, mens reduktionen i trin 6 er "
        "designdiagrammets egen, feltdokumenterede værdi. Kørslerne står "
        "under Trafikklasse-korrelation, og metoden er beskrevet i Hjælp, "
        "afsnit 1 og 2.</div>"
    )
    # Titlen sættes fed og underrubrikken normal, som i sektionens hoved i
    # designforslaget; ekspanderens etiket sættes af markdown.
    resultat = t_1lag if t_1lag is not None else t_2lag
    overskrift = (
        f"**Sådan er tallene fremkommet** — fra trafikklasse {t_klasse}"
    )
    if resultat is not None:
        overskrift += f" til {ui.mm(resultat)} bærelag"
    with st.expander(overskrift, expanded=False):
        st.html(f'<div class="kob">{krop}{fod}</div>')


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


def _trafik_badge_tekst(klasser: list[int], eu: float) -> str:
    """Produktets belastningsklasser oversat til trafikklasser ved dette Eu.

    Rammer ingen trafikklasse produktets klasser (fx et klasse 1-3-net ved et
    Eu, hvor alle kørte trafikklasser lander højere), vises '—'.
    """
    if not klasser:
        return "—"
    return format_trafikklasse_interval(
        trafikklasser_for_belastningsklasser(
            klasser, eu, _aktiv_koersler(), _aktiv_t_basis_table()
        )
    )


def _korrektion_label(g: dict) -> str | None:
    """Kort tekst for netkorrektionen ift. referencenettet (TX160/SX160/T6).

    Fortegnskonvention som resten af appen: positiv = tykkere bærelag (mindre
    effektiv), negativ = tyndere (mere effektiv). Returnerer fx '−10 %',
    '+20 %', '0 % (ref.)' eller '−10 … −20 %' for interval-produkter
    (NX750/NX850). None for det manuelle produkt (korrektion sættes af brugeren).
    """
    if g.get("navn") == "Anden armering (manuel)":
        return None
    interval = g.get("korrektion_interval")
    if interval:
        best, kons = interval  # (best-case, konservativ)
        return f"{kons * 100:+.0f} … {best * 100:+.0f} %"
    kor = g.get("korrektion")
    if kor is None:
        return None
    if abs(kor) < 0.005:
        return "0 % (ref.)"
    return f"{kor * 100:+.0f} %"


def _produkt_label(navn: str) -> str:
    """Dropdown-label: produktnavn + anbefalede klasser + netkorrektion, fx
    'GS-GRID SX170 (Klasse 4-6 · Net-korrektion: -10 %)'.

    Referencenettene mærkes efter navnet, jf. REFERENCENET. Tilføjelsen
    '(ref.)' udgår af korrektionen i vælgeren; den angiver alene, at
    korrektionen er 0, og flere net uden for REFERENCENET har samme værdi.
    Hvilke net der er referencenet, fremgår af mærkatet.

    Bemærk: Streamlit-dropdownen kan ikke farve en del af teksten, så
    klasse-/korrektions-delen vises i samme farve som navnet (kun captionen
    nedenunder kan vises nedtonet).
    """
    g = find_geonet(navn)
    if not g:
        return navn
    titel = f"{navn} · Referencenet" if navn in REFERENCENET else navn
    dele: list[str] = []
    kl = g.get("klasser")
    if kl:
        dele.append(f"Klasse {_format_klasse_liste(kl)}")
    kor_txt = _korrektion_label(g)
    if kor_txt:
        dele.append(f"Net-korrektion: {kor_txt.replace(' (ref.)', '')}")
    return f"{titel} ({' · '.join(dele)})" if dele else titel


def _resultat_til_gruppe(
    res: dict, geonet: dict, valgt_klasse: int
) -> dict | None:
    """
    Pak et enkelt beregn()-resultat ind i samme dict-struktur som
    grupper_produkter()-output, så det kan vises i _render_produkt_tabel.

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


def _render_uarmeret_mangler_besked(eu: float, eo: float) -> None:
    st.warning(
        "Der er ikke defineret nogen ustabiliseret bærelagstykkelse for "
        f"det valgte Eu/Eo ({ui.mpa(eu)} / {ui.mpa(eo)}). "
        "Stabiliserede resultater vises stadig, hvor designdiagrammet har data."
    )


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
    phi: float = PHI_BASIS,
) -> str:
    """Reduktions-opdeling for ÉT lag (basis/net/φ/samlet) som fortegns-deltaer.

    Linjerne summer: basisreduktion (grå, negativ) + net-korrektion (grøn hvis
    sparer, rød hvis koster) + φ-korrektion (kun når φ ≠ 37) = samlet reduktion
    (grå, overstreg). Alle deltaer måles mod rå t_uarmeret_mm, så summen går op
    med produktets faktiske t_armeret_mm = t_basis × (1 + φ-kor + net-kor).
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
            f'<span class="val">{_delta_mm(basis_delta)}</span></span>'
        )

    if t_basis is not None:
        if abs(kor) < 0.005 and is_ref:
            linjer.append(
                '<span class="rt-dlinje rt-graa">'
                '<span>Net-korrektion ift. ref.</span>'
                '<span class="val">ref. produkt (0 %)</span></span>'
            )
        elif abs(kor) < 0.005:
            linjer.append(
                '<span class="rt-dlinje rt-graa">'
                '<span>Net-korrektion (0 %) ift. ref.</span>'
                '<span class="val">0 mm</span></span>'
            )
        else:
            net_mm = round(t_basis * kor)
            css = "rt-spar" if net_mm <= 0 else "rt-pen"
            linjer.append(
                f'<span class="rt-dlinje {css}">'
                f'<span>Net-korrektion ({_pct_fortegn(kor)}) ift. ref.</span>'
                f'<span class="val">{_delta_mm(net_mm)}</span></span>'
            )

    # φ-korrektion — kun når φ afviger fra basis (Brugerdefineret). Placeres
    # lige under net-korrektion. Samme fortegns-/farvekonvention som net.
    if t_basis is not None and abs(phi - PHI_BASIS) > 0.05:
        phi_kor = K_PHI * (phi - PHI_BASIS)
        phi_mm = round(t_basis * phi_kor)
        css = "rt-spar" if phi_mm <= 0 else "rt-pen"
        linjer.append(
            f'<span class="rt-dlinje {css}">'
            f'<span>φ-korrektion ({_pct_fortegn(phi_kor)}, φ = {ui.grader(phi)})</span>'
            f'<span class="val">{_delta_mm(phi_mm)}</span></span>'
        )

    if t_uarm is not None:
        samlet_delta = -round(t_uarm - t_arm)
        linjer.append(
            '<span class="rt-dlinje rt-graa rt-samlet">'
            '<span>Samlet reduktion</span>'
            f'<span class="val">{_delta_mm(samlet_delta)}</span></span>'
        )

    return "".join(linjer)


def _rt_baerelag_linjer(p: dict | None) -> str:
    """Simpelt regnestykke for bærelagstykkelsen: ustabiliseret → reduktion → stabiliseret.

    Placeres under 'Bærelagstykkelse'-kolonnen, ved siden af den detaljerede
    faktoropdeling i _rt_reduktion_linjer (samme samlede reduktion, blot uden
    opdeling på basis/net/φ). Mellemlinjen hedder derfor 'Reduktion i alt' som
    kolonneoverskriften — den dækker hele forskellen mod den ustabiliserede
    tykkelse, altså også φ-bidraget, ikke kun geonettets.
    """
    if not _rt_gyldig(p):
        return '<span class="rt-bd-tom">—</span>'

    t_uarm = p.get("t_uarmeret_mm")
    t_arm = p["t_armeret_mm"]
    if t_uarm is None:
        return '<span class="rt-bd-tom">—</span>'

    reduktion_delta = -round(t_uarm - t_arm)
    return (
        '<span class="rt-dlinje rt-graa">'
        '<span>Ustab. bærelagstykkelse</span>'
        f'<span class="val">{ui.mm(t_uarm)}</span></span>'
        '<span class="rt-dlinje rt-graa">'
        '<span>Reduktion i alt</span>'
        f'<span class="val">{_delta_mm(reduktion_delta)}</span></span>'
        '<span class="rt-dlinje rt-graa rt-samlet">'
        '<span>Stabiliseret bærelagstykkelse</span>'
        f'<span class="val">{ui.mm(t_arm)}</span></span>'
    )


def _rt_optimal_tip_html(p: dict | None, phi: float = PHI_BASIS) -> str:
    """Tooltip-indhold: optimal opdeling for et interval-produkt (ét lag).

    Returnerer "" hvis produktet ikke er et interval-produkt (intet
    t_armeret_mm_min). Genbruger _rt_reduktion_linjer med de optimale værdier.
    Reduktionsprocenten måles mod rå t_uarmeret_mm (som resten af tabellen).

    Opdelingen på basis-, net- og φ-korrektion vises sammen med den optimale
    tykkelse, jf. afsnit 8.
    """
    if not _rt_gyldig(p) or p.get("t_armeret_mm_min") is None:
        return ""
    kor_opt = p.get("korrektion_min")
    t_opt = p["t_armeret_mm_min"]
    t_uarm = p.get("t_uarmeret_mm")
    pct_opt = (t_uarm - t_opt) / t_uarm if t_uarm else None
    linjer = _rt_reduktion_linjer(p, False, kor=kor_opt, t_arm=t_opt, phi=phi)
    pct_txt = f" ({ui.procent(pct_opt * 100)} tyndere)" if pct_opt is not None else ""
    return (
        '<span class="rt-tip-box">'
        '<span class="rt-tip-titel">Under optimale forhold</span>'
        f'{linjer}'
        '<span class="rt-dlinje rt-tip-resultat">'
        '<span>Optimal bærelagstykkelse</span>'
        f'<span class="val">{ui.mm(t_opt)}{pct_txt}</span></span>'
        '</span>'
    )


def _rt_tk_celle(
    p: dict | None, valid: bool, t_txt: str, cls: str, phi: float = PHI_BASIS
) -> str:
    """Tykkelse-celle. For interval-produkter pakkes værdien i et hover-tooltip
    med den optimale beregning; ellers vises bare værdien."""
    if valid and p is not None and p.get("t_armeret_mm_min") is not None:
        tip = _rt_optimal_tip_html(p, phi)
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
    phi: float = PHI_BASIS,
    eu: float | None = None,
    vis_indeks: bool = False,
) -> str:
    """Foldbar detalje justeret efter tabellens kolonner.

    Layout (samme grid som tabellen): 'Krav til udførsel' til venstre (under
    Produkt/klasse); under 'Bærelagstykkelse, x lag geonet' vises det simple
    regnestykke (ustabiliseret → reduktion → stabiliseret); under
    'Reduktion i alt, x lag' vises reduktionen opdelt på basis/net/φ.

    Opdelingen på basis-, net- og φ-korrektion vises i fold-ud-detaljen,
    jf. afsnit 8.
    """
    if not (_rt_gyldig(p1) or _rt_gyldig(p2)):
        return (
            '<div class="rt-detalje-tom">'
            'Ingen gyldig beregning for denne kombination.</div>'
        )

    # Krav til udførsel — uafhængig af lag. Overlægget afhænger dog af
    # underbundens E-værdi, jf. placement.overlap_krav_mm.
    geonet = None if is_ref else find_geonet(navn)
    krav = placement_requirements(geonet)
    tilslag = (geonet or {}).get("anbefalet_tilslag") or "—"
    overlap_mm, overlap_betingelse = overlap_krav_mm(krav, eu)
    krav_html = (
        '<div class="rt-d-krav">'
        '<div class="rt-krav-titel">Krav til udførsel</div>'
        '<div class="rt-dlinje rt-graa"><span>Minimum dæklag over geonet</span>'
        f'<span class="val">{ui.mm(krav["min_top_cover_mm"])}</span></div>'
        '<div class="rt-dlinje rt-graa"><span>Anbefalet afstand imellem geonetlag</span>'
        f'<span class="val">{krav["min_spacing_mm"]:.0f}–{ui.mm(krav["max_spacing_mm"])}</span></div>'
        '<div class="rt-dlinje rt-graa"><span>Anbefalet tilslagsstørrelse</span>'
        f'<span class="val">{tilslag}</span></div>'
        # Betingelsen indeholder "<" ved blød underbund og skal escapes,
        # ellers opfatter browseren den som starten på et tag.
        f'<div class="rt-dlinje rt-graa"><span>Overlæg i samlinger '
        f'({html.escape(overlap_betingelse)})</span>'
        f'<span class="val">{ui.mm(overlap_mm)}</span></div>'
        '</div>'
    )

    bt1 = _rt_baerelag_linjer(p1)
    bt2 = _rt_baerelag_linjer(p2)

    bd1 = _rt_reduktion_linjer(p1, is_ref, phi=phi)
    bd2 = _rt_reduktion_linjer(p2, is_ref, phi=phi)

    return (
        '<div class="rt-detalje">'
        f'{krav_html}'
        f'<div class="rt-d-bt rt-d-bt1">{bt1}</div>'
        f'<div class="rt-d-bd rt-d-bd1">{bd1}</div>'
        f'<div class="rt-d-bt rt-d-bt2">{bt2}</div>'
        f'<div class="rt-d-bd rt-d-bd2">{bd2}</div>'
        '</div>'
    )


def _rt_red_txt(p: dict | None) -> str:
    """Reduktionstekst for ét lag mod rå uarmeret basis: '{mm} mm ({pct})' / '—'.

    Måles mod rå t_uarmeret_mm (ikke φ-korrigeret), så kolonnen stemmer med
    fold-ud 'Samlet reduktion'. Ved φ = 37 identisk med calculator-reduktionen.
    """
    if not _rt_gyldig(p):
        return "—"
    t_uarm = p.get("t_uarmeret_mm")
    t_arm = p.get("t_armeret_mm")
    if t_uarm and t_arm is not None:
        mm = t_uarm - t_arm
        return f'{ui.mm(mm)} ({ui.procent(mm / t_uarm * 100)})'
    return "—"


def _indeks_tal(navn: str) -> int:
    """Effektindekset som tal til sortering. Ukendt indeks stilles bagest.

    Produkter med korrektionsinterval har indeks angivet som et spænd,
    eksempelvis "115–130"; den nedre ende anvendes, så sorteringen hviler på
    den konservative værdi, tabellens tykkelser også er regnet af.
    """
    raa = str((find_geonet(navn) or {}).get("effektindeks") or "")
    tal = re.match(r"\s*(\d+)", raa)
    return int(tal.group(1)) if tal else 0


def _effektindeks(navn: str, is_ref: bool = False) -> str:
    """Produktets effektindeks. Referencenettet har indeks 100.

    Indekset angiver produktets effektivitet i forhold til designmanualernes
    referencenet og er tabuleret i geonet-databasen.
    """
    if is_ref:
        return "100"
    g = find_geonet(navn) or {}
    return str(g.get("effektindeks") or "—")


def _rt_kor_celler(p: dict | None, phi: float) -> str:
    """De tre korrektionsled som selvstændige kolonner, jf. afsnit 6b.

    Basisreduktionen er forskellen mellem den ustabiliserede og den armerede
    basistykkelse; net- og φ-korrektionen er de to led, der anvendes på
    basistykkelsen. Summen er rækkens samlede reduktion.
    """
    if not _rt_gyldig(p):
        return '<span class="num rt-tom">—</span>' * 3

    t_uarm = p.get("t_uarmeret_mm")
    t_basis = p.get("t_basis_arm_mm")
    if t_uarm is None or t_basis is None:
        return '<span class="num rt-tom">—</span>' * 3

    basis = -round(t_uarm - t_basis)
    net = round(t_basis * (p.get("korrektion") or 0.0))
    phi_led = round(t_basis * K_PHI * (phi - PHI_BASIS))

    def celle(v: int) -> str:
        css = "rt-spar" if v <= 0 else "rt-pen"
        return f'<span class="num {css}">{_delta_mm(v)}</span>'

    return celle(basis) + celle(net) + celle(phi_led)


def _rt_raekke_html(
    navn: str,
    p1: dict | None,
    p2: dict | None,
    *,
    is_ref: bool = False,
    phi: float = PHI_BASIS,
    trafik_eu: float | None = None,
    eu: float | None = None,
    vis_indeks: bool = False,
    udfoldet: bool = False,
) -> str:
    """Byg én foldbar tabelrække (<details>) for et produkt/referencenet.

    Alle rækker deler details-attributten name="rt-produkt", så de opfører sig
    som en harmonika: kun én række kan være foldet ud ad gangen (native HTML
    'exclusive accordion'). Den udfoldede række markeres grønt via CSS [open].

    trafik_eu ≠ None betyder trafikklasse-tilstand: klasse-badgen oversættes
    til de trafikklasser, der slår op i produktets belastningsklasser ved
    netop dette Eu.
    """
    v1 = _rt_gyldig(p1)
    v2 = _rt_gyldig(p2)
    chosen = p1 if v1 else (p2 if v2 else (p1 or p2 or {}))

    klasser = chosen.get("klasser") or []
    klasse_ok = chosen.get("klasse_ok", True)
    kl_txt = _format_klasse_liste(klasser) if klasser else "—"
    if trafik_eu is not None:
        kl_txt = _trafik_badge_tekst(klasser, trafik_eu)
    badge_css = "rt-badge-ok" if klasse_ok else "rt-badge-advarsel"
    badge_pre = ""

    t1 = f'{int(round(p1["t_armeret_mm"]))}' if v1 else "—"
    t2 = f'{int(round(p2["t_armeret_mm"]))}' if v2 else "—"
    t1_cls = "num" if v1 else "num rt-tom"
    t2_cls = "num" if v2 else "num rt-tom"

    red1_txt = _rt_red_txt(p1)
    red2_txt = _rt_red_txt(p2)
    red1_cls = "num" if v1 else "num rt-tom"
    red2_cls = "num" if v2 else "num rt-tom"

    raekke_css = "rt-raekke rt-ref" if is_ref else "rt-raekke"
    if vis_indeks:
        raekke_css += " rt-med-indeks"
    raekke_css += " rt-med-kor"
    indeks_html = (
        f'<span class="num rt-indeks">{_effektindeks(navn, is_ref)}</span>'
        if vis_indeks else ""
    )
    kor_html = _rt_kor_celler(p1 if v1 else p2, phi)

    return (
        f'<details class="{raekke_css}" name="rt-produkt"'
        f'{" open" if udfoldet else ""}>'
        f'<summary class="rt-sum">'
        f'<span class="rt-navn"><span class="rt-chev">▸</span> {navn}</span>'
        f'{indeks_html}'
        f'<span><span class="rt-badge {badge_css}">{badge_pre}{kl_txt}</span></span>'
        f'{kor_html}'
        f'{_rt_tk_celle(p1, v1, t1, t1_cls, phi)}'
        f'<span class="{red1_cls}">{red1_txt}</span>'
        f'{_rt_tk_celle(p2, v2, t2, t2_cls, phi)}'
        f'<span class="{red2_cls}">{red2_txt}</span>'
        f'</summary>'
        f'{_rt_detalje_html(navn, p1, p2, is_ref, phi, eu, vis_indeks)}'
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
    phi: float = PHI_BASIS,
    vis_reference: bool = True,
    trafik_eu: float | None = None,
    eu: float | None = None,
    grupperet: bool = False,
    udfoldet_navn: str | None = None,
) -> None:
    """Resultattabel: én foldbar række pr. produkt. Bruges af både Standard og
    Brugerdefineret (sidstnævnte sender φ ≠ 37, som giver en φ-korrektionslinje
    i fold-ud-opdelingen).

    Referencenettet øverst som basis, derefter produkter med tyndeste
    1-lag-bærelag først (tyndeste gyldige fremhævet grønt). 1-lag og 2-lag
    vises som kolonner; detaljer (reduktions-opdeling) skjules i fold-ud.

    vis_reference=False udelader referencerækken (brugt af 'Vælg specifikt
    produkt', hvor kun det valgte produkt skal vises).

    trafik_eu sættes i trafikklasse-tilstand og skifter klasse-kolonnen til
    anbefalede trafikklasser ved netop dette Eu.

    grupperet=True anvendes i standardtilstanden, hvor produktoversigten er
    hovedindholdet: rækkerne samles under versale serieoverskrifter, og
    produktets effektindeks vises i en egen kolonne, jf. afsnit 10.
    """
    refp1 = ref_1["produkter"][0] if ref_1 and ref_1.get("produkter") else None
    refp2 = ref_2["produkter"][0] if ref_2 and ref_2.get("produkter") else None

    p1_by = {p["navn"]: p for p in prod_1lag}
    p2_by = {p["navn"]: p for p in prod_2lag}
    navne = list(p1_by.keys())
    for n in p2_by:
        if n not in p1_by:
            navne.append(n)

    # I trafikklasse-tilstand oversættes klasse-kolonnen. Titlen bærer sit Eu,
    # fordi oversættelsen kun gælder dét Eu — se
    # data.trafikklasser_for_belastningsklasser.
    if trafik_eu is not None:
        kl_kol = (
            f'<span title="Produktets anbefalede belastningsklasser oversat til '
            f'trafikklasser ved Eu = {ui.mpa(trafik_eu)}. Hver trafikklasse '
            f'slår op i den belastningsklasse, dens Eo_ækv ligger nærmest. '
            f'Oversættelsen gælder kun dette Eu — den er ikke en egenskab ved '
            f'nettet." style="cursor:help">'
            f'Anbefalet trafikklasse (ved Eu = {trafik_eu:.0f})</span>'
        )
    else:
        kl_kol = '<span>Anbefalet belastningsklasse</span>'

    indeks_kol = (
        '<span class="num" title="Produktets effektivitet i forhold til '
        'designmanualernes referencenet, som har indeks 100." '
        'style="cursor:help">Indeks</span>'
        if grupperet else ""
    )
    kor_kol = (
        '<span class="num">Basisreduktion</span>'
        '<span class="num">Net-korr.</span>'
        '<span class="num">φ-korr.</span>'
    )
    hoved_css = "rt-head"
    if grupperet:
        hoved_css += " rt-head-indeks"
    hoved_css += " rt-med-kor"
    dele = ['<div class="rt-tabel">']
    dele.append(
        f'<div class="{hoved_css}">'
        '<span>Produkt</span>'
        f'{indeks_kol}'
        f'{kl_kol}'
        f'{kor_kol}'
        '<span class="num">Bærelagstykkelse, 1 lag geonet</span>'
        '<span class="num">Reduktion i alt, 1 lag</span>'
        '<span class="num">Bærelagstykkelse, 2 lag geonet</span>'
        '<span class="num">Reduktion i alt, 2 lag</span>'
        '</div>'
    )
    if vis_reference:
        if grupperet:
            dele.append('<div class="rt-gruppe">Reference</div>')
        dele.append(
            _rt_raekke_html(REFERENCE_NAVN_TABEL, refp1, refp2, is_ref=True,
                            phi=phi, trafik_eu=trafik_eu, eu=eu,
                            vis_indeks=grupperet,
                            udfoldet=udfoldet_navn == REFERENCE_NAVN_TABEL)
        )

    if grupperet:
        # Produkterne samles efter serie i håndbogsrækkefølgen, jf.
        # SERIE_ORDER, og inden for hver serie efter faldende effektindeks.
        navne = sorted(
            navne,
            key=lambda n: (
                SERIE_ORDER.get(
                    (p1_by.get(n) or p2_by.get(n) or {}).get("serie", ""), 99
                ),
                -_indeks_tal(n),
                n,
            ),
        )

    sidste_serie: str | None = None
    for n in navne:
        p1 = p1_by.get(n)
        p2 = p2_by.get(n)
        if not (_rt_gyldig(p1) or _rt_gyldig(p2)):
            continue
        if grupperet:
            serie = (p1 or p2 or {}).get("serie") or "Øvrige"
            if serie != sidste_serie:
                sidste_serie = serie
                dele.append(f'<div class="rt-gruppe">{html.escape(serie)}</div>')
        dele.append(_rt_raekke_html(n, p1, p2, phi=phi, trafik_eu=trafik_eu,
                                    eu=eu, vis_indeks=grupperet,
                                    udfoldet=udfoldet_navn == n))
    dele.append('</div>')
    if grupperet:
        caption = (
            "Produkterne er samlet efter serie og ordnet efter faldende "
            "effektindeks. Indeks 100 svarer til designmanualernes "
            "referencenet; et højere indeks angiver et net, der giver en "
            "tyndere opbygning. Klik på en række for krav til udførelse"
        )
    elif vis_reference:
        caption = (
            "Referencenet vises øverst, derefter de mest effektive produkter "
            "først. Klik på hver række for flere detaljer"
        )
    else:
        caption = "Klik på rækken for flere detaljer"
    dele.append(f'<div class="rt-caption">{caption}</div>')
    st.markdown("".join(dele), unsafe_allow_html=True)


def _indeks_ender(navn: str) -> tuple[str, str] | None:
    """Effektindeksets to ender for produkter med korrektionsinterval.

    Indekset er tabuleret som et spænd, eksempelvis "115–130", hvor den nedre
    ende svarer til den konservative korrektion og den øvre til den optimale.
    Returnerer (konservativ, optimal); None for produkter med ét indeks.
    """
    raa = str((find_geonet(navn) or {}).get("effektindeks") or "")
    dele = [d.strip() for d in re.split(r"[–—-]", raa) if d.strip()]
    return (dele[0], dele[1]) if len(dele) == 2 else None


def _optimal_beregning(
    produkt: dict | None,
    *,
    net_navn: str,
    phi: float,
    er_reference: bool = False,
) -> dict | None:
    """Mellemregningen bag den optimale bærelagstykkelse.

    Produkterne Tensar InterAx NX750 og NX850 er tabuleret med et effektindeks
    i to ender. Beregningerne tager udgangspunkt i den nedre, konservative
    ende; her opgøres samme regnestykke ved den øvre ende:

    ```
    T_optimal = T_basis × (1 + k_net,optimal + k_φ)
    ```

    hvor:

    - **k_net,optimal** = net-korrektionen ved effektindeksets øvre ende.
    - **k_φ** = korrektion for friktionsvinklen, jf. afsnittet "Sådan dannes
      diagrammet". Den er uafhængig af nettet og indgår med samme værdi i
      begge ender.

    Returnerer None for produkter uden korrektionsinterval og for beregninger
    uden gyldigt resultat. Ellers en opslagstabel med ``linjer`` (regnestykket
    som (tegn, titel, mm)), ``t_mm`` (den optimale tykkelse), ``indeks``
    (effektindeksets øvre ende) og ``kor`` (net-korrektionen samme sted).
    """
    if er_reference or not _rt_gyldig(produkt):
        return None
    t_best = produkt.get("t_armeret_mm_min")
    kor_best = produkt.get("korrektion_min")
    t_uarm = produkt.get("t_uarmeret_mm")
    t_basis = produkt.get("t_basis_arm_mm")
    if t_best is None or kor_best is None or t_basis is None:
        return None

    ender = _indeks_ender(net_navn)
    indeks = ender[1] if ender else _effektindeks(net_navn)
    phi_kor = K_PHI * (phi - PHI_BASIS)
    basis_mm = (
        round(t_uarm - t_basis) if t_uarm is not None and t_basis is not None
        else None
    )
    net_mm = round(t_basis * kor_best)
    phi_mm = round(t_basis * phi_kor)

    linjer: list[tuple[str, str, float | None]] = [
        ("", "Ustabiliseret bærelagstykkelse", t_uarm),
        ("−", "Basisreduktion, referencenet", abs(basis_mm or 0)),
        (
            "−" if net_mm < 0 else "+",
            f"Net-korrektion, indeks {indeks}",
            abs(net_mm),
        ),
    ]
    if abs(phi_kor) > 0.0005:
        linjer.append((
            "−" if phi_mm < 0 else "+",
            f"φ-korrektion, {_pct_fortegn(phi_kor, 1)}",
            abs(phi_mm),
        ))
    return {
        "linjer": linjer,
        "t_mm": t_best,
        "indeks": indeks,
        "kor": kor_best,
    }


def _optimal_tooltip(beregning: dict) -> str:
    """Regnestykket bag den optimale tykkelse som tekst til title-attributten."""
    linjer = [
        f"{tegn} {titel}: {ui.mm(mm)}".strip()
        for tegn, titel, mm in beregning["linjer"]
    ]
    linjer.append(
        f"= Stabiliseret bærelagstykkelse: {ui.mm(beregning['t_mm'])}"
    )
    linjer.insert(
        0,
        f"Optimal korrektion · effektindeks {beregning['indeks']} · "
        f"net-korrektion {_pct_fortegn(beregning['kor'])}",
    )
    return "\n".join(linjer)


def _optimal_note(
    produkt: dict | None, *, net_navn: str | None, phi: float,
) -> str | None:
    """Mellemregningen bag den optimale tykkelse som hover-tekst i snittet.

    Returnerer None, når produktet ikke har et korrektionsinterval.
    """
    if not net_navn:
        return None
    beregning = _optimal_beregning(produkt, net_navn=net_navn, phi=phi)
    return _optimal_tooltip(beregning) if beregning else None


def _render_valgt_net_detaljer(
    produkt_1: dict | None,
    produkt_2: dict | None,
    *,
    net_navn: str,
    phi: float,
    er_reference: bool = False,
) -> None:
    """Vis det valgte nets beregning i den kompakte designvisning."""
    def _lag_html(label: str, produkt: dict | None) -> str:
        if not _rt_gyldig(produkt):
            return (
                f'<section class="rt-detaljer-lag">'
                f'<div class="rt-detaljer-lag-titel">{html.escape(label)}</div>'
                '<div class="rt-detaljer-tom">Ingen gyldig beregning.</div></section>'
            )

        t_uarm = produkt.get("t_uarmeret_mm")
        t_basis = produkt.get("t_basis_arm_mm")
        t_arm = produkt.get("t_armeret_mm")
        net_kor = 0.0 if er_reference else float(produkt.get("korrektion") or 0.0)
        phi_kor = K_PHI * (phi - PHI_BASIS)
        # Produkter med korrektionsinterval er tabuleret med et effektindeks i
        # to ender. Tabellen er regnet af den nedre, konservative ende, og
        # rækken angiver derfor denne ende alene; det fulde spænd og den
        # optimale ende fremgår af blokken nederst.
        ender = None if er_reference else _indeks_ender(net_navn)
        index = ender[0] if ender else _effektindeks(net_navn, is_ref=er_reference)
        basis_mm = -round(t_uarm - t_basis) if t_uarm is not None and t_basis is not None else None
        net_mm = round(t_basis * net_kor) if t_basis is not None else None
        phi_mm = round(t_basis * phi_kor) if t_basis is not None else None
        reduktion_mm = round(t_uarm - t_arm) if t_uarm is not None else None
        reduktion_pct = reduktion_mm / t_uarm if t_uarm else None

        def _raekke(
            tegn: str, titel: str, vaerdi: str, klasse: str = "",
            forklaring: str | None = None,
        ) -> str:
            attr = f' title="{html.escape(forklaring, quote=True)}"' if forklaring else ""
            klasser = f"rt-detaljer-raekke {klasse}".strip()
            if forklaring:
                klasser += " rt-detaljer-hjaelp"
            return (
                f'<div class="{klasser}"{attr}>'
                f'<span class="rt-detaljer-tegn">{html.escape(tegn)}</span>'
                f'<span>{html.escape(titel)}</span>'
                f'<span class="rt-detaljer-vaerdi">{html.escape(vaerdi)}</span>'
                '</div>'
            )

        phi_tekst = _pct_fortegn(phi_kor, 1)
        net_forklaring = (
            f"Effektindeks {_effektindeks(net_navn)}. Beregningen tager "
            f"udgangspunkt i den nedre, konservative ende, indeks {index}, "
            f"svarende til net-korrektionen {_pct_fortegn(net_kor)}."
        ) if ender else None
        rows = [
            _raekke("", "Ustabiliseret bærelagstykkelse", ui.mm(t_uarm)),
            _raekke("−", "Basisreduktion, referencenet", ui.mm(abs(basis_mm or 0))),
            _raekke(
                "−" if (net_mm or 0) < 0 else "+",
                f"Net-korrektion, indeks {index}",
                ui.mm(abs(net_mm or 0)),
                forklaring=net_forklaring,
            ),
        ]
        if abs(phi_kor) > 0.0005:
            rows.append(
                _raekke(
                    "−" if (phi_mm or 0) < 0 else "+",
                    f"φ-korrektion, {phi_tekst}",
                    ui.mm(abs(phi_mm or 0)),
                )
            )

        # Den optimale ende af korrektionsintervallet opgøres for sig, så det
        # fremgår, hvilken tykkelse der er tale om, og hvordan den er dannet.
        optimal = _optimal_beregning(
            produkt, net_navn=net_navn, phi=phi, er_reference=er_reference,
        )
        optimal_html = ""
        if optimal is not None:
            # Linjeskift i en title-attribut angives som tegnreference, så
            # markdown-behandlingen ikke bryder blokken op.
            tip = html.escape(_optimal_tooltip(optimal), quote=True).replace(
                "\n", "&#10;"
            )
            optimal_html = (
                f'<div class="rt-detaljer-optimal" title="{tip}">'
                '<span>Optimal korrektion, indeks '
                f'{html.escape(str(optimal["indeks"]))}</span>'
                '<span class="rt-detaljer-optimal-tal">'
                f'{html.escape(ui.mm(optimal["t_mm"]))}</span>'
                '</div>'
                '<div class="rt-detaljer-optimal-note">'
                'Der gøres opmærksom på, at regnestykket ovenfor er opgjort ved '
                f'indeks {html.escape(str(index))}. Mellemregningen bag den '
                'optimale værdi vises ved markøren.</div>'
            )

        return (
            f'<section class="rt-detaljer-lag">'
            f'<div class="rt-detaljer-lag-titel">{html.escape(label)}</div>'
            f'{"".join(rows)}'
            '<div class="rt-detaljer-resultat">'
            '<div><strong>Stabiliseret bærelagstykkelse</strong></div>'
            f'<div class="rt-detaljer-resultat-tal">{html.escape(ui.mm(t_arm))}</div>'
            '</div>'
            '<div class="rt-detaljer-samlet">Reduktion i alt '
            f'{html.escape(_delta_mm(-(reduktion_mm or 0)))} · '
            f'{html.escape(ui.procent((reduktion_pct or 0) * 100))}</div>'
            f'{optimal_html}'
            '</section>'
        )

    st.markdown(
        '<div class="rt-detaljer-grid">'
        f'{_lag_html("1 LAG GEONET", produkt_1)}'
        f'{_lag_html("2 LAG GEONET", produkt_2)}'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_alle_produkter_overblik(
    prod_1lag: list[dict],
    prod_2lag: list[dict],
    *,
    valgt_navn: str | None = None,
) -> None:
    """Vis alle produkter som en enkel, effektivitetssorteret oversigt."""
    p1_by = {p["navn"]: p for p in prod_1lag}
    p2_by = {p["navn"]: p for p in prod_2lag}
    navne = list(p1_by)
    navne.extend(n for n in p2_by if n not in p1_by)

    def _effektivitet_noegle(navn: str) -> tuple:
        p1 = p1_by.get(navn) or {}
        p2 = p2_by.get(navn) or {}
        t1 = p1.get("t_armeret_mm") if _rt_gyldig(p1) else None
        t2 = p2.get("t_armeret_mm") if _rt_gyldig(p2) else None
        return (
            t1 is None and t2 is None,
            float(t1) if t1 is not None else float("inf"),
            float(t2) if t2 is not None else float("inf"),
            -_indeks_tal(navn),
            navn,
        )

    def _tykkelse(produkt: dict | None) -> str:
        return ui.mm(produkt.get("t_armeret_mm")) if _rt_gyldig(produkt) else "—"

    def _sparet(produkt: dict | None) -> str:
        if not _rt_gyldig(produkt) or produkt.get("t_uarmeret_mm") is None:
            return "—"
        t_uarm = produkt["t_uarmeret_mm"]
        t_arm = produkt["t_armeret_mm"]
        return f"{_delta_mm(-(t_uarm - t_arm))} · {ui.procent((t_uarm - t_arm) / t_uarm * 100)}"

    rækker = []
    for navn in sorted(navne, key=_effektivitet_noegle):
        p1 = p1_by.get(navn)
        p2 = p2_by.get(navn)
        valgt = navn == valgt_navn
        valgt_p = p1 if _rt_gyldig(p1) else p2
        klasser = format_klasse_interval(valgt_p.get("klasser", [])) if valgt_p else "—"
        rækker.append(
            f'<div class="rt-alle-raekke{" rt-alle-valgt" if valgt else ""}">'
            f'<div class="rt-alle-produkt">{html.escape(navn)}</div>'
            f'<div>{html.escape(klasser)}</div>'
            f'<div class="rt-alle-num">{html.escape(_effektindeks(navn))}</div>'
            f'<div class="rt-alle-num">{html.escape(_tykkelse(p1))}</div>'
            f'<div class="rt-alle-sparet">{html.escape(_sparet(p1))}</div>'
            f'<div class="rt-alle-num">{html.escape(_tykkelse(p2))}</div>'
            f'<div class="rt-alle-sparet">{html.escape(_sparet(p2))}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="rt-alle-tabel">'
        '<div class="rt-alle-hoved">'
        '<span>Produkt</span><span>Klasse</span><span class="rt-alle-num">Indeks</span>'
        '<span class="rt-alle-num">1 lag</span><span class="rt-alle-num">Sparet</span>'
        '<span class="rt-alle-num">2 lag</span><span class="rt-alle-num">Sparet</span>'
        '</div>'
        f'{"".join(rækker)}'
        '</div>'
        '<div class="rt-caption">Produkterne er sorteret efter den tyndeste gyldige '
        'opbygning under de aktuelle forudsætninger.</div>',
        unsafe_allow_html=True,
    )


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
        dk_str = f"{ui.mm(dk_unik[0])}"
    else:
        dk_str = f"{dk_unik[0]:.0f}–{ui.mm(dk_unik[-1])} (varierer pr. produkt)"

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
        afstand_str = f"{min_afst[0]:.0f}–{ui.mm(max_afst[0])}"
    else:
        afstand_str = (
            f"{min(min_afst):.0f}–{ui.mm(max(max_afst))} "
            "(varierer pr. produkt)"
        )

    return navne, dk_str, korn_str, afstand_str


_REF_VALG = "Referencenet (TX160 / SX160 / T6)"


def _naturlig_noegle(navn: str) -> tuple:
    """Sorteringsnøgle, hvor tal i produktnavnet ordnes efter værdi.

    Navnet opdeles i skiftevis tekst og tal, så TX150 står før TX160 og
    TX190L, og B30/30 før B40/40. En ren tegnsortering ville stille
    TX1500 mellem TX150 og TX160.
    """
    dele = re.split(r"(\d+)", navn.lower())
    return tuple(int(d) if d.isdigit() else d for d in dele)


def _geonet_valgliste(gyldige: list[str]) -> tuple[list[str], int]:
    """Geonet-vælgerens produkter og standardvalgets plads i listen.

    Produkterne ordnes efter serie, jf. SERIE_ORDER, så Tensar-, GS-GRID-
    og E'GRID-nettene står samlet. Inden for serien ordnes de efter navn
    med tallene efter værdi, jf. _naturlig_noegle(), så produktfamilierne
    følges ad. Standardvalget er TX160. Er nettet ikke gyldigt for den
    valgte belastningsklasse, står valget på det første produkt i listen.

    Navne, der forekommer i både 1-lags- og 2-lags-listen, optages én gang.
    """
    def _noegle(navn: str) -> tuple:
        serie = (find_geonet(navn) or {}).get("serie", "")
        return (SERIE_ORDER.get(serie, len(SERIE_ORDER)), _naturlig_noegle(navn))

    valg = sorted(set(gyldige), key=_noegle)
    return valg, valg.index(STANDARD_GEONET) if STANDARD_GEONET in valg else 0


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
    return (_produkt_opslag(produkter, navn) or {}).get("t_armeret_mm_min")


def _produkt_opslag(produkter: list[dict] | None, navn: str) -> dict | None:
    """Produkt-dict'en for et navn i en liste fra beregn_alle_produkter."""
    for p in produkter or []:
        if p["navn"] == navn and p.get("fejl") is None:
            return p
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

    # Statusteksten formuleres som en konstatering: "311 mm for lidt" frem for
    # "Mangler 311 mm".

    # Hvis konservativ er tilstrækkelig → grøn (overskud)
    if diff_kons >= 0:
        if diff_best is not None and diff_best > diff_kons:
            return (
                f"{ui.mm(diff_kons)} i overskud\n({ui.mm(diff_best)} optimalt)",
                "success",
            )
        return f"{ui.mm(diff_kons)} i overskud", "success"

    # Hvis best-case er tilstrækkelig men konservativ ikke → orange (interval)
    if diff_best is not None and diff_best >= 0:
        return (
            f"{ui.mm(-diff_kons)} for lidt (optimalt {ui.mm(diff_best)} i overskud)",
            "warning",
        )

    # Begge mangler → rød. Konservativ stor (størst mangler), optimal i parentes.
    if diff_best is not None:
        return (
            f"{ui.mm(-diff_kons)} for lidt\n({ui.mm(-diff_best)} optimalt)",
            "danger",
        )
    return f"{ui.mm(-diff_kons)} for lidt", "danger"


def _tegn_designdiagram(
    eu: float,
    eo: float,
    phi: float,
    geonet: dict | None,
    t_basis_table: dict,
    t_indtastet_mm: float | None,
    produkt_1: dict | None,
    produkt_2: dict | None,
) -> None:
    """Tegner designdiagrammet.

    Figuren bærer selv sin signatur, og fremgangsmåden bag kurverne —
    interpolation og korrektion — står i Hjælp, kapitel 1 og 3. Der er derfor
    ingen forklaring under figuren.
    """
    try:
        fig = byg_designdiagram(
            eu=float(eu),
            eo=float(eo),
            phi=float(phi),
            geonet=geonet,
            t_indtastet_mm=t_indtastet_mm,
            t_basis_table=t_basis_table,
            t_1_lag_mm=(produkt_1 or {}).get("t_armeret_mm"),
            t_2_lag_mm=(produkt_2 or {}).get("t_armeret_mm"),
            t_1_lag_best_mm=(produkt_1 or {}).get("t_armeret_mm_min"),
            t_2_lag_best_mm=(produkt_2 or {}).get("t_armeret_mm_min"),
        )
    except Exception as exc:
        st.warning(f"Kunne ikke generere designdiagram: {exc}")
        return

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _render_opbygningsvisualisering(
    eu: float,
    ref_1: dict | None,
    ref_2: dict | None,
    prod_1lag: list[dict] | None = None,
    prod_2lag: list[dict] | None = None,
    materialer: list[dict] | None = None,
    phi: float = PHI_BASIS,
    tvunget_produkt: str | None = None,
    laas_valg: bool = False,
) -> None:
    """Tre eller fire opbygnings-snit side om side (Koncept A).

    I Brugerdefineret-tilstand (materialer != []) vises fire søjler:
    "Indtastet opbygning" + tre krav-søjler (Uarmeret/1 lag/2 lag).
    I Standard-tilstand vises de tre krav-søjler alene.

    Hvis prod_1lag/prod_2lag er givet OG tvunget_produkt er None, vises en
    dropdown der lader brugeren skifte til et hvilket som helst gyldigt
    produkt fra resultatlisten. Hvis tvunget_produkt er sat (Brugerdefineret
    → 'Vælg specifikt produkt'), bruges det navn direkte uden dropdown.

    Tegnes af core.diagram.byg_snit(), som rapporten eksporterer til PNG af —
    så snittene i dimensioneringen og i rapporten er den samme figur.
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
    if laas_valg:
        valg = tvunget_produkt or _REF_VALG
    elif tvunget_produkt is not None:
        # Brugerdefineret 'Vælg specifikt produkt': dropdown skjules, det
        # valgte produkt bruges direkte. Hvis produktet ikke er i listen
        # (fx kun gyldigt i én lag-mode) bruges det alligevel.
        valg = tvunget_produkt
    elif navne_sorteret:
        def _format_valg(navn: str) -> str:
            if navn == _REF_VALG:
                return navn
            t1 = _produkt_t(prod_1lag, navn)
            t2 = _produkt_t(prod_2lag, navn)
            t1_str = f"{ui.mm(t1)}" if t1 is not None else "—"
            t2_str = f"{ui.mm(t2)}" if t2 is not None else "—"
            return f"{navn}  ·  1 lag: {t1_str}  ·  2 lag: {t2_str}"

        dd_kol, _ = st.columns([1, 1])
        with dd_kol:
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
        note_1_best = None
        note_2_best = None
        valgt_geonet = None
        geonet_label = "Tensar TriAx 160 / GS-GRID SX160 / E'GRID T6"
    else:
        t_1 = _produkt_t(prod_1lag, valg)
        t_2 = _produkt_t(prod_2lag, valg)
        t_1_best = _produkt_t_best(prod_1lag, valg)
        t_2_best = _produkt_t_best(prod_2lag, valg)
        note_1_best = _optimal_note(
            _produkt_opslag(prod_1lag, valg), net_navn=valg, phi=phi,
        )
        note_2_best = _optimal_note(
            _produkt_opslag(prod_2lag, valg), net_navn=valg, phi=phi,
        )
        valgt_geonet = find_geonet(valg)
        geonet_label = valg

    # ── Skalering: brug t_uarm hvis defineret, ellers største armerede ─
    kandidater = [t for t in (t_uarm, t_1, t_2) if t is not None]
    if not kandidater:
        st.caption("Ingen gyldige beregninger at visualisere.")
        return

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
                f"Ustabiliseret bærelag ikke defineret for Eu = {ui.mpa(eu)}"
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
        best_case_note=note_1_best,
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
        best_case_note=note_2_best,
        placement=placement_2,
        er_krav_soejle=not brug_sub_2,
        t_indtastet_mm=t_indtastet_for_linje,
        status_tekst=status_tekst_2,
        status_farve=status_farve_2,
        phi_vaegtet=har_indtastet,
    ))

    # Forudsætningerne står i kortets sidehoved, jf. ui.kort().
    ui.snit(
        snit_til_kolonner(snit_liste, materialer, eu),
        reference_mm=t_indtastet_for_linje,
        geonet_navn=geonet_label,
    )


def _render_opbygning_afsnit(
    eu: float,
    ref_1: dict | None,
    ref_2: dict | None,
    *,
    prod_1lag: list[dict] | None = None,
    prod_2lag: list[dict] | None = None,
    materialer: list[dict] | None = None,
    phi: float = PHI_BASIS,
    geonet_navn: str | None = None,
    laas_geonetvalg: bool = False,
    som_kort: bool = False,
) -> None:
    """Opbygning som et primært resultatkort, lige efter resultatkortene."""
    if ref_1 is None and ref_2 is None:
        return
    materialer = materialer or []
    indtastet = _indtastet_total(materialer)
    note = "Snit i samme lodrette skala"
    if indtastet:
        note += f" · stiplet linje = indtastet {ui.mm(indtastet)}"
    else:
        note += " · uden materialelag vises kravet som ét ubundet lag"
    def _vis_indhold() -> None:
        _render_opbygningsvisualisering(
            eu, ref_1, ref_2,
            prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            materialer=materialer, phi=phi, tvunget_produkt=geonet_navn,
            laas_valg=laas_geonetvalg,
        )

    if som_kort:
        with ui.kort("Opbygning", note):
            _vis_indhold()
    else:
        ui.underhoved("Opbygning", note)
        _vis_indhold()


def _render_oversigt_expanders(
    eu: float,
    eo: float,
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
    eo_interpoleret: bool = False,
    vis_opbygning: bool = True,
) -> None:
    """Opbygningsafsnittet og informations-expanderne under resultaterne.

    Beregningsmetoden og datagrundlaget står i Hjælp og gentages ikke her;
    expanderne rummer alene advarsler og udførelseskrav for det valgte net.

    Bruges af både Standard (phi=37, geonet=None, materialer=None)
    og Brugerdefineret (egne phi/geonet/materialer-værdier).

    bedste_1 / bedste_2: bedste (mindste t_armeret) gruppe i hver lag-mode,
    eller None hvis ingen er gyldige. I "Vælg specifikt produkt"-mode er
    bedste-gruppen den enkelte produkts resultat pakket via
    _resultat_til_gruppe().
    """
    materialer = materialer or []

    # --- Opbygningsvisualisering (referencenet eller valgt produkt) -----
    if vis_opbygning:
        _render_opbygning_afsnit(
            eu, ref_1, ref_2,
            prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            materialer=materialer, phi=phi, geonet_navn=geonet_navn,
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
    # I 'Vælg specifikt produkt' vises ingen dropdown, og
    # opbygning_geonet_valg opdateres derfor ikke — den ville pege på
    # referencenettet og give placeringsadvarsler for det forkerte net.
    # geonet_navn er det produkt, snittegningen faktisk viser.
    valgt_opbygning = geonet_navn or st.session_state.get(
        "opbygning_geonet_valg", _REF_VALG
    )

    def _placeringsadvarsler_for_valgt_opbygning(lag_mode: str) -> list[tuple[str, str]]:
        # Placeringen evalueres i krav-tykkelsen med SAMME lag-baserede
        # placering som snittegningen: med ≥2 materialelag lægges det øverste
        # net i materialeskiftet (materialerne skaleret til krav-tykkelsen),
        # ellers falder vi tilbage på minimumsdæklag-reglen (sub_lag=None).
        # Det holder afstands-advarslen i sync med det, tegningen faktisk viser
        # (uden lag-baseret placering blev afstanden regnet fra minimumsdæklaget
        # og gav en falsk >max-afstand-advarsel).
        def _sub_for(total_mm: float) -> list[dict] | None:
            skaleret = _sub_lag_skaleret_fra_materialer(materialer, total_mm)
            return skaleret if len(skaleret) >= 2 else None

        if valgt_opbygning == _REF_VALG:
            ref = ref_1 if lag_mode == "1_lag" else ref_2
            if ref is None or ref.get("t_armeret_mm") is None:
                return []
            t_ref = ref["t_armeret_mm"]
            placement = check_geonet_placement(
                lag_mode=lag_mode,
                total_mm=t_ref,
                geonet=None,
                sub_lag=_sub_for(t_ref),
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
                sub_lag=_sub_for(t),
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
            tillad_interpoleret_eo=eo_interpoleret,
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
                f"Den samlede foreslåede opbygning ({ui.mm(total_opbygning)}) er "
                f"mindre end minimumtykkelsen ved 1 lag geonet ({ui.mm(t_min_1)}), "
                f"men tilstrækkelig ved 2 lag geonet ({ui.mm(t_min_2)}). "
                f"Anvend 2 lag geonet for denne opbygning."
            )
        elif t_min_1 is not None and t_min_2 is not None:
            # Utilstrækkelig ved både 1 og 2 lag
            opbyg_adv = (
                f"Den samlede foreslåede opbygning ({ui.mm(total_opbygning)}) er "
                f"mindre end den beregnede minimumtykkelse ved både 1 lag "
                f"({ui.mm(t_min_1)}) og 2 lag geonet ({ui.mm(t_min_2)}). "
                f"Øg den samlede materialetykkelse, eller anvend materialer med "
                f"højere friktionsvinkel."
            )
        else:
            # Kun ét lag-mode er gyldigt for kombinationen
            t_kendt = t_min_1 if t_min_1 is not None else t_min_2
            lag_txt = "1 lag" if t_min_1 is not None else "2 lag"
            opbyg_adv = (
                f"Den samlede foreslåede opbygning ({ui.mm(total_opbygning)}) er "
                f"mindre end minimumtykkelsen ved {lag_txt} geonet "
                f"({ui.mm(t_kendt)}). Øg den samlede materialetykkelse, eller "
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
        t_1_str = f"<b>{ui.mm(bedste_1['t_armeret_mm'])}</b>"
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
            t_2_str = f"<b>{ui.mm(bedste_2['t_armeret_mm'])}</b>"
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
            f"<b>{ui.mm(bedste_2['t_armeret_mm'])}</b>. "
            f"1 lag geonet er sandsynligvis tilstrækkeligt for denne belastning"
        )
        if bedste_1 is not None:
            msg += f" (1 lag giver <b>{ui.mm(bedste_1['t_armeret_mm'])}</b>)."
        else:
            msg += "."
        anbefalinger.append(msg)

    antal = len(advarsler_unik) + len(anbefalinger)
    titel_adv = (
        f"Advarsler og anbefalinger ({antal})"
        if antal else "Advarsler og anbefalinger"
    )
    # Advarsler og udførelseskrav er konklusioner og bliver liggende
    # sammenfoldede. Antallet står i overskriften, så det fremgår, at der er
    # noget at læse.
    with st.expander(titel_adv):
        if antal == 0:
            st.caption(
                "Ingen generelle advarsler for den valgte Eu og belastning."
            )
        for a in advarsler_unik:
            vis_advarsel(a)
        for r in anbefalinger:
            vis_anbefaling(r)

    # --- Udførelseskrav ---------------------------------------------------
    with st.expander("Udførelseskrav"):
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
                f"{ui.mm(krav['max_spacing_mm'])}"
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
            pct_str = ui.procent(red_pct * 100)
            red_html = (
                f'<span style="color:{GRØN};font-size:0.85em;margin-left:10px">'
                f'Reduceres {ui.mm(red_mm)} fra ustabiliseret ({pct_str})'
                f'</span>'
            )
        result_html = (
            f'<div style="border-top:1px solid #C8E6C9;margin-top:6px;'
            f'padding-top:6px;display:flex;align-items:baseline;gap:6px">'
            f'<span style="font-size:1.25rem;font-weight:700;color:{GRØN}">'
            f'= {ui.mm(t_final)}</span>'
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
        reduktion_txt = (
            f" (reduceres {ui.mm(red_mm)} fra ustabiliseret, "
            f"{ui.procent(red_pct * 100)})"
        )
    else:
        reduktion_txt = ""
    st.markdown(
        f'<div style="font-size:0.85rem;color:#444;'
        f'padding:4px 10px 0 10px;margin-top:-6px">'
        f'Best case (effektindeks i øvre ende, net-kor {kor_pct} %): '
        f'<b>{ui.mm(t_best)}</b>{reduktion_txt} — '
        f'interval: <b>{t_best:.0f}–{ui.mm(t_konservativ)}</b>'
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
        st.markdown("**Beregnings-breakdown**")

        # ── Uarmeret ──────────────────────────────────────────────────
        st.markdown("**Ustabiliseret bærelagstykkelse**")
        if not ref_uarm.get("fejl") and ref_uarm.get("t_basis_uarm_mm") is not None:
            t_b_u = ref_uarm["t_basis_uarm_mm"]
            phi_kor_mm_u = t_b_u * phi_kor
            rows_u: list[tuple[str, str, str]] = [
                ("T_basis (opslag)", f"{ui.mm(t_b_u)}", ""),
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
                    ("T_basis_stabiliseret (opslag)", f"{ui.mm(t_b_1)}", ""),
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
                    ("T_basis_stabiliseret (opslag)", f"{ui.mm(t_b_2)}", ""),
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
            st.caption(note)


# ===========================================================================
# To-kolonne-layout: fælles byggeklodser
# ===========================================================================

@st.cache_data(show_spinner=False)
def _beregn_produkter_cachet(
    eu: float,
    eo: float,
    lag_mode: str,
    phi: float,
    valgt_klasse: int | None,
    t_basis_table: dict,
) -> list[dict]:
    """Cachet indpakning af beregn_alle_produkter.

    Streamlit gentegner hele siden ved hver ændring. Uden cache genberegnes
    samtlige produkter, hver gang en skyder flyttes, og resultatpanelet
    blinker. Nøglen er de seks argumenter alene; funktionen læser ikke
    st.session_state, jf. afsnit 5.

    Der returneres en kopi ved hvert opslag, så kalderen frit kan berige
    produkterne med placeringsdata uden at forurene cachen.
    """
    return beregn_alle_produkter(
        eu, eo, lag_mode, phi=phi, t_basis_table=t_basis_table,
        klasse_for_anbefaling=valgt_klasse,
    )


def _tilstand_vaelger() -> str:
    """Valget mellem Standard og Brugerdefineret, øverst i inputkolonnen."""
    return st.segmented_control(
        "Tilstand",
        ["Standard", "Brugerdefineret"],
        default="Standard",
        key="tilstand",
        label_visibility="collapsed",
        width="stretch",
        help=(
            "**Standard:** Vælg Eu/Cv og belastningsklasse — få en oversigt over "
            "alle geonet-produkter med deres opnåelige bærelagstykkelse.  \n"
            "**Brugerdefineret:** Få en oversigt over alle produkter, eller vælg "
            "ét produkt med op til 3 materialelag, med beregning af vægtet "
            "friktionsvinkel"
        ),
    ) or "Standard"


def _faste_forudsaetninger() -> None:
    """De forudsætninger, standardtilstanden holder fast, jf. afsnit 10.

    Forudsætningerne fremgår ikke af inputfelterne og gøres derfor eksplicitte,
    så forskellen til Brugerdefineret kan aflæses direkte.
    """
    ui.etiket("Faste forudsætninger")
    st.markdown(
        "I standardberegningen forudsættes 1 samlet bærelag, med en "
        f"friktionsvinkel φ = {PHI_BASIS:g}°. Der kan derfor ikke "
        "vælges forskellige materialelag. Reduktion i bærelagstykkelser "
        "korrigeres for de forskellige geonets effektindeks, som er "
        "virkningsgraden set i forhold til referencenettene, med indeks 100."
    )


def _input_trin1(key_prefix: str) -> tuple[float, dict]:
    """Trin 1: underbundens styrke og dimensioneringsgrundlaget.

    De to valg står side om side, og trinnets nøgletal i en tredje kolonne,
    jf. designgennemgangens flow A. Returnerer (Eu, grundlag).
    """
    kol_eu, kol_grundlag, kol_tal = st.columns([1, 1, 1.1], gap="medium")

    with kol_eu:
        ui.etiket("Underbundens styrke")
        eu = input_underbund(key_prefix=key_prefix, kompakt=True, uden_etiket=True)

    with kol_grundlag:
        ui.etiket("Dimensioneringsgrundlag")
        grundlag = input_grundlag(
            key_prefix=key_prefix, eu=eu, kompakt=True, uden_etiket=True,
        )

    with kol_tal:
        _trin1_noegletal(grundlag, eu)

    return eu, grundlag


def _trin1_noegletal(grundlag: dict, eu: float) -> None:
    """Nøgletallene for det valgte grundlag, i trin 1's tredje kolonne.

    Betegnelserne er afkortet til kolonnens bredde, og den typiske anvendelse
    står i boksens hoved frem for som egen række, jf. designgennemgangen.
    Nøgletallene vises alene her; de gentages ikke under vælgeren.
    """
    if grundlag["type"] == "trafikklasse":
        t_klasse = grundlag["t_klasse"]
        tal = dict(trafikklasse_noegletal(t_klasse))
        raekker = [
            ("Tunge køretøjer pr. døgn, begge retninger",
             tal.get("Tunge køretøjer pr. døgn, begge retninger", "—")
             .replace(" til ", "–")),
            ("Dimensionerende trafikbelastning",
             tal.get("Dimensionsgivende trafikbelastning", "—")
             .replace(" pr. år pr. vognbane", "/år")),
            ("Svarende til 20 år", tal.get("Svarende til 20 år", "—")),
        ]
        if grundlag.get("eo_aekv") is not None:
            raekker.append(
                (f"Ækvivalent Eo-kurve ved Eu = {ui.mpa(eu)}",
                 ui.mpa(grundlag["eo_aekv"]))
            )
        titel = format_trafikklasse(t_klasse)
        # Den typiske anvendelse er vejledende og indgår ikke i håndbogen;
        # den står derfor dæmpet i hovedet frem for blandt nøgletallene.
        hoved_note = tal.get("Typisk anvendelse", "")
    else:
        info = grundlag["info"]
        raekker = [
            ("Belastning", str(info.get("belastning", "—"))),
            ("Eo-kurve", ui.mpa(grundlag["eo"])),
        ]
        titel = f"Klasse {grundlag['valgt_klasse']}"
        hoved_note = str(info.get("anvendelse", ""))

    st.markdown(
        f'<div class="bg-noegletal">'
        f'<div class="bg-noegletal-hoved">'
        f'<span class="t">{html.escape(titel)}</span>'
        f'<span class="n">{html.escape(hoved_note)}</span></div>'
        + _noegletal_tabel_html(raekker, dæmpet=True)
        + '</div>',
        unsafe_allow_html=True,
    )


def _trin1_opsummering(eu: float, grundlag: dict) -> str:
    """Trin 1's opsummering: de valgte forudsætninger på én linje."""
    dele = [f"Eu {eu:.0f} MPa"]
    if grundlag["type"] == "trafikklasse":
        dele.append(str(grundlag["t_klasse"]))
        if grundlag.get("eo_aekv") is not None:
            dele.append(f"Eo,ækv {grundlag['eo_aekv']:.0f} MPa")
    else:
        dele.append(f"Klasse {grundlag['valgt_klasse']}")
        dele.append(f"Eo {grundlag['eo']:.0f} MPa")
    return " · ".join(dele)


def _grundlag_tekst(grundlag: dict) -> str:
    """Grundlaget som en kort tekst til resultatafsnittets sidehoved."""
    if grundlag["type"] == "trafikklasse":
        return f"trafikklasse {grundlag['t_klasse']}"
    return f"belastningsklasse {grundlag['valgt_klasse']}"


def _produkttabel_note(eu: float) -> str:
    """Produkttabellens undertekst med adgang til beregningsdetaljerne."""
    return "Klik en række for reduktionsopdeling og udførelseskrav"


def _vaelg_geonet_note(grundlag: dict) -> str:
    """Noten ved »Vælg geonet« i resultatblokken.

    Ved dimensionering efter trafikklasse hviler grundlaget på VejDim-kørsler,
    hvis underbund er forudsat frostsikker. Forbeholdet om koblingshøjden
    angives derfor sammen med resultatet; ved belastningsklasse forekommer
    kørslerne ikke, og linjen udelades.
    """
    note = "Resultat, opbygning og mellemregninger opdateres med det valgte net"
    if grundlag.get("type") == "trafikklasse":
        note += (
            '<span class="bg-underhoved-forbehold">Beregningen tager ikke '
            "højde for minimumskrav til koblingshøjde pga frostfarlighed, "
            "jf. Vejdirektoratets dimensioneringshåndbog</span>"
        )
    return note


def _resultat_note(eu: float, grundlag: dict) -> str:
    """Forudsætningerne bag resultatet, til resultatblokkens sidehoved."""
    return (
        f"Bærelagstykkelse over underbund med Eu = {ui.mpa(eu)}, "
        f"{_grundlag_tekst(grundlag)}"
    )


def _indtastet_total(materialer: list[dict] | None) -> float | None:
    """Den indtastede opbygnings samlede tykkelse, eller None uden materialelag."""
    if not materialer:
        return None
    total = sum(float(m.get("tykkelse_mm") or 0) for m in materialer)
    return total or None


def _note_uarmeret(eo_interpoleret: bool, phi: float) -> str:
    """Undertekst til den ustabiliserede tykkelse: hvordan værdien er fremkommet."""
    dele = ["Ustabiliseret opbygning"]
    if eo_interpoleret:
        dele.append("interpoleret")
    if abs(phi - PHI_BASIS) > 0.05:
        dele.append("φ-korrigeret")
    return " · ".join(dele)


def _vis_resultatkort(
    t_uarm: float | None,
    t_1: float | None,
    t_2: float | None,
    *,
    standard: bool,
    note_uarm: str,
    navne_1: str = "",
    navne_2: str = "",
    indtastet_total: float | None = None,
) -> None:
    """Resultatrækken: ustabiliseret tykkelse og de to armerede alternativer.

    Reduktionen måles mod den rå ustabiliserede tykkelse, som produkttabellens
    kolonne 'Reduktion i alt' gør det, så de to opgørelser ikke kan divergere.

    Det tyndeste alternativ fremhæves. I brugerdefineret tilstand fremhæves
    alene et alternativ, som den indtastede opbygning holder til; holder ingen
    af dem, fremhæves intet, og årsagen fremgår af advarselsafsnittet.
    """
    if t_uarm is None:
        return

    def _kort(etiket: str, t: float | None, navne: str) -> dict | None:
        if t is None:
            return None
        red_mm = t_uarm - t
        kort = {
            "etiket": etiket,
            "vaerdi": ui.mm(t).replace(" mm", ""),
            "delta": f"{ui.fortegn(t - t_uarm)} mm",
            "delta_note": f"{ui.procent(red_mm / t_uarm * 100)} tyndere",
        }
        if navne:
            kort["delta_note"] += f" · {navne}"
        return kort

    kort_1 = _kort("Bedste med 1 lag" if standard else "1 lag geonet", t_1, navne_1)
    kort_2 = _kort("Bedste med 2 lag" if standard else "2 lag geonet", t_2, navne_2)

    # Det tyndeste alternativ, opbygningen holder til. Uden indtastet opbygning
    # er der intet krav at holde mod, og det tyndeste alternativ fremhæves.
    def _holder(t: float | None) -> bool:
        if t is None:
            return False
        if indtastet_total is None:
            return True
        return indtastet_total >= t

    if kort_2 and _holder(t_2):
        kort_2["anbefalet"] = True
        if indtastet_total is not None:
            kort_2["delta_note"] += f" · holder ved {ui.mm(indtastet_total)}"
    elif kort_1 and _holder(t_1):
        kort_1["anbefalet"] = True
        if indtastet_total is not None:
            kort_1["delta_note"] += f" · holder ved {ui.mm(indtastet_total)}"

    kort = [{
        "etiket": "Uden geonet" if standard else "Nødvendig uden geonet",
        "vaerdi": ui.mm(t_uarm).replace(" mm", ""),
        "note": note_uarm,
    }]
    kort += [k for k in (kort_1, kort_2) if k]

    ui.resultatkort(kort, badge_tekst="TYNDEST" if standard else "ANBEFALET")


def render_standard() -> None:
    """Standard-tilstand: produktoversigt for alle geonet på én gang.

    Flow A: dimensioneringen føres igennem som nummererede trin på én side,
    og resultatet står som en samlet blok nedenunder. Standardtilstanden har
    hverken materialelag eller produktvalg og bruger derfor ét trin.
    """

    with ui.trin_kort(1, "Underbund og dimensioneringsgrundlag") as trin1:
        eu, grundlag = _input_trin1("std")
        trin1.opsummering = _trin1_opsummering(eu, grundlag)

    with ui.trin_kort(2, "Forudsætninger") as trin2:
        _faste_forudsaetninger()
        trin2.opsummering = (
            f"φ {ui.grader(PHI_BASIS)} · ingen φ-korrektion"
        )

    eo = grundlag["eo"]
    valgt_klasse = grundlag["valgt_klasse"]
    eo_interpoleret = grundlag["type"] == "trafikklasse"

    # Trafikklasse uden for kernezonen: zone-beskeden er allerede vist i
    # trin 1 — der er intet driftspunkt at dimensionere efter.
    if grundlag["type"] == "trafikklasse" and grundlag["zone"] != "ok":
        return

    # --- Beregn alt -----------------------------------------------------
    t_basis_table = _aktiv_t_basis_table()
    ref_1, ref_2, ref_fejl_1, ref_fejl_2 = _beregn_referencegrupper(
        eu, eo, PHI_BASIS, valgt_klasse, t_basis_table
    )
    prod_1lag = _beregn_produkter_cachet(
        eu, eo, "1_lag", PHI_BASIS, valgt_klasse, t_basis_table
    )
    prod_2lag = _beregn_produkter_cachet(
        eu, eo, "2_lag", PHI_BASIS, valgt_klasse, t_basis_table
    )

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

    # Rækkefølgen i vælgeren fastlægges af _geonet_valgliste().
    gyldige_geonet = [
        p["navn"]
        for p in prod_1lag + prod_2lag
        if p.get("navn") != "Anden armering (manuel)"
        and p.get("fejl") is None
        and p.get("t_armeret_mm") is not None
    ]
    if not gyldige_geonet and not haard_fejl:
        haard_fejl = (
            "Der forekommer ikke et geonet, som kan dimensioneres for "
            f"Eu = {ui.mpa(eu)} og det valgte grundlag."
        )

    # --- Resultater -----------------------------------------------------
    vis_kobling = False
    with ui.resultat_blok(_resultat_note(eu, grundlag)):
        if haard_fejl:
            vis_fejl(haard_fejl)
        else:
            resultat_geonet_valg, std_index = _geonet_valgliste(gyldige_geonet)
            if st.session_state.get("std_geonet") not in resultat_geonet_valg:
                st.session_state.pop("std_geonet", None)

            ui.underhoved(
                "Vælg geonet",
                _vaelg_geonet_note(grundlag),
            )
            vaelger_kol, _ = st.columns([1, 1.6])
            with vaelger_kol:
                valgt_net = st.selectbox(
                    "Produkt",
                    resultat_geonet_valg,
                    index=std_index,
                    key="std_geonet",
                    format_func=_produkt_label,
                    label_visibility="collapsed",
                )

            valgt_geonet = find_geonet(valgt_net)
            valgt_1 = next(
                (p for p in prod_1lag if p.get("navn") == valgt_net), None
            )
            valgt_2 = next(
                (p for p in prod_2lag if p.get("navn") == valgt_net), None
            )

            if t_uarm is not None:
                _vis_resultatkort(
                    t_uarm,
                    valgt_1.get("t_armeret_mm") if valgt_1 else None,
                    valgt_2.get("t_armeret_mm") if valgt_2 else None,
                    standard=False,
                    note_uarm=(
                        "Ubunden opbygning · interpoleret mellem Eo-kurverne"
                        if eo_interpoleret else "Ubunden opbygning"
                    ),
                )
            else:
                _render_uarmeret_mangler_besked(eu, eo)

            _render_opbygning_afsnit(
                eu, ref_1, ref_2,
                prod_1lag=prod_1lag, prod_2lag=prod_2lag,
                materialer=[], phi=PHI_BASIS,
                geonet_navn=valgt_net, laas_geonetvalg=True, som_kort=True,
            )

            with ui.kort(
                f"Detaljer · {valgt_net}",
                "Mellemregninger for det valgte net",
            ):
                _render_valgt_net_detaljer(
                    valgt_1,
                    valgt_2,
                    net_navn=valgt_net,
                    phi=PHI_BASIS,
                )
                ui.underhoved(
                    "Designdiagram",
                    f"Eo = {ui.mpa(eo)} · {_grundlag_tekst(grundlag)} · "
                    f"{valgt_net}",
                    skillelinje=True,
                )
                _tegn_designdiagram(
                    eu, eo, PHI_BASIS, valgt_geonet, t_basis_table,
                    None, valgt_1, valgt_2,
                )

            vis_kobling = eo_interpoleret

            with ui.kort("Alle produkter", _produkttabel_note(eu)):
                _render_alle_produkter_overblik(
                    prod_1lag,
                    prod_2lag,
                    valgt_navn=valgt_net,
                )

    if vis_kobling:
        _render_trafik_kobling_forklaring(
            grundlag["t_klasse"], eu, grundlag["eo_aekv"], PHI_BASIS,
            ref_1, ref_2, t_basis_table,
        )

    # --- Informations-expandere ----------------------------------------
    _render_oversigt_expanders(
        eu, eo, bedste_1, bedste_2,
        ref_1=ref_1, ref_2=ref_2,
        prod_1lag=prod_1lag, prod_2lag=prod_2lag,
        t_basis_table=t_basis_table,
        eo_interpoleret=eo_interpoleret,
        vis_opbygning=False,
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


def _pct_fortegn(v: float, decimaler: int = 0) -> str:
    """Korrektionsfaktor som procent med fortegn: 0,10 → '+10 %', −0,10 → '−10 %'.

    ui.procent() angiver ingen fortegn og anvendes til rene procentangivelser;
    net-korrektionen aflæses derimod som en signeret størrelse.

    φ-korrektionen er lille og angives med én decimal, så en ændring af
    friktionsvinklen kan aflæses i tallet.
    """
    return (
        f"{v * 100:+.{decimaler}f} %".replace("-", "−").replace(".", ",")
    )


def _tusind(v: float) -> str:
    """Heltal med tusindtalspunktum: 26800 → '26.800'."""
    return f"{v:,.0f}".replace(",", ".")


def _delta_mm(v: float) -> str:
    """Difference i mm med fortegn og typografisk minus: '−375 mm', '+49 mm'.

    ui.fortegn() angiver intet plus. I reduktionsopdelingen er fortegnet
    meningsbærende, idet net-korrektionen kan både spare og koste tykkelse.
    """
    return f"{v:+,.0f} mm".replace(",", ".").replace("-", "−")


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
) -> None:
    """Opsummeringsboks under lag-inputs: tabel, formel, φ-korrektion, mm-ækvivalent.

    Boksen viser mellemregningen bag den vægtede φ.
    """
    data = _phi_tabel_data(materialer)
    phi_weighted = data["phi_weighted"]
    overskrevet = abs(phi_final - phi_weighted) > 0.005

    phi_w_str = _dk_num(phi_weighted, ".2f")
    phi_f_str = _dk_num(phi_final, ".2f")
    bidrag_str = _dk_num(data["total_bidrag"], ".0f")
    v_str = _dk_num(data["total_v"], ".0f")

    phi_kor = K_PHI * (phi_final - PHI_BASIS)
    phi_kor_str = _dk_num(phi_kor, "+.4f")
    phi_kor_pct_str = _dk_num(phi_kor * 100, "+.2f")

    boks_kol, _ = st.columns([1, 1])
    with boks_kol, st.container(border=True):
        st.markdown("**φ-beregning fra materialelagene**")
        st.markdown(data["tabel_md"])
        st.markdown(
            f"**Vægtet φ** = Σ({data['symbol']}ᵢ × φᵢ) / Σ({data['symbol']}ᵢ) = "
            f"{bidrag_str} / {v_str} = **{phi_w_str}°**"
        )

        if overskrevet:
            st.markdown(
                f"φ overskrevet manuelt — bruger **{phi_f_str}°** "
                f"i resten af beregningen (vægtet værdi {phi_w_str}° ignoreres)."
            )

        k_phi_str = _dk_num(K_PHI, ".2f")
        phi_basis_str = f"{PHI_BASIS:g}"
        st.markdown(
            f"**φ-korrektion** = {k_phi_str} × (φ − {phi_basis_str}°) = "
            f"{k_phi_str} × ({phi_f_str} − {phi_basis_str}) = **{phi_kor_str}** "
            f"({phi_kor_pct_str} % af basistykkelsen)"
        )




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


def _input_materialelag(kompakt: bool = False) -> tuple[list[dict], float]:
    """Materialelagene som tabel, jf. designgennemgangens trin 2.

    Lagene opstilles med nummer, materiale, tykkelse og friktionsvinkel i
    kolonner, afsluttet af en samlet-række. Returnerer (materialer-liste,
    beregnet eller overskrevet φ).

    kompakt bevares i signaturen af hensyn til kaldere uden for flow A.
    """
    etiket_kol, antal_kol = st.columns([3, 1], vertical_alignment="bottom")
    with etiket_kol:
        ui.etiket("Materialelag")
    with antal_kol:
        antal_lag = st.number_input(
            "Antal lag", min_value=1, max_value=3, value=2, step=1,
            key="bd_antal_lag", label_visibility="collapsed",
            help="Antal materialelag i opbygningen.",
        )

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

    # Bidraget t x phi er mellemregningen bag den vægtede φ.
    BREDDER = [0.35, 3.2, 1.5, 0.9, 1.0]
    st.html(
        '<div class="bg-lagtabel-hoved med-bidrag">'
        '<span>#</span><span>Materiale</span>'
        '<span class="num">Tykkelse</span><span class="num">&#966;</span>'
        '<span class="num">t&#215;&#966;</span>'
        + '</div>'
    )

    materialer: list[dict] = []
    dynamiske_navne = [
        m["navn"] for m in st.session_state.get("materialer", [])
    ]
    materiale_options = dynamiske_navne + ["Manuel indtastning"]

    for i in range(int(antal_lag)):
        mat_key = f"bd_mat_{i}"
        slettet_materiale = None
        if (
            mat_key in st.session_state
            and st.session_state[mat_key] not in materiale_options
        ):
            slettet_materiale = st.session_state[mat_key]
            st.session_state[mat_key] = "Manuel indtastning"

        kolonner = st.columns(BREDDER, vertical_alignment="center")
        kol_nr, kol_mat, kol_t, kol_phi = kolonner[:4]
        kol_bidrag = kolonner[4]
        with kol_nr:
            st.html(f'<div class="bg-lagtabel-nr">{i + 1}</div>')
        with kol_mat:
            mat_navn = st.selectbox(
                "Materiale", materiale_options, key=mat_key,
                label_visibility="collapsed",
            )

        md = (
            None
            if mat_navn == "Manuel indtastning"
            else _find_materiale_session(mat_navn)
        )

        t_key = f"bd_t_{i}"
        if (
            t_key in st.session_state
            and st.session_state[t_key] < MIN_LAGTYKKELSE_MM
        ):
            st.session_state[t_key] = MIN_LAGTYKKELSE_MM
        with kol_t:
            t_i = st.number_input(
                "Tykkelse (mm)",
                min_value=MIN_LAGTYKKELSE_MM,
                max_value=2000,
                step=50,
                key=t_key,
                label_visibility="collapsed",
            )

        if md is None:
            # Manuel indtastning: φ, kornstørrelse og lagtype angives selv og
            # får en egen linje, da de ikke er plads til i tabellens kolonner.
            with kol_phi:
                phi_i = st.number_input(
                    "φ (°)", 20.0, 60.0, PHI_BASIS, 0.5, key=f"bd_phi_m_{i}",
                    label_visibility="collapsed",
                )
            _, kol_korn, kol_type = st.columns(
                [0.35, 3.2, 2.4], vertical_alignment="center",
            )
            with kol_korn:
                korn_i = st.number_input(
                    "Max kornstørrelse (mm)", 0, 500, 32, key=f"bd_korn_m_{i}",
                )
            with kol_type:
                ltype_i = st.selectbox(
                    "Lagtype", ["Bærelag", "Bundsikring"], key=f"bd_lt_m_{i}",
                )
            krav_maske_i = None
            lag_navn = "Manuel indtastning"
        else:
            phi_i = float(md["phi"])
            korn_i = md["max_korn"]
            ltype_i = md["lagtype"]
            krav_maske_i = md.get("krav_maskestoerrelse_mm")
            lag_navn = mat_navn
            with kol_phi:
                st.html(
                    f'<div class="bg-lagtabel-phi">{ui.grader(phi_i)}</div>'
                )
            krav_txt = (
                f" · krav til geonet maskestørrelse {krav_maske_i} mm"
                if krav_maske_i is not None else ""
            )
            st.html(
                f'<div class="bg-lagtabel-note">{ltype_i} · maks. korn '
                f'{korn_i} mm{krav_txt}</div>'
            )

        if slettet_materiale is not None:
            st.warning(
                f"Materialet '{slettet_materiale}' findes ikke længere i "
                "databasen. Laget er skiftet til manuel indtastning."
            )
        elif mat_navn != "Manuel indtastning" and md is None:
            st.warning(
                f"Materialet '{mat_navn}' findes ikke længere i databasen. "
                "Laget behandles som manuel indtastning."
            )

        with kol_bidrag:
            st.html(
                f'<div class="bg-lagtabel-bidrag">'
                f'{_tusind(float(t_i) * phi_i)}</div>'
            )

        materialer.append({
            "navn": lag_navn, "phi": phi_i, "max_korn": korn_i,
            "lagtype": ltype_i, "tykkelse_mm": float(t_i),
            "pct": None,
            "krav_maskestoerrelse_mm": krav_maske_i,
        })

    phi_weighted = _phi_tabel_data(materialer)["phi_weighted"]
    total_t = sum(m["tykkelse_mm"] for m in materialer)

    bidrag_sum = sum(m["tykkelse_mm"] * m["phi"] for m in materialer)
    st.html(
        '<div class="bg-lagtabel-sum med-bidrag">'
        f'<span></span><span>Samlet</span>'
        f'<span class="num">{ui.mm(total_t)}</span>'
        f'<span class="num">{ui.grader(phi_weighted)}</span>'
        f'<span class="num">{_tusind(bidrag_sum)}</span>'
        + '</div>'
    )
    st.caption(
        f"Mindste lagtykkelse der kan indtastes er {MIN_LAGTYKKELSE_MM} mm. "
        f"Der gøres opmærksom på, at φ er vægtet efter lagtykkelse."
    )

    if st.checkbox("Overskriv φ manuelt", key="bd_phi_override"):
        overskriv_kol, _ = st.columns([1, 2.4])
        with overskriv_kol:
            phi = st.number_input(
                "φ (°)", 20.0, 60.0, round(phi_weighted, 1), 0.5,
                key="bd_phi_man",
            )
        ui.besked(
            "Den manuelt indtastede værdi anvendes i stedet for den vægtede. "
            "Opmærksomheden henledes på, at værdien ikke længere følger "
            "ændringer i materialelagene.",
            "advarsel",
        )
    else:
        phi = phi_weighted

    _vis_phi_opsummeringsboks(materialer, phi)

    return materialer, phi


def _input_materialelag_med_korrektioner() -> tuple[list[dict], float]:
    """Materialelag med φ-korrektioner i en højre kolonne ved mellemregning."""
    for idx, (navn, tykkelse) in enumerate((
        ("Stabilgrus SGII 0-32", 300),
        ("Bundsikringssand", 400),
    )):
        st.session_state.setdefault(f"bd_mat_{idx}", navn)
        st.session_state.setdefault(f"bd_t_{idx}", tykkelse)

    materiale_kol, korrektion_kol = st.columns([1.8, 1], gap="large")
    materialer: list[dict] = []
    dynamiske_navne = [m["navn"] for m in st.session_state.get("materialer", [])]
    materiale_options = dynamiske_navne + ["Manuel indtastning"]

    with materiale_kol:
        etiket_kol, antal_kol = st.columns([3, 1], vertical_alignment="bottom")
        with etiket_kol:
            ui.etiket("Materialelag")
        with antal_kol:
            antal_lag = st.number_input(
                "Antal lag", min_value=1, max_value=3, value=2, step=1,
                key="bd_antal_lag", label_visibility="collapsed",
                help="Antal materialelag i opbygningen.",
            )
        st.html(
            '<div class="bg-lagtabel-hoved">'
            '<span>#</span><span>Materiale</span>'
            '<span class="num">Tykkelse</span><span class="num">&#966;</span>'
            '</div>'
        )
        for i in range(int(antal_lag)):
            mat_key = f"bd_mat_{i}"
            if (
                mat_key in st.session_state
                and st.session_state[mat_key] not in materiale_options
            ):
                st.session_state[mat_key] = "Manuel indtastning"

            kol_nr, kol_mat, kol_t, kol_phi = st.columns(
                [0.35, 3.2, 1.5, 0.9], vertical_alignment="center",
            )
            with kol_nr:
                st.html(f'<div class="bg-lagtabel-nr">{i + 1}</div>')
            with kol_mat:
                mat_navn = st.selectbox(
                    "Materiale", materiale_options, key=mat_key,
                    label_visibility="collapsed",
                )
            md = None if mat_navn == "Manuel indtastning" else _find_materiale_session(mat_navn)

            t_key = f"bd_t_{i}"
            if st.session_state.get(t_key, MIN_LAGTYKKELSE_MM) < MIN_LAGTYKKELSE_MM:
                st.session_state[t_key] = MIN_LAGTYKKELSE_MM
            with kol_t:
                t_i = st.number_input(
                    "Tykkelse (mm)", min_value=MIN_LAGTYKKELSE_MM,
                    max_value=2000, step=50, key=t_key,
                    label_visibility="collapsed",
                )

            if md is None:
                with kol_phi:
                    phi_i = st.number_input(
                        "φ (°)", 20.0, 60.0, PHI_BASIS, 0.5,
                        key=f"bd_phi_m_{i}", label_visibility="collapsed",
                    )
                _, kol_korn, kol_type = st.columns([0.35, 3.2, 2.4])
                with kol_korn:
                    korn_i = st.number_input("Max kornstørrelse (mm)", 0, 500, 32, key=f"bd_korn_m_{i}")
                with kol_type:
                    ltype_i = st.selectbox("Lagtype", ["Bærelag", "Bundsikring"], key=f"bd_lt_m_{i}")
                lag_navn, krav_maske_i = "Manuel indtastning", None
            else:
                phi_i, korn_i, ltype_i = float(md["phi"]), md["max_korn"], md["lagtype"]
                krav_maske_i = md.get("krav_maskestoerrelse_mm")
                lag_navn = mat_navn
                with kol_phi:
                    st.html(f'<div class="bg-lagtabel-phi">{ui.grader(phi_i)}</div>')
                krav_txt = f" · krav til geonet maskestørrelse {krav_maske_i} mm" if krav_maske_i is not None else ""
                st.html(f'<div class="bg-lagtabel-note">{ltype_i} · maks. korn {korn_i} mm{krav_txt}</div>')

            materialer.append({
                "navn": lag_navn, "phi": phi_i, "max_korn": korn_i,
                "lagtype": ltype_i, "tykkelse_mm": float(t_i), "pct": None,
                "krav_maskestoerrelse_mm": krav_maske_i,
            })

        data = _phi_tabel_data(materialer)
        phi_weighted = data["phi_weighted"]
        total_t = sum(m["tykkelse_mm"] for m in materialer)
        st.html(
            '<div class="bg-lagtabel-sum">'
            f'<span></span><span>Samlet</span><span class="num">{ui.mm(total_t)}</span>'
            f'<span class="num">{ui.grader(phi_weighted)}</span></div>'
        )
        st.caption(f"Mindste lagtykkelse der kan indtastes er {MIN_LAGTYKKELSE_MM} mm.")
        overskrevet = st.checkbox("Overskriv φ manuelt", key="bd_phi_override")
        if overskrevet:
            phi = st.number_input("φ (°)", 20.0, 60.0, round(phi_weighted, 1), 0.5, key="bd_phi_man")
        else:
            phi = phi_weighted

    phi_kor = K_PHI * (phi - PHI_BASIS)
    with korrektion_kol:
        ui.etiket("φ-korrektion")
        with st.container(border=True):
            st.markdown("**Vægtet friktionsvinkel**")
            st.code(
                f"φ = Σ(tᵢ × φᵢ) / Σ(tᵢ)\n"
                f"  = {_dk_num(data['total_bidrag'], '.0f')} / {_dk_num(data['total_v'], '.0f')}"
                f" = {_dk_num(phi_weighted, '.2f')}°",
                language=None,
            )
        with st.container(border=True):
            st.markdown("**φ-korrektionsfaktor**")
            st.code(
                f"k_φ = {_dk_num(K_PHI, '.2f')} × (φ − {PHI_BASIS:g}°)\n"
                f"    = {_dk_num(K_PHI, '.2f')} × ({_dk_num(phi, '.2f')} − {PHI_BASIS:g})\n"
                f"    = {_dk_num(phi_kor, '+.4f')} = {_dk_num(phi_kor * 100, '+.2f')} %",
                language=None,
            )
        st.caption("Korrektionen anvendes på basistykkelsen.")

    return materialer, phi


def render_brugerdefineret() -> None:
    """Brugerdefineret-tilstand: inputtrin og resultatet som samlet blok.

    Underbund og grundlag (trin 1) samt opbygningens materialelag (trin 2)
    indtastes først. Geonettet vælges derefter øverst i resultatblokken, så
    resultat, opbygning og mellemregninger altid gælder samme produkt.
    """

    t_basis_table = _aktiv_t_basis_table()

    with ui.trin_kort(1, "Underbund og dimensioneringsgrundlag") as trin1:
        eu, grundlag = _input_trin1("bd")
        trin1.opsummering = _trin1_opsummering(eu, grundlag)

    zone_blokerer = (
        grundlag["type"] == "trafikklasse" and grundlag["zone"] != "ok"
    )

    materialer: list[dict] = []
    phi = PHI_BASIS
    geonet: dict | None = None
    geonet_navn: str | None = None
    specifikt_mode = False

    # Blokerer zonen, er der intet driftspunkt at dimensionere efter, og
    # opbygning og geonet ville alligevel ikke føre til et resultat.
    if not zone_blokerer:
        with ui.trin_kort(2, "Opbygning") as trin2:
            materialer, phi = _input_materialelag_med_korrektioner()
            total = _indtastet_total(materialer)
            phi_ord = "vægtet φ"
            trin2.opsummering = (
                f"{len(materialer)} lag · {ui.mm(total)} · "
                f"{phi_ord} {ui.grader(phi)} · "
                f"k_φ {_pct_fortegn(K_PHI * (phi - PHI_BASIS), 1)}"
            )

    if zone_blokerer:
        st.session_state.pop("sidste_dim", None)
        return

    eo = grundlag["eo"]
    valgt_klasse = grundlag["valgt_klasse"]
    eo_interpoleret = grundlag["type"] == "trafikklasse"

    bedste_1: dict | None = None
    bedste_2: dict | None = None
    # Argumenterne til koblings-forklaringen. De to modes sender hver sit sæt
    # (referencenet mod valgt produkt), og forklaringen renderes først nederst
    # i resultatsektionen — se kaldet før st.divider().
    kobling_args: tuple | None = None

    # Reference- og produktberegninger bruges i begge modes — både til
    # at vise reference-banneret og til opbygnings-expanderens dropdown.
    ref_1, ref_2, ref_fejl_1, ref_fejl_2 = _beregn_referencegrupper(
        eu, eo, phi, valgt_klasse, t_basis_table
    )
    prod_1lag = _beregn_produkter_cachet(
        eu, eo, "1_lag", phi, valgt_klasse, t_basis_table
    )
    prod_2lag = _beregn_produkter_cachet(
        eu, eo, "2_lag", phi, valgt_klasse, t_basis_table
    )
    prod_1lag = _berig_produkter_med_placering(prod_1lag, "1_lag", materialer)
    prod_2lag = _berig_produkter_med_placering(prod_2lag, "2_lag", materialer)
    # Rækkefølgen i vælgeren fastlægges af _geonet_valgliste().
    gyldige_geonet = [
        p["navn"]
        for p in prod_1lag + prod_2lag
        if p.get("navn") != "Anden armering (manuel)"
        and p.get("fejl") is None
        and p.get("t_armeret_mm") is not None
    ]
    resultat_geonet_valg, std_index = _geonet_valgliste(gyldige_geonet)
    if not resultat_geonet_valg:
        # Forekommer der ikke et gyldigt produkt, står vælgeren på
        # referencenettet, og beregningen føres med netkorrektion 0.
        resultat_geonet_valg, std_index = [_REF_VALG], 0
    if st.session_state.get("bd_geonet") not in resultat_geonet_valg:
        st.session_state.pop("bd_geonet", None)

    with ui.resultat_blok(_resultat_note(eu, grundlag)):
        ui.underhoved(
            "Vælg geonet",
            _vaelg_geonet_note(grundlag),
        )
        vaelger_kol, _ = st.columns([1, 1.6])
        with vaelger_kol:
            geonet_navn = st.selectbox(
                "Produkt",
                resultat_geonet_valg,
                index=std_index,
                key="bd_geonet",
                format_func=_produkt_label,
                label_visibility="collapsed",
            )
        geonet = find_geonet(geonet_navn)
        if geonet and geonet["navn"] == "Anden armering (manuel)":
                kor_man = st.number_input(
                    "Korrektionsfaktor (−0.20 til +0.20)",
                    min_value=-0.20, max_value=0.20,
                    value=0.0, step=0.01, format="%.2f", key="bd_kor_man",
                    help="0.00 = samme effektivitet som reference (TX160/SX160/T6).",
                )
                geonet = {**geonet, "korrektion": kor_man}
        specifikt_mode = True

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
                    _vis_resultatkort(
                        t_uarm,
                        bedste_1["t_armeret_mm"] if bedste_1 else None,
                        bedste_2["t_armeret_mm"] if bedste_2 else None,
                        standard=False,
                        note_uarm=_note_uarmeret(eo_interpoleret, phi),
                        navne_1=_navne_kort(bedste_1) if bedste_1 else "",
                        navne_2=_navne_kort(bedste_2) if bedste_2 else "",
                        indtastet_total=_indtastet_total(materialer),
                    )
                else:
                    _render_uarmeret_mangler_besked(eu, eo)
                _render_opbygning_afsnit(
                    eu, ref_1, ref_2,
                    prod_1lag=prod_1lag, prod_2lag=prod_2lag,
                    materialer=materialer, phi=phi,
                )
                # Renderes nederst i resultatsektionen, lige over Opbygning.
                if eo_interpoleret:
                    kobling_args = (
                        grundlag["t_klasse"], eu, grundlag["eo_aekv"], phi,
                        ref_1, ref_2, t_basis_table,
                    )
                _render_produkt_tabel(
                    ref_1, ref_2, ref_fejl_1, ref_fejl_2,
                    prod_1lag, prod_2lag, valgt_klasse, phi=phi, eu=eu,
                    trafik_eu=eu if grundlag["type"] == "trafikklasse" else None,
                )

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

            if geonet is None:
                bedste_1 = _reference_resultat_til_gruppe(res_1, valgt_klasse)
                bedste_2 = _reference_resultat_til_gruppe(res_2, valgt_klasse)
            else:
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
                    "grundlag_type": grundlag["type"],
                    "t_klasse": grundlag.get("t_klasse"),
                    "eo_aekv": grundlag.get("eo_aekv"),
                    "zone": grundlag.get("zone"),
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
                    _vis_resultatkort(
                        t_uarm,
                        res_1.get("t_armeret_mm") if not res_1.get("fejl") else None,
                        res_2.get("t_armeret_mm") if not res_2.get("fejl") else None,
                        standard=False,
                        note_uarm=_note_uarmeret(eo_interpoleret, phi),
                        indtastet_total=_indtastet_total(materialer),
                    )
                else:
                    _render_uarmeret_mangler_besked(eu, eo)

                _render_opbygning_afsnit(
                    eu, ref_1, ref_2,
                    prod_1lag=prod_1lag, prod_2lag=prod_2lag,
                    materialer=materialer, phi=phi, geonet_navn=geonet_navn,
                    laas_geonetvalg=True, som_kort=True,
                )

                if eo_interpoleret:
                    # res_1/res_2 er beregnet med det VALGTE nets korrektion —
                    # ref_1/ref_2 er altid referencenettet. Forklaringen skal vise
                    # det net, brugeren rent faktisk har valgt. Renderes nederst i
                    # resultatsektionen, lige over Opbygning.
                    kobling_args = (
                        grundlag["t_klasse"], eu, grundlag["eo_aekv"], phi,
                        None if res_1.get("fejl") else res_1,
                        None if res_2.get("fejl") else res_2,
                        t_basis_table, geonet, materialer,
                    )

                # Mellemregninger for det valgte net. Enkeltprodukt-listerne
                # læses fra de interval-berigede grupper.
                prod_1 = (
                    [bedste_1["produkter"][0]]
                    if bedste_1 and bedste_1.get("produkter") else []
                )
                prod_2 = (
                    [bedste_2["produkter"][0]]
                    if bedste_2 and bedste_2.get("produkter") else []
                )
                with ui.kort(
                    f"Detaljer · {geonet_navn}",
                    "Mellemregninger for det valgte net",
                ):
                    _render_valgt_net_detaljer(
                        prod_1[0] if prod_1 else None,
                        prod_2[0] if prod_2 else None,
                        net_navn=geonet_navn,
                        phi=phi,
                    )
                    t_indtastet_total = _indtastet_total(materialer)
                    ui.underhoved(
                        "Designdiagram",
                        f"Eo = {ui.mpa(eo)} · {_grundlag_tekst(grundlag)} · "
                        f"φ = {ui.grader(phi)} · {geonet_navn}",
                        skillelinje=True,
                    )
                    vis_din_prik = st.checkbox(
                        "Vis indtastet opbygning",
                        value=True,
                        key="bd_dd_vis_din_prik",
                        disabled=t_indtastet_total is None,
                    )
                    vis_lag_prikker = st.checkbox(
                        "Vis endepunkter for 1 og 2 lag geonet",
                        value=True,
                        key="bd_dd_vis_lag_prikker",
                    )
                    _tegn_designdiagram(
                        eu, eo, phi, geonet, t_basis_table,
                        t_indtastet_total if vis_din_prik else None,
                        prod_1[0] if vis_lag_prikker and prod_1 else None,
                        prod_2[0] if vis_lag_prikker and prod_2 else None,
                    )

                with ui.kort("Alle produkter", _produkttabel_note(eu)):
                    _render_alle_produkter_overblik(
                        prod_1lag,
                        prod_2lag,
                        valgt_navn=geonet_navn,
                    )

    if kobling_args is not None:
        _render_trafik_kobling_forklaring(*kobling_args)

    # --- Informations-expandere --------------------------------------------
    _render_oversigt_expanders(
        eu, eo, bedste_1, bedste_2,
        ref_1=ref_1, ref_2=ref_2,
        prod_1lag=prod_1lag, prod_2lag=prod_2lag,
        phi=phi,
        geonet=geonet,
        geonet_navn=geonet_navn,
        materialer=materialer,
        t_basis_table=t_basis_table,
        eo_interpoleret=eo_interpoleret,
        vis_opbygning=False,
    )


# ===========================================================================
# Sidebar navigation
# ===========================================================================

# Navigationen er delt i to blokke. Beregning er arbejdsgangen fra
# dimensionering til færdig rapport; Opslag er de tabelværker, beregningen
# hviler på, og som redigeres uafhængigt af den enkelte sag.
_NAV_GRUPPER = [
    ("Beregning", [
        (":material/straighten:",   "Dimensionering",           "dimensionering"),
        (":material/description:",  "Rapport",                  "rapport"),
    ]),
    ("Opslag", [
        (":material/layers:",       "Materialer",               "materialer"),
        (":material/grid_on:",      "Geonet-database",          "geonet_database"),
        (":material/show_chart:",   "Designdiagrammer",         "designdiagrammer"),
        (":material/table_chart:",  "Trafikklasse-korrelation", "trafikklasse_korrelation"),
        (":material/help:",          "Hjælp og dokumentation",   "hjaelp"),
    ]),
]

_NAV_ITEMS = [punkt for _, punkter in _NAV_GRUPPER for punkt in punkter]


def render_sidebar() -> str:
    """Render venstre navigationsmenu. Returnerer nøglen for den aktive side.

    Firmalogoet står i topbjælken og gentages ikke her.
    """
    if "aktiv_side" not in st.session_state:
        st.session_state.aktiv_side = "dimensionering"

    with st.sidebar:
        for gruppe, punkter in _NAV_GRUPPER:
            st.caption(gruppe)
            for ikon, navn, nøgle in punkter:
                aktiv = st.session_state.aktiv_side == nøgle
                # Ikonet sættes som selvstændigt element (ikke som en del af
                # teksten), så det kan gives fast bredde i CSS og navnene flugter.
                if st.button(
                    navn,
                    icon=ikon,
                    key=f"_nav_{nøgle}",
                    width="stretch",
                    type="primary" if aktiv else "secondary",
                ):
                    st.session_state.aktiv_side = nøgle
                    st.rerun()

        st.markdown(
            '<hr class="sb-divider" style="margin-top:1.5rem">'
            '<div class="sb-footer">'
            "<span>BG Byggros A/S<br>Beregningsværktøj v0.4</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    return st.session_state.aktiv_side


# ===========================================================================
# Hjælp og dokumentation
# ===========================================================================
#
# Teksten vedligeholdes som markdown-filer i »Dokumenter og data/hjaelp« og
# indlæses ved visning, jf. core/hjaelp.py, så dokumentationen kun findes ét
# sted. Siden står for opstillingen: kapitlerne som foldbare kort med resumé,
# formlerne i egne rammer og figurerne i sidekolonnen ved deres afsnit.
# ===========================================================================

# Kapitlet, der står åbent, når siden åbnes uden en henvisning.
_HJAELP_STANDARD_KAPITEL = "beregningsmetoden"

_HJAELP_INTRO = (
    "Værktøjet fastlægger, hvor tykt et ubundet bærelag en vej kræver, og hvor "
    "meget tykkelsen kan nedsættes ved at armere opbygningen med geonet. "
    "Grundlaget er leverandørernes designdiagrammer, ét pr. belastningsklasse.\n\n"
    "Dimensioneringen kan tage udgangspunkt i to grundlag. **Belastningsklassen** "
    "henviser direkte til sit designdiagram, hvor lagtykkelserne aflæses ved "
    "underbundens E-modul. **Trafikklassen** har intet designdiagram; den føres "
    "ind i diagrammerne gennem en VejDim-kørsel, som fastlægger den ubundne "
    "lagtykkelse, og derfra til det punkt, hvor den ustabiliserede kurve giver "
    "samme tykkelse. Der foretages ingen teoretisk omregning mellem de to "
    "metoder."
)

_HJAELP_TRIN = (
    "Underbundens styrke og dimensioneringsgrundlaget angives",
    "Opbygningens materialelag sammensættes",
    "Geonettet vælges",
    "Tykkelsen læses med og uden armering",
)

# Fagudtrykkene og deres forklaring. Listen er sidens ordforklaring og er
# samtidig grundlaget for de forklaringer, udtrykkene bærer ude i appen.
_HJAELP_FAGUDTRYK = (
    ("Eu", "Underbundens E-modul [MN/m²]. Angives i dimensioneringen."),
    ("Eo", "Designdiagrammets overflademodul [MN/m²]. Ved dimensionering efter "
           "belastningsklasse er værdien diagrammets egen, forudsatte "
           "størrelse."),
    ("Eo,ækv", "Det tilbageberegnede opslagspunkt ved dimensionering efter "
               "trafikklasse. En indeksværdi mellem to diagrammer, ikke et "
               "forventet overflademodul."),
    ("NÆ10", "Dimensioneringstrafikken over 20 år for trafikklassen, angivet "
             "i ækvivalente 10-tons akseltryk."),
    ("φ", "Den tykkelsevægtede friktionsvinkel i de ubundne materialelag [°]. "
          "Designmanualerne forudsætter 37°."),
    ("k_net", "Korrektionen for det valgte geonet i forhold til "
              "referencenettet. Positiv giver et tykkere bærelag."),
    ("effektindeks", "Produktets effektivitet i forhold til referencenettet, "
                     "som har indeks 100."),
)

# Symboler, der sættes med sænket skrift i formlerne. Mønsteret dækker
# skrivemåden i kapitelfilerne, fx t_SG, k_φ, Eo_ækv og t_lav,armeret.
_FORMEL_SENKET = re.compile(
    r"\b([A-Za-zÆØÅæøåφ]+)_([A-Za-zÆØÅæøåφ0-9]+(?:,[A-Za-zÆØÅæøå0-9]+)*)"
)


def _formel_html(udtryk: str) -> str:
    """Sæt en formel med sænket skrift på symbolernes indeks.

    Formlerne skrives i kapitelfilerne som almindelig tekst — »t_SG«, »k_φ« —
    og sættes her med sænket skrift, så de fremstår som i håndbogen. Teksten
    escapes først, da formlerne indgår i sidens HTML.
    """
    return _FORMEL_SENKET.sub(
        lambda m: f"{html.escape(m.group(1))}<sub>{html.escape(m.group(2))}</sub>",
        html.escape(udtryk),
    )


def _render_hjaelp_formel(formel) -> None:
    """Formlen i egen ramme med en »hvor:«-liste under, jf. håndbogen."""
    linjer = "<br>".join(_formel_html(l) for l in formel.udtryk.split("\n"))
    hvor = ""
    if formel.hvor:
        poster = "<br>".join(_formel_html(l) for l in formel.hvor)
        hvor = f'<div class="hj-hvor">hvor:<br>{poster}</div>'
    st.html(f'<div class="hj-formel"><div class="hj-udtryk">{linjer}</div>{hvor}</div>')


def _render_hjaelp_figur(figur, nummer: int) -> None:
    """Figuren som en lille tabel med figurtekst under.

    Tabellen sættes af markdown; nummer og figurtekst står omkring den, så
    figuren kan henvises til fra brødteksten.
    """
    st.html(f'<div class="hj-figur-nr">Figur {nummer}</div>')
    st.markdown(figur.tabel)
    st.html(f'<div class="hj-figur-tekst">{html.escape(figur.tekst)}</div>')


def _render_hjaelp_kilder(kilder) -> None:
    """Kildedokumenterne med link til udgiverens egen offentliggjorte udgave.

    En tom blok viser produktdokumenterne fra core.data.KILDEDOKUMENTER,
    hvorfra også noten under geonet-tabellen dannes; ellers vises kapitlets
    egne poster. Linket åbnes i et nyt faneblad, så beregningen ikke forlades.
    """
    def _note(d: dict) -> str:
        # Datoen udelades, hvor dokumentet ikke har en fast udgave.
        return " · ".join(x for x in (d.get("udgiver"), d.get("dato")) if x)

    poster = "".join(
        f'<a class="hj-kilde" href="{html.escape(d["url"], quote=True)}" '
        f'target="_blank" rel="noopener">'
        f'<span class="hj-kilde-titel">{html.escape(d["titel"])}</span>'
        f'<span class="hj-kilde-note">{html.escape(_note(d))}</span></a>'
        for d in (kilder.poster or KILDEDOKUMENTER)
    )
    st.html(f'<div class="hj-kilder">{poster}</div>')


def _render_hjaelp_gaatil(henvisning, key: str) -> None:
    """Henvisning til en anden side som knap.

    Sidenøglen slås op i navigationen; peger den ikke på en kendt side,
    udelades knappen, så en skrivefejl i kapitelfilen ikke standser visningen.
    """
    kendte = {noegle for _, _, noegle in _NAV_ITEMS}
    if henvisning.side not in kendte:
        return
    kol, _ = st.columns([1, 1.1])
    with kol:
        if st.button(henvisning.tekst, key=key, width="stretch"):
            st.session_state["aktiv_side"] = henvisning.side
            st.rerun()


def _render_hjaelp_kapitel(kapitel) -> None:
    """Kapitlets afsnit med figurerne i sidekolonnen.

    Hvert afsnit sættes i sin egen række, så figuren står ud for det afsnit,
    den hører til.
    """
    figur_nr = 0
    for afsnit in kapitel.afsnit:
        venstre, hoejre = st.columns([1.75, 1], gap="large")
        with venstre:
            st.html(
                f'<div class="hj-afsnit-titel">'
                f'<span>{html.escape(afsnit.nummer)}</span>'
                f'{html.escape(afsnit.titel)}</div>'
            )
            for nr, stykke in enumerate(afsnit.indhold):
                if isinstance(stykke, hjaelp_mod.Formel):
                    _render_hjaelp_formel(stykke)
                elif isinstance(stykke, hjaelp_mod.Gaatil):
                    _render_hjaelp_gaatil(
                        stykke,
                        key=f"hj_gaatil_{kapitel.noegle}_{afsnit.nummer}_{nr}",
                    )
                elif isinstance(stykke, hjaelp_mod.Kilder):
                    _render_hjaelp_kilder(stykke)
                else:
                    st.markdown(stykke)
        with hoejre:
            for figur in afsnit.figurer:
                figur_nr += 1
                _render_hjaelp_figur(figur, figur_nr)


def render_hjaelp() -> None:
    """Hjælp og dokumentation — metoden, datagrundlaget og forbeholdene.

    Kapitlerne indlæses fra markdown ved hver visning og vises som foldbare
    kort. Resuméet står i kortets hoved, også når kapitlet er lukket, så det
    rette kapitel kan findes uden at åbne dem alle.
    """
    ui.sidehoved(
        "Hjælp og dokumentation",
        "Beregningsmetoden, datagrundlaget og forbeholdene bag værktøjet.",
    )

    kapitler = hjaelp_mod.laes_kapitler()
    if not kapitler:
        ui.besked(
            "Hjælpeteksten kunne ikke indlæses. Kapitlerne forventes at ligge "
            "som markdown-filer i mappen <i>Dokumenter og data/hjaelp</i>.",
            "advarsel",
        )
        return

    # ── Intro ─────────────────────────────────────────────────────────────
    with ui.kort("Hvad værktøjet gør", "Grundlaget bag beregningen"):
        venstre, hoejre = st.columns([1.35, 1], gap="large")
        with venstre:
            st.markdown(_HJAELP_INTRO)
        with hoejre:
            trin = "".join(
                f'<div class="hj-trin"><span>{nr}</span>{html.escape(tekst)}</div>'
                for nr, tekst in enumerate(_HJAELP_TRIN, start=1)
            )
            udtryk = "".join(
                f'<div class="hj-udtryk-post" title="{html.escape(forklaring, quote=True)}">'
                f'{_formel_html(navn)}</div>'
                for navn, forklaring in _HJAELP_FAGUDTRYK
            )
            st.html(
                '<div class="hj-trinblok">'
                '<div class="hj-trinblok-hoved">En beregning i fire trin</div>'
                f'{trin}'
                '<div class="hj-fagudtryk-hoved">Fagudtryk — forklaringen '
                'vises ved markøren</div>'
                f'<div class="hj-fagudtryk">{udtryk}</div></div>'
            )

    # ── Kapitler ──────────────────────────────────────────────────────────
    aabne = st.session_state.setdefault(
        "hjaelp_aabne", {_HJAELP_STANDARD_KAPITEL}
    )

    for kapitel in kapitler:
        aaben = kapitel.noegle in aabne
        with st.container(key=f"hj_kap_{kapitel.noegle}"):
            kol_hoved, kol_toggle = st.columns([1, 0.17], gap="small")
            with kol_hoved:
                st.html(
                    f'<div class="hj-kap-hoved{" hj-kap-aaben" if aaben else ""}">'
                    f'<div class="hj-kap-nr">{kapitel.nummer}</div>'
                    f'<div class="hj-kap-titel">{html.escape(kapitel.titel)}</div>'
                    f'<div class="hj-kap-antal">{kapitel.afsnit_tal}</div>'
                    f'<div class="hj-kap-resume">{html.escape(kapitel.resume)}</div>'
                    '</div>'
                )
            with kol_toggle:
                if st.button(
                    "Luk" if aaben else "Læs",
                    key=f"hj_toggle_{kapitel.noegle}",
                    width="stretch",
                    type="primary" if aaben else "secondary",
                ):
                    if aaben:
                        aabne.discard(kapitel.noegle)
                    else:
                        aabne.add(kapitel.noegle)
                    st.session_state["hjaelp_aabne"] = aabne
                    st.rerun()
            if aaben:
                _render_hjaelp_kapitel(kapitel)


# ===========================================================================
# Placeholder-sider (Materialer, Geonet database, Designdiagrammer)
# ===========================================================================

def render_geonet_database() -> None:
    """Geonet-databasen, opstillet som Hjælp-siden.

    Tabellen står i sit eget kort, og hver note står som et kort for sig, så
    forbehold og kildehenvisninger kan aflæses enkeltvis.
    """
    ui.sidehoved(
        "Geonet-database",
        "Oversigt over alle geonet-produkter med effektindeks, "
        "belastningsklasser og tekniske data fra datablade og designmanualer.",
    )

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
                f"{_pct_fortegn(g['korrektion_interval'][0])} til "
                f"{_pct_fortegn(g['korrektion_interval'][1])}"
                if g.get("korrektion_interval") is not None
                else _pct_fortegn(g["korrektion"])
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

    kolonne_hjaelp = {
        "Produkt": "Produktnavn som angivet i datablad/designmanual.",
        "Serie": "Produktserie: GS-GRID, E'GRID eller Tensar.",
        "Type": "Netgeometri: biaxialt (firkantede masker), triaxialt eller hexagonalt (triangulære masker).",
        "Effektindeks": "Relativ effektivitet ift. referenceproduktet (= 100). Højere indeks = tyndere bærelag.",
        "Korrektions-\nfaktor": "Direkte korrektionsfaktor på den aflæste bærelagstykkelse i beregningen. Negativt fortegn = tykkelsen reduceres.",
        "BK": "Anbefalede belastningsklasser (1–6) iflg. designmanualerne.",
        "Min. dæklag\n(cm)": "Mindste lagtykkelse over geonettet (cm) — under dette kan geonettets funktion ikke garanteres.",
        "Maks. korn\n(datablad mm)": "Maksimal kornstørrelse i tilslaget angivet i produktdatabladet (mm).",
        "Anb. tilslag\n(designmanual)": "Anbefalet tilslagsstørrelse iflg. dimensioneringsmanualen (mm).",
        "Maskestørrelse\n(datablad mm)": "Maskestørrelse (ca.) angivet i produktdatabladet (mm).",
        "Rudeåbning/maskestørrelse\n(designmanual)": "Rudeåbning/maskestørrelse angivet i designmanualen — kan afvige fra databladets maskestørrelse.",
        "Radial stivhed\n(kN/m @ 0,5%)": "Radial sekantstivhed ved 0,5 % tøjning (kN/m) — angives kun for hexagonale produkter.",
        "GWP A1–A3\n(kg CO₂/m²)": "Klimaaftryk i produktionsfasen A1–A3 (kg CO₂-ækvivalent pr. m²). Ved flere værdier angives pr. rullebredde.",
        "Min. levetid": "Teknisk minimumslevetid angivet i datablad.",
        "Min. trækstyrke\n(kN/m)": "Minimum trækstyrke ved brud (kN/m) iflg. datablad.",
        "Trækstyrke 2%\n(kN/m)": "Trækstyrke ved 2 % tøjning (kN/m) — udtryk for stivhed ved små deformationer.",
        "Trækstyrke 5%\n(kN/m)": "Trækstyrke ved 5 % tøjning (kN/m) — udtryk for den kraft nettet kan mobilisere ved store deformationer (reservekapacitet).",
        "Maks. def.\n(%)": "Maksimal deformation (tøjning) ved brud iflg. datablad (%).",
        "Knudepunkt\neffektivitet": "Knudepunkternes styrke i procent af ribbernes trækstyrke — udtryk for hvor godt kræfter overføres i nettet.",
        "Maskestabilitet\n(N.mm/grad)": "Maskens rotationsstabilitet (aperture stability modulus, N·mm/grad) — modstand mod vridning af maskerne.",
        "Ribbetykkelse\n(mm)": "Ribbernes tykkelse (mm) iflg. datablad.",
        "Stivhedsforhold": "Forhold mellem stivhed i nettets retninger — tæt på 1 betyder ensartede egenskaber i alle retninger.",
        "Overlæg Eu ≥ 5\n(cm)": "Påkrævet overlæg i samlinger (cm) når underbundens E-modul Eu ≥ 5 MPa.",
        "Overlæg Eu < 5\n(cm)": "Påkrævet overlæg i samlinger (cm) når underbundens E-modul Eu < 5 MPa.",
        "Bemærkning": "Særlige forhold, datakilder og rettelser for produktet.",
    }

    # Kolonnebeskrivelserne ligger som tooltips på kolonneoverskrifterne, jf.
    # kolonne_hjaelp ovenfor. Alle 25 kolonner er dækket.
    with ui.kort(
        "Produkter",
        f"{len(rækker)} produkter · {len(kolonne_hjaelp)} kolonner · "
        "forklaringen vises ved kolonneoverskriften",
    ):
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            height=tabel_hoejde,
            column_config={
                navn: st.column_config.Column(help=tekst)
                for navn, tekst in kolonne_hjaelp.items()
            },
        )

    # ── Noter og kildehenvisninger ────────────────────────────────────────
    # Hver note står i sit eget kort, jf. kapitlerne på Hjælp-siden. Noterne
    # er korte og vises derfor åbne; teksten sættes af markdown, idet enkelte
    # noter rummer opstillinger og henvisninger.
    ui.underhoved(
        "Database-noter og kildehenvisninger",
        f"{len(GEONET_NOTER)} noter",
        skillelinje=True,
    )
    for nr, note in enumerate(GEONET_NOTER, start=1):
        with st.container(key=f"bg_note_{nr}"):
            st.html(
                '<div class="bg-note-hoved">'
                f'<div class="bg-note-nr">Note {nr}</div>'
                f'<div class="bg-note-titel">{html.escape(note["titel"])}</div>'
                '</div>'
            )
            st.markdown(note["tekst"])


def _diagram_daekning(diagram: dict) -> str:
    """Kurvernes gyldighedsområde i det enkelte diagram, som fodnotetekst.

    Diagrammerne er ikke optegnet for hele Eu-området: den ustabiliserede
    opbygning er ikke dimensioneret ved de laveste bundmoduler, og de
    armerede kurver ophører ved hver sin øvre grænse. Fodnoten angiver de
    faktiske grænser, så en tom celle kan skelnes fra en manglende aflæsning.
    """
    dele: list[str] = []
    for felt, navn in (
        ("t_uarmeret_cm", "Ustabiliseret"),
        ("t_1_lag_cm", "1 lag armering"),
        ("t_2_lag_cm", "2 lag armering"),
    ):
        eu_vals = [
            r["eu"] for r in diagram["rows"] if r.get(felt) is not None
        ]
        if eu_vals:
            dele.append(
                f"{navn} Eu = {min(eu_vals):.0f}–{max(eu_vals):.0f} MN/m²"
            )
        else:
            dele.append(f"{navn} forekommer ikke")
    return " · ".join(dele)


def _diagram_tabel_html(diagram: dict) -> str:
    """De aflæste diagramdata som fast tabel.

    Tabellen er skrivebeskyttet i visningstilstanden; redigering foregår i
    st.data_editor, jf. Redigér-knappen. Manglende aflæsninger angives med
    tankestreg, jf. _diagram_daekning().
    """
    def _tal(v: float | None) -> str:
        return "—" if v is None else f"{v:.1f}".replace(".", ",")

    hoved = (
        '<div class="dd-tabel-hoved">'
        '<div>E<sub>u</sub> MPA</div>'
        '<div>USTABILISERET</div><div>1 LAG</div><div>2 LAG</div></div>'
    )
    raekker = "".join(
        '<div class="dd-tabel-raekke">'
        f'<div class="dd-tabel-eu">{r["eu"]:.0f}</div>'
        f'<div>{_tal(r.get("t_uarmeret_cm"))}</div>'
        f'<div>{_tal(r.get("t_1_lag_cm"))}</div>'
        f'<div>{_tal(r.get("t_2_lag_cm"))}</div></div>'
        for r in diagram["rows"]
    )
    return f'{hoved}<div class="dd-tabel-krop">{raekker}</div>'


def _render_diagram_vaelger(diagrammer: list[dict], valgt_nr: int) -> None:
    """Diagrammerne som kort, der vælges ét ad gangen.

    Hvert kort angiver diagrammets nummer, dets overflademodul og den
    belastningsklasse, det dækker. Kortet er selv knappen; den ligger som en
    gennemsigtig flade oven på indholdet, jf. st-key-dd_kort_ i stylesheetet.
    """
    for kol, d in zip(st.columns(len(diagrammer), gap="small"), diagrammer):
        nr = d["diagram_nr"]
        valgt = " dd-kort-valgt" if nr == valgt_nr else ""
        with kol:
            with st.container(key=f"dd_kort_{nr}"):
                # Knappen står først og fylder kortets plads; kortets indhold
                # trækkes op oven på den med negativ margin og lader klik gå
                # igennem, jf. st-key-dd_kort_ i stylesheetet. Rækkefølgen er
                # væsentlig — indholdet skal tegnes efter knappen.
                if st.button(
                    f"Vælg diagram {nr}",
                    key=f"dd_vaelg_{nr}",
                    width="stretch",
                ):
                    st.session_state["dd_valgt_nr"] = nr
                    st.rerun()
                st.html(
                    f'<div class="dd-kort{valgt}">'
                    f'<div class="dd-kort-nr">DIAGRAM {nr}</div>'
                    f'<div class="dd-kort-eo">{d["eo"]:.0f}'
                    f'<span> MN/m²</span></div>'
                    f'<div class="dd-kort-klasse">Belastningsklasse '
                    f'{d["klasse"]}</div></div>'
                )


def render_designdiagrammer() -> None:
    ui.sidehoved(
        "Designdiagrammer",
        "Diagrammer fra designmanualerne med tilhørende aflæste data. "
        "Beregningerne slår op direkte i tabellerne, da interpolationen "
        "mellem diagrammernes værdier er foretaget på forhånd.",
    )

    import pandas as pd

    diagrammer = st.session_state["designdiagrammer"]
    eo_vals = [d["eo"] for d in diagrammer]

    # ── 1 Vælg diagram ────────────────────────────────────────────────────
    valgt_nr = st.session_state.get("dd_valgt_nr", diagrammer[0]["diagram_nr"])
    if valgt_nr not in {d["diagram_nr"] for d in diagrammer}:
        valgt_nr = diagrammer[0]["diagram_nr"]

    with ui.trin_kort(1, "Vælg diagram") as trin:
        trin.opsummering = (
            f"{len(diagrammer)} diagrammer · Eo {min(eo_vals):.0f}–"
            f"{max(eo_vals):.0f} MN/m²"
        )
        _render_diagram_vaelger(diagrammer, valgt_nr)

    diagram = next(d for d in diagrammer if d["diagram_nr"] == valgt_nr)

    # ── 2 Det valgte diagram ──────────────────────────────────────────────
    titel = (
        f"Diagram {valgt_nr} — Eo = {diagram['eo']:.0f} MN/m², "
        f"belastningsklasse {diagram['klasse']}"
    )
    redigerer = st.session_state.get("dd_redigerer") == valgt_nr

    with ui.trin_kort(2, titel):
        kol_diagram, kol_tabel = st.columns([1.1, 1], gap="large")

        with kol_diagram:
            # Optegningen gengiver tabellen; scanningen er manualens egen
            # figur. De to visninger skiftes der imellem, så den aflæste
            # kurve kan holdes op mod kilden.
            visning = st.segmented_control(
                "Visning",
                ["Original scan", "Optegnet"],
                default="Optegnet",
                key=f"dd_visning_{valgt_nr}",
                label_visibility="collapsed",
            ) or "Optegnet"
            if visning == "Original scan":
                st.image(
                    os.path.join(
                        os.path.dirname(__file__),
                        "diagrambilleder",
                        diagram["image_name"],
                    ),
                    width="stretch",
                )
                st.caption("Scanning fra designmanualen")
            else:
                fig = byg_raadiagram(diagram)
                if fig is None:
                    ui.besked(
                        "Diagrammet kan ikke optegnes, da tabellen ikke "
                        "indeholder aflæste værdier.",
                        "advarsel",
                    )
                else:
                    st.plotly_chart(
                        fig, width="stretch",
                        config={"displayModeBar": False},
                        key=f"dd_fig_{valgt_nr}",
                    )
                    st.caption(
                        "Optegnet af tabellens værdier · skift til den "
                        "originale scanning i vælgeren ovenfor"
                    )

        with kol_tabel:
            kol_titel, kol_knap = st.columns([1, 0.32], gap="small")
            with kol_titel:
                st.html(
                    '<div class="dd-tabel-titel">Aflæste diagramdata · '
                    'bærelagstykkelse i cm</div>'
                )
            with kol_knap:
                if redigerer:
                    if st.button("Færdig", key=f"dd_luk_{valgt_nr}",
                                 width="stretch", type="primary"):
                        st.session_state.pop("dd_redigerer", None)
                        st.rerun()
                elif st.button("Redigér", key=f"dd_rediger_{valgt_nr}",
                               width="stretch"):
                    st.session_state["dd_redigerer"] = valgt_nr
                    st.rerun()

            if redigerer:
                _rediger_diagramdata(diagram, pd)
            else:
                st.html(_diagram_tabel_html(diagram))

            st.html(
                '<div class="dd-tabel-fod">— Uden for diagrammets område. '
                f'{html.escape(_diagram_daekning(diagram))}.</div>'
            )

    # Nulstillingen gælder samtlige diagrammer og står derfor for sig, uden
    # for det enkelte diagrams kort.
    if st.button("Nulstil alle diagramdata til standard", type="secondary"):
        slet_designdiagrammer_json_og_nulstil()
        st.session_state["designdiagrammer"] = _standard_designdiagrammer()
        st.session_state.pop("dd_redigerer", None)
        _opdater_aktiv_t_basis_table()
        st.rerun()
    st.caption(
        "Nulstillingen kasserer redigeringer i alle seks diagrammer og "
        "genindlæser designmanualernes aflæste værdier."
    )


def _rediger_diagramdata(diagram: dict, pd) -> None:
    """Diagramdataen som redigerbar tabel.

    Ændringer træder i kraft, efterhånden som de indtastes, og gemmes til
    designdiagrammer_brugerdefineret.json. Beregningernes opslagstabel
    dannes på ny ved hver ændring, jf. _opdater_aktiv_t_basis_table().
    """
    kolonner = {
        "Eu (MPa)": ("eu", 1.0, "%.0f"),
        "Ustabiliseret tykkelse (cm)": ("t_uarmeret_cm", 0.1, "%.1f"),
        "1 lag tykkelse (cm)": ("t_1_lag_cm", 0.1, "%.1f"),
        "2 lag tykkelse (cm)": ("t_2_lag_cm", 0.1, "%.1f"),
    }
    redigeret = st.data_editor(
        pd.DataFrame([
            {label: row[felt] for label, (felt, _, _) in kolonner.items()}
            for row in diagram["rows"]
        ]),
        width="stretch",
        height=520,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            label: st.column_config.NumberColumn(
                label, min_value=0.0, step=trin, format=fmt,
            )
            for label, (_, trin, fmt) in kolonner.items()
        },
        key=f"diagram_editor_{diagram['diagram_nr']}",
    )

    opdaterede = [
        {**d, "rows": redigeret.to_dict("records")}
        if d["diagram_nr"] == diagram["diagram_nr"] else d
        for d in st.session_state["designdiagrammer"]
    ]
    normaliserede, fejl = _normaliser_designdiagrammer(opdaterede)
    if fejl:
        st.error("Diagramdata er ikke gemt, fordi der er fejl: " + " ".join(fejl))
    elif normaliserede != st.session_state["designdiagrammer"]:
        st.session_state["designdiagrammer"] = normaliserede
        gem_designdiagrammer(normaliserede)
        _opdater_aktiv_t_basis_table()
        st.rerun()


def _korrelation_pivot_rows(korr: dict) -> list[dict]:
    """Eo_ækv-tabellen som rækker til st.dataframe (T × Eu → tekst)."""
    rows = []
    for t in TRAFIKKLASSER:
        row = {"Trafikklasse": t}
        for eu in TRAFIK_EU_PUNKTER:
            v = korr.get(t, {}).get(eu)
            row[f"Eu {eu}"] = v if isinstance(v, str) else (
                f"{v:.0f}" if v is not None else "—"
            )
        rows.append(row)
    return rows


# Metoden bag koblingen — de fire led, siden sammenfatter. Formlerne og det
# gennemregnede eksempel står i Hjælp, kapitel 1 og 2.
_KORR_TRIN = (
    ("Ubunden lagtykkelse",
     "VejDim-kørslen fastlægger den lagtykkelse, trafikklassen kræver ved "
     "underbundens E-modul. Hvis der er valgt et Eu mellem kørte E-værdier interpoleres værdien."),
    ("Ækvivalent Eo",
     "Den Eo-kurve, hvis ustabiliserede lagtykkelse svarer til den fastlagte, "
     "bestemmes ved interpolation mellem de to nærmeste kurver fra de originale designdiagrammer."),
    ("Geonet-reduktion",
     "Reduktionen følger af de samme to kurvers armerede lagtykkelser med "
     "samme interpolationsfaktor."),
    ("Korrektion",
     "Lagtykkelsen korrigeres for friktionsvinkel og for det valgte geonets effektindeks i "
     "forhold til referencenettet."),
)

# Kørslernes faste forudsætninger. Forbehold og gyldighedsområde står i
# Hjælp, kapitel 7.
_KORR_FORUDSAETNINGER = (
    ("Belastningsmodel", "Æ10 tvillingehjul, 60–80 km/t"),
    ("Afvanding", "Nej"),
    ("Underbund", "Frostsikker, E overskrevet til cellens Eu"),
    ("Levetidsmål", "20 år, alle lag"),
    ("Ubundne lag", "SG II (E = 300) over BL II U≤3 (E = 100)"),
    ("Asfalt-E", "Standard, ikke overskrevet"),
)

# Kørselstabellens første kolonner bliver stående ved vandret scroll, så den
# række, der rettes i, altid kan aflæses.
_KORR_FASTE_KOLONNER = ("Trafikklasse", "Eu (MPa)")


# Cellen, regneeksemplet ved siden af Eo-matricen tager udgangspunkt i.
# Ligger den uden for designdiagrammernes område — hvilket kan ske, når
# kørslerne er rettet — vælges den første celle i zonen ok i stedet.
_KORR_EKSEMPEL = ("T3", 15)


def _korr_eksempel_celle(korr: dict) -> tuple[str, int] | None:
    """Vælg den celle, regneeksemplet opstilles for.

    Eksemplet skal vise en gennemført tilbageberegning og kan derfor ikke
    hvile på en celle i zonen under, over eller mangler.
    """
    t_std, eu_std = _KORR_EKSEMPEL
    if isinstance((korr.get(t_std) or {}).get(eu_std), (int, float)):
        return t_std, eu_std
    for t_klasse, raekke in korr.items():
        for eu, vaerdi in raekke.items():
            if isinstance(vaerdi, (int, float)):
                return t_klasse, int(eu)
    return None


def _render_korr_eksempel(korr: dict, t_basis_table: dict) -> None:
    """Regneeksempel ved siden af Eo-matricen.

    Eksemplet regnes af de aktive kørsler og det aktive designdiagram og
    følger derfor med, når et af de to grundlag rettes. Trinene svarer til
    Hjælp, kapitel 1, afsnit 3 og 4.
    """
    celle = _korr_eksempel_celle(korr)
    if celle is None:
        return
    t_klasse, eu = celle
    tal = _eo_aekv_trin_tal(t_klasse, float(eu), t_basis_table)
    if not tal or "eo_aekv" not in tal["trin2"]:
        return
    t1, t2 = tal["trin1"], tal["trin2"]

    def _mm(v: float) -> str:
        return f"{v:,.0f}".replace(",", ".")

    # Trin 1 er enten et direkte opslag i en kørsel eller en interpolation i
    # log(Eu). Eksempelcellen er et kørt punkt, men udtrykket dannes for
    # begge tilfælde, så eksemplet også holder ved en rettet kørsel.
    if t1.get("direkte") and t1.get("sg") is not None:
        trin1_udtryk = (
            f"t_ubundet = {_mm(t1['sg'])} + {_mm(t1['bl'])} "
            f"= {_mm(t1['ubundet_mm'])} mm"
        )
        trin1_note = "SG + BL fra kørslen"
    else:
        trin1_udtryk = f"t_ubundet = {_mm(t1['ubundet_mm'])} mm"
        trin1_note = f"interpoleret i log(Eu) mellem {t1.get('lav')} og {t1.get('hoej')} MPa"

    frac = t2["frac"]
    eo_aekv = t2["eo_aekv"]
    st.markdown(
        "**Eksempel på udregning af ækvivalent Eo-værdi i tabellen**"
    )
    st.html(
        '<div class="korr-eksempel">'
        f'<div class="korr-eksempel-hoved">Eksempel · {t_klasse} ved '
        f'Eu = {eu} MN/m²</div>'

        '<div class="korr-eksempel-trin"><span>1</span>'
        f'<div><div class="korr-eksempel-tekst">{trin1_note}</div>'
        f'<div class="korr-eksempel-tal">{html.escape(trin1_udtryk)}</div>'
        '</div></div>'

        '<div class="korr-eksempel-trin"><span>2</span>'
        '<div><div class="korr-eksempel-tekst">Tykkelsen findes mellem to '
        'ustabiliserede kurver</div>'
        f'<div class="korr-eksempel-tal">Eo = {t2["eo_lav"]:.0f} MPa'
        f'<span class="korr-eksempel-pil">→</span>{_mm(t2["t_lav"])} mm<br>'
        f'Eo = {t2["eo_hoej"]:.0f} MPa'
        f'<span class="korr-eksempel-pil">→</span>{_mm(t2["t_hoej"])} mm</div>'
        '</div></div>'

        '<div class="korr-eksempel-trin"><span>3</span>'
        '<div><div class="korr-eksempel-tekst">Interpolation mellem de '
        'to kurver</div>'
        f'<div class="korr-eksempel-tal">f = ({_mm(t1["ubundet_mm"])} − '
        f'{_mm(t2["t_lav"])}) / ({_mm(t2["t_hoej"])} − {_mm(t2["t_lav"])}) '
        f'= {_dk_num(frac, ".2f")}<br>'
        f'Eo_ækv = {t2["eo_lav"]:.0f} + {_dk_num(frac, ".2f")} × '
        f'({t2["eo_hoej"]:.0f} − {t2["eo_lav"]:.0f}) '
        f'= {_dk_num(eo_aekv, ".1f")}</div></div></div>'

        '<div class="korr-eksempel-svar">Cellen viser '
        f'<b>{eo_aekv:.0f}</b><span>afrundet fra '
        f'{_dk_num(eo_aekv, ".1f")} MPa</span></div>'
        '</div>'
    )


def _tykkelse_interval(vaerdier: list[float]) -> str:
    """Formatér en tykkelse som tal eller interval, fx '40' eller '117–120'."""
    unikke = sorted({round(v) for v in vaerdier if v})
    if not unikke:
        return ""
    if len(unikke) == 1:
        return f"{unikke[0]:.0f}"
    return f"{unikke[0]:.0f}–{unikke[-1]:.0f}"


def _asfaltpakke_rows(raekker: list[dict]) -> list[dict]:
    """Byg asfaltpakke-tabellen dynamisk ud fra de aktive kørsler."""
    ud: list[dict] = []
    for t in TRAFIKKLASSER:
        t_raekker = [r for r in raekker if r["T"] == t]
        if not t_raekker:
            continue
        dele: list[str] = []
        for navn_key, tyk_key in (
            ("slidlag", "t_slid_mm"),
            ("bindelag", "t_bindelag_mm"),
            ("bundet_baerelag", "t_bundet_mm"),
        ):
            navne = {r[navn_key] for r in t_raekker if r[navn_key] not in ("", "-")}
            tykkelser = [r[tyk_key] for r in t_raekker if r[tyk_key]]
            if not navne or not tykkelser:
                continue
            navn = " / ".join(sorted(navne))
            suffiks = " (bindelag)" if navn_key == "bindelag" else ""
            dele.append(f"{_tykkelse_interval(tykkelser)} {navn}{suffiks}")
        naae10 = TRAFIKKLASSER[t]["naae10_mio_20aar"]
        ud.append({
            "Klasse": t,
            "NÆ10 (20 år)": f"~{f'{naae10:g}'.replace('.', ',')} mio.",
            "Slidlag + bundne bærelag (mm)": " + ".join(dele) or "—",
        })
    return ud

def render_trafikklasse_korrelation() -> None:
    """Trafikklasse-korrelationen som fire trin, jf. designgennemgangens 10a.

    Siden viser tabellerne og hvad de betyder; metoden med formler og
    gennemregnet eksempel står i Hjælp, kapitel 1 og 2. Eo-matricen er sidens
    egentlige indhold og fremhæves, idet det er den tabel, dimensioneringen
    slår op i.
    """
    ui.sidehoved(
        "Trafikklasse-korrelation",
        "Vejledende kobling mellem Vejdirektoratets trafikklasser og "
        "designmanualernes Eo-kurver. Kørslerne kan redigeres — den "
        "ækvivalente Eo genberegnes og anvendes med det samme i "
        "dimensioneringen. Metoden er beskrevet i Hjælp og dokumentation.",
    )

    raekker = berig_koersel_raekker(_aktiv_koersel_raekker())

    import pandas as pd

    # Kortet rummer kørselstabellen i fuld bredde, og brødteksten følger med,
    # så den ikke står som en smal spalte over tabellen.
    with ui.trin_kort(1, "VejDim-kørsler", bred_brodtekst=True) as t1:
        t1.opsummering = f"{len(raekker)} kørsler · redigerbar"
        st.markdown(
            "Der er udført dimensionering af de ubundne lag med Vejdirektoratets værktøj VejDim. I tabellen herunder er angivet de anvendte materialer og deres tykkelser som angivet i VejDim efter hver beregning. "
            "Rettes en værdi, følger Eo-matricen nedenfor og dimensioneringen med. **Ubundet** og **Samlet højde** beregnes og kan ikke redigeres."
        )

        kol_nulstil, kol_csv, _ = st.columns([1, 1, 2.6], gap="small")
        with kol_nulstil:
            if st.button(
                "Nulstil kørsler",
                key="korr_nulstil",
                width="stretch",
                help="Kasserer foretagne ændringer og gendanner de oprindelige "
                     f"{len(raekker)} kørsler.",
            ):
                slet_koersler_json_og_nulstil()
                st.session_state["vejdim_koersel_raekker"] = _standard_koersel_raekker()
                st.session_state.pop("koersel_editor", None)
                st.rerun()

        editor_rows = [
            {
                "Trafikklasse": r["T"],
                "Eu (MPa)": r["eu"],
                "Slidlag": r["slidlag"],
                "t slidlag (mm)": r["t_slid_mm"],
                "Bindelag": r["bindelag"],
                "t bindelag (mm)": r["t_bindelag_mm"],
                "Bundet bærelag": r["bundet_baerelag"],
                "t bundet (mm)": r["t_bundet_mm"],
                "Asfalt-E (MPa)": r["E_asf_vist_MPa"],
                "Ubundet bærelag": r.get(
                    "ubundet_baerelag", UBUNDET_BAERELAG_STANDARD),
                "SG (mm)": r["t_SG_mm"],
                "Bundsikringslag": r.get("bundsikring", BUNDSIKRING_STANDARD),
                "BL (mm)": r["t_BL_mm"],
                "Ubundet (mm)": r["t_ubundet_total_mm"],
                "Samlet højde (mm)": r["t_befaestelse_total_mm"],
                "Levetid (år)": r["levetid_styrende_aar"],
                "Bemærkning": r["bemaerkning"],
            }
            for r in raekker
        ]
        with kol_csv:
            st.download_button(
                "Hent som CSV",
                data=pd.DataFrame(editor_rows).to_csv(index=False, sep=";")
                     .encode("utf-8-sig"),
                file_name="vejdim_koersler.csv",
                mime="text/csv",
                key="korr_csv",
                width="stretch",
                help="De viste kørsler med semikolon som skilletegn.",
            )

        _mm = dict(min_value=0.0, step=10.0, format="%.0f")
        # Siden viser de første ni kørsler og lader resten ligge i tabellens
        # scrollområde. Det holder siden kompakt, uden at rækkerne bliver
        # skjult fra editoren.
        vis_alle = st.session_state.get("korr_vis_alle", False)
        synlige_rækker = len(editor_rows) if vis_alle else min(9, len(editor_rows))
        editor_hoejde = 35 * (synlige_rækker + 1) + 3
        redigeret = st.data_editor(
            pd.DataFrame(editor_rows),
            width="stretch",
            height=editor_hoejde,
            hide_index=True,
            column_config={
                # Trafikklasse og Eu bliver stående ved vandret scroll, så den
                # række, der rettes i, altid kan aflæses.
                "Trafikklasse": st.column_config.TextColumn(
                    "Trafikklasse", disabled=True, pinned=True),
                "Eu (MPa)": st.column_config.NumberColumn(
                    "Eu (MPa)", disabled=True, format="%.0f", pinned=True),
                "t slidlag (mm)": st.column_config.NumberColumn("t slidlag (mm)", **_mm),
                "t bindelag (mm)": st.column_config.NumberColumn("t bindelag (mm)", **_mm),
                "t bundet (mm)": st.column_config.NumberColumn("t bundet (mm)", **_mm),
                "Asfalt-E (MPa)": st.column_config.NumberColumn(
                    "Asfalt-E (MPa)", min_value=0.0, step=100.0, format="%.0f"),
                "Ubundet bærelag": st.column_config.TextColumn(
                    "Ubundet bærelag",
                    help="Materialet i det ubundne bærelag, som kørslen er "
                         "udført med. Tykkelsen angives i kolonnen SG (mm)."),
                "SG (mm)": st.column_config.NumberColumn("SG (mm)", **_mm),
                "Bundsikringslag": st.column_config.TextColumn(
                    "Bundsikringslag",
                    help="Materialet i bundsikringslaget, som kørslen er udført "
                         "med. Tykkelsen angives i kolonnen BL (mm)."),
                "BL (mm)": st.column_config.NumberColumn("BL (mm)", **_mm),
                # Afledte kolonner — beregnes, kan ikke redigeres.
                "Ubundet (mm)": st.column_config.NumberColumn(
                    "Ubundet (mm)", disabled=True, format="%.0f",
                    help="SG + BL — det tal Eo_ækv beregnes ud fra."),
                "Samlet højde (mm)": st.column_config.NumberColumn(
                    "Samlet højde (mm)", disabled=True, format="%.0f",
                    help="Asfaltpakke + SG + BL. Relevant for frostkontrollen."),
                "Levetid (år)": st.column_config.NumberColumn(
                    "Levetid (år)", min_value=0.0, step=0.1, format="%.1f"),
            },
            key="koersel_editor",
        )
        fod_venstre, fod_hoejre = st.columns([1, 1], vertical_alignment="center")
        with fod_venstre:
            st.caption(
                f"Viser {synlige_rækker} af {len(editor_rows)} kørsler · "
                "Trafikklasse og Eu bliver stående ved vandret scroll"
            )
        with fod_hoejre:
            if st.button(
                "Vis kun de første 9" if vis_alle else f"Vis alle {len(editor_rows)}",
                key="korr_vis_alle_knap",
                type="tertiary",
            ):
                st.session_state["korr_vis_alle"] = not vis_alle
                st.rerun()

        nye_raekker = _normaliser_koersel_raekker([
            {
                "T": r["Trafikklasse"], "eu": r["Eu (MPa)"],
                "slidlag": r["Slidlag"], "t_slid_mm": r["t slidlag (mm)"],
                "bindelag": r["Bindelag"], "t_bindelag_mm": r["t bindelag (mm)"],
                "bundet_baerelag": r["Bundet bærelag"], "t_bundet_mm": r["t bundet (mm)"],
                "E_asf_vist_MPa": r["Asfalt-E (MPa)"],
                "ubundet_baerelag": r["Ubundet bærelag"], "t_SG_mm": r["SG (mm)"],
                "bundsikring": r["Bundsikringslag"], "t_BL_mm": r["BL (mm)"],
                "levetid_styrende_aar": r["Levetid (år)"],
                "bemaerkning": r["Bemærkning"],
            }
            for r in redigeret.to_dict("records")
        ])
        if nye_raekker != _aktiv_koersel_raekker():
            st.session_state["vejdim_koersel_raekker"] = nye_raekker
            gem_koersel_raekker(nye_raekker)
            # Kør siden igen: de afledte visninger (asfaltpakke, Eo_ækv) står før
            # editoren og ville ellers vise værdierne fra før redigeringen.
            st.rerun()

        if nye_raekker != _standard_koersel_raekker():
            antal = sum(
                1 for ny, std in zip(nye_raekker, _standard_koersel_raekker())
                if ny != std
            )
            ui.besked(
                f"<b>{antal} kørsel(er) er ændret</b> i forhold til de oprindelige "
                f"værdier. Brug <i>Nulstil kørsler</i> for at gendanne dem.",
                "advarsel",
            )

    # Eo-matricen er sidens egentlige indhold og fremhæves derfor: det er
    # denne tabel, dimensioneringen slår op i.
    with ui.trin_kort(
        2, "Ækvivalent Eo — opslagstabellen", fremhaevet=True,
    ) as t2:
        t2.opsummering = "MPa · afledt af kørslerne ovenfor"
        # Den fulde forklaring — afledningen, forbeholdet om at matricen alene
        # gælder trafikklasse, og figuren — står i Hjælp, kapitel 2. Siden
        # angiver alene, hvad tabellen bruges til.
        st.markdown(
            "Det er denne tabel, dimensioneringen slår op i ved valg af "
            "trafikklasse."
        )
        t_basis = _aktiv_t_basis_table()
        korr = korrelation_fra_koersler(koersler_fra_raekker(raekker), t_basis)
        # Regneeksemplet står ved siden af tabellen, så en enkelt celle kan
        # følges fra kørsel til opslagspunkt uden at forlade siden.
        kol_tabel, kol_eksempel = st.columns([1.15, 1], gap="large")
        with kol_tabel:
            _vis_korrelationstabel(korr, med_forklaring=False)
        with kol_eksempel:
            _render_korr_eksempel(korr, t_basis)

        st.html(
            '<div class="korr-zoneforklaring"><b>under</b> / <b>over</b> — '
            'trafikklassen kræver en tyndere henholdsvis tykkere opbygning '
            'end designdiagrammernes område, og reduktionen kan ikke '
            'bestemmes</div>'
        )
        st.caption("Se Hjælp afsnit 2 for yderligere detaljer om trafikklasse korrelationen.")

    kol_metode, kol_data = st.columns([1, 1], gap="medium")
    with kol_metode:
        with ui.trin_kort(3, "Sådan er koblingen fremstillet") as t3:
            t3.opsummering = f"{len(_KORR_TRIN)} trin"
            poster = "".join(
                f'<div class="korr-trin"><span>{nr}</span>'
                f'<div><div class="korr-trin-titel">{html.escape(titel)}</div>'
                f'<div class="korr-trin-tekst">{html.escape(tekst)}</div>'
                '</div></div>'
                for nr, (titel, tekst) in enumerate(_KORR_TRIN, start=1)
            )
            st.html(f'<div class="korr-trinliste">{poster}</div>')
            st.caption(
                "Se Hjælp afsnit 1 for yderligere detaljer om "
                "beregningsmetoden."
            )

    with kol_data:
        with ui.trin_kort(4, "Datagrundlag og forudsætninger") as t4:
            t4.opsummering = "Kan redigeres"
            st.markdown(
                f"**{len(raekker)} kørsler** = T1–T6 × Eu "
                "{3, 4, 5, 10, 15, 20, 30, 40} MPa, alle med:"
            )
            poster = "".join(
                f'<div class="korr-data-post"><span>{html.escape(navn)}</span>'
                f'<span>{html.escape(vaerdi)}</span></div>'
                for navn, vaerdi in _KORR_FORUDSAETNINGER
            )
            st.html(f'<div class="korr-dataliste">{poster}</div>')
            with st.expander(
                f"Fast asfaltpakke pr. klasse · {len(TRAFIKKLASSER)} rækker"
            ):
                st.dataframe(
                    _asfaltpakke_rows(raekker), width="stretch", hide_index=True,
                )
                st.caption(
                    "Bundne bærelag er låst, hvor det er muligt; ellers er "
                    "VejDims egne værdier anvendt, og tykkelsen varierer med "
                    "Eu. NÆ10 er dimensioneringstrafikken over 20 år."
                )
            st.caption(
                "Se Hjælp afsnit 7 for yderligere detaljer om datagrundlag og forbehold."
            )


def _materiale_editor(lagtype: str, materialer: list[dict], noegle: str):
    """Redigerbar tabel for én lagtype, jf. afsnit 5b.

    Friktionsvinklen står i én kolonne. Standardværdierne er fastlagt i
    _standard_materialer() og gendannes med Nulstil til standard; hvilke
    materialer der afviger, fremgår af meddelelsen øverst på siden.
    """
    import pandas as pd

    raekker = [m for m in materialer if m.get("lagtype") == lagtype]
    df = pd.DataFrame(
        raekker,
        columns=[
            "navn", "phi", "max_korn",
            "krav_maskestoerrelse_mm", "anvendelse",
        ],
    )
    redigeret = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "navn": st.column_config.TextColumn("Materiale", required=True),
            "phi": st.column_config.NumberColumn(
                "φ (°)",
                help=(
                    "Materialets friktionsvinkel. Værdien kan tilpasses "
                    "lokalt; standardværdien gendannes med Nulstil til "
                    "standard."
                ),
                min_value=20, max_value=60, step=1,
                format="%d", required=True,
            ),
            "max_korn": st.column_config.NumberColumn(
                "Maks. korn (mm)", min_value=0, max_value=500, step=1,
                format="%d", required=False,
            ),
            "krav_maskestoerrelse_mm": st.column_config.NumberColumn(
                "Krav til geonet — maskestørrelse (mm)",
                help=(
                    "Minimum kvadratisk maskestørrelse i mm som materialet "
                    "kræver af et biaksialt geonet. Sammenlignes kun med "
                    "biaksiale net i Brugerdefineret-tilstand."
                ),
                min_value=0, max_value=500, step=5,
                format="%d", required=False,
            ),
            "anvendelse": st.column_config.TextColumn("Bemærkning"),
        },
        key=noegle,
    )
    ud = []
    for r in redigeret.to_dict("records"):
        r["lagtype"] = lagtype
        ud.append(r)
    return ud


def _afvigende_materialer(materialer: list[dict]) -> list[str]:
    """Materialer, hvis friktionsvinkel afviger fra standarden."""
    std = {m["navn"]: m["phi"] for m in _standard_materialer()}
    return [
        m["navn"] for m in materialer
        if m["navn"] in std and m["phi"] != std[m["navn"]]
    ]


def render_materialer() -> None:
    """Materialeopslaget som nummererede trin, jf. afsnit 5b."""
    ui.sidehoved(
        "Materialer",
        "Friktionsvinkler og kornstørrelser anvendt i dimensioneringen. "
        "Værdierne kan tilpasses; ændringer gemmes lokalt og indgår i "
        "beregningen i Brugerdefineret-tilstand.",
    )

    materialer = st.session_state.get("materialer", [])
    afvigende = _afvigende_materialer(materialer)
    if afvigende:
        ui.besked(
            "Friktionsvinklen afviger fra standarden for "
            f"<b>{html.escape(', '.join(afvigende))}</b>. Brug "
            "<i>Nulstil til standard</i> for at gendanne værdierne.",
            "advarsel",
        )

    with ui.trin_kort(1, "Bærelagsmaterialer") as t1:
        baerelag = _materiale_editor("Bærelag", materialer, "mat_editor_baere")
        t1.opsummering = f"{len(baerelag)} materialer"

    with ui.trin_kort(2, "Bundsikringsmaterialer") as t2:
        bundsikring = _materiale_editor(
            "Bundsikring", materialer, "mat_editor_bund"
        )
        t2.opsummering = f"{len(bundsikring)} materialer"

    kol_a, kol_b, _ = st.columns([1, 1, 3])
    with kol_a:
        if st.button("Nulstil til standard", icon=":material/refresh:",
                     width="stretch", type="secondary"):
            slet_json_og_nulstil()
            st.session_state["materialer"] = indlaes_materialer()
            st.session_state.pop("mat_editor_baere", None)
            st.session_state.pop("mat_editor_bund", None)
            st.rerun()

    ny_liste = _normaliser_materialer(baerelag + bundsikring)
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

    ui.sidehoved(
        "Rapport",
        "Dokumentation af beregningen til projektmateriale. Rapporten samler "
        "forudsætninger, resultat og udførelseskrav i ét dokument i Word og "
        "PDF. Standardteksterne kan redigeres pr. rapport.",
    )

    sd = st.session_state.get("sidste_dim")
    if not sd or not sd.get("geonet"):
        st.info(
            "Der skal først foretages en dimensionering med et specifikt "
            "valgt geonet, før rapporten kan genereres.\n\n"
            "Dimensioneringen udføres under **Dimensionering → "
            "Brugerdefineret** med visningen **Vælg specifikt produkt**."
        )
        if st.button("Gå til Dimensionering", type="primary"):
            st.session_state.aktiv_side = "dimensionering"
            st.rerun()
        return

    # Opsummering af det aktuelle beregningsgrundlag
    if sd.get("grundlag_type") == "trafikklasse":
        grundlag_txt = (
            f"Trafikklasse {sd.get('t_klasse', '—')} "
            f"(Eo_ækv = {ui.mpa(sd['eo'])})"
        )
    else:
        grundlag_txt = f"Klasse {sd['valgt_klasse']} (Eo = {ui.mpa(sd['eo'])})"
    st.success(
        f"**Rapport baseret på:**  Eu = {ui.mpa(sd['eu'])}  ·  "
        f"{grundlag_txt}  ·  "
        f"Produkt: **{sd['geonet_navn']}**  ·  φ = {ui.grader(sd['phi'])}"
    )

    with ui.trin_kort(1, "Sagsoplysninger") as t1:
        # --- A. Metadata --------------------------------------------------------
        # Projekt-oplysningerne huskes til næste gang på disk (undtagen dato, der
        # som udgangspunkt altid er dags dato).
        if "rapport_metadata" not in st.session_state:
            st.session_state["rapport_metadata"] = indlaes_rapport_metadata()
        md_state = st.session_state["rapport_metadata"]
        # Migrér gamle session-states der mangler nyere felter
        md_state.setdefault("sagsbehandler_mail", "")
        md_state.setdefault("kontrol", "")

        kol_a_titel, kol_a_reset = st.columns([4, 1])
        with kol_a_titel:
            st.caption(
                "Felterne huskes automatisk til næste gang. "
                "Brug **Nulstil felter** for at rydde dem."
            )
        with kol_a_reset:
            if st.button(
                "Nulstil felter", icon=":material/refresh:",
                key="rap_nulstil_felter", width="stretch",
                help="Rydder alle projekt-oplysninger og glemmer de gemte værdier.",
            ):
                st.session_state["rapport_metadata"] = _standard_rapport_metadata()
                # Sæt widget-nøglerne eksplicit til den tomme værdi i stedet for
                # blot at fjerne dem: browseren sender ellers de gamle værdier
                # tilbage ved næste kørsel, så felterne kom til at stå urørte.
                # En værdi lagt i session_state før widget'en oprettes vinder.
                for _wk in (
                    "rap_projekt", "rap_omfang", "rap_sagsbehandler",
                    "rap_sagsbehandler_mail", "rap_kontrol", "rap_beskrivelse",
                    "rap_udfoeres_for",
                ):
                    st.session_state[_wk] = ""
                st.session_state["rap_dato"] = _date.today()
                st.session_state.pop("_rapport_metadata_gemt", None)
                slet_rapport_metadata_json()
                st.rerun()

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
            md_state["kontrol"] = st.text_input(
                "Kontrol", value=md_state.get("kontrol", ""),
                key="rap_kontrol",
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

        # Gem oplysningerne på disk, når de ændrer sig, så de huskes til næste gang.
        _md_disk = {f: md_state.get(f, "") for f in _RAPPORT_METADATA_DISK_FELTER}
        if _md_disk != st.session_state.get("_rapport_metadata_gemt"):
            gem_rapport_metadata(md_state)
            st.session_state["_rapport_metadata_gemt"] = _md_disk

        st.divider()
        t1.opsummering = " · ".join(x for x in (md_state.get("projekt"), md_state.get("sagsnummer")) if x) or "Ikke udfyldt"

    with ui.trin_kort(2, "Indhold") as t2:
        # --- B. Redigerbare skabelon-sektioner ---------------------------------
        st.caption(
            "Standardteksterne fra BG Byggros' eksempelrapport er forudfyldt. "
            "Teksterne kan redigeres pr. rapport eller nulstilles til standard."
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
                    if st.button("Nulstil", icon=":material/refresh:", key=f"rap_reset_{nøgle}",
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
        t2.opsummering = f"{len(rapport_mod.SECTION_KEYS)} afsnit"

    with ui.trin_kort(3, "Gennemsyn") as t3:
        # --- C. Visualiseringsvalg + preview -----------------------------------

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
                "Tegner designkurverne (ustabiliseret, 1 lag og 2 lag) tilpasset "
                "de valgte materialer og det valgte geonet, med den indtastede "
                "opbygning og E-værdi som referencer. Formen svarer til de "
                "oprindelige designdiagrammer."
                if designdiagram_muligt
                else "Vælg et specifikt geonet under Dimensionering for at få "
                     "kurverne med produktets net-korrektion."
            ),
        )
        kol_dd1, kol_dd2 = st.columns(2)
        with kol_dd1:
            vis_dd_din_prik = st.checkbox(
                "Vis 'Indtastet opbygning'-prik i designdiagram",
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
        # Statusteksten (for lidt / i overskud) giver kun mening sammen med linjen.
        status_indtastet_ref = (
            indtastet_total_rap if vis_indtastet_aktiv else None
        )

        # Mellemregningen bag den optimale tykkelse. Dimensioneringens
        # beregningsresultat bærer ikke intervallets nedre korrektion; den
        # aflæses af geonettet og føjes til, så noten kan dannes samme sted
        # som på dimensioneringssiden.
        _interval_rap = (sd.get("geonet") or {}).get("korrektion_interval")

        def _optimal_note_rap(res: dict, t_best: float | None) -> str | None:
            if not _interval_rap or t_best is None:
                return None
            return _optimal_note(
                {
                    **res,
                    "t_armeret_mm_min": t_best,
                    "korrektion_min": _interval_rap[0],
                },
                net_navn=sd.get("geonet_navn"),
                phi=phi_dim,
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
                status_indtastet_ref, t_1, sd.get("t_1_lag_best_mm"),
            )
            snit_liste.append(rapport_mod.Snit(
                titel="1 lag geonet", t_baerelag_mm=t_1,
                geonet_y_fracs=fracs_1,
                sub_lag=sub_red_1 if brug_sub_1 else None,
                best_case_mm=sd.get("t_1_lag_best_mm"),
                best_case_note=_optimal_note_rap(
                    res_1, sd.get("t_1_lag_best_mm")
                ),
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
                status_indtastet_ref, t_2, sd.get("t_2_lag_best_mm"),
            )
            snit_liste.append(rapport_mod.Snit(
                titel="2 lag geonet", t_baerelag_mm=t_2,
                geonet_y_fracs=fracs_2,
                sub_lag=sub_red_2 if brug_sub_2 else None,
                best_case_mm=sd.get("t_2_lag_best_mm"),
                best_case_note=_optimal_note_rap(
                    res_2, sd.get("t_2_lag_best_mm")
                ),
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
                eu=sd["eu"], snit_liste=snit_liste,
                geonet_label=geonet_label,
                materialer=materialer_dim,
                reference_mm=t_indtastet_for_snit,
            )
            with ui.kort(
                "Opbygning",
                "Snit i samme lodrette skala · forhåndsvisning fra dimensioneringen",
            ):
                ui.snit(
                    snit_til_kolonner(snit_liste, materialer_dim, sd["eu"]),
                    reference_mm=t_indtastet_for_snit,
                    geonet_navn=geonet_label,
                )

        # --- Personligt designdiagram (preview + rapport-PNG) ----------------
        designdiagram_png: bytes | None = None
        if vis_designdiagram and designdiagram_muligt:
            try:
                designdiagram_png = rapport_mod.render_personligt_designdiagram_png(
                    eu=float(sd["eu"]),
                    eo=float(sd["eo"]),
                    klasse=sd.get("valgt_klasse"),
                    grundlag_label=(
                        f"Trafikklasse {sd.get('t_klasse')}"
                        if sd.get("grundlag_type") == "trafikklasse" else None
                    ),
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
                diagram_p1 = {
                    **res_1,
                    "t_armeret_mm_min": sd.get("t_1_lag_best_mm"),
                } if t_1 is not None else None
                diagram_p2 = {
                    **res_2,
                    "t_armeret_mm_min": sd.get("t_2_lag_best_mm"),
                } if t_2 is not None else None
                with ui.kort(
                    "Designdiagram",
                    f"Eo = {ui.mpa(sd['eo'])} · {grundlag_txt} · "
                    f"φ = {ui.grader(sd.get('phi', PHI_BASIS))} · "
                    f"{sd.get('geonet_navn') or 'referencenet'}",
                ):
                    _tegn_designdiagram(
                        float(sd["eu"]),
                        float(sd["eo"]),
                        float(sd.get("phi", PHI_BASIS)),
                        geonet,
                        _aktiv_t_basis_table(),
                        (
                            indtastet_total_rap
                            if har_indtastet_rap and vis_dd_din_prik else None
                        ),
                        diagram_p1 if vis_dd_lag_prikker else None,
                        diagram_p2 if vis_dd_lag_prikker else None,
                    )
            except Exception as e:
                st.warning(f"Kunne ikke generere designdiagram: {e}")
                designdiagram_png = None

        st.divider()
        t3.opsummering = "Sådan bliver siderne"

    with ui.trin_kort(4, "Generér") as t4:
        # --- D. Generér rapport -----------------------------------------------

        rapport_data = {
            "metadata": dict(md_state),
            "dim": sd,
            "tekster": dict(tekster_state),
            "visualisering_png": visu_png,
            "designdiagram_png": designdiagram_png,
            "valg": {},
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
            "Generér rapport",
            icon=":material/description:",
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
                    "Word-filen kan hentes herunder og konverteres via 'Gem som "
                    "PDF' i Word."
                )

            if genereret.get("pdf_bytes"):
                kol_d1, kol_d2 = st.columns(2)
            else:
                kol_d1 = st.container()
                kol_d2 = None

            with kol_d1:
                st.download_button(
                    "Hent som Word (.docx)",
                    icon=":material/download:",
                    data=genereret["docx_bytes"],
                    file_name=f"{genereret['filnavn_base']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch",
                )
            if kol_d2 is not None:
                with kol_d2:
                    st.download_button(
                        "Hent som PDF (.pdf)",
                        icon=":material/download:",
                        data=genereret["pdf_bytes"],
                        file_name=f"{genereret['filnavn_base']}.pdf",
                        mime="application/pdf",
                        width="stretch",
                    )
        t4.opsummering = ""

# ===========================================================================
# Top-level layout — sidebar + routing
# ===========================================================================

# Nøgle-præfikser for de input-widgets i Dimensionering hvis værdi skal
# overleve, når man skifter side i sidebaren. Streamlit sletter ellers en
# widgets værdi fra session_state, så snart widgeten ikke længere rendres —
# så alle valg ville blive nulstillet ved navigation. Ved at "røre" nøglerne
# øverst i hvert run (før nogen widget oprettes) bevares værdierne.
#
# BEMÆRK: knap-widgets (st.button) må IKKE sættes via session_state — det
# kaster en undtagelse. Deres nøgler (…_kl_N belastningsklasse, …_tk_TX
# trafikklasse) er derfor bevidst udeladt.
_BEVAR_DIM_PRAEFIKSER: tuple[str, ...] = (
    "tilstand",
    "std_eu_", "std_cv_", "std_grundlag", "std_valgt_klasse", "std_valgt_tklasse",
    "bd_eu_", "bd_cv_", "bd_grundlag", "bd_valgt_klasse", "bd_valgt_tklasse",
    "bd_antal_lag", "bd_mat_", "bd_phi_", "bd_korn_", "bd_lt_", "bd_t_",
    "bd_visning", "bd_geonet", "bd_kor_man", "bd_dd_vis_",
    "opbygning_geonet_valg",
)


def _bevar_dimensionering_state() -> None:
    """Bevar Dimensionerings-input på tværs af sidenavigation.

    Kaldes øverst i hvert script-run, før nogen widget oprettes.
    """
    for nøgle in list(st.session_state.keys()):
        if nøgle.startswith(_BEVAR_DIM_PRAEFIKSER):
            st.session_state[nøgle] = st.session_state[nøgle]


# Felter, Nulstil-knappen i topbjælken rydder, pr. side. Nøglerne slettes fra
# session_state, så widgets genoprettes med deres standardværdier.
# Rapportsiden har sin egen nulstilling, som også rydder de gemte
# projektoplysninger, og indgår derfor ikke her.
_NULSTIL_PRAEFIKSER: dict[str, tuple[str, ...]] = {
    "dimensionering": ("std_", "bd_", "opbygning_geonet_valg"),
}


def _nulstil_aktiv_side(side: str) -> None:
    """Ryd inputfelterne på den aktive side, jf. Nulstil i topbjælken."""
    praefikser = _NULSTIL_PRAEFIKSER.get(side)
    if not praefikser:
        return
    for nøgle in list(st.session_state.keys()):
        if nøgle.startswith(praefikser):
            del st.session_state[nøgle]


# Bevar input på tværs af sidenavigation — SKAL køre før nogen widget oprettes.
_bevar_dimensionering_state()

aktiv_side = render_sidebar()

# Topbjælkens to knapper aflæses her, hvor den aktive side er kendt.
if st.session_state.get("bg_gaa_til_rapport"):
    st.session_state.aktiv_side = "rapport"
    st.rerun()
if st.session_state.get("bg_nulstil"):
    _nulstil_aktiv_side(aktiv_side)
    st.rerun()

if aktiv_side == "dimensionering":
    # Flow A: dimensioneringen føres igennem som nummererede trin på én side,
    # og resultatet står som en samlet blok nedenunder. Sidehovedet bærer
    # sidens navn til venstre og tilstandsvalget til højre.
    kol_titel, kol_tilstand = st.columns([3, 1], vertical_alignment="bottom")
    with kol_titel:
        st.markdown(
            '<div class="bg-sidehoved"><h1>Dimensionering</h1>'
            "<p>Bærelagstykkelse med og uden geonetarmering. Grundlaget er "
            "BG Byggros' designmanualer til Tensar og GS-GRID samt interne "
            "forsøgsdata.</p></div>",
            unsafe_allow_html=True,
        )
    with kol_tilstand:
        _tilstand_vaelger()

    if st.session_state.get("tilstand", "Standard") == "Standard":
        render_standard()
    else:
        render_brugerdefineret()

elif aktiv_side == "materialer":
    render_materialer()

elif aktiv_side == "geonet_database":
    render_geonet_database()

elif aktiv_side == "designdiagrammer":
    render_designdiagrammer()

elif aktiv_side == "trafikklasse_korrelation":
    render_trafikklasse_korrelation()

elif aktiv_side == "hjaelp":
    render_hjaelp()

elif aktiv_side == "rapport":
    render_rapport()
