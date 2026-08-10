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

INFO_VISUALISERING_MD = """**Sådan læses søjlerne**

**Indtastet opbygning** viser de indtastede lagtykkelser.

**Ustabiliseret basistykkelse (φ-korrigeret)** er den ustabiliserede
lagtykkelse fra designdiagrammet, bestemt ud fra Eu og Eo og korrigeret for
den vægtede friktionsvinkel:

```
T_krav = T_basis × (1 + k_φ)
```

Materialeforholdet fra den indtastede opbygning bevares, og lagtykkelsen
fordeles proportionalt på lagene. Værdierne kan derfor overstige de
indtastede. Differencen er angivet som "X mm for lidt" under søjlen.

**1 lag / 2 lag geonet** viser den stabiliserede lagtykkelse med samme
proportionale lagfordeling. Ved 2 lag placeres det øverste geonet ved den
reducerede materialegrænse.
"""


INFO_DESIGNDIAGRAM_MD = """**Sådan dannes diagrammet**

Kurverne er dannet på grundlag af designdiagram-tabellen ved det viste **Eo**.
Tabellen angiver basis-lagtykkelsen (cm) for hver Eu-række og for hver
opbygning (ustabiliseret, 1 lag og 2 lag geonet). Rammer Eo ikke en af
tabellens søjler (30, 45, 60, 80, 120 og 150 MPa), bestemmes værdien ved
lineær interpolation mellem de to nærmeste søjler. Dette er altid tilfældet
ved dimensionering efter trafikklasse, hvor Eo er den tilbageberegnede
**ækvivalente Eo**.

Basis-lagtykkelsen korrigeres med en samlet faktor:

```
T   = T_basis × (1 + k_φ + k_net)
k_φ = −0,02 × (φ − 37°)
```

hvor:

- **k_φ** = korrektion for friktionsvinklen i de valgte materialelag.
  Anvendes på samtlige tre kurver.
- **k_net** = korrektion for det valgte geonet. Værdien er 0 for
  referencenettet og negativ for net med højere effektivitet. Anvendes alene
  på de armerede kurver, idet den ustabiliserede opbygning ikke indeholder
  geonet.

For produkter med et korrektionsinterval, eksempelvis NX750 og NX850, tegnes
både den konservative og den optimale kurve med et tonet bånd imellem.

**Punkter i diagrammet:**

- Det røde punkt "Indtastet opbygning" angiver den indtastede bærelagstykkelse
  ved den valgte E-værdi.
- Punkterne for 1 og 2 lag geonet angiver den krævede lagtykkelse ved samme
  E-værdi for det valgte geonet. Udfyldt markering angiver den konservative
  værdi, åben markering den optimale. Åben markering forekommer alene for
  produkter med korrektionsinterval.
"""


def _vis_billede_med_info(
    png: bytes,
    info_md: str,
    *,
    caption: str | None = None,
    use_container_width: bool = False,
) -> None:
    """Vis PNG med Streamlits grå ⍰-hjælpeikon ved siden af.

    Ikonet er st.markdown(help=...) — samme udseende og opførsel som
    hjælpeikonet på widgets. Falder tilbage til et popover, hvis
    den installerede Streamlit ikke understøtter help på st.markdown.
    """
    col_img, col_info = st.columns([0.95, 0.05])
    with col_img:
        kwargs = {"width": "stretch" if use_container_width else "content"}
        if caption:
            st.image(png, caption=caption, **kwargs)
        else:
            st.image(png, **kwargs)
    with col_info:
        try:
            st.markdown("", help=info_md)
        except TypeError:
            popover = getattr(st, "popover", None)
            if callable(popover):
                with popover("Forklaring", width="stretch"):
                    st.markdown(info_md)
            else:
                with st.expander("Forklaring", expanded=False):
                    st.markdown(info_md)


def _vis_opbygning_med_info(png: bytes, *, caption: str | None = None) -> None:
    """Vis opbygnings-PNG med hjælpeikon (INFO_VISUALISERING_MD)."""
    _vis_billede_med_info(png, INFO_VISUALISERING_MD, caption=caption)


def _vis_designdiagram_med_info(
    png: bytes,
    *,
    caption: str | None = None,
    use_container_width: bool = False,
) -> None:
    """Vis designdiagram-PNG med hjælpeikon (INFO_DESIGNDIAGRAM_MD)."""
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


def input_underbund(key_prefix: str, kompakt: bool = False) -> float:
    """Render Underbund (Eu eller Cv → Eu). Returnerer Eu i MPa.

    kompakt=True anvendes i inputkolonnen, hvor bredden ikke rummer
    opslagstabellen ved siden af slideren; tabellen lægges da i et popover.
    """
    ui.etiket("Underbund") if kompakt else st.subheader("Underbund")
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
        st.caption(f"Valgt **Eu = {ui.mpa(eu)}**")
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
            st.markdown(tabel_html, unsafe_allow_html=True)
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
    key_prefix: str, kompakt: bool = False
) -> tuple[int, dict, float]:
    """Render Belastningsklasse som en vælger med de seks klasser.

    Returnerer (klasse, info, eo). kompakt=True lægger designdiagrammet i et
    popover, idet inputkolonnen ikke er bred nok til at vise det ved siden af.
    """
    ui.etiket("Belastningsklasse") if kompakt else st.subheader("Belastningsklasse")

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
    st.caption(
        f"**Klasse {valgt}** · {info['belastning']} · "
        f"Eo = {ui.mpa(eo)} · _{info['anvendelse']}_"
    )

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


_TRAFIK_GRUNDLAG_MD = """
Grundlaget bygger på to uafhængige, empiriske datasæt:

1. **VejDim-kørslerne** fastlægger den ubundne lagtykkelse (stabilgrus og
   bundsikring), en given trafikklasse kræver ved en given underbund.
2. **Designdiagrammerne** (feltforsøg fra GS-GRID og Tensar) fastlægger den
   reduktion af lagtykkelsen, et geonet medfører.

Datasættene sammenkædes ved tilbageberegning: der bestemmes den diagramkurve,
hvis ustabiliserede lagtykkelse ved samme underbunds-E-værdi svarer til den
lagtykkelse, VejDim fastlægger. Kurven benævnes den **ækvivalente Eo**.
Værdien er en indeksværdi, der angiver opslagspunktet i diagrammet, og
udtrykker ikke et krav til overflademodulet. Reduktionen aflæses i punktet og
er dermed designdiagrammets egen, feltbestemte værdi. Der foretages ingen
omregning mellem de to metoders dimensioneringskriterier.

Grundlaget er rent bæreevnemæssigt og tager ikke højde for underbundes frostfarlighed.
Kravene til frostsikring og koblingshøjde bør kontrolleres særskilt, jf.
Vejdirektoratets dimensioneringshåndbog afsnit 5.1 og 5.3. Metode, datagrundlag og forbehold er beskrevet
under **Trafikklasse-korrelation** i menuen.
"""


