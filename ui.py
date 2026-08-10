"""BG Byggros — præsentationslag til Geonet-beregning.

Modulet indeholder de visuelle byggeklodser fra designgennemgangen. Ingen
beregningslogik: alle funktioner tager færdige tal og returnerer opmærkning.

Anvendelse i app.py:

    import ui

    ui.opsaet_side()                      # skal stå før alle andre st-kald
    ui.topbjaelke(vis_mellemregninger=False)
    ...
    input_col, resultat_col = st.columns([328, 1000], gap="large")

Kræver .streamlit/config.toml og assets/byggros_theme.css fra samme udrulning.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------- konstanter

FARVE = {
    "ink": "#15211A",
    "ink_70": "#4A554E",
    "ink_45": "#7A857D",
    "ink_25": "#9AA39C",
    "linje": "#DCE1DD",
    "linje_blod": "#E6EAE6",
    "flade": "#FFFFFF",
    "laerred": "#F4F6F4",
    "gron": "#1B6B34",
    "gron_mork": "#12401F",
    "gron_lys": "#F7FBF8",
    "gron_050": "#EDF4EE",
    "advarsel": "#A8600B",
    "advarsel_flade": "#FCF5E8",
    "kritisk": "#B42318",
    "jord": "#8B7355",
    "baerelag": "#D9DDD9",
    "baerelag_kant": "#B9C0BA",
    "bundsikring": "#EDEFED",
    "bundsikring_kant": "#C4CAC5",
}

SANS = "'IBM Plex Sans',system-ui,sans-serif"
MONO = "'IBM Plex Mono',ui-monospace,monospace"

ROD = Path(__file__).parent


# ------------------------------------------------------------ talformatering

def mm(vaerdi: float | None) -> str:
    """1038 → '1.038 mm'. None → '—'."""
    if vaerdi is None:
        return "—"
    return f"{vaerdi:,.0f} mm".replace(",", ".")


def mpa(vaerdi: float | None) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:,.0f} MPa".replace(",", ".")


def grader(vaerdi: float | None) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:.1f}°".replace(".", ",")


def procent(vaerdi: float | None, decimaler: int = 0) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:.{decimaler}f} %".replace(".", ",")


def fortegn(vaerdi: float) -> str:
    """-245 → '−245' med typografisk minus."""
    return f"{vaerdi:,.0f}".replace(",", ".").replace("-", "−")


# ------------------------------------------------------------------ opsætning

def opsaet_side(titel: str = "Geonet-dimensionering · BG Byggros") -> None:
    """Sætter sidekonfiguration og indlæser stylesheetet. Kaldes først i app.py."""
    st.set_page_config(
        page_title=titel,
        page_icon=str(ROD / "assets" / "byggros_logo.jpeg"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css = (ROD / "assets" / "byggros_theme.css").read_text(encoding="utf-8")
    # En afsluttende style-tag i stylesheetet — også inde i en kommentar —
    # ville afbryde style-elementet, så resten af filen blev vist som tekst.
    css = re.sub(r"</\s*style", "<\\/style", css, flags=re.I)
    st.html(f"<style>{css}</style>")


# -------------------------------------------------------------------- topbar

def topbjaelke(version: str = "v0.4") -> None:
    """Mørk bjælke med logo, værktøjsnavn og kontakten for mellemregninger.

    Kontakten tegnes som en Streamlit-widget inde i bjælken, så dens tilstand
    kan aflæses i st.session_state["vis_mellemregninger"]. Bjælken gentages på
    alle sider, så kontakten gælder hele værktøjet.

    Logoet ligger på en hvid brik: firmamærket er mørkt og ville forsvinde
    direkte på bjælken.
    """
    if "vis_mellemregninger" not in st.session_state:
        st.session_state.vis_mellemregninger = False

    with st.container(key="bg_topbar"):
        navn_kol, handling_kol = st.columns([3, 2], vertical_alignment="center")
        with navn_kol:
            st.html(
                f"""
                <div style="display:flex;align-items:center;gap:14px">
                  <div style="background:#fff;border-radius:3px;padding:5px 8px;
                              display:flex;align-items:center">
                    <img src="app/static/byggros_logo.png" alt="BG Byggros"
                         style="height:15px;width:auto;display:block">
                  </div>
                  <div style="width:1px;height:20px;background:rgba(255,255,255,.22)"></div>
                  <div style="font:600 13px/1 {SANS};color:#fff;letter-spacing:-.01em">
                    Geonet-dimensionering</div>
                  <div style="font:500 10px/1 {MONO};color:rgba(255,255,255,.5);
                              padding:3px 6px;border:1px solid rgba(255,255,255,.2);
                              border-radius:3px">{escape(version)}</div>
                </div>
                """
            )
        with handling_kol:
            kontakt_kol, nulstil_kol, rapport_kol = st.columns(
                [2, 1, 1.4], vertical_alignment="center"
            )
            with kontakt_kol:
                st.toggle(
                    "Vis mellemregninger",
                    key="vis_mellemregninger",
                    help=(
                        "Viser φ-beregningen, korrektionsleddene og "
                        "interpolationsdetaljerne bag de viste tykkelser."
                    ),
                )
            # Knapperne aflæses af app.py gennem deres nøgler, når den aktive
            # side er bestemt. Nulstil gælder dimensioneringens felter; på de
            # øvrige sider er der intet at rydde, og knappen er slået fra.
            paa_dimensionering = (
                st.session_state.get("aktiv_side", "dimensionering")
                == "dimensionering"
            )
            with nulstil_kol:
                st.button(
                    "Nulstil",
                    key="bg_nulstil",
                    width="stretch",
                    disabled=not paa_dimensionering,
                    help=(
                        "Nulstil dimensioneringens felter til standardværdierne."
                        if paa_dimensionering
                        else "Gælder dimensioneringens felter."
                    ),
                )
            with rapport_kol:
                st.button(
                    "Generér rapport",
                    key="bg_gaa_til_rapport",
                    type="primary",
                    width="stretch",
                    disabled=not paa_dimensionering,
                    help="Gå til rapportsiden med den aktuelle dimensionering.",
                )


def mellemregninger() -> bool:
    """Er kontakten for mellemregninger slået til."""
    return bool(st.session_state.get("vis_mellemregninger", False))


def etiket(tekst: str) -> None:
    """Lille versal sektionsetiket — erstatter emoji-overskrifter."""
    st.html(f'<div class="bg-eyebrow">{escape(tekst.upper())}</div>')


# ------------------------------------------------------------- resultatkort

def resultatkort(kort: list[dict]) -> None:
    """Rækken af resultattal.

    Hvert kort: {"etiket", "vaerdi", "enhed", "note", "delta", "delta_note",
                 "anbefalet": bool}
    Første kort er referencetallet uden delta.
    """
    kolonner = "1.15fr" + " 1fr" * (len(kort) - 1)
    celler = []
    for k in kort:
        anbefalet = k.get("anbefalet", False)
        flade = FARVE["gron_lys"] if anbefalet else FARVE["flade"]
        kant = f"box-shadow:inset 3px 0 0 {FARVE['gron']};" if anbefalet else ""
        etiket_farve = FARVE["gron"] if anbefalet else FARVE["ink_45"]
        tal_farve = FARVE["gron_mork"] if anbefalet else FARVE["ink"]
        badge = (
            f'<div style="font:600 9px/1 {MONO};letter-spacing:.08em;color:#fff;'
            f'background:{FARVE["gron"]};padding:4px 7px;border-radius:3px">ANBEFALET</div>'
            if anbefalet else ""
        )
        delta = ""
        if k.get("delta") is not None:
            delta = (
                f'<div style="display:flex;align-items:center;gap:7px;margin-top:9px">'
                f'<div style="font:600 11.5px/1 {MONO};color:{FARVE["gron"]}">{escape(k["delta"])}</div>'
                f'<div style="font:400 11.5px/1 {SANS};color:{FARVE["ink_70"]}">'
                f'{escape(k.get("delta_note", ""))}</div></div>'
            )
        elif k.get("note"):
            delta = (
                f'<div style="font:400 11.5px/1.5 {SANS};color:{FARVE["ink_45"]};'
                f'margin-top:9px">{escape(k["note"])}</div>'
            )
        celler.append(
            f"""
            <div style="background:{flade};padding:18px 20px 17px;{kant}">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px">
                <div style="font:600 9.5px/1 {MONO};letter-spacing:.1em;color:{etiket_farve}">
                  {escape(k['etiket'].upper())}</div>{badge}
              </div>
              <div style="display:flex;align-items:baseline;gap:6px">
                <div style="font:600 40px/1 {MONO};color:{tal_farve};
                            font-variant-numeric:tabular-nums;letter-spacing:-.02em">{escape(k['vaerdi'])}</div>
                <div style="font:500 15px/1 {SANS};color:{FARVE['ink_70']}">{escape(k.get('enhed','mm'))}</div>
              </div>
              {delta}
            </div>
            """
        )
    st.html(
        f'<div style="display:grid;grid-template-columns:{kolonner};gap:1px;'
        f'background:{FARVE["linje"]};border:1px solid {FARVE["linje"]};'
        f'border-radius:5px;overflow:hidden">{"".join(celler)}</div>'
    )


# --------------------------------------------------------- snit-visualisering

def snit(
    kolonner: list[dict],
    reference_mm: float | None = None,
    hoejde_px: int = 230,
    jord_px: int = 26,
) -> None:
    """Tegner opbygningssnittene i HTML — erstatter matplotlib-figuren.

    kolonner: liste af
        {"titel", "lag": [(navn, mm, "baerelag"|"bundsikring")],
         "geonet_mm": [kote målt fra underbundens overkant],
         "total_mm", "status": (tekst, "gron"|"kritisk"|"neutral")}
    reference_mm: den indtastede tykkelse; tegnes som fælles stiplet linje.
                  None i Standard-tilstand, hvor der ikke indtastes lag.

    Alle kolonner deler skala, så søjlerne kan sammenlignes direkte.
    """
    maks = max(k["total_mm"] for k in kolonner)
    if reference_mm:
        maks = max(maks, reference_mm)
    skala = (hoejde_px - jord_px - 8) / maks          # px pr. mm

    def px(v: float) -> float:
        return round(v * skala, 1)

    ref_linje = ""
    if reference_mm:
        ref_linje = (
            f'<div style="position:absolute;left:0;right:0;'
            f'bottom:{px(reference_mm) + jord_px}px;'
            f'border-top:1.5px dashed {FARVE["ink_25"]}"></div>'
        )

    celler = []
    for i, k in enumerate(kolonner):
        lag_html = []
        for navn, tykkelse, slags in k["lag"]:
            flade = FARVE["baerelag"] if slags == "baerelag" else FARVE["bundsikring"]
            kant = FARVE["baerelag_kant"] if slags == "baerelag" else FARVE["bundsikring_kant"]
            h = px(tykkelse)
            indhold = (
                f'<div style="font:500 10px/1.2 {SANS};color:{FARVE["ink"]};text-align:center">{escape(navn)}</div>'
                f'<div style="font:600 10px/1 {MONO};color:{FARVE["ink"]}">{tykkelse:.0f}</div>'
            ) if h >= 34 else ""
            lag_html.append(
                f'<div style="height:{h}px;background:{flade};border:1px solid {kant};'
                f'display:flex;flex-direction:column;align-items:center;justify-content:flex-start;'
                f'padding-top:8px;box-sizing:border-box;gap:1px;overflow:hidden">{indhold}</div>'
            )

        geonet_html = "".join(
            f'<div style="position:absolute;left:50%;transform:translateX(-50%);'
            f'bottom:{px(kote) + jord_px - 1}px;width:112px;height:2px;'
            f'background:{FARVE["kritisk"]}"></div>'
            for kote in k.get("geonet_mm", [])
        )

        jord_tekst = (
            f'<div style="font:600 9px/1 {MONO};color:#fff;letter-spacing:.05em">'
            f'{escape(k["underbund_tekst"])}</div>'
            if k.get("underbund_tekst") else ""
        )

        status_tekst, status_slags = k.get("status", ("", "neutral"))
        status_farve = {
            "gron": FARVE["gron"], "kritisk": FARVE["kritisk"],
        }.get(status_slags, FARVE["ink_45"])
        vaegt = 600 if status_slags == "gron" else 500

        titel_farve = FARVE["gron"] if status_slags == "gron" else FARVE["ink"]

        celler.append(
            f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:12px">
              <div style="font:600 11.5px/1 {SANS};color:{titel_farve}">{escape(k['titel'])}</div>
              <div style="position:relative;width:100%;height:{hoejde_px}px">
                {ref_linje}
                <div style="position:absolute;left:50%;transform:translateX(-50%);
                            bottom:{jord_px}px;width:104px;display:flex;flex-direction:column">
                  {''.join(lag_html)}
                </div>
                {geonet_html}
                <div style="position:absolute;left:0;right:0;bottom:0;height:{jord_px}px;
                            background:repeating-linear-gradient(45deg,{FARVE['jord']},{FARVE['jord']} 3px,#7A6449 3px,#7A6449 6px);
                            display:flex;align-items:center;justify-content:center">{jord_tekst}</div>
                <div style="position:absolute;left:calc(50% + 58px);
                            bottom:{px(k['total_mm']) / 2 + jord_px}px;
                            font:600 10.5px/1 {MONO};color:{FARVE['ink']};white-space:nowrap">
                  {mm(k['total_mm'])}</div>
              </div>
              <div style="font:{vaegt} 10.5px/1 {SANS};color:{status_farve}">{escape(status_tekst)}</div>
            </div>
            """
        )

    signatur = [
        (f'<div style="width:16px;height:9px;background:{FARVE["baerelag"]};'
         f'border:1px solid {FARVE["baerelag_kant"]}"></div>', "Bærelag"),
        (f'<div style="width:16px;height:9px;background:{FARVE["bundsikring"]};'
         f'border:1px solid {FARVE["bundsikring_kant"]}"></div>', "Bundsikring"),
        (f'<div style="width:16px;height:2px;background:{FARVE["kritisk"]}"></div>', "Geonet"),
    ]
    if reference_mm:
        signatur.append(
            (f'<div style="width:16px;border-top:1.5px dashed {FARVE["ink_25"]}"></div>',
             "Indtastet niveau")
        )
    signatur_html = "".join(
        f'<div style="display:flex;align-items:center;gap:6px">{glyf}{escape(tekst)}</div>'
        for glyf, tekst in signatur
    )

    st.html(
        f"""
        <div style="padding:26px 0 14px;display:grid;
                    grid-template-columns:repeat({len(kolonner)},1fr);gap:22px">{''.join(celler)}</div>
        <div style="display:flex;align-items:center;gap:20px;
                    font:400 10.5px/1 {SANS};color:{FARVE['ink_45']}">{signatur_html}</div>
        """
    )