def _vis_korrelationstabel(
    korr: dict,
    *,
    valgt_t: str | None = None,
    eu: float | None = None,
    key_prefix: str = "",
) -> None:
    """Vis Eo_ækv-tabellen (T × Eu) med den aktuelle celle markeret.

    Bruges både i dimensioneringen (så man kan se hele korrelationen mens man
    vælger trafikklasse) og i Trafikklasse-sektionen. valgt_t/eu markerer den række og
    celle, dimensioneringen aktuelt slår op i.
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

    st.markdown("**Ækvivalent Eo (MPa) — hele korrelationstabellen**")
    st.dataframe(df.style.apply(_markering, axis=None), width="content")
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


def input_trafikklasse(key_prefix: str, eu: float, kompakt: bool = False) -> dict:
    """Render Trafikklasse-vælger (T1–T6) + udledt ækvivalent Eo og zone.

    Bruger korrelationen KORRELATION_T_EO (dokumenteret bro fra VejDim til
    designdiagrammerne). Returnerer en grundlag-dict — se input_grundlag().

    kompakt=True lægger korrelationstabellen i et popover, idet inputkolonnen
    ikke er bred nok til at vise den ved siden af vælgeren.
    """
    if kompakt:
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

    # Nøgletal efter håndbogens Figur 4.1, jf. data.trafikklasse_noegletal.
    st.markdown(
        f'<div style="margin:0.2rem 0 0.6rem">'
        f'<div style="font-weight:700;margin-bottom:2px">'
        f'{format_trafikklasse(valgt_t)}</div>'
        + _noegletal_tabel_html(
            trafikklasse_noegletal(valgt_t), dæmpet=True
        )
        + '<div style="font-size:0.76rem;color:#777;margin-top:4px">'
        'Værdierne er gengivet efter håndbogens Figur 4.1. Den typiske '
        'anvendelse er vejledende og indgår ikke i håndbogen.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if zone == "ok":
        tal = _trafik_kobling_tal(eu, eo_aekv, _aktiv_t_basis_table())
        # Nabokurverne, Eo_ækv er interpoleret imellem. Falder Eo_ækv
        # præcis på en kolonne, er de to ens, og der vises kun den ene.
        if tal["kl_lav"] != tal["kl_hoej"]:
            klasse_txt = (
                f"{tal['kl_lav']} (Eo = {tal['eo_lav']} MPa) og "
                f"{tal['kl_hoej']} (Eo = {tal['eo_hoej']} MPa)"
            )
        else:
            klasse_txt = f"{tal['kl_lav']} (Eo = {tal['eo_lav']} MPa)"
        # Ligger Eu mellem to kørte VejDim-punkter, er tykkelseskravet —
        # og dermed Eo_ækv — interpoleret i log(Eu). Det markeres, så
        # tallet ikke forveksles med en aflæst kørsel. Markeringen er en
        # mellemregning og vises alene, når kontakten er slået til.
        trin = _eo_aekv_trin_tal(valgt_t, eu, _aktiv_t_basis_table())
        interp_txt = (
            f' <span style="font-weight:400;color:{ui.FARVE["ink_45"]}">'
            f'(interpoleret)</span>'
            if ui.mellemregninger() and trin and not trin["trin1"]["direkte"]
            else ""
        )
        raekker = [
            ("Tykkelseskrav til ubundet opbygning fra VejDim",
             f"{ui.mm(tal['t_krav_mm'])}{interp_txt}"
             if tal["t_krav_mm"] is not None else "—"),
            ("Nærmeste belastningsklasser", klasse_txt),
            ("Ækvivalent Eo-kurve", f"{ui.mpa(eo_aekv)}{interp_txt}"),
        ]
        ui.besked(
            f"<b>{valgt_t} ved Eu = {ui.mpa(eu)}:</b>"
            f'<hr style="margin:5px 0 4px;border:none;'
            f'border-top:1px solid {ui.FARVE["linje"]}">'
            + _noegletal_tabel_html(raekker),
            "info",
        )
    elif zone == "under":
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
    else:  # udenfor
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

    with st.expander("Om trafikklasse-grundlaget"):
        st.markdown(_TRAFIK_GRUNDLAG_MD)

    return {
        "type": "trafikklasse",
        "eo": eo_aekv,
        "valgt_klasse": naermeste,
        "t_klasse": valgt_t,
        "eo_aekv": eo_aekv,
        "zone": zone,
        "info": TRAFIKKLASSER[valgt_t],
    }


def input_grundlag(key_prefix: str, eu: float, kompakt: bool = False) -> dict:
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
    if kompakt:
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
        valgt_klasse, info, eo = input_belastning(key_prefix, kompakt=kompakt)
        return {
            "type": "belastningsklasse",
            "eo": eo,
            "valgt_klasse": valgt_klasse,
            "t_klasse": None,
            "eo_aekv": None,
            "zone": None,
            "info": info,
        }

    return input_trafikklasse(key_prefix, eu, kompakt=kompakt)


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


def _eo_aekv_tooltips(
    t_klasse: str,
    eu: float,
    eo_aekv: float,
    t_basis_table: dict,
    t_krav_mm: float | None = None,
    ref_1: dict | None = None,
    ref_2: dict | None = None,
    phi: float = PHI_BASIS,
    geonet: dict | None = None,
) -> dict[str, str]:
    """Regnestykket bag Eo_ækv, opdelt som tooltip-tekst til hver flow-boks.

    Nøglerne svarer til boksene: "valg", "krav", "driftspunkt", "geonet".
    Trin 1 ("krav") skifter form, alt efter om Eu rammer et kørt punkt
    (direkte opslag) eller ligger imellem to (interpolation i log(Eu)).
    Tomme strenge, hvor der ikke er noget at regne på.
    """
    tips = {"valg": "", "krav": "", "driftspunkt": "", "materiale": "",
            "geonet": ""}
    eu_txt = _dk_num(eu, ".0f")
    tal = _eo_aekv_trin_tal(t_klasse, eu, t_basis_table)
    if not tal:
        return tips
    t1, t2 = tal["trin1"], tal["trin2"]
    ub = t1["ubundet_mm"]
    # Et interpoleret krav har decimaler — vis dem, så trin 2's brøk går op.
    ub_txt = _dk_num(ub, ".0f" if abs(ub - round(ub)) < 0.05 else ".1f")

    # --- Boks 1: valgt grundlag ------------------------------------------
    kendte = ", ".join(str(p) for p in t1.get("kendte", []))
    tips["valg"] = (
        f"Trafikklasse {t_klasse} ved en underbund med E-værdi "
        f"Eu = {eu_txt} MPa.\n\n"
        f"For denne trafikklasse er der udført VejDim-kørsler ved "
        f"Eu = {kendte} MPa. "
        + (
            f"Eu = {eu_txt} MPa er et af de kørte punkter, og lagtykkelsen "
            f"aflæses direkte."
            if t1["direkte"]
            else f"Eu = {eu_txt} MPa ligger mellem to kørte punkter, og "
                 f"lagtykkelsen bestemmes ved interpolation."
        )
    )

    # --- Boks 2: trin 1, den ubundne lagtykkelse fra VejDim --------------
    if t1["direkte"]:
        aflaes = (
            f"bundsikring {_dk_num(t1['bl'], '.0f')} mm + "
            f"stabilgrus {_dk_num(t1['sg'], '.0f')} mm = {ub_txt} mm"
            if t1.get("sg") is not None else f"{ub_txt} mm"
        )
        tips["krav"] = (
            f"1 UBUNDEN LAGTYKKELSE\n\n"
            f"Eu = {eu_txt} MPa er et kørt punkt, og lagtykkelsen aflæses "
            f"direkte i kørselstabellen:\n\n"
            f"    {t_klasse} / Eu {t1['eu_punkt']}:  {aflaes}"
        )
    else:
        tips["krav"] = (
            f"1 UBUNDEN LAGTYKKELSE\n\n"
            f"Eu = {eu_txt} MPa ligger mellem to kørte punkter. Lagtykkelsen "
            f"bestemmes ved lineær interpolation i log(Eu), idet lagtykkelsen "
            f"aftager tilnærmelsesvis retlinet med log(Eu):\n\n"
            f"    {t_klasse} / Eu {t1['lav']}:  "
            f"{_dk_num(t1['t_lav'], '.0f')} mm   (kørt punkt)\n"
            f"    {t_klasse} / Eu {t1['hoej']}:  "
            f"{_dk_num(t1['t_hoej'], '.0f')} mm   (kørt punkt)\n\n"
            f"    frac = (ln {eu_txt} − ln {t1['lav']}) / "
            f"(ln {t1['hoej']} − ln {t1['lav']}) = {_dk_num(t1['frac'], '.3f')}\n"
            f"    krav = {_dk_num(t1['t_lav'], '.0f')} + "
            f"{_dk_num(t1['frac'], '.3f')} × ({_dk_num(t1['t_hoej'], '.0f')} − "
            f"{_dk_num(t1['t_lav'], '.0f')}) = {ub_txt} mm"
        )

    # --- Boks 3: trin 2, tilbageberegning i diagrammet -------------------
    if "eo_aekv" in t2:
        kurve_linjer = "\n".join(
            f"    klasse {eo_til_klasse(eo) or '–'}  ·  Eo {eo:>3}  →  "
            f"{_dk_num(mm, '.0f'):>5} mm"
            + ("   ←" if eo in (t2["eo_lav"], t2["eo_hoej"]) else "")
            for eo, mm in sorted(t2["kurver"])
        )
        kl_lav = eo_til_klasse(t2["eo_lav"])
        kl_hoej = eo_til_klasse(t2["eo_hoej"])
        tips["driftspunkt"] = (
            f"2 ÆKVIVALENT Eo\n\n"
            f"Der bestemmes den Eo-kurve, hvis ustabiliserede lagtykkelse ved "
            f"Eu = {eu_txt} MPa svarer til {ub_txt} mm. De ustabiliserede "
            f"lagtykkelser ved denne E-værdi er:\n\n"
            f"{kurve_linjer}\n\n"
            f"Værdien ligger mellem kurverne for klasse {kl_lav} og "
            f"{kl_hoej}, og der interpoleres lineært mellem disse:\n\n"
            f"    f      = ({ub_txt} − {_dk_num(t2['t_lav'], '.0f')}) / "
            f"({_dk_num(t2['t_hoej'], '.0f')} − {_dk_num(t2['t_lav'], '.0f')}) "
            f"= {_dk_num(t2['frac'], '.3f')}\n"
            f"    Eo_ækv = {t2['eo_lav']} + {_dk_num(t2['frac'], '.3f')} × "
            f"({t2['eo_hoej']} − {t2['eo_lav']}) = "
            f"{_dk_num(t2['eo_aekv'], '.1f')} MPa  →  {_dk_num(eo_aekv, '.0f')}\n\n"
            f"Den ækvivalente Eo er en indeksværdi, der angiver opslagspunktet "
            f"i diagrammet. Den udtrykker ikke et krav til underbunden, hvis "
            f"E-værdi fortsat er {eu_txt} MPa. Ligger lagtykkelsen uden for "
            f"rækkens yderste kurver, kan opslaget ikke foretages, og cellen "
            f"angives som under eller over."
        )

    # --- Materiale-boksen: φ-korrektionen alene -------------------------
    phi_kor_v = K_PHI * (phi - PHI_BASIS)
    t_uarm_kor = (ref_1 or ref_2 or {}).get("t_uarmeret_phi_kor_mm")
    if abs(phi_kor_v) > 1e-9 and t_uarm_kor and t_krav_mm:
        tips["materiale"] = (
            f"KORREKTION FOR FRIKTIONSVINKEL\n\n"
            f"Afsnit 1 og 2 ovenfor angiver diagrammets basisværdier ved "
            f"φ = {_dk_num(PHI_BASIS, '.1f')}°. Værdierne holdes ukorrigerede, "
            f"idet den ækvivalente Eo skal være uafhængig af materialevalget. "
            f"VejDims krav til trafikklassen afhænger ikke af de valgte "
            f"ubundne materialer.\n\n"
            f"Herefter regnes med de valgte materialer "
            f"(φ = {_dk_num(phi, '.1f')}°):\n\n"
            f"    k_φ = {_dk_num(K_PHI, '.2f')} × "
            f"({_dk_num(phi, '.1f')} − {_dk_num(PHI_BASIS, '.1f')}) "
            f"= {_dk_num(phi_kor_v, '.3f')}\n"
            f"    T   = {_dk_num(t_krav_mm, '.0f')} × "
            f"{_dk_num(1 + phi_kor_v, '.3f')} = {_dk_num(t_uarm_kor, '.0f')} mm\n\n"
            f"Værdien svarer til designdiagrammets ustabiliserede kurve ved "
            f"Eu = {eu_txt} MPa og udgør referencen for geonet-reduktionerne "
            f"nedenfor."
        )

    # --- Boks 4/5: geonet-reduktionen -----------------------------------
    t3 = tal["trin3"]
    if t_krav_mm and t3 and "eo_aekv" in t2:
        kl_lav = eo_til_klasse(t2["eo_lav"])
        kl_hoej = eo_til_klasse(t2["eo_hoej"])
        pct = _dk_num(t2["frac"] * 100, ".1f")
        N, K = 14, 12          # bredde på navne- og talkolonner

        def _linje(navn: str, a, b, c) -> str:
            return (f"    {navn:<{N}}{a:>{K}}{b:>{K}}{c:>{K}}")

        raekker = [
            _linje("", f"klasse {kl_lav}", f"klasse {kl_hoej}", f"{pct} % inde"),
            _linje("uarmeret", _dk_num(t2["t_lav"], ".0f"),
                   _dk_num(t2["t_hoej"], ".0f"), _dk_num(t_krav_mm, ".0f")),
        ]
        for lag, navn in (("1_lag", "1 lag geonet"), ("2_lag", "2 lag geonet")):
            if lag in t3:
                raekker.append(_linje(
                    navn, _dk_num(t3[lag]["lav"], ".0f"),
                    _dk_num(t3[lag]["hoej"], ".0f"),
                    _dk_num(t3[lag]["basis"], ".0f"),
                ))

        linjer = [
            "3 GEONET-REDUKTION",
            "",
            f"Designdiagrammet indeholder tre feltbestemte kurver for hver "
            f"Eo-værdi. Den ækvivalente Eo ligger {pct} % inde mellem "
            f"klasse {kl_lav} og {kl_hoej}, og samme interpolationsfaktor "
            f"anvendes på alle tre kurver (mm ved Eu = {eu_txt} MPa):",
            "",
            *raekker,
        ]

        # φ- og net-korrektion: samme faktor på de armerede tal, så procenterne
        # bliver ærlige. Kun den uarmerede reference bærer φ alene — nettet
        # findes jo ikke i den opbygning.
        phi_kor = K_PHI * (phi - PHI_BASIS)
        t_uarm_ref = (ref_1 or ref_2 or {}).get("t_uarmeret_phi_kor_mm")
        net_kor = (geonet or {}).get("korrektion") or 0.0
        if abs(phi_kor) > 1e-9 and t_uarm_ref:
            linjer += [
                "",
                f"Herefter korrigeres for friktionsvinklen "
                f"(φ = {_dk_num(phi, '.1f')}° mod diagrammets "
                f"{_dk_num(PHI_BASIS, '.1f')}°):",
                f"    k_φ = {_dk_num(K_PHI, '.2f')} × "
                f"({_dk_num(phi, '.1f')} − {_dk_num(PHI_BASIS, '.1f')}) "
                f"= {_dk_num(phi_kor, '.3f')}",
            ]
        if abs(net_kor) >= 0.005:
            navn = (geonet or {}).get("navn") or "det valgte net"
            linjer += [
                "",
                f"Der korrigeres tillige for geonettypen. {navn} ligger "
                f"{_dk_num(net_kor * 100, '+.0f')} % i forhold til "
                f"referencenettet. Den samlede faktor på de armerede "
                f"lagtykkelser bliver:",
                f"    1 + ({_dk_num(phi_kor, '.3f')}) + "
                f"({_dk_num(net_kor, '.3f')}) "
                f"= {_dk_num(1 + phi_kor + net_kor, '.3f')}",
            ]
        linjer.append("")
        linjer.append(
            f"    uarmeret:      {_dk_num(t_uarm_ref or t_krav_mm, '.0f'):>5} mm"
        )
        for ref, navn in ((ref_1, "1 lag geonet"), (ref_2, "2 lag geonet")):
            t_arm = ref.get("t_armeret_mm") if ref else None
            if t_arm is None:
                continue
            red = ref.get("reduktion_pct")
            red_txt = f"   (−{_dk_num(red * 100, '.0f')} %)" if red else ""
            linjer.append(f"    {navn}:  {_dk_num(t_arm, '.0f'):>5} mm{red_txt}")
        if t_uarm_ref:
            linjer += [
                "",
                f"Reduktionen opgøres i forhold til de "
                f"{_dk_num(t_uarm_ref, '.0f')} mm, som er den ustabiliserede "
                f"opbygning i samme materiale. Begge lagtykkelser er dermed "
                f"korrigeret på samme grundlag.",
            ]
        tips["geonet"] = "\n".join(linjer)

    return tips


def _render_trafik_kobling_forklaring(
    t_klasse: str,
    eu: float,
    eo_aekv: float,
    phi: float,
    ref_1: dict | None,
    ref_2: dict | None,
    t_basis_table: dict,
    geonet: dict | None = None,
) -> None:
    """Trinvis forklaring af hvordan (trafikklasse, Eu) bliver til en
    bærelagstykkelse — med brugerens egne tal. Tykkelses-først.

    Ligger i en expander, der er lukket som standard: forklaringen er
    baggrundsstof, som man slår op i efter behov. Placeres lige efter
    'Ustabiliseret bærelagstykkelse'-banneret, så bannerets tal hænger
    direkte sammen med forklaringen.
    """
    tal = _trafik_kobling_tal(eu, eo_aekv, t_basis_table)
    t_krav = tal["t_krav_mm"]
    kl_lav, kl_hoej = tal["kl_lav"], tal["kl_hoej"]
    t_lav, t_hoej = tal["t_lav_mm"], tal["t_hoej_mm"]
    naermeste = eo_til_naermeste_klasse(eo_aekv)
    t_1lag = ref_1.get("t_armeret_mm") if ref_1 else None
    t_2lag = ref_2.get("t_armeret_mm") if ref_2 else None
    # Reduktionen måles mod den φ-korrigerede uarmerede tykkelse — samme
    # korrektion som de armerede tal bærer. Bruges t_krav (diagrammets
    # ukorrigerede værdi) som reference, overdrives besparelsen. Vi tager
    # appens egne procenter, så forklaringen ikke kan divergere fra tabellen.
    t_uarm_ref = (ref_1 or ref_2 or {}).get("t_uarmeret_phi_kor_mm") or t_krav
    red_1 = ref_1.get("reduktion_pct") if ref_1 else None
    red_2 = ref_2.get("reduktion_pct") if ref_2 else None
    # Net-korrektionen indgår allerede i ref_1/ref_2, når kalderen har sendt
    # det valgte produkts resultater. Navn/procent bruges kun til at sige
    # hvilket net tallene gælder — ellers ligner de altid referencenettets.
    net_kor = (geonet or {}).get("korrektion") or 0.0
    net_navn = (geonet or {}).get("navn")
    net_label = (
        f"{net_navn} ({_dk_num(net_kor * 100, '+.0f')} %)"
        if net_navn and abs(net_kor) >= 0.005 else (net_navn or "referencenet")
    )

    if t_krav is None:
        with st.expander(
        "Kobling imellem trafikklasse og designdiagram",
        expanded=ui.mellemregninger(),
    ):
            st.caption(
                "Designdiagrammet indeholder ingen ustabiliseret kurve i dette "
                "punkt, og sammenkædningen kan derfor ikke vises trinvist."
            )
        return

    # --- Principiel trinvis tekst (brugerens egne tal) ------------------
    linje2_kurver = (
        f"**belastningsklasse {kl_lav}-kurven ({ui.mm(t_lav)}) og "
        f"klasse {kl_hoej}-kurven ({ui.mm(t_hoej)})**"
        if (t_lav is not None and t_hoej is not None and kl_lav != kl_hoej)
        else f"**belastningsklasse-kurverne**"
    )
    # Reduktionen holdes op mod den φ-korrigerede uarmerede tykkelse, ikke mod
    # diagrammets rå værdi — ellers passer procenten ikke med produkttabellens.
    uarm_note = (
        f", opgjort i forhold til {ui.mm(t_uarm_ref)}, som er de "
        f"{ui.mm(t_krav)} korrigeret for de valgte materialer "
        f"(φ = {_dk_num(phi, '.1f')}°). Det er tillige den lagtykkelse, "
        f"designdiagrammets ustabiliserede kurve angiver"
        if t_uarm_ref is not None and abs(t_uarm_ref - t_krav) >= 1 else ""
    )
    linje3 = (
        f"3. På samme kurve reduceres lagtykkelsen med **1 lag geonet** til "
        f"**{ui.mm(t_1lag)}"
        + (f" (−{ui.procent(red_1 * 100)})" if red_1 is not None else "")
        + f"**{uarm_note}."
        + (
            f" Med 2 lag geonet fås **{ui.mm(t_2lag)}**"
            + (f" (−{ui.procent(red_2 * 100)})" if red_2 is not None else "")
            + "."
            if t_2lag is not None else ""
        )
    ) if t_1lag is not None else (
        "3. Geonet-reduktionen aflæses på samme kurve, jf. resultaterne ovenfor."
    )
    prosa = (
        f"1. For **{t_klasse} ved Eu = {ui.mpa(eu)}** fastlægger VejDim en "
        f"ubunden lagtykkelse på **{ui.mm(t_krav)}** (bundsikring og "
        f"stabilgrus). Værdien er angivet i feltet *Ustabiliseret "
        f"bærelagstykkelse* ovenfor.\n"
        f"2. Ved Eu = {ui.mpa(eu)} ligger de {ui.mm(t_krav)} i "
        f"designdiagrammet mellem {linje2_kurver}. Kurven benævnes "
        f"**Eo_ækv = {ui.mpa(eo_aekv)}** (nærmeste hele belastningsklasse: "
        f"{naermeste}).\n"
        f"{linje3}"
    )

    # --- Kompakt lodret trin-flow (tykkelses-først) ---------------------
    def _box(top: str, big: str, sub: str = "", tip: str = "") -> str:
        """En grøn trin-boks. Med tip vises regnestykket bag trinnet som
        browser-tooltip (title), markeret med en prik og hjælpe-markør."""
        sub_html = (
            f'<div style="font-size:0.8rem;color:#555">{sub}</div>' if sub else ""
        )
        # &#10; er linjeskift inde i en title-attribut.
        tip_attr = (
            f' title="{html.escape(tip, quote=True).replace(chr(10), "&#10;")}"'
            if tip else ""
        )
        markør = (
            f'<span style="font-size:0.72rem;color:{ui.FARVE["gron"]};'
            f'margin-left:5px">&#9679;</span>'
            if tip else ""
        )
        ekstra = "cursor:help;" if tip else ""
        return (
            f'<div{tip_attr} style="background:#F8FFF8;border:1px solid #C8E6C9;'
            f'border-radius:6px;padding:6px 16px;text-align:center;{ekstra}'
            f'display:inline-block;min-width:260px">'
            f'<div style="font-size:0.68rem;color:#777;text-transform:uppercase;'
            f'letter-spacing:.03em">{top}{markør}</div>'
            f'<div style="font-size:1.05rem;font-weight:700;color:{GRØN}">{big}</div>'
            f'{sub_html}</div>'
        )

    def _arrow(label: str) -> str:
        return (
            f'<div style="color:{GRÅ};font-size:0.76rem;margin:2px 0">▼'
            f'<span style="margin-left:6px">{label}</span></div>'
        )

    # Regnestykket bag hvert trin — vises som tooltip på den enkelte boks.
    tips = _eo_aekv_tooltips(
        t_klasse, eu, eo_aekv, t_basis_table,
        t_krav_mm=t_krav, ref_1=ref_1, ref_2=ref_2, phi=phi, geonet=geonet,
    )

    def _geonet_sub(red: float | None) -> str:
        red_s = f"−{ui.procent(red * 100)} · " if red is not None else ""
        return f"{red_s}{net_label}"

    et_lag_box = (
        _box("Med 1 lag geonet", f"{ui.mm(t_1lag)}",
             _geonet_sub(red_1), tips["geonet"])
        if t_1lag is not None else _box("Med geonet", "se resultater", "")
    )
    # 2-lags-boksen kommer kun med, når diagrammet har en 2-lags-kurve i punktet.
    to_lag_box = (
        _arrow("endnu et lag i opbygningen")
        + _box("Med 2 lag geonet", f"{ui.mm(t_2lag)}",
               _geonet_sub(red_2), tips["geonet"])
    ) if t_2lag is not None else ""

    # Materiale-trinnet gør skiftet fra diagrammets basisværdier til den
    # φ-korrigerede virkelighed synligt. Uden det springer flowet fra en
    # ukorrigeret tykkelse (trin 1-2, som Eo_ækv tilbageberegnes fra) til
    # korrigerede resultater — præcis som designdiagrammet tegner dem.
    phi_afviger = abs(phi - PHI_BASIS) > 0.05
    materiale_box = (
        _arrow(f"Korrektion for friktionsvinkel (φ = {_dk_num(phi, '.1f')}°)")
        + _box("Ustabiliseret, korrigeret", f"{ui.mm(t_uarm_ref)}",
               "designdiagrammets ustabiliserede kurve", tips["materiale"])
    ) if (phi_afviger and t_uarm_ref is not None
          and abs(t_uarm_ref - t_krav) >= 1) else ""

    flow = (
        '<div style="display:flex;flex-direction:column;align-items:center;'
        'gap:0;margin:0.5rem 0 0.9rem">'
        + _box("Valgt grundlag", f"{t_klasse} · Eu {ui.mpa(eu)}", "",
               tips["valg"])
        + _arrow("VejDims krav til ubundet lag")
        + _box("Krævet ubundet opbygning", f"{ui.mm(t_krav)}",
               "bundsikring og stabilgrus", tips["krav"])
        + _arrow("Tykkelsen findes på designdiagrammet ved valgt Eu")
        + _box(f"Kurve for Eo_ækv ≈ {ui.mpa(eo_aekv)} bestemmes",
               f"mellem klasse {kl_lav} og {kl_hoej}", "", tips["driftspunkt"])
        + materiale_box
        + _arrow("Geonet-reduktion aflæses i punktet")
        + et_lag_box
        + to_lag_box
        + '</div>'
    )
    # --- Layout: forklaring til venstre, designdiagram til højre --------
    with st.expander(
        "Kobling imellem trafikklasse og designdiagram",
        expanded=ui.mellemregninger(),
    ):
        kol_forklaring, kol_figur = st.columns([1.05, 0.95], gap="large")
        with kol_forklaring:
            st.markdown(prosa)
            st.markdown(flow, unsafe_allow_html=True)
        with kol_figur:
            from core import rapport as rapport_mod
            try:
                # Mere kvadratisk figsize + container-bredde: figuren fylder den
                # højre (mindre) kolonne og bliver ca. samme højde som
                # forklaringen.
                png = rapport_mod.render_personligt_designdiagram_png(
                    eu=float(eu),
                    eo=float(eo_aekv),
                    klasse=naermeste,
                    grundlag_label=f"Trafikklasse {t_klasse}",
                    phi=float(phi),
                    geonet=geonet,
                    t_indtastet_mm=None,
                    t_basis_table=t_basis_table,
                    t_1_lag_mm=t_1lag,
                    t_2_lag_mm=t_2lag,
                    dpi=120,
                    figsize=(7.4, 6.6),
                )
                st.image(png, width="stretch")
                # Kurverne er tegnet φ-korrigerede (rapport.py: f_uarm =
                # 1 + phi_kor), så billedteksten skal nævne den korrigerede
                # tykkelse — ikke diagrammets basisværdi.
                st.caption(
                    f"Kurven for Eo_ækv ≈ {ui.mpa(eo_aekv)} krydser "
                    f"{ui.mm((t_uarm_ref or t_krav))} ved Eu = {ui.mpa(eu)}"
                    + (
                        f" (φ-korrigeret fra {ui.mm(t_krav)})"
                        if t_uarm_ref is not None
                        and abs(t_uarm_ref - t_krav) >= 1 else ""
                    )
                    + "; geonet-punkterne viser reduktionen."
                )
            except Exception as e:
                st.caption(f"Kunne ikke tegne designdiagram: {e}")


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

    Bemærk: Streamlit-dropdownen kan ikke farve en del af teksten, så
    klasse-/korrektions-delen vises i samme farve som navnet (kun captionen
    nedenunder kan vises nedtonet).
    """
    g = find_geonet(navn)
    if not g:
        return navn
    dele: list[str] = []
    kl = g.get("klasser")
    if kl:
        dele.append(f"Klasse {_format_klasse_liste(kl)}")
    kor_txt = _korrektion_label(g)
    if kor_txt:
        dele.append(f"Net-korrektion: {kor_txt}")
    return f"{navn} ({' · '.join(dele)})" if dele else navn


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

    Opdelingen på basis-, net- og φ-korrektion er en mellemregning; er
    kontakten slået fra, vises alene den optimale tykkelse, jf. afsnit 8.
    """
    if not _rt_gyldig(p) or p.get("t_armeret_mm_min") is None:
        return ""
    kor_opt = p.get("korrektion_min")
    t_opt = p["t_armeret_mm_min"]
    t_uarm = p.get("t_uarmeret_mm")
    pct_opt = (t_uarm - t_opt) / t_uarm if t_uarm else None
    linjer = (
        _rt_reduktion_linjer(p, False, kor=kor_opt, t_arm=t_opt, phi=phi)
        if ui.mellemregninger() else ""
    )
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

    Opdelingen på basis-, net- og φ-korrektion er en mellemregning og vises
    alene, når kontakten i topbjælken er slået til, jf. afsnit 8.
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

    if not ui.mellemregninger():
        return (
            '<div class="rt-detalje">'
            f'{krav_html}'
            f'<div class="rt-d-bt rt-d-bt1">{bt1}</div>'
            f'<div class="rt-d-bt rt-d-bt2">{bt2}</div>'
            '</div>'
        )

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
    indeks_html = (
        f'<span class="num rt-indeks">{_effektindeks(navn, is_ref)}</span>'
        if vis_indeks else ""
    )

    return (
        f'<details class="{raekke_css}" name="rt-produkt">'
        f'<summary class="rt-sum">'
        f'<span class="rt-navn"><span class="rt-chev">▸</span> {navn}</span>'
        f'{indeks_html}'
        f'<span><span class="rt-badge {badge_css}">{badge_pre}{kl_txt}</span></span>'
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
    dele = ['<div class="rt-tabel">']
    dele.append(
        f'<div class="rt-head{" rt-head-indeks" if grupperet else ""}">'
        '<span>Produkt</span>'
        f'{indeks_kol}'
        f'{kl_kol}'
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
                            vis_indeks=grupperet)
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
                                    eu=eu, vis_indeks=grupperet))
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

    # Statusteksten formuleres som en konstatering: "311 mm for lidt" frem for
    # "Mangler 311 mm".

    # Hvis konservativ er tilstrækkelig → grøn (overskud)
    if diff_kons >= 0:
        if diff_best is not None and diff_best > diff_kons:
            return (
                f"{ui.mm(diff_kons)} i overskud\n({ui.mm(diff_best)})",
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
            f"{ui.mm(-diff_kons)} for lidt\n({ui.mm(-diff_best)})",
            "danger",
        )
    return f"{ui.mm(-diff_kons)} for lidt", "danger"


def _plotly_designdiagram(
    *,
    eu: float,
    eo: float,
    phi: float,
    geonet: dict | None,
    t_indtastet_mm: float | None,
    t_basis_table: dict,
    t_1_lag_mm: float | None = None,
    t_2_lag_mm: float | None = None,
    t_1_lag_best_mm: float | None = None,
    t_2_lag_best_mm: float | None = None,
):
    """Designdiagrammet som Plotly-figur til skærmen.

    Kurverne dannes af designdiagram-tabellen ved det viste Eo og korrigeres
    med φ og nettets korrektion, jf. afsnittet "Sådan dannes diagrammet".
    Produkter med korrektionsinterval tegnes med et tonet bånd mellem den
    optimale og den konservative kurve.

    Der gøres opmærksom på, at rapporten fortsat tegnes af matplotlib i
    core/rapport.py; ændres udtrykket her, bør rapporten følge med.
    """
    import plotly.graph_objects as go

    phi_kor = K_PHI * (phi - PHI_BASIS)
    net_kor_kons = float(geonet.get("korrektion", 0.0)) if geonet else 0.0
    interval = geonet.get("korrektion_interval") if geonet else None
    net_kor_best = float(interval[0]) if interval else None
    geonet_navn = (geonet or {}).get("navn", "Referencenet")

    eu_vals = sorted(t_basis_table.keys())

    def _kurve(lag_mode: str, faktor: float) -> tuple[list[float], list[float]]:
        xs: list[float] = []
        ys: list[float] = []
        for eu_v in eu_vals:
            v = _slaa_op_interp(eu_v, eo, lag_mode, t_basis_table=t_basis_table)
            if v is not None:
                xs.append(v * faktor)      # cm
                ys.append(eu_v)
        return xs, ys

    FARVE_UARM = "#8B7355"
    FARVE_1LAG = "#15211A"
    FARVE_2LAG = "#1B6B34"
    HOVER = "%{x:.0f} cm · Eu %{y:.1f} MN/m²<extra>%{fullData.name}</extra>"

    fig = go.Figure()

    xs_u, ys_u = _kurve("uarmeret", 1.0 + phi_kor)
    if xs_u:
        fig.add_trace(go.Scatter(
            x=xs_u, y=ys_u, mode="lines", name="Uden geonet",
            line=dict(color=FARVE_UARM, width=2),
            hovertemplate=HOVER,
        ))

    def _armeret(lag_mode: str, farve: str, navn: str) -> None:
        xs_k, ys_k = _kurve(lag_mode, 1.0 + phi_kor + net_kor_kons)
        if not xs_k:
            return
        if net_kor_best is not None:
            xs_b, ys_b = _kurve(lag_mode, 1.0 + phi_kor + net_kor_best)
            if xs_b and ys_b == ys_k:
                # Båndet mellem den optimale og den konservative kurve.
                fig.add_trace(go.Scatter(
                    x=xs_b + xs_k[::-1], y=ys_b + ys_k[::-1],
                    fill="toself", fillcolor=farve, opacity=0.10,
                    line=dict(width=0), hoverinfo="skip",
                    showlegend=False,
                ))
                fig.add_trace(go.Scatter(
                    x=xs_b, y=ys_b, mode="lines",
                    name=f"{navn} (optimal)",
                    line=dict(color=farve, width=1.2, dash="dot"),
                    hovertemplate=HOVER,
                ))
        fig.add_trace(go.Scatter(
            x=xs_k, y=ys_k, mode="lines", name=navn,
            line=dict(color=farve, width=2),
            hovertemplate=HOVER,
        ))

    _armeret("1_lag", FARVE_1LAG, f"1 lag · {geonet_navn}")
    _armeret("2_lag", FARVE_2LAG, f"2 lag · {geonet_navn}")

    for t_mm, farve, navn in (
        (t_1_lag_mm, FARVE_1LAG, "1 lag geonet"),
        (t_2_lag_mm, FARVE_2LAG, "2 lag geonet"),
    ):
        if t_mm:
            fig.add_trace(go.Scatter(
                x=[t_mm / 10.0], y=[eu], mode="markers",
                name=navn, showlegend=False,
                marker=dict(color=farve, size=9,
                            line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate=HOVER,
            ))
    for t_mm, farve, navn in (
        (t_1_lag_best_mm, FARVE_1LAG, "1 lag geonet (optimal)"),
        (t_2_lag_best_mm, FARVE_2LAG, "2 lag geonet (optimal)"),
    ):
        if t_mm:
            fig.add_trace(go.Scatter(
                x=[t_mm / 10.0], y=[eu], mode="markers",
                name=navn, showlegend=False,
                marker=dict(color="rgba(0,0,0,0)", size=10,
                            line=dict(color=farve, width=2)),
                hovertemplate=HOVER,
            ))

    # Den indtastede opbygning med lodret hjælpelinje, så aflæsningen på
    # x-aksen kan foretages direkte.
    if t_indtastet_mm and t_indtastet_mm > 0:
        t_cm = t_indtastet_mm / 10.0
        fig.add_shape(
            type="line", x0=t_cm, x1=t_cm, y0=0, y1=eu,
            line=dict(color=ui.FARVE["kritisk"], width=1, dash="dash"),
        )
        fig.add_trace(go.Scatter(
            x=[t_cm], y=[eu], mode="markers",
            name="Indtastet opbygning", showlegend=False,
            marker=dict(color=ui.FARVE["kritisk"], size=11,
                        line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate=HOVER,
        ))
        fig.add_annotation(
            x=t_cm, y=0, yanchor="bottom", yshift=6,
            text=f"Indtastet {t_cm:.0f} cm", showarrow=False,
            font=dict(size=10, color="#FFFFFF"),
            bgcolor=ui.FARVE["kritisk"], borderpad=3,
        )

    alle_x = list(xs_u)
    for t in (t_indtastet_mm, t_1_lag_mm, t_2_lag_mm,
              t_1_lag_best_mm, t_2_lag_best_mm):
        if t:
            alle_x.append(t / 10.0)
    x_maks = max(alle_x) * 1.08 if alle_x else 160

    akse = dict(
        gridcolor="#EDEFED", zeroline=False,
        linecolor=ui.FARVE["linje"], ticks="outside",
        tickcolor=ui.FARVE["linje"], tickfont=dict(size=10),
    )
    fig.update_layout(
        height=380,
        margin=dict(l=60, r=20, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", size=11,
                  color=ui.FARVE["ink"]),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.0,
                    xanchor="right", x=1, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Bærelagstykkelse [cm]", range=[0, max(x_maks, 80)], **akse),
        yaxis=dict(
            title="Bundmodul Eu [MN/m²]",
            range=[0, max(max(eu_vals) * 1.05, eu * 1.2, 50)],
            **akse,
        ),
    )
    return fig


def _lagtype_for_navn(navn: str, materialer: list[dict] | None) -> str:
    """Fladefarve for et lag: bærelag eller bundsikring.

    Lagtypen slås op i de indtastede materialer. Findes navnet ikke — søjlen
    kan være dannet af en skaleret fordeling — afgøres den ud fra navnet.
    """
    for m in materialer or []:
        if m.get("navn") == navn:
            return (
                "bundsikring"
                if str(m.get("lagtype", "")).lower().startswith("bunds")
                else "baerelag"
            )
    return "bundsikring" if "bundsikring" in navn.lower() else "baerelag"


def _snit_til_kolonner(
    snit_liste: list, materialer: list[dict] | None, eu: float,
) -> list[dict]:
    """Oversætter snit-listen til ui.snit()'s kolonner.

    Snit-objekterne er den fælles beskrivelse, som også rapportens
    matplotlib-figur tegnes af. Her omsættes de til opmærkningens format:

    - geonet_y_fracs er brøkdele målt fra bærelagets overkant; ui.snit()
      forventer koter over underbunden, altså total × (1 − frac).
    - En søjle uden materialefordeling tegnes som ét ubundet lag.
    - Statusfarverne følger stylesheetets tre statusfarver.
    """
    farve = {"danger": "kritisk", "warning": "advarsel", "success": "gron"}
    kolonner: list[dict] = []
    for s in snit_liste:
        total = s.t_baerelag_mm
        if s.sub_lag:
            lag = [
                (
                    l["navn"],
                    l["tykkelse_mm"],
                    _lagtype_for_navn(l["navn"], materialer),
                )
                for l in s.sub_lag
            ]
        elif total:
            lag = [("Ubunden opbygning", total, "baerelag")]
        else:
            lag = []

        advarsler = list((s.placement or {}).get("placeringsadvarsler") or [])

        kolonner.append({
            "titel": s.titel,
            "lag": lag,
            "geonet_mm": [
                total * (1 - frac) for frac in (s.geonet_y_fracs or []) if total
            ],
            "total_mm": total,
            "tom_tekst": s.ikke_defineret_tekst or "Ikke defineret",
            "best_case_mm": s.best_case_mm,
            "advarsler": advarsler,
            "status": (
                s.status_tekst or "",
                farve.get(s.status_farve or "", "neutral"),
            ),
        })

    if kolonner:
        kolonner[0]["underbund_tekst"] = f"UNDERBUND · Eu {eu:.0f} MPa"
    return kolonner


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
        valgt_geonet = None
        geonet_label = "Tensar TriAx 160 / GS-GRID SX160 / E'GRID T6"
    else:
        t_1 = _produkt_t(prod_1lag, valg)
        t_2 = _produkt_t(prod_2lag, valg)
        t_1_best = _produkt_t_best(prod_1lag, valg)
        t_2_best = _produkt_t_best(prod_2lag, valg)
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

    ui.snit(
        _snit_til_kolonner(snit_liste, materialer, eu),
        reference_mm=t_indtastet_for_linje,
        geonet_navn=geonet_label,
    )
    st.caption(
        "Snit i samme lodrette skala"
        + (
            f" · stiplet linje = indtastet {ui.mm(t_indtastet_for_linje)}"
            if t_indtastet_for_linje else ""
        )
        + (
            "" if har_indtastet
            else " · uden materialelag vises kravet som ét ubundet lag"
        )
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
    phi: float = PHI_BASIS,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
    materialer: list[dict] | None = None,
    t_basis_table: dict | None = None,
    eo_interpoleret: bool = False,
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
        st.markdown("#### Opbygning")
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

    # --- Sådan beregnes det -----------------------------------------------
    # Afsnittet åbnes af sig selv, når mellemregningerne er slået til.
    with st.expander("Sådan beregnes det", expanded=ui.mellemregninger()):
        if eo_interpoleret:
            st.info(
                "**Trafikklasse-tilstand:** trin 2 nedenfor (kravet til Eo) "
                "bestemmes ikke ud fra en belastningsklasse, men via "
                "trafikklasse-koblingen — VejDim fastlægger den krævede ubundne "
                "tykkelse, og den ækvivalente Eo (Eo_ækv) er blot den diagramkurve, "
                "tykkelsen lander på, jf. **'Kobling imellem trafikklasse og "
                "designdiagram'** ovenfor. Trin 5–6 (φ- og net-korrektion) gælder uændret."
            )
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
        _noegletal_tabel_html([
            ("Friktionsvinkel φ", ui.grader(PHI_BASIS)),
            ("φ-korrektion", "ingen"),
            ("Materialelag", "indgår ikke"),
        ]),
        unsafe_allow_html=True,
    )
    st.caption(
        f"I standardberegningen sættes bærelagets friktionsvinkel "
        f"φ = {ui.grader(PHI_BASIS)}, svarende til designmanualernes "
        f"forudsætning. Der beregnes derfor ingen φ-korrektion."
    )


def _grundlag_tekst(grundlag: dict) -> str:
    """Grundlaget som en kort tekst til resultatafsnittets sidehoved."""
    if grundlag["type"] == "trafikklasse":
        return f"trafikklasse {grundlag['t_klasse']}"
    return f"belastningsklasse {grundlag['valgt_klasse']}"


def _resultat_overskrift(eu: float, grundlag: dict, phi: float) -> None:
    """Overskriften over resultatkolonnen med beregningens forudsætninger."""
    st.markdown(
        f'<div class="bg-resultat-hoved">'
        f'<h2>Resultat</h2>'
        f'<span>Krav til bærelagstykkelse ved Eu = {ui.mpa(eu)}, '
        f'{_grundlag_tekst(grundlag)}, φ = {ui.grader(phi)}</span>'
        f'</div>',
        unsafe_allow_html=True,
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


def render_standard(input_kol, resultat_kol) -> None:
    """Standard-tilstand: produktoversigt for alle geonet på én gang.

    Input står i venstre kolonne, resultatet i højre, jf. afsnit 5.
    Beregningen ligger imellem de to, så resultatet altid dannes af de
    værdier, inputkolonnen netop har afsat.
    """

    with input_kol:
        ui.etiket("Forudsætninger")
        _tilstand_vaelger()

        st.caption(
            "Standardtilstanden viser kravet for samtlige geonet ved den valgte "
            "underbund. Skal opbygningen sammensættes af flere materialelag med "
            "hver sin friktionsvinkel, vælges Brugerdefineret."
        )

        eu = input_underbund(key_prefix="std", kompakt=True)
        grundlag = input_grundlag(key_prefix="std", eu=eu, kompakt=True)
        _faste_forudsaetninger()

    eo = grundlag["eo"]
    valgt_klasse = grundlag["valgt_klasse"]
    eo_interpoleret = grundlag["type"] == "trafikklasse"

    # Trafikklasse uden for kernezonen: zone-beskeden er allerede vist i
    # inputkolonnen — der er intet driftspunkt at dimensionere efter.
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

    # --- Resultater -----------------------------------------------------
    with resultat_kol:
        _resultat_overskrift(eu, grundlag, PHI_BASIS)

        vis_kobling = False
        if haard_fejl:
            vis_fejl(haard_fejl)
        else:
            if t_uarm is not None:
                _vis_resultatkort(
                    t_uarm,
                    bedste_1["t_armeret_mm"] if bedste_1 else None,
                    bedste_2["t_armeret_mm"] if bedste_2 else None,
                    standard=True,
                    note_uarm=(
                        "Ubunden opbygning · interpoleret mellem Eo-kurverne"
                        if eo_interpoleret else "Ubunden opbygning"
                    ),
                    navne_1=_navne_kort(bedste_1) if bedste_1 else "",
                    navne_2=_navne_kort(bedste_2) if bedste_2 else "",
                )
            else:
                _render_uarmeret_mangler_besked(eu, eo)

            # Koblings-forklaringen renderes nederst i resultatsektionen, lige
            # over Opbygning — se kaldet nedenfor.
            vis_kobling = eo_interpoleret

            st.markdown(
                '<div class="bg-resultat-hoved" style="margin-top:1.5rem">'
                '<h2>Alle produkter</h2>'
                '<span>Klik en række for krav til udførelse</span></div>',
                unsafe_allow_html=True,
            )
            _render_produkt_tabel(
                ref_1, ref_2, ref_fejl_1, ref_fejl_2,
                prod_1lag, prod_2lag, valgt_klasse, eu=eu,
                trafik_eu=eu if grundlag["type"] == "trafikklasse" else None,
                grupperet=True,
            )
            st.caption(
                "I resultatoversigten vises, hvilke belastningsklasser "
                "produkterne anbefales til. Der vises en advarsel, hvis et "
                "produkt ikke anbefales anvendt til den valgte klasse."
            )

        if vis_kobling:
            _render_trafik_kobling_forklaring(
                grundlag["t_klasse"], eu, grundlag["eo_aekv"], PHI_BASIS,
                ref_1, ref_2, t_basis_table,
            )

        # --- Informations-expandere ------------------------------------
        _render_oversigt_expanders(
            eu, eo, valgt_klasse, bedste_1, bedste_2,
            ref_1=ref_1, ref_2=ref_2,
            prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            t_basis_table=t_basis_table,
            eo_interpoleret=eo_interpoleret,
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


def _pct_fortegn(v: float) -> str:
    """Korrektionsfaktor som procent med fortegn: 0,10 → '+10 %', −0,10 → '−10 %'.

    ui.procent() angiver ingen fortegn og anvendes til rene procentangivelser;
    net-korrektionen aflæses derimod som en signeret størrelse.
    """
    return f"{v * 100:+.0f} %".replace("-", "−")


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

    Boksen er en mellemregning og vises alene, når kontakten i topbjælken er
    slået til. Den vægtede φ fremgår fortsat af inputkolonnen.
    """
    if not ui.mellemregninger():
        return

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
    """
    Materialelag — render input-sektionen og returnér
    (materialer-liste, beregnet/overskrevet φ).

    kompakt=True stiller lagene under hinanden i inputkolonnens fulde bredde
    i stedet for i en halv kolonne.
    """
    ui.etiket("Opbygning") if kompakt else st.subheader("Materialelag")

    if kompakt:
        antal_lag = st.number_input(
            "Antal lag", min_value=1, max_value=3, value=2, step=1,
            key="bd_antal_lag",
        )
    else:
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

    for i in range(int(antal_lag)):
        # I inputkolonnen fylder laget hele bredden; ellers halvdelen, så
        # felterne ikke trækkes ud over en læsbar linjelængde.
        lag_ramme = (
            contextlib.nullcontext() if kompakt else st.columns([1, 1])[0]
        )
        with lag_ramme, st.expander(_lag_label(i, int(antal_lag)), expanded=True):
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
    st.markdown(f"**Samlet tykkelse af opbygning:** {ui.mm(total_t)}")

    phi_weighted = _phi_tabel_data(materialer)["phi_weighted"]

    if st.checkbox("Overskriv φ manuelt", key="bd_phi_override"):
        phi = st.number_input(
            "φ (°)", 20.0, 60.0, round(phi_weighted, 1), 0.5, key="bd_phi_man",
        )
    else:
        phi = phi_weighted

    _vis_phi_opsummeringsboks(materialer, phi)

    return materialer, phi