# ----------------------------------------------------------- produkttabellen

def produkttabel(raekker: list[dict], grupperet: bool = False) -> None:
    """Produktvalg.

    Hver række: {"navn", "note", "en_lag", "en_delta", "to_lag", "to_delta",
                 "indeks": str|None, "anbefalet": bool, "gruppe": str|None}
    grupperet=True indsætter en versal gruppeoverskrift, når "gruppe" skifter
    (Standard-tilstand). Alle tal er højrestillede og tabulære.
    """
    har_indeks = any(r.get("indeks") for r in raekker)
    kolonner = "1.6fr .7fr .8fr .8fr" if har_indeks else "1.5fr .8fr .8fr"

    hoved = ['<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s">PRODUKT</div>'
             % (MONO, FARVE["ink_45"])]
    if har_indeks:
        hoved.append('<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s;text-align:right">INDEKS</div>'
                     % (MONO, FARVE["ink_45"]))
    for m in ("1 LAG", "2 LAG"):
        hoved.append('<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s;text-align:right">%s</div>'
                     % (MONO, FARVE["ink_45"], m))

    krop, sidste_gruppe = [], None
    for r in raekker:
        if grupperet and r.get("gruppe") and r["gruppe"] != sidste_gruppe:
            sidste_gruppe = r["gruppe"]
            krop.append(
                f'<div style="padding:12px 20px 5px;font:600 9.5px/1 {MONO};'
                f'letter-spacing:.08em;color:{FARVE["ink_25"]};background:#FDFDFD">'
                f'{escape(r["gruppe"].upper())}</div>'
            )
        anbefalet = r.get("anbefalet", False)
        flade = f'background:{FARVE["gron_lys"]};box-shadow:inset 3px 0 0 {FARVE["gron"]};' if anbefalet else ""
        vaegt = 600 if anbefalet else 500
        note_farve = FARVE["gron"] if anbefalet else FARVE["ink_25"]

        indeks = (f'<div style="text-align:right;font:500 12px/1.2 {MONO};'
                  f'color:{FARVE["ink_70"]}">{escape(str(r.get("indeks","")))}</div>') if har_indeks else ""

        def tal(vaerdi, delta, groen):
            farve = FARVE["gron_mork"] if (anbefalet and groen) else FARVE["ink"]
            d_farve = FARVE["gron"] if (anbefalet and groen) else FARVE["ink_45"]
            return (
                f'<div style="text-align:right">'
                f'<div style="font:{vaegt} 13px/1.2 {MONO};color:{farve};'
                f'font-variant-numeric:tabular-nums">{vaerdi:.0f}</div>'
                f'<div style="font:400 10px/1.2 {MONO};color:{d_farve}">{fortegn(delta)}</div></div>'
            )

        krop.append(
            f'<div style="display:grid;grid-template-columns:{kolonner};padding:10px 20px;'
            f'border-bottom:1px solid #F0F2F0;align-items:baseline;{flade}">'
            f'<div><div style="font:{vaegt} 12px/1.3 {SANS};color:{FARVE["ink"]}">{escape(r["navn"])}</div>'
            f'<div style="font:400 10.5px/1.3 {SANS};color:{note_farve}">{escape(r.get("note",""))}</div></div>'
            f'{indeks}{tal(r["en_lag"], r["en_delta"], False)}{tal(r["to_lag"], r["to_delta"], True)}</div>'
        )

    st.html(
        f'<div style="display:grid;grid-template-columns:{kolonner};padding:9px 20px;'
        f'border-bottom:1px solid {FARVE["linje_blod"]};background:#FBFCFB">{"".join(hoved)}</div>'
        f'{"".join(krop)}'
    )


# ------------------------------------------------------------------ besked

def besked(tekst: str, slags: str = "info") -> None:
    """Ensartet besked. slags: info | advarsel | kritisk | ok."""
    stil = {
        "info": (FARVE["laerred"], FARVE["linje"], FARVE["ink_45"]),
        "advarsel": (FARVE["advarsel_flade"], "#F0E2C6", FARVE["advarsel"]),
        "kritisk": ("#FBF0EF", "#F2D6D3", FARVE["kritisk"]),
        "ok": (FARVE["gron_lys"], "#DDE9DF", FARVE["gron"]),
    }[slags]
    st.html(
        f'<div style="background:{stil[0]};border:1px solid {stil[1]};'
        f'border-left:3px solid {stil[2]};border-radius:4px;padding:10px 12px;margin:2px 0">'
        f'<div style="font:400 11.5px/1.55 {SANS};color:{FARVE["ink_70"]}">{tekst}</div></div>'
    )