def render_brugerdefineret(input_kol, resultat_kol) -> None:
    """Brugerdefineret-tilstand: input + resultater + expandere.

    Input står i venstre kolonne, resultatet i højre, jf. afsnit 5. Sektion
    Geonet lader brugeren vælge mellem 'Alle produkter' (oversigt med
    brugerdefineret φ) og 'Vælg produkt' (detaljeret resultat for ét produkt).
    Begge tilstande viser 1-lag og 2-lag side om side.
    """

    t_basis_table = _aktiv_t_basis_table()

    # --- Inputkolonnen: underbund, grundlag, opbygning, geonet ----------
    with input_kol:
        ui.etiket("Forudsætninger")
        _tilstand_vaelger()

        eu = input_underbund(key_prefix="bd", kompakt=True)
        grundlag = input_grundlag(key_prefix="bd", eu=eu, kompakt=True)
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
            materialer, phi = _input_materialelag(kompakt=True)

            ui.etiket("Geonet")
            visning = st.segmented_control(
                "Visning",
                ["Alle produkter", "Vælg produkt"],
                default="Alle produkter",
                key="bd_visning",
                label_visibility="collapsed",
                width="stretch",
                help=(
                    "**Alle produkter:** samme oversigt som Standard-beregningen, "
                    "men med den vægtede friktionsvinkel φ fra materialelagene.  \n"
                    "**Vælg produkt:** detaljeret resultat for ét valgt "
                    "produkt, herunder produktets specifikke udførelseskrav."
                ),
            ) or "Alle produkter"
            specifikt_mode = visning == "Vælg produkt"

            if specifikt_mode:
                geonet_navn = st.selectbox(
                    "Produkt",
                    GEONET_NAVNE,
                    index=GEONET_NAVNE.index("GS-GRID SX160"),
                    key="bd_geonet",
                    format_func=_produkt_label,
                    label_visibility="collapsed",
                )
                geonet = find_geonet(geonet_navn)

                if geonet:
                    korn_txt = (
                        f"{geonet['max_korn']} mm" if geonet["max_korn"] else "—"
                    )
                    kl_txt = _format_klasse_liste(geonet["klasser"])
                    kor_txt = _pct_fortegn(geonet["korrektion"])
                    rude_txt = geonet.get("rudeaabning") or "—"
                    db_maske = geonet.get("maskestoerrelse_datablad_mm")
                    if db_maske:
                        rude_txt += f" (datablad: {db_maske} mm)"
                    st.caption(
                        f"Serie: **{geonet['serie']}** · Korrektion: {kor_txt} · "
                        f"Max korn: {korn_txt} · "
                        f"Rudeåbning/maskestørrelse: {rude_txt} · "
                        f"Belastningsklasser: {kl_txt} · "
                        f"Min dæklag: {geonet['min_daklag']} cm"
                    )
                    if geonet["navn"] == "Anden armering (manuel)":
                        kor_man = st.number_input(
                            "Korrektionsfaktor (−0.20 til +0.20)",
                            min_value=-0.20, max_value=0.20,
                            value=0.0, step=0.01, format="%.2f",
                            key="bd_kor_man",
                            help=(
                                "0.00 = samme effektivitet som reference "
                                "(TX160/SX160/T6)."
                            ),
                        )
                        geonet = {**geonet, "korrektion": kor_man}

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

    with resultat_kol:
        _resultat_overskrift(eu, grundlag, phi)

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

                if eo_interpoleret:
                    # res_1/res_2 er beregnet med det VALGTE nets korrektion —
                    # ref_1/ref_2 er altid referencenettet. Forklaringen skal vise
                    # det net, brugeren rent faktisk har valgt. Renderes nederst i
                    # resultatsektionen, lige over Opbygning.
                    kobling_args = (
                        grundlag["t_klasse"], eu, grundlag["eo_aekv"], phi,
                        None if res_1.get("fejl") else res_1,
                        None if res_2.get("fejl") else res_2,
                        t_basis_table, geonet,
                    )

                # Ny tabel: referencerække + den valgte produkt-række. Enkelt-
                # produkt-lister læses fra de interval-berigede grupper.
                prod_1 = (
                    [bedste_1["produkter"][0]]
                    if bedste_1 and bedste_1.get("produkter") else []
                )
                prod_2 = (
                    [bedste_2["produkter"][0]]
                    if bedste_2 and bedste_2.get("produkter") else []
                )
                _render_produkt_tabel(
                    ref_1, ref_2, ref_fejl_1, ref_fejl_2,
                    prod_1, prod_2, valgt_klasse, phi=phi, eu=eu,
                    vis_reference=False,
                    trafik_eu=eu if grundlag["type"] == "trafikklasse" else None,
                )

                if geonet and geonet.get("navn"):
                    t_indtastet_total = _indtastet_total(materialer)
                    produkt_1 = (
                        bedste_1["produkter"][0]
                        if bedste_1 and bedste_1.get("produkter") else None
                    )
                    produkt_2 = (
                        bedste_2["produkter"][0]
                        if bedste_2 and bedste_2.get("produkter") else None
                    )

                    st.markdown(
                        f'<div class="bg-resultat-hoved" style="margin-top:1.5rem">'
                        f'<h2>Designdiagram</h2>'
                        f'<span>Eo = {ui.mpa(eo)} · {_grundlag_tekst(grundlag)} · '
                        f'φ = {ui.grader(phi)}</span></div>',
                        unsafe_allow_html=True,
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

                    try:
                        fig = _plotly_designdiagram(
                            eu=float(eu),
                            eo=float(eo),
                            phi=float(phi),
                            geonet=geonet,
                            t_indtastet_mm=(
                                t_indtastet_total if vis_din_prik else None
                            ),
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
                        st.plotly_chart(
                            fig,
                            width="stretch",
                            config={"displayModeBar": False},
                        )
                        with st.expander("Sådan dannes diagrammet"):
                            st.markdown(INFO_DESIGNDIAGRAM_MD)
                    except Exception as e:
                        st.warning(f"Kunne ikke generere designdiagram: {e}")

        if kobling_args is not None:
            _render_trafik_kobling_forklaring(*kobling_args)

        # --- Informations-expandere ------------------------------------------
        _render_oversigt_expanders(
            eu, eo, valgt_klasse, bedste_1, bedste_2,
            ref_1=ref_1, ref_2=ref_2,
            prod_1lag=prod_1lag, prod_2lag=prod_2lag,
            phi=phi,
            geonet=geonet,
            geonet_navn=geonet_navn,
            materialer=materialer,
            t_basis_table=t_basis_table,
            eo_interpoleret=eo_interpoleret,
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
# Placeholder-sider (Materialer, Geonet database, Designdiagrammer)
# ===========================================================================

def render_geonet_database() -> None:
    st.title("Geonet-database")
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

    # Kolonnebeskrivelserne ligger som tooltips på kolonneoverskrifterne, jf.
    # kolonne_hjaelp ovenfor. Alle 25 kolonner er dækket.

    # ── Vigtige noter ─────────────────────────────────────────────────────
    # Noterne står som et samlet afsnit frem for i expandere, så forbehold og
    # kildehenvisninger kan læses uden at skulle åbnes enkeltvis.
    st.subheader("Database-noter og kildehenvisninger")
    st.markdown("\n\n".join(
        f"##### {i} {note['titel']}\n{note['tekst']}"
        for i, note in enumerate(GEONET_NOTER, start=1)
    ))


def render_designdiagrammer() -> None:
    st.title("Designdiagrammer")
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


# Metode-, datagrundlag- og forbeholds-tekster (kondenseret fra
# "Dokumenter og data/Korrelation_trafikklasse_Eo.md").
_KORR_METODE_MD = """
Trafikklassegrundlaget sammenkæder Vejdirektoratets trafikklasser med de
geonet-designdiagrammer, dimensioneringen bygger på. Sammenkædningen sker uden
teoretisk omregning mellem de to metoder, idet den alene anvender to
uafhængige, empiriske datasæt:

- **VejDim-kørslerne** fastlægger den ubundne lagtykkelse, en given trafikklasse
  kræver ved en given underbund.
- **Designdiagrammerne** fastlægger den reduktion af lagtykkelsen, et geonet
  medfører i det pågældende punkt.

Fremgangsmåden er beskrevet i afsnit 1–4 nedenfor. Som gennemgående eksempel
anvendes trafikklasse T4 ved en underbund med E-værdi Eu = 8 MPa.

---

#### 1 Ubunden lagtykkelse

For hver kombination af trafikklasse og underbunds-E-værdi er der udført en
VejDim-kørsel. Kørslerne fremgår af tabellen nederst på siden. Den ubundne
lagtykkelse fastlægges som summen af de to ubundne lag:

```
t_ubundet = t_SG + t_BL
```

hvor:

- **t_SG** = tykkelsen af stabilgruslaget [mm].
- **t_BL** = tykkelsen af bundsikringslaget [mm].

Kørslerne er udført ved Eu = 3, 4, 5, 10, 15, 20, 30 og 40 MPa. For
mellemliggende E-værdier bestemmes lagtykkelsen ved lineær interpolation i
log(Eu) mellem de to nærmeste kørsler:

```
f         = (ln(Eu) − ln(Eu_1)) / (ln(Eu_2) − ln(Eu_1))
t_ubundet = t_1 + f × (t_2 − t_1)
```

hvor Eu_1 og Eu_2 er de nærmeste kørte E-værdier, og t_1 og t_2 de tilhørende
lagtykkelser.

Lagtykkelsen aftager tilnærmelsesvis retlinet med log(Eu) i hele datasættet.
Ved en udeladelsestest er middelafvigelsen på den ækvivalente Eo bestemt til
2,9 MPa ved interpolation i log(Eu) mod 5,5 MPa ved interpolation i Eu.

For T4 ved Eu = 8 MPa fås:

| Trafikklasse | Eu = 5 MPa | Eu = 8 MPa | Eu = 10 MPa |
|---|---|---|---|
| T4 | 1184 mm | 1038 mm | 969 mm |

*Figur 1 Ubunden lagtykkelse for T4. Værdien ved Eu = 8 MPa er interpoleret
(f = 0,678).*

---

#### 2 Ækvivalent Eo

Ved den ækvivalente Eo forstås den Eo-værdi, hvis ustabiliserede lagtykkelse
ved samme Eu svarer til den lagtykkelse, der er fastlagt efter afsnit 1.
Værdien bestemmes ved lineær interpolation mellem de to nærmeste Eo-kurver i
designdiagrammet:

```
f      = (t_ubundet − t_lav) / (t_høj − t_lav)
Eo_ækv = Eo_lav + f × (Eo_høj − Eo_lav)
```

hvor t_lav og t_høj er de ustabiliserede lagtykkelser ved de to nærmeste
Eo-kurver, Eo_lav og Eo_høj.

De ustabiliserede lagtykkelser ved Eu = 8 MPa fremgår af Figur 2.

| Eo [MPa] | 30 | 45 | 60 | 80 | 120 | 150 |
|---|---|---|---|---|---|---|
| Belastningsklasse | 1 | 2 | 3 | 4 | 5 | 6 |
| Ustabiliseret lagtykkelse [mm] | 700 | 800 | 877 | 1000 | 1100 | 1200 |

*Figur 2 Ustabiliserede lagtykkelser ved Eu = 8 MPa.*

En lagtykkelse på 1038 mm ligger mellem kurverne for Eo = 80 MPa og
Eo = 120 MPa, og der fås f = 0,382 og Eo_ækv = 95,3 MPa.

Den ækvivalente Eo er en indeksværdi, der angiver opslagspunktet i
designdiagrammet. I modsætning til belastningsklasserne udtrykker den ikke et
krav til eller en forventet størrelse af overflademodulet på oversiden af de
ubundne lag. Værdien er alene et resultat af interpolationen.

Opmærksomheden henledes på, at opslagspunktet afhænger af både trafikklasse og
underbundens E-værdi. En trafikklasse kan derfor ikke henføres til ét bestemt
designdiagram, jf. Figur 3.

| T4 ved Eu = | 5 MPa | 10 MPa | 15 MPa | 20 MPa |
|---|---|---|---|---|
| Eo_ækv [MPa] | 90 | 108 | 135 | 148 |
| Nærmeste designdiagram | 4 | mellem 4 og 5 | 5 | 6 |

*Figur 3 Ækvivalent Eo for T4 ved forskellige underbunds-E-værdier.*

Forholdet skyldes, at de to klassesystemer beskriver forskellige størrelser:
belastningsklasserne beskriver lastens størrelse, mens trafikklasserne
beskriver antallet af belastningsgentagelser.

---

#### 3 Geonet-reduktion

Designdiagrammerne indeholder som udgangspunkt tre kurver for hver Eo-værdi:
én for ustabiliseret opbygning og én for henholdsvis 1 og 2 lag geonet. Alle
tre er fastlagt ved feltforsøg.

Lagtykkelsen for armeret opbygning bestemmes ved interpolation mellem de samme
to Eo-kurver som i afsnit 2 og med den samme interpolationsfaktor f:

```
t_armeret = t_lav,armeret + f × (t_høj,armeret − t_lav,armeret)
```

For T4 ved Eu = 8 MPa, hvor f = 0,382, fås værdierne i Figur 4.

| Ved Eu = 8 MPa | Eo = 80 MPa (kl. 4) | Eo = 120 MPa (kl. 5) | Eo_ækv = 95,3 MPa |
|---|---|---|---|
| Ustabiliseret | 1000 mm | 1100 mm | 1038 mm |
| 1 lag geonet | 700 mm | 800 mm | 738 mm |
| 2 lag geonet | 600 mm | 700 mm | 638 mm |

*Figur 4 Lagtykkelser ved Eo_ækv, bestemt ved interpolation mellem de to
nærmeste Eo-kurver.*

Reduktionen bestemmes som forskellen mellem den ustabiliserede og den armerede
lagtykkelse:

```
1 lag geonet:  (1038 − 738) / 1038 = 28,9 %
2 lag geonet:  (1038 − 638) / 1038 = 38,5 %
```

Reduktionen interpoleres ikke direkte, men følger af de interpolerede
lagtykkelser. Den fundne reduktion på 28,9 % ligger følgelig mellem de to
nærmeste kurvers egne reduktioner på henholdsvis 30,0 % (Eo = 80 MPa) og
27,3 % (Eo = 120 MPa).

Da den ustabiliserede kurve indgår i begge interpolationer, er
interpolationsfaktoren den samme, uanset om den bestemmes ud fra lagtykkelsen
eller ud fra Eo-værdien. Den ækvivalente Eo kan derfor betragtes som en
angivelse af interpolationsfaktoren.

Der gøres opmærksom på, at designdiagrammerne ikke indeholder armerede kurver
i alle punkter. Ved Eu = 10 MPa findes eksempelvis ingen kurve for 2 lag
geonet ved Eo = 30, 45, 60 og 80 MPa. Falder den ækvivalente Eo i dette
område, kan reduktionen for 2 lag ikke bestemmes, og resultatet udelades.

---

#### 4 Korrektion for materialer og geonettype

De lagtykkelser, der bestemmes efter afsnit 3, er designdiagrammernes
basisværdier, som forudsætter en friktionsvinkel på φ = 37°. Lagtykkelsen
korrigeres for det valgte materiale og det valgte geonet:

```
T   = T_basis × (1 + k_φ + k_net)
k_φ = −0,02 × (φ − 37°)
```

hvor:

- **k_φ** = korrektion for friktionsvinklen i de ubundne materialer.
- **k_net** = korrektion for det valgte geonet i forhold til referencenettet.
  Værdien er 0 for referencenettet og negativ for net med højere effektivitet.

Korrektionen for friktionsvinklen anvendes på samtlige tre kurver. Korrektionen
for geonettype anvendes alene på de armerede kurver, idet den ustabiliserede
opbygning ikke indeholder geonet. Reduktionen opgøres derfor i forhold til den
korrigerede ustabiliserede lagtykkelse, således at begge lagtykkelser er
korrigeret på samme grundlag.

---

#### 5 Sammenfatning

Fremgangsmåden kan sammenfattes i fire trin pr. kombination af trafikklasse og
underbunds-E-værdi:

1. Den ubundne lagtykkelse fastlægges som t_SG + t_BL fra VejDim-kørslen. Ved
   E-værdier mellem de kørte punkter interpoleres i log(Eu).
2. Den ækvivalente Eo bestemmes ved interpolation mellem de to nærmeste
   Eo-kurver, således at den ustabiliserede lagtykkelse svarer til den
   fastlagte.
3. Lagtykkelsen for armeret opbygning bestemmes ved interpolation mellem de
   samme to Eo-kurver med samme interpolationsfaktor. Reduktionen følger heraf.
4. Lagtykkelserne korrigeres for friktionsvinkel og geonettype.

Grundlaget er rent bæreevnemæssigt. Kravene til frostsikring og koblingshøjde,
jf. håndbogens afsnit 5.1 og 5.3, er ikke omfattet og bør kontrolleres
særskilt.
"""

_KORR_DATA_INTRO_MD = """
**{antal} kørsler** = T1–T6 × Eu {{3, 4, 5, 10, 15, 20, 30, 40 MPa}}, alle med:

- Belastningsmodel Æ10 tvillingehjul (standard), 60–80 km/t, afvanding "Nej".
- Underbund "Frostsikker" med **manuelt overskrevet E = celle-Eu** — fjerner
  koblingshøjdekravet, så kørslen bliver ren bæreevne (dokumenteret forudsætning).
- Levetidsmål 20 år; alle lag ≥ 20 år; SG II (E = 300) over BL II U≤3 (E = 100),
  justeret af VejDim.
- **Standard asfalt-E** (ikke overskrevet).

**Fast asfaltpakke pr. klasse** (bundet lag låst hvor muligt, ellers
VejDim-beregnet — derfor et interval, hvor tykkelsen varierer med Eu):
"""

_KORR_DATA_NOTE_MD = """
Tykkelser på bundne bærelag, som VejDim selv beregner (kan ikke låses), er
programmets egne værdier. NÆ10 er dimensioneringstrafikken over
20 år for klassen.
"""


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

_KORR_ZONER_MD = """
Sammenkædningen er gyldig i en veldefineret **kernezone**, som omfatter 30 af
tabellens 48 celler — typisk T2–T4 ved middel underbund og de lave
trafikklasser ved stiv underbund. I kernezonen ligger reduktionerne på
**25–47 %, med en middelværdi på 30 %**, hvilket svarer til niveauet ved
dimensionering efter belastningsklasse.

Uden for kernezonen falder opslagspunktet uden for designdiagrammernes
gyldighedsområde. Der foretages ikke ekstrapolation; i stedet afvises cellen:

- **"under"** (blød underbund, lav trafikklasse): den ubundne lagtykkelse fra
  VejDim er mindre end den mest konservative kurve i diagrammet.
  Belastningsklassegrundlaget bør anvendes. Koblingshøjden er ofte styrende for
  disse celler i praksis.
- **"over"** (stiv underbund, høj trafikklasse): den ubundne lagtykkelse fra
  VejDim overstiger diagrammernes tykkelsesområde. En konkret VejDim-beregning
  er nødvendig.

**Forbehold:**

1. **VejDim omfatter ikke geonet.** Reduktionen hviler på feltforsøg fra
   GS-GRID og Tensar, ikke på vejreglen.
2. **MSL erstatter stabilgrus og bundsikring samlet.** Sammenligningen foretages
   på den samlede ubundne lagtykkelse. Materialekravet til MSL svarer til
   stabilgrus og er dermed strengere end kravet til bundsikring, hvilket er
   konservativt.
3. **Frostsikring og koblingshøjde er ikke omfattet.** Kørslerne er udført med
   frostsikker underbund. En geonet-reduceret opbygning bør ikke bringe
   totalhøjden under koblingshøjden for frostfarlig underbund, jf. håndbogens
   afsnit 5.3. Forholdet bør kontrolleres særskilt.
4. **Manglende armerede kurver i kernezonen.** I enkelte celler mangler
   diagrammet data for 1 lag geonet ved den ækvivalente Eo, idet kurven er tom
   ved høj Eo og tynd opbygning. Reduktionen kan da ikke bestemmes, selv om
   cellen ligger inden for kernezonen.
5. **Følsomhed over for asfaltpakken.** Den ækvivalente Eo afhænger af den
   valgte, faste asfaltpakke pr. trafikklasse. De anvendte pakker er VejDims
   egne værdier.
6. **Trafikklasse T7 er ikke medtaget**, idet klassen er åben. Der henvises til
   en konkret VejDim-beregning.
"""

def render_trafikklasse_korrelation() -> None:
    st.title("Trafikklasse-korrelation")
    st.caption(
        "Datagrundlaget bag trafikklasse-dimensioneringen: Vejdirektoratets "
        "trafikklasser koblet til designdiagrammerne via de rå VejDim-kørsler. "
        "Kørslerne kan redigeres — den ækvivalente Eo genberegnes og bruges live "
        "i beregningen."
    )

    raekker = berig_koersel_raekker(_aktiv_koersel_raekker())

    with st.expander("Metode og fremgangsmåde", expanded=True):
        st.markdown(_KORR_METODE_MD)
    with st.expander("Datagrundlag og forudsætninger"):
        st.markdown(_KORR_DATA_INTRO_MD.format(antal=len(raekker) or 36))
        st.dataframe(
            _asfaltpakke_rows(raekker),
            width="content",
            hide_index=True,
        )
        st.markdown(_KORR_DATA_NOTE_MD)
    with st.expander("Zoner og forbehold"):
        st.markdown(_KORR_ZONER_MD)
    st.caption(
        "Fuld dokumentation: *Dokumenter og data/Korrelation_trafikklasse_Eo.md*."
    )

    st.divider()

    import pandas as pd

    st.subheader("VejDim-kørsler (redigerbar)")
    st.caption(
        "De oprindelige kørsler, præcis som de blev indtastet i VejDim — og "
        "samtidig det grundlag, dimensioneringen regner på. Ret en værdi, og "
        "Eo_ækv-tabellen nedenfor og trafikklasse-beregningen følger med med "
        "det samme. **Ubundet** og **Samlet højde** beregnes automatisk og kan "
        "ikke redigeres."
    )

    if st.button(
        "Nulstil til standardværdier",
        type="secondary",
        help="Kasserer foretagne ændringer og gendanner de oprindelige "
             "48 kørsler.",
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
    _mm = dict(min_value=0.0, step=10.0, format="%.0f")
    # Højde nok til alle rækker, så tabellen vises i fuld længde uden scroll.
    # Streamlit bruger ca. 35 px pr. række + 35 px til overskriftsrækken.
    editor_hoejde = 35 * (len(editor_rows) + 1) + 3
    redigeret = st.data_editor(
        pd.DataFrame(editor_rows),
        width="stretch",
        height=editor_hoejde,
        hide_index=True,
        column_config={
            "Trafikklasse": st.column_config.TextColumn("Trafikklasse", disabled=True),
            "Eu (MPa)": st.column_config.NumberColumn("Eu (MPa)", disabled=True, format="%.0f"),
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
            f"værdier. Brug <i>Nulstil til standardværdier</i> for at gendanne dem.",
            "advarsel",
        )

    st.divider()

    st.subheader("Afledt: ækvivalent Eo (Eo_ækv)")
    st.markdown(
        "Tabellen angiver resultatet af tilbageberegningen for hver celle, "
        "det vil sige opslagspunktet i designdiagrammet — den kurve, hvis "
        "ustabiliserede lagtykkelse svarer til kørslens ubundne opbygning, "
        "jf. metodeafsnittet ovenfor. Det er denne tabel, dimensioneringen "
        "slår op i ved valg af trafikklasse.\n\n"
        "Designdiagrammerne omfatter alene kurverne **Eo = 30–150 MPa**. En "
        "celle kan derfor kun tildeles et opslagspunkt, hvis den ubundne "
        "lagtykkelse fra VejDim ligger mellem den tyndeste og den tykkeste "
        "kurve ved den pågældende E-værdi. I modsat fald angives:\n\n"
        "- **under** — den ubundne lagtykkelse er mindre end diagrammets mest "
        "konservative kurve (Eo = 30 MPa). Eksempelvis kræver T1 ved "
        "Eu = 5 MPa 560 mm, mens kurven for Eo = 30 MPa ligger på 900 mm. Der "
        "findes ingen kurve med så lille en lagtykkelse, og reduktionen kan "
        "ikke bestemmes. Belastningsklassegrundlaget bør anvendes. I praksis "
        "er frostkravet ofte styrende for totalhøjden i disse tilfælde.\n"
        "- **over** — den ubundne lagtykkelse overstiger diagrammets stiveste "
        "kurve (Eo = 150 MPa). Eksempelvis kræver T6 ved Eu = 10 MPa 1.146 mm, "
        "mens kurven for Eo = 150 MPa slutter ved 1.100 mm. Kurverne "
        "forlænges ikke ud over feltforsøgenes gyldighedsområde, og der "
        "henvises til en konkret VejDim-beregning.\n\n"
        "- **mangler** — cellen indeholder endnu ingen VejDim-kørsel, idet den "
        "ubundne lagtykkelse er 0. Cellen indgår hverken i opslaget eller i "
        "interpolationen, før den udfyldes i tabellen ovenfor.\n\n"
        "Vælges en celle i zonen 'under' eller 'over' ved dimensioneringen, "
        "vises den tilsvarende meddelelse i stedet for resultater. Der gøres "
        "opmærksom på, at zonerne følger det aktive designdiagram. Ændres "
        "diagramdata eller kørslerne ovenfor, kan celler skifte zone.\n\n"
        "For E-værdier mellem to kørte punkter bestemmes den ubundne "
        "lagtykkelse ved lineær interpolation i log(Eu), hvorefter den "
        "ækvivalente Eo tilbageberegnes ved den valgte E-værdi. Lagtykkelsen "
        "aftager tilnærmelsesvis retlinet med log(Eu), hvorfor denne "
        "fremgangsmåde er mere nøjagtig end interpolation på den ækvivalente "
        "Eo."
    )
    korr = korrelation_fra_koersler(
        koersler_fra_raekker(raekker), _aktiv_t_basis_table()
    )
    _vis_korrelationstabel(korr)


def render_materialer() -> None:
    st.title("Materialer")
    st.caption(
        "Anvend standard materialerne til dimensioneringen, eller indtast egne materialer. Ændringer gemmes automatisk og anvendes ved beregninger "
        "i Brugerdefineret-tilstand."
    )
    st.divider()

    import pandas as pd

    kol_a, kol_b, kol_c = st.columns([1, 1, 4])
    with kol_a:
        if st.button("Tilføj materiale", icon=":material/add:", width="stretch"):
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
        if st.button("Nulstil til standard", icon=":material/refresh:",
                     width="stretch", type="secondary"):
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

    st.title("Rapport")
    st.caption(
        "Generér en notat-rapport (Word og PDF) baseret på den seneste "
        "dimensionering. Standardtekster kan redigeres pr. rapport."
    )
    st.divider()

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
        st.subheader("A. Projekt-oplysninger")
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

    # --- B. Redigerbare skabelon-sektioner ---------------------------------
    st.subheader("B. Skabelon-tekster")
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
    # Flow B, jf. afsnit 5: input i venstre kolonne, resultatet fast i højre.
    # Tilstandsvalget står øverst i inputkolonnen og aflæses her, fordi det
    # afgør, hvilken af de to render-funktioner der tegner begge kolonner.
    input_kol, resultat_kol = st.columns([328, 1000], gap="large")

    if st.session_state.get("tilstand", "Standard") == "Standard":
        render_standard(input_kol, resultat_kol)
    else:
        render_brugerdefineret(input_kol, resultat_kol)

elif aktiv_side == "materialer":
    render_materialer()

elif aktiv_side == "geonet_database":
    render_geonet_database()

elif aktiv_side == "designdiagrammer":
    render_designdiagrammer()

elif aktiv_side == "trafikklasse_korrelation":
    render_trafikklasse_korrelation()

elif aktiv_side == "rapport":
    render_rapport()
